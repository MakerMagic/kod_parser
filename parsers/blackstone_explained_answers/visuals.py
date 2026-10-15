"""Question-owned raster/vector explanation regions and complete source previews."""

from hashlib import sha256

import pypdfium2 as pdfium

from parsers.blackstone.visuals import _save_crop

from .structure import reference


def contains(outer, inner):
    return all(
        (
            outer[0] <= inner[0],
            outer[1] <= inner[1],
            outer[2] >= inner[2],
            outer[3] >= inner[3],
        )
    )


def overlaps(a, b, gap=0):
    return (
        a[0] <= b[2] + gap
        and b[0] <= a[2] + gap
        and a[1] <= b[3] + gap
        and b[1] <= a[3] + gap
    )


def union(boxes):
    return [
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    ]


def objects_on_page(page):
    result = []
    for kind, objects in (
        ("raster_image", page.images),
        ("line", page.lines),
        ("rectangle", page.rects),
        ("curve", page.curves),
    ):
        for index, obj in enumerate(objects):
            box = [obj["x0"], obj["top"], obj["x1"], obj["bottom"]]
            # Page backgrounds and white masks are not explanatory graphics.
            if kind != "raster_image":
                color = obj.get("non_stroking_color")
                white = (
                    color == 1
                    or isinstance(color, (tuple, list))
                    and color
                    and all(v == 1 for v in color)
                )
                if obj.get("fill") and white:
                    continue
                if (box[2] - box[0]) * (
                    box[3] - box[1]
                ) > page.width * page.height * 0.85:
                    continue
            result.append(
                {
                    "object_id": f"p{page.page_number}_{kind}_{index}",
                    "kind": kind,
                    "bbox": box,
                }
            )
    return result


def visual_groups(objects, scale):
    groups = [[obj] for obj in objects]
    changed = True
    while changed:
        changed = False
        for i, group in enumerate(groups):
            box = union([o["bbox"] for o in group])
            for j in range(i + 1, len(groups)):
                other = groups[j]
                # Separate raster objects remain separate unless they overlap.
                raster = any(o["kind"] == "raster_image" for o in [*group, *other])
                if overlaps(
                    box, union([o["bbox"] for o in other]), 0 if raster else scale * 0.5
                ):
                    groups[i] += groups.pop(j)
                    changed = True
                    break
            if changed:
                break
    return [
        g
        for g in groups
        if any(o["kind"] == "raster_image" for o in g)
        or len(g) >= 2
        and (union([o["bbox"] for o in g])[2] - union([o["bbox"] for o in g])[0])
        > scale
        and (union([o["bbox"] for o in g])[3] - union([o["bbox"] for o in g])[1])
        > scale
        or any(
            o["kind"] in {"rectangle", "curve"}
            and o["bbox"][2] - o["bbox"][0] > scale * 2
            and o["bbox"][3] - o["bbox"][1] > scale * 2
            for o in g
        )
    ]


