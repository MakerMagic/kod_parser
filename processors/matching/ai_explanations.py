"""Strict text-only explanation overlay for already matched records.

This module deliberately does not parse PDFs or alter clean/raw question data.
It accepts independently generated candidate explanations, validates them against
the matched question, and writes a separate matched snapshot.  A candidate that
does not satisfy the quality contract remains a review item rather than becoming
an explanation merely to improve a completion count.
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from .storage import load_matched, protect_output

MAXIMUM_CHARACTERS = 2000
GENERATION_FORMAT = "text_only_explanation_v2"
_VISUAL_TERMS = re.compile(
    r"\b(?:diagram|graph|chart|table|figure|image|picture|illustration|"
    r"map|shown below|see below|as shown)\b",
    re.IGNORECASE,
)
_GENERIC_REASONS = {
    "it is incorrect.",
    "this option is incorrect.",
    "it does not fit.",
    "it is irrelevant.",
    "it contradicts the passage.",
}


def _plain(value):
    return " ".join(str(value or "").split())


def _identity(record):
    identity = record.get("identity") or {}
    return (
        identity.get("year"),
        identity.get("section"),
        identity.get("question_number"),
    )


def _key(identity):
    return "|".join(str(value) for value in identity)


def _has_visual_dependency(question):
    if not question:
        return True
    if question.get("visual_assets") or question.get("images"):
        return True
    if any(option.get("images") for option in question.get("options", [])):
        return True
    if any(block.get("type") == "visual" for block in question.get("main_body", [])):
        return True
    text = "\n".join(
        [
            question.get("question_text", ""),
            question.get("main_question", ""),
            *[block.get("text", "") for block in question.get("main_body", [])],
        ]
    )
    return bool(_VISUAL_TERMS.search(text))


def eligibility(record):
    """Classify one record without claiming that an unresolved record is usable."""
    final = record.get("final_explanation") or {}
    if final.get("status") == "available" and final.get("blocks"):
        return (
            "existing_source_explanation",
            "A source or approved manual explanation exists.",
        )
    if record.get("status") != "matched":
        return (
            "skipped_missing_or_uncertain_correct_answer",
            "The matching record is not an exact usable match.",
        )
    question = record.get("question") or {}
    correct = record.get("correct_answer")
    options = question.get("options") or []
    labels = [option.get("label") for option in options]
    if not isinstance(correct, str) or labels.count(correct) != 1:
        return (
            "skipped_missing_or_uncertain_correct_answer",
            "No unique stored correct option is available.",
        )
    if _has_visual_dependency(question):
        return (
            "skipped_visual_dependency",
            "A visual asset or visual reference is needed by this question.",
        )
    if (
        question.get("cleaning_issues")
        or question.get("raw_warnings")
        or not _plain(question.get("main_question") or question.get("question_text"))
        or len(options) < 2
        or any(
            not isinstance(option.get("label"), str)
            or not _plain(option.get("text"))
            or option.get("warnings")
            for option in options
        )
    ):
        return (
            "skipped_missing_or_incomplete_question",
            "Question text, option text, or upstream structure is unresolved.",
        )
    return (
        "eligible",
        "Matched, text-only question with complete text options and a unique answer.",
    )


def _reason_is_substantive(reason):
    compact = _plain(reason)
    words = re.findall(r"[A-Za-z0-9]+", compact)
    return (
        len(words) >= 9
        and len(compact) >= 50
        and compact.casefold() not in _GENERIC_REASONS
    )


def _candidate_parts(candidate):
    if not isinstance(candidate, dict):
        return None, None
    main = candidate.get("main_reasoning")
    reasons = candidate.get("incorrect_options")
    return main, reasons


def validate_candidate(record, candidate):
    """Return deterministic validation findings; never rewrite candidate text."""
    errors = []
    status, reason = eligibility(record)
    if status != "eligible":
        return [f"record_not_eligible:{status}:{reason}"]
    main, reasons = _candidate_parts(candidate)
    if not isinstance(main, str) or not _reason_is_substantive(main):
        errors.append("main_reasoning_not_substantive")
    if not isinstance(reasons, list):
        return [*errors, "incorrect_options_not_a_list"]
    expected = [
        option["label"]
        for option in record["question"]["options"]
        if option["label"] != record["correct_answer"]
    ]
    received = [item.get("label") for item in reasons if isinstance(item, dict)]
    if sorted(received) != sorted(expected) or len(received) != len(set(received)):
        errors.append("incorrect_option_labels_do_not_match_question")
    normalized = []
    for item in reasons:
        if not isinstance(item, dict) or not _reason_is_substantive(item.get("reason")):
            errors.append("incorrect_option_reason_not_substantive")
            continue
        normalized.append(_plain(item["reason"]).casefold())
    if len(normalized) != len(set(normalized)):
        errors.append("incorrect_option_reasons_duplicated")
    count = len(_plain(main)) + sum(
        len(_plain(item.get("reason"))) for item in reasons if isinstance(item, dict)
    )
    if count > MAXIMUM_CHARACTERS:
        errors.append("explanation_exceeds_maximum_characters")
    return sorted(set(errors))


def candidate_to_final(candidate, source_reference):
    """Represent a validated candidate using the established Final Explanation blocks."""
    return {
        "status": "available",
        "ordering": "ai_generated_block_order",
        "blocks": [
            {
                "type": "paragraph",
                "role": "main",
                "order": 1,
                "text": candidate["main_reasoning"],
            },
            {
                "type": "list",
                "role": "incorrect_choices",
                "order": 2,
                "items": [
                    {"label": item["label"], "text": item["reason"]}
                    for item in candidate["incorrect_options"]
                ],
            },
        ],
        "unplaced_components": [],
        "omitted_artifacts": [],
        "deduplicated_blocks": [],
        "source_reference": deepcopy(source_reference),
        "source_warnings": [],
        "issues": [],
        "explanation_by_ai": True,
        "source_type": "ai_generated_text_only",
    }


def _source_reference(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}


def apply_candidates(data, candidates, candidate_path):
    """Return a separate snapshot and a complete generation audit.

    ``candidates`` is an iterable of reviewed generation results.  Unlisted
    eligible records are not treated as generated; they stay in the report as
    ``failed_generation_or_validation``.
    """
    output = deepcopy(data)
    source_reference = _source_reference(candidate_path)
    indexed = {}
    duplicates = set()
    for candidate in candidates:
        values = candidate.get("identity") if isinstance(candidate, dict) else None
        key = _key(
            (values or {}).get(name) for name in ("year", "section", "question_number")
        )
        if key in indexed:
            duplicates.add(key)
        indexed[key] = candidate
    audit = []
    for record in output["records"]:
        key_values = _identity(record)
        key = _key(key_values)
        status, reason = eligibility(record)
        candidate = indexed.get(key)
        errors = (
            ["duplicate_candidate_identity"]
            if key in duplicates
            else validate_candidate(record, candidate)
            if candidate is not None
            else []
        )
        item = {
            "identity": {
                "year": key_values[0],
                "section": key_values[1],
                "question_number": key_values[2],
            },
            "status": status,
            "reason": reason,
        }
        if status == "eligible" and candidate is not None and not errors:
            final = candidate_to_final(candidate, source_reference)
            record["final_explanation"] = final
            record["ai_explanation"] = {
                "generation_status": "generated",
                "explanation_by_ai": True,
                "source_type": "ai_generated_text_only",
                "source_reference": deepcopy(source_reference),
                "character_count": sum(
                    len(_plain(value))
                    for value in [
                        candidate["main_reasoning"],
                        *[entry["reason"] for entry in candidate["incorrect_options"]],
                    ]
                ),
            }
            item.update(
                status="successfully_generated",
                reason="Validated text-only AI explanation attached.",
            )
        elif status == "eligible":
            item.update(
                status="failed_generation_or_validation",
                reason="No candidate was supplied."
                if candidate is None
                else "; ".join(errors),
            )
            record["ai_explanation"] = {
                "generation_status": "failed_validation",
                "explanation_by_ai": False,
                "validation_errors": errors or ["candidate_not_supplied"],
            }
        else:
            record["ai_explanation"] = {
                "generation_status": status,
                "explanation_by_ai": False,
            }
        audit.append(item)
    output["ai_explanations"] = {
        "format": GENERATION_FORMAT,
        "source": source_reference,
        "maximum_characters": MAXIMUM_CHARACTERS,
        "status_counts": dict(Counter(item["status"] for item in audit)),
        "audit": audit,
    }
    return output


def write_report(data, output):
    audit = data.get("ai_explanations", {}).get("audit", [])
    groups = defaultdict(dict)
    for item in audit:
        key = tuple(
            item["identity"].get(name)
            for name in ("year", "section", "question_number")
        )
        groups[item["status"]][key] = item
    lines = [
        "<!-- tsa-ai-explanation-report -->",
        "# Text-only AI explanation generation",
        "",
        "This report is an eligibility and validation audit. A skipped or failed item has not acquired an AI explanation.",
        "",
    ]
    for category, rows in sorted(groups.items()):
        lines.extend(
            [f"## {category.replace('_', ' ').title()} ({len(rows)} questions)", ""]
        )
        for _, item in sorted(rows.items()):
            identity = item["identity"]
            lines.append(
                f"- {identity['year']} {identity['section']} Q{identity['question_number']}: {item['reason']}"
            )
        lines.append("")
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def audit_data(data):
    """Build a reportable eligibility snapshot without creating explanations."""
    audit = []
    for record in data["records"]:
        status, reason = eligibility(record)
        identity = _identity(record)
        audit.append(
            {
                "identity": {
                    "year": identity[0],
                    "section": identity[1],
                    "question_number": identity[2],
                },
                "status": "eligible_pending_generation"
                if status == "eligible"
                else status,
                "reason": reason,
            }
        )
    return {
        **deepcopy(data),
        "ai_explanations": {
            "format": GENERATION_FORMAT,
            "maximum_characters": MAXIMUM_CHARACTERS,
            "status_counts": dict(Counter(item["status"] for item in audit)),
            "audit": audit,
        },
    }


def _read_candidates(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != GENERATION_FORMAT:
        raise ValueError(f"Expected {GENERATION_FORMAT} candidate JSON")
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        raise TypeError("Candidate JSON must contain a candidates list")
    return candidates


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    apply = subparsers.add_parser(
        "apply", help="validate candidates into a separate matched snapshot"
    )
    apply.add_argument("--matched-json", type=Path, required=True)
    apply.add_argument("--candidates-json", type=Path, required=True)
    apply.add_argument("--output", type=Path, required=True)
    apply.add_argument("--report", type=Path, required=True)
    apply.add_argument("--overwrite", action="store_true")
    audit = subparsers.add_parser(
        "audit", help="write the text-only eligibility report"
    )
    audit.add_argument("--matched-json", type=Path, required=True)
    audit.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    data = load_matched(args.matched_json)
    if args.command == "audit":
        audited = audit_data(data)
        write_report(audited, args.report)
        print(audited["ai_explanations"]["status_counts"])
        return 0
    if args.output.exists() and not args.overwrite:
        raise ValueError("Output exists; use --overwrite or a new output path")
    protect_output(data, args.output, merged_json=args.matched_json)
    updated = apply_candidates(
        data, _read_candidates(args.candidates_json), args.candidates_json
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(updated, args.report)
    print(updated["ai_explanations"]["status_counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
