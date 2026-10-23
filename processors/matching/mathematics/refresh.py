"""Refresh selected matching rows from current RAW after independent key verification."""

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from processors.stage_artifacts import write_stage_pair

from .core import build, load, write

ROOT = Path(__file__).resolve().parents[3]


def refresh(merged, raw_path, supplied_key, question_numbers):
    """Rebuild content, options, issues and references; never just replace hashes.

    The independently supplied key must agree with every native key entry. A
    conflict aborts before persistence, so it cannot silently overwrite an answer.
    """
    raw_path = Path(raw_path).resolve()
    raw = load(raw_path)
    source = raw["source_document"]
    if (
        supplied_key["source_document_id"] != source["id"]
        or supplied_key["source_pdf"] != source["filename"]
    ):
        raise ValueError("Supplied answer source identifies a different document")
    image = supplied_key["image"]
    if sha256((ROOT / image["path"]).read_bytes()).hexdigest() != image["sha256"]:
        raise ValueError("Authoritative answer image changed")
    answers = {int(n): answer for n, answer in supplied_key["answers"].items()}
    native = raw["answer_key"]["entries"]
    if len({e["question_number"] for e in native}) != len(native):
        raise ValueError("Duplicate native key entries")
    if answers != {e["question_number"]: e["correct_answer"] for e in native}:
        raise ValueError("Authoritative image transcription conflicts with native key")

    rebuilt = build([raw_path])
    current = {row["question_number"]: row for row in rebuilt["questions"]}
    selected = set(question_numbers)
    if not selected or not selected <= current.keys():
        raise ValueError("Question selection is empty or absent from current RAW")
    old = {
        row["question_number"]: row
        for row in merged["questions"]
        if row["source_document_id"] == source["id"]
    }
    if set(old) != set(current):
        raise ValueError("Existing matching identities disagree with current RAW")
    corrected_answers = []
    for number in sorted(selected):
        row = current[number]
        labels = [option["label"] for option in row["options"]]
        if (
            row["id"] != old[number]["id"]
            or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)])
            or len(labels) < 2
            or any(not option["content"] for option in row["options"])
            or row["matching"]["status"] != "matched"
            or row["correct_answer"] != answers[number]
        ):
            raise ValueError(f"Current RAW/options cannot validate Q{number}")
        if row["correct_answer"] != old[number].get("correct_answer"):
            corrected_answers.append(number)

    result = deepcopy(merged)
    replacements = {current[n]["id"]: current[n] for n in selected}
    result["questions"] = [replacements.get(q["id"], q) for q in result["questions"]]
    ids = [q["id"] for q in result["questions"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate matching IDs")
    raw_reference = rebuilt["inputs"][0]
    result["inputs"] = [
        raw_reference if Path(ref["path"]).resolve() == raw_path else ref
        for ref in result["inputs"]
    ]
    if raw_reference not in result["inputs"]:
        raise ValueError("Current source is not an existing matching input")
    result["summary"].update(
        matched=sum(q["matching"]["status"] == "matched" for q in result["questions"]),
        issue_questions=sum(bool(q["issues"]) for q in result["questions"]),
        issues_by_code=dict(
            sorted(
                Counter(
                    i["code"] for q in result["questions"] for i in q["issues"]
                ).items()
            )
        ),
    )
    validation = {
        "domain": "mathematics",
        "stage": "mathematics_matching_refresh_validation",
        "source_document_id": source["id"],
        "source_pdf": source["filename"],
        "authority": supplied_key,
        "raw_reference": raw_reference,
        "selected_question_numbers": sorted(selected),
        "verified_answers": len(answers),
        "repaired_records": len(selected),
        "corrected_answers": corrected_answers,
        "issues": [
            {"id": current[n]["id"], "question_number": n, **issue}
            for n in sorted(selected)
            for issue in current[n]["issues"]
        ],
    }
    return result, validation


def generate_artifacts(validation, docs_dir):
    name = validation["source_pdf"]
    back = [
        f"# {name} MATCHING backtesting",
        "",
        "Generated from canonical matching and scoped refresh validation JSON.",
        "",
        f"Revalidated matching records: {validation['repaired_records']}",
        f"Answers verified against supplied key: {validation['verified_answers']}",
        f"Changed answer values: {len(validation['corrected_answers'])}",
        "Selected question numbers: "
        + ", ".join(map(str, validation["selected_question_numbers"])),
        "Current RAW content, options and native-key references were rebuilt with the existing matcher.",
        "Unselected records were preserved.",
    ]
    issues = [
        f"# {name} MATCHING issues",
        "",
        "Generated from scoped structured matching validation.",
        "",
        f"Total issues: {len(validation['issues'])}",
        "",
    ]
    for issue in validation["issues"]:
        issues.append(
            f"- {name} Q{issue['question_number']} ({issue['id']}): "
            f"{issue['code']} — {issue['reason']}"
        )
    if not validation["issues"]:
        issues.append("No unresolved matching issues in the refreshed selection.")
    return write_stage_pair(
        docs_dir, "MATCHING", tuple("\n".join(lines) + "\n" for lines in (back, issues))
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--answer-key", type=Path, required=True)
    parser.add_argument("--question", type=int, action="append", required=True)
    parser.add_argument(
        "--merged", type=Path, default=ROOT / "data/merged/mathematics/questions.json"
    )
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--docs-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    result, validation = refresh(
        load(args.merged), args.raw, load(args.answer_key), args.question
    )
    write(args.merged, result)
    write(args.validation, validation)
    generate_artifacts(load(args.validation), args.docs_dir)
    print(
        {
            k: validation[k]
            for k in ("repaired_records", "verified_answers", "corrected_answers")
        }
    )
    return 0 if not validation["issues"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
