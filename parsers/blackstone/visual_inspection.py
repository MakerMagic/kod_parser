"""Read saved PNGs for offline inspection and non-mutating visual QA."""

import base64
import json
import struct
import zlib
from html import escape
from pathlib import Path

from .visual_structure import foreign_option_anchors
from .visuals import valid_bbox


def resolve_asset(raw_json, reference):
    if not isinstance(reference, str) or not reference or "://" in reference:
        raise ValueError("visual_asset_not_saved")
    root = Path(raw_json).resolve().parent
    path = (root / reference).resolve()
    if not path.is_relative_to(root) or path.suffix.lower() != ".png":
        raise ValueError("visual_asset_path_invalid")
    return path


def read_png(path):
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("visual_asset_not_displayable:invalid_png")
    offset = 8
    ended = False
    while offset + 12 <= len(data):
        size = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + size]
        if offset + size + 12 > len(data):
            raise ValueError("visual_asset_not_displayable:truncated_png")
        crc = struct.unpack(">I", data[offset + 8 + size : offset + 12 + size])[0]
        if zlib.crc32(chunk + payload) & 0xFFFFFFFF != crc:
            raise ValueError("visual_asset_not_displayable:png_crc_mismatch")
        offset += size + 12
        if chunk == b"IEND":
            ended = True
            break
    if not ended:
        raise ValueError("visual_asset_not_displayable:missing_png_end")
    return data


