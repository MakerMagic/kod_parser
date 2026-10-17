"""Generic intermediate-record matching; no PDF extraction or fuzzy matching."""

import json
import re
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from parsers.blackstone.visual_inspection import read_png, resolve_asset
from processors.normalization.blackstone.body_assets import (
    resolve_question_asset,
    validate_pinned_asset,
)
from processors.normalization.blackstone.option_assets import resolve_clean_asset
from processors.normalization.blackstone.storage import clean_files, load_clean

from .explanation import build_final_explanation
from .manual_replacements import select_manual_replacement


def file_reference(path, pointer=None):
    path = Path(path).resolve()
    result = {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}
    if pointer is not None:
        result["json_pointer"] = pointer
    return result


def identity(record, question=False):
    values = record.get("metadata", {}) if question else record
    year, section, number = (
        values.get("year"),
        values.get("section"),
        record.get("question_number"),
    )
    if (
        type(year) is not int
        or type(number) is not int
        or number < 1
        or not isinstance(section, str)
        or not section
    ):
        return None
    return year, section, number


def finding(code, reason, key=None, **extra):
    return {
        "code": code,
        "reason": reason,
        "year": key[0] if key else None,
        "section": key[1] if key else None,
        "question_number": key[2] if key else None,
        "manual_review_required": True,
        **extra,
    }


def verify_question_evidence(answer, question):
    """Optional question-bearing answer sources must agree beyond numeric identity.

    Ignore typographic/whitespace differences but retain mathematical operators,
    decimal points and currency. Never rewrite either source. Opening prose and
    all supplied textual options must agree.
    Image-only options have no invented textual comparison.
    """
    evidence = answer.get("question_evidence")
    if evidence is None:
        return None

    def compact(text):
        text = (
            str(text)
            .casefold()
            .translate(str.maketrans({"–": "-", "—": "-", "−": "-"}))
        )
        return "".join(re.findall(r"[^\W_]|[+\-×÷=<>%£$.:/]", text))

    source_text = evidence.get("question_text", "")
    source = compact(source_text.splitlines()[0] if source_text else "")
    target = compact(question.get("question_text", ""))
    # Introductory prose precedes any embedded table/diagram extraction order.
    prefix = source
    if len(prefix) < 40 or not target.startswith(prefix):
        return False
    options = question.get("options") or []
    supplied = evidence.get("options") or []
    if [o.get("label") for o in supplied] != [o.get("label") for o in options]:
        return False
    return all(
        not original.get("text")
        or compact(original["text"]) == compact(clean.get("text", ""))
        for original, clean in zip(supplied, options)
    )


def existing_question_source_conflicts(data, existing):
    """Do not silently replace a prior answer/manual explanation on source import.

    Opt-in question-bearing sources only; older workflows retain their existing
    behaviour. Same-PDF parser refinements are allowed, not a different source or
    an AI/manual overlay being overwritten with different content.
    """

    def key(record):
        value = record["identity"]
        return value["year"], value["section"], value["question_number"]

    previous = {key(r): r for r in existing["records"]}
    conflicts = []
    for record in data["records"]:
        answer = record.get("answer") or {}
        if answer.get("question_evidence") is None:
            continue
        ident = record["identity"]
        old = previous.get(key(record))
        if not old:
            continue
        old_final = old.get("final_explanation") or {}
        new_final = record.get("final_explanation") or {}
        old_answer = old.get("answer") or {}
        different_answer = old.get("correct_answer") and old[
            "correct_answer"
        ] != answer.get("correct_answer")
        different_explanation = (
            old_final.get("status") == "available"
            and old_final.get("blocks") != new_final.get("blocks")
            and (
                old_final.get("explanation_by_ai")
                or old_answer.get("source_document", {}).get("sha256")
                != answer.get("source_document", {}).get("sha256")
            )
        )
        if different_answer or different_explanation:
            conflicts.append(
                finding(
                    "existing_answer_explanation_conflict",
                    "Existing answer/explanation differs from incoming question-bearing source; existing matched output was not overwritten",
                    (ident["year"], ident["section"], ident["question_number"]),
                )
            )
    return conflicts


