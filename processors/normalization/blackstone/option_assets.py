"""Derived clean answer PNGs; structural anchors only, raw assets stay intact."""

import json
import math
import re
import struct
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from parsers.blackstone.visual_inspection import read_png, resolve_asset
from parsers.blackstone.visual_structure import (
    foreign_option_anchors,
    intersects,
    option_anchor_is_left_of_visual,
)
from parsers.blackstone.visuals import valid_bbox

from .png_pixels import decode_png, encode_png


def is_image_option(option):
    return option.get("content_type") == "image" or bool(
        option.get("images") and not str(option.get("text") or "").strip()
    )


def resolve_clean_asset(clean_json, reference):
    if not isinstance(reference, str) or not reference or "://" in reference:
        raise ValueError("Derived asset reference unavailable")
    root = Path(clean_json).resolve().parent
    path = (root / reference).resolve()
    if not path.is_relative_to(root) or path.suffix.lower() != ".png":
        raise ValueError("Derived asset path escapes clean output")
    return path


def derive_crop(asset, option, anchors, raw_json, pages, dpi):
    """Remove a verified glyph window, then trim only fully white margins."""
    label = option.get("label_bbox")
    box = asset.get("bbox")
    graphic = asset.get("graphic_bbox")
    if not all(valid_bbox(b, math.inf, math.inf) for b in (label, box, graphic)):
        raise ValueError("Option/crop/graphic geometry unavailable")
    if asset.get("option_label") != option.get("label") or option.get(
        "page"
    ) != asset.get("page"):
        raise ValueError("Raw option association/page mismatch")
    owner = {"bbox": label}
    if not option_anchor_is_left_of_visual(owner, graphic):
        raise ValueError("Option anchor is not left of the answer visual")
    if foreign_option_anchors(box, anchors, asset["page"], option["label"]):
        raise ValueError("Foreign/multiple structural option letters in raw crop")
    if asset.get("warnings"):
        raise ValueError("Raw crop has unresolved warnings; no unsafe derivation")
    source = resolve_asset(raw_json, asset.get("path"))
    data = read_png(source)
    digest = sha256(data).hexdigest()
    if asset.get("sha256") and asset["sha256"] != digest:
        raise ValueError("Raw asset hash mismatch")
    width, height, channels, rows = decode_png(data)
    if not intersects(box, label):
        return data, {
            "operation": "copy_anchor_outside_crop",
            "pixel_crop_box": [0, 0, width, height],
            "removed_label_rect_px": None,
            "pixel_size": [width, height],
            "raw_asset_sha256": digest,
        }
    page = pages.get(asset["page"])
    if not page or not isinstance(dpi, (int, float)) or dpi <= 0:
        raise ValueError("Exact raw render scale/page geometry unavailable")
    sx = math.ceil(page["width"] * dpi / 72) / page["width"]
    sy = math.ceil(page["height"] * dpi / 72) / page["height"]
    origin = (math.floor(box[0] * sx), math.floor(box[1] * sy))
    predicted = [math.ceil(box[2] * sx) - origin[0], math.ceil(box[3] * sy) - origin[1]]
    if predicted != [width, height] or asset.get("pixel_size", predicted) != predicted:
        raise ValueError("Raw PNG/render coordinates inconsistent")
    protected = [graphic]
    for word in [*asset.get("visual_text", []), *asset.get("axis_labels", [])]:
        bounds = word.get("bbox")
        if not valid_bbox(bounds, math.inf, math.inf):
            continue
        # Upstream may retain CID glyph tokens in visual_text while its trusted
        # structural anchor is already decoded. Identify that same glyph by
        # exact geometry, not by re-decoding/normalizing raw text in cleaning.
        own = (
            word.get("text") == option["label"]
            or re.fullmatch(r"(?:\(cid:\d+\))+", word.get("text", ""))
        ) and all(abs(a - b) < 0.1 for a, b in zip(bounds, label))
        if not own:
            protected.append(bounds)
    white = b"\xff" * channels
    # PDF font metrics can underestimate rendered glyph overhang. Expand only
    # within a fraction of the anchor's size, checking all protected geometry
    # each time. Never use an arbitrary fixed-width strip of the answer image.
    rectangle = None
    for fraction in (0.08, 0.16, 0.24):
        padding = min(label[2] - label[0], label[3] - label[1]) * fraction
        window = [
            label[0] - padding,
            label[1] - padding,
            label[2] + padding,
            label[3] + padding,
        ]
        if any(intersects(window, bounds) for bounds in protected):
            raise ValueError(
                "Option glyph window overlaps visual/axis/label/answer content"
            )
        candidate = [
            max(0, math.floor(window[0] * sx) - origin[0]),
            max(0, math.floor(window[1] * sy) - origin[1]),
            min(width, math.ceil(window[2] * sx) - origin[0]),
            min(height, math.ceil(window[3] * sy) - origin[1]),
        ]
        x0, y0, x1, y1 = candidate
        if x1 <= x0 or y1 <= y0:
            raise ValueError("Empty option glyph window")
        ring = [
            rows[y0][x0 * channels : x1 * channels],
            rows[y1 - 1][x0 * channels : x1 * channels],
        ]
        ring.extend(
            rows[y][x * channels : (x + 1) * channels]
            for y in range(y0, y1)
            for x in (x0, x1 - 1)
        )
        if all(pixel == b"\xff" * len(pixel) for pixel in ring):
            rectangle = candidate
            break
    if rectangle is None:
        raise ValueError("Option glyph is not isolated on a verified white background")
    x0, y0, x1, y1 = rectangle
    for y in range(y0, y1):
        rows[y][x0 * channels : x1 * channels] = white * (x1 - x0)
    occupied = []
    for y, row in enumerate(rows):
        if row.strip(b"\xff"):
            left = (len(row) - len(row.lstrip(b"\xff"))) // channels
            right = (len(row.rstrip(b"\xff")) + channels - 1) // channels
            occupied.append((left, y, right, y + 1))
    if not occupied:
        raise ValueError("No answer ink remains after removing the anchor")
    margin = max(1, math.ceil((label[3] - label[1]) * sy * 0.15))
    crop = [
        max(0, min(b[0] for b in occupied) - margin),
        max(0, min(b[1] for b in occupied) - margin),
        min(width, max(b[2] for b in occupied) + margin),
        min(height, max(b[3] for b in occupied) + margin),
    ]
    left, top, right, bottom = crop
    result = encode_png(
        right - left,
        bottom - top,
        channels,
        [row[left * channels : right * channels] for row in rows[top:bottom]],
    )
    return result, {
        "operation": "erase_verified_anchor_trim_white_margins",
        "removed_label_bbox_pdf": label[:],
        "removed_label_rect_px": rectangle,
        "pixel_crop_box": crop,
        "pixel_size": [right - left, bottom - top],
        "raw_asset_sha256": digest,
    }


