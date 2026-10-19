"""Current, unique-record BMAT classification QA from persisted output."""

import json
import os
from collections import Counter, defaultdict
from hashlib import sha256
from html import escape
from pathlib import Path

from parsers.bmat.backtest import write_html
from processors.normalization.bmat.backtest import load, render_html

from .core import OWNER


def read(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("owner") != OWNER:
        raise ValueError("Not BMAT categorization output")
    taxonomy = data["taxonomy_reference"]
    if sha256(Path(taxonomy["path"]).read_bytes()).hexdigest() != taxonomy["sha256"]:
        raise ValueError("Stale BMAT categorization taxonomy")
    if data["summary"] != dict(
        Counter(r["categorization"]["status"] for r in data["records"])
    ):
        raise ValueError("Categorization summary does not match persisted records")
    for source in data["sources"]:
        if sha256(Path(source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Stale BMAT categorization input")
    matching_source = data.get("matching_source")
    if (
        matching_source
        and sha256(Path(matching_source["path"]).read_bytes()).hexdigest()
        != matching_source["sha256"]
    ):
        raise ValueError("Stale BMAT categorization matching context")
    return data


def report(path, issues, guide, inspections):
    data = read(path)
    root = Path(inspections)
    root.mkdir(parents=True, exist_ok=True)
    loaded = {}
    groups = defaultdict(list)
    links = []
    seen = set()
    matched = None
    if data.get("matching_source"):
        from processors.matching.storage import load_matched

        matched = load_matched(data["matching_source"]["path"])
    for record in data["records"]:
        if record["question_id"] in seen:
            raise ValueError("Duplicate categorized identity")
        seen.add(record["question_id"])
        q = record["question"]
        reference = record["question_reference"]["path"]
        if reference not in loaded:
            loaded[reference] = load(reference)
        source = loaded[reference]
        index = int(record["question_reference"]["json_pointer"].rsplit("/", 1)[1])
        if q != source["questions"][index]:
            raise ValueError("Categorization question snapshot changed")
        a = record["categorization"]
        year, number = q["metadata"]["year"], q["question_number"]
        filename = f"{year}_q{number:03}.html"
        html = render_html(source, q, reference)
        if record.get("matching_reference"):
            from processors.matching.bmat.backtest import inspect

            ref = record["matching_reference"]
            if {k: ref[k] for k in ("path", "sha256")} != data["matching_source"]:
                raise ValueError("Categorization matching reference changed")
            m = matched["records"][int(ref["json_pointer"].rsplit("/", 1)[1])]
            if m["question"] != q or m["status"] != record["matching_status"]:
                raise ValueError("Categorization matching snapshot changed")
            html = inspect(m)
        addition = (
            "<section id='categorization'><h2>Categorization</h2><pre>"
            + escape(json.dumps(a, ensure_ascii=False, indent=2))
            + "</pre>"
            f"<p>Matching status: {escape(record['matching_status'])}. Attribution remains independent of explanation wording.</p></section>"
        )
        html = html.replace(
            "<details><summary>Raw/original record",
            addition + "<details><summary>Raw/original record",
            1,
        )
        write_html(root / filename, html)
        links.append((year, number, a, filename))
        if a["status"] == "needs_review":
            code = "upstream_defect" if q["cleaning_issues"] else a["issues"][0]["code"]
            groups[code].append((year, number, a, filename))

    def relative(target, base):
        return os.path.relpath(
            Path(target).resolve(), Path(base).resolve().parent
        ).replace("\\", "/")

    rows = sum(len(v) for v in groups.values())
    skipped_upstream = sum(
        r["categorization"]["status"] == "intentional_skip"
        and bool(r["question"]["cleaning_issues"])
        for r in data["records"]
    )
    text = [
        "<!-- bmat-categorization-report-v1 -->",
        "# BMAT categorization issues",
        "",
        "Only current unresolved decisions are active issues. Intentional skips and unattempted normal attribution are counted separately; neither is a successfully matched dataset.",
        "Independent upstream defects on skipped records remain in BMAT_RAW_ISSUES.md and BMAT_CLEANING_ISSUES.md; exclusion does not repair them.",
        "",
        "```json",
        json.dumps(
            {
                "records": len(seen),
                "unique_review_questions": rows,
                "statuses": data["summary"],
                "skipped_with_upstream_defects": skipped_upstream,
            },
            indent=2,
        ),
        "```",
        "",
    ]
    for code, entries in sorted(groups.items()):
        text += [
            f"## {code} ({len(entries)} unique questions)",
            "",
            "| Year | Question | Reason |",
            "|---|---|---|",
        ]
        text += [
            f"| {y} | [{n}]({relative(root / f, issues)}) | {a['rationale'].replace('|', '/')} |"
            for y, n, a, f in entries
        ]
        text += [""]
    Path(issues).parent.mkdir(parents=True, exist_ok=True)
    Path(issues).write_text("\n".join(text), encoding="utf-8")
    trail = [
        "# BMAT categorization backtesting",
        "",
        "Reads persisted CLEAN-based task attribution with hash-verified matching context where available. Correct Answer, Main/Final Explanation and source screenshots are shown together; attribution does not infer categories from explanation wording. BMAT exclusions have precedence. All records remain inspectable.",
        "",
        "Reproduce: `python -m categorization.bmat run` (or `python -m processors.bmat categorize run`). Refresh exclusion evidence independently with `python -m parsers.bmat.skip_rules data/raw/bmat --overwrite`, then regenerate CLEAN before categorization. No PDF or answer matching runs in categorization.",
        "",
        f"- [Inspection index]({relative(root / 'index.html', guide)})",
        f"- [Current issues]({relative(issues, guide)})",
        "",
        "| Year | Question | Status | Result / evidence |",
        "|---|---|---|---|",
    ]
    for y, n, a, f in links:
        label = (
            " / ".join([a["category"] or "", *a["subcategories"]]).strip(" /")
            or a["rationale"]
        )
        trail.append(
            f"| {y} | [{n}]({relative(root / f, guide)}) | {a['status']} | {label.replace('|', '/')} |"
        )
    Path(guide).write_text("\n".join(trail) + "\n", encoding="utf-8")
    write_html(
        root / "index.html",
        "<!doctype html><meta charset='utf-8'><h1>BMAT categorization</h1><table>"
        + "".join(
            f"<tr><td>{y}</td><td><a href='{f}'>Q{n}</a></td><td>{a['status']}</td><td>{escape(a['rationale'])}</td></tr>"
            for y, n, a, f in links
        )
        + "</table>",
    )
    return {
        "records": len(seen),
        "unique_review_questions": rows,
        "review_reasons": dict(Counter({k: len(v) for k, v in groups.items()})),
        "statuses": data["summary"],
    }
