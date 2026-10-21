"""Exact-identity explanation imports and reviewed visual explanation workspace.

No PDF parsing, provider calls, or changes to raw/clean question snapshots.
"""

import argparse
import json
import re
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from processors.explanations.generator import PROMPT
from processors.explanations.validator import render_text, validate

from .ai_explanations import candidate_to_final
from .export_without_explanations import has_explanation
from .storage import load_matched, protect_output

IDENTITY = re.compile(r"blackstone_(\d{4})_.+_section_1_q(\d+)$")
WORKSPACE = Path("docs/critical_thinking_problem_solving/tsa/2017-2019_questions_images_with_explanation_ai_generated")
IMPORTS = Path("docs/critical_thinking_problem_solving/tsa/2017-2019_questions_text_with_explanation_ai_generated")


def fingerprint(value):
    return sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def read_entries(path):
    """Recover intact objects only from the supplied pasted-fragment format.

    Original bytes remain immutable. Unparsed material must consist entirely of
    known container keys and JSON punctuation; arbitrary damaged text is rejected.
    Each recovered object retains its exact character range and source hash.
    """
    path = Path(path).resolve()
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    warning = None
    try:
        json.loads(text)
    except json.JSONDecodeError as error:
        warning = f"Malformed container at line {error.lineno}: {error.msg}; intact record objects recovered, original unchanged."
    decoder = json.JSONDecoder()
    entries, residue, previous = [], [], 0
    for match in re.finditer(r'\{\s*"number"\s*:', text):
        if match.start() < previous:
            continue
        entry, end = decoder.raw_decode(text, match.start())
        if not isinstance(entry, dict) or not entry.get("question_record"):
            raise ValueError("Entry lacks stable question record")
        residue.append(text[previous : match.start()])
        entries.append(
            (
                entry,
                {
                    "path": str(path),
                    "sha256": sha256(raw).hexdigest(),
                    "character_range": [match.start(), end],
                },
            )
        )
        previous = end
    residue.append(text[previous:])
    rest = re.sub(r'"(?:explanations|not_generated)"', "", "".join(residue))
    if not entries or re.sub(r"[\s{}\[\],:]", "", rest):
        raise ValueError(f"Unaccounted content in explanation input: {path.name}")
    return entries, warning


def entry_identity(entry):
    match = IDENTITY.fullmatch(str(entry.get("question_record", "")))
    if not match:
        raise ValueError("Invalid stable question record identifier")
    year, number = map(int, match.groups())
    if entry.get("number") != number or entry.get("year", year) != year:
        raise ValueError("Year/number disagrees with question record")
    return year, "section_1", number


def record_identity(record):
    return tuple(
        record["identity"][field] for field in ("year", "section", "question_number")
    )


def load_sources(folder):
    entries, warnings = [], []
    for path in sorted(
        Path(folder).glob("*_question_text_explanations_ai_generated.json")
    ):
        found, warning = read_entries(path)
        entries.extend(found)
        if warning:
            warnings.append({"path": str(path.resolve()), "reason": warning})
    if not entries:
        raise ValueError("No explanation input files found")
    return entries, warnings


def candidate(entry, record):
    reasons = entry.get("incorrect_options", {})
    if isinstance(reasons, dict):
        reasons = [
            {"label": label, "reason": reason} for label, reason in reasons.items()
        ]
    return {
        "correct_answer": entry.get("correct_answer", record.get("correct_answer")),
        "main_reasoning": entry.get("main_reasoning"),
        "incorrect_options": reasons,
    }


def attach(record, value, reference, source_type, *, review=None):
    final = candidate_to_final(value, reference)
    final["source_type"] = source_type
    if review:
        final["review"] = deepcopy(review)
    record["final_explanation"] = final
    record["ai_explanation"] = {
        "generation_status": "accepted",
        "validation_status": "accepted",
        "semantic_review_status": "reviewed_visual_evidence"
        if review
        else "user_supplied_import",
        "explanation_by_ai": True,
        "source_type": source_type,
        "source_reference": deepcopy(reference),
        "character_count": len(render_text(value)),
        **({"provider": "codex_assistant"} if review else {}),
        **({"review": deepcopy(review)} if review else {}),
    }


