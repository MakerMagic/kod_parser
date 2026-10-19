"""Conservative repeated-layout detection for label-anchored image choices."""

import re
from math import ceil

from .visual_structure import (
    bounds,
    focused_crop,
    option_anchor_is_left_of_visual,
    words,
)


def option_cell_owner(box, anchors, page):
    """Require a complete answer set and containment in one label-defined cell.

    Unlike fragment voting, a following label merely near the bottom edge does
    not claim an otherwise contained shape. This never accepts an object that
    crosses the next option boundary or an arbitrary letter inside a diagram.
    """
    labels = [a["label"] for a in anchors]
    if (
        len(labels) < 5
        or len(set(labels)) != len(labels)
        or set(labels) != set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)])
    ):
        return None
    candidates = []
    on_page = [a for a in anchors if a["page"] == page and a.get("label_only")]
    for anchor in on_page:
        a = anchor["bbox"]
        height = a[3] - a[1]
        if not option_anchor_is_left_of_visual(anchor, box) or box[1] < a[1] - height:
            continue
        right = min(
            (
                b["bbox"][0]
                for b in on_page
                if abs(b["bbox"][1] - a[1]) < height and b["bbox"][0] > a[2]
            ),
            default=float("inf"),
        )
        bottom = min(
            (
                b["bbox"][1]
                for b in on_page
                if abs(b["bbox"][0] - a[0]) < height * 2 and b["bbox"][1] > a[3]
            ),
            default=float("inf"),
        )
        reach = min((right - a[2]) * 0.7, (box[2] - box[0]) * 1.5)
        if box[2] < right and box[3] < bottom and box[0] - a[2] <= reach:
            candidates.append(anchor)
    return candidates[0] if len(candidates) == 1 else None


def partition_option_objects(group, anchors, page, bitmap, pixels, page_size):
    """Separate native objects with distinct, complete option-cell ownership.

    Overlapping raster envelopes additionally require a rendered blank band
    around the next label row. A shared PDF object cannot be split this way.
    Source object IDs and their original bboxes remain unchanged.
    """
    buckets = {}
    for obj in group["objects"]:
        owner = option_cell_owner(obj["bbox"], anchors, page)
        if owner is None:
            return None
        buckets.setdefault(owner["label"], {"owner": owner, "objects": []})[
            "objects"
        ].append(obj)
    if len(buckets) < 2:
        return None
    pieces = [
        {
            "bbox": bounds([o["bbox"] for o in b["objects"]]),
            "objects": b["objects"],
            "option_override": label,
        }
        for label, b in buckets.items()
    ]
    sx, sy = bitmap.width / page_size[0], bitmap.height / page_size[1]
    for upper in pieces:
        for lower in pieces:
            u, v = upper["bbox"], lower["bbox"]
            if upper is lower or not (
                u[1] < v[1] < u[3] and max(u[0], v[0]) < min(u[2], v[2])
            ):
                continue
            if any(o["kind"] != "raster" for g in (upper, lower) for o in g["objects"]):
                return None
            a = buckets[lower["option_override"]]["owner"]["bbox"]
            h = a[3] - a[1]
            first, last = max(v[1], a[1] - h), min(u[3] + h, a[3])
            x0, x1 = int(min(u[0], v[0]) * sx), ceil(max(u[2], v[2]) * sx)
            runs, run = [], []
            for y in range(max(0, int(first * sy)), min(bitmap.height, int(last * sy))):
                scan = pixels[y * bitmap.stride + x0 * 3 : y * bitmap.stride + x1 * 3]
                if scan and min(scan) >= 245:
                    run.append(y)
                elif run:
                    runs.append(run)
                    run = []
            if run:
                runs.append(run)
            valid = [r for r in runs if len(r) / sy >= h * 0.25]
            if not valid:
                return None
            band = max(valid, key=len)
            cut = (band[0] + band[-1] + 1) / (2 * sy)
            upper["bbox"][3] = min(u[3], cut)
            lower["bbox"][1] = max(v[1], cut)
            lower.setdefault("object_crop_evidence", []).extend(
                {
                    "object_id": obj["image_id"],
                    "source_bbox": obj["bbox"][:],
                    "visible_bbox": [
                        obj["bbox"][0],
                        max(obj["bbox"][1], cut),
                        *obj["bbox"][2:],
                    ],
                    "method": "complete_option_cells_and_rendered_blank_band",
                    "blank_band_bbox": [
                        x0 / sx,
                        band[0] / sy,
                        x1 / sx,
                        (band[-1] + 1) / sy,
                    ],
                    "cut": cut,
                    "option_label": lower["option_override"],
                    "neighbor_option_label": upper["option_override"],
                    "neighbor_object_ids": [o["image_id"] for o in upper["objects"]],
                    "minimum_channel": 245,
                }
                for obj in lower["objects"]
                if obj["bbox"][1] < cut
            )
    for piece in pieces:
        piece["grouping_notes"] = [
            "Native PDF objects partitioned by complete option-anchor cells; overlapping raster padding separated only at a rendered blank band. Original object bounds retained."
        ]
    return pieces


