"""Inspect stored raw questions and report detectable extraction issues."""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

from .visual_inspection import render_html, visual_issues

REPORT_MARKER = "<!-- blackstone-raw-backtest-report -->"
INFORMATIONAL_WARNINGS = {
    "graphics_present:option_association_not_resolved",
    "no_extractable_text:blank_or_scanned_page",
}


def load_raw(raw_json):
    """Read a raw dataset without validating away incomplete inspection targets."""
    path = Path(raw_json).resolve(strict=True)
    with path.open(encoding="utf-8") as handle:
        dataset = json.load(handle)
    if not isinstance(dataset, dict) or not isinstance(dataset.get("questions"), list):
        raise TypeError(f"Not a raw question dataset: {path}")
    if any(not isinstance(question, dict) for question in dataset["questions"]):
        raise ValueError(f"Raw questions must be objects: {path}")
    return dataset


def raw_files(references):
    """Resolve explicit JSON files or directories of existing *.raw.json outputs."""
    files = []
    for reference in references:
        path = Path(reference).resolve(strict=True)
        files.extend(sorted(path.rglob("*.raw.json")) if path.is_dir() else [path])
    files = list(dict.fromkeys(files))
    if not files:
        raise ValueError("No raw JSON files found")
    return files


def _source_matches(dataset, reference):
    file = dataset.get("input") or {}
    recorded = [
        file.get(field) for field in ("filename", "path", "url", "link", "reference")
    ]
    recorded.append((dataset.get("acquisition") or {}).get("origin"))
    for value in recorded:
        if not isinstance(value, str):
            continue
        if reference == value:
            return True
        # A path selector never falls back to its basename.
        if (
            "://" not in reference
            and "://" not in value
            and os.path.normcase(os.path.abspath(reference))
            == os.path.normcase(os.path.abspath(value))
        ):
            return True
    return False


def _metadata_value(dataset, question, field):
    key = question.get("source_question_key") or {}
    if field in key:
        return key[field]
    if field in question:
        return question[field]
    return dataset.get(field)


def inspect_question(
    references, *, source, question_number, include_pages=False, **selectors
):
    """Return every stored question field, with separate document context."""
    matches = []
    for path in raw_files(references):
        dataset = load_raw(path)
        if not _source_matches(dataset, source):
            continue
        for question in dataset["questions"]:
            if question.get("question_number") != question_number:
                continue
            if any(
                value is not None and _metadata_value(dataset, question, field) != value
                for field, value in selectors.items()
            ):
                continue
            matches.append((path, dataset, question))
    if not matches:
        raise ValueError(
            "No matching stored question; check raw file, source reference, number, and metadata"
        )
    if len(matches) != 1:
        details = [
            f"{path} (year={_metadata_value(dataset, question, 'year')}, "
            f"paper={_metadata_value(dataset, question, 'paper')}, "
            f"session={_metadata_value(dataset, question, 'session')}, "
            f"question_id={question.get('question_id')})"
            for path, dataset, question in matches
        ]
        raise ValueError(
            "Ambiguous selection; use an exact raw file or more metadata:\n"
            + "\n".join(details)
        )
    path, dataset, question = matches[0]
    expected = (
        "question_number",
        "page_reference",
        "raw",
        "question_text",
        "subpoints",
        "options",
        "answer",
        "explanation",
        "images",
        "warnings",
    )
    result = {
        "raw_json": str(path),
        "document": {
            key: value
            for key, value in dataset.items()
            if key not in {"questions", "pages"}
        },
        "question": question,
        "availability": {
            "missing_fields": [field for field in expected if field not in question],
            "null_fields": [
                field
                for field in expected
                if field in question and question[field] is None
            ],
        },
    }
    result["visual_issues"] = [
        {"reason": reason, "asset_path": reference}
        for reason, reference in visual_issues(
            question,
            path,
            {page.get("page_number"): page for page in dataset.get("pages", [])},
        )
    ]
    if include_pages:
        page_reference = question.get("page_reference") or {}
        start, end = page_reference.get("start_page"), page_reference.get("end_page")
        result["pages"] = [
            page
            for page in dataset.get("pages", [])
            if isinstance(start, int)
            and isinstance(end, int)
            and start <= page.get("page_number", 0) <= end
        ]
    return result