def visual_issues(question, raw_json, pages):
    """Return (reason, saved path) pairs only for detectable visual problems."""
    issues = []
    assets = [*question.get("visual_assets", []), *question.get("visual_previews", [])]
    meaningful = [
        image for image in question.get("images", []) if not image.get("decorative")
    ]
    if meaningful and not question.get("visual_assets"):
        issues.append(
            ("visual_assets_unavailable:detected_graphics_have_no_saved_regions", None)
        )
    saved_ids = {
        identifier
        for asset in question.get("visual_assets", [])
        for identifier in asset.get("object_ids", [])
    }
    if question.get("visual_assets") and any(
        image.get("image_id") not in saved_ids for image in meaningful
    ):
        issues.append(("visual_detected_object_not_saved", None))
    orders = [asset.get("asset_index") for asset in question.get("visual_assets", [])]
    if orders and orders != list(range(1, len(orders) + 1)):
        issues.append(("visual_asset_order_inconsistent", None))
    indexed = {a["image_id"]: a for a in question.get("visual_assets", [])}
    option_anchors = [
        {"label": option["label"], "bbox": option["label_bbox"], "page": option["page"]}
        for option in question.get("options", [])
        if isinstance(option.get("label_bbox"), list)
        and len(option["label_bbox"]) == 4
        and isinstance(option.get("page"), int)
    ]
    image_options = []
    for option in question.get("options", []):
        references = option.get("images", [])
        if option.get("content_type") != "image" and not (
            references and not str(option.get("text") or "").strip()
        ):
            continue
        image_options.append(option)
        if len(references) != 1 or any(
            a.get("image_id") not in indexed
            or indexed[a["image_id"]].get("option_label") != option["label"]
            or option.get("page") is not None
            and indexed[a["image_id"]].get("page") != option["page"]
            for a in references
        ):
            issues.append(
                (
                    f"visual_image_option_mapping_inconsistent:{option['label']}",
                    references[0].get("path") if references else None,
                )
            )
        for reference in references:
            asset = indexed.get(reference.get("image_id"))
            if not asset or not valid_bbox(
                asset.get("bbox"), float("inf"), float("inf")
            ):
                continue
            foreign = foreign_option_anchors(
                asset["bbox"], option_anchors, asset.get("page"), option["label"]
            )
            if foreign:
                labels = ",".join(dict.fromkeys(a["label"] for a in foreign))
                issues.append(
                    (
                        f"foreign_option_letter_in_crop:{option['label']}->{labels}",
                        asset.get("path"),
                    )
                )
    for index, option in enumerate(image_options):
        for other in image_options[index + 1 :]:
            for left in option.get("images", []):
                for right in other.get("images", []):
                    if left.get("page") != right.get("page"):
                        continue
                    a = left.get("graphic_bbox", left.get("bbox"))
                    b = right.get("graphic_bbox", right.get("bbox"))
                    if not valid_bbox(a, float("inf"), float("inf")) or not valid_bbox(
                        b, float("inf"), float("inf")
                    ):
                        continue
                    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(
                        0, min(a[3], b[3]) - max(a[1], b[1])
                    )
                    smallest = min(
                        (a[2] - a[0]) * (a[3] - a[1]),
                        (b[2] - b[0]) * (b[3] - b[1]),
                    )
                    if smallest and intersection / smallest > 0.05:
                        issues.extend(
                            (
                                f"overlapping_option_visual_assets:{option['label']},{other['label']}",
                                path,
                            )
                            for path in (left.get("path"), right.get("path"))
                        )
    blocks = question.get("layout_blocks")
    if blocks is not None:
        if [b.get("order") for b in blocks] != list(range(1, len(blocks) + 1)):
            issues.append(("visual_layout_order_inconsistent", None))
        ids = {a["image_id"] for a in question.get("visual_assets", [])}
        placed = [b.get("asset_id") for b in blocks if b.get("type") == "visual"]
        if set(placed) != ids or len(placed) != len(ids):
            issues.append(("visual_layout_asset_reference_inconsistent", None))
        raw = question.get("raw", {}).get("question_block", "")
        for block in blocks:
            if block.get("type") != "text":
                continue
            span = block.get("raw_span") or {}
            start, end = span.get("start"), span.get("end")
            if (
                not isinstance(start, int)
                or not isinstance(end, int)
                or not 0 <= start <= end <= len(raw)
                or raw[start:end] != block.get("text")
            ):
                issues.append(("visual_layout_raw_span_inconsistent", None))
    for asset in assets:
        reference = asset.get("path")
        for warning in asset.get("warnings", []):
            issues.append((warning, reference))
        page = pages.get(asset.get("page"))
        if page and not valid_bbox(
            asset.get("bbox"),
            page.get("width", float("inf")),
            page.get("height", float("inf")),
        ):
            issues.append(("visual_invalid_bbox", reference))
        if (
            asset.get("asset_type") == "rendered_crop"
            and asset.get("belongs_to") == "unknown"
        ):
            issues.append(("visual_component_association_uncertain", reference))
        if asset.get("asset_type") == "rendered_crop" and valid_bbox(
            asset.get("bbox"), float("inf"), float("inf")
        ):
            crop = asset["bbox"]
            objects = [
                i
                for i in meaningful
                if i.get("image_id") in asset.get("object_ids", [])
            ]
            if any(
                not (
                    crop[0] <= i["bbox"][0]
                    and crop[1] <= i["bbox"][1]
                    and crop[2] >= i["bbox"][2]
                    and crop[3] >= i["bbox"][3]
                )
                for i in objects
            ):
                issues.append(
                    ("visual_crop_may_be_incomplete:object_outside_crop", reference)
                )
        try:
            read_png(resolve_asset(raw_json, reference))
        except FileNotFoundError:
            issues.append(("visual_asset_file_missing", reference))
        except (OSError, ValueError) as error:
            issues.append((str(error), reference))
    return list(dict.fromkeys(issues))