def import_text(data, entries):
    output = deepcopy(data)
    indexed = {record_identity(record): record for record in output["records"]}
    record_counts = Counter(record_identity(record) for record in output["records"])
    counts = Counter(entry_identity(entry) for entry, _ in entries)
    audit, remaining = [], []
    for entry, reference in entries:
        key = entry_identity(entry)
        record = indexed.get(key)
        item = {
            "year": key[0],
            "number": key[2],
            "question_record": entry["question_record"],
            "source_reference": reference,
        }
        errors = []
        if counts[key] != 1:
            errors.append("duplicate_import_identity")
        if record_counts[key] > 1:
            errors.append("duplicate_matched_identity")
        if record is None:
            errors.append("question_not_found")
        elif (record.get("question") or {}).get("question_id") != entry[
            "question_record"
        ]:
            errors.append("question_record_mismatch")
        if errors:
            audit.append({**item, "status": "import_rejected", "errors": errors})
            continue
        if "main_reasoning" not in entry:
            remaining.append((entry, record))
            audit.append(
                {
                    **item,
                    "status": "visual_not_generated",
                    "reason": entry.get("reason"),
                }
            )
            continue
        value = candidate(entry, record)
        if record["status"] != "matched":
            errors.append("matching_not_resolved")
        errors += validate(
            value,
            options=record["question"]["options"],
            correct_answer=record.get("correct_answer"),
        )
        source_type = "imported_ai_text_explanation"
        if has_explanation(record):
            existing = record.get("final_explanation") or {}
            if (
                existing.get("source_type") == source_type
                and existing.get("source_reference") == reference
            ):
                audit.append(
                    {
                        **item,
                        "status": "imported_existing",
                        "characters": len(render_text(value)),
                    }
                )
                continue
            errors.append("existing_explanation_conflict")
        if errors:
            audit.append(
                {**item, "status": "import_rejected", "errors": sorted(set(errors))}
            )
            continue
        attach(record, value, reference, source_type)
        audit.append(
            {**item, "status": "imported", "characters": len(render_text(value))}
        )
    output["explanation_imports"] = {"audit": audit}
    return output, remaining


def visual_context(record):
    q = record["question"]
    assets, errors = [], []
    used = set()

    def add(asset, role, label=None):
        asset_id = asset.get("image_id", asset.get("asset_id"))
        if label is not None and asset.get("option_label") not in (None, label):
            errors.append("conflicting_option_asset_label")
        effective = asset.get("clean_asset") or asset
        base = (
            record["question_reference"]["path"]
            if effective.get("path_base") == "clean_json_parent"
            else q["raw_reference"]["path"]
        )
        if not effective.get("path"):
            errors.append("missing_asset_reference")
            return
        path = (Path(base).parent / effective["path"]).resolve()
        if not path.is_file():
            errors.append("missing_asset")
            return
        if asset_id in used:
            errors.append("shared_visual_ownership")
        used.add(asset_id)
        assets.append(
            {
                "asset_id": asset_id,
                "role": role,
                "option_label": label,
                "path": str(path),
                "sha256": sha256(path.read_bytes()).hexdigest(),
            }
        )

    by_id = {a["image_id"]: a for a in q.get("visual_assets", [])}
    for block in q.get("main_body", []):
        if block.get("type") == "visual":
            add(by_id.get(block["asset_id"], {"asset_id": block["asset_id"]}), "body")
    for option in q.get("options", []):
        for asset in option.get("images", []):
            add(asset, "option", option["label"])
    for asset_id, asset in by_id.items():
        if asset_id not in used:
            add(asset, "unassigned")
            errors.append("unassigned_visual")
    # Full stored question crops retain layout evidence that small/disconnected
    # assets alone may omit (for example a calendar's unboxed printed dates).
    for preview in q.get("visual_previews", []):
        add(preview, "question_layout")
    labels = [o.get("label") for o in q.get("options", [])]
    if record.get("status") != "matched" or labels != list("ABCDE"):
        errors.append("ambiguous_matching_or_options")
    if q.get("cleaning_issues") or any(
        not o.get("text") and not o.get("images") for o in q.get("options", [])
    ):
        errors.append("unresolved_question_structure")
    if not assets:
        errors.append("visual_dependency_not_confirmed")
    content = {
        "main_body": q.get("main_body"),
        "main_question": q.get("main_question"),
        "options": q.get("options"),
        "correct_answer": record.get("correct_answer"),
        "assets": assets,
    }
    return content, sorted(set(errors))


