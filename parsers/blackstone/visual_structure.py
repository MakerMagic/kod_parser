"""Focused visual boundaries and additive, raw-span-backed question layout."""

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


def words(line):
    return list(zip(line.get("word_boxes", []), line.get("word_texts", [])))


def focused_crop(group, lines, page, width, height):
    """Keep internal labels; external prose is a barrier, not a label source.

    Full line context is used before selecting nearby words, so a short fragment
    of a long sentence cannot masquerade as a diagram label. Raw text is untouched.
    """
    graphic = group["bbox"]
    kept, excluded, warnings = [], [], []
    included_spans, excluded_spans = [], []
    for line in lines:
        if line["page"] != page:
            continue
        box = [line["x0"], line["top"], line["x1"], line["bottom"]]
        nearby = [(b, t) for b, t in words(line) if overlaps(graphic, b, LABEL_REACH)]
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
        continuation = (
            outside
            and count >= 5
            and not named_caption
            and not text.rstrip().endswith((".", "?", ":"))
            and any(
                other["page"] == page
                and other is not line
                and abs(other["x0"] - line["x0"]) < 8
                and 0
                <= max(other["top"] - line["bottom"], line["top"] - other["bottom"])
                <= 8
                and len(words(other)) >= 5
                and other["text"].rstrip().endswith((".", "?", ":"))
                and (other["bottom"] <= graphic[1] or other["top"] >= graphic[3])
                for other in lines
            )
        )
        prose = (
            outside
            and not named_caption
            and count >= 5
            and (text.rstrip().endswith((".", "?", ":")) or continuation)
        )
        span = {"start": line["block_start"], "end": line["block_start"] + len(text)}
        if prose:
            excluded.extend(b for b, _ in nearby)
            excluded_spans.append(span)
            continue
        # Capture only local labels on rows shared by adjacent diagrams.
        kept.extend(
            b for b, _ in (words(line) if outside and named_caption else nearby)
        )
        included_spans.append(span)
        if outside and count >= 7:
            warnings.append(
                "visual_caption_boundary_uncertain:external_caption_preserved"
            )
            if not named_caption and len(nearby) < count:
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
    return crop, {
        "graphic_bbox": graphic[:],
        "crop_method": "pdf_objects_text_barriers",
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
            for word, _ in word_list:
                matches = [
                    a["image_id"]
                    for a in assets
                    if a["page"] == line["page"]
                    and a["bbox"][0] <= word[0]
                    and a["bbox"][1] <= word[1]
                    and a["bbox"][2] >= word[2]
                    and a["bbox"][3] >= word[3]
                ]
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
