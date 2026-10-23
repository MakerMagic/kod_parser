"""Apply a source-authored mathematics answer key to selected matched records."""

import argparse
import json
import re
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from processors.stage_artifacts import validate_stage_pairs, write_stage_pair

from .core import build as build_matching
from .core import load, write

ROOT = Path(__file__).resolve().parents[3]
TEST_PATTERN = re.compile(r"^Test[_ ]?(\d+)\.pdf$", re.IGNORECASE)
SECTION_PATTERN = re.compile(r"(?im)^\s*Answers\s+to\s+test\s*#?\s*(\d+)\s*:\s*\r?$")
ANSWER_PATTERN = re.compile(r"(?m)^\s*(\d+)\s*\.?\s*([A-E])\s*$", re.IGNORECASE)


def parse_answer_file(path):
    """Parse and strictly validate all eight 30-answer sections."""
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    sections = list(SECTION_PATTERN.finditer(text))
    answers = {}
    for index, section in enumerate(sections):
        test_number = int(section.group(1))
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        body = text[section.end() : end]
        rows = {}
        for question, label in ANSWER_PATTERN.findall(body):
            number = int(question)
            if number in rows:
                raise ValueError(f"Duplicate answer for Test {test_number} Q{number}")
            rows[number] = label.upper()
        if set(rows) != set(range(1, 31)):
            missing = sorted(set(range(1, 31)) - set(rows))
            extra = sorted(set(rows) - set(range(1, 31)))
            raise ValueError(
                f"Test {test_number} answer coverage invalid; missing={missing}, extra={extra}"
            )
        if test_number in answers:
            raise ValueError(f"Duplicate answer section for Test {test_number}")
        answers[test_number] = rows
    if set(answers) != set(range(1, 9)):
        raise ValueError("Answers 1-8 must contain exactly Test 1 through Test 8")
    return answers


def build_answer_key(answer_path, merged):
    answer_path = Path(answer_path).resolve()
    answers = parse_answer_file(answer_path)
    root = ROOT.resolve()
    try:
        source_path = answer_path.relative_to(root).as_posix()
    except ValueError as error:
        raise ValueError(
            "Authoritative answer file must be within the project"
        ) from error
    sources = {}
    for source_id, source in merged["sources"].items():
        match = TEST_PATTERN.fullmatch(source["filename"])
        if match:
            number = int(match.group(1))
            if number in sources:
                raise ValueError(f"Multiple RAW sources identify Test {number}")
            sources[number] = (source_id, source["filename"])
    if set(sources) != set(range(1, 9)):
        raise ValueError("Matched data must contain exactly the eight Test sources")
    entries = []
    for test_number in range(1, 9):
        source_id, source_pdf = sources[test_number]
        for question_number in range(1, 31):
            entries.append(
                {
                    "source_document_id": source_id,
                    "source_pdf": source_pdf,
                    "test_number": test_number,
                    "question_number": question_number,
                    "correct_answer": answers[test_number][question_number],
                }
            )
    return {
        "domain": "mathematics",
        "stage": "mathematics_supplied_answer_key",
        "schema_version": "1",
        "authority": "Answers 1-8",
        "source_file": {
            "path": source_path,
            "sha256": sha256(answer_path.read_bytes()).hexdigest(),
        },
        "entries": entries,
    }


def answer_reference(path, data, index):
    return {
        "path": Path(path).resolve().relative_to(ROOT.resolve()).as_posix(),
        "sha256": sha256(Path(path).read_bytes()).hexdigest(),
        "json_pointer": f"/entries/{index}",
    }