def prepare_workspace(remaining, workspace):
    for year in (2017, 2018, 2019):
        folder = Path(workspace) / str(year)
        folder.mkdir(parents=True, exist_ok=True)
        rows = []
        for entry, record in remaining:
            if record["identity"]["year"] != year:
                continue
            content, errors = visual_context(record)
            previews = [
                {
                    "path": str(
                        (
                            Path(record["question"]["raw_reference"]["path"]).parent
                            / p["path"]
                        ).resolve()
                    ),
                    "sha256": p.get("sha256"),
                }
                for p in record["question"].get("visual_previews", [])
            ]
            rows.append(
                {
                    "year": year,
                    "number": entry["number"],
                    "question_record": entry["question_record"],
                    "status": "manual_review_required"
                    if errors
                    else "ready_for_visual_review",
                    "issues": errors,
                    "listed_reason": entry.get("reason"),
                    "context_sha256": fingerprint(content),
                    "context": content,
                    "original_previews": previews,
                }
            )
        (folder / "candidates.json").write_text(
            json.dumps(
                {
                    "prompt_sha256": sha256(PROMPT.encode()).hexdigest(),
                    "questions": rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    # A single fixed prompt reference/copy, unchanged from the established template.
    (Path(workspace) / "prompt.txt").write_text(PROMPT, encoding="utf-8")


def apply_visuals(data, workspace):
    output = deepcopy(data)
    indexed = {record_identity(record): record for record in output["records"]}
    audit = []
    for year in (2017, 2018, 2019):
        folder = Path(workspace) / str(year)
        manifest = json.loads((folder / "candidates.json").read_text(encoding="utf-8"))
        source = folder / "explanations.json"
        results = (
            json.loads(source.read_text(encoding="utf-8"))
            if source.exists()
            else {"explanations": []}
        )
        supplied = results.get("explanations", [])
        counts = Counter(e["number"] for e in supplied)
        known = {e["number"] for e in manifest["questions"]}
        if set(counts) - known:
            raise ValueError("Visual result is outside the verified candidate set")
        for row in manifest["questions"]:
            record = indexed[(year, "section_1", row["number"])]
            content, errors = visual_context(record)
            entries = [e for e in supplied if e["number"] == row["number"]]
            item = {
                "year": year,
                "number": row["number"],
                "question_record": row["question_record"],
                "backtest": f"../../../inspections/critical_thinking_problem_solving/tsa/matching/explanation_imports/{year}_q{row['number']:02}.html",
            }
            if not entries:
                audit.append(
                    {
                        **item,
                        "status": "manual_review_required",
                        "errors": errors or ["no_reviewed_explanation_supplied"],
                    }
                )
                if not has_explanation(record):
                    record["ai_explanation"] = {
                        "generation_status": "manual_review_required",
                        "explanation_by_ai": False,
                        "validation_status": "not_run",
                        "validation_errors": audit[-1]["errors"],
                    }
                continue
            entry = entries[0]
            if entry.get("status") == "text_sufficient_illustration":
                if (
                    entry.get("question_record") != record["question"]["question_id"]
                    or entry.get("year") != year
                    or entry.get("context_sha256") != fingerprint(content)
                ):
                    raise ValueError(
                        "Text-sufficiency review identity/context mismatch"
                    )
                audit.append(
                    {
                        **item,
                        "status": "skipped_text_sufficient_illustration",
                        "errors": [entry["reason"]],
                    }
                )
                if not has_explanation(record):
                    record["ai_explanation"] = {
                        "generation_status": "skipped_text_sufficient_illustration",
                        "explanation_by_ai": False,
                        "validation_status": "not_applied_outside_visual_scope",
                        "validation_errors": audit[-1]["errors"],
                    }
                continue
            if entry.get("status") == "rejected":
                audit.append(
                    {
                        **item,
                        "status": "reasoning_review_rejected",
                        "errors": [entry.get("reason", "unreliable_visual_reasoning")],
                    }
                )
                if not has_explanation(record):
                    record["ai_explanation"] = {
                        "generation_status": "reasoning_review_rejected",
                        "explanation_by_ai": False,
                        "validation_status": "not_accepted",
                        "quality_review_reasons": audit[-1]["errors"],
                    }
                continue
            review = entry.get("review") or {}
            if counts[row["number"]] != 1:
                errors.append("duplicate_visual_explanation")
            if (
                entry.get("question_record") != record["question"]["question_id"]
                or entry.get("year") != year
            ):
                errors.append("visual_identity_mismatch")
            if entry.get("context_sha256") != fingerprint(content) or row[
                "context_sha256"
            ] != fingerprint(content):
                errors.append("visual_context_changed")
            if manifest.get("prompt_sha256") != sha256(PROMPT.encode()).hexdigest():
                errors.append("prompt_changed")
            if (
                set(review.get("assets_reviewed", []))
                != {a["asset_id"] for a in content["assets"]}
                or not review.get("visual_evidence")
                or not review.get("reasoning_check")
            ):
                errors.append("visual_review_incomplete")
            value = candidate(entry, record)
            errors += validate(
                value,
                options=record["question"]["options"],
                correct_answer=record.get("correct_answer"),
            )
            reference = {
                "path": str(source.resolve()),
                "sha256": sha256(source.read_bytes()).hexdigest(),
                "question_record": entry.get("question_record"),
                "context_sha256": fingerprint(content),
                "prompt_sha256": manifest["prompt_sha256"],
            }
            if (
                has_explanation(record)
                and record.get("final_explanation", {}).get("source_reference")
                != reference
            ):
                errors.append("existing_explanation_conflict")
            if errors:
                audit.append(
                    {
                        **item,
                        "status": "validation_rejected",
                        "errors": sorted(set(errors)),
                    }
                )
                if not has_explanation(record):
                    record["ai_explanation"] = {
                        "generation_status": "validation_rejected",
                        "explanation_by_ai": False,
                        "validation_status": "rejected",
                        "validation_errors": audit[-1]["errors"],
                    }
                continue
            attach(
                record,
                value,
                reference,
                "ai_generated_visual_explanation",
                review=review,
            )
            audit.append(
                {**item, "status": "accepted", "characters": len(render_text(value))}
            )
    output["visual_explanations"] = {"audit": audit}
    return output


def write_reports(data, workspace, source_warnings):
    for year in (2017, 2018, 2019):
        rows = [
            e
            for e in data.get("visual_explanations", {}).get("audit", [])
            if e["year"] == year
        ]
        imports = [e for e in data["explanation_imports"]["audit"] if e["year"] == year]
        text_only = sum(
            e["status"] == "skipped_text_sufficient_illustration" for e in rows
        )
        lines = [
            f"# {year} explanation import and visual generation",
            "",
            f"Imported explanations: {sum(e['status'].startswith('imported') for e in imports)}. Source-listed visual candidates: {len(rows)}. Verified visual-dependent candidates: {len(rows) - text_only}. Accepted visual explanations: {sum(e['status'] == 'accepted' for e in rows)}. Unresolved visual explanations: {sum(e['status'] not in ('accepted', 'skipped_text_sufficient_illustration') for e in rows)}. Text-sufficient illustrations excluded: {text_only}.",
            "",
            "Source container recovery is an import operation, not a parser fix. Original files are preserved.",
            "",
        ]
        for warning in source_warnings:
            if str(year) in Path(warning["path"]).name:
                lines += ["- " + warning["reason"], ""]
        report_rows = [
            e for e in imports if e["status"] != "visual_not_generated"
        ] + rows
        for status in sorted({e["status"] for e in report_rows}):
            group = [e for e in report_rows if e["status"] == status]
            lines += [
                f"## {status.replace('_', ' ').title()} ({len({e['number'] for e in group})} questions)",
                "",
            ]
            for entry in sorted(group, key=lambda e: e["number"]):
                reason = (
                    "; ".join(entry.get("errors", []))
                    or entry.get("reason")
                    or f"{entry.get('characters', 'unknown')} characters"
                )
                lines.append(
                    f"- Q{entry['number']}: {reason}. [Backtest](../../../inspections/critical_thinking_problem_solving/tsa/matching/explanation_imports/{year}_q{entry['number']:02}.html)"
                )
            lines.append("")
        (Path(workspace) / str(year) / "ISSUES.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )


def write_backtests(path):
    """Rebuild owned HTML views through the existing live inspection workflow."""
    from html import escape

    from .backtest import inspect_question, render_html

    data = load_matched(path)
    folder = Path("inspections/critical_thinking_problem_solving/tsa/matching/explanation_imports")
    protect_output(data, folder / "index.html")
    folder.mkdir(parents=True, exist_ok=True)
    marker = "<!-- tsa-explanation-import-backtest -->"
    lines = [
        marker,
        "<!doctype html><meta charset='utf-8'><title>2017–2019 explanations</title>",
        "<h1>2017–2019 explanation backtests</h1><p>Matching status and explanation availability are separate. Unresolved cases remain visible.</p>",
    ]
    validation = []
    for record in data["records"]:
        ident = record["identity"]
        year, number = ident["year"], ident["question_number"]
        result = inspect_question(path, year=year, question_number=number)
        filename = f"{year}_q{number:02}.html"
        output = folder / filename
        if output.exists() and not output.read_text(encoding="utf-8").startswith(
            marker
        ):
            raise ValueError(f"Refusing to overwrite unrelated HTML: {output}")
        output.write_text(marker + "\n" + render_html(result), encoding="utf-8")
        final = record.get("final_explanation") or {}
        lines.append(
            f"<p><a href='{filename}'>{year} Q{number}</a>: match={escape(record['status'])}; explanation={escape(final.get('status', 'unavailable'))}; source={escape(final.get('source_type', 'unavailable'))}</p>"
        )
        validation.append(
            {
                "year": year,
                "number": number,
                "explanation_available": final.get("status") == "available",
                "live_issues": result["live_inspection_issues"],
                "path": str(output),
            }
        )
    (folder / "index.html").write_text("\n".join(lines), encoding="utf-8")
    (folder / "validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return validation


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "apply"))
    parser.add_argument("--matched-json", type=Path, required=True)
    parser.add_argument("--imports", type=Path, default=IMPORTS)
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backtests", action="store_true")
    args = parser.parse_args(argv)
    if not args.output.name.endswith(".matched.json"):
        parser.error("Explanation output must end in .matched.json")
    if args.output.exists():
        load_matched(args.output)
    if any(
        args.output.resolve().is_relative_to(folder.resolve())
        for folder in (args.imports, args.workspace)
    ):
        parser.error(
            "Matched output must not overwrite explanation source/workspace files"
        )
    original = load_matched(args.matched_json)
    protect_output(original, args.output)
    entries, warnings = load_sources(args.imports)
    updated, remaining = import_text(original, entries)
    if args.command == "prepare":
        prepare_workspace(remaining, args.workspace)
    updated = apply_visuals(updated, args.workspace)
    updated["explanation_imports"]["source_warnings"] = warnings
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_reports(updated, args.workspace, warnings)
    if args.backtests:
        write_backtests(args.output)
    print(
        json.dumps(
            {
                "imports": dict(
                    Counter(
                        e["status"] for e in updated["explanation_imports"]["audit"]
                    )
                ),
                "visuals": dict(
                    Counter(
                        e["status"] for e in updated["visual_explanations"]["audit"]
                    )
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
