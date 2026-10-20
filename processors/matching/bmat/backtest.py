"""Inspect persisted BMAT matches/deferred sources using existing question views."""

import base64
import json
import os
from collections import Counter
from hashlib import sha256
from html import escape
from pathlib import Path

from processors.matching.explanation import build_final_explanation
from processors.matching.storage import load_matched
from processors.normalization.bmat.backtest import load as load_clean
from processors.normalization.bmat.backtest import render_html as question_html

from .core import eligibility


def dump(value):
    return "<pre>" + escape(json.dumps(value, ensure_ascii=False, indent=2)) + "</pre>"


def render_blocks(blocks, assets):
    rendered = []
    for b in blocks:
        if b["type"] == "paragraph":
            rendered.append("<p class='text'>" + escape(b["text"]) + "</p>")
        elif b["type"] == "list":
            tag = "ol" if b.get("ordered") else "ul"
            rendered.append(
                "<"
                + tag
                + ">"
                + "".join(
                    "<li class='text'>" + escape(i["text"]) + "</li>"
                    for i in b["items"]
                )
                + "</"
                + tag
                + ">"
            )
        elif b["type"] == "visual":
            asset = next(
                (
                    a
                    for a in assets
                    if a.get("asset_index") == b.get("asset_index")
                    and b.get("asset_index") is not None
                    or a.get("source_url") == b.get("source_url")
                ),
                None,
            )
            if not asset:
                rendered.append(
                    "<p>Unresolved source visual: "
                    + escape(b.get("source_url", ""))
                    + "</p>"
                )
                continue
            path = Path(asset.get("path", asset.get("local_path", "")))
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != asset.get(
                "sha256"
            ):
                raise ValueError("Explanation visual missing/changed")
            mime = asset.get("content_type", "image/png")
            rendered.append(
                "<figure><img style='max-width:100%;height:auto' alt='Worked explanation source visual' src='data:"
                + escape(mime)
                + ";base64,"
                + base64.b64encode(path.read_bytes()).decode("ascii")
                + "'></figure>"
            )
    return "".join(rendered)


def inspect(record):
    q, answer = record["question"], record["answer"]
    if q:
        html = question_html(
            {"document": record["question_document"]},
            q,
            record["question_reference"]["path"],
        )
    else:
        html = "<!doctype html><meta charset='utf-8'><body><main></main></body>"
    parts = []

    def section(identifier, title, text):
        parts.append(
            f"<section id='{identifier}'><h2>{escape(title)}</h2>{text}</section>"
        )

    section(
        "match-identity",
        "BMAT Matching Identity",
        dump({**record["identity"], "status": record["status"]}),
    )
    section(
        "correct-answer",
        "Correct Answer",
        escape(record.get("correct_answer") or "Not attached / unresolved"),
    )
    final = record["final_explanation"]
    caution = (
        "<p class='issue'>Existing source content is preserved for review, not a verified successful match.</p>"
        if final["blocks"] and record["status"] != "matched"
        else ""
    )
    section(
        "main-explanation",
        "Main Explanation",
        caution
        + "<p>This source supplies one full explanation, preserved below without artificial subcomponents.</p>"
        "<div id='final-explanation'><h3>Final Explanation</h3>"
        + render_blocks(
            final["blocks"],
            (answer or {}).get("explanation", {}).get("visual_assets", []),
        )
        + "</div>"
        if final["blocks"]
        else "<div id='final-explanation'><h3>Final Explanation</h3><p>No accepted explanation attached; see deferred source below.</p></div>",
    )
    section(
        "explanation-by-ai",
        "Explanation by AI: False",
        "<p>Source worked solution; no generated explanation.</p>",
    )
    section(
        "explanation-source",
        "Explanation Source",
        dump(
            {
                "source": (answer or {}).get("source_document"),
                "answer_extraction": (answer or {}).get("answer_extraction"),
                "header_evidence": (answer or {})
                .get("raw", {})
                .get("header_extraction"),
                "reference": record["answer_reference"],
            }
        ),
    )
    for candidate in record["answer_candidates"]:
        a = candidate["record"]
        blocks = a.get("explanation", {}).get(
            "blocks", a.get("raw", {}).get("source_blocks", [])
        )
        assets = a.get("explanation", {}).get(
            "visual_assets", a.get("source_assets", [])
        )
        section(
            "deferred-source",
            "Unattached Source — not a successful match",
            dump(
                {
                    "reference": candidate["reference"],
                    "source": a.get("source_document"),
                    "warnings": a.get("warnings"),
                    "correct_answer": a.get("correct_answer"),
                }
            )
            + render_blocks(blocks, assets),
        )
    for index, item in enumerate(record.get("supplied_imports", []), 1):
        a = item["record"]
        section(
            f"supplied-source-{index}",
            "User-supplied explanation — text only",
            dump(
                {
                    "import_status": item["import_status"],
                    "comparison": item["comparison"],
                    "source": a["source_document"],
                    "reference": item["reference"],
                    "correct_answer": a["correct_answer"],
                    "warnings": a["warnings"],
                    "review_notes": a["review_notes"],
                }
            )
            + render_blocks(a["explanation"]["blocks"], []),
        )
    section(
        "matching-metadata",
        "Matching Metadata",
        dump(
            {
                "status": record["status"],
                **record["matching"],
                "question_reference": record["question_reference"],
            }
        ),
    )
    section(
        "matching-issues",
        "Matching / Upstream Issues",
        dump(
            {"matching": record["issues"], "upstream": (q or {}).get("cleaning_issues")}
        ),
    )
    # Keep the student-facing answer/explanation alongside the question, before
    # original-source and diagnostic details. Render the full explanation once.
    evidence = "".join(parts[:4])
    marker = "<section id='original-screenshot'>"
    if marker in html:
        html = html.replace(marker, evidence + marker, 1)
    else:
        html = html.replace("</main>", evidence + "</main>", 1)
    return html.replace("</main>", "".join(parts[4:]) + "</main>", 1)


