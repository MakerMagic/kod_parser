"""Save PDF-rendered regions and question previews without changing raw text."""

import math
import re
import struct
import zlib
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import pypdfium2 as pdfium

DPI = 144
PADDING = 12


def valid_bbox(box, width, height):
    return (
        isinstance(box, (list, tuple))
        and len(box) == 4
        and all(isinstance(n, (int, float)) and math.isfinite(n) for n in box)
        and 0 <= box[0] <= box[2] <= width
        and 0 <= box[1] <= box[3] <= height
    )


def _union(boxes):
    return [
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    ]


def _near(a, b, gap=12):
    return (
        a[0] <= b[2] + gap
        and b[0] <= a[2] + gap
        and a[1] <= b[3] + gap
        and b[1] <= a[3] + gap
    )


def _regions(images):
    """Connected PDF objects, not one screenshot per vector stroke."""
    groups = []
    for image in images:
        box = image["bbox"]
        group = {"bbox": box[:], "objects": [image]}
        changed = True
        while changed:
            changed = False
            for existing in groups[:]:
                if _near(group["bbox"], existing["bbox"]):
                    group["objects"].extend(existing["objects"])
                    group["bbox"] = _union([group["bbox"], existing["bbox"]])
                    groups.remove(existing)
                    changed = True
        groups.append(group)
    return sorted(groups, key=lambda g: (g["bbox"][1], g["bbox"][0]))


def _png_chunk(kind, data):
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def _save_crop(bitmap, pixels, bbox, page_size, path, overwrite):
    """Encode PDFium RGB pixels as PNG using stdlib; no Pillow ABI dependency."""
    sx, sy = bitmap.width / page_size[0], bitmap.height / page_size[1]
    x0, y0 = math.floor(bbox[0] * sx), math.floor(bbox[1] * sy)
    x1, y1 = math.ceil(bbox[2] * sx), math.ceil(bbox[3] * sy)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(bitmap.width, x1), min(bitmap.height, y1)
    width, height = x1 - x0, y1 - y0
    if width < 1 or height < 1 or bitmap.mode != "RGB":
        raise ValueError("Invalid rendered crop or unsupported bitmap mode")
    rows = bytearray()
    for row in range(y0, y1):
        offset = row * bitmap.stride + x0 * 3
        rows.append(0)
        rows.extend(pixels[offset : offset + width * 3])
    data = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(rows))
        + _png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        if path.read_bytes() != data:
            raise FileExistsError(
                f"Existing visual asset differs: {path}; rerun with --overwrite"
            )
    else:
        path.write_bytes(data)
    return [width, height]


def _anchors(question, lines):
    start = len(question["raw"]["question_block"]) - len(
        question["raw"]["options_block"]
    )
    grouped = any(w.startswith("multi_column_options:") for w in question["warnings"])
    anchors = []
    labels = {option["label"] for option in question["options"]}
    for line in lines:
        if line["block_start"] < start:
            continue
        if grouped and not re.fullmatch(r"[A-E](?:[ \t]+[A-E])*", line["text"]):
            continue
        match = re.match(
            r"^(?:[A-E](?:\s+|$)|\(cid:(?:36|37|38|39|40)\))", line["text"]
        )
        if not match:
            continue
        positions = (
            line.get("label_positions", [])
            if grouped
            else line.get("label_positions", [])[:1]
        )
        for position in positions:
            if position["label"] in labels:
                anchors.append({**position, "page": line["page"]})
    return anchors


def _component(box, page_number, anchors):
    on_page = [anchor for anchor in anchors if anchor["page"] == page_number]
    if not on_page or box[1] < min(a["bbox"][1] for a in on_page) - 8:
        return "question", None
    center = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]
    for anchor in on_page:
        a = anchor["bbox"]
        right = min(
            (
                other["bbox"][0]
                for other in on_page
                if abs(other["bbox"][1] - a[1]) < 8 and other["bbox"][0] > a[0] + 8
            ),
            default=math.inf,
        )
        bottom = min(
            (other["bbox"][1] for other in on_page if other["bbox"][1] > a[1] + 8),
            default=math.inf,
        )
        if (
            a[0] - 5 <= center[0] < right
            and a[1] - 5 <= center[1] < bottom
            and box[3] <= bottom + 3
            and box[2] <= right + 3
        ):
            return "option", anchor["label"]
    return "unknown", None