def readiness(references, *, years=None, question_source=None):
    """Check usable input contracts/provenance, not absence of all upstream issues."""
    loaded, failures, reviews, counts, hashes = [], [], [], defaultdict(int), {}

    def verify(path, expected):
        path = Path(path).resolve()
        if path not in hashes:
            hashes[path] = sha256(path.read_bytes()).hexdigest()
        if not expected or hashes[path] != expected:
            raise ValueError(f"Traceability hash mismatch: {path}")

    for path in clean_files(references):
        try:
            data = load_clean(path)
            year = data["document"].get("year")
            if (
                years is not None
                and year not in years
                or question_source is not None
                and data["document"].get("source") != question_source
            ):
                continue
            verify(data["raw_reference"]["path"], data["raw_reference"]["sha256"])
            original = json.loads(
                Path(data["raw_reference"]["path"]).read_text(encoding="utf-8")
            )
            source = data["document"]["input"]
            verify(source["path"], source["sha256"])
            for i, question in enumerate(data["questions"]):
                key = identity(question, True)
                if (
                    question["raw_record"] != original["questions"][i]
                    or question["source_question_key"]
                    != original["questions"][i]["source_question_key"]
                ):
                    raise ValueError(
                        "Clean snapshot does not agree with the original raw question"
                    )
                if key:
                    counts[key] += 1
                    source_key = question["source_question_key"]
                    if (
                        source_key.get("year"),
                        source_key.get("section"),
                        source_key.get("question_number"),
                    ) != key:
                        raise ValueError(
                            "Clean metadata/source question identity conflict"
                        )
                raw = question["raw_reference"]["path"]
                assets = [
                    *question["visual_assets"],
                    *question["visual_previews"],
                    *[
                        a
                        for o in question["options"] or []
                        for a in o.get("images", [])
                    ],
                ]
                for asset in assets:
                    verify(resolve_question_asset(raw, path, asset), asset["sha256"])
                    validate_pinned_asset(asset)
                    if asset.get("clean_asset"):
                        clean = asset["clean_asset"]
                        verify(
                            resolve_clean_asset(path, clean["path"]), clean["sha256"]
                        )
                if question["cleaning_issues"]:
                    reviews.append(
                        {
                            "identity": key,
                            "clean_json": str(path),
                            "issues": question["cleaning_issues"],
                        }
                    )
            loaded.append((path, data))
        except (OSError, ValueError, KeyError, TypeError) as error:
            failures.append(
                finding("readiness_blocked", str(error), clean_json=str(path))
            )
    if not loaded:
        failures.append(
            finding(
                "readiness_blocked",
                "No usable clean question datasets in the selected scope",
            )
        )
    return {
        "ready": not failures,
        "question_count": sum(len(d["questions"]) for _, d in loaded),
        "unique_keys": len(counts),
        "duplicate_keys": [list(k) for k, n in counts.items() if n > 1],
        "upstream_review_records": reviews,
        "issues": failures,
    }, loaded


def answer_files(references):
    paths = []
    for value in references:
        p = Path(value).resolve(strict=True)
        paths.extend(sorted(p.rglob("*.answers.json")) if p.is_dir() else [p])
    if not paths:
        raise ValueError("No parsed answer intermediates; run the source parser first")
    return list(dict.fromkeys(paths))


