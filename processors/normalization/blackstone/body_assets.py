"""Explicit, hash-bound manual body visual substitutions; never write raw assets."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from parsers.blackstone.visual_inspection import read_png, resolve_asset

from .option_assets import resolve_clean_asset

MANIFEST = Path(__file__).with_name("pinned_sources") / "body_visuals.json"


def resolve_question_asset(raw_json, clean_json, asset):
    if asset.get("path_base") == "clean_json_parent":
        if clean_json is None:
            raise ValueError("Clean JSON path required for a pinned visual")
        return resolve_clean_asset(clean_json, asset["path"])
    return resolve_asset(raw_json, asset.get("path"))


def validate_pinned_asset(asset):
    """Validate both project-controlled inputs, not just a generated PNG copy."""
    provenance = asset.get("provenance", {})
    if provenance.get("origin") != "user_supplied_pinned_body_visual":
        return
    if asset["sha256"] != provenance["supplied_image_reference"]["sha256"]:
        raise ValueError("Pinned output is not the exact approved supplied image")
    for field in ("manifest_reference", "supplied_image_reference"):
        reference = provenance[field]
        if (
            sha256(Path(reference["path"]).read_bytes()).hexdigest()
            != reference["sha256"]
        ):
            raise ValueError(
                f"Pinned visual {field} changed; explicit review/regeneration required"
            )
    read_png(Path(provenance["supplied_image_reference"]["path"]))


def prepare_body_assets(dataset, output, *, manifest=MANIFEST):
    """Run during clean writing, independently of the PDF and generated raw names."""
    manifest = Path(manifest).resolve()
    config = json.loads(manifest.read_text(encoding="utf-8"))
    if config.get("version") != "1":
        raise ValueError("Unsupported pinned body visual manifest")
    result = deepcopy(dataset)
    for rule in config["overrides"]:
        for q in result["questions"]:
            if q["source_question_key"] != rule["source_question_key"]:
                continue
            try:
                if result["document"]["input"]["sha256"] != rule["source_sha256"]:
                    raise ValueError(
                        "Pinned source PDF hash no longer matches the approved source"
                    )
                # Idempotent for a previously written clean dataset, not just a fresh transform.
                if any(
                    o["override_id"] == rule["override_id"]
                    for o in q.get("body_visual_overrides", [])
                ):
                    for asset in q["visual_assets"]:
                        validate_pinned_asset(asset)
                    continue
                source = (manifest.parent / rule["image"]).resolve()
                if not source.is_relative_to(manifest.parent):
                    raise ValueError(
                        "Pinned source image escapes the manifest directory"
                    )
                png = read_png(source)
                digest = sha256(png).hexdigest()
                if digest != rule["image_sha256"]:
                    raise ValueError("Supplied pinned image hash mismatch")
                indices = rule["replaced_asset_indices"]
                replaced = [
                    a
                    for a in q["visual_assets"]
                    if a.get("asset_index") in indices and a.get("page") == rule["page"]
                ]
                if sorted(a["asset_index"] for a in replaced) != sorted(indices):
                    raise ValueError(
                        "Approved source visual group changed; no replacement inferred"
                    )
                ids = {a["image_id"] for a in replaced}
                blocks = [b for b in q["main_body"] if b.get("asset_id") in ids]
                if len(blocks) != len(ids) or any(
                    a.get("option_label") for a in replaced
                ):
                    raise ValueError(
                        "Pinned group is not uniquely represented in Main Body"
                    )
                positions = [i for i, b in enumerate(q["main_body"]) if b in blocks]
                if positions != list(range(min(positions), max(positions) + 1)):
                    raise ValueError(
                        "Pinned group is interrupted by other content; order requires review"
                    )
                folder = (
                    Path(output).resolve().parent
                    / "assets"
                    / "pinned"
                    / rule["source_sha256"][:20]
                )
                folder.mkdir(parents=True, exist_ok=True)
                target = folder / f"{rule['override_id']}_{digest[:12]}.png"
                if target.exists() and target.read_bytes() != png:
                    raise ValueError(
                        "Existing pinned output differs; refusing destructive replacement"
                    )
                if not target.exists():
                    target.write_bytes(png)
                identifier = rule["override_id"] + "_" + digest[:12]
                provenance = {
                    "origin": rule["origin"],
                    "override_id": rule["override_id"],
                    "approval": rule["approval"],
                    "source_sha256": rule["source_sha256"],
                    "source_question_key": deepcopy(q["source_question_key"]),
                    "manifest_reference": {
                        "path": str(manifest),
                        "sha256": sha256(manifest.read_bytes()).hexdigest(),
                    },
                    "supplied_image_reference": {"path": str(source), "sha256": digest},
                    "replaced_raw_assets": deepcopy(replaced),
                }
                asset = {
                    "image_id": identifier,
                    "path": target.relative_to(
                        Path(output).resolve().parent
                    ).as_posix(),
                    "path_base": "clean_json_parent",
                    "sha256": digest,
                    "asset_type": "manually_supplied_combined_visual",
                    "page": rule["page"],
                    "bbox": [
                        min(a["bbox"][0] for a in replaced),
                        min(a["bbox"][1] for a in replaced),
                        max(a["bbox"][2] for a in replaced),
                        max(a["bbox"][3] for a in replaced),
                    ],
                    "belongs_to": "question_body",
                    "option_label": None,
                    "warnings": [],
                    "provenance": provenance,
                }
                q["visual_assets"].append(asset)
                combined = {
                    "type": "visual",
                    "asset_id": identifier,
                    "raw_component": "stimulus",
                    "source_blocks": [
                        s for b in blocks for s in b.get("source_blocks", [])
                    ],
                    "override_id": rule["override_id"],
                }
                q["main_body"] = [
                    combined if i == positions[0] else b
                    for i, b in enumerate(q["main_body"])
                    if i == positions[0] or i not in positions
                ]
                for order, block in enumerate(q["main_body"], 1):
                    block["order"] = order
                q.setdefault("body_visual_overrides", []).append(provenance)
                result["cleaning"]["body_asset_rules"] = [
                    "explicit_hash_bound_pinned_body_visual"
                ]
            except (OSError, ValueError, KeyError, TypeError) as error:
                q["cleaning_issues"].append(
                    {
                        "code": "pinned_body_visual_unresolved",
                        "field": "main_body",
                        "reason": str(error),
                        "asset_path": rule["image"],
                        "manual_review_required": True,
                    }
                )
    return result
