"""Current, unique-record BMAT classification QA from persisted output."""

import json
from collections import Counter, defaultdict
from hashlib import sha256
from html import escape
from pathlib import Path

from parsers.bmat.backtest import write_html
from processors.normalization.bmat.backtest import load, render_html

from .core import OWNER
from .taxonomy import validate


def cell(value):
    """Metadata table cells must not acquire source-text rows/newlines."""
    return " ".join(str(value).split()).replace("|", "/")


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
    from categorization.core import verify_refs

    from .review import load as load_review

    verify_refs(
        [
            r
            for r in [
                data.get("model_reference"),
                data.get("review_reference"),
                *data.get("definition_references", []),
            ]
            if r
        ]
    )
    decisions = (
        load_review(data["review_reference"]["path"])
        if data.get("review_reference")
        else {}
    )
    for row in data["records"]:
        validate(row["categorization"])
        reviewed = row["categorization"].get("review")
        if reviewed:
            from categorization.core import digest
            from categorization.review import visual_references

            from .review import visual_row

            key = digest(row["question"])
            decision = decisions.get(key)
            refs, missing = visual_references(visual_row(row))
            if (
                not decision
                or missing
                or refs != decision["visual_references"]
                or reviewed["question_sha256"] != key
            ):
                raise ValueError("Stale BMAT reviewed question/visual evidence")
            a = row["categorization"]
            if (
                a["rationale"] != decision["evidence"]
                or (decision.get("input_issue") and a["status"] != "needs_review")
                or (
                    not decision.get("input_issue")
                    and a["patterns"] != [decision["category_id"]]
                )
            ):
                raise ValueError("Persisted BMAT result differs from verified review")
            verify_refs(refs)
    return data


def render_record(record, source, reference, matched=None):
    """Existing user inspection view; never needed to read a canonical record."""
    q, a = record["question"], record["categorization"]
    html = render_html(source, q, reference)
    if record.get("matching_reference"):
        from processors.matching.bmat.backtest import inspect

        ref = record["matching_reference"]
        m = matched["records"][int(ref["json_pointer"].rsplit("/", 1)[1])]
        html = inspect(m)
    addition = (
        "<section id='categorization'><h2>Categorization</h2>"
        f"<p>Assigned category: {escape(' / '.join([a['category'] or 'Unresolved', *a['subcategories']]))}</p>"
        f"<p>Canonical ID: {escape(', '.join(a['patterns']) or '—')}; status: {escape(a['status'])}</p>"
        f"<p>Evidence: {escape(a['rationale'])}</p>"
        + (
            "<p>Previous categorization: "
            + escape(json.dumps(a["review"]["baseline"], ensure_ascii=False))
            + "</p>"
            if a.get("review")
            else ""
        )
        + "<details><summary>Attribution diagnostics and verified review evidence</summary><pre>"
        + escape(json.dumps(a, ensure_ascii=False, indent=2))
        + "</pre></details>"
        f"<p>Matching status: {escape(record['matching_status'])}. Attribution remains independent of explanation wording.</p></section>"
    )
    return html.replace(
        "<details><summary>Raw/original record",
        addition + "<details><summary>Raw/original record",
        1,
    )


def report(path, issues, guide, inspections, *, render=True, year=None, question=None):
    data = read(path)
    root = Path(inspections)
    if render:
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
        y, number = q["metadata"]["year"], q["question_number"]
        filename = f"{y}_q{number:03}.html"
        if record.get("matching_reference"):
            ref = record["matching_reference"]
            if {k: ref[k] for k in ("path", "sha256")} != data["matching_source"]:
                raise ValueError("Categorization matching reference changed")
            m = matched["records"][int(ref["json_pointer"].rsplit("/", 1)[1])]
            if m["question"] != q or m["status"] != record["matching_status"]:
                raise ValueError("Categorization matching snapshot changed")
        selected = (year is None or y == year) and (
            question is None or number == question
        )
        if render and selected:
            write_html(
                root / filename, render_record(record, source, reference, matched)
            )
        links.append((y, number, a, filename))
        if a["status"] == "needs_review":
            code = "upstream_defect" if q["cleaning_issues"] else a["issues"][0]["code"]
            groups[code].append((y, number, a, filename))

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
        "Only current unresolved decisions are active issues. Each supported/intentional-skip result has one canonical category. Categorization is not a claim of successful matching or upstream repair.",
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
        text += [f"| {y} | {n} | {cell(a['rationale'])} |" for y, n, a, f in entries]
        text += [""]
    Path(issues).parent.mkdir(parents=True, exist_ok=True)
    Path(issues).write_text("\n".join(text), encoding="utf-8")
    trail = [
        "# BMAT categorization backtesting",
        "",
        "Reads persisted CLEAN-based dominant-task attribution with hash-verified matching context, TSA model and content-bound rulebook review. Correct Answer, Main/Final Explanation, body/option assets and source screenshots remain visible. All records, including excluded and unresolved questions, remain inspectable. Existing BMAT-specific taxonomy and exclusion precedence are preserved; TSA multi-label behavior is not changed.",
        "",
        "Reproduce: `python -m categorization.bmat run` (or `python -m processors.bmat categorize run`). Review source: `categorization/bmat/decisions.tsv`; rebind verified decisions with `python -m categorization.bmat bind-review`. A changed question or asset needs fresh review; unseen weak-evidence cases abstain. No parsing, cleaning, answer matching or explanation generation runs in categorization.",
        "",
        "## User-requested inspection",
        "",
        "`python -m categorization.bmat report --year 2021 --question 25` exports only the selected question. Omit `--question` for a requested year export; omit both selectors only for an explicitly requested full export. `run` writes canonical categories and current issue indexes without rendering question HTML.",
        "",
        "Canonical input is `data/categorized/bmat/questions.categorized.json`. Read `records` by identity or categorization issue code directly; open the referenced assets when needed. Internal candidates are not accepted primary categories. BMAT-specific types remain separate from normal TSA categories. Blocked upstream records and source reviews are not repaired by categorization.",
        "",
    ]
    distribution = Counter(
        a["patterns"][0]
        for _, _, a, _ in links
        if a["status"] in {"supported", "intentional_skip"}
    )
    Path(guide).write_text("\n".join(trail).rstrip() + "\n", encoding="utf-8")
    if render:
        write_html(
            root / "index.html",
            "<!doctype html><meta charset='utf-8'><h1>BMAT categorization</h1><table>"
            + "".join(
                f"<tr><td>{y}</td><td><a href='{f}'>Q{n}</a></td><td>{a['status']}</td><td>{escape(a['rationale'])}</td></tr>"
                for y, n, a, f in links
                if (year is None or y == year) and (question is None or n == question)
            )
            + "</table>",
        )
    return {
        "records": len(seen),
        "unique_review_questions": rows,
        "review_reasons": dict(Counter({k: len(v) for k, v in groups.items()})),
        "statuses": data["summary"],
        "categorized": sum(distribution.values()),
        "distribution": dict(distribution),
    }