def render_html(result):
    """Self-contained PNG-backed view; does not read or render the source PDF."""
    question = result["question"]
    number = question.get("question_number")
    source = (result["document"].get("input") or {}).get(
        "filename", "Source unavailable"
    )
    title = f"{source} - question {number}"
    parts = [
        "<!doctype html><html lang='en'><meta charset='utf-8'>",
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; img-src data:; style-src 'unsafe-inline'\">",
        f"<title>{escape(title)}</title>",
        "<style>body{font:16px system-ui,sans-serif;background:#f1f4f8;color:#182334;margin:0}main{max-width:1100px;margin:32px auto;padding:24px;background:white;border-radius:12px}figure{margin:20px 0}img{max-width:100%;height:auto;border:1px solid #ccd5df}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.5 Consolas,monospace;background:#f7f9fc;padding:16px}figcaption{color:#526177;font-size:14px;margin:8px 0}.issue{background:#fff0dc;border-left:4px solid #d68d20;padding:12px}summary{cursor:pointer;padding:12px;font-weight:600}</style>",
        f"<main><h1>{escape(title)}</h1>",
        "<p>Saved layout preview preserves PDF text, subparts, options and diagrams in their original positions. The stored parsed record below is authoritative for structured fields.</p>",
    ]

    def figure(asset, heading):
        reference = asset.get("path")
        parts.append(
            f"<figure><figcaption>{escape(heading)} - page {escape(str(asset.get('page')))}; {escape(str(reference))}</figcaption>"
        )
        if asset.get("warnings"):
            parts.append(
                "<p class='issue'>Manual review: "
                + escape("; ".join(asset["warnings"]))
                + "</p>"
            )
        if asset.get("axis_labels"):
            parts.append(
                "<p>Axis labels: "
                + escape(
                    "; ".join(
                        f"{label['axis']}: {label['text']}"
                        for label in asset["axis_labels"]
                    )
                )
                + "</p>"
            )
        try:
            data = read_png(resolve_asset(result["raw_json"], reference))
            encoded = base64.b64encode(data).decode("ascii")
            parts.append(
                f"<img src='data:image/png;base64,{encoded}' alt='{escape(heading, quote=True)}'>"
            )
        except (OSError, ValueError) as error:
            parts.append(
                f"<p class='issue'>Visual unavailable: {escape(str(error))}</p>"
            )
        parts.append("</figure>")

    blocks = question.get("layout_blocks")
    if blocks:
        parts.append(
            "<h2>Stored question structure</h2><p>Geometric reading order; component labels are structural estimates. Visual-label text is preserved inside the image and in the raw record.</p>"
        )
        assets_by_id = {a["image_id"]: a for a in question.get("visual_assets", [])}
        for block in blocks:
            if block["component"] == "visual_label":
                continue
            location = block["component"].replace("_", " ")
            if block.get("label"):
                location += " " + str(block["label"])
            parts.append(
                f"<section data-component='{escape(block['component'], quote=True)}'><small>{escape(location)} · page {escape(str(block['page']))}</small>"
            )
            if block["type"] == "visual":
                asset = assets_by_id.get(block["asset_id"])
                if asset:
                    figure(asset, f"{location} — asset {asset['asset_index']}")
                else:
                    parts.append("<p class='issue'>Unresolved visual reference</p>")
            else:
                parts.append(f"<pre>{escape(block['text'])}</pre>")
            parts.append("</section>")

    previews = question.get("visual_previews", [])
    if not previews:
        parts.append(
            "<p class='issue'>No saved layout preview. Re-run parsing to save visual assets.</p>"
        )
    if blocks:
        parts.append("<details><summary>Original saved layout previews</summary>")
    for preview in sorted(previews, key=lambda asset: asset.get("asset_index", 0)):
        figure(preview, "Question layout as saved during parsing")
    if blocks:
        parts.append("</details>")
    if question.get("visual_assets"):
        parts.append(
            "<details><summary>Individual saved graphics / image-based options</summary>"
        )
        for asset in sorted(
            question["visual_assets"], key=lambda item: item.get("asset_index", 0)
        ):
            heading = f"Asset {asset.get('asset_index')} ({asset.get('belongs_to')}; option {asset.get('option_label')})"
            figure(asset, heading)
        parts.append("</details>")
    parts.append(
        "<h2>Stored question text</h2><pre>"
        + escape(str(question.get("question_text", "unavailable")))
        + "</pre>"
    )
    parts.append("<h2>Stored answer options</h2>")
    for option in question.get("options", []):
        parts.append(
            f"<pre>{escape(str(option.get('label')))}: {escape('[image-based option]' if option.get('content_type') == 'image' else str(option.get('text')))}</pre>"
        )
        for asset in option.get("images", []):
            figure(asset, f"Answer option {option.get('label')}")
    for heading, value in (
        ("Full stored question record", question),
        ("Source / document metadata", result["document"]),
        ("Missing/null field availability", result["availability"]),
        ("Visual inspection issues", result.get("visual_issues", [])),
    ):
        parts.append(
            f"<details><summary>{escape(heading)}</summary><pre>{escape(json.dumps(value, ensure_ascii=False, indent=2))}</pre></details>"
        )
    parts.append("</main></html>")
    return "\n".join(parts)