def contains(outer, inner, tolerance=0.1):
    return all(
        (
            outer[i] <= inner[i] + tolerance
            if i < 2
            else outer[i] >= inner[i] - tolerance
        )
        for i in range(4)
    )


def image_choice_anchors(question, lines, pages):
    """Recover labels hidden in rows like 'A 100 B 100', only with full evidence.

    Require a unique contiguous sequence, separate similarly sized visuals,
    repeated anchor alignment, and coverage of ALL non-anchor option words.
    Existing raw blocks are never rewritten; uncertain candidates stay raw.
    """
    start = len(question["raw"]["question_block"]) - len(
        question["raw"]["options_block"]
    )
    candidates = []
    for line in lines:
        if line["block_start"] < start or line["page"] not in pages:
            continue
        groups, width, height = pages[line["page"]]
        for box, text in words(line):
            if not re.fullmatch(r"[A-Z]", text):
                continue
            if any(contains(g["bbox"], box) for g in groups):
                continue  # Letters inside diagrams are not option anchors.
            eligible = [
                g
                for g in groups
                if option_anchor_is_left_of_visual({"bbox": box}, g["bbox"])
                and g["bbox"][0] - box[2] <= 60
                and abs(g["bbox"][1] - box[1]) <= (50 if g.get("graph") else 20)
            ]
            if len(eligible) != 1:
                continue
            candidates.append(
                {
                    "label": text,
                    "bbox": box,
                    "page": line["page"],
                    "label_only": True,
                    "group": eligible[0],
                    "line_start": line["block_start"],
                    "size": (width, height),
                }
            )
    labels = [a["label"] for a in candidates]
    if len(labels) < 5 or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]):
        return []
    if len({id(a["group"]) for a in candidates}) != len(candidates):
        return []
    # Detached legend swatches are native parts of an answer chart, not body
    # figures. Only a complete, unique answer-cell layout can claim them.
    primary = {id(a["group"]) for a in candidates}
    for anchor in candidates:
        groups = pages[anchor["page"]][0]
        extras = [
            g
            for g in groups
            if id(g) not in primary
            and option_cell_owner(
                bounds([anchor["group"]["bbox"], g["bbox"]]), candidates, anchor["page"]
            )
            is anchor
        ]
        if extras:
            original = anchor["group"]
            anchor["group"] = {
                **original,
                "bbox": bounds([original["bbox"], *[g["bbox"] for g in extras]]),
                "objects": [
                    *original["objects"],
                    *[o for g in extras for o in g["objects"]],
                ],
            }
    sizes = [
        (
            a["group"]["bbox"][2] - a["group"]["bbox"][0],
            a["group"]["bbox"][3] - a["group"]["bbox"][1],
        )
        for a in candidates
    ]
    similar = all(
        min(s[i] for s in sizes) >= max(s[i] for s in sizes) * 0.65 for i in (0, 1)
    )
    # Shape choices can have different widths. A complete label-only answer
    # region plus a repeated height/width is stronger evidence than dimensions
    # alone. Still require unique groups, left anchors, full text containment,
    # safe crop boundaries and repeated alignment below.
    label_only_region = all(
        not line.get("readable_text", line["text"]).strip()
        or re.fullmatch(
            r"[A-Z](?:\s+[A-Z])*", line.get("readable_text", line["text"]).strip()
        )
        for line in lines
        if line["block_start"] >= start
    )
    shared_dimension = any(
        min(s[i] for s in sizes) >= max(s[i] for s in sizes) * 0.85 for i in (0, 1)
    )
    bounded_shapes = all(
        option_cell_owner(a["group"]["bbox"], candidates, a["page"]) is a
        for a in candidates
    )
    if (
        not similar
        and not (label_only_region and shared_dimension)
        and not bounded_shapes
    ):
        return []
    if not all(
        any(
            b is not a
            and b["page"] == a["page"]
            and (
                abs(a["bbox"][0] - b["bbox"][0]) < 8
                or abs(a["bbox"][1] - b["bbox"][1]) < 8
            )
            for b in candidates
        )
        for a in candidates
    ):
        return []
    for anchor in candidates:
        groups, width, height = pages[anchor["page"]]
        owned_ids = {o["image_id"] for o in anchor["group"]["objects"]}
        neighbors = [
            g
            for g in groups
            if not owned_ids.intersection(o["image_id"] for o in g["objects"])
        ]
        anchor["crop"], evidence = focused_crop(
            anchor["group"],
            lines,
            anchor["page"],
            width,
            height,
            [anchor["group"], *neighbors],
            candidates,
            owner_label=anchor["label"],
        )
        if evidence["warnings"]:
            question["warnings"].append(
                "visual_image_option_association_uncertain:crop_boundary"
            )
            return []
    for line in lines:
        if line["block_start"] < start:
            continue
        for box, text in words(line):
            if any(
                a["page"] == line["page"] and a["bbox"] == box and a["label"] == text
                for a in candidates
            ):
                continue
            if not any(
                a["page"] == line["page"] and contains(a["crop"], box)
                for a in candidates
            ):
                # Genuine mixed text/image options are not rewritten. Incomplete
                # parsed labels, however, make this repeated visual layout suspect.
                if [o["label"] for o in question["options"]] != labels:
                    question["warnings"].append(
                        "visual_image_option_association_uncertain:outside_text"
                    )
                return []
    question["raw"]["text_option_candidates"] = question["options"]
    question["options"] = [
        {
            "label": a["label"],
            "text": "",
            "images": [],
            "warnings": [],
            "content_type": "image",
            "page": a["page"],
            "label_bbox": a["bbox"],
            "association_method": "repeated_label_visual_layout_and_text_containment",
        }
        for a in candidates
    ]
    question["warnings"] = [
        w
        for w in question["warnings"]
        if not w.startswith(
            (
                "incomplete_or_ambiguous_options:",
                "multi_column_options:",
            )
        )
    ]
    return [
        {
            **{k: a[k] for k in ("label", "bbox", "page", "label_only")},
            "object_ids": {o["image_id"] for o in a["group"]["objects"]},
        }
        for a in candidates
    ]


