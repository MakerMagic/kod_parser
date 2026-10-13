"""Focused visual boundaries and additive, raw-span-backed question layout."""

import math
import re

ASSET_PADDING = 4
LABEL_REACH = 16
STEM = re.compile(
    r"^(?:Which|What|How|Why|Who|Where|When|Is|Are|Does|Do|Can|Could|Should|Would)\b",
    re.IGNORECASE,
)


def bounds(boxes):
    return [
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    ]


def overlaps(a, b, gap=0):
    return (
        a[0] <= b[2] + gap
        and b[0] <= a[2] + gap
        and a[1] <= b[3] + gap
        and b[1] <= a[3] + gap
    )


def intersects(a, b):
    """Positive-area overlap; touching PDF bounds are not a contained letter."""
    return (
        min(a[2], b[2]) > max(a[0], b[0]) + 0.1
        and min(a[3], b[3]) > max(a[1], b[1]) + 0.1
    )


def foreign_option_anchors(crop, anchors, page, owner_label):
    """Only structural option anchors count, never letters inside a graphic."""
    return [
        anchor
        for anchor in anchors
        if anchor["page"] == page
        and anchor["label"] != owner_label
        and intersects(crop, anchor["bbox"])
    ]


def option_anchor_is_left_of_visual(anchor, visual):
    """Image-choice labels are structural anchors only when left of the visual."""
    return anchor["bbox"][2] <= visual[0] + 0.1


def words(line):
    return list(zip(line.get("word_boxes", []), line.get("word_texts", [])))


def rotated_label_bounds(chars, *, with_runs=False):
    """Join transformed glyphs in PDF stream order along their own baseline."""
    result, runs, run = {}, [], []

    def finish():
        if run:
            box = bounds([[c["x0"], c["top"], c["x1"], c["bottom"]] for c in run])
            record = {
                "text": "".join(c["text"] for c in run),
                "bbox": box,
                "vertical": all(c.get("upright") is False for c in run)
                and abs(run[0]["matrix"][0]) < 0.1,
                "keys": {(c["x0"], c["top"], c["text"]) for c in run},
            }
            runs.append(record)
            for c in run:
                result[(c["x0"], c["top"], c["text"])] = box
            run.clear()

    for char in chars:
        matrix = char.get("matrix", (1, 0, 0, 1, 0, 0))
        if abs(matrix[1]) < 0.01:
            finish()
            continue
        if run:
            previous = run[-1]["matrix"]
            length = math.hypot(matrix[0], matrix[1])
            dx, dy = matrix[4] - previous[4], matrix[5] - previous[5]
            along = (dx * matrix[0] + dy * matrix[1]) / length
            across = abs(dx * matrix[1] - dy * matrix[0]) / length
            same_orientation = all(
                abs(a - b) < 0.02 for a, b in zip(matrix[:4], previous[:4])
            )
            advance = max(length * 1.3, run[-1].get("adv", 0) * 1.5)
            if not same_orientation or across > 1 or not 0 < along <= advance:
                finish()
        run.append(char)
    finish()
    return (result, runs) if with_runs else result


def _prose_lines(lines, graphic):
    """Paragraph membership includes short wrapped endings, not just long lines."""
    outside = [
        line
        for line in lines
        if (line["bottom"] <= graphic[1] or line["top"] >= graphic[3])
        and not re.match(
            r"^(?:Figure|Fig\.|Table|Chart|Diagram)\s+\d+\b",
            line["text"],
            re.IGNORECASE,
        )
    ]
    prose = {
        id(line)
        for line in outside
        if len(line["text"].split()) >= 5
        and line["text"].rstrip().endswith((".", "?", ":"))
    }
    # A wrapped paragraph may end in only two or three words. Grow through
    # aligned, closely spaced prose, but never through a visual's internal text.
    changed = True
    while changed:
        changed = False
        for line in outside:
            if id(line) in prose:
                continue
            for other in outside:

                def indent(item):
                    tokens = words(item)
                    if len(tokens) > 1 and tokens[0][1].isdigit():
                        return tokens[1][0][0]
                    return item["x0"]

                if abs(indent(other) - indent(line)) >= 8:
                    continue
                gap = max(other["top"] - line["bottom"], line["top"] - other["bottom"])
                if not 0 <= gap <= 8:
                    continue
                if id(other) in prose or (
                    len(other["text"].split()) >= 8
                    and line["text"].rstrip().endswith((".", "?", ":"))
                ):
                    prose.update((id(line), id(other)))
                    changed = True
                    break
    return prose