def attach_visuals(answer, lines, pages, project):
    assets = []
    for segment in answer["raw"]["page_spans"]:
        page = pages[segment["page"] - 1]
        header_refs = [
            r for r in answer["raw"]["header_line_refs"] if r["page"] == page["page"]
        ]
        region = segment["bbox"][:]
        if header_refs:
            region[1] = max(ref["bbox"][3] for ref in header_refs)
        page_lines = [line for line in lines if line["page"] == page["page"]]
        scale = min(
            (line["bbox"][3] - line["bbox"][1] for line in page_lines), default=11
        )
        objects = [obj for obj in page["objects"] if contains(region, obj["bbox"])]
        for group in visual_groups(objects, scale):
            box = union([obj["bbox"] for obj in group])
            raster = any(obj["kind"] == "raster_image" for obj in group)
            # Closed grids retain contained cell text. Short detached labels are
            # included conservatively for vector regions, with explicit review.
            extra = (
                [
                    line
                    for line in page_lines
                    if not contains(box, line["bbox"])
                    and overlaps(box, line["bbox"], scale * 0.5)
                    and len(line["text"]) <= 45
                ]
                if not raster
                else []
            )
            if extra:
                box = union([box, *[line["bbox"] for line in extra]])
                answer["warnings"].append(
                    "explanation_visual_crop_uncertain:nearby_vector_labels_included_conservatively"
                )
            pad = max(scale * 0.15, 0.5)
            crop = [
                max(region[0], box[0] - pad),
                max(region[1], box[1] - pad),
                min(region[2], box[2] + pad),
                min(region[3], box[3] + pad),
            ]
            assets.append(
                {
                    "page": page["page"],
                    "bbox": crop,
                    "graphic_bbox": box,
                    "asset_type": "rendered_crop",
                    "detected_types": sorted({obj["kind"] for obj in group}),
                    "object_ids": [obj["object_id"] for obj in group],
                    "year": answer["year"],
                    "question_number": answer["question_number"],
                    "source_pdf": answer["source_document"]["path"],
                    "source_sha256": answer["source_document"]["sha256"],
                    "path": None,
                    "warnings": [],
                }
            )
    assets.sort(key=lambda asset: (asset["page"], asset["bbox"][1], asset["bbox"][0]))
    for index, asset in enumerate(assets, 1):
        asset["asset_index"] = index
        asset["asset_id"] = f"{answer['answer_id']}_visual_{index}"
    owned = {}
    for line in lines:
        candidates = [
            a
            for a in assets
            if a["page"] == line["page"] and contains(a["bbox"], line["bbox"])
        ]
        if len(candidates) == 1:
            owned[(line["page"], line["line_id"])] = candidates[0]["asset_index"]
        elif len(candidates) > 1:
            answer["warnings"].append(
                "explanation_visual_association_uncertain:overlapping_visual_text"
            )
    events = [
        ((line["page"], line["bbox"][1], line["bbox"][0]), "text", line)
        for line in lines
        if (line["page"], line["line_id"]) not in owned
    ]
    events += [((a["page"], a["bbox"][1], a["bbox"][0]), "visual", a) for a in assets]
    events.sort(key=lambda e: e[0])
    explanation, _ = project([], answer["correct_answer"])
    pending = []

    def flush():
        projected, warnings = project(pending, answer["correct_answer"])
        offset = len(explanation["blocks"])
        for item in projected["choice_analysis"]:
            item["list_order"] += offset
        explanation["choice_analysis"].extend(projected["choice_analysis"])
        explanation["blocks"].extend(projected["blocks"])
        answer["warnings"].extend(warnings)
        pending.clear()

    for _, kind, value in events:
        if kind == "text":
            pending.append(value)
        else:
            flush()
            refs = [
                reference(line)
                for line in lines
                if owned.get((line["page"], line["line_id"])) == value["asset_index"]
            ]
            explanation["blocks"].append(
                {
                    "type": "visual",
                    "role": "explanation_visual",
                    "asset_index": value["asset_index"],
                    "page": value["page"],
                    "bbox": value["bbox"],
                    "line_refs": refs,
                }
            )
    flush()
    for index, block in enumerate(explanation["blocks"], 1):
        block["order"] = index
    explanation["paragraphs"] = [
        b
        for b in explanation["blocks"]
        if b["type"] == "paragraph" and b["role"] == "main"
    ]
    explanation["main_explanation"] = "\n\n".join(
        b["text"] for b in explanation["paragraphs"]
    )
    explanation["bulleted_blocks"] = [
        b for b in explanation["blocks"] if b["type"] == "list"
    ]
    explanation["other_lists"] = [
        b
        for b in explanation["bulleted_blocks"]
        if not b["role"].startswith("incorrect_choices")
    ]
    explanation["visual_assets"] = assets
    answer["explanation"] = explanation


