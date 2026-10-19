"""BMAT-only exact matching, after current RAW/CLEAN exclusion and quality gates."""

import json
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

from processors.matching.core import file_reference
from processors.matching.explanation import build_final_explanation
from processors.matching.storage import load_matched, protect_output
from processors.normalization.bmat.backtest import files, load


def key(value, question=False):
    meta = value.get("metadata", {}) if question else value
    family = meta.get("source_family", meta.get("source"))
    year, section, number = (
        meta.get("year"),
        meta.get("section"),
        value.get("question_number"),
    )
    if (
        family != "bmat"
        or type(year) is not int
        or section != "section_1"
        or type(number) is not int
        or number < 1
    ):
        raise ValueError("Identity is not a reliable BMAT Section 1 identity")
    if question:
        original = value["source_question_key"]
        if (
            original.get("source"),
            original.get("year"),
            original.get("section"),
            original.get("question_number"),
        ) != (family, year, section, number):
            raise ValueError("Question key conflicts with metadata")
    return family, year, section, number


def eligibility(question):
    if question["bmat_filter"]["skip_from_pipeline"]:
        return "intentionally_skipped", "Target remains excluded by BMAT policy."
    if (
        question["cleaning_issues"]
        or question["raw_record"]["parsing_issues"]
        or question.get("raw_document_warnings")
        or not question["pipeline_eligible"]
        or question["pipeline_status"] != "clean_ready"
    ):
        return (
            "deferred_upstream_issue",
            "Matching deferred because question has unresolved upstream issue.",
        )
    options = question["options"]
    labels = [o["label"] for o in options]
    if (
        not question.get("main_question")
        or len(options) < 2
        or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)])
        or any(not (o.get("text", "").strip() or o.get("images")) for o in options)
    ):
        return (
            "deferred_question_structure",
            "Usable Main Question and complete answer choices are required.",
        )
    return None