def update_matching(merged, key_data, key_path):
    """Return an updated full matching projection and a scoped validation record."""
    result = deepcopy(merged)
    entry_indexes = {
        (entry["source_document_id"], entry["question_number"]): index
        for index, entry in enumerate(key_data["entries"])
    }
    if len(entry_indexes) != len(key_data["entries"]):
        raise ValueError(
            "Supplied answer key contains duplicate source/question mappings"
        )
    observed = {
        (row["source_document_id"], row["question_number"])
        for row in result["questions"]
        if (row["source_document_id"], row["question_number"]) in entry_indexes
    }
    if observed != set(entry_indexes):
        raise ValueError(
            "Supplied answer key does not map one-to-one to merged questions"
        )
    counts = Counter()
    affected = []
    for row in result["questions"]:
        identity = (row["source_document_id"], row["question_number"])
        if identity not in entry_indexes:
            continue
        index = entry_indexes[identity]
        entry = key_data["entries"][index]
        ref = answer_reference(key_path, key_data, index)
        labels = [option.get("label") for option in row.get("options", [])]
        complete_options = (
            bool(labels)
            and len(labels) == len(set(labels))
            and all(bool(option.get("content")) for option in row.get("options", []))
        )
        if not complete_options or entry["correct_answer"] not in labels:
            if not complete_options:
                reason = (
                    f"Answers 1-8 maps {entry['source_pdf']} Q{entry['question_number']} "
                    f"to {entry['correct_answer']}, but canonical RAW has no complete "
                    "extracted answer-option set, so the answer label cannot be validated "
                    "against this question."
                )
                counts["unmatched_missing_options"] += 1
            else:
                reason = (
                    f"Answers 1-8 maps {entry['source_pdf']} Q{entry['question_number']} "
                    f"to {entry['correct_answer']}, but that label is absent from the "
                    f"canonical ordered options ({', '.join(labels)})."
                )
                counts["unmatched_label_not_present"] += 1
            row["correct_answer"] = None
            row["matching"] = {
                "status": "unmatched",
                "method": "supplied_test_answer_key_by_source_and_question",
                "key_reference": None,
                "candidate_answer": entry["correct_answer"],
                "candidate_key_reference": ref,
                "issues": [{"code": "answer_matching", "reason": reason}],
            }
            row["issues"] = [
                issue
                for issue in row.get("issues", [])
                if issue.get("code") != "answer_matching"
            ] + row["matching"]["issues"]
            affected.append(
                {
                    "id": row["id"],
                    "source_pdf": entry["source_pdf"],
                    "question_number": entry["question_number"],
                    "state": "unmatched",
                    "candidate_answer": entry["correct_answer"],
                    "reason": reason,
                }
            )
            continue

        previous = row.get("correct_answer")
        preserved = (
            row.get("matching", {}).get("status") == "matched"
            and previous == entry["correct_answer"]
        )
        row["correct_answer"] = entry["correct_answer"]
        row["matching"] = {
            "status": "matched",
            "method": "supplied_test_answer_key_by_source_and_question",
            "key_reference": ref,
            "issues": [],
        }
        row["issues"] = [
            issue
            for issue in row.get("issues", [])
            if issue.get("code") != "answer_matching"
        ]
        counts["already_valid_preserved" if preserved else "newly_matched"] += 1

    result["external_answer_key"] = {
        "authority": key_data["authority"],
        "source_file": key_data["source_file"],
        "structured_path": Path(key_path)
        .resolve()
        .relative_to(ROOT.resolve())
        .as_posix(),
        "structured_sha256": sha256(Path(key_path).read_bytes()).hexdigest(),
    }
    result["summary"]["matched"] = sum(
        row.get("matching", {}).get("status") == "matched"
        for row in result["questions"]
    )
    result["summary"]["issue_questions"] = sum(
        bool(row.get("issues")) for row in result["questions"]
    )
    result["summary"]["issues_by_code"] = dict(
        sorted(
            Counter(
                issue["code"]
                for row in result["questions"]
                for issue in row.get("issues", [])
            ).items()
        )
    )
    result["summary"]["supplied_answer_key_entries"] = len(key_data["entries"])
    result["summary"]["supplied_answer_key_matched"] = sum(
        counts[key] for key in ("newly_matched", "already_valid_preserved")
    )
    result["summary"]["supplied_answer_key_unmatched"] = len(affected)
    selected = [
        row
        for row in result["questions"]
        if (row["source_document_id"], row["question_number"]) in entry_indexes
    ]
    per_source = {}
    for source_id, source in sorted(result["sources"].items()):
        rows = [row for row in selected if row["source_document_id"] == source_id]
        if rows:
            per_source[source["filename"]] = {
                "questions": len(rows),
                "matched": sum(row["matching"]["status"] == "matched" for row in rows),
                "unmatched": sum(
                    row["matching"]["status"] != "matched" for row in rows
                ),
            }
    validation = {
        "domain": "mathematics",
        "stage": "mathematics_matching_validation",
        "scope": "Test 1–8",
        "summary": {
            "questions": len(selected),
            "matched": sum(row["matching"]["status"] == "matched" for row in selected),
            "unmatched": len(affected),
            "by_source": per_source,
            "preserved_existing_matches": counts["already_valid_preserved"],
            "newly_matched": counts["newly_matched"],
        },
        "issues": affected,
    }
    return result, validation