def _warning_component(warning):
    """Map actual warning codes; do not infer faults from ordinary empty lists."""
    if warning in INFORMATIONAL_WARNINGS:
        return None
    prefix = warning.split(":", 1)[0]
    if prefix.startswith("visual_"):
        return "images/graphics"
    components = {
        "source_assigned_by_parser_profile": "source metadata",
        "uncertain_metadata": "source metadata",
        "question_id_unavailable": "question identity",
        "font_encoding_artifacts": "question/option text",
        "cid_structural_markers_interpreted": "question number/option labels",
        "multi_column_options": "options/images",
        "multi_column_option": "options/images",
        "empty_option_text": "options/images",
        "incomplete_or_ambiguous_options": "options",
        "nonsequential_or_duplicate_question_numbers": "question numbering",
        "question_count_mismatch": "question coverage",
        "no_questions_detected": "question coverage",
        "unassigned_encoded_page": "page mapping/text",
        "line_offset_unavailable": "page mapping",
        "unrecognized_document": "source metadata",
    }
    if prefix in components:
        return components[prefix]
    if any(
        term in warning.lower()
        for term in ("unresolved", "uncertain", "missing", "invalid", "low_confidence")
    ):
        return "parser warning"
    return None


def collect_issues(dataset, raw_json):
    """Build separate review rows, preserving the raw dataset unchanged."""
    rows = []
    document_warnings = dataset.get("warnings") or []
    file = dataset.get("input") or {}
    source = file.get("path") or file.get("filename") or file.get("url")

    def add(scope, question, page, findings):
        if not findings:
            return
        rows.append(
            {
                "raw_json": str(raw_json),
                "source_file": source,
                "year": _metadata_value(dataset, question or {}, "year"),
                "session": _metadata_value(dataset, question or {}, "session"),
                "paper": _metadata_value(dataset, question or {}, "paper"),
                "variant": _metadata_value(dataset, question or {}, "variant"),
                "section": _metadata_value(dataset, question or {}, "section"),
                "scope": scope,
                "question_number": question.get("question_number")
                if question is not None
                else None,
                "page_reference": page,
                "components": list(
                    dict.fromkeys(component for component, _ in findings)
                ),
                "reasons": list(dict.fromkeys(reason for _, reason in findings)),
                "manual_review_required": True,
                "asset_paths": [],
            }
        )

    for warning in document_warnings:
        component = _warning_component(warning)
        if component:
            page = None
            if (
                warning.startswith("unassigned_encoded_page:")
                and warning.split(":")[-1].isdigit()
            ):
                page = {
                    "start_page": int(warning.split(":")[-1]),
                    "end_page": int(warning.split(":")[-1]),
                }
            add("document", None, page, [(component, warning)])
    if not source:
        add(
            "document",
            None,
            None,
            [("source file", "source_file_reference_unavailable")],
        )
    for field in ("source", "year", "section"):
        if (
            dataset.get(field) is None
            and f"uncertain_metadata:{field}" not in document_warnings
        ):
            add(
                "document",
                None,
                None,
                [("source metadata", f"metadata_unavailable:{field}")],
            )
    number_counts = Counter(
        question.get("question_number") for question in dataset["questions"]
    )
    pages = {page.get("page_number"): page for page in dataset.get("pages", [])}
    for question in dataset["questions"]:
        findings = []
        key = question.get("source_question_key") or {}
        for field in ("source", "year", "paper", "variant", "section"):
            if field in key and field in dataset and key[field] != dataset[field]:
                findings.append(
                    ("source metadata", f"source_question_key_mismatch:{field}")
                )
        for warning in question.get("warnings") or []:
            # Shared uncertain metadata is already represented by a document row.
            if warning.startswith("question_id_unavailable:") and any(
                w.startswith("uncertain_metadata:") for w in document_warnings
            ):
                continue
            component = _warning_component(warning)
            if component:
                findings.append((component, warning))
        number = question.get("question_number")
        if type(number) is not int or number < 1:
            findings.append(("question number", "missing_or_invalid_question_number"))
        elif number_counts[number] > 1:
            findings.append(("question number", "duplicate_question_number"))
        for field in ("question_text",):
            value = question.get(field)
            if not isinstance(value, str) or not value.strip():
                findings.append((field, "missing_or_empty_question_text"))
        raw = question.get("raw") or {}
        if (
            not isinstance(raw.get("question_block"), str)
            or not raw["question_block"].strip()
        ):
            findings.append(("raw text", "missing_or_empty_raw_question_block"))
        for option in question.get("options") or []:
            for warning in option.get("warnings") or []:
                component = _warning_component(warning)
                if component:
                    findings.append(
                        (component, f"option {option.get('label')}: {warning}")
                    )
        if question.get("unresolved") is True or question.get("confidence") in (
            "low",
            "uncertain",
        ):
            findings.append(
                ("parser flags", "stored_unresolved_or_low_confidence_flag")
            )
        reference = question.get("page_reference") or {}
        start, end = reference.get("start_page"), reference.get("end_page")
        if type(start) is not int or type(end) is not int or start < 1 or end < start:
            findings.append(("page mapping", "missing_or_invalid_page_reference"))
        elif pages and any(page not in pages for page in range(start, end + 1)):
            findings.append(("page mapping", "referenced_page_not_stored"))
        spans = raw.get("page_spans")
        if spans and pages:
            if reference != {
                "start_page": spans[0].get("page"),
                "end_page": spans[-1].get("page"),
            }:
                findings.append(
                    ("page mapping", "page_reference_differs_from_raw_page_spans")
                )
            pieces = []
            for span in spans:
                text = (pages.get(span.get("page")) or {}).get("raw_text")
                begin, finish = span.get("start"), span.get("end")
                if (
                    not isinstance(text, str)
                    or type(begin) is not int
                    or type(finish) is not int
                    or not 0 <= begin <= finish <= len(text)
                ):
                    findings.append(("page mapping", "invalid_raw_page_span"))
                    break
                pieces.append(text[begin:finish])
            else:
                if "\n".join(pieces) != raw.get("question_block"):
                    findings.append(
                        ("page mapping", "raw_block_differs_from_stored_page_spans")
                    )
        detected = visual_issues(question, raw_json, pages)
        findings.extend(("images/graphics", reason) for reason, _ in detected)
        add("question", question, question.get("page_reference"), findings)
        if findings:
            rows[-1]["asset_paths"] = list(
                dict.fromkeys(path for _, path in detected if path)
            )
    # Report page failures even when no question could be attached to them.
    for page in pages.values():
        findings = [
            (component, warning)
            for warning in page.get("warnings") or []
            if (component := _warning_component(warning))
            in {"page mapping", "images/graphics"}
        ]
        page_visuals = visual_issues(
            {"visual_assets": page.get("visual_assets", [])}, raw_json, pages
        )
        findings.extend(("images/graphics", reason) for reason, _ in page_visuals)
        if findings:
            add(
                "page",
                None,
                {
                    "start_page": page.get("page_number"),
                    "end_page": page.get("page_number"),
                },
                findings,
            )
            rows[-1]["asset_paths"] = list(
                dict.fromkeys(path for _, path in page_visuals if path)
            )
    return rows


