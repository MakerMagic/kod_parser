"""BMAT RAW/CLEAN side-by-side QA, with separate upstream and cleaning issues."""

import argparse
import base64
import json
import os
from collections import Counter, defaultdict
from hashlib import sha256
from html import escape
from pathlib import Path

from parsers.blackstone.visual_inspection import read_png, resolve_asset

from .cleaner import validate_clean


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    source = Path(data["raw_reference"]["path"])
    if sha256(source.read_bytes()).hexdigest() != data["raw_reference"]["sha256"]:
        raise ValueError("Stale BMAT CLEAN: regenerate from current RAW first")
    validate_clean(data, json.loads(source.read_text(encoding="utf-8")))
    return data


def files(inputs):
    return sorted(
        {
            p.resolve()
            for root in inputs
            for p in (
                Path(root).glob("*.clean.json") if Path(root).is_dir() else [Path(root)]
            )
        }
    )


def inspect(path, number, output, *, data=None):
    data = data if data is not None else load(path)
    q = next(q for q in data["questions"] if q["question_number"] == number)
    content = render_html(data, q, path)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    from parsers.bmat.backtest import write_html

    write_html(output, content)
    return output


def render_html(data, q, path):
    """Use the TSA CLEAN renderer, not a parallel BMAT inspection design."""
    from copy import deepcopy

    from processors.normalization.blackstone.backtest import render_html as tsa_html

    shown = deepcopy(q)
    raw = q["raw_record"]
    shown["availability"] = {
        "main_body": bool(q["main_body"]),
        "main_question": bool(q["main_question"]),
        "options": bool(q["options"]),
        "pipeline_status": q["pipeline_status"],
        "pipeline_eligible": q["pipeline_eligible"],
    }
    shown["raw_component_comparison"] = {
        "Raw Main Body": raw["raw_components"]["main_body"],
        "Clean Main Body": q["main_body"],
        "Raw Main Question": raw["raw_components"]["main_question"],
        "Clean Main Question": q["main_question"],
        "Raw Main Answers": raw["options"],
        "Clean Main Answers": q["options"],
    }
    # Textual fraction normalization is the effective CLEAN answer. Its source
    # crop stays in the persisted record and expandable RAW comparison.
    for option in shown["options"]:
        if option.get("render_text_only"):
            option["source_math_images"] = option["images"]
            option["images"] = []
    # Validate asset identity before giving unchanged source refs to TSA's
    # renderer. Missing assets remain explicit issues, never invented pictures.
    asset_problems = []
    for asset in [*q["visual_assets"], *q["visual_previews"]]:
        try:
            png = read_png(resolve_asset(q["raw_reference"]["path"], asset["path"]))
            if sha256(png).hexdigest() != asset["sha256"]:
                raise ValueError("Asset hash mismatch")
        except (OSError, ValueError) as error:
            asset_problems.append(
                {"code": "inspection_asset_unavailable", "reason": str(error)}
            )
    result = {
        "question": shown,
        "document": data["document"],
        "clean_json": str(Path(path).resolve()),
        "raw_visual_issues": asset_problems,
        "cleaning_issues": q["cleaning_issues"],
    }
    html = tsa_html(result)
    unresolved = []
    for asset in q["visual_assets"]:
        if asset["belongs_to"] != "unknown":
            continue
        try:
            png = read_png(resolve_asset(q["raw_reference"]["path"], asset["path"]))
            unresolved.append(
                "<figure class='issue'><figcaption>Unresolved asset — not Main Body or an accepted option association: "
                + escape(asset["path"])
                + "</figcaption><img alt='Unresolved source asset' src='data:image/png;base64,"
                + base64.b64encode(png).decode("ascii")
                + "'></figure>"
            )
        except (OSError, ValueError):
            pass  # Missing reference is already explicit in inspection_asset_unavailable.
    if unresolved:
        html = html.replace(
            "<section id='issues'><h2>Visual Inspection Issues</h2>",
            "<section id='issues'><h2>Visual Inspection Issues</h2>"
            + "".join(unresolved),
            1,
        )
    addition = (
        "<section id='bmat-specific'><h2>BMAT-specific category</h2><pre>"
        + escape(json.dumps(q["bmat_filter"], ensure_ascii=False, indent=2))
        + "</pre></section>"
    )
    return html.replace(
        "<details><summary>Raw/original record",
        addition + "<details><summary>Raw/original record",
        1,
    )


