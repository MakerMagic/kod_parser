"""Read-only matched question/solution inspection, reusing clean presentation."""

import argparse
import base64
import json
import re
from hashlib import sha256
from html import escape
from pathlib import Path

from parsers.blackstone.backtest import _source_matches
from parsers.blackstone.visual_inspection import read_png, resolve_asset, visual_issues
from processors.normalization.blackstone.backtest import render_html as clean_html
from processors.normalization.blackstone.issues import current_issues

from .explanation import build_final_explanation
from .report import write_report
from .storage import load_matched, protect_output


def inspect_question(
    path, *, year, question_number, section="section_1", source=None, **selectors
):
    data = load_matched(path)
    found = [
        r
        for r in data["records"]
        if r["identity"]
        == {"year": year, "section": section, "question_number": question_number}
        and (
            source is None or _source_matches(r.get("question_document") or {}, source)
        )
        and all(
            value is None
            or (r.get("question") or {}).get("metadata", {}).get(field) == value
            for field, value in selectors.items()
        )
    ]
    if len(found) != 1:
        raise ValueError(
            "No unique matched record; refine selection"
            if found
            else "No selected record"
        )
    record = found[0]
    # Older matched files remain inspectable, without writing back to them.
    record.setdefault(
        "final_explanation",
        build_final_explanation(record.get("answer"), record.get("answer_reference")),
    )
    live = []
    refs = [record.get("question_reference"), record.get("answer_reference")]
    q, a = record.get("question"), record.get("answer")
    if q:
        refs += [q["raw_reference"], record["question_document"]["input"]]
        live += current_issues(q, clean_json=record["question_reference"]["path"])
        live += [
            {"code": "raw_visual_issue", "reason": reason, "asset_path": asset}
            for reason, asset in visual_issues(
                q["raw_record"], q["raw_reference"]["path"], {}
            )
        ]
    if a:
        refs.append(a["source_document"])
        refs.extend(a["source_document"].get("related_sources", []))
        refs += [
            {
                "path": str(
                    resolve_asset(record["answer_reference"]["path"], asset["path"])
                ),
                "sha256": asset["sha256"],
            }
            for asset in [
                *a.get("visual_previews", []),
                *a.get("explanation", {}).get("visual_assets", []),
            ]
        ]
    for candidate in record.get("superseded_answer_candidates", []):
        original = candidate["record"]
        refs += [candidate["reference"], original["source_document"]]
        refs.extend(original["source_document"].get("related_sources", []))
        refs += [
            {
                "path": str(
                    resolve_asset(candidate["reference"]["path"], asset["path"])
                ),
                "sha256": asset["sha256"],
            }
            for asset in [
                *original.get("visual_previews", []),
                *original["explanation"].get("visual_assets", []),
            ]
        ]
    for ref in refs:
        if ref is None:
            continue
        try:
            if sha256(Path(ref["path"]).read_bytes()).hexdigest() != ref["sha256"]:
                raise ValueError("Stored source hash differs")
        except (OSError, ValueError) as error:
            live.append(
                {
                    "code": "inspection_reference_unavailable",
                    "path": ref["path"],
                    "reason": str(error),
                }
            )
    result = {
        "matched_json": str(Path(path).resolve()),
        "record": record,
        "live_inspection_issues": live,
    }
    generation_entries = [
        entry
        for entry in data.get("explanation_pilot", {}).get("audit", [])
        if entry.get("identity") == record["identity"]
    ]
    if len(generation_entries) == 1:
        entry = generation_entries[0]
        result["explanation_generation_history"] = entry.get("generation_attempts") or [
            {"candidate": entry.get("candidate"), "metadata": entry.get("metadata")}
        ]
        result["explanation_provider_events"] = entry.get("events", [])
        result["explanation_semantic_review"] = entry.get("semantic_review")
        result["explanation_candidate"] = entry.get("candidate")
        result["explanation_generation_metrics"] = data.get(
            "explanation_pilot", {}
        ).get("metrics")
    source_issues = [
        issue
        for issue in data["issues"]
        if issue not in record["issues"]
        and issue.get("year") == year
        and issue.get("question_number") == question_number
    ]
    if source_issues:
        result["source_parsing_issues"] = source_issues
    return result


