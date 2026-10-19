"""BMAT above-centred choice labels, independent of TSA's left-label geometry."""

import re
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pypdfium2 as pdfium

from parsers.blackstone.visual_structure import bounds, words
from parsers.blackstone.visuals import _save_crop


def centered_cells(question, pending, width):
    options = question["options"]
    if len(options) < 3 or any(o["text"].strip() for o in options):
        return []
    start = len(question["raw"]["question_block"]) - len(
        question["raw"]["options_block"]
    )
    anchors = []
    for line in pending["lines"]:
        text = line.get("readable_text", line["text"]).strip()
        if line["block_start"] < start or not re.fullmatch(r"[A-Z](?:\s+[A-Z])*", text):
            continue
        anchors.extend(
            {"label": t, "bbox": b, "page": line["page"]}
            for b, t in words(line)
            if re.fullmatch("[A-Z]", t)
        )
    if [a["label"] for a in anchors] != [o["label"] for o in options]:
        return []
    cells = []
    for a in anchors:
        b = a["bbox"]
        height, mid = b[3] - b[1], (b[0] + b[2]) / 2
        row = [
            n
            for n in anchors
            if n["page"] == a["page"] and abs(n["bbox"][1] - b[1]) < height
        ]
        left = max(
            [(n["bbox"][0] + n["bbox"][2]) / 2 for n in row if n["bbox"][2] < b[0]],
            default=0,
        )
        right = min(
            [(n["bbox"][0] + n["bbox"][2]) / 2 for n in row if n["bbox"][0] > b[2]],
            default=width,
        )
        bottom = min(
            [
                n["bbox"][1]
                for n in anchors
                if n["page"] == a["page"] and n["bbox"][1] > b[3]
            ],
            default=float("inf"),
        )
        cells.append(
            {
                **a,
                "cell": [
                    (left + mid) / 2 if left else 0,
                    b[1],
                    (right + mid) / 2 if right != width else width,
                    bottom,
                ],
            }
        )
    return cells


def owner(box, cells, page):
    candidates = [
        a
        for a in cells
        if a["page"] == page
        and a["cell"][0] <= box[0] <= box[2] <= a["cell"][2]
        and a["bbox"][3] <= box[1] < box[3] < a["cell"][3]
    ]
    if len(candidates) == 1:
        return candidates[0]
    # Unequal native shapes can extend slightly beyond centre midpoints. A
    # distinct source object must cover exactly one label's horizontal centre,
    # remain in that row and stay within a width-relative cell envelope.
    aligned = [
        a
        for a in cells
        if a["page"] == page
        and box[0] <= (a["bbox"][0] + a["bbox"][2]) / 2 <= box[2]
        and a["bbox"][3] <= box[1] < box[3] < a["cell"][3]
    ]
    if len(aligned) == 1:
        a = aligned[0]
        tolerance = (box[2] - box[0]) * 0.2
        if a["cell"][0] - tolerance <= box[0] and box[2] <= a["cell"][2] + tolerance:
            return a
    return None