def report(inputs, output, index_dir=None, all_html=False):
    groups = {"raw": defaultdict(dict), "cleaning": defaultdict(dict)}
    rows = []
    states = Counter()
    for path in files(inputs):
        data = load(path)
        for q in data["questions"]:
            row = {
                "year": q["metadata"]["year"],
                "question_number": q["question_number"],
                "question_id": q["question_id"],
                "status": q["pipeline_status"],
                "skip": q["bmat_filter"]["skip_from_pipeline"],
                "issues": q["cleaning_issues"],
                "clean_json": str(path),
            }
            rows.append(row)
            states[q["pipeline_status"]] += 1
            for i in q["cleaning_issues"]:
                groups[i["origin"]][i["code"]][q["question_id"]] = (row, i)
            if all_html:
                inspect(
                    path,
                    q["question_number"],
                    Path(index_dir)
                    / f"{row['year']}_q{row['question_number']:03}.html",
                    data=data,
                )
    counts = {
        origin: len(
            {identity for group in groups[origin].values() for identity in group}
        )
        for origin in groups
    }
    summary = {
        "records": len(rows),
        "status_counts": dict(states),
        "unique_upstream_issue_questions": counts["raw"],
        "unique_cleaning_specific_issue_questions": counts["cleaning"],
        "unique_issue_questions": sum(bool(r["issues"]) for r in rows),
    }
    lines = [
        "<!-- bmat-clean-report-v1 -->",
        "# BMAT cleaning issues",
        "",
        "Intentional skips remain stored and are not cleaning defects. Upstream defects are propagated, never repaired or concealed by cleaning.",
        "",
        "```json",
        json.dumps(summary, indent=2),
        "```",
        "",
    ]
    for origin, title in [
        ("raw", "A. Propagated RAW defects"),
        ("cleaning", "B. Cleaning-specific defects"),
    ]:
        lines.extend([f"## {title} ({counts[origin]} unique questions)", ""])
        if not groups[origin]:
            lines.extend(["None detected.", ""])
        for code, entries in sorted(groups[origin].items()):
            lines.extend(
                [
                    f"### {code} ({len(entries)} unique questions)",
                    "",
                    "| Year | Question | Status | Reason |",
                    "|---|---|---|---|",
                ]
            )
            for row, issue in entries.values():
                target = (
                    Path(index_dir or "inspections/critical_thinking_problem_solving/bmat/clean")
                    / f"{row['year']}_q{row['question_number']:03}.html"
                )
                link = os.path.relpath(
                    target.resolve(), Path(output).resolve().parent
                ).replace("\\", "/")
                reason = issue["reason"].replace("|", "\\|").replace("\n", " ")
                lines.append(
                    f"| {row['year']} | [{row['question_number']}]({link}) | {row['status']} | {reason} |"
                )
            lines.append("")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not output.read_text(encoding="utf-8").startswith(
        "<!-- bmat-clean-report-v1 -->"
    ):
        raise ValueError("Refusing unrelated report overwrite")
    output.write_text("\n".join(lines), encoding="utf-8")
    if index_dir:
        root = Path(index_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / "status.json").write_text(
            json.dumps(
                {"stage": "bmat_clean_qa", "summary": summary, "records": rows},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        html = [
            f"<tr><td>{r['year']}</td><td>{r['question_number']}</td><td>{r['status']}</td><td><a href='{r['year']}_q{r['question_number']:03}.html'>Inspect RAW/CLEAN</a></td></tr>"
            for r in rows
        ]
        (root / "index.html").write_text(
            "<!doctype html><meta charset='utf-8'><h1>BMAT CLEAN inspection</h1><input aria-label='Filter' placeholder='Year, number, status' oninput=\"for(const r of document.querySelectorAll('tbody tr'))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())\"><table><thead><tr><th>Year<th>Question<th>Status<th>Inspection</tr></thead><tbody>"
            + "".join(html)
            + "</tbody></table>",
            encoding="utf-8",
        )
    return summary


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=["report", "inspect"])
    cli.add_argument("--clean-json", nargs="+", default=["data/clean/bmat"])
    cli.add_argument("--output", type=Path)
    cli.add_argument("--index-dir", type=Path, default=Path("inspections/critical_thinking_problem_solving/bmat/clean"))
    cli.add_argument("--all-html", action="store_true")
    cli.add_argument("--year", type=int)
    cli.add_argument("--question", type=int)
    args = cli.parse_args(argv)
    if args.command == "report":
        print(
            json.dumps(
                report(
                    args.clean_json,
                    args.output or Path("docs/critical_thinking_problem_solving/bmat/BMAT_CLEANING_ISSUES.md"),
                    args.index_dir,
                    args.all_html,
                )
            )
        )
        return 0
    selected = [
        p for p in files(args.clean_json) if load(p)["document"]["year"] == args.year
    ]
    if len(selected) != 1 or args.question is None:
        cli.error("Select one year and question")
    print(
        inspect(
            selected[0],
            args.question,
            args.output or args.index_dir / f"{args.year}_q{args.question:03}.html",
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