def _cell(value):
    if value is None:
        return "unavailable"
    return str(value).replace("|", "\\|").replace("\n", "<br>").replace("\r", "")


def _issue_category(reason):
    """Classify an observed warning, not an expected-but-undetected problem."""
    code = reason.split(":", 1)[0]
    if code.startswith("option ") and ": " in reason:
        code = reason.split(": ", 1)[1].split(":", 1)[0]
    if code == "foreign_option_letter_in_crop":
        return "Foreign Option Letter in Crop"
    if code == "overlapping_option_visual_assets" or code.startswith(
        "visual_neighbor_boundary_uncertain"
    ):
        return "Overlapping Visual Assets"
    if code.startswith(
        (
            "visual_crop_",
            "visual_caption_",
            "visual_option_boundary_",
            "visual_question_boundary_overlap",
        )
    ):
        return "Incomplete or Uncertain Visual Crop"
    if code.startswith(
        (
            "visual_image_option_",
            "visual_multiple_option_",
            "visual_option_",
            "multi_column_option",
            "incomplete_or_ambiguous_options",
        )
    ):
        return "Option Association Issues"
    if code.startswith(
        (
            "visual_component_association_uncertain",
            "visual_question_association_uncertain",
        )
    ):
        return "Visual Asset Unassigned"
    if code.startswith(
        (
            "visual_asset_file_missing",
            "visual_asset_not_displayable",
            "visual_asset_not_saved",
            "visual_asset_path_invalid",
            "visual_assets_unavailable",
            "visual_save_failed",
            "visual_detected_object_not_saved",
        )
    ):
        return "Missing/Corrupt Asset"
    if code.startswith("visual_"):
        return "Visual Structure Issues"
    if code.startswith(
        (
            "font_encoding_artifacts",
            "cid_structural_markers_interpreted",
            "missing_or_empty_question_text",
            "missing_or_empty_raw_question_block",
        )
    ):
        return "Question Text Parsing Issues"
    if code.startswith(
        (
            "missing_or_invalid_page_reference",
            "referenced_page_not_stored",
            "page_reference_differs_from_raw_page_spans",
            "invalid_raw_page_span",
            "raw_block_differs_from_stored_page_spans",
            "unassigned_encoded_page",
            "line_offset_unavailable",
        )
    ):
        return "Page/Range Mapping Issues"
    if code.startswith(
        (
            "missing_or_invalid_question_number",
            "duplicate_question_number",
            "nonsequential_or_duplicate_question_numbers",
            "question_count_mismatch",
            "no_questions_detected",
        )
    ):
        return "Duplicate/Invalid Question Number"
    if code.startswith(
        (
            "source_assigned_by_parser_profile",
            "uncertain_metadata",
            "source_question_key_mismatch",
            "source_file_reference_unavailable",
            "metadata_unavailable",
            "question_id_unavailable",
            "unrecognized_document",
        )
    ):
        return "Source Metadata Issues"
    return "Other / Unclassified"


