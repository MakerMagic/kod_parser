"""Save PDF-rendered regions and question previews without changing raw text."""

import math
import re
import struct
import zlib
from contextlib import closing
from hashlib import sha256
from itertools import pairwise
from pathlib import Path

import pypdfium2 as pdfium

from .image_options import image_choice_anchors
from .visual_structure import focused_crop, foreign_option_anchors

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


def _regions(images, gap=12):
    """Connected PDF objects, not one screenshot per vector stroke."""
    groups = []
    for image in images:
        box = image["bbox"]
        group = {"bbox": box[:], "objects": [image]}
        changed = True
        while changed:
            changed = False
            for existing in groups[:]:
                if _near(group["bbox"], existing["bbox"], gap=gap):
                    group["objects"].extend(existing["objects"])
                    group["bbox"] = _union([group["bbox"], existing["bbox"]])
                    groups.remove(existing)
                    changed = True
        groups.append(group)
    return sorted(groups, key=lambda g: (g["bbox"][1], g["bbox"][0]))


def _is_graph(group):
    """Require repeated horizontal guides plus plotted marks, not table rules."""
    guides = marks = 0
    for obj in group["objects"]:
        x0, y0, x1, y1 = obj["bbox"]
        width, height = x1 - x0, y1 - y0
        guides += width > 50 and height < 1.2
        marks += (
            3 < width < 65
            and height > max(18, width * 1.4)
            or obj["object_type"] == "curve"
            and 2 < width < 30
            and 2 < height < 30
            or obj["object_type"] == "line"
            and width > 3
            and height > 3
        )
    return guides >= 3 and marks >= 3


def _graph_regions(images):
    """Join a detached top guide to one bar graph, never to a table or neighbor."""
    groups = _regions(images)
    for main in [g for g in groups if _is_graph(g)]:
        m = main["bbox"]
        possible = [
            cap
            for cap in groups
            if cap is not main
            and len(cap["objects"]) == 1
            and cap["objects"][0]["object_type"] == "line"
            and cap["bbox"][2] - cap["bbox"][0] > 80
            and cap["bbox"][3] - cap["bbox"][1] < 1.2
            and 0 < m[1] - cap["bbox"][3] <= 20
            and abs(m[0] - cap["bbox"][0]) <= 7
            and abs(m[2] - cap["bbox"][2]) <= 7
        ]
        if len(possible) == 1:
            cap = possible[0]
            # The cap must have only this graph as a plausible owner.
            owners = [
                other
                for other in groups
                if other is not cap
                and _is_graph(other)
                and 0 < other["bbox"][1] - cap["bbox"][3] <= 20
                and abs(other["bbox"][0] - cap["bbox"][0]) <= 7
            ]
            if len(owners) == 1:
                main["objects"].extend(cap["objects"])
                main["bbox"] = _union([m, cap["bbox"]])
                groups.remove(cap)
        main["graph"] = True
    return sorted(groups, key=lambda g: (g["bbox"][1], g["bbox"][0]))


