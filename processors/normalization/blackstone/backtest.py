"""Read-only clean/raw comparison with self-contained HTML and stored PNGs."""

import argparse
import base64
import json
import sys
from html import escape
from pathlib import Path

from parsers.blackstone.backtest import _source_matches
from parsers.blackstone.visual_inspection import read_png, visual_issues

from .body_assets import resolve_question_asset
from .issues import current_issues, write_report
from .option_assets import is_image_option, resolve_clean_asset
from .storage import clean_files, load_clean, protect_output


def inspect_question(references, *, source, question_number, **selectors):
    matches = []
    for path in clean_files(references):
        dataset = load_clean(path)
        if not _source_matches(dataset["document"], source):
            continue
        for q in dataset["questions"]:
            if q["question_number"] == question_number and all(
                value is None
                or (
                    q.get("question_id")
                    if field == "question_id"
                    else q["metadata"].get(field)
                )
                == value
                for field, value in selectors.items()
            ):
                matches.append((path, dataset, q))
    if len(matches) != 1:
        raise ValueError(
            "No matching clean question"
            if not matches
            else "Ambiguous clean selection; specify an exact file or additional metadata"
        )
    path, dataset, q = matches[0]
    try:
        raw_visual = [
            {"reason": reason, "asset_path": asset}
            for reason, asset in visual_issues(
                q["raw_record"], q["raw_reference"]["path"], {}
            )
        ]
    except (KeyError, TypeError, ValueError) as error:
        raw_visual = [{"reason": "raw_visual_validation_unavailable: " + str(error)}]
    return {
        "clean_json": str(path),
        "document": dataset["document"],
        "question": q,
        "cleaning_issues": current_issues(q, clean_json=path),
        "raw_visual_issues": raw_visual,
    }


def render_html(result):
    q = result["question"]
    year = q["metadata"].get("year")
    title = f"Question {q['question_number']} — {year if year is not None else 'year unavailable'}"
    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; img-src data:; style-src 'unsafe-inline'\">",
        f"<title>{escape(title)}</title>",
        "<style>body{font:16px/1.55 system-ui,sans-serif;background:#eef2f6;color:#192535}main{max-width:1000px;margin:24px auto;background:white;padding:28px}h2{color:#235586;border-bottom:1px solid #dbe2e8}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:14px}img{max-width:100%;height:auto}figure{margin:20px 0}figcaption{font-size:13px;color:#52606f}.issue{border-left:4px solid #b56c00;background:#fff5df;padding:10px}.text{white-space:pre-wrap}section{margin-bottom:32px}</style></head>",
        f"<body><main><h1>{escape(title)}</h1>",
        "<p>Conservative clean representation. Unresolved structure is not proof of correctness; compare the original screenshot and retained raw record.</p>",
    ]

    def text(value):
        if value is None:
            parts.append(
                "<p class='issue'>Unavailable / null. No missing content inferred.</p>"
            )
        elif value == "":
            parts.append("<p>[empty text]</p>")
        else:
            parts.append(f"<p class='text'>{escape(str(value))}</p>")

    def figure(asset, caption, *, answer=False):
        derived = asset.get("clean_asset") if answer else None
        shown = derived or asset
        parts.append(
            f"<figure><figcaption>{escape(caption)} · page {escape(str(shown.get('page')))} · {escape(str(shown.get('path')))}</figcaption>"
        )
        try:
            data = read_png(
                resolve_clean_asset(result["clean_json"], derived["path"])
                if derived
                else resolve_question_asset(
                    q["raw_reference"]["path"], result["clean_json"], asset
                )
            )
            if derived:
                parts.append(
                    "<small>Derived clean crop; original raw asset retained in the record.</small>"
                )
            elif (
                asset.get("provenance", {}).get("origin")
                == "user_supplied_pinned_body_visual"
            ):
                parts.append(
                    "<small>User-supplied pinned composite; original raw assets retained for traceability.</small>"
                )
            elif answer:
                parts.append(
                    "<p class='issue'>Clean option crop unavailable/unresolved; original raw asset shown without silent modification.</p>"
                )
            parts.append(
                f"<img src='data:image/png;base64,{base64.b64encode(data).decode('ascii')}' alt='{escape(caption, quote=True)}'>"
            )
        except (OSError, ValueError) as error:
            parts.append(
                f"<p class='issue'>Image unavailable: {escape(str(error))}</p>"
            )
        if asset.get("axis_labels"):
            text("; ".join(label["text"] for label in asset["axis_labels"]))
        if asset.get("warnings"):
            text("Preserved raw visual warnings: " + "; ".join(asset["warnings"]))
        parts.append("</figure>")

    assets = {a["image_id"]: a for a in q["visual_assets"]}
    parts.append("<section id='main-body'><h2>Main Body</h2>")
    if not q["main_body"]:
        parts.append("<p>[empty body context]</p>")
    for block in q["main_body"]:
        if block["type"] == "text":
            text(block["text"])
        elif block["asset_id"] in assets:
            figure(
                assets[block["asset_id"]],
                "Body context graphic"
                + (
                    " — unresolved placement"
                    if block.get("raw_component") in {"unknown", "option"}
                    else ""
                ),
            )
        else:
            parts.append("<p class='issue'>Unresolved body visual reference</p>")
    parts.append("</section><section id='main-question'><h2>Main Question</h2>")
    text(q["main_question"])
    parts.append("</section><section id='main-answers'><h2>Main Answers</h2>")
    if not q["options"]:
        text(q["options"])
    for option in q["options"] or []:
        parts.append(
            f"<article data-option='{escape(str(option.get('label')), quote=True)}'><h3>{escape(str(option.get('label')))}</h3>"
        )
        if option.get("content_type") == "image" and option.get("text") == "":
            parts.append("<p>[image-based option]</p>")
        else:
            text(option.get("text"))
        for asset in option.get("images") or []:
            figure(
                asset, f"Option {option.get('label')}", answer=is_image_option(option)
            )
        parts.append("</article>")
    parts.append(
        "</section><section id='original-screenshot'><h2>Original Screenshot</h2>"
    )
    if not q["visual_previews"]:
        parts.append(
            "<p class='issue'>Original screenshot unavailable; cleaning never reopens the PDF.</p>"
        )
    for asset in q["visual_previews"]:
        figure(asset, "Full question context saved during raw parsing")
    parts.append("</section>")
    for identifier, heading, value in (
        (
            "metadata",
            "Source / Document Metadata",
            {
                "document": result["document"],
                "question_metadata": q["metadata"],
                "clean_json": result["clean_json"],
                "raw_reference": q["raw_reference"],
            },
        ),
        ("availability", "Missing / Null Field Availability", q["availability"]),
        (
            "issues",
            "Visual Inspection Issues",
            {
                "preserved_raw_warnings": q["raw_warnings"],
                "preserved_document_warnings": q["raw_document_warnings"],
                "raw_visual_issues": result["raw_visual_issues"],
                "cleaning_issues": result["cleaning_issues"],
            },
        ),
    ):
        parts.append(
            f"<section id='{identifier}'><h2>{escape(heading)}</h2><pre>{escape(json.dumps(value, ensure_ascii=False, indent=2))}</pre></section>"
        )
    parts.append(
        "<details><summary>Raw/original record and clean transformation evidence</summary><pre>"
        + escape(json.dumps(q, ensure_ascii=False, indent=2))
        + "</pre></details></main></body></html>"
    )
    return "\n".join(parts)