def render_html(result):
    r = result["record"]
    q, a = r.get("question"), r.get("answer")
    identity = r["identity"]
    inherited = {}
    if q:
        clean = clean_html(
            {
                "question": q,
                "document": r["question_document"],
                "clean_json": r["question_reference"]["path"],
                "cleaning_issues": q["cleaning_issues"],
                "raw_visual_issues": [],
            }
        )
        inherited = dict(
            re.findall(r"<section id='([^']+)'>(.*?)</section>", clean, re.DOTALL)
        )
    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; img-src data:; style-src 'unsafe-inline'\">",
        "<title>Matching inspection</title><style>body{font:16px/1.55 system-ui;max-width:1050px;margin:24px auto;padding:24px}h2{color:#235586}img{max-width:100%;height:auto}pre,.text{white-space:pre-wrap;overflow-wrap:anywhere}section{margin:28px 0}.issue{background:#fff0d8;padding:12px}</style></head><body><main>",
        "<h1>Matched question / explanation inspection</h1>",
    ]

    def section(identifier, title, content):
        parts.append(
            f"<section id='{identifier}'><h2>{escape(title)}</h2>{content}</section>"
        )

    def text(value):
        return (
            f"<p class='text'>{escape(str(value))}</p>"
            if value
            else "<p>[unavailable / empty]</p>"
        )

    def dump(value):
        return (
            "<pre>" + escape(json.dumps(value, ensure_ascii=False, indent=2)) + "</pre>"
        )

    section("identity", "Question Identity", dump({**identity, "status": r["status"]}))
    for ident, heading in (
        ("main-body", "Main Body"),
        ("main-question", "Main Question"),
        ("main-answers", "Main Answers"),
    ):
        parts.append(
            f"<section id='{ident}'>"
            + inherited.get(
                ident, f"<h2>{heading}</h2><p>Unavailable; no candidate selected.</p>"
            )
            + "</section>"
        )
    section("correct-answer", "Correct Answer", text(r.get("correct_answer")))
    explanation = (a or {}).get("explanation", {})
    answer_only = explanation.get("availability") == "not_supplied_by_source_format"
    assets = {
        asset["asset_index"]: asset for asset in explanation.get("visual_assets", [])
    }

    def visual(asset):
        try:
            png = read_png(resolve_asset(r["answer_reference"]["path"], asset["path"]))
            if sha256(png).hexdigest() != asset["sha256"]:
                raise ValueError("Saved explanation visual differs from stored hash")
            return (
                f"<figure data-asset-index='{asset['asset_index']}'><figcaption>Explanation visual {asset['asset_index']}, page {asset['page']}</figcaption>"
                f"<img alt='Explanation visual {asset['asset_index']}' src='data:image/png;base64,{base64.b64encode(png).decode('ascii')}'></figure>"
            )
        except (OSError, ValueError, KeyError) as error:
            return (
                "<p class='issue'>Explanation visual unavailable: "
                + escape(str(error))
                + "</p>"
            )

    def explanation_block(block):
        if block["type"] == "visual":
            asset = assets.get(block["asset_index"])
            return (
                visual(asset)
                if asset
                else "<p class='issue'>Explanation visual reference unresolved.</p>"
            )
        if block["type"] == "list":
            return (
                "<ul>"
                + "".join(
                    f"<li class='text' data-option='{escape(item.get('label') or 'unresolved')}'>{escape((item['label'] + ': ') if item.get('label') and not re.match(r'^' + re.escape(item['label']) + r'\s*[-–—.:)]', item['text']) else '')}{escape(item['text'])}</li>"
                    for item in block["items"]
                )
                + "</ul>"
            )
        if block["type"] != "paragraph":
            return (
                "<p class='issue'>Unsupported explanation block; retained below.</p>"
                + dump(block)
            )
        return (
            ""
            if block.get("role") == "list_marker_artifact"
            else text(block.get("text"))
        )

    final = r.get("final_explanation") or build_final_explanation(
        a, r.get("answer_reference")
    )
    final_content = (
        "<p><strong>Manually supplied by the user; not extracted from the source PDF.</strong></p>"
        if (a or {}).get("provenance", {}).get("origin") == "user_supplied_manual"
        else ""
    )
    if final["status"] == "unavailable" or (
        not final["blocks"] and not final["unplaced_components"]
    ):
        final_content += text(
            "No explanation is available: this source format supplies answers only."
            if final.get("reason") == "not_supplied_by_source_format"
            else "Explanation unavailable; see original components/source and issues below."
        )
    if final["status"] == "uncertain":
        final_content += "<p class='issue'>Final Explanation requires review; unresolved content/order has not been repaired or guessed.</p>"
    final_content += "".join(explanation_block(block) for block in final["blocks"])
    if final["unplaced_components"]:
        final_content += (
            "<details open><summary>Unplaced components — order not asserted</summary>"
            + dump(final["unplaced_components"])
            + "</details>"
        )
    final_content += (
        "<details><summary>Combination provenance / warnings</summary>"
        + dump(
            {
                k: v
                for k, v in final.items()
                if k not in ("blocks", "unplaced_components")
            }
        )
        + "</details>"
    )
    section("final-explanation", "Final Explanation", final_content)
    section(
        "explanation-provenance",
        "Explanation Provenance",
        text(
            "Explanation by AI: "
            + ("True" if final.get("explanation_by_ai") else "False")
        )
        + dump(
            {
                "explanation_by_ai": bool(final.get("explanation_by_ai")),
                "source_type": final.get("source_type", "source_or_manual"),
                "generation": r.get("ai_explanation"),
            }
        ),
    )
    generation = r.get("ai_explanation")
    if generation:
        metrics = result.get("explanation_generation_metrics")
        availability = (
            text(
                f"Generation availability: {metrics['received_output']}/{metrics['selected']}\n"
                f"Explanation quality among completed returned outputs: {metrics['accepted']}/{metrics['quality_evaluated']} accepted (provider failures excluded)\n"
                f"Overall completed: {metrics['accepted']}/{metrics['selected']}"
            )
            if metrics
            else ""
        )
        first_status = generation.get(
            "first_attempt_validation_status",
            generation.get("validation_status", "unavailable"),
        )
        final_status = (
            "rejected"
            if generation.get("quality_review_status") == "rejected"
            else generation.get("validation_status", "unavailable")
        )
        section(
            "generation-validation",
            "Generation Validation",
            availability
            + text(
                f"Provider: {generation.get('provider', 'unavailable')}\n"
                f"Model: {generation.get('model', 'unavailable')}\n"
                f"First-attempt validation status: {first_status}\n"
                f"Retry attempted: {bool(generation.get('retry_attempted', False))}\n"
                f"Retry result: {generation.get('retry_result', 'not_attempted')}\n"
                f"Deferred provider retry cycles (this run): {generation.get('deferred_retry_cycles', 0)}\n"
                f"Provider failure: {generation.get('failure_code', 'none')}\n"
                f"Final validation status: {final_status}\n"
                f"Semantic-review status: {generation.get('semantic_review_status', 'not_recorded')}\n"
                f"Generation status: {generation.get('generation_status', 'unavailable')}"
            )
            + text(
                "First-attempt rejection reasons: "
                + ", ".join(generation.get("first_attempt_validation_errors", []))
            )
            + text(
                "Final rejection reasons: "
                + "; ".join(
                    generation.get("quality_review_reasons", [])
                    or generation.get("validation_errors", [])
                    or (
                        [generation["failure_code"]]
                        if generation.get("failure_code")
                        else []
                    )
                )
            )
            + "<details><summary>Generation attempt history</summary>"
            + dump(result.get("explanation_generation_history", []))
            + dump(result.get("explanation_provider_events", []))
            + dump(result.get("explanation_semantic_review"))
            + "</details>",
        )
        candidate = result.get("explanation_candidate")
        if candidate and generation.get("semantic_review_status") in (
            "pending",
            "rejected",
        ):
            section(
                "semantic-review-candidate",
                "Candidate — Not Accepted: Semantic Review",
                text(candidate.get("main_reasoning"))
                + "".join(
                    text(f"{item['label']}: {item['reason']}")
                    for item in candidate.get("incorrect_options", [])
                    if isinstance(item, dict) and "label" in item and "reason" in item
                ),
            )

    section(
        "main-explanation",
        "Main Explanation",
        (
            "<p><strong>Manually supplied by the user; not extracted from the source PDF.</strong></p>"
            if (a or {}).get("provenance", {}).get("origin") == "user_supplied_manual"
            else ""
        )
        + (
            "<p>No explanation is available: this source format supplies answers only.</p>"
            if answer_only
            else (
                (
                    "".join(explanation_block(b) for b in explanation.get("blocks", []))
                    if "visual_assets" in explanation
                    else "".join(
                        text(p["text"]) for p in explanation.get("paragraphs", [])
                    )
                )
                or text(None)
            )
        ),
    )
    if "visual_assets" in explanation:
        section(
            "explanation-visuals",
            "Explanation Visuals",
            "".join(visual(asset) for asset in assets.values())
            or "<p>No separate visual assets detected; source previews remain available.</p>",
        )
    wrong = []
    for block in explanation.get("bulleted_blocks", []):
        if block.get("role", "").startswith("incorrect_choices"):
            wrong.append(text(block.get("transition")))
            if block["role"] == "incorrect_choices_unmapped":
                if any(
                    "choice_transition_without_unique_incorrect_labels" in warning
                    for warning in (a or {}).get("warnings", [])
                ):
                    wrong.append(
                        "<p class='issue'>Individual option mapping unresolved; no labels inferred.</p>"
                    )
                else:
                    wrong.append(
                        "<p>Items retained in source order; individual option letters are not inferred.</p>"
                    )
            wrong.append(
                "<ul>"
                + "".join(
                    f"<li class='text' data-option='{escape(item.get('label', 'unresolved'))}'>{escape(item['text'])}</li>"
                    for item in block["items"]
                )
                + "</ul>"
            )
    section(
        "incorrect-explanations",
        "Incorrect Answer Explanations",
        "".join(wrong) or text(None),
    )
    other = []
    for block in explanation.get("other_lists", []):
        other.append(
            "<ul>"
            + "".join(
                f"<li class='text'>{escape(item['text'])}</li>"
                for item in block["items"]
            )
            + "</ul>"
        )
    section("other-lists", "Other Explanation Lists", "".join(other) or text(None))
    section(
        "explanation-order",
        "Original Explanation Block Order",
        dump(explanation.get("blocks")),
    )
    for candidate in r.get("superseded_answer_candidates", []):
        original = candidate["record"]
        content = "<p>Manually superseded, not a claimed parser fix. Original content and warnings are preserved.</p>"
        content += dump(
            {
                "reference": candidate["reference"],
                "source": original["source_document"],
                "pages": original["page_reference"],
                "warnings": original["warnings"],
                "explanation": original["explanation"],
            }
        )
        for asset in original.get("visual_previews", []):
            try:
                png = read_png(
                    resolve_asset(candidate["reference"]["path"], asset["path"])
                )
                if sha256(png).hexdigest() != asset["sha256"]:
                    raise ValueError("Original source preview hash differs")
                content += f"<figure><figcaption>Original source page {asset['page']}</figcaption><img alt='Original superseded explanation' src='data:image/png;base64,{base64.b64encode(png).decode('ascii')}'></figure>"
            except (OSError, ValueError) as error:
                content += "<p class='issue'>" + escape(str(error)) + "</p>"
        section(
            "superseded-explanation",
            "Original PDF Explanation — Manually Superseded",
            content,
        )
    section(
        "original-screenshot",
        "Original Question Screenshot",
        inherited.get("original-screenshot", text(None)).replace(
            "<h2>Original Screenshot</h2>", ""
        ),
    )
    answer_source = dump(
        {
            "source": (a or {}).get("source_document"),
            "pages": (a or {}).get("page_reference"),
            "answer_reference": r.get("answer_reference"),
            **({"parsed_answer_key_row": a["raw"]} if answer_only else {}),
            **({"provenance": a["provenance"]} if (a or {}).get("provenance") else {}),
        }
    )
    for asset in (a or {}).get("visual_previews", []):
        try:
            png = read_png(resolve_asset(r["answer_reference"]["path"], asset["path"]))
            answer_source += f"<figure><figcaption>Answer source page {asset['page']}</figcaption><img alt='Original explanation' src='data:image/png;base64,{base64.b64encode(png).decode('ascii')}'></figure>"
        except (OSError, ValueError) as error:
            answer_source += "<p class='issue'>" + escape(str(error)) + "</p>"
    answer_source += (
        (
            "<details><summary>Raw answer-key row</summary>"
            if answer_only
            else "<details><summary>Raw explanation excerpt</summary>"
        )
        + text((a or {}).get("raw", {}).get("source_excerpt"))
        + "</details>"
    )
    section(
        "answer-source",
        "Answer-Key Source" if answer_only else "Answer / Explanation Source",
        answer_source,
    )
    section(
        "matching-metadata",
        "Matching Metadata",
        dump(
            {
                "keys": identity,
                "status": r["status"],
                "matching": r["matching"],
                "question_reference": r.get("question_reference"),
                "question_document": r.get("question_document"),
                "question_candidates": r.get("question_candidates"),
                "answer_candidates": r.get("answer_candidates"),
            }
        ),
    )
    section(
        "availability",
        "Question Field Availability",
        dump((q or {}).get("availability")),
    )
    section(
        "issues",
        "Issues",
        dump(
            {
                "matching": r["issues"],
                **(
                    {"source_parsing": result["source_parsing_issues"]}
                    if result.get("source_parsing_issues")
                    else {}
                ),
                "answer_parsing": (a or {}).get("warnings"),
                **(
                    {
                        "superseded_source_warnings": [
                            {
                                "source": c["reference"],
                                "warnings": c["record"]["warnings"],
                            }
                            for c in r["superseded_answer_candidates"]
                        ]
                    }
                    if r.get("superseded_answer_candidates")
                    else {}
                ),
                "raw_question": (q or {}).get("raw_warnings"),
                "raw_document": (q or {}).get("raw_document_warnings"),
                "cleaning": (q or {}).get("cleaning_issues"),
                "live_validation": result["live_inspection_issues"],
            }
        ),
    )
    parts.append("</main></body></html>")
    return "\n".join(parts)


