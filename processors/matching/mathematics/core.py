"""Exact source-content identity + question number, independent of PDF parsing."""

import json
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from parsers.mathematics.structure import walk


def load(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = load(path)
        if old.get("domain") != "mathematics" or old.get("stage") != data.get("stage"):
            raise ValueError("Refusing unrelated domain/stage output")
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
        newline="\n",
    )


def match_document(raw, reference):
    if raw.get("stage") != "mathematics_raw" or raw.get("domain") != "mathematics":
        raise ValueError("Mathematics matcher requires mathematics RAW JSON")
    rows = defaultdict(list)
    for i, a in enumerate(raw["answer_key"]["entries"]):
        rows[a["question_number"]].append((i, a))
    records = []
    for index, q in enumerate(raw["questions"]):
        row = deepcopy(q)
        row["raw_reference"] = {**reference, "json_pointer": f"/questions/{index}"}
        candidates = rows[q["question_number"]]
        status = "matched"
        answer = None
        ref = None
        issues = []
        if len(candidates) != 1:
            status = "ambiguous" if candidates else "unmatched"
            issues.append(
                {
                    "code": "answer_matching",
                    "reason": "Duplicate key rows"
                    if candidates
                    else "No source key row",
                    "question_number": q["question_number"],
                }
            )
        else:
            ki, a = candidates[0]
            labels = [o["label"] for o in q["options"]]
            if (
                len(labels) != len(set(labels))
                or a["correct_answer"] not in labels
                or any(o.get("content") == [] for o in q["options"])
            ):
                status = "unmatched"
                issues.append(
                    {
                        "code": "answer_matching",
                        "reason": "Source answer cannot be validated against complete extracted options",
                        "question_number": q["question_number"],
                    }
                )
            else:
                answer = a["correct_answer"]
                ref = {**reference, "json_pointer": f"/answer_key/entries/{ki}"}
        row["correct_answer"] = answer
        row["matching"] = {
            "status": status,
            "method": "exact_source_sha256_question_number",
            "key_reference": ref,
            "issues": issues,
        }
        row["issues"].extend(issues)
        records.append(row)
    numbers = {q["question_number"] for q in raw["questions"]}
    orphan = [
        a
        for entries in rows.values()
        for _, a in entries
        if a["question_number"] not in numbers
    ]
    return records, orphan


def build(paths):
    questions = []
    sources = {}
    inputs = []
    orphans = []
    source_issues = []
    for path in sorted({Path(p).resolve() for p in paths}):
        raw = load(path)
        if raw.get("domain") != "mathematics" or raw.get("stage") != "mathematics_raw":
            raise ValueError("Mathematics matching accepts mathematics RAW only")
        ref = {"path": path.as_posix(), "sha256": sha256(path.read_bytes()).hexdigest()}
        source = raw["source_document"]
        if any(q["source_document_id"] != source["id"] for q in raw["questions"]):
            raise ValueError("Question/source-document identity mismatch")
        if source["id"] in sources:
            raise ValueError("Duplicate source document version")
        sources[source["id"]] = deepcopy(source)
        sources[source["id"]]["page_count"] = len(raw["pages"])
        sources[source["id"]]["roles"] = {
            str(p["page"]): p["role"] for p in raw["pages"]
        }
        sources[source["id"]]["key_count"] = len(raw["answer_key"]["entries"])
        inputs.append(ref)
        rows, unassigned = match_document(raw, ref)
        questions.extend(rows)
        orphans.extend({"source_document_id": source["id"], **a} for a in unassigned)
        source_issues.extend(
            {"source_document_id": source["id"], **i}
            for i in [*raw["issues"], *raw["answer_key"]["issues"]]
        )
    ids = [q["id"] for q in questions]
    identities = [(q["source_document_id"], q["question_number"]) for q in questions]
    if len(ids) != len(set(ids)) or len(identities) != len(set(identities)):
        raise ValueError("Duplicate mathematics identity")
    summary = {
        "sources": len(sources),
        "questions": len(questions),
        "answer_key_entries": sum(s["key_count"] for s in sources.values()),
        "matched": sum(q["matching"]["status"] == "matched" for q in questions),
        "issue_questions": sum(bool(q["issues"]) for q in questions),
        "issues_by_code": dict(
            Counter(i["code"] for q in questions for i in q["issues"])
        ),
        "orphan_key_entries": len(orphans),
    }
    source_names = {source["source"] for source in sources.values()}
    data = {
        "domain": "mathematics",
        "source": next(iter(source_names)) if len(source_names) == 1 else "multiple",
        "stage": "mathematics_matched",
        "schema_version": "2",
        "inputs": inputs,
        "sources": sources,
        "questions": questions,
        "orphan_key_entries": orphans,
        "source_issues": source_issues,
        "summary": summary,
    }
    return data