def render_inspection(result, format="text"):
    if format == "html":
        return render_html(result)
    if format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    q = result["question"]
    return (
        "\n\n".join(
            [
                f"Question {q['question_number']} — year {q['metadata'].get('year')}",
                "MAIN BODY",
                json.dumps(q["main_body"], ensure_ascii=False, indent=2),
                "MAIN QUESTION",
                str(q["main_question"]),
                "MAIN ANSWERS",
                json.dumps(q["options"], ensure_ascii=False, indent=2),
                "FULL CLEAN/RAW COMPARISON",
                json.dumps(result, ensure_ascii=False, indent=2),
            ]
        )
        + "\n"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--clean-json", nargs="+", required=True, type=Path)
    inspect.add_argument("--source", required=True)
    inspect.add_argument("--question", required=True, type=int)
    inspect.add_argument("--year", type=int)
    for field in ("session", "paper", "variant", "section", "question_id"):
        inspect.add_argument("--" + field.replace("_", "-"))
    inspect.add_argument("--format", choices=("text", "json", "html"), default="text")
    inspect.add_argument("--output", type=Path)
    report = commands.add_parser("report")
    report.add_argument("--clean-json", nargs="+", required=True, type=Path)
    report.add_argument("--output", type=Path, default=Path("docs/critical_thinking_problem_solving/tsa/CLEANING_ISSUES.md"))
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            print(
                f"Reported {write_report(args.clean_json, args.output)} categorized clean records"
            )
            return 0
        result = inspect_question(
            args.clean_json,
            source=args.source,
            question_number=args.question,
            **{
                field: getattr(args, field)
                for field in (
                    "year",
                    "session",
                    "paper",
                    "variant",
                    "section",
                    "question_id",
                )
            },
        )
        rendered = render_inspection(result, args.format)
        if args.output:
            output = protect_output(
                args.output, [result["question"]["raw_reference"]["path"]]
            )
            if output.resolve() == Path(result["clean_json"]).resolve():
                raise ValueError("Inspection cannot overwrite clean JSON")
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"Clean inspection failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