def _distance(a, b):
    return max(a[0] - b[2], b[0] - a[2], 0) ** 2 + max(a[1] - b[3], b[1] - a[3], 0) ** 2


def focused_crop(
    group, lines, page, width, height, neighbors=(), anchors=(), owner_label=None
):
    """Keep internal labels; external prose is a barrier, not a label source.

    Full line context is used before selecting nearby words, so a short fragment
    of a long sentence cannot masquerade as a diagram label. Raw text is untouched.
    """
    graphic = group["bbox"]
    graph = bool(group.get("graph"))
    page_lines = [line for line in lines if line["page"] == page]
    if group.get("closed_box"):
        # A complete drawn border is a stronger boundary than nearby prose.
        # Its internal words (including table cells) are already inside it.
        included = [
            {
                "start": line["block_start"],
                "end": line["block_start"] + len(line["text"]),
            }
            for line in page_lines
            if any(
                graphic[0] - 1 <= box[0]
                and box[2] <= graphic[2] + 1
                and graphic[1] - 1 <= box[1]
                and box[3] <= graphic[3] + 1
                for box, _ in words(line)
            )
        ]
        crop = [
            max(0, graphic[0] - ASSET_PADDING),
            max(0, graphic[1] - ASSET_PADDING),
            min(width, graphic[2] + ASSET_PADDING),
            min(height, graphic[3] + ASSET_PADDING),
        ]
        return crop, {
            "graphic_bbox": graphic[:],
            "crop_method": "pdf_closed_border",
            "included_text_spans": included,
            "excluded_text_spans": [],
            "warnings": [],
        }
    prose_lines = _prose_lines(page_lines, graphic)
    others = [g["bbox"] for g in neighbors if g is not group and g["bbox"] != graphic]
    kept, excluded, warnings = [], [], []
    included_spans, excluded_spans = [], []
    for line in lines:
        if line["page"] != page:
            continue
        box = [line["x0"], line["top"], line["x1"], line["bottom"]]
        line_anchors = [
            anchor
            for anchor in anchors
            if anchor["page"] == page
            and any(anchor["bbox"] == word for word, _ in words(line))
        ]
        # An external line led by another option's anchor is that option's
        # content, not a caption for this visual (e.g. "C Third" below B).
        if (
            line_anchors
            and not any(a["label"] == owner_label for a in line_anchors)
            and (box[3] <= graphic[1] or box[1] >= graphic[3])
        ):
            continue
        nearby = []
        for b, t in words(line):
            if any(
                anchor["page"] == page
                and anchor["label"] != owner_label
                and anchor["bbox"] == b
                for anchor in anchors
            ):
                continue
            # Rotated axis numerals can extend well below the drawn axes. Their
            # nearest graphic owns them, even when another chart is just below.
            axis_row = all(
                re.fullmatch(r"[\d.,%+−-]+|[A-Z]", value) for _, value in words(line)
            )
            reach = (
                min(40, max(34, (graphic[2] - graphic[0]) * 0.16))
                if graph
                else 34
                if axis_row and re.fullmatch(r"[\d.,%+−-]+", t)
                else LABEL_REACH
            )
            if not overlaps(graphic, b, reach):
                continue
            if any(_distance(b, other) < _distance(b, graphic) for other in others):
                continue
            nearby.append((b, t))
        if not nearby:
            continue
        outside = box[3] <= graphic[1] or box[1] >= graphic[3]
        text = line["text"]
        count = len(words(line))
        named_caption = bool(
            re.match(
                r"^(?:Figure|Fig\.|Table|Chart|Diagram)\s+\d+\b", text, re.IGNORECASE
            )
        )
        prose = id(line) in prose_lines
        span = {"start": line["block_start"], "end": line["block_start"] + len(text)}
        if prose:
            excluded.extend(b for b, _ in nearby)
            excluded_spans.append(span)
            continue
        # Capture only local labels on rows shared by adjacent diagrams.
        if outside and named_caption:
            nearby = [
                (b, t)
                for b, t in words(line)
                if not any(
                    _distance(b, other) < _distance(b, graphic) for other in others
                )
            ]
        kept.extend(b for b, _ in nearby)
        included_spans.append(span)
        if (
            outside
            and count >= 7
            and not all(re.fullmatch(r"[\d.,%+−-]+", t) for _, t in nearby)
        ):
            warnings.append(
                "visual_caption_boundary_uncertain:external_caption_preserved"
            )
            if len(nearby) < count:
                warnings.append(
                    "visual_caption_may_be_incomplete:local_text_preserved_in_layout"
                )
    expanded = bounds([graphic, *kept])
    crop = [
        max(0, expanded[0] - ASSET_PADDING),
        max(0, expanded[1] - ASSET_PADDING),
        min(width, expanded[2] + ASSET_PADDING),
        min(height, expanded[3] + ASSET_PADDING),
    ]
    # Padding must not reintroduce prose which was deliberately excluded.
    for box in excluded:
        if box[3] <= expanded[1]:
            crop[1] = max(crop[1], min(expanded[1], box[3] + 1))
        elif box[1] >= expanded[3]:
            crop[3] = min(crop[3], max(expanded[3], box[1] - 1))
        if overlaps(crop, box) and box[1] < crop[3] and box[3] > crop[1]:
            warnings.append("visual_crop_contains_unrelated_text:boundary_overlap")
    # Padding cannot cross into a neighboring graphic. If actual content bounds
    # overlap, retain it and report ambiguity instead of clipping real content.
    for box in others:
        if not overlaps(crop, box):
            continue
        if box[2] <= expanded[0]:
            crop[0] = max(crop[0], (box[2] + expanded[0]) / 2)
        elif box[0] >= expanded[2]:
            crop[2] = min(crop[2], (box[0] + expanded[2]) / 2)
        elif box[3] <= expanded[1]:
            crop[1] = max(crop[1], (box[3] + expanded[1]) / 2)
        elif box[1] >= expanded[3]:
            crop[3] = min(crop[3], (box[1] + expanded[3]) / 2)
        else:
            warnings.append("visual_neighbor_boundary_uncertain:content_bounds_overlap")
    for anchor in foreign_option_anchors(crop, anchors, page, owner_label):
        box = anchor["bbox"]
        # A structural letter outside the actual visual is a crop barrier.
        # Trim padding only; never clip graphic objects or retained labels.
        candidates = []
        if box[2] + 1 <= expanded[0]:
            candidates.append((expanded[0] - box[2], 0, box[2] + 1))
        if box[0] - 1 >= expanded[2]:
            candidates.append((box[0] - expanded[2], 2, box[0] - 1))
        if box[3] + 1 <= expanded[1]:
            candidates.append((expanded[1] - box[3], 1, box[3] + 1))
        if box[1] - 1 >= expanded[3]:
            candidates.append((box[1] - expanded[3], 3, box[1] - 1))
        if candidates:
            _, edge, value = min(candidates)
            crop[edge] = max(crop[edge], value) if edge < 2 else min(crop[edge], value)
        if intersects(crop, box):
            warnings.append("visual_option_anchor_boundary_uncertain:manual_review")
    return crop, {
        "graphic_bbox": graphic[:],
        "crop_method": "pdf_objects_paragraph_barriers_text_ownership",
        "included_text_spans": included_spans,
        "excluded_text_spans": excluded_spans,
        "warnings": list(dict.fromkeys(warnings)),
    }


