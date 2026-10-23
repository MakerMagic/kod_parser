"""Validate and publish directly authored mathematics explanations.

This module never calls a model or service. Explanation text is authored in the
separate canonical explanation output and this command validates its binding to
the read-only PRE-FINAL question data, then regenerates stage artifacts.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from .mathematics_latex import validate as validate_latex
from processors.stage_artifacts import write_stage_pair

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/pre_final/mathematics/questions.json"
OUTPUT = ROOT / "data/explanations/mathematics/explanations.json"
DOCS = ROOT / "docs/mathematics"
MAX_CHARACTERS = 2000


def _latex_errors(text):
    errors = []
    pattern = re.compile(r"\\\[(.*?)\\\]|\\\((.*?)\\\)", re.DOTALL)
    cursor = 0
    for match in pattern.finditer(text):
        prefix = text[cursor : match.start()]
        if any(mark in prefix for mark in (r"\[", r"\]", r"\(", r"\)")):
            errors.append("unmatched_math_delimiter")
        if re.search(r"\\[A-Za-z]+", prefix):
            errors.append("math_command_outside_math_delimiters")
        formula = match.group(1) if match.group(1) is not None else match.group(2)
        errors.extend("invalid_latex:" + error for error in validate_latex(formula))
        cursor = match.end()
    if any(mark in text[cursor:] for mark in (r"\[", r"\]", r"\(", r"\)")):
        errors.append("unmatched_math_delimiter")
    if re.search(r"\\[A-Za-z]+", text[cursor:]):
        errors.append("math_command_outside_math_delimiters")
    if text.count(r"\(") != text.count(r"\)") or text.count(r"\[") != text.count(r"\]"):
        errors.append("unmatched_math_delimiter")
    return sorted(set(errors))


def validate_question(question):
    required = {
        "id", "source_pdf", "question_number", "content_sha256", "main_body",
        "main_question", "main_answers", "correct_answer",
    }
    if not isinstance(question, dict) or required - question.keys():
        return "source_content_missing", "Required canonical PRE-FINAL fields are missing."
    answers = question.get("main_answers")
    if not isinstance(answers, list):
        return "source_content_invalid", "Canonical answer options are not a list."
    labels = [answer.get("label") for answer in answers if isinstance(answer, dict)]
    if len(labels) != len(answers) or labels.count(question["correct_answer"]) != 1:
        return "source_answer_invalid", "Stored correct answer does not identify exactly one supplied option."
    groups = [question["main_body"], question["main_question"] or []]
    groups.extend(answer.get("content") for answer in answers)
    if any(not isinstance(group, list) for group in groups):
        return "source_content_invalid", "Question fields do not follow the canonical ordered-block structure."
    if not any(block.get("type") in {"text", "math", "visual", "list"} for group in groups for block in group if isinstance(block, dict)):
        return "source_content_missing", "No question or answer content is available."
    return None


def validate_explanation(question, record):
    errors = []
    if not isinstance(record, dict):
        return ["invalid_explanation_record"]
    if record.get("id") != question.get("id"):
        errors.append("question_id_mismatch")
    if record.get("source_pdf") != question.get("source_pdf") or record.get("question_number") != question.get("question_number"):
        errors.append("question_provenance_mismatch")
    if record.get("content_sha256") != question.get("content_sha256"):
        errors.append("stale_question_content_hash")
    if record.get("correct_answer") != question.get("correct_answer"):
        errors.append("stored_answer_binding_mismatch")
    final = record.get("final_explanation")
    if not isinstance(final, dict):
        return errors + ["missing_final_explanation"]
    if final.get("explanation_by_ai") is not True:
        errors.append("missing_ai_provenance_flag")
    reference = final.get("source_reference")
    if not isinstance(reference, dict) or reference.get("stage") != "mathematics_pre_final" or reference.get("question_id") != question.get("id") or reference.get("content_sha256") != question.get("content_sha256"):
        errors.append("invalid_source_reference")
    blocks = final.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        return errors + ["empty_explanation"]
    texts = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "paragraph" or not isinstance(block.get("text"), str):
            errors.append("invalid_explanation_block")
        else:
            texts.append(block["text"])
    text = "\n\n".join(texts)
    if not text.strip():
        errors.append("empty_explanation")
    if len(text) > MAX_CHARACTERS:
        errors.append("explanation_exceeds_2000_characters")
    if re.search(r"(?<!\\)\$", text):
        errors.append("noncanonical_latex_delimiter")
    errors.extend(_latex_errors(text))
    if final.get("source_type") != "ai_generated_text_only":
        errors.append("invalid_explanation_source_type")
    return sorted(set(errors))


def build(data, *, existing=None, limit=None):
    if (
        data.get("domain") != "mathematics"
        or data.get("stage") != "mathematics_pre_final"
        or data.get("summary", {}).get("ready_for_rendering") is not True
        or data.get("summary", {}).get("blocking_issues")
    ):
        raise ValueError("Mathematics explanation publishing requires ready PRE-FINAL input")
    if not isinstance(existing, dict):
        existing = {"questions": []}
    authored = {row.get("id"): row for row in existing.get("questions", [])}
    if len(authored) != len(existing.get("questions", [])):
        raise ValueError("Duplicate explanation IDs; no record may overwrite another")
    prior_issues = {}
    for row in existing.get("issues", []):
        qid = row.get("id")
        if qid not in prior_issues or (
            prior_issues[qid].get("code") == "explanation_not_yet_authored"
            and row.get("code") != "explanation_not_yet_authored"
        ):
            prior_issues[qid] = row
    issues = []
    records = []
    questions = data["questions"][:limit]
    for question in questions:
        qid = question.get("id")
        common = {
            key: question.get(key)
            for key in ("id", "source_pdf", "question_number", "content_sha256")
        }
        input_issue = validate_question(question)
        if input_issue:
            code, reason = input_issue
            issues.append({**common, "code": code, "reason": reason})
            continue
        record = authored.get(qid)
        if record is None:
            prior_issue = prior_issues.get(qid)
            if prior_issue and prior_issue.get("content_sha256") == question.get("content_sha256"):
                if prior_issue.get("code") == "explanation_not_yet_authored":
                    issues.append({
                        **common,
                        "code": "explanation_not_yet_authored",
                        "reason": "No directly authored, source-checked explanation is stored. This stage validates and publishes authored content but does not generate it; the direct-authoring pass remains incomplete for this question. No answer was generated or inferred by software.",
                    })
                else:
                    issues.append(prior_issue)
            else:
                issues.append({
                    **common,
                    "code": "explanation_not_yet_authored",
                    "reason": "No directly authored, source-checked explanation is stored. This stage validates and publishes authored content but does not generate it; the direct-authoring pass remains incomplete for this question. No answer was generated or inferred by software.",
                })
            continue
        errors = validate_explanation(question, record)
        if errors:
            issues.append({
                **common,
                "code": "explanation_validation_failed",
                "reason": "Stored explanation failed: " + ", ".join(errors) + ".",
            })
            continue
        records.append(record)
    counts = Counter(issue["code"] for issue in issues)
    lengths = [
        sum(len(block["text"]) for block in row["final_explanation"]["blocks"])
        for row in records
    ]
    return {
        "domain": "mathematics",
        "stage": "mathematics_explanations",
        "schema_version": "1",
        "input": "data/pre_final/mathematics/questions.json",
        "questions": sorted(records, key=lambda row: row["id"]),
        "issues": sorted(issues, key=lambda row: row["id"]),
        "summary": {
            "input_questions": len(questions),
            "eligible_questions": len(questions)
            - sum(
                count
                for code, count in counts.items()
                if code not in {"explanation_not_yet_authored", "explanation_validation_failed"}
            ),
            "explanations_authored": len(records),
            "explanations_missing_or_invalid": len(issues),
            "issues_by_code": dict(sorted(counts.items())),
            "average_characters": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            "maximum_characters": max(lengths, default=0),
            "explanations_by_origin": dict(sorted(Counter(
                row.get("explanation_origin", "existing")
                for row in records
            ).items())),
        },
    }


def validate_complete(data, output):
    """Account for every input exactly once; missing-authoring is not blocking."""
    questions = {q["id"]: q for q in data["questions"]}
    if len(questions) != len(data["questions"]):
        raise ValueError("Duplicate input question IDs")
    records = output.get("questions", [])
    issues = output.get("issues", [])
    record_ids = [r["id"] for r in records]
    issue_ids = [r["id"] for r in issues]
    if len(set(record_ids)) != len(records) or len(set(issue_ids)) != len(issues):
        raise ValueError("Duplicate explanation or issue IDs")
    if set(record_ids) & set(issue_ids):
        raise ValueError("Question has both a valid explanation and a blocking issue")
    if set(record_ids) | set(issue_ids) != set(questions):
        raise ValueError("Explanation completeness: missing or unknown question IDs")
    for row in records:
        errors = validate_explanation(questions[row["id"]], row)
        if errors:
            raise ValueError(f"Invalid explanation {row['id']}: {errors}")
    for issue in issues:
        if (
            issue.get("blocking") is not True
            or issue.get("code") in {"explanation_not_yet_authored", "explanation_validation_failed"}
            or not issue.get("reason", "").strip()
            or issue.get("content_sha256") != questions[issue["id"]]["content_sha256"]
        ):
            raise ValueError(f"Unresolved authoring or unbound blocker: {issue['id']}")
    return {
        "total_questions": len(questions),
        "blocking_questions": len(issues),
        "eligible_questions": len(records),
        "eligible_without_explanation": 0,
    }


def artifacts(data):
    summary = data["summary"]
    backtesting = [
        "# Mathematics Explanation Backtesting", "",
        "Generated from reviewed AI explanation records bound to read-only PRE-FINAL content.", "",
        f"- PRE-FINAL questions checked: {summary['input_questions']}",
        f"- Explanations authored and validated: {summary['explanations_authored']}",
        f"- Missing or invalid explanations: {summary['explanations_missing_or_invalid']}",
        f"- Average explanation length: {summary['average_characters']} characters",
        f"- Maximum explanation length: {summary['maximum_characters']} characters",
        "- AI provenance flag: true for directly AI-authored explanations; no external model/provider is used by this stage.", "",
    ]
    for origin, count in summary.get("explanations_by_origin", {}).items():
        backtesting.append(f"- Explanation origin {origin}: {count}")
    backtesting.append("")
    for row in data["questions"]:
        final = row["final_explanation"]
        text = " ".join(block["text"].replace("\n", " ") for block in final["blocks"])
        backtesting.append(f"- `{row['source_pdf']}` Q{row['question_number']} — `{row['id']}` — {len(text)} chars; answer `{row['correct_answer']}`: {text}")
    issues = ["# Mathematics Explanation Issues", "", f"Total issues: {len(data['issues'])}", ""]
    for issue in data["issues"]:
        issues.append(f"- `{issue['source_pdf']}` Q{issue['question_number']} — `{issue['id']}` — `{issue['code']}`: {issue['reason']}")
    if not data["issues"]:
        issues.append("No unresolved explanation issues currently exist.")
    return "\n".join(backtesting) + "\n", "\n".join(issues) + "\n"


def save(data, output=OUTPUT, docs=DOCS):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    write_stage_pair(docs, "EXPLANATION", artifacts(data))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--docs-dir", type=Path, default=DOCS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args(argv)
    source = json.loads(args.input.read_text(encoding="utf8"))
    prior = json.loads(args.output.read_text(encoding="utf8")) if args.output.exists() else None
    result = build(source, existing=prior, limit=args.limit)
    if args.require_complete:
        if args.limit is not None:
            parser.error("--require-complete cannot use a population limit")
        validate_complete(source, result)
    save(result, args.output, args.docs_dir)
    print(json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