def render_inspection(result, format="text"):
    if format == "html":
        return render_html(result)
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--matched-json", type=Path, required=True)
    inspect.add_argument("--year", type=int, required=True)
    inspect.add_argument("--question", type=int, required=True)
    inspect.add_argument("--section", default="section_1")
    for field in ("source", "paper", "variant"):
        inspect.add_argument("--" + field)
    inspect.add_argument("--format", choices=("text", "json", "html"), default="text")
    inspect.add_argument("--output", type=Path)
    report = commands.add_parser("report")
    report.add_argument("--matched-json", type=Path, required=True)
    report.add_argument(
        "--output", type=Path, default=Path("docs/MATCHING_2008-2016_ISSUES.md")
    )
    args = cli.parse_args(argv)
    try:
        data = load_matched(args.matched_json)
        if args.output:
            protect_output(data, args.output, merged_json=args.matched_json)
        if args.command == "report":
            write_report(data, args.output)
            return 0
        result = inspect_question(
            args.matched_json,
            year=args.year,
            question_number=args.question,
            section=args.section,
            source=args.source,
            paper=args.paper,
            variant=args.variant,
        )
        content = render_inspection(result, args.format)
        if args.output:
            suffix = (
                ".html"
                if args.format == "html"
                else ".json"
                if args.format == "json"
                else ".txt"
            )
            if args.output.suffix.lower() != suffix:
                raise ValueError(f"Expected {suffix} inspection output")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(content)
            print(args.output)
        else:
            print(content)
    except (OSError, ValueError, KeyError, TypeError) as error:
        cli.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