def add_layout(question, pending):
    """Record source-order text/visual blocks without replacing any existing field."""
    lines = pending["lines"]
    assets = question["visual_assets"]
    options_start = len(question["raw"]["question_block"]) - len(
        question["raw"]["options_block"]
    )
    stems = [
        line
        for line in lines
        if line["block_start"] < options_start
        and STEM.match(re.sub(r"^\d+\s+", "", line["text"]))
    ]
    stem_start = stems[-1]["block_start"] if stems else None
    sublabels = {sub["label"] for sub in question["subpoints"]}
    blocks = []
    option_label = None
    subpart_label = None
    option_labels = {o["label"] for o in question["options"]}
    for line in lines:
        text, start = line["text"], line["block_start"]
        box = [line["x0"], line["top"], line["x1"], line["bottom"]]
        component, label = "question_body", None
        if start >= options_start and question["options"]:
            match = re.match(r"^([A-Z])(?:\s|$)", text)
            cid = re.match(r"^\(cid:(3[6-9]|40)\)", text)
            if (
                match
                and match[1] in option_labels
                or cid
                and chr(int(cid[1]) + 29) in option_labels
            ):
                option_label = match[1] if match else chr(int(cid[1]) + 29)
            grouped = bool(re.fullmatch(r"[A-Z](?:\s+[A-Z])+", text))
            component, label = "option", None if grouped else option_label
        else:
            sub = re.match(r"^([1-9]\d*)[.)]\s+", text)
            if sub and sub[1] in sublabels:
                subpart_label = sub[1]
            elif start == stem_start:
                subpart_label = None
            if subpart_label:
                component, label = "subpart", subpart_label
            elif stem_start is not None and start < stem_start:
                component = "stimulus"
        linked = []
        word_list = words(line)
        if word_list:
            coverage = []
            for word, word_text in word_list:
                matches = [
                    a["image_id"]
                    for a in assets
                    if a["page"] == line["page"]
                    and a["bbox"][0] <= word[0]
                    and a["bbox"][1] <= word[1]
                    and a["bbox"][2] >= word[2]
                    and a["bbox"][3] >= word[3]
                ]
                # An image-choice anchor is represented by its option heading,
                # not by repeating a mixed extracted row such as 'A 100 B 100'.
                for option in question["options"]:
                    if (
                        option.get("content_type") == "image"
                        and option.get("page") == line["page"]
                        and option.get("label_bbox") == word
                        and option["label"] == word_text
                    ):
                        matches.extend(a["image_id"] for a in option["images"])
                coverage.append(matches)
            if all(coverage):
                linked = list(dict.fromkeys(i for matches in coverage for i in matches))
        blocks.append(
            {
                "type": "text",
                "component": "visual_label" if linked else component,
                "label": label,
                "page": line["page"],
                "bbox": box,
                "text": text,
                "raw_span": {"start": start, "end": start + len(text)},
                "asset_ids": linked,
            }
        )
    for asset in assets:
        page, box = asset["page"], asset.get("graphic_bbox", asset["bbox"])
        context = [
            b
            for b in blocks
            if b["page"] == page
            and b["type"] == "text"
            and b["component"] != "visual_label"
        ]
        before = [b for b in context if b["bbox"][3] <= box[1]]
        after = [b for b in context if b["bbox"][1] >= box[3]]
        preceding = max(before, key=lambda b: b["bbox"][3], default=None)
        following = min(after, key=lambda b: b["bbox"][1], default=None)
        if asset["belongs_to"] == "option":
            component, label = "option", asset["option_label"]
        elif (
            asset["belongs_to"] == "unknown"
            or asset.get("warnings")
            and any(
                "boundary_overlap" in w or "coordinate_space" in w
                for w in asset["warnings"]
            )
        ):
            component, label = "unknown", None
        elif (
            preceding and following and preceding["component"] != following["component"]
        ):
            component, label = "intermediate", None
        elif preceding or following:
            neighbor = preceding or following
            component, label = neighbor["component"], neighbor["label"]
        else:
            component, label = "unknown", None
        asset["placement"] = {
            "component": component,
            "label": label,
            "after_raw_span": preceding["raw_span"] if preceding else None,
            "before_raw_span": following["raw_span"] if following else None,
        }
        if (
            component == "unknown"
            and "visual_component_association_uncertain" not in asset["warnings"]
        ):
            asset["warnings"].append("visual_component_association_uncertain")
            question["warnings"].append("visual_component_association_uncertain")
        blocks.append(
            {
                "type": "visual",
                "component": component,
                "label": label,
                "page": page,
                "bbox": box,
                "asset_id": asset["image_id"],
                "raw_span": None,
            }
        )
    blocks.sort(
        key=lambda b: (b["page"], round(b["bbox"][1] / 4), b["bbox"][0], b["type"])
    )
    for order, block in enumerate(blocks, 1):
        block["block_id"] = f"block_{order:03}"
        block["order"] = order
    question["layout_blocks"] = blocks