def build(clean_inputs, answer_path, *, previous=None, supplied_path=None):
    answer_path = Path(answer_path).resolve()
    source = json.loads(answer_path.read_text(encoding="utf-8"))
    if source.get("source_family") != "bmat" or source.get("stage") != "answer_raw":
        raise ValueError("BMAT matcher requires normalized BMAT answers")
    manifest_ref = source["source_document"]
    if file_reference(manifest_ref["path"])["sha256"] != manifest_ref["sha256"]:
        raise ValueError("Acquisition manifest changed; reparse before matching")
    questions, answers, unresolved = (
        defaultdict(list),
        defaultdict(list),
        defaultdict(list),
    )
    answer_ref = file_reference(answer_path)
    inputs = [{"kind": "answer_intermediate", **answer_ref}]
    for path in files(clean_inputs):
        data = load(path)
        if data["document"]["source"] != "bmat":
            raise ValueError(
                "TSA/non-BMAT inputs are never considered by BMAT matching"
            )
        ref = file_reference(path)
        inputs.append({"kind": "clean_questions", **ref})
        for i, q in enumerate(data["questions"]):
            questions[key(q, True)].append(
                {
                    "record": q,
                    "reference": {**ref, "json_pointer": f"/questions/{i}"},
                    "document": data["document"],
                }
            )
    for field, groups in (("answers", answers), ("unresolved_sources", unresolved)):
        for i, a in enumerate(source[field]):
            k = key(a)
            if a.get("source_document"):
                doc = a["source_document"]
                if file_reference(doc["path"])["sha256"] != doc["sha256"]:
                    raise ValueError("Saved solution HTML changed")
            groups[k].append(
                {
                    "record": a,
                    "document": deepcopy(a.get("source_document", {})),
                    "reference": {**answer_ref, "json_pointer": f"/{field}/{i}"},
                }
            )
    old = {}
    if previous:
        if previous.get("source_family") != "bmat":
            raise ValueError("Refusing to overwrite unrelated matched output")
        old = {
            tuple(
                r["identity"][f]
                for f in ("source_family", "year", "section", "question_number")
            ): r
            for r in previous["records"]
        }
    result = {
        "stage": "matched",
        "schema_version": "1",
        "source_family": "bmat",
        "inputs": inputs,
        "records": [],
        "issues": [],
        "source_issues": deepcopy(source["issues"]),
        "source_unresolved": deepcopy(source["unresolved_sources"]),
    }
    for k in sorted(set(questions) | set(answers) | set(unresolved)):
        qs, candidates = questions[k], answers[k]
        target = qs[0] if len(qs) == 1 else None
        q = target["record"] if target else None
        issues = []
        status, reason = "matched", None
        if not qs:
            status, reason = "target_missing", "Target BMAT question missing."
        elif not target:
            status, reason = (
                "duplicate_target",
                "Multiple target question records share identity.",
            )
        elif blocked := eligibility(q):
            status, reason = blocked
        elif len(candidates) > 1 or candidates and unresolved[k]:
            status, reason = (
                "duplicate_source",
                "Multiple source candidates; no candidate selected.",
            )
        elif not candidates:
            status, reason = (
                ("source_unresolved", "Source explanation/header is unresolved.")
                if unresolved[k]
                else ("source_missing", "Question solution link/source missing.")
            )
        selected = candidates[0] if len(candidates) == 1 else None
        if status == "matched":
            a = selected["record"]
            if (
                a.get("status") != "parsed"
                or a["warnings"]
                or a["correct_answer"] not in {o["label"] for o in q["options"]}
            ):
                status, reason = (
                    "answer_incompatible",
                    "Source answer is unresolved or incompatible with actual options.",
                )
            elif not a.get("explanation", {}).get("blocks"):
                status, reason = "source_unresolved", "Full explanation missing."
        a = selected["record"] if selected and status == "matched" else None
        final = build_final_explanation(a, selected["reference"] if a else None)
        if status == "matched" and final["status"] != "available":
            status, reason = (
                "source_unresolved",
                "Final Explanation is not safely ordered/complete.",
            )
            a = None
            final = build_final_explanation(None)
        current_answer = (q or {}).get("correct_answer") or old.get(k, {}).get(
            "correct_answer"
        )
        previous_record = old.get(k, {})
        previous_final = previous_record.get("final_explanation") or {}
        if status == "matched" and (
            current_answer
            and current_answer != a["correct_answer"]
            or previous_final.get("status") == "available"
            and previous_final.get("blocks") != final.get("blocks")
            and (previous_record.get("answer") or {})
            .get("source_document", {})
            .get("source_format")
            != "task_supplied_bmat_explanations"
        ):
            status, reason = (
                "answer_explanation_conflict",
                "Existing answer/explanation differs; incoming source was not silently applied.",
            )
            issues.append(
                {
                    "code": status,
                    "reason": reason,
                    "stored_answer": current_answer,
                    "worked_answer": a["correct_answer"],
                    "source_url": a["source_document"]["source_url"],
                }
            )
            a = deepcopy(previous_record.get("answer"))
            final = (
                deepcopy(previous_final)
                if previous_final
                else build_final_explanation(None)
            )
        if reason and not issues:
            issues.append({"code": status, "reason": reason})
        identity = dict(zip(("source_family", "year", "section", "question_number"), k))
        record = {
            "identity": identity,
            "status": status,
            "question": deepcopy(q),
            "question_document": deepcopy(target["document"]) if target else None,
            "question_reference": target["reference"] if target else None,
            "answer": deepcopy(a),
            "answer_reference": selected["reference"]
            if a and status == "matched"
            else previous_record.get("answer_reference")
            if a
            else None,
            "correct_answer": a["correct_answer"]
            if a
            else current_answer
            if status == "answer_explanation_conflict"
            else None,
            "final_explanation": final,
            "explanation_by_ai": False,
            "answer_candidates": deepcopy(candidates + unresolved[k])
            if status != "matched"
            else [],
            "question_candidates": deepcopy(qs) if len(qs) > 1 else [],
            "matching": {
                "confidence": "exact_source_family_year_section_question"
                if status == "matched"
                else None,
                "upstream_review_required": bool(q and q["cleaning_issues"]),
            },
            "issues": issues,
        }
        result["records"].append(record)
        result["issues"].extend({**i, **identity} for i in issues)
    counts = Counter(r["status"] for r in result["records"])
    result["summary"] = {
        "questions": sum(bool(r["question"]) for r in result["records"]),
        "eligible": sum(
            r["question"] is not None and eligibility(r["question"]) is None
            for r in result["records"]
        ),
        "parsed_explanations": len(source["answers"]),
        "unique_parsed_question_identities": sum(bool(v) for v in answers.values()),
        "unresolved_sources": len(source["unresolved_sources"]),
        "unique_unresolved_source_identities": sum(
            bool(v) for v in unresolved.values()
        ),
        "duplicate_source_question_identities": sum(
            len(answers[k]) + len(unresolved[k]) > 1
            for k in set(answers) | set(unresolved)
        ),
        "statuses": dict(counts),
    }
    if supplied_path is not None:
        from .supplied import apply

        apply(result, supplied_path, previous=previous)
    return result


def write(path, data):
    path = Path(path)
    protect_output(data, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run(clean_inputs, answer_path, output, supplied_path=None):
    previous = load_matched(output) if Path(output).exists() else None
    data = build(
        clean_inputs, answer_path, previous=previous, supplied_path=supplied_path
    )
    write(output, data)
    return data
