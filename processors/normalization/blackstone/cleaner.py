"""Pure, deterministic raw-to-clean transformation with a retained raw snapshot."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from parsers.blackstone.visual_inspection import read_png, resolve_asset

from .structure import build_structure
from .text import artifact_reason, normalize_text

VERSION = "1"
RULES = [
    "nfc",
    "common_horizontal_whitespace",
    "paragraph_preservation",
    "conservative_prose_wraps",
    "explicit_single_prompt",
    "raw_layout_alignment",
    "verified_cid_layout_equality",
    "sentence_aware_prompt_tail",
    "introduced_structured_blocks",
    "wrapped_structured_introductions",
]
METADATA = ("source", "year", "session", "paper", "variant", "section", "document_role")
EXPECTED = (
    "question_id",
    "question_number",
    "question_text",
    "subpoints",
    "options",
    "images",
    "visual_assets",
    "visual_previews",
    "page_reference",
    "warnings",
    "answer",
    "explanation",
)


def availability(record, expected):
    return {
        "missing_fields": [key for key in expected if key not in record],
        "null_fields": [
            key for key in expected if key in record and record[key] is None
        ],
        "empty_fields": [
            key for key in expected if key in record and record[key] in ("", [], {})
        ],
        "unavailable_fields": [
            key for key in expected if key not in record or record[key] is None
        ],
    }


def _hash(value):
    return sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def clean_dataset(dataset, raw_json, *, raw_sha256=None):
    """Consume stored JSON only. Never write raw data, open PDFs or acquire files."""
    path = Path(raw_json).resolve()
    digest = raw_sha256 or sha256(path.read_bytes()).hexdigest()
    document = deepcopy(
        {
            key: value
            for key, value in dataset.items()
            if key not in {"questions", "pages"}
        }
    )
    result = {
        "stage": "clean",
        "schema_version": VERSION,
        "cleaning": {"processor": "blackstone", "version": VERSION, "rules": RULES[:]},
        "raw_reference": {"path": str(path), "sha256": digest},
        "document": document,
        "questions": [],
    }
    for index, raw in enumerate(dataset["questions"]):
        issues, changes = [], []

        def issue(code, field, reason, asset_path=None, *, issues=issues):
            entry = {
                "code": code,
                "field": field,
                "reason": reason,
                "asset_path": asset_path,
                "manual_review_required": True,
            }
            if entry not in issues:
                issues.append(entry)

        def text(
            value,
            field,
            *,
            join_lines=True,
            separate_blocks=False,
            changes=changes,
            issue=issue,
        ):
            reason = artifact_reason(value)
            if reason:
                issue("encoding_artifact_unresolved", field, reason)
            cleaned = normalize_text(
                value, join_lines=join_lines, separate_blocks=separate_blocks
            )
            if cleaned != value:
                changes.append(
                    {
                        "field": field,
                        "before_sha256": _hash(value),
                        "after_sha256": _hash(cleaned),
                        "rules": RULES[:4]
                        + (
                            [
                                "introduced_structured_blocks",
                                "wrapped_structured_introductions",
                            ]
                            if separate_blocks
                            else []
                        ),
                    }
                )
            return cleaned

        safe = deepcopy(raw)
        for field in (
            "options",
            "subpoints",
            "images",
            "visual_assets",
            "visual_previews",
            "layout_blocks",
        ):
            value = safe.get(field)
            if value is not None and (
                not isinstance(value, list)
                or any(not isinstance(v, dict) for v in value)
            ):
                issue(
                    "malformed_component",
                    field,
                    "Expected structured objects; original value retained in raw_record, not silently repaired.",
                )
                safe[field] = []
            elif value is None:
                safe[field] = []
        question = {
            "question_id": deepcopy(raw.get("question_id")),
            "question_number": deepcopy(raw.get("question_number")),
            "source_question_key": deepcopy(raw.get("source_question_key")),
            "metadata": {
                key: deepcopy(
                    (raw.get("source_question_key") or {}).get(key, document.get(key))
                )
                for key in METADATA
            },
            "page_reference": deepcopy(raw.get("page_reference")),
            "raw_reference": {
                "path": str(path),
                "sha256": digest,
                "json_pointer": f"/questions/{index}",
                "question_id": raw.get("question_id"),
            },
            "raw_record": deepcopy(raw),
            "raw_warnings": deepcopy(raw.get("warnings")),
            "warnings": deepcopy(raw.get("warnings")),
            "raw_document_warnings": deepcopy(dataset.get("warnings")),
            "availability": {
                "raw": availability(raw, EXPECTED),
                "metadata": availability(document, METADATA),
            },
            "question_text": text(
                raw.get("question_text"), "question_text", separate_blocks=True
            ),
            "options": deepcopy(safe["options"])
            if isinstance(raw.get("options"), list)
            else None,
            "subpoints": deepcopy(safe["subpoints"])
            if isinstance(raw.get("subpoints"), list)
            else None,
            "visual_assets": deepcopy(safe["visual_assets"]),
            "visual_previews": deepcopy(safe["visual_previews"]),
            "images": deepcopy(raw.get("images")),
        }
        for optional in ("answer", "explanation"):
            if optional in raw:
                question[optional] = deepcopy(raw[optional])
        for field in ("options", "subpoints"):
            for item_index, item in enumerate(question[field] or []):
                if "text" in item:
                    item["text"] = text(item["text"], f"{field}/{item_index}/text")
                if isinstance(item.get("label"), str):
                    # Only trim label whitespace, never infer or reassign labels.
                    item["label"] = text(
                        item["label"], f"{field}/{item_index}/label", join_lines=False
                    )
        question["availability"]["raw_options"] = [
            availability(item, ("label", "text", "images", "warnings"))
            for item in safe["options"]
        ]
        question["availability"]["clean_options"] = [
            availability(item, ("label", "text", "images", "warnings"))
            for item in question["options"] or []
        ]
        labels = [o.get("label") for o in question["options"] or []]
        if raw.get("options") is None:
            issue(
                "option_structure_unavailable",
                "options",
                "Missing/null option structure retained; no choices inferred.",
            )
        if len(labels) != len({str(v) for v in labels}) or any(
            not isinstance(v, str) or not v for v in labels
        ):
            issue(
                "option_labels_unresolved",
                "options",
                "Duplicate/empty/invalid labels preserved without regrouping.",
            )
        if any(
            (
                o.get("text") is None
                or isinstance(o.get("text"), str)
                and not o["text"].strip()
            )
            and not o.get("images")
            for o in question["options"] or []
        ):
            issue(
                "option_content_unavailable",
                "options",
                "An option has neither text nor visual references; no missing content invented.",
            )
        if isinstance(raw.get("question_text"), str) and any(
            line.strip() in {":", "=", "/", "−", "+"}
            for line in raw["question_text"].splitlines()
        ):
            issue(
                "isolated_symbol_ordering_unresolved",
                "question_text",
                "An isolated symbol may belong inside an expression; its original line retained, not repositioned.",
            )
        body, prompt, accounting = build_structure(safe, issue)
        question.update(
            main_body=body, main_question=prompt, content_accounting=accounting
        )
        indexed = {a["image_id"]: a for a in question["visual_assets"]}
        for option in question["options"] or []:
            for reference in option.get("images") or []:
                identifier = reference.get("image_id")
                asset = indexed.get(identifier)
                if not asset or asset.get("option_label") != option.get("label"):
                    issue(
                        "option_visual_mapping_unresolved",
                        "options",
                        "Stored option-to-asset mapping is inconsistent; preserved without reassignment.",
                        reference.get("path"),
                    )
                elif asset.get("path") != reference.get("path"):
                    issue(
                        "option_visual_reference_conflict",
                        "options",
                        "Option reference and canonical asset disagree; both original references retained.",
                        reference.get("path"),
                    )
        references = [*question["visual_assets"], *question["visual_previews"]]
        references.extend(
            a for o in question["options"] or [] for a in o.get("images") or []
        )
        for asset in references:
            try:
                read_png(resolve_asset(path, asset.get("path")))
            except (OSError, ValueError) as error:
                issue(
                    "broken_image_reference",
                    "visual_assets",
                    str(error),
                    asset.get("path"),
                )
        if not question["visual_previews"]:
            issue(
                "original_screenshot_unavailable",
                "visual_previews",
                "No upstream full-question preview; cleaning does not reopen/render PDFs.",
            )
        question["cleaning_issues"] = issues
        question["transformations"] = changes
        question["availability"]["clean"] = availability(
            question, (*EXPECTED, "main_body", "main_question")
        )
        result["questions"].append(question)
    validate_clean(result)
    return result


def validate_clean(dataset):
    if dataset.get("stage") != "clean" or dataset.get("schema_version") != VERSION:
        raise ValueError("Unsupported clean dataset/version")
    pointers = []
    for i, question in enumerate(dataset["questions"]):
        reference = question["raw_reference"]
        if (
            reference["sha256"] != dataset["raw_reference"]["sha256"]
            or reference["path"] != dataset["raw_reference"]["path"]
            or reference["json_pointer"] != f"/questions/{i}"
        ):
            raise ValueError("Clean/raw reference mismatch")
        raw = question["raw_record"]
        for field in (
            "question_id",
            "question_number",
            "source_question_key",
            "page_reference",
        ):
            if question[field] != raw.get(field):
                raise ValueError(f"Cleaning changed identity/page mapping: {field}")
        if question["raw_warnings"] != raw.get("warnings"):
            raise ValueError("Cleaning dropped raw warnings")
        if question["question_text"] != normalize_text(
            raw.get("question_text"),
            separate_blocks="introduced_structured_blocks"
            in dataset["cleaning"]["rules"],
            wrapped_lead_ins="wrapped_structured_introductions"
            in dataset["cleaning"]["rules"],
        ):
            raise ValueError("Question text is not the declared conservative transform")
        pointers.append(reference["json_pointer"])
    if len(pointers) != len(set(pointers)):
        raise ValueError("Duplicate raw record pointers")