def prepare_option_assets(dataset, clean_json):
    """Materialize new clean PNGs on write, not during read-only inspection."""
    result = deepcopy(dataset)
    raw_path = Path(dataset["raw_reference"]["path"])
    raw_bytes = raw_path.read_bytes()
    if sha256(raw_bytes).hexdigest() != dataset["raw_reference"]["sha256"]:
        raise ValueError("Raw input changed before derived asset generation")
    raw = json.loads(raw_bytes)
    pages = {p["page_number"]: p for p in raw.get("pages", [])}
    dpi = (raw.get("extraction", {}).get("visual_assets") or {}).get("dpi")
    result["cleaning"]["asset_rules"] = ["verified_option_anchor_removal_v1"]
    for question in result["questions"]:
        options = question.get("options") or []
        anchors = [
            {"label": o["label"], "bbox": o["label_bbox"], "page": o["page"]}
            for o in options
            if valid_bbox(o.get("label_bbox"), math.inf, math.inf)
            and isinstance(o.get("page"), int)
        ]
        for option in options:
            if not is_image_option(option):
                continue
            for image in option.get("images") or []:
                image.pop("clean_asset", None)
                try:
                    if (
                        len(option["images"]) != 1
                        or sum(a["label"] == option["label"] for a in anchors) != 1
                    ):
                        raise ValueError("No unique single-visual option/anchor")
                    payload, metadata = derive_crop(
                        image, option, anchors, raw_path, pages, dpi
                    )
                    digest = sha256(payload).hexdigest()
                    name = image["image_id"] + "_clean_" + digest[:12] + ".png"
                    reference = (
                        "assets/"
                        + image.get(
                            "source_sha256", dataset["raw_reference"]["sha256"]
                        )[:20]
                        + "/"
                        + name
                    )
                    target = resolve_clean_asset(clean_json, reference)
                    if target.resolve() == resolve_asset(
                        raw_path, image["path"]
                    ).resolve() or target.is_relative_to(raw_path.parent.resolve()):
                        raise ValueError("Derived asset would overwrite raw output")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        if target.read_bytes() != payload:
                            raise ValueError(
                                "Existing derived asset differs; not overwritten"
                            )
                    else:
                        with target.open("xb") as handle:
                            handle.write(payload)
                    image["clean_asset"] = {
                        **metadata,
                        "image_id": name[:-4],
                        "path": reference,
                        "path_base": "clean_json_parent",
                        "sha256": digest,
                        "page": image["page"],
                        "option_label": option["label"],
                        "asset_type": "derived_option_crop",
                        "raw_asset_id": image["image_id"],
                        "raw_asset_path": image["path"],
                    }
                except (OSError, ValueError, KeyError, struct.error) as error:
                    issue = {
                        "code": "clean_option_crop_unresolved",
                        "field": "options",
                        "reason": str(error),
                        "asset_path": image.get("path"),
                        "manual_review_required": True,
                    }
                    if issue not in question["cleaning_issues"]:
                        question["cleaning_issues"].append(issue)
    return result