def replace_test_sources(merged, rebuilt):
    """Replace only Test rows with a fresh projection of their current RAW data."""
    result = deepcopy(merged)
    source_ids = set(rebuilt["sources"])
    old_rows = {
        (row["source_document_id"], row["question_number"]): row
        for row in result["questions"]
        if row["source_document_id"] in source_ids
    }
    new_rows = {
        (row["source_document_id"], row["question_number"]): row
        for row in rebuilt["questions"]
    }
    if set(old_rows) != set(new_rows):
        raise ValueError("Current RAW source identities differ from existing Test rows")
    result["questions"] = [
        new_rows.get((row["source_document_id"], row["question_number"]), row)
        for row in result["questions"]
    ]
    for source_id, source in rebuilt["sources"].items():
        result["sources"][source_id] = source
    old_raw_paths = {
        row.get("raw_reference", {}).get("path")
        for row in old_rows.values()
        if row.get("raw_reference")
    }
    result["inputs"] = [
        ref for ref in result["inputs"] if ref.get("path") not in old_raw_paths
    ] + rebuilt["inputs"]
    result["source_issues"] = [
        issue
        for issue in result.get("source_issues", [])
        if issue.get("source_document_id") not in source_ids
    ] + rebuilt["source_issues"]
    result["orphan_key_entries"] = [
        issue
        for issue in result.get("orphan_key_entries", [])
        if issue.get("source_document_id") not in source_ids
    ] + rebuilt["orphan_key_entries"]
    result["inputs"] = sorted(result["inputs"], key=lambda ref: ref["path"])
    result["sources"] = dict(sorted(result["sources"].items()))
    result["summary"] = {
        "sources": len(result["sources"]),
        "questions": len(result["questions"]),
        "answer_key_entries": sum(
            source["key_count"] for source in result["sources"].values()
        ),
        "matched": sum(
            row["matching"]["status"] == "matched" for row in result["questions"]
        ),
        "issue_questions": sum(bool(row.get("issues")) for row in result["questions"]),
        "issues_by_code": dict(
            sorted(
                Counter(
                    issue["code"]
                    for row in result["questions"]
                    for issue in row.get("issues", [])
                ).items()
            )
        ),
        "orphan_key_entries": len(result["orphan_key_entries"]),
    }
    return result