def _graph_cell(group, anchors, page):
    """A letter owns a graph only inside its column and before the next row."""
    box = group["bbox"]
    on_page = [a for a in anchors if a["page"] == page and a.get("label_only")]
    candidates = []
    for anchor in on_page:
        label = anchor["bbox"]
        if not (
            0 <= box[0] - label[2] <= 100
            and label[1] <= box[1]
            and box[1] - label[1] <= 65
        ):
            continue
        next_column = min(
            (
                a["bbox"][0]
                for a in on_page
                if abs(a["bbox"][1] - label[1]) < 8 and a["bbox"][0] > label[0] + 8
            ),
            default=math.inf,
        )
        next_row = min(
            (
                a["bbox"][1]
                for a in on_page
                if abs(a["bbox"][0] - label[0]) < 8 and a["bbox"][1] > label[1] + 8
            ),
            default=math.inf,
        )
        if box[0] < next_column and box[3] <= next_row:
            candidates.append(anchor)
    return candidates[0] if len(candidates) == 1 else None


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
    labels_in_record = [option["label"] for option in question["options"]]
    if len(labels_in_record) != len(set(labels_in_record)):
        question["warnings"].append(
            "visual_option_labels_ambiguous:duplicate_structural_labels"
        )
        return []
    start = len(question["raw"]["question_block"]) - len(
        question["raw"]["options_block"]
    )
    grouped = any(w.startswith("multi_column_options:") for w in question["warnings"])
    anchors = []
    labels = {option["label"] for option in question["options"]}
    for line in lines:
        if line["block_start"] < start:
            continue
        if grouped and not re.fullmatch(r"[A-Z](?:[ \t]+[A-Z])*", line["text"]):
            continue
        match = re.match(
            r"^(?:[A-Z](?:\s+|$)|\(cid:(?:36|37|38|39|40)\))", line["text"]
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
                anchors.append(
                    {
                        **position,
                        "page": line["page"],
                        "label_only": bool(
                            re.fullmatch(
                                r"(?:[A-Z]|\(cid:(?:36|37|38|39|40)\))(?:\s+(?:[A-Z]|\(cid:(?:36|37|38|39|40)\)))*",
                                line["text"],
                            )
                        ),
                    }
                )
    return anchors


def _component(box, page_number, anchors):
    on_page = [anchor for anchor in anchors if anchor["page"] == page_number]
    contained_labels = [
        a
        for a in on_page
        if a.get("label_only")
        and box[0] <= (a["bbox"][0] + a["bbox"][2]) / 2 <= box[2]
        and max(a["bbox"][1] - box[3], box[1] - a["bbox"][3], 0) <= 30
    ]
    if len(contained_labels) > 1:
        return "unknown", None
    # Label-only choices can sit above, below, or beside their image. Use local
    # rows/columns, not the old assumption that every image follows its label.
    candidates = []
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    for anchor in on_page:
        if not anchor.get("label_only"):
            continue
        a = anchor["bbox"]
        ax, ay = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
        row = [other["bbox"] for other in on_page if abs(other["bbox"][1] - a[1]) < 8]
        left = max(((b[0] + b[2]) / 2 for b in row if b[2] < a[0]), default=-math.inf)
        right = min(((b[0] + b[2]) / 2 for b in row if b[0] > a[2]), default=math.inf)
        previous = max(
            (
                (b["bbox"][1] + b["bbox"][3]) / 2
                for b in on_page
                if b["bbox"][3] < a[1] - 8
            ),
            default=-math.inf,
        )
        following = min(
            (
                (b["bbox"][1] + b["bbox"][3]) / 2
                for b in on_page
                if b["bbox"][1] > a[3] + 8
            ),
            default=math.inf,
        )
        dx, dy = (
            max(a[0] - box[2], box[0] - a[2], 0),
            max(a[1] - box[3], box[1] - a[3], 0),
        )
        if (
            (left + ax) / 2 < cx < (right + ax) / 2
            and (previous + ay) / 2 < cy < (following + ay) / 2
            and dx <= 50
            and dy <= 30
        ):
            candidates.append((math.hypot(dx, dy), anchor["label"]))
    if candidates:
        candidates.sort()
        if len(candidates) > 1 and candidates[1][0] - candidates[0][0] < 5:
            return "unknown", None
        return "option", candidates[0][1]
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


def _associate_rows(groups, anchors, page, lines, options_start):
    """Match complete image rows one-to-one instead of greedily stealing a label.

    Left-aligned labels can be far from their own wide chart and closer to the
    preceding chart. A complete, separated row supplies stronger evidence than
    nearest-label distance; incomplete or overlapping rows keep the fallback.
    """
    rows = []
    for anchor in sorted(
        (a for a in anchors if a["page"] == page and a.get("label_only")),
        key=lambda a: (a["bbox"][1], a["bbox"][0]),
    ):
        if not rows or abs(anchor["bbox"][1] - rows[-1][0]["bbox"][1]) > 8:
            rows.append([])
        rows[-1].append(anchor)
    candidates = {index: [] for index in range(len(rows))}
    for group in groups:
        box = group["bbox"]
        nearby = [
            (abs(box[1] - row[0]["bbox"][1]), index)
            for index, row in enumerate(rows)
            if max(row[0]["bbox"][1] - box[3], box[1] - row[0]["bbox"][3], 0) <= 30
        ]
        nearby = [
            (distance, index)
            for distance, index in nearby
            if not any(
                line["page"] == page
                and line["block_start"] < options_start
                and len(line.get("word_boxes", [])) >= 5
                and line["text"].rstrip().endswith(("?", "."))
                and box[3] <= line["top"] <= line["bottom"] <= rows[index][0]["bbox"][1]
                for line in lines
            )
        ]
        if nearby:
            candidates[min(nearby)[1]].append(group)
    for index, row in enumerate(rows):
        images = sorted(candidates[index], key=lambda g: g["bbox"][0])
        labels = sorted(row, key=lambda a: a["bbox"][0])
        if len(images) != len(labels) or len(images) < 2:
            continue
        if any(a["bbox"][2] > b["bbox"][0] + 3 for a, b in pairwise(images)):
            continue
        for group, anchor in zip(images, labels):
            if group.get("merge_warning"):
                continue
            if (
                max(
                    anchor["bbox"][0] - group["bbox"][2],
                    group["bbox"][0] - anchor["bbox"][2],
                    0,
                )
                <= 100
            ):
                group["option_override"] = anchor["label"]


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
        page_groups = {
            p["page_number"]: (
                _graph_regions(
                    [
                        i
                        for i in question["images"]
                        if i["page"] == p["page_number"]
                        and not i.get("decorative")
                        and valid_bbox(i["bbox"], p["width"], p["height"])
                    ]
                ),
                p["width"],
                p["height"],
            )
            for p in dataset["pages"]
            if any(s["page"] == p["page_number"] for s in pending["segments"])
        }
        anchors = image_choice_anchors(
            question, pending["lines"], page_groups
        ) or _anchors(question, pending["lines"])
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
                            groups = _graph_regions(meaningful)
                            refined = []
                            for group in groups:
                                box = group["bbox"]
                                graph_owner = (
                                    _graph_cell(group, anchors, number)
                                    if group.get("graph")
                                    else None
                                )
                                if graph_owner:
                                    group["option_override"] = graph_owner["label"]
                                    refined.append(group)
                                    continue
                                if any(
                                    a.get("object_ids")
                                    == {o["image_id"] for o in group["objects"]}
                                    for a in anchors
                                ):
                                    refined.append(group)
                                    continue
                                labels = [
                                    a
                                    for a in anchors
                                    if a["page"] == number
                                    and a.get("label_only")
                                    and box[0]
                                    <= (a["bbox"][0] + a["bbox"][2]) / 2
                                    <= box[2]
                                    and max(
                                        a["bbox"][1] - box[3], box[1] - a["bbox"][3], 0
                                    )
                                    <= 30
                                ]
                                object_choices = {
                                    choice
                                    for image in group["objects"]
                                    if (
                                        component_choice := _component(
                                            image["bbox"], number, anchors
                                        )
                                    )[0]
                                    == "option"
                                    and (choice := component_choice[1]) is not None
                                }
                                multiple_choices = (
                                    len(labels) > 1 or len(object_choices) > 1
                                )
                                split = (
                                    _regions(group["objects"], gap=3)
                                    if multiple_choices
                                    else [group]
                                )
                                if multiple_choices and len(split) == 1:
                                    split[0]["merge_warning"] = (
                                        "visual_multiple_option_images_merged:shared_geometry_requires_review"
                                    )
                                refined.extend(split)
                            groups = sorted(
                                refined, key=lambda g: (g["bbox"][1], g["bbox"][0])
                            )
                            _associate_rows(
                                groups,
                                anchors,
                                number,
                                pending["lines"],
                                len(question["raw"]["question_block"])
                                - len(question["raw"]["options_block"]),
                            )
                            for group in groups:
                                crop_owner = (
                                    group.get("option_override")
                                    or _component(group["bbox"], number, anchors)[1]
                                )
                                group["crop"], group["crop_context"] = focused_crop(
                                    group,
                                    pending["lines"],
                                    number,
                                    width,
                                    height,
                                    groups,
                                    anchors,
                                    owner_label=crop_owner,
                                )
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
                                asset.update(group["crop_context"])
                                if group.get("graph"):
                                    asset["visual_kind"] = "graph"
                                if group.get("merge_warning"):
                                    asset["warnings"].append(group["merge_warning"])
                                asset["belongs_to"], asset["option_label"] = _component(
                                    group["bbox"], number, anchors
                                )
                                if group.get("option_override"):
                                    asset["belongs_to"], asset["option_label"] = (
                                        "option",
                                        group["option_override"],
                                    )
                                confirmed = [a for a in anchors if a.get("object_ids")]
                                if confirmed:
                                    owner = next(
                                        (
                                            a
                                            for a in confirmed
                                            if a["object_ids"]
                                            == set(asset["object_ids"])
                                        ),
                                        None,
                                    )
                                    asset["belongs_to"], asset["option_label"] = (
                                        ("option", owner["label"])
                                        if owner
                                        else ("question", None)
                                    )
                                if group.get("merge_warning"):
                                    asset["belongs_to"], asset["option_label"] = (
                                        "unknown",
                                        None,
                                    )
                                if any(
                                    w.startswith("visual_option_labels_ambiguous:")
                                    for w in question["warnings"]
                                ):
                                    asset["belongs_to"], asset["option_label"] = (
                                        "unknown",
                                        None,
                                    )
                                if any(
                                    w.startswith(
                                        "visual_image_option_association_uncertain:"
                                    )
                                    for w in question["warnings"]
                                ) and any(
                                    a["page"] == number
                                    and group["bbox"][1] >= a["bbox"][1] - 8
                                    for a in anchors
                                ):
                                    asset["belongs_to"], asset["option_label"] = (
                                        "unknown",
                                        None,
                                    )
                                if asset["belongs_to"] == "option":
                                    owner = asset["option_label"]
                                    matching = [
                                        anchor
                                        for anchor in anchors
                                        if anchor["page"] == number
                                        and anchor["label"] == owner
                                    ]
                                    foreign = foreign_option_anchors(
                                        asset["bbox"], anchors, number, owner
                                    )
                                    if foreign:
                                        labels = ",".join(
                                            dict.fromkeys(a["label"] for a in foreign)
                                        )
                                        asset["warnings"].append(
                                            f"foreign_option_letter_in_crop:{owner}->{labels}"
                                        )
                                    if len(matching) != 1:
                                        asset["warnings"].append(
                                            "visual_option_anchor_ambiguous:manual_review"
                                        )
                                    if foreign or len(matching) != 1:
                                        asset["belongs_to"] = "unknown"
                                        asset["option_label"] = None
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
                                            matching = [
                                                anchor
                                                for anchor in anchors
                                                if anchor["page"] == number
                                                and anchor["label"] == option["label"]
                                            ]
                                            if len(matching) == 1:
                                                option.setdefault(
                                                    "label_bbox", matching[0]["bbox"]
                                                )
                                                option.setdefault("page", number)
                                            if asset["path"]:
                                                option["warnings"] = [
                                                    w
                                                    for w in option["warnings"]
                                                    if w
                                                    != "empty_option_text:may_be_image_only"
                                                ]
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
                            if question["options"] and all(
                                o["images"] and all(a["path"] for a in o["images"])
                                for o in question["options"]
                            ):
                                question["warnings"] = [
                                    w
                                    for w in question["warnings"]
                                    if w
                                    != "multi_column_options:text_and_image_association_unresolved"
                                ]
                                for option in question["options"]:
                                    option["warnings"] = [
                                        w
                                        for w in option["warnings"]
                                        if w
                                        != "multi_column_option:content_preserved_in_raw_options_block"
                                    ]
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
