"""Conservative repeated-layout detection for label-anchored image choices."""

import re

from .visual_structure import focused_crop, option_anchor_is_left_of_visual, words


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
    sizes = [
        (
            a["group"]["bbox"][2] - a["group"]["bbox"][0],
            a["group"]["bbox"][3] - a["group"]["bbox"][1],
        )
        for a in candidates
    ]
    if any(min(s[i] for s in sizes) < max(s[i] for s in sizes) * 0.65 for i in (0, 1)):
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
        anchor["crop"], evidence = focused_crop(
            anchor["group"],
            lines,
            anchor["page"],
            width,
            height,
            groups,
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
        for begin, end in sorted(set(spans), reverse=True):
            if end < len(original) and original[end] == "\n":
                end += 1
            original = original[:begin] + original[end:]
        question["question_text"] = original