def save_visuals(data, source, asset_dir, *, overwrite):
    folder = asset_dir / data["source_document"]["sha256"][:20]
    folder.mkdir(parents=True, exist_ok=True)
    claimed = {
        oid
        for answer in data["answers"]
        for asset in answer["explanation"]["visual_assets"]
        for oid in asset["object_ids"]
    }
    unassigned = []
    for page in data["pages"]:
        if page.get("section") != "section_1":
            continue
        remaining = [
            obj
            for obj in page["objects"]
            if obj["object_id"] not in claimed
            and obj["bbox"][1] > page["content_top"] + 2
        ]
        for group in visual_groups(remaining, 11):
            region = {
                "page": page["page"],
                "bbox": union([obj["bbox"] for obj in group]),
                "year": data["answers"][0]["year"],
                "question_number": None,
                "object_ids": [obj["object_id"] for obj in group],
                "detected_types": sorted({obj["kind"] for obj in group}),
                "asset_index": len(unassigned) + 1,
                "asset_type": "rendered_crop",
                "source_pdf": str(source),
                "source_sha256": data["source_document"]["sha256"],
                "path": None,
                "warnings": [
                    "explanation_visual_association_uncertain:no_question_owner"
                ],
            }
            unassigned.append(region)
            data["issues"].append(
                {
                    "code": "explanation_visual_unassigned",
                    "year": data["answers"][0]["year"],
                    "section": "section_1",
                    "reason": "Detected visual crosses question ownership bounds or has no supported owner; PDF objects retained",
                    "page": page["page"],
                    "bbox": union([obj["bbox"] for obj in group]),
                    "object_ids": [obj["object_id"] for obj in group],
                    "visual_asset": region,
                }
            )
    requests = {}
    for region in unassigned:
        requests.setdefault(region["page"], []).append((None, region, "unassigned"))
    for answer in data["answers"]:
        for segment in answer["raw"]["page_spans"]:
            requests.setdefault(segment["page"], []).append(
                (answer, segment, "preview")
            )
        for asset in answer["explanation"]["visual_assets"]:
            requests.setdefault(asset["page"], []).append((answer, asset, "visual"))
    with pdfium.PdfDocument(str(source)) as doc:
        for number, entries in requests.items():
            page = doc[number - 1]
            bitmap = page.render(scale=2, rev_byteorder=True)
            try:
                pixels, size = (
                    bytes(bitmap.buffer),
                    [page.get_width(), page.get_height()],
                )
                for answer, region, kind in entries:
                    shape = sha256(repr(region["bbox"]).encode()).hexdigest()[:10]
                    suffix = (
                        f"visual_{region['asset_index']:02}"
                        if kind != "preview"
                        else "preview"
                    )
                    identity = (
                        answer["answer_id"]
                        if answer
                        else f"{region['year']}_unassigned"
                    )
                    target = folder / f"{identity}_p{number:03}_{suffix}_{shape}.png"
                    try:
                        dimensions = _save_crop(
                            bitmap, pixels, region["bbox"], size, target, overwrite
                        )
                        saved = {
                            "path": target.relative_to(asset_dir.parent).as_posix(),
                            "sha256": sha256(target.read_bytes()).hexdigest(),
                            "pixel_size": dimensions,
                        }
                        if kind != "preview":
                            region.update(saved)
                        else:
                            answer["visual_previews"].append(
                                {"page": number, "bbox": region["bbox"], **saved}
                            )
                    except (OSError, ValueError) as error:
                        warning = f"explanation_{kind}_not_saved:{error}"
                        if answer:
                            answer["warnings"].append(warning)
                        if kind != "preview":
                            region["warnings"].append(warning)
            finally:
                bitmap.close()
                page.close()
    for answer in data["answers"]:
        if not answer["explanation"]["blocks"]:
            answer["warnings"].append(
                "explanation_text_unavailable:no_explanation_content_detected"
            )