def report(path, issues, guide, folder, *, render=True, year=None, question=None):
    data = load_matched(path)
    for ref in data["inputs"]:
        if sha256(Path(ref["path"]).read_bytes()).hexdigest() != ref["sha256"]:
            raise ValueError("Stale matched output; regenerate before backtesting")
    root = Path(folder)
    if render:
        root.mkdir(parents=True, exist_ok=True)
    counts = Counter(r["status"] for r in data["records"])
    if dict(counts) != data["summary"]["statuses"]:
        raise ValueError("Matched summary differs from persisted records")
    guide = Path(guide)
    guide.parent.mkdir(parents=True, exist_ok=True)
    issues = Path(issues)
    issues.parent.mkdir(parents=True, exist_ok=True)
    rows, active = [], []
    clean_cache = {}
    for r in data["records"]:
        ident = r["identity"]
        q = r["question"]
        if q:
            ref = r["question_reference"]
            if ref["path"] not in clean_cache:
                clean_cache[ref["path"]] = load_clean(ref["path"])
            index = int(ref["json_pointer"].split("/")[-1])
            if q != clean_cache[ref["path"]]["questions"][index]:
                raise ValueError("Persisted question snapshot changed")
        if r["status"] == "matched" and (
            eligibility(q)
            or r["final_explanation"]
            != build_final_explanation(r["answer"], r["answer_reference"])
        ):
            raise ValueError("An ineligible/stale explanation was marked matched")
        filename = f"{ident['year']}_q{ident['question_number']:03}.html"
        if (
            render
            and (year is None or ident["year"] == year)
            and (question is None or ident["question_number"] == question)
        ):
            (root / filename).write_text(inspect(r), encoding="utf-8")
        row = f"| {ident['year']} | {ident['question_number']} | {r['status']} | {r.get('correct_answer') or '—'} |"
        rows.append(row)
        if r["status"] not in {"matched", "intentionally_skipped"}:
            active.append(row)
    index_rows = [
        f"<li><a href='{r['identity']['year']}_q{r['identity']['question_number']:03}.html'>{r['identity']['year']} Q{r['identity']['question_number']}: {escape(r['status'])}</a></li>"
        for r in data["records"]
        if (year is None or r["identity"]["year"] == year)
        and (question is None or r["identity"]["question_number"] == question)
    ]
    if render:
        (root / "index.html").write_text(
            "<!doctype html><meta charset='utf-8'><h1>BMAT matching inspections</h1><ul>"
            + "".join(index_rows)
            + "</ul>",
            encoding="utf-8",
        )
    title = "# BMAT Section 1 matching backtesting\n\nRead-only views of canonical matches. Excluded/deferred sources are explicitly not accepted matches.\n\n"
    title += (
        "## Reproduce independently\n\n```powershell\n"
        "python -m acquisition.bmat_worked_solutions\n"
        "python -m parsers.bmat_worked_solutions\n"
        "python -m parsers.bmat_supplied_explanations data/input/bmat_supplied_explanations/2026-10-19.txt\n"
        "python -m processors.matching.bmat run\n"
        "python -m processors.matching.bmat report\n```\n\n"
        "Acquisition uses hash-verified local cache. Parser and matching need no network. "
        "An unavailable external mirror host is deferred after verified connection/TLS failures; "
        "use acquisition `--retry-failed-hosts` explicitly after connectivity returns. "
        "No answers are inferred from prose. Source-image answer headers are locally OCR-read, "
        "checked against the page identity, and retained with bbox/hash evidence; full explanation images are preserved. "
        "The 2014 Section 1 index links a separate specimen PDF, not individual solutions; "
        "that file is not substituted for these question records.\n\n"
        "User-supplied material is a separate hash/line-bound local source. Imports never add images, overwrite an existing explanation, or bypass BMAT eligibility. "
        "Same-answer variants remain separate; explicit source cautions remain review issues. A missing question header is not inferred from neighboring prose.\n\n"
    )
    table = "\n| Year | Question | Status | Correct answer |\n|---|---|---|---|\n"
    summary = (
        "```json\n"
        + json.dumps(
            {
                **data["summary"],
                "supplied_imports": data.get("supplied_import_summary"),
            },
            indent=2,
        )
        + "\n```\n"
    )
    title += "## Select a user-requested inspection\n\n```powershell\npython -m processors.matching.bmat report --year 2021 --question 25\n```\n\nOnly explicitly requested `report` commands render HTML. Omit `--question` to select a year; omit both selectors only when a complete export is actually requested. `run` persists matching and issues without HTML exports. Canonical data is `data/merged/bmat/questions.matched.json`; filter `records` by identity/status to read a question directly. Referenced assets can be opened directly. Correct Answer and Main/Final Explanation remain separate; reviews, conflicts, provenance and upstream exclusions remain visible. Counts and individual records belong to JSON and issue indexes, not this guide.\n"
    guide.write_text(title, encoding="utf-8")
    warnings = Counter(
        w
        for a in data["source_unresolved"]
        for w in a.get("warnings", [a.get("error", "download_failed")])
    )
    source_groups = {}
    for a in data["source_unresolved"]:
        ident = (a["year"], a["question_number"])
        for warning in a.get("warnings", ["download_failed"]):
            source_groups.setdefault(warning, set()).add(ident)
    content = (
        "# BMAT Section 1 matching issues\n\nCounts are unique question records. Intentional skips are policy exclusions, not parser errors.\n\n"
        + summary
    )
    content += (
        "\n## Source acquisition/parser issues\n\n"
        + "```json\n"
        + json.dumps(
            {
                "acquisition_issues": data["source_issues"],
                "unresolved_source_reasons": dict(warnings),
                "unique_questions_by_source_reason": {
                    k: len(v) for k, v in source_groups.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n```\n"
    )
    content += "\n## Active matching / deferred records\n"
    for status in sorted(counts):
        if status in {"matched", "intentionally_skipped"}:
            continue
        grouped = [row for row in active if f"| {status} |" in row]
        content += (
            f"\n### {status} ({len(grouped)} unique questions)\n"
            + table
            + "\n".join(grouped)
            + "\n"
        )
    content += (
        "\n## Intentional exclusions\n\n"
        + str(counts["intentionally_skipped"])
        + " targets remain skipped. Full per-question reasons/source candidates are available in the [backtest]("
        + Path(os.path.relpath(guide, issues.parent)).as_posix()
        + ").\n"
    )
    issues.write_text(content, encoding="utf-8")
    return data["summary"]
