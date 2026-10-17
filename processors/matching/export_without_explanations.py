"""Offline, read-only Markdown views of known answers without explanations."""

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from .storage import load_matched, protect_output


def identity(record):
    value = record.get("identity", record)
    return value["year"], value["section"], value["question_number"]


def has_explanation(record):
    """Uncertain/unplaced/source/manual/current AI content is still content.

    Rejected generation audit candidates and answer-key row previews are not
    explanations. No AI modules/providers are imported by this exporter.
    """
    final = record.get("final_explanation") or {}
    if final.get("blocks") or final.get("unplaced_components"):
        return True
    answers = [
        record.get("answer"),
        *[c["record"] for c in record.get("answer_candidates", [])],
    ]
    for answer in answers:
        explanation = (answer or {}).get("explanation") or {}
        if any(
            explanation.get(field)
            for field in (
                "main_explanation",
                "blocks",
                "paragraphs",
                "bulleted_blocks",
                "choice_analysis",
                "other_lists",
                "visual_assets",
            )
        ):
            return True
    return bool(record.get("explanation"))


def select_records(data, keys, years):
    """Cross-check stored answers against independent answer intermediates."""
    records = {}
    for record in data["records"]:
        key = identity(record)
        if key in records:
            raise ValueError(f"Duplicate matched identity: {key}")
        records[key] = record
    rows, omitted = defaultdict(list), defaultdict(list)
    for key in sorted(set(records) | set(keys)):
        if key[0] not in years:
            continue
        record = records.get(
            key,
            {
                "identity": dict(zip(("year", "section", "question_number"), key)),
                "status": "missing_question",
                "question": None,
            },
        )
        if has_explanation(record):
            omitted[key[0]].append((key[2], "explanation_exists"))
            continue
        candidates = [
            v
            for v in (
                record.get("correct_answer"),
                (record.get("answer") or {}).get("correct_answer"),
            )
            if v
        ]
        source_keys = keys.get(key, [])
        candidates += [a.get("correct_answer") for a in source_keys]
        labels = set(candidates)
        if (
            len(source_keys) > 1
            or len(labels) != 1
            or not all(isinstance(v, str) and re.fullmatch(r"[A-Z]", v) for v in labels)
        ):
            omitted[key[0]].append((key[2], "missing_or_ambiguous_answer_key"))
            continue
        rows[key[0]].append((record, labels.pop(), source_keys))
    return rows, omitted


def text(value):
    if not isinstance(value, str) or not value:
        return "[Unavailable in the cleaned record.]"
    value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    value = re.sub(r"([*_`])", r"\\\1", value)
    lines = value.split("\n")
    return "\n".join(
        line + ("  " if line and i + 1 < len(lines) and lines[i + 1] else "")
        for i, line in enumerate(lines)
    )


def link(label, target, output):
    path = Path(target).resolve()
    relative = Path(os.path.relpath(path, output.parent.resolve())).as_posix()
    return f"[{label}](<{relative}>)"


def asset_lines(asset, question, record, output, *, answer=False):
    selected = asset.get("clean_asset") if answer else None
    selected = selected or asset
    base = (
        record.get("question_reference", {}).get("path")
        if selected.get("path_base") == "clean_json_parent"
        else question.get("raw_reference", {}).get("path")
    )
    if not selected.get("path") or not base:
        return [
            f"[Visual reference unavailable: {asset.get('image_id', asset.get('asset_id', 'unknown'))}]",
            "",
        ]
    path = Path(base).parent / selected["path"]
    label = f"Visual {asset.get('image_id', asset.get('asset_id', ''))}"
    lines = [
        "!" + link(label, path, output),
        "",
        "Asset: " + link(selected["path"], path, output),
        "",
    ]
    if not path.is_file():
        lines += ["**Missing asset file; reference preserved.**", ""]
    return lines