def validate(data):
    from parsers.mathematics.latex import validate as validate_latex

    problems = []
    by_source = {}
    ids = [q["id"] for q in data["questions"]]
    coverage = {}
    for ref in data["inputs"]:
        path = Path(ref["path"])
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
            problems.append({"path": ref["path"], "code": "raw_reference_changed"})
            continue
        raw = load(path)
        expected = set()
        for page in raw["pages"]:
            if page["role"] != "questions":
                continue
            for c in page["glyphs"]:
                if not c["text"].strip():
                    continue
                x, y = (c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2
                if not any(
                    e["bbox"][0] <= x < e["bbox"][2]
                    and e["bbox"][1] <= y < e["bbox"][3]
                    for e in page["exclusions"]
                ):
                    expected.add(c["id"])
        observed = Counter(g for q in raw["questions"] for g in q["raw"]["glyph_ids"])
        missing = sorted(expected - set(observed))
        duplicate = sorted(g for g, c in observed.items() if c > 1)
        qnumbers = {q["question_number"] for q in raw["questions"]}
        knumbers = {k["question_number"] for k in raw["answer_key"]["entries"]}
        filename = raw["source_document"]["filename"]
        coverage[filename] = {
            "expected_non_header_glyphs": len(expected),
            "unassigned_glyph_ids": missing,
            "duplicated_glyph_ids": duplicate,
            "question_numbers_without_key": sorted(qnumbers - knumbers),
            "key_numbers_without_question": sorted(knumbers - qnumbers),
        }
        if missing or duplicate or qnumbers != knumbers:
            problems.append({"source": filename, "code": "source_coverage"})
    for sid, source in data["sources"].items():
        qq = [q for q in data["questions"] if q["source_document_id"] == sid]
        by_source[source["filename"]] = {
            "questions": len(qq),
            "key_entries": source["key_count"],
            "matched": sum(q["matching"]["status"] == "matched" for q in qq),
            "issue_questions": sum(bool(q["issues"]) for q in qq),
            "cover_skipped": source["roles"]["1"] == "cover",
            "key_excluded": source["roles"][str(source["page_count"])] == "answer_key",
        }
        if len(qq) != source["key_count"]:
            problems.append(
                {"source": source["filename"], "code": "source_count_mismatch"}
            )
    formulas = 0
    for q in data["questions"]:
        content = [*q["content"], *[b for o in q["options"] for b in o["content"]]]
        for b in walk(content):
            if b["type"] == "math":
                formulas += 1
                if validate_latex(b["latex"]):
                    problems.append({"question_id": q["id"], "code": "malformed_latex"})
        if not q["raw_reference"] or not q["regions"] or not q["raw"]["glyph_ids"]:
            problems.append({"question_id": q["id"], "code": "source_traceability"})
        labels = [o["label"] for o in q["options"]]
        if len(labels) < 2 or labels != list(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]
        ):
            problems.append({"question_id": q["id"], "code": "option_structure"})
        if any(not o["content"] for o in q["options"]):
            problems.append({"question_id": q["id"], "code": "empty_option"})
    return {
        "domain": "mathematics",
        "stage": "mathematics_validation",
        "summary": data["summary"],
        "by_source": by_source,
        "latex_formulas": formulas,
        "source_coverage": coverage,
        "duplicate_ids": len(ids) - len(set(ids)),
        "problems": problems,
        "source_issues": data["source_issues"],
    }


def issue_summary(data, path):
    rows = [
        "# Mathematics extraction/matching issues",
        "",
        "Canonical source: `data/merged/mathematics/questions.json`. Counts below derive from unique structured question IDs; source/key issues remain separate.",
        "",
        f"Questions: {len(data['questions'])}; affected questions: {sum(bool(q['issues']) for q in data['questions'])}.",
        "",
        "| Code | Unique questions | Findings |",
        "|---|---:|---:|",
    ]
    codes = sorted({i["code"] for q in data["questions"] for i in q["issues"]})
    for code in codes:
        count = sum(
            any(i["code"] == code for i in q["issues"]) for q in data["questions"]
        )
        rows.append(
            f"| {code} | {count} | {sum(i['code'] == code for q in data['questions'] for i in q['issues'])} |"
        )
    rows.extend(
        [
            "",
            f"Source/key findings: {len(data['source_issues'])}; orphan key entries: {len(data['orphan_key_entries'])}.",
            "",
            "Select issue-bearing records from JSON or use the documented inspection command. Uncertain formulas retain their original source crop; no mathematical solving or replacement takes place.",
        ]
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(rows) + "\n", encoding="utf8")
