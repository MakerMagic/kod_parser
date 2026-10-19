"""Source geometry for table-row rejection and inline mathematical choices."""

import re
from copy import deepcopy

from parsers.blackstone.visual_structure import words


def reject_data_rows(q, pending):
    """A named A--H dataset is not a separately supplied answer set.

    Require an explicit in-stem range, a referenced table with a header above the
    alleged choices, and dense numeric row records. A textual X-axis/Y-axis
    answer table or an ordinary A--E list does not meet these conditions.
    """
    from .parser import marker

    options = q["options"]
    labels = [o["label"] for o in options]
    if len(labels) < 3 or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]):
        return
    block = q["raw"]["question_block"]
    start = len(block) - len(q["raw"]["options_block"])
    prefix = q["question_text"]
    if not re.search(r"\btable\b", prefix, re.IGNORECASE):
        return
    request = re.search(r"\bWhich\b[^?]+\?", prefix, re.IGNORECASE | re.DOTALL)
    if not request or not re.search(
        r"\(\s*A\s*[-–]\s*" + labels[-1] + r"\s*\)", request[0]
    ):
        return
    header = prefix[request.end() :]
    if len(header.split()) < 6 or re.search(
        r"\b(?:answers?|options?|choices?)\b", header, re.IGNORECASE
    ):
        return
    if not all(len(re.findall(r"\d+(?:[.,]\d+)*", o["text"])) >= 4 for o in options):
        return
    anchors = [
        l for l in pending["lines"] if l["block_start"] >= start and marker(l, "option")
    ]
    if [marker(l, "option")[0] for l in anchors] != labels:
        return
    # Rows must have several aligned numeric columns, not sentence options.
    columns = []
    for line in anchors:
        boxes = [b for b, t in words(line) if re.fullmatch(r"\d[\d.,]*", t)]
        if len(boxes) < 4:
            return
        columns.append(boxes)
    if any(abs(row[0][0] - columns[0][0][0]) > 4 for row in columns):
        return
    q["raw"]["rejected_option_candidates"] = deepcopy(options)
    q["raw"]["option_rejection_evidence"] = {
        "method": "named_dataset_range_and_numeric_table_rows",
        "range": [labels[0], labels[-1]],
        "header": header,
        "anchor_spans": [l["block_start"] for l in anchors],
        "reason": "Choice letters are identifiers of records inside the referenced multi-column data table; no separate answer list is supplied.",
    }
    q["options"] = []
    q["raw"]["options_block"] = ""
    q["question_text"] = block[marker(pending["lines"][0], "number")[1] :]
    q["warnings"] = [
        w
        for w in q["warnings"]
        if not w.startswith(
            ("incomplete_or_ambiguous_options:", "multi_column_options:")
        )
    ]


def inline_layout(q, pending):
    """Attach exact glyph/line evidence to textual answer cells; no n/d rewrite."""
    from .parser import marker

    if len(q["options"]) < 3:
        return
    start = len(q["raw"]["question_block"]) - len(q["raw"]["options_block"])
    anchors = [
        l for l in pending["lines"] if l["block_start"] >= start and marker(l, "option")
    ]
    if [marker(l, "option")[0] for l in anchors] != [o["label"] for o in q["options"]]:
        return
    for i, (option, line) in enumerate(zip(q["options"], anchors)):
        if option.get("images"):
            continue
        following = anchors[i + 1] if i + 1 < len(anchors) else None
        middle = (line["top"] + line["bottom"]) / 2
        top = (
            (middle + (anchors[i - 1]["top"] + anchors[i - 1]["bottom"]) / 2) / 2
            if i
            else line["top"] - (line["bottom"] - line["top"])
        )
        bottom = (
            (middle + (following["top"] + following["bottom"]) / 2) / 2
            if following and following["page"] == line["page"]
            else float("inf")
        )
        evidence = []
        for item in pending.get("math_layout", []):
            b = item["bbox"]
            if (
                item["page"] == line["page"]
                and b[1] >= top
                and b[3] < bottom
                and b[0] > line["x0"] + 12
            ):
                evidence.append(deepcopy(item))
        if evidence:
            for item in evidence:
                item["glyphs"] = [c for c in item["glyphs"] if top <= c["top"] < bottom]
            option["glyph_layout"] = evidence
            option["label_bbox"] = next(
                (b for b, t in words(line) if t == option["label"]), None
            )
            option["page"] = line["page"]