def save_visuals(dataset, pending_questions, asset_dir, *, overwrite=False):
    """Augment existing image references; save layouts and complete padded regions."""
    root = Path(asset_dir).resolve()
    base = root.parent
    digest = dataset["input"]["sha256"]
    folder = root / digest[:20]
    dataset["extraction"]["visual_assets"] = {
        "renderer": "pypdfium2",
        "dpi": DPI,
        "path_base": "raw_json_parent",
    }
    by_page = {}
    for record_index, (question, pending) in enumerate(
        zip(dataset["questions"], pending_questions), start=1
    ):
        question["visual_assets"] = []
        question["visual_previews"] = []
        anchors = _anchors(question, pending["lines"])
        for segment in pending["segments"]:
            by_page.setdefault(segment["page"], []).append(
                (record_index, question, pending, segment, anchors)
            )

    def asset_record(
        question, record_index, page, box, order, role, detected, objects=None
    ):
        year = dataset["year"] if dataset["year"] is not None else "unknown-year"
        number = question["question_number"] if question else "unassigned"
        shape = sha256(repr([round(v, 3) for v in box]).encode()).hexdigest()[:10]
        stem = f"blackstone_{year}_q{str(number).zfill(3)}_r{record_index:03}_p{page:03}_{role}_{order:02}_{shape}"
        return {
            "image_id": stem,
            "path": None,
            "page": page,
            "bbox": box,
            "asset_type": "rendered_crop" if role == "asset" else "rendered_question",
            "detected_types": detected,
            "asset_index": order,
            "order_key": [page, box[1], box[0]],
            "source_sha256": digest,
            "source": dataset["source"],
            "year": dataset["year"],
            "question_number": question["question_number"] if question else None,
            "belongs_to": "question" if question else "document",
            "option_label": None,
            "object_ids": [image["image_id"] for image in objects or []],
            "notes": [
                "Rendered from original PDF; coordinates use top-left PDF points."
            ],
            "warnings": [],
        }

    try:
        document = pdfium.PdfDocument(dataset["input"]["path"])
    except (OSError, ValueError, pdfium.PdfiumError) as error:
        for question in dataset["questions"]:
            question["warnings"].append(f"visual_save_failed:{error}")
        return
    with document:
        for page_record in dataset["pages"]:
            number = page_record["page_number"]
            items = by_page.get(number, [])
            if not items and not page_record["images"]:
                continue
            page_record["visual_assets"] = []
            width, height = page_record["width"], page_record["height"]
            try:
                with closing(document[number - 1]) as page:
                    rendered_size = page.get_size()
                    coordinate_mismatch = any(
                        abs(a - b) > 0.1 for a, b in zip(rendered_size, (width, height))
                    )
                    if coordinate_mismatch:
                        width, height = rendered_size
                    with closing(
                        page.render(scale=DPI / 72, rev_byteorder=True)
                    ) as bitmap:
                        pixels = bytes(bitmap.buffer)

                        def save(asset, pixels=pixels, width=width, height=height):
                            destination = folder / f"{asset['image_id']}.png"
                            try:
                                asset["pixel_size"] = _save_crop(
                                    bitmap,
                                    pixels,
                                    asset["bbox"],
                                    (width, height),
                                    destination,
                                    overwrite,
                                )
                                asset["path"] = destination.relative_to(base).as_posix()
                                asset["sha256"] = sha256(
                                    destination.read_bytes()
                                ).hexdigest()
                            except (OSError, ValueError) as error:
                                asset["warnings"].append(f"visual_save_failed:{error}")

                        if coordinate_mismatch:
                            warning = "visual_coordinate_space_mismatch:full_rendered_page_saved"
                            page_record["warnings"].append(warning)
                            for record_index, question, _, _, _ in items:
                                images = [
                                    i for i in question["images"] if i["page"] == number
                                ]
                                view = asset_record(
                                    question,
                                    record_index,
                                    number,
                                    [0, 0, width, height],
                                    len(question["visual_previews"]) + 1,
                                    "view",
                                    sorted({i["kind"] for i in images}),
                                    images,
                                )
                                view["warnings"].append(warning)
                                view["notes"].append(
                                    "Bounds use renderer page size; source object bounds remain unchanged. Question association requires manual review."
                                )
                                save(view)
                                question["visual_previews"].append(view)
                                if images:
                                    question["visual_assets"].append(
                                        {
                                            **view,
                                            "asset_type": "rendered_crop",
                                            "asset_index": len(
                                                question["visual_assets"]
                                            )
                                            + 1,
                                            "belongs_to": "unknown",
                                        }
                                    )
                                question["warnings"].extend(view["warnings"])
                                for image in images:
                                    image["path"] = view["path"]
                            view = asset_record(
                                None,
                                0,
                                number,
                                [0, 0, width, height],
                                1,
                                "view",
                                sorted({i["kind"] for i in page_record["images"]}),
                                page_record["images"],
                            )
                            view["warnings"].append(warning)
                            save(view)
                            page_record["visual_assets"].append(view)
                            for image in page_record["images"]:
                                image["path"] = view["path"]
                            continue

                        assigned_ids = set()
                        for record_index, question, pending, segment, anchors in items:
                            images = [
                                image
                                for image in question["images"]
                                if image["page"] == number
                            ]
                            for image in images:
                                if not valid_bbox(image["bbox"], width, height):
                                    question["warnings"].append(
                                        f"visual_invalid_bbox:{image['image_id']}"
                                    )
                            meaningful = [
                                image
                                for image in images
                                if not image.get("decorative")
                                and valid_bbox(image["bbox"], width, height)
                            ]
                            groups = _regions(meaningful)
                            for group in groups:
                                box = group["bbox"]
                                # Include nearby labels as well as strokes; padding avoids tight diagram crops.
                                nearby = [
                                    word
                                    for line in pending["lines"]
                                    if line["page"] == number
                                    for word in line.get("word_boxes", [])
                                    if _near(box, word, gap=16)
                                ]
                                expanded = _union([box, *nearby])
                                group["crop"] = [
                                    max(0, expanded[0] - PADDING),
                                    max(0, expanded[1] - PADDING),
                                    min(width, expanded[2] + PADDING),
                                    min(height, expanded[3] + PADDING),
                                ]
                            # Stable visual row order, left-to-right within nearly aligned rows.
                            row_top = None
                            row = []
                            ordered = []
                            for group in groups:
                                if (
                                    row_top is not None
                                    and group["bbox"][1] > row_top + 8
                                ):
                                    ordered.extend(
                                        sorted(row, key=lambda g: g["bbox"][0])
                                    )
                                    row = []
                                    row_top = None
                                row_top = (
                                    group["bbox"][1] if row_top is None else row_top
                                )
                                row.append(group)
                            ordered.extend(sorted(row, key=lambda g: g["bbox"][0]))
                            for group in ordered:
                                order = len(question["visual_assets"]) + 1
                                asset = asset_record(
                                    question,
                                    record_index,
                                    number,
                                    group["crop"],
                                    order,
                                    "asset",
                                    sorted(
                                        {image["kind"] for image in group["objects"]}
                                    ),
                                    group["objects"],
                                )
                                asset["belongs_to"], asset["option_label"] = _component(
                                    group["bbox"], number, anchors
                                )
                                if asset["belongs_to"] == "unknown":
                                    asset["warnings"].append(
                                        "visual_component_association_uncertain"
                                    )
                                if (
                                    group["bbox"][1] < segment["bbox"][1] - PADDING
                                    or group["bbox"][3] > segment["bbox"][3] + 3
                                ):
                                    asset["warnings"].append(
                                        "visual_question_boundary_overlap:complete_region_saved"
                                    )
                                save(asset)
                                question["visual_assets"].append(asset)
                                for image in group["objects"]:
                                    image["path"] = asset["path"]
                                    image["asset_id"] = asset["image_id"]
                                    image["asset_index"] = order
                                    image["belongs_to"] = asset["belongs_to"]
                                    image["option_label"] = asset["option_label"]
                                    image["notes"] = [
                                        "Saved as a padded rendered region; original object bbox retained."
                                    ]
                                    assigned_ids.add(image["image_id"])
                                if asset["option_label"] is not None:
                                    for option in question["options"]:
                                        if option["label"] == asset["option_label"]:
                                            option["images"].append(asset)
                            view_box = _union(
                                [segment["bbox"], *[group["crop"] for group in groups]]
                            )
                            view = asset_record(
                                question,
                                record_index,
                                number,
                                view_box,
                                len(question["visual_previews"]) + 1,
                                "view",
                                [],
                            )
                            save(view)
                            question["visual_previews"].append(view)
                            for image in images:
                                if image.get("decorative"):
                                    image["path"] = view["path"]
                                    image["asset_id"] = view["image_id"]
                                    image["notes"] = [
                                        "White background/decorative object retained in question preview."
                                    ]
                                    assigned_ids.add(image["image_id"])
                            for asset in [*question["visual_assets"], view]:
                                question["warnings"].extend(asset["warnings"])
                        unassigned = [
                            image
                            for image in page_record["images"]
                            if image["image_id"] not in assigned_ids
                            and not image.get("decorative")
                        ]
                        if unassigned:
                            view = asset_record(
                                None,
                                0,
                                number,
                                [0, 0, width, height],
                                1,
                                "view",
                                sorted({i["kind"] for i in unassigned}),
                                unassigned,
                            )
                            save(view)
                            page_record["visual_assets"].append(view)
                            if any(
                                image["bbox"][1] < item[3]["bbox"][3]
                                and image["bbox"][3] > item[3]["bbox"][1]
                                for image in unassigned
                                for item in items
                            ):
                                page_record["warnings"].append(
                                    "visual_question_association_uncertain:unassigned_page_graphics"
                                )
                            for image in unassigned:
                                image["path"] = view["path"]
                        paths = {
                            image["image_id"]: image.get("path")
                            for _, question, _, _, _ in items
                            for image in question["images"]
                            if image["page"] == number
                        }
                        for image in page_record["images"]:
                            if image["image_id"] in paths:
                                image["path"] = paths[image["image_id"]]
            except (OSError, ValueError, pdfium.PdfiumError) as error:
                page_record["warnings"].append(f"visual_save_failed:{error}")
                for _, question, _, _, _ in items:
                    question["warnings"].append(
                        f"visual_save_failed:page_{number}:{error}"
                    )