def render_year(year, rows, omitted, data, source, output):
    matched = sum(identity(r)[0] == year for r in data["records"])
    lines = [
        f"# Questions without explanations — {year}",
        "",
        f"Year: {year}  ",
        f"Total questions listed: {len(rows)}",
        "",
        "Only the correct-answer key is available for these records; no source/manual or current matched explanation is present.",
        "",
        f"Matched records checked: {matched}. Excluded: {len(omitted)}. Unresolved question structure is retained, not repaired.",
        "",
    ]
    if omitted:
        lines += [
            "Excluded records: "
            + "; ".join(f"Q{q}: {reason}" for q, reason in omitted),
            "",
        ]
    for record, correct, _key_sources in rows:
        question = record.get("question") or {}
        ident = record["identity"]
        lines += [
            f"## Question {ident['question_number']}",
            "",
            f"Year: {year}; section: {ident['section']}",
            "",
            "### Main Body",
            "",
        ]
        assets = {
            a.get("image_id", a.get("asset_id")): a
            for a in question.get("visual_assets", [])
        }
        used = set()
        for block in question.get("main_body", []):
            if block.get("type") == "visual":
                asset_id = block.get("asset_id")
                lines += asset_lines(
                    assets.get(asset_id, {"asset_id": asset_id}),
                    question,
                    record,
                    output,
                )
                used.add(asset_id)
            else:
                lines += [text(block.get("text")), ""]
        if not question.get("main_body"):
            lines += ["[No separate Main Body recorded.]", ""]
        lines += [
            "### Main Question",
            "",
            text(question.get("main_question")),
            "",
            "### Answers",
            "",
        ]
        for option in question.get("options", []):
            lines += [f"#### {option.get('label') or '[Label unavailable]'}", ""]
            if option.get("text"):
                lines += [text(option["text"]), ""]
            for asset in option.get("images", []):
                lines += asset_lines(asset, question, record, output, answer=True)
                used.add(asset.get("image_id", asset.get("asset_id")))
            if not option.get("text") and not option.get("images"):
                lines += ["[Option content unavailable.]", ""]
        if not question.get("options"):
            lines += ["[Answer options unavailable.]", ""]
        extra = [a for key, a in assets.items() if key not in used]
        if extra:
            lines += [
                "### Additional / Unassigned Visual References",
                "",
                "Ownership remains as stored; no association is inferred here.",
                "",
            ]
            for asset in extra:
                lines += asset_lines(asset, question, record, output)
        lines += [
            f"**Correct answer:** {correct}",
            "",
            "### Traceability / Availability",
            "",
            f"- Match status: {record.get('status', 'unavailable')}",
            f"- Question record: `{question.get('question_id', 'unavailable')}`",
        ]
        issues = [
            f"{i.get('code', 'issue')}: {i.get('reason', '')}"
            for i in record.get("issues", []) + question.get("cleaning_issues", [])
        ]
        issues += question.get("raw_warnings", []) + question.get("warnings", [])
        labels = [o.get("label") for o in question.get("options", [])]
        if record.get("status") != "matched" or labels.count(correct) != 1:
            issues.append(
                "Known source answer key shown without resolving the missing/ambiguous option mapping."
            )
        if not question.get("main_question"):
            issues.append(
                "Main Question unavailable; original readable question text retained below."
            )
            lines += [
                "",
                "Readable unsplit question text:",
                "",
                text(question.get("question_text")),
                "",
            ]
        for issue in dict.fromkeys(issues):
            lines.append("- Review: " + text(issue))
        lines += ["", "---", ""]
    return "\n".join(lines)


def export(source, output_dir, years=(2017, 2018, 2019)):
    source, output_dir = Path(source), Path(output_dir)
    data = load_matched(source)
    keys = defaultdict(list)
    for entry in data["inputs"]:
        input_path = Path(entry["path"])
        if (
            entry.get("sha256")
            and sha256(input_path.read_bytes()).hexdigest() != entry["sha256"]
        ):
            raise ValueError(f"Matched input is stale or changed: {input_path}")
        if entry["kind"] == "answer_intermediate":
            answer_data = json.loads(Path(entry["path"]).read_text(encoding="utf-8"))
            for answer in answer_data["answers"]:
                keys[identity(answer)].append(answer)
    rows, omitted = select_records(data, keys, years)
    paths = {
        year: output_dir / f"{year}_questions_without_explanations.md" for year in years
    }
    for path in paths.values():
        protect_output(data, path, merged_json=source)
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for year, path in paths.items():
        path.write_text(
            render_year(year, rows[year], omitted[year], data, source, path),
            encoding="utf-8",
        )
        counts[year] = {
            "exported": len(rows[year]),
            "excluded": len(omitted[year]),
            "known_key_records": sum(k[0] == year for k in keys),
            "exclusions": dict(Counter(reason for _, reason in omitted[year])),
        }
    return counts


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--matched-json", type=Path, required=True)
    cli.add_argument(
        "--output-dir", type=Path, default=Path("docs/questions_without_explanations")
    )
    args = cli.parse_args(argv)
    print(json.dumps(export(args.matched_json, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
