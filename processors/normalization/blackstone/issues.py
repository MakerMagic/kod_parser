"""Clean-stage issues only; upstream parser warnings remain separate evidence."""

from hashlib import sha256
from pathlib import Path

from parsers.blackstone.visual_inspection import read_png

from .body_assets import resolve_question_asset, validate_pinned_asset
from .option_assets import is_image_option, resolve_clean_asset
from .storage import clean_files, load_clean, protect_output

MARKER = "<!-- blackstone-cleaning-issues-report -->"
CATEGORIES = {
    "ambiguous_body_question_split": "Body / Prompt Separation",
    "encoding_artifact_unresolved": "Unresolved Encoding",
    "isolated_symbol_ordering_unresolved": "Text / Expression Ordering",
    "broken_image_reference": "Broken Image References",
    "broken_clean_image_reference": "Broken Image References",
    "clean_option_crop_unresolved": "Clean Answer Image Derivation",
    "original_screenshot_unavailable": "Original Screenshot Availability",
    "raw_reference_changed": "Raw Traceability",
    "raw_reference_unavailable": "Raw Traceability",
}


def current_issues(question, *, clean_json=None):
    issues = list(question["cleaning_issues"])

    def add(code, field, reason, path=None):
        row = {
            "code": code,
            "field": field,
            "reason": reason,
            "asset_path": path,
            "manual_review_required": True,
        }
        if row not in issues:
            issues.append(row)

    raw = Path(question["raw_reference"]["path"])
    try:
        if sha256(raw.read_bytes()).hexdigest() != question["raw_reference"]["sha256"]:
            add(
                "raw_reference_changed",
                "raw_reference",
                "Raw bytes changed since cleaning; stored raw snapshot retained.",
            )
    except OSError as error:
        add("raw_reference_unavailable", "raw_reference", str(error))
    assets = [*question["visual_assets"], *question["visual_previews"]]
    assets.extend(a for o in question["options"] or [] for a in o.get("images") or [])
    for asset in assets:
        try:
            data = read_png(resolve_question_asset(raw, clean_json, asset))
            if asset.get("path_base") == "clean_json_parent":
                if sha256(data).hexdigest() != asset["sha256"]:
                    raise ValueError("Pinned output hash mismatch")
                validate_pinned_asset(asset)
        except (OSError, ValueError, KeyError) as error:
            add(
                "broken_image_reference", "visual_assets", str(error), asset.get("path")
            )
    for option in question["options"] or []:
        if not is_image_option(option):
            continue
        for asset in option.get("images") or []:
            derived = asset.get("clean_asset")
            if not derived:
                if not any(
                    i["code"] == "clean_option_crop_unresolved"
                    and i["asset_path"] == asset.get("path")
                    for i in issues
                ):
                    add(
                        "clean_option_crop_unresolved",
                        "options",
                        "No saved clean crop; rerun cleaning or review missing anchor geometry.",
                        asset.get("path"),
                    )
            elif clean_json is not None:
                try:
                    data = read_png(resolve_clean_asset(clean_json, derived["path"]))
                    if sha256(data).hexdigest() != derived["sha256"]:
                        raise ValueError("Derived asset hash mismatch")
                    if derived.get("raw_asset_id") != asset.get(
                        "image_id"
                    ) or derived.get("raw_asset_path") != asset.get("path"):
                        raise ValueError("Derived/raw asset trace mismatch")
                except (OSError, ValueError, KeyError) as error:
                    add(
                        "broken_clean_image_reference",
                        "options",
                        str(error),
                        derived.get("path"),
                    )
    return issues


def write_report(references, output):
    datasets = [(path, load_clean(path)) for path in clean_files(references)]
    output = protect_output(output, [d["raw_reference"]["path"] for _, d in datasets])
    if output.suffix.lower() != ".md":
        raise ValueError("Cleaning report must be a separate Markdown file")
    if output.exists() and not output.read_text(encoding="utf-8").startswith(MARKER):
        raise FileExistsError("Refusing to replace a non-generated cleaning report")
    groups = {}
    for path, dataset in datasets:
        for question in dataset["questions"]:
            for issue in current_issues(question, clean_json=path):
                code = issue["code"]
                category = CATEGORIES.get(
                    code,
                    "Visual Placement / Ordering"
                    if "visual" in code or "layout" in code
                    else "Structured Field Consistency",
                )
                key = (str(path), question["raw_reference"]["json_pointer"])
                row = groups.setdefault(category, {}).setdefault(
                    key,
                    {
                        "question": question,
                        "clean_json": str(path),
                        "source_file": (dataset["document"].get("input") or {}).get(
                            "path"
                        ),
                        "issues": [],
                    },
                )
                if issue not in row["issues"]:
                    row["issues"].append(issue)
    text = [
        MARKER,
        "# Blackstone cleaning issues",
        "",
        "Clean-stage findings only. Raw parser warnings are preserved in each clean record and in RAW_PARSING_ISSUES.md; they are not copied into this report. Counts are unique records per category. No finding is not proof of fidelity.",
        "",
    ]

    def cell(value):
        return (
            str(value if value is not None else "unavailable")
            .replace("|", "\\|")
            .replace("\n", " ")
        )

    for category, rows in sorted(groups.items()):
        text.extend(
            [
                f"## {category} ({len(rows)} records)",
                "",
                "| Source | Year/session/paper | Question | Pages | Field | Reason | Asset | Review | Raw JSON / pointer | Clean JSON |",
                "|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in sorted(
            rows.values(),
            key=lambda r: (
                str(r["question"]["metadata"].get("year") or ""),
                r["question"]["raw_reference"]["path"],
                str(r["question"]["question_number"]),
            ),
        ):
            q = row["question"]
            metadata = q["metadata"]
            source = row["source_file"]
            details = row["issues"]
            values = [
                source,
                "/".join(cell(metadata.get(k)) for k in ("year", "session", "paper")),
                q["question_number"],
                q["page_reference"],
                "; ".join(dict.fromkeys(i["field"] for i in details)),
                "; ".join(i["code"] + ": " + i["reason"] for i in details),
                "; ".join(
                    dict.fromkeys(i["asset_path"] for i in details if i["asset_path"])
                )
                or None,
                "yes",
                q["raw_reference"]["path"] + " " + q["raw_reference"]["json_pointer"],
                row["clean_json"],
            ]
            text.append("| " + " | ".join(cell(v) for v in values) + " |")
        text.append("")
    if not groups:
        text.append("No clean-stage issues detected by these checks.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(text) + "\n", encoding="utf-8")
    return sum(len(rows) for rows in groups.values())