def coalesce_anchor_groups(groups, anchors, page):
    """Reassemble only object sets already certified by complete text containment."""
    remaining = list(groups)
    result = []
    for anchor in anchors:
        ids = anchor.get("object_ids")
        if anchor["page"] != page or not ids:
            continue
        owned = [g for g in remaining if {o["image_id"] for o in g["objects"]} <= ids]
        if (
            len(owned) < 2
            or {o["image_id"] for g in owned for o in g["objects"]} != ids
        ):
            continue
        result.append(
            {
                "bbox": bounds([g["bbox"] for g in owned]),
                "objects": [o for g in owned for o in g["objects"]],
                "graph": any(g.get("graph") for g in owned),
                "option_override": anchor["label"],
                "grouping_notes": [
                    "Complete answer-cell geometry and text containment bind detached visual components, including legends, to one option."
                ],
            }
        )
        remaining = [g for g in remaining if g not in owned]
    return [*remaining, *result]


def attach_visual_text(question, lines):
    """Keep geometrically owned text with its visual, backed by original spans."""
    for asset in question["visual_assets"]:
        owned = [
            line
            for line in lines
            if line["page"] == asset["page"]
            and words(line)
            and all(contains(asset["bbox"], box) for box, _ in words(line))
        ]
        graph = asset.get("visual_kind") == "graph"
        vertical = {}
        if graph:
            for line in owned:
                for run in line.get("oriented_runs", []):
                    if contains(asset["bbox"], run["bbox"]):
                        key = (run["text"], tuple(run["bbox"]))
                        vertical.setdefault(key, {"run": run, "spans": []})[
                            "spans"
                        ].append(
                            {
                                "start": line["block_start"],
                                "end": line["block_start"] + len(line["text"]),
                            }
                        )
        asset["visual_text"] = []
        for line in lines:
            if line["page"] != asset["page"]:
                continue
            for box, value in words(line):
                if not contains(asset["bbox"], box):
                    continue
                if graph and any(
                    contains(item["run"]["bbox"], box, tolerance=1)
                    for item in vertical.values()
                ):
                    continue
                asset["visual_text"].append(
                    {
                        "text": value,
                        "bbox": box,
                        "source_line_span": {
                            "start": line["block_start"],
                            "end": line["block_start"] + len(line["text"]),
                        },
                    }
                )
        if not graph:
            continue
        asset["axis_labels"] = []
        for entry in vertical.values():
            run = entry["run"]
            spans = list(dict.fromkeys((s["start"], s["end"]) for s in entry["spans"]))
            label = {
                "axis": "y",
                "text": run["text"],
                "bbox": run["bbox"],
                "page": asset["page"],
                "orientation": "pdf_text_matrix",
                "source_line_spans": [
                    {"start": start, "end": end} for start, end in spans
                ],
            }
            asset["axis_labels"].append(label)
            asset["visual_text"].append(
                {
                    "text": run["text"],
                    "bbox": run["bbox"],
                    "source_line_spans": label["source_line_spans"],
                    "orientation": "pdf_text_matrix",
                }
            )
        graphic = asset.get("graphic_bbox", asset["bbox"])
        center = (graphic[0] + graphic[2]) / 2
        for line in owned:
            value = line["text"].strip()
            if not re.fullmatch(r"[A-Za-z][A-Za-z ]{0,32}", value):
                continue
            if not graphic[3] <= line["top"] <= graphic[3] + 40:
                continue
            if (
                abs((line["x0"] + line["x1"]) / 2 - center)
                > (graphic[2] - graphic[0]) * 0.35
            ):
                continue
            asset["axis_labels"].append(
                {
                    "axis": "x",
                    "text": value,
                    "bbox": [line["x0"], line["top"], line["x1"], line["bottom"]],
                    "page": asset["page"],
                    "orientation": "horizontal_pdf_text",
                    "source_line_spans": [
                        {
                            "start": line["block_start"],
                            "end": line["block_start"] + len(line["text"]),
                        }
                    ],
                }
            )

    # PDF text extraction can reverse vertically transformed glyphs. Keep every
    # original byte in raw.question_block, but do not present graph-owned tokens
    # as ordinary question prose.
    block = question["raw"]["question_block"]
    original = question["question_text"]
    start = block.find(original)
    if start < 0 or not original:
        return
    graph_assets = [
        a for a in question["visual_assets"] if a.get("visual_kind") == "graph"
    ]
    spans = []
    for line in lines:
        begin = line["block_start"]
        end = begin + len(line["text"])
        if not (start <= begin and end <= start + len(original)) or not words(line):
            continue
        if any(
            line["page"] == asset["page"]
            and all(contains(asset["bbox"], box) for box, _ in words(line))
            for asset in graph_assets
        ):
            spans.append((begin - start, end - start))
    if spans:
        question["raw"]["text_question_candidate"] = original
        removed = []
        for begin, end in sorted(set(spans), reverse=True):
            if end < len(original) and original[end] == "\n":
                end += 1
            removed.append((begin, end))
            original = original[:begin] + original[end:]
        question["question_text"] = original
        return sorted(removed)
    return []