def recover_spatial_text(q, pending):
    """Reassociate raised/lowered numeric rows, never normalize their values.

    Require a complete aligned sequence, repeated separator/glyph evidence,
    a finished preceding question and numeric/unit-only answer rows.
    """
    from .encoding import decode_block
    from .parser import interpreted, marker

    labels = [o["label"] for o in q["options"]]
    if len(labels) < 3 or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]):
        return
    start = len(q["raw"]["question_block"]) - len(q["raw"]["options_block"])
    anchors = [
        l for l in pending["lines"] if l["block_start"] >= start and marker(l, "option")
    ]
    if [marker(l, "option")[0] for l in anchors] != labels or len(
        {l["page"] for l in anchors}
    ) != 1:
        return
    if max(l["x0"] for l in anchors) - min(l["x0"] for l in anchors) > 4:
        return
    request = [
        l
        for l in pending["lines"]
        if l["block_start"] < start and "?" in interpreted(l)
    ]
    if not request:
        return
    before = request[-1]
    if before["page"] != anchors[0]["page"]:
        return
    height = anchors[0]["bottom"] - anchors[0]["top"]
    candidates = [
        l
        for l in pending["lines"]
        if l["page"] == before["page"]
        and l["top"] > before["bottom"]
        and l["top"] < anchors[-1]["bottom"] + height
        and l["x0"] >= anchors[0]["x0"] - 1
    ]
    if (
        sum(
            item["page"] == before["page"]
            and item["bbox"][1] > before["bottom"]
            and item["bbox"][3] < anchors[-1]["bottom"] + height
            for item in pending.get("math_layout", [])
        )
        < 2
    ):
        return
    grouped = {label: [] for label in labels}
    anchor_offsets = {l["block_start"]: marker(l, "option")[1] for l in anchors}
    block = q["raw"]["question_block"]
    for l in candidates:
        offset = anchor_offsets.get(l["block_start"], 0)
        value = interpreted(l)
        content = value[offset:].strip() if offset else value.strip()
        if not re.fullmatch(
            r"[\d\s/⁄.,%+−–*-]*(?:(?:km|cm|mm|m|s|kg|g|h)\b)?", content
        ):
            return
        nearest = min(
            anchors,
            key=lambda a: abs((a["top"] + a["bottom"] - l["top"] - l["bottom"]) / 2),
        )
        label = marker(nearest, "option")[0]
        if content:
            grouped[label].append(
                {
                    "text": block[
                        l["block_start"] + offset : l["block_start"] + len(l["text"])
                    ],
                    "raw_span": {
                        "start": l["block_start"] + offset,
                        "end": l["block_start"] + len(l["text"]),
                    },
                    "page": l["page"],
                    "bbox": [l["x0"], l["top"], l["x1"], l["bottom"]],
                }
            )
    if not all(grouped.values()):
        return
    earliest = min(l["block_start"] for l in candidates)
    q["raw"]["spatial_text_candidates"] = {
        "question_text": q["question_text"],
        "options": deepcopy(q["options"]),
        "options_block": q["raw"]["options_block"],
    }
    q["raw"]["field_method"] = "complete_choice_labels_and_numeric_glyph_rows"
    q["raw"]["options_block"] = block[earliest:]
    q["question_text"] = decode_block(
        block[marker(pending["lines"][0], "number")[1] : earliest], pending["lines"]
    )
    for o in q["options"]:
        o["text"] = "\n".join(
            decode_block(r["text"], pending["lines"]) for r in grouped[o["label"]]
        )
        o["source_lines"] = grouped[o["label"]]


def recover_inline_cells(dataset, records, asset_dir):
    """Unmix adjacent inline vector symbols via their distinct option rows."""
    from contextlib import closing
    from hashlib import sha256
    from pathlib import Path

    import pypdfium2 as pdfium

    from parsers.blackstone.visual_structure import bounds
    from parsers.blackstone.visuals import _save_crop

    with pdfium.PdfDocument(dataset["input"]["path"]) as doc:
        for q in dataset["questions"]:
            grouped = {}
            for option in q["options"]:
                items = option.get("glyph_layout", [])
                native = [
                    o
                    for o in q["images"]
                    if any(
                        o["page"] == item["page"]
                        and all(
                            abs(a - b) < 0.01 for a, b in zip(o["bbox"], item["bbox"])
                        )
                        for item in items
                    )
                ]
                if items and native:
                    grouped[option["label"]] = (option, items, native)
            if len(grouped) < 2:
                continue
            ids = {o["image_id"] for _, _, ns in grouped.values() for o in ns}
            old = [a for a in q["visual_assets"] if set(a["object_ids"]) & ids]
            if not old or any(set(a["object_ids"]) - ids for a in old):
                continue
            created = []
            for label, (option, items, native) in grouped.items():
                glyphs = {tuple(c.items()): c for item in items for c in item["glyphs"]}
                box = bounds(
                    [o["bbox"] for o in native]
                    + [
                        [c["x0"], c["top"], c["x1"], c["bottom"]]
                        for c in glyphs.values()
                    ]
                )
                box = [box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1]
                name = f"bmat_{dataset['year']}_q{q['question_number']:03}_p{option['page']:03}_inline_{label}_{sha256(repr(box).encode()).hexdigest()[:10]}"
                dest = (
                    Path(asset_dir) / dataset["input"]["sha256"][:20] / (name + ".png")
                )
                with (
                    closing(doc[option["page"] - 1]) as page,
                    closing(page.render(scale=2, rev_byteorder=True)) as bitmap,
                ):
                    size = _save_crop(
                        bitmap, bytes(bitmap.buffer), box, page.get_size(), dest, False
                    )
                asset = {
                    **deepcopy(old[0]),
                    "image_id": name,
                    "path": dest.relative_to(Path(asset_dir).parent).as_posix(),
                    "bbox": box,
                    "graphic_bbox": bounds([o["bbox"] for o in native]),
                    "pixel_size": size,
                    "sha256": sha256(dest.read_bytes()).hexdigest(),
                    "belongs_to": "option",
                    "option_label": label,
                    "object_ids": [o["image_id"] for o in native],
                    "warnings": [],
                    "association_method": "bmat_inline_choice_geometry",
                    "page": option["page"],
                    "placement": {"component": "option", "label": label},
                    "visual_text": [],
                    "association_evidence": {
                        "distinct_option_row": True,
                        "raw_glyph_geometry": True,
                    },
                }
                created.append(asset)
                option["images"] = [deepcopy(asset)]
                for obj in native:
                    obj.update(
                        belongs_to="option",
                        option_label=label,
                        asset_id=name,
                        path=asset["path"],
                    )
            q["raw"].setdefault("inline_visual_candidates", []).extend(deepcopy(old))
            q["visual_assets"] = [
                a for a in q["visual_assets"] if a not in old
            ] + created
            for i, a in enumerate(q["visual_assets"], 1):
                a["asset_index"] = i
            removed = {w for a in old for w in a["warnings"]}
            still = {w for a in q["visual_assets"] for w in a["warnings"]}
            q["warnings"] = [w for w in q["warnings"] if w not in removed - still]
