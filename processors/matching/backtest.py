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
        refs += [
            {
                "path": str(
                    resolve_asset(record["answer_reference"]["path"], asset["path"])
                ),
                "sha256": asset["sha256"],
            }
            for asset in a.get("visual_previews", [])
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
    return {
        "matched_json": str(Path(path).resolve()),
        "record": record,
        "live_inspection_issues": live,
    }


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
    section(
        "main-explanation",
        "Main Explanation",
        "".join(text(p["text"]) for p in explanation.get("paragraphs", []))
        or text(None),
    )
    wrong = []
    for block in explanation.get("bulleted_blocks", []):
        if block.get("role", "").startswith("incorrect_choices"):
            wrong.append(text(block.get("transition")))
            if block["role"] == "incorrect_choices_unmapped":
                wrong.append(
                    "<p class='issue'>Individual option mapping unresolved; no labels inferred.</p>"
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
        }
    )
    for asset in (a or {}).get("visual_previews", []):
        try:
            png = read_png(resolve_asset(r["answer_reference"]["path"], asset["path"]))
            answer_source += f"<figure><figcaption>Answer source page {asset['page']}</figcaption><img alt='Original explanation' src='data:image/png;base64,{base64.b64encode(png).decode('ascii')}'></figure>"
        except (OSError, ValueError) as error:
            answer_source += "<p class='issue'>" + escape(str(error)) + "</p>"
    answer_source += (
        "<details><summary>Raw explanation excerpt</summary>"
        + text((a or {}).get("raw", {}).get("source_excerpt"))
        + "</details>"
    )
    section("answer-source", "Answer / Explanation Source", answer_source)
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
                "answer_parsing": (a or {}).get("warnings"),
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
