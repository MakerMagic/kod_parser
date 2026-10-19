"""Offline BMAT issue/status reporting and self-contained RAW inspection."""

import argparse
import base64
import json
import os
from collections import Counter, defaultdict
from hashlib import sha256
from html import escape
from pathlib import Path

from .parser import validate_raw
from .quality import status
from .skip_rules import ORDER


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_raw(data)
    return data


def files(inputs):
    return sorted(
        {
            p.resolve()
            for item in inputs
            for p in (
                Path(item).glob("*.raw.json") if Path(item).is_dir() else [Path(item)]
            )
        }
    )


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def report(inputs, output, *, index_dir=None):
    datasets = [(p, load(p)) for p in files(inputs)]
    tags, problems, documents = defaultdict(list), defaultdict(list), []
    totals, by_year = Counter(), {}
    all_rows = []
    for path, data in datasets:
        counts = Counter()
        for w in data["warnings"]:
            documents.append((data["year"], w))
        for q in data["questions"]:
            state, issues = status(data, q, path)
            counts[state] += 1
            row = {
                "year": data["year"],
                "number": q["question_number"],
                "pages": q["page_reference"],
                "status": state,
                "types": [t["type"] for t in q["bmat_filter"]["types"]],
                "issues": issues,
                "raw_json": str(path),
                "question_id": q["question_id"],
            }
            all_rows.append(row)
            for tag in q["bmat_filter"]["types"]:
                tags[tag["type"]].append((row, tag["reason"]))
            for issue in issues:
                problems[issue.split(":", 1)[0].split(" [", 1)[0]].append((row, issue))
        by_year[str(data["year"])] = dict(counts)
        totals.update(counts)
    unique_issues = {(r["year"], r["number"]) for r in all_rows if r["issues"]}
    summary = {
        "questions": len(all_rows),
        "status_counts": dict(totals),
        "unique_intentional_skips": totals["skipped"],
        "unique_parsing_issue_questions": len(unique_issues),
        "retained_without_parsing_issues": totals["retained"],
        "skip_tag_counts_overlapping": {t: len(tags[t]) for t in ORDER},
        "by_year": by_year,
        "document_issues": documents,
    }
    lines = [
        "<!-- bmat-raw-report-v1 -->",
        "# BMAT Section 1 RAW issues",
        "",
        "Intentional skips and parser defects are independent. Tag counts overlap; unique question counts do not. A skipped record may also retain a genuine parser defect. No finding is not a correctness certification.",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## A. Intentional BMAT-specific skips",
        "",
    ]

    def table(entries):
        out = ["| Year | Question | Pages | Evidence / issue |", "|---|---|---|---|"]
        for r, reason in entries:
            target = (
                Path(index_dir or "inspections_bmat")
                / f"{r['year']}_q{r['number']:03}.html"
            )
            link = os.path.relpath(
                target.resolve(), Path(output).resolve().parent
            ).replace("\\", "/")
            out.append(
                f"| {r['year']} | [{r['number']}]({link}) | {r['pages']['start_page']}–{r['pages']['end_page']} | {cell(reason)} |"
            )
        return out

    for t in ORDER:
        lines.extend(
            [f"### {t} ({len(tags[t])} unique questions)", "", *table(tags[t]), ""]
        )
    lines.extend(["## B. Genuine parsing issues", ""])
    for code, entries in sorted(problems.items()):
        seen = {(r["year"], r["number"]): (r, reason) for r, reason in entries}
        lines.extend(
            [
                f"### {code} ({len(seen)} unique questions)",
                "",
                *table(seen.values()),
                "",
            ]
        )
    lines.extend(
        [
            "## Document / range issues",
            "",
            *([f"- {year}: {cell(w)}" for year, w in documents] or ["None detected."]),
            "",
        ]
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not output.read_text(encoding="utf-8").startswith(
        "<!-- bmat-raw-report-v1 -->"
    ):
        raise ValueError("Refusing unrelated report overwrite")
    output.write_text("\n".join(lines), encoding="utf-8")
    if index_dir:
        root = Path(index_dir)
        root.mkdir(parents=True, exist_ok=True)
        payload = {"stage": "bmat_raw_qa", "summary": summary, "records": all_rows}
        (root / "status.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        links = [
            f"<tr><td>{r['year']}</td><td>{r['number']}</td><td>{r['status']}</td><td>{escape(', '.join(r['types']))}</td><td><a href='{r['year']}_q{r['number']:03}.html'>Inspect</a></td></tr>"
            for r in all_rows
        ]
        (root / "index.html").write_text(
            "<!doctype html><meta charset='utf-8'><title>BMAT RAW inspection</title><h1>BMAT RAW</h1><input aria-label='Filter' placeholder='Year, status or type' oninput=\"for(const r of document.querySelectorAll('tr'))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())\"><table><thead><th>Year<th>Question<th>Status<th>BMAT types<th>Inspection</thead><tbody>"
            + "".join(links)
            + "</tbody></table>",
            encoding="utf-8",
        )
    return summary


def inspect(path, question_number, output):
    path = Path(path).resolve()
    data = load(path)
    q = next(q for q in data["questions"] if q["question_number"] == question_number)
    state, issues = status(data, q, path)
    parts = [
        "<!doctype html><html lang='en'><meta charset='utf-8'><meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; img-src data:; style-src 'unsafe-inline'\"><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere}img{max-width:100%;height:auto}section{border-top:1px solid #bbb;padding:16px 0}.issue{background:#fff0dd}</style>",
        f"<h1>BMAT {data['year']} Section 1 — Q{question_number}</h1>",
        f"<p>Status: {state}</p>",
    ]

    def text_section(title, value):
        parts.extend(
            [
                f"<section><h2>{title}</h2><pre>{escape(value or '(not established)')}</pre></section>"
            ]
        )

    def image(asset):
        if not asset.get("path"):
            return "<p>Asset unavailable</p>"
        target = (path.parent / asset["path"]).resolve()
        if not target.is_relative_to(path.parent) or not target.exists():
            return "<p class='issue'>Asset missing/unsafe path</p>"
        content = target.read_bytes()
        if sha256(content).hexdigest() != asset["sha256"]:
            return "<p class='issue'>Asset hash mismatch</p>"
        return f"<figure><img src='data:image/png;base64,{base64.b64encode(content).decode()}'><figcaption>{escape(asset['image_id'])}; page {asset['page']}; {escape(str(asset['bbox']))}</figcaption></figure>"

    text_section(
        "BMAT-specific exclusion",
        json.dumps(q["bmat_filter"], ensure_ascii=False, indent=2),
    )
    text_section("Raw Main Body", q["raw_components"]["main_body"])
    parts.append(
        "<section><h2>Body visuals (resolved ownership only)</h2>"
        + "".join(image(a) for a in q["visual_assets"] if a["belongs_to"] == "question")
        + "</section>"
    )
    text_section("Raw Main Question", q["raw_components"]["main_question"])
    parts.append("<section><h2>Raw Main Answers</h2>")
    for option in q["options"]:
        parts.append(
            f"<h3>{option['label']}</h3><pre>{escape(option['text'])}</pre>"
            + "".join(image(a) for a in option["images"])
        )
    parts.append(
        "</section><section><h2>Unresolved visual ownership — not Main Body</h2>"
        + "".join(image(a) for a in q["visual_assets"] if a["belongs_to"] == "unknown")
        + "</section>"
    )
    parts.append(
        "<section><h2>Original source preview</h2>"
        + "".join(image(a) for a in q["visual_previews"])
        + "</section>"
    )
    text_section(
        "Issues / warnings",
        json.dumps(
            {
                "parsing_issues": issues,
                "raw_warnings": q["warnings"],
                "document_warnings": data["warnings"],
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    text_section(
        "Source / identity",
        json.dumps(
            {
                "source": data["input"],
                "key": q["source_question_key"],
                "pages": q["page_reference"],
                "raw_json": str(path),
            },
            indent=2,
        ),
    )
    text_section("Exact raw question block", q["raw"]["question_block"])
    parts.append("</html>")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(parts), encoding="utf-8")
    return state


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=["report", "inspect", "list"])
    cli.add_argument(
        "--raw-json", nargs="+", type=Path, default=[Path("data/raw/bmat")]
    )
    cli.add_argument("--year", type=int)
    cli.add_argument("--question", type=int)
    cli.add_argument("--status", choices=["retained", "skipped", "parser_review"])
    cli.add_argument("--type", dest="type_name", choices=ORDER)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--all-html", action="store_true")
    args = cli.parse_args(argv)
    paths = files(args.raw_json)
    if args.command == "report":
        result = report(
            paths,
            args.output or Path("docs/BMAT_RAW_ISSUES.md"),
            index_dir="inspections_bmat",
        )
        print(json.dumps(result, ensure_ascii=False))
    for path in paths:
        d = load(path)
        if args.year and args.year != d["year"]:
            continue
        for q in d["questions"]:
            state, issues = status(d, q, path)
            if (
                args.question
                and q["question_number"] != args.question
                or args.status
                and state != args.status
                or args.type_name
                and not any(
                    t["type"] == args.type_name for t in q["bmat_filter"]["types"]
                )
            ):
                continue
            if args.command == "list":
                print(
                    d["year"],
                    q["question_number"],
                    state,
                    [t["type"] for t in q["bmat_filter"]["types"]],
                    issues,
                )
            elif args.command == "inspect" or args.all_html:
                inspect(
                    path,
                    q["question_number"],
                    args.output
                    if args.command == "inspect" and args.output
                    else Path(
                        f"inspections_bmat/{d['year']}_q{q['question_number']:03}.html"
                    ),
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