def validate_update(merged, validation, key_data, key_path, raw_paths):
    """Validate source-key coverage, current RAW projection and match decisions."""
    expected = {
        (entry["source_document_id"], entry["question_number"]): (index, entry)
        for index, entry in enumerate(key_data["entries"])
    }
    if len(expected) != 240:
        raise ValueError("Expected 240 unique Test 1–8 answer mappings")
    current = {}
    for raw_path in raw_paths:
        raw = load(raw_path)
        if raw["source_document"]["filename"] not in {
            entry["source_pdf"] for entry in key_data["entries"]
        }:
            raise ValueError("Unexpected RAW source in scoped matching inputs")
        reference = {
            "path": Path(raw_path).resolve().as_posix(),
            "sha256": sha256(Path(raw_path).read_bytes()).hexdigest(),
        }
        for index, raw_row in enumerate(raw["questions"]):
            current[(raw_row["source_document_id"], raw_row["question_number"])] = (
                raw_row,
                {**reference, "json_pointer": f"/questions/{index}"},
            )
    rows = {
        (row["source_document_id"], row["question_number"]): row
        for row in merged["questions"]
        if (row["source_document_id"], row["question_number"]) in expected
    }
    if set(rows) != set(expected) or set(current) != set(expected):
        raise ValueError(
            "Matching projection, RAW and key do not have identical coverage"
        )
    path_rel = Path(key_path).resolve().relative_to(ROOT.resolve()).as_posix()
    key_hash = sha256(Path(key_path).read_bytes()).hexdigest()
    for identity, (index, entry) in expected.items():
        row, raw_pair = rows[identity], current[identity]
        raw_row, raw_ref = raw_pair
        for field in (
            "id",
            "source_document_id",
            "question_number",
            "regions",
            "content",
            "options",
            "assets",
            "raw",
            "extraction_status",
        ):
            if row.get(field) != raw_row.get(field):
                raise ValueError(
                    f"Matched {field} differs from current RAW for {identity}"
                )
        raw_issues = [
            issue
            for issue in row.get("issues", [])
            if issue.get("code") != "answer_matching"
        ]
        if raw_issues != raw_row.get("issues", []) or row["raw_reference"] != raw_ref:
            raise ValueError(f"RAW provenance/issues differ for {identity}")
        labels = [option["label"] for option in row["options"]]
        expected_ref = {
            "path": path_rel,
            "sha256": key_hash,
            "json_pointer": f"/entries/{index}",
        }
        if row["matching"]["status"] == "matched":
            if (
                row["correct_answer"] != entry["correct_answer"]
                or entry["correct_answer"] not in labels
            ):
                raise ValueError(
                    f"Matched answer is not supported by options for {identity}"
                )
            if row["matching"].get("key_reference") != expected_ref:
                raise ValueError(f"Matched answer key reference differs for {identity}")
        elif (
            row.get("correct_answer") is not None
            or row["matching"].get("candidate_answer") != entry["correct_answer"]
            or row["matching"].get("candidate_key_reference") != expected_ref
            or not row["matching"].get("issues")
        ):
            raise ValueError(f"Unmatched mapping is not traceable for {identity}")
    if (
        validation["summary"]["questions"] != 240
        or validation["summary"]["matched"] + validation["summary"]["unmatched"] != 240
        or len(validation["issues"]) != validation["summary"]["unmatched"]
    ):
        raise ValueError("Scoped matching validation totals disagree")
    return True