def _categorize_rows(issues):
    grouped = {}
    for row in issues:
        page = row.get("page_reference") or {}
        key = (
            row["raw_json"],
            row["scope"],
            row["question_number"],
            page.get("start_page"),
            page.get("end_page"),
        )
        for reason in row["reasons"]:
            category = _issue_category(reason)
            bucket = grouped.setdefault(category, {})
            if key not in bucket:
                bucket[key] = {**row, "reasons": [], "asset_paths": []}
            if reason not in bucket[key]["reasons"]:
                bucket[key]["reasons"].append(reason)
            for path in row.get("asset_paths", []):
                if path not in bucket[key]["asset_paths"]:
                    bucket[key]["asset_paths"].append(path)

    def order(row):
        page = row.get("page_reference") or {}
        return (
            row["year"] if isinstance(row["year"], int) else float("inf"),
            str(row["source_file"] or "").casefold(),
            row["question_number"] if isinstance(row["question_number"], int) else -1,
            page.get("start_page") or -1,
            row["scope"],
            row["raw_json"],
        )

    return {name: sorted(grouped[name].values(), key=order) for name in sorted(grouped)}


def write_report(references, output):
    """Refresh only a separate generated Markdown report, never raw JSON."""
    files = raw_files(references)
    output = Path(output).resolve()
    if output in files or output.suffix.lower() != ".md":
        raise ValueError("The issues report must be a separate Markdown file")
    if output.exists() and not output.read_text(encoding="utf-8").startswith(
        REPORT_MARKER
    ):
        raise FileExistsError(
            "Refusing to replace a file that is not a generated parsing-issues report"
        )
    issues = []
    questions = 0
    for path in files:
        dataset = load_raw(path)
        questions += len(dataset["questions"])
        issues.extend(collect_issues(dataset, path))
    question_rows = sum(row["scope"] == "question" for row in issues)
    text = [
        REPORT_MARKER,
        "# Blackstone raw parsing issues",
        "",
        f"Scanned {len(files)} raw files and {questions} stored questions. {question_rows} question records require review; {len(issues) - question_rows} document/page issues are listed separately.",
        "",
        "This is a generated snapshot of detectable issues, not a correctness score. Shared source/year warnings appear once per document. General graphics-presence notices and blank-page notices alone do not mark a question unresolved. No issue row means no issue detected by these checks, not verified correctness.",
        "",
        "Regenerate with `python -m parsers.blackstone.backtest report --raw-json data/raw/blackstone --output PATH_TO_THIS_REPORT`.",
        "",
    ]
    for category, rows in _categorize_rows(issues).items():
        text.extend(
            [
                f"## {category}",
                "",
                "| Source file | Year/session/test | Question | Pages | Components | Reason | Saved asset paths | Manual review | Raw JSON |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in rows:
            metadata = "; ".join(
                f"{field}={row[field] if row[field] is not None else 'unavailable'}"
                for field in ("year", "session", "paper", "variant", "section")
            )
            page = row["page_reference"] or {}
            page_label = (
                f"{page.get('start_page')}–{page.get('end_page')}" if page else None
            )
            values = [
                row["source_file"],
                metadata,
                row["question_number"]
                if row["scope"] == "question"
                else f"{row['scope']} (no question number)",
                page_label,
                "; ".join(row["components"]),
                "; ".join(row["reasons"]),
                "; ".join(row.get("asset_paths", [])) or "unavailable",
                "yes",
                row["raw_json"],
            ]
            text.append("| " + " | ".join(_cell(value) for value in values) + " |")
        text.append("")
    if not issues:
        text.extend(["", "No unresolved cases detected by these checks."])
    elif text[-1] == "":
        text.pop()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(text) + "\n", encoding="utf-8")
    return issues


def render_inspection(result, output_format):
    if output_format == "html":
        return render_html(result)
    if output_format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    question = result["question"]
    block = (question.get("raw") or {}).get("question_block", "unavailable")
    if block is None:
        block = "null (stored value)"
    text = [
        "SOURCE / DOCUMENT METADATA",
        json.dumps(result["document"], ensure_ascii=False, indent=2),
        "FULL STORED QUESTION RECORD",
        json.dumps(question, ensure_ascii=False, indent=2),
        "AVAILABILITY",
        json.dumps(result["availability"], ensure_ascii=False, indent=2),
        "RAW QUESTION BLOCK (VERBATIM)",
        block,
    ]
    if "pages" in result:
        text.extend(
            [
                "REFERENCED STORED PAGES",
                json.dumps(result["pages"], ensure_ascii=False, indent=2),
            ]
        )
    if result.get("visual_issues"):
        text.extend(
            [
                "VISUAL INSPECTION ISSUES",
                json.dumps(result["visual_issues"], ensure_ascii=False, indent=2),
            ]
        )
    return "\n\n".join(text) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser(
        "inspect", help="Print/export one complete stored question"
    )
    inspect.add_argument("--raw-json", nargs="+", required=True, type=Path)
    inspect.add_argument(
        "--source",
        required=True,
        help="Recorded PDF path, filename, or URL (never fetched)",
    )
    inspect.add_argument("--question", required=True, type=int)
    inspect.add_argument("--year", type=int)
    for field in ("session", "paper", "variant", "section", "question_id"):
        inspect.add_argument("--" + field.replace("_", "-"))
    inspect.add_argument("--include-pages", action="store_true")
    inspect.add_argument("--format", choices=("text", "json", "html"), default="text")
    inspect.add_argument(
        "--output",
        type=Path,
        help="Export to a new file; existing files are never overwritten",
    )
    report = commands.add_parser(
        "report", help="Write a separate Markdown issues report"
    )
    report.add_argument("--raw-json", nargs="+", required=True, type=Path)
    report.add_argument("--output", type=Path, default=Path("docs/PARSING_ISSUES.md"))
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            issues = write_report(args.raw_json, args.output)
            print(f"Reported {len(issues)} review rows -> {args.output}")
            return 0
        selectors = {
            field: getattr(args, field)
            for field in (
                "year",
                "session",
                "paper",
                "variant",
                "section",
                "question_id",
            )
        }
        result = inspect_question(
            args.raw_json,
            source=args.source,
            question_number=args.question,
            include_pages=args.include_pages,
            **selectors,
        )
        rendered = render_inspection(result, args.format)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"Backtest failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