def recover_centered_options(dataset, pending_questions, asset_dir, overwrite):
    with pdfium.PdfDocument(dataset["input"]["path"]) as doc:
        for q, pending in zip(dataset["questions"], pending_questions):
            cells = centered_cells(
                q,
                pending,
                dataset["pages"][q["page_reference"]["start_page"] - 1]["width"],
            )
            if not cells:
                continue
            objects = [o for o in q["images"] if not o.get("decorative")]
            assigned = {a["label"]: [] for a in cells}
            for obj in objects:
                a = owner(obj["bbox"], cells, obj["page"])
                if a:
                    assigned[a["label"]].append(obj)
            if not all(assigned.values()):
                continue
            ids = {o["image_id"] for group in assigned.values() for o in group}
            # Do not split one PDF object/crop that crosses distinct components.
            candidates = [a for a in q["visual_assets"] if set(a["object_ids"]) & ids]
            if any(set(a["object_ids"]) - ids for a in candidates):
                continue
            new = []
            for a in cells:
                native = assigned[a["label"]]
                graphic = bounds([o["bbox"] for o in native])
                # Include genuine internal/interpretive text within that choice cell.
                word_boxes = [
                    b
                    for line in pending["lines"]
                    if line["page"] == a["page"]
                    for b, t in words(line)
                    if t.strip() and owner(b, cells, a["page"]) is a
                ]
                box = bounds([graphic, a["bbox"], *word_boxes])
                prefix = f"bmat_{dataset['year']}_q{q['question_number']:03}_p{a['page']:03}_option_{a['label']}_{sha256(repr(box).encode()).hexdigest()[:10]}"
                path = (
                    Path(asset_dir)
                    / dataset["input"]["sha256"][:20]
                    / (prefix + ".png")
                )
                with (
                    closing(doc[a["page"] - 1]) as page,
                    closing(page.render(scale=2, rev_byteorder=True)) as bitmap,
                ):
                    size = _save_crop(
                        bitmap,
                        bytes(bitmap.buffer),
                        box,
                        page.get_size(),
                        path,
                        overwrite,
                    )
                new.append(
                    {
                        "image_id": prefix,
                        "path": path.relative_to(Path(asset_dir).parent).as_posix(),
                        "page": a["page"],
                        "bbox": box,
                        "graphic_bbox": graphic,
                        "asset_type": "rendered_crop",
                        "detected_types": sorted({o["kind"] for o in native}),
                        "order_key": [a["page"], box[1], box[0]],
                        "source_sha256": dataset["input"]["sha256"],
                        "source": "bmat",
                        "year": dataset["year"],
                        "question_number": q["question_number"],
                        "belongs_to": "option",
                        "option_label": a["label"],
                        "object_ids": [o["image_id"] for o in native],
                        "warnings": [],
                        "pixel_size": size,
                        "sha256": sha256(path.read_bytes()).hexdigest(),
                        "association_method": "bmat_complete_above_label_cells",
                        "placement": {"component": "option", "label": a["label"]},
                        "association_evidence": {
                            "anchor": a,
                            "native_objects_contained": True,
                            "complete_option_group": True,
                        },
                    }
                )
            q["raw"]["visual_candidates"] = deepcopy(candidates)
            for asset in new:
                a = asset["graphic_bbox"]
                for other in new:
                    b = other["graphic_bbox"]
                    if (
                        asset is not other
                        and asset["page"] == other["page"]
                        and min(a[2], b[2]) > max(a[0], b[0])
                        and min(a[3], b[3]) > max(a[1], b[1])
                    ):
                        asset["warnings"].append(
                            "visual_neighbor_boundary_uncertain:touching_native_envelopes"
                        )
            q["visual_assets"] = [
                a for a in q["visual_assets"] if a not in candidates
            ] + new
            # Keep complete alphabetic row order despite small baseline jitter.
            for i, asset in enumerate(q["visual_assets"], 1):
                asset["asset_index"] = i
            for option, a, asset in zip(q["options"], cells, new):
                option.update(
                    images=[asset.copy()],
                    warnings=[],
                    content_type="image",
                    page=a["page"],
                    label_bbox=a["bbox"],
                    association_method="bmat_complete_above_label_cells",
                )
                for obj in assigned[option["label"]]:
                    obj.update(belongs_to="option", option_label=option["label"])
            removed = {w for a in candidates for w in a["warnings"]}
            remaining = {w for a in q["visual_assets"] for w in a["warnings"]}
            q["warnings"] = [
                w
                for w in q["warnings"]
                if not (
                    w in removed - remaining
                    or w.startswith(
                        ("multi_column_options:", "incomplete_or_ambiguous_options:")
                    )
                )
            ]
            q["warnings"].extend(sorted(remaining - set(q["warnings"])))


def guard_body_boundary(question, pending):
    """Do not display unresolved image-choice geometry as established body art."""
    if not question["options"] or any(o["text"].strip() for o in question["options"]):
        return
    start = len(question["raw"]["question_block"]) - len(
        question["raw"]["options_block"]
    )
    lines = [l for l in pending["lines"] if l["block_start"] >= start]
    if not lines:
        return
    first = lines[0]
    for asset in question["visual_assets"]:
        b = asset.get("graphic_bbox", asset["bbox"])
        if asset["belongs_to"] == "question" and (
            asset["page"] > first["page"]
            or asset["page"] == first["page"]
            and b[1] >= first["top"]
        ):
            warning = "visual_component_association_uncertain:body_candidate_inside_image_answer_region"
            asset.update(
                belongs_to="unknown",
                option_label=None,
                placement={"component": "unknown", "label": None},
            )
            asset["warnings"].append(warning)
            question["warnings"].append(warning)