def validate_answer_input(data, path):
    """Generic intermediate contract/provenance; independent of PDF layout."""
    if data.get("stage") != "answer_raw" or data.get("schema_version") != "1":
        raise ValueError("Unsupported answer intermediate contract")
    source = data["source_document"]
    if file_reference(source["path"])["sha256"] != source["sha256"]:
        raise ValueError("Answer source document hash changed")
    for related in source.get("related_sources", []):
        if file_reference(related["path"])["sha256"] != related["sha256"]:
            raise ValueError("Related answer source document hash changed")
    for issue in data.get("issues", []):
        asset = issue.get("visual_asset")
        if asset:
            png = read_png(resolve_asset(path, asset["path"]))
            if sha256(png).hexdigest() != asset["sha256"]:
                raise ValueError("Unassigned explanation visual changed/missing")
    for answer in data["answers"]:
        if answer["source_document"] != source:
            raise ValueError("Answer record/source document conflict")
        explanation = answer["explanation"]
        for field in (
            "blocks",
            "paragraphs",
            "bulleted_blocks",
            "choice_analysis",
            "other_lists",
        ):
            if not isinstance(explanation[field], list):
                raise TypeError(f"Invalid explanation structure: {field}")
        if not isinstance(explanation["main_explanation"], str):
            raise TypeError("Invalid main explanation")
        if explanation.get("availability") == "not_supplied_by_source_format" and (
            source.get("explanations_supplied") is not False
            or any(
                explanation[field]
                for field in (
                    "main_explanation",
                    "blocks",
                    "paragraphs",
                    "bulleted_blocks",
                    "choice_analysis",
                    "other_lists",
                    "visual_assets",
                )
                if field in explanation
            )
        ):
            raise ValueError("Answer-only explanation availability/content conflict")
        for asset in [
            *answer.get("visual_previews", []),
            *explanation.get("visual_assets", []),
        ]:
            if (
                file_reference(resolve_asset(path, asset["path"]))["sha256"]
                != asset["sha256"]
            ):
                raise ValueError("Answer explanation preview changed/missing")
            read_png(resolve_asset(path, asset["path"]))
        assets = explanation.get("visual_assets", [])
        indices = [asset["asset_index"] for asset in assets]
        if indices != list(range(1, len(assets) + 1)):
            raise ValueError("Explanation visual order is invalid")
        visual_blocks = [b for b in explanation["blocks"] if b.get("type") == "visual"]
        if [b["asset_index"] for b in visual_blocks] != indices:
            raise ValueError("Explanation visual block/asset references conflict")
        if not explanation["blocks"] and not answer.get("visual_previews"):
            raise ValueError("Explanation has neither text nor a source preview")