def render_artifacts(merged, validation):
    sources = merged["sources"]
    rows = [
        row
        for row in merged["questions"]
        if row["source_document_id"] in sources
        and TEST_PATTERN.fullmatch(sources[row["source_document_id"]]["filename"])
    ]
    rows.sort(
        key=lambda row: (
            sources[row["source_document_id"]]["filename"],
            row["question_number"],
        )
    )
    summary = validation["summary"]
    if (
        len(rows) != summary["questions"]
        or sum(row["matching"]["status"] == "matched" for row in rows)
        != summary["matched"]
        or len(validation["issues"]) != summary["unmatched"]
    ):
        raise ValueError("Scoped MATCHING counts disagree with canonical records")
    issue_ids = {issue["id"] for issue in validation["issues"]}
    if len(issue_ids) != len(validation["issues"]) or issue_ids != {
        row["id"] for row in rows if row["matching"]["status"] != "matched"
    }:
        raise ValueError("Scoped MATCHING issues do not cover every unmatched record")
    back = [
        "# Mathematics second-set MATCHING backtesting",
        "",
        "Generated from canonical `data/merged/mathematics/questions.json` and its scoped structured validation.",
        "The answer source is `Answers 1-8`; inspect JSON for individual question data.",
        "",
        f"Questions: {summary['questions']}",
        f"Matched: {summary['matched']}",
        f"Unmatched: {summary['unmatched']}",
        f"Existing valid matches preserved: {summary['preserved_existing_matches']}",
        "",
        "## By test",
        "",
    ]
    for name, counts in summary["by_source"].items():
        back.append(
            f"- {name}: {counts['matched']} matched / {counts['questions']} questions; {counts['unmatched']} unmatched"
        )
    back += [
        "",
        "## Unmatched mappings",
        "",
        "The answer key label is retained as an unvalidated candidate; it is not exposed as `correct_answer` until options can validate it.",
        "",
    ]
    for issue in validation["issues"]:
        back.append(
            f"- {issue['source_pdf']} Q{issue['question_number']}: candidate {issue['candidate_answer']} (see MATCHING_ISSUES.md)."
        )
    issue_md = [
        "# Mathematics second-set MATCHING issues",
        "",
        "Generated from the scoped structured matching validation; canonical matched JSON remains authoritative.",
        "",
        f"Total issues: {len(validation['issues'])}",
        f"Unmatched questions: {summary['unmatched']}",
        "",
    ]
    if not validation["issues"]:
        issue_md.append("No unresolved matching issues currently exist for Test 1–8.")
    for issue in validation["issues"]:
        issue_md += [
            f"## {issue['source_pdf']} — Q{issue['question_number']} — {issue['id']}",
            "",
            f"State: {issue['state']}; candidate answer from Answers 1-8: `{issue['candidate_answer']}`.",
            f"Exact reason: {issue['reason']}",
            "",
        ]
    return "\n".join(back).rstrip() + "\n", "\n".join(issue_md).rstrip() + "\n"


def generate_artifacts(merged_path, validation_path, docs_dir):
    merged, validation = load(merged_path), load(validation_path)
    expected = render_artifacts(merged, validation)
    paths = write_stage_pair(docs_dir, "MATCHING", expected)
    validate_stage_pairs([(docs_dir, "MATCHING", render_artifacts(merged, validation))])
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=ROOT / "data/merged/mathematics/questions.json"
    )
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/mathematics")
    parser.add_argument(
        "--answer-file",
        type=Path,
        default=ROOT / "acquisition/local/mathematics/sky (trial)/Answers 1-8.txt",
    )
    parser.add_argument(
        "--key-output",
        type=Path,
        default=ROOT / "data/merged/mathematics/second_set_answer_key.json",
    )
    parser.add_argument(
        "--validation-output",
        type=Path,
        default=ROOT / "data/merged/mathematics/second_set_validation.json",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data/merged/mathematics/questions.json"
    )
    parser.add_argument(
        "--docs-dir", type=Path, default=ROOT / "docs/mathematics/second_set"
    )
    args = parser.parse_args(argv)
    merged = load(args.input)
    raw_paths = sorted(args.raw_dir.glob("Test_*.raw.json"))
    if len(raw_paths) != 8:
        raise ValueError(
            f"Expected eight current Test RAW files, found {len(raw_paths)}"
        )
    rebuilt = replace_test_sources(merged, build_matching(raw_paths))
    key_data = build_answer_key(args.answer_file, rebuilt)
    write(args.key_output, key_data)
    updated, validation = update_matching(rebuilt, key_data, args.key_output)
    validate_update(updated, validation, key_data, args.key_output, raw_paths)
    write(args.output, updated)
    write(args.validation_output, validation)
    paths = generate_artifacts(args.output, args.validation_output, args.docs_dir)
    print(json.dumps(validation["summary"], ensure_ascii=False, sort_keys=True))
    print("\n".join(str(path) for path in paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