def match_records(
    clean_references,
    answer_references,
    *,
    years=None,
    question_source=None,
    section="section_1",
):
    ready, loaded = readiness(
        clean_references, years=years, question_source=question_source
    )
    output = {
        "stage": "matched",
        "schema_version": "1",
        "matching": {
            "method": "exact_year_section_question_number",
            "question_source_scope": question_source,
            "years": sorted(years) if years is not None else None,
            "section": section,
        },
        "readiness": ready,
        "inputs": [],
        "records": [],
        "issues": ready["issues"][:],
    }
    if not ready["ready"]:
        return output  # Absolutely no matching after a failed prerequisite check.
    questions, answers, invalid = defaultdict(list), defaultdict(list), []
    for path, data in loaded:
        ref = file_reference(path)
        output["inputs"].append({"kind": "clean_questions", **ref})
        for i, q in enumerate(data["questions"]):
            item = {
                "record": q,
                "reference": {**ref, "json_pointer": f"/questions/{i}"},
                "document": data["document"],
            }
            key = identity(q, True)
            if key is None:
                invalid.append(("question", item, "question_identity_unavailable"))
            elif key[1] == section:
                questions[key].append(item)
    answer_inputs = []
    for path in answer_files(answer_references):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data.get("answers"), list):
            raise TypeError("Answer intermediate must contain an answers list")
        try:
            validate_answer_input(data, path)
        except (OSError, ValueError, KeyError, TypeError) as error:
            issue = finding("readiness_blocked", str(error), source_json=str(path))
            output["issues"].append(issue)
            output["readiness"]["issues"].append(issue)
            output["readiness"]["ready"] = False
        answer_inputs.append((path, data))
    if not output["readiness"]["ready"]:
        return output
    for path, data in answer_inputs:
        ref = file_reference(path)
        output["inputs"].append({"kind": "answer_intermediate", **ref})
        relevant = any(years is None or a.get("year") in years for a in data["answers"])
        relevant = relevant or any(
            years is None or issue.get("year") in years
            for issue in data.get("issues", [])
        )
        for issue in data.get("issues", []) if relevant else []:
            if (
                years is not None
                and issue.get("year") is not None
                and issue["year"] not in years
            ):
                continue
            issue_key = (
                issue.get("year"),
                issue.get("section", section),
                issue.get("question_number"),
            )
            candidates = questions.get(issue_key, [])
            output["issues"].append(
                {
                    **issue,
                    "manual_review_required": True,
                    "source_json": str(path),
                    "answer_source": data["source_document"],
                    "question_source": candidates[0]["document"].get("input")
                    if len(candidates) == 1
                    else None,
                    "answer_pages": issue.get("answer_pages")
                    or (
                        {"start_page": issue["page"], "end_page": issue["page"]}
                        if issue.get("page")
                        else None
                    ),
                }
            )
        for i, a in enumerate(data["answers"]):
            item = {
                "record": a,
                "reference": {**ref, "json_pointer": f"/answers/{i}"},
                "document": data.get("source_document", {}),
            }
            key = identity(a)
            if key is None:
                invalid.append(("answer", item, "answer_identity_unavailable"))
            elif key[1] != section:
                invalid.append(("answer", item, "section_excluded"))
            elif years is None or key[0] in years:
                answers[key].append(item)
    for key in sorted(set(questions) | set(answers)):
        qs, ans = questions[key], answers[key]
        ans, superseded = select_manual_replacement(
            ans, qs[0]["record"]["source_question_key"] if len(qs) == 1 else None
        )
        issues = []
        if len(qs) > 1 or len(ans) > 1:
            status = "ambiguous"
            issues.append(
                finding(
                    "duplicate_candidate_match",
                    f"{len(qs)} question candidates, {len(ans)} answer candidates; none selected",
                    key,
                )
            )
        elif not qs:
            status = "unmatched_answer"
            issues.append(
                finding(
                    "answer_without_question", "No corresponding cleaned question", key
                )
            )
        elif not ans:
            status = "unmatched_question"
            issues.append(
                finding(
                    "question_without_answer", "No corresponding parsed answer", key
                )
            )
        else:
            q, a = qs[0]["record"], ans[0]["record"]
            if verify_question_evidence(a, q) is False:
                issues.append(
                    finding(
                        "source_question_content_conflict",
                        "Question-bearing answer source does not agree with clean opening prose/options; no match forced",
                        key,
                    )
                )
            if (
                a.get("target_question_key") is not None
                and a["target_question_key"] != q["source_question_key"]
            ):
                issues.append(
                    finding(
                        "identity_metadata_conflict",
                        "Explicit answer target conflicts with the cleaned source question key",
                        key,
                    )
                )
            correct = a.get("correct_answer")
            if not isinstance(correct, str) or not correct:
                issues.append(
                    finding(
                        "correct_answer_unavailable",
                        "Malformed/missing correct-answer field",
                        key,
                    )
                )
            elif [o.get("label") for o in q["options"] or []].count(correct) != 1:
                issues.append(
                    finding(
                        "correct_answer_option_conflict",
                        "Correct label is absent/duplicated in clean options; upstream structure needs review",
                        key,
                        upstream_cause=q["raw_warnings"]
                        + [i["code"] for i in q["cleaning_issues"]],
                    )
                )
            for field in ("paper", "variant", "exam"):
                if (
                    a.get(field) is not None
                    and q["metadata"].get(field) is not None
                    and a[field] != q["metadata"][field]
                ):
                    issues.append(
                        finding(
                            "identity_metadata_conflict",
                            f"Conflicting {field} metadata",
                            key,
                        )
                    )
            for warning in a.get("warnings", []):
                if warning.startswith(
                    ("explanation_boundary_unresolved", "malformed_question_header")
                ):
                    issues.append(
                        finding("explanation_boundary_unresolved", warning, key)
                    )
            status = "conflict" if issues else "matched"
        q_item = qs[0] if len(qs) == 1 else None
        a_item = ans[0] if len(ans) == 1 else None
        if a_item:
            for warning in a_item["record"].get("warnings", []):
                if not warning.startswith(
                    ("explanation_boundary_unresolved", "malformed_question_header")
                ):
                    issues.append(finding(warning.split(":")[0], warning, key))
        final_explanation = build_final_explanation(
            a_item["record"] if a_item else None,
            a_item["reference"] if a_item else None,
        )
        issues.extend(
            finding(
                item["code"],
                item["reason"],
                key,
                **(
                    {"source_pointer": item["source_pointer"]}
                    if item.get("source_pointer")
                    else {}
                ),
            )
            for item in final_explanation["issues"]
        )
        for issue in issues:
            issue["question_source"] = (
                q_item["document"].get("input") if q_item else None
            )
            issue["answer_source"] = a_item["document"] if a_item else None
            issue["answer_pages"] = (
                a_item["record"].get("page_reference") if a_item else None
            )
        record = {
            "identity": {"year": key[0], "section": key[1], "question_number": key[2]},
            "status": status,
            "correct_answer": a_item["record"]["correct_answer"]
            if status == "matched"
            else None,
            "question": deepcopy(q_item["record"]) if q_item else None,
            "answer": deepcopy(a_item["record"]) if a_item else None,
            "final_explanation": final_explanation,
            "question_reference": q_item["reference"] if q_item else None,
            "answer_reference": a_item["reference"] if a_item else None,
            "question_document": deepcopy(q_item["document"]) if q_item else None,
            "question_candidates": deepcopy(qs) if len(qs) > 1 else [],
            "answer_candidates": deepcopy(ans) if len(ans) > 1 else [],
            "matching": {
                "confidence": "exact_core_identity" if status == "matched" else None,
                **(
                    {
                        "source_question_verified": verify_question_evidence(
                            a_item["record"], q_item["record"]
                        )
                    }
                    if a_item
                    and q_item
                    and a_item["record"].get("question_evidence") is not None
                    else {}
                ),
                "paper_variant_verified": bool(
                    a_item
                    and a_item["record"].get("paper")
                    and a_item["record"].get("variant")
                ),
                "upstream_review_required": bool(
                    q_item
                    and (
                        q_item["record"]["cleaning_issues"]
                        or any(
                            "requires_review" in w
                            or "uncertain" in w
                            or "not_resolved" in w
                            for w in q_item["record"]["raw_warnings"]
                        )
                        or any(
                            x.get("warnings") for x in q_item["record"]["visual_assets"]
                        )
                    )
                ),
            },
            "issues": issues,
        }
        if superseded:
            record["superseded_answer_candidates"] = deepcopy(superseded)
        output["records"].append(record)
        output["issues"].extend(issues)
    for side, item, code in invalid:
        issue = finding(
            code,
            "Invalid/missing matching identity or excluded section; record preserved",
            source_json=item["reference"]["path"],
        )
        output["records"].append(
            {
                "identity": {
                    "year": item["record"].get("year"),
                    "section": item["record"].get("section"),
                    "question_number": item["record"].get("question_number"),
                },
                "status": "conflict",
                "question": item["record"] if side == "question" else None,
                "answer": item["record"] if side == "answer" else None,
                "final_explanation": build_final_explanation(
                    item["record"] if side == "answer" else None,
                    item["reference"] if side == "answer" else None,
                ),
                "correct_answer": None,
                "question_reference": item["reference"] if side == "question" else None,
                "answer_reference": item["reference"] if side == "answer" else None,
                "question_document": item["document"] if side == "question" else None,
                "matching": {"confidence": None},
                "issues": [issue],
            }
        )
        output["issues"].append(issue)
    return output
