"""BMAT-specific geometry evidence layered on the shared immutable crop renderer."""

import re
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from statistics import median

import pypdfium2 as pdfium

from parsers.blackstone.image_options import contains
from parsers.blackstone.visual_structure import bounds, focused_crop, words
from parsers.blackstone.visuals import _save_crop


def prose_barriers(lines, graphic):
    outside = [l for l in lines if l["bottom"] <= graphic[1] or l["top"] >= graphic[3]]
    selected = {
        id(l)
        for l in outside
        if len(l.get("readable_text", l["text"]).split()) >= 8
        and re.search(r"[a-z]{3}", l.get("readable_text", l["text"]))
        and not re.match(
            r"^(?:Figure|Fig\.|Table|Chart|Diagram)\s+\d+\b",
            l.get("readable_text", l["text"]),
            re.IGNORECASE,
        )
    }
    for _ in range(len(outside)):
        previous = len(selected)
        for line in outside:

            def indent(item):
                tokens = words(item)
                return (
                    tokens[1][0][0]
                    if len(tokens) > 1
                    and tokens[0][1].isdigit()
                    and len(tokens[0][1]) <= 2
                    else item["x0"]
                )

            if any(
                id(other) in selected
                and abs(indent(line) - indent(other)) < (line["bottom"] - line["top"])
                and 0
                <= max(line["top"] - other["bottom"], other["top"] - line["bottom"])
                < (line["bottom"] - line["top"]) * 0.8
                for other in outside
            ):
                selected.add(id(line))
        if len(selected) == previous:
            break
    return selected


def anchors_for(q, pending):
    labels = [o["label"] for o in q["options"]]
    if len(labels) < 3 or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]):
        return []
    start = len(q["raw"]["question_block"]) - len(q["raw"]["options_block"])
    anchors = []
    for line in pending["lines"]:
        if line["block_start"] < start:
            continue
        value = line.get("readable_text", line["text"]).strip()
        if re.fullmatch(r"[A-Z](?:\s+[A-Z])*", value):
            tokens = value.split()
            if tokens != labels[len(anchors) : len(anchors) + len(tokens)]:
                continue  # Repeated axis tick alphabets are not choice rows.
            for box, token in words(line):
                # A rotated axis word may extract as isolated A/D/etc. Its
                # retained word box spans the complete rotated word; it is not
                # an upright structural choice letter on this source row.
                if (
                    token in labels
                    and box[3] - box[1] <= (line["bottom"] - line["top"]) * 1.5
                ):
                    anchors.append(
                        {
                            "label": token,
                            "bbox": box,
                            "page": line["page"],
                            "label_only": True,
                        }
                    )
            if [a["label"] for a in anchors] == labels:
                return anchors
    return []


def pair_options(q, pending):
    anchors = anchors_for(q, pending)
    if not anchors:
        return {}
    assets = q["visual_assets"]
    assigned = {}
    same_column = max(a["bbox"][0] for a in anchors) - min(
        a["bbox"][0] for a in anchors
    ) < min(a["bbox"][3] - a["bbox"][1] for a in anchors)
    for a in anchors:
        b = a["bbox"]
        choices = []
        for asset in assets:
            if asset["page"] != a["page"]:
                continue
            g = asset.get("graphic_bbox", asset["bbox"])
            h = b[3] - b[1]
            internal = contains(g, b, tolerance=h * 0.15)
            left = (
                b[2] < g[0]
                and g[1] - h <= (b[1] + b[3]) / 2 <= g[3] + h
                and g[0] - b[2] < (g[2] - g[0])
            )
            above = (
                b[3] <= g[1] + h
                and g[0] <= (b[0] + b[2]) / 2 <= g[2]
                and g[1] - b[3] < h * 2
            )
            next_row = min(
                [
                    other["bbox"][1]
                    for other in anchors
                    if other["page"] == a["page"] and other["bbox"][1] > b[3]
                ],
                default=float("inf"),
            )
            complete_row = (
                same_column
                and b[1] <= g[1] < g[3] < next_row
                and abs(g[0] - b[0]) < h * 2
                and len(asset["object_ids"]) >= 2
            )
            if not (internal or left or above or complete_row):
                continue
            if any(
                other is not a
                and other["page"] == a["page"]
                and contains(g, other["bbox"], tolerance=0)
                for other in anchors
            ):
                continue
            distance = (
                max(g[0] - b[2], b[0] - g[2], 0) ** 2
                + max(g[1] - b[3], b[1] - g[3], 0) ** 2
            )
            choices.append((distance, asset))
        if not choices:
            return {}
        choices.sort(key=lambda v: v[0])
        if len(choices) > 1 and choices[0][0] == choices[1][0]:
            return {}
        assigned[a["label"]] = (a, choices[0][1])
    if len({id(asset) for _, asset in assigned.values()}) != len(anchors):
        return {}
    # Every non-anchor word in the option area must belong to a visual.
    start = len(q["raw"]["question_block"]) - len(q["raw"]["options_block"])
    owned_words = {id(asset): [] for _, asset in assigned.values()}
    for l in pending["lines"]:
        if l["block_start"] < start:
            continue
        for b, t in words(l):
            if any(a["page"] == l["page"] and a["bbox"] == b for a in anchors):
                continue
            candidates = []
            for _, asset in assigned.values():
                if asset["page"] != l["page"]:
                    continue
                g = asset.get("graphic_bbox", asset["bbox"])
                h = b[3] - b[1]
                if same_column and contains(asset["bbox"], b, tolerance=0.1):
                    candidates.append((0, asset))
                    continue
                if not g[0] - h <= b[0] <= b[2] <= g[2] + h:
                    continue
                distance = (
                    max(g[0] - b[2], b[0] - g[2], 0) ** 2
                    + max(g[1] - b[3], b[1] - g[3], 0) ** 2
                )
                if distance <= (h * 2) ** 2:
                    candidates.append((distance, asset))
            candidates.sort(key=lambda x: x[0])
            if (
                not candidates
                or len(candidates) > 1
                and candidates[0][0] == candidates[1][0]
            ):
                return {}
            owned_words[id(candidates[0][1])].append(b)
    for _, asset in assigned.values():
        asset["bmat_option_word_boxes"] = owned_words[id(asset)]
    return assigned


def save_revision(dataset, q, asset, box, doc, asset_dir):
    if box == asset["bbox"]:
        return
    q["raw"].setdefault("visual_revisions", []).append(deepcopy(asset))
    token = sha256(repr(box).encode()).hexdigest()[:10]
    name = f"bmat_{dataset['year']}_q{q['question_number']:03}_p{asset['page']:03}_geometry_{token}"
    dest = Path(asset_dir) / dataset["input"]["sha256"][:20] / (name + ".png")
    with (
        closing(doc[asset["page"] - 1]) as page,
        closing(page.render(scale=2, rev_byteorder=True)) as bitmap,
    ):
        size = _save_crop(
            bitmap, bytes(bitmap.buffer), box, page.get_size(), dest, False
        )
    asset.update(
        image_id=name,
        path=dest.relative_to(Path(asset_dir).parent).as_posix(),
        bbox=box,
        pixel_size=size,
        sha256=sha256(dest.read_bytes()).hexdigest(),
    )


def reunite_swatch_legends(dataset, records, asset_dir):
    """Join a detached, repeated two-swatch legend to its single adjacent graph.

    Native swatch shape/scale, repeated alignment, chart complexity and a
    prose-free source gap are all required. General nearby figures are not
    merged, and source candidates/assets remain immutable.
    """
    with pdfium.PdfDocument(dataset["input"]["path"]) as doc:
        for q, pending in zip(dataset["questions"], records):
            bodies = [a for a in q["visual_assets"] if a["belongs_to"] == "question"]
            for legend in list(bodies):
                native = [
                    o for o in q["images"] if o["image_id"] in legend["object_ids"]
                ]
                if len(native) != 2 or not all(
                    o["object_type"] == "rect" for o in native
                ):
                    continue
                a, b = [o["bbox"] for o in native]
                size = max(a[2] - a[0], a[3] - a[1])
                if not (
                    0.65 < (a[2] - a[0]) / max(a[3] - a[1], 0.01) < 1.5
                    and abs(a[0] - b[0]) < size * 0.2
                    and abs((a[2] - a[0]) - (b[2] - b[0])) < size * 0.2
                    and size < abs(a[1] - b[1]) < size * 5
                ):
                    continue
                lg = legend.get("graphic_bbox", legend["bbox"])
                candidates = []
                for graph in bodies:
                    g = graph.get("graphic_bbox", graph["bbox"])
                    if (
                        graph is legend
                        or graph["page"] != legend["page"]
                        or len(graph["object_ids"]) < 15
                    ):
                        continue
                    if not (
                        g[2] <= lg[0] <= g[2] + (g[2] - g[0]) * 0.4
                        and g[1] < lg[1] < lg[3] < g[3]
                        and lg[3] - lg[1] < (g[3] - g[1]) * 0.4
                    ):
                        continue
                    gap = [
                        l
                        for l in pending["lines"]
                        if l["page"] == legend["page"]
                        and g[2] < l["x0"] < lg[0]
                        and l["bottom"] > lg[1]
                        and l["top"] < lg[3]
                    ]
                    if any(len(l["text"].split()) > 4 for l in gap):
                        continue
                    candidates.append(graph)
                if len(candidates) != 1:
                    continue
                graph = candidates[0]
                q["raw"].setdefault("legend_component_candidates", []).extend(
                    deepcopy([graph, legend])
                )
                box = bounds([graph["bbox"], legend["bbox"]])
                save_revision(dataset, q, graph, box, doc, asset_dir)
                graph["object_ids"] += legend["object_ids"]
                graph["bmat_legend_evidence"] = {
                    "swatches": [a, b],
                    "method": "repeated_rectangular_swatches_adjacent_to_unique_graph",
                }
                # Geometry union includes the legend, while the chart's native
                # bounds continue to identify its axes rather than a second graph.
                q["visual_assets"].remove(legend)
                bodies.remove(legend)
            for i, asset in enumerate(q["visual_assets"], 1):
                asset["asset_index"] = i


def revise_visuals(dataset, records, asset_dir):
    """Recompute crops against paragraph barriers, then bind complete choice sets."""
    with pdfium.PdfDocument(dataset["input"]["path"]) as doc:
        for q, pending in zip(dataset["questions"], records):
            old_warnings = {
                w for a in q["visual_assets"] for w in a.get("warnings", [])
            }
            for asset in q["visual_assets"]:
                if not any(
                    w.startswith(
                        ("visual_caption_", "visual_crop_contains_unrelated_text:")
                    )
                    for w in asset["warnings"]
                ):
                    continue
                page = dataset["pages"][asset["page"] - 1]
                graphic = asset.get("graphic_bbox", asset["bbox"])
                ls = [l for l in pending["lines"] if l["page"] == asset["page"]]
                barriers = prose_barriers(ls, graphic)
                filtered = [l for l in ls if id(l) not in barriers]
                group = {"bbox": graphic, "graph": asset.get("visual_kind") == "graph"}
                neighbors = [
                    {"bbox": a.get("graphic_bbox", a["bbox"])}
                    for a in q["visual_assets"]
                    if a["page"] == asset["page"]
                ]
                box, evidence = focused_crop(
                    group,
                    filtered,
                    asset["page"],
                    page["width"],
                    page["height"],
                    neighbors,
                )
                # Paragraphs are barriers, including short wrapped tails.
                for line in ls:
                    if id(line) not in barriers:
                        continue
                    if line["bottom"] <= graphic[1]:
                        box[1] = max(box[1], min(graphic[1], line["bottom"] + 1))
                    if line["top"] >= graphic[3]:
                        box[3] = min(box[3], max(graphic[3], line["top"] - 1))
                if box[0] < box[2] and box[1] < box[3]:
                    save_revision(dataset, q, asset, box, doc, asset_dir)
                    replace = (
                        "visual_caption_",
                        "visual_crop_contains_unrelated_text:",
                        "visual_neighbor_boundary_uncertain:content_bounds_overlap",
                    )
                    asset["warnings"] = [
                        w for w in asset["warnings"] if not w.startswith(replace)
                    ] + evidence["warnings"]
                    asset["bmat_crop_evidence"] = {
                        **evidence,
                        "paragraph_barrier_spans": [
                            {
                                "start": l["block_start"],
                                "end": l["block_start"] + len(l["text"]),
                            }
                            for l in ls
                            if id(l) in barriers
                        ],
                    }
            pairs = pair_options(q, pending)
            if pairs:
                q["raw"].setdefault(
                    "option_component_candidates", deepcopy(q["options"])
                )
                for option in q["options"]:
                    a, asset = pairs[option["label"]]
                    box = bounds(
                        [
                            asset["bbox"],
                            a["bbox"],
                            *asset.get("bmat_option_word_boxes", []),
                        ]
                    )
                    # Keep the option letter in the RAW crop, with no foreign letter.
                    if any(
                        other[0] is not a
                        and other[0]["page"] == a["page"]
                        and contains(box, other[0]["bbox"])
                        for other in pairs.values()
                    ):
                        raise ValueError("Ambiguous foreign option label")
                    save_revision(dataset, q, asset, box, doc, asset_dir)
                    asset.update(
                        belongs_to="option",
                        option_label=option["label"],
                        association_method="bmat_complete_anchor_envelopes",
                        placement={"component": "option", "label": option["label"]},
                        association_evidence={
                            "anchor": a,
                            "complete_option_group": True,
                        },
                    )
                    asset["warnings"] = [
                        w
                        for w in asset["warnings"]
                        if not w.startswith(
                            (
                                "visual_multiple_option_images_merged:",
                                "visual_component_association_uncertain",
                                "visual_option_anchor_boundary_uncertain:",
                                "visual_option_anchor_not_left_of_image:",
                            )
                        )
                    ]
                    option.update(
                        text="",
                        images=[asset.copy()],
                        warnings=[],
                        content_type="image",
                        page=a["page"],
                        label_bbox=a["bbox"],
                        association_method=asset["association_method"],
                    )
                q["warnings"] = [
                    w
                    for w in q["warnings"]
                    if not w.startswith(
                        ("multi_column_options:", "incomplete_or_ambiguous_options:")
                    )
                ]
            remaining = {w for a in q["visual_assets"] for w in a["warnings"]}
            q["warnings"] = [
                w for w in q["warnings"] if w not in old_warnings - remaining
            ]
            q["warnings"].extend(sorted(remaining - set(q["warnings"])))
            for option in q["options"]:
                option["images"] = [
                    a.copy()
                    for a in q["visual_assets"]
                    if a.get("option_label") == option["label"]
                    and a["belongs_to"] == "option"
                ]


def project_visual_text(q, pending, excluded=None):
    """Remove only fully owned exact source rows from the textual projection."""
    original = q["question_text"]
    block = q["raw"]["question_block"]
    end = len(block) - len(q["raw"]["options_block"])
    first = pending["lines"][0]
    from .parser import marker

    begin = first["block_start"] + marker(first, "number")[1]
    spans = []
    for line in pending["lines"]:
        if not begin <= line["block_start"] < end:
            continue
        tokens = words(line)
        if not tokens:
            continue
        covering = []
        for box, _ in tokens:
            owners = [
                a["image_id"]
                for a in q["visual_assets"]
                if a["page"] == line["page"]
                and contains(a["bbox"], box, tolerance=0.1)
                and (
                    a["belongs_to"] == "option"
                    or (
                        a.get("graphic_bbox", a["bbox"])[3]
                        - a.get("graphic_bbox", a["bbox"])[1]
                    )
                    > (line["bottom"] - line["top"]) * 2
                )
            ]
            if not owners:
                break
            covering.extend(owners)
        else:
            spans.append(
                {
                    "start": line["block_start"],
                    "end": line["block_start"] + len(line["text"]),
                    "asset_ids": list(dict.fromkeys(covering)),
                    "page": line["page"],
                }
            )
    q["raw"]["visual_text_exclusions"] = spans
    from .encoding import decode_block
    from .parser import ADMIN

    context = list(pending["lines"])
    offset = 0
    for segment in pending["segments"]:
        for l in (excluded or {}).get(segment["page"], []):
            a = offset + l["start"] - segment["start"]
            if 0 <= a and a + len(l["text"]) <= len(block):
                context.append({**l, "block_start": a})
        offset += len(segment["text"]) + 1
    admin = []
    pending_starts = {l["block_start"] for l in pending["lines"]}
    for line in context:
        if line["block_start"] not in pending_starts:
            admin.append(
                {
                    "start": line["block_start"],
                    "end": line["block_start"] + len(line["text"]),
                    "reason": "verified_page_administration",
                }
            )
    for m in re.finditer(r"(?m)^.*$", block):
        if ADMIN.match(decode_block(m[0], context).strip()):
            admin.append(
                {
                    "start": m.start(),
                    "end": m.end(),
                    "reason": "structural_source_marker",
                }
            )
    q["raw"]["structural_exclusions"] = admin
    intervals = [*spans, *admin]
    pieces = []
    cursor = begin
    for span in sorted(intervals, key=lambda s: s["start"]):
        a, b = span["start"], span["end"]
        if a < begin or b > end:
            continue
        pieces.append(block[cursor:a])
        cursor = max(cursor, b)
    pieces.append(block[cursor:end])
    q["question_text"] = decode_block("".join(pieces), context)
    if intervals:
        q["raw"].setdefault("visual_text_candidate", original)
    for option in q["options"]:
        if option.get("content_type") == "image":
            continue
        source = decode_block(option["text"], context)
        # Admin markers are whole structural source lines, never prose tokens.
        option["text"] = "\n".join(
            t for t in source.split("\n") if not ADMIN.match(t.strip())
        )


def recover_oriented_labels(dataset, records, asset_dir):
    """Bind transformed axis text through the PDF matrix and nearest graphic."""
    with pdfium.PdfDocument(dataset["input"]["path"]) as doc:
        for q, pending in zip(dataset["questions"], records):
            for asset in q["visual_assets"]:
                if asset["belongs_to"] != "question":
                    continue
                g = asset.get("graphic_bbox", asset["bbox"])
                if g[2] - g[0] < 50 or g[3] - g[1] < 30:
                    continue
                runs = []
                for line in pending["lines"]:
                    if line["page"] != asset["page"]:
                        continue
                    for run in line.get("oriented_runs", []):
                        b = run["bbox"]
                        if (
                            not run.get("vertical")
                            or not g[1] <= (b[1] + b[3]) / 2 <= g[3]
                        ):
                            continue
                        gap = max(g[0] - b[2], b[0] - g[2], 0)
                        if gap > min((g[2] - g[0]) * 0.2, (g[3] - g[1]) * 0.35):
                            continue
                        if any(
                            a is not asset
                            and a["page"] == asset["page"]
                            and contains(a["bbox"], b)
                            for a in q["visual_assets"]
                        ):
                            continue

                        def distance(c, b=b):
                            return (
                                max(c[0] - b[2], b[0] - c[2], 0) ** 2
                                + max(c[1] - b[3], b[1] - c[3], 0) ** 2
                            )

                        if any(
                            a is not asset
                            and a["page"] == asset["page"]
                            and distance(a.get("graphic_bbox", a["bbox"])) < distance(g)
                            for a in q["visual_assets"]
                        ):
                            continue
                        runs.append(b)
                if not runs:
                    continue
                boxes = [asset["bbox"], *runs]
                for line in pending["lines"]:
                    if line["page"] != asset["page"]:
                        continue
                    value = line.get("readable_text", line["text"]).strip()
                    if (
                        len(value.split()) > 4
                        or not re.search(r"[a-zA-Z]", value)
                        or "?" in value
                        or re.match(r"^(?:Which|What|How|If|The|This|A|An)\b", value)
                    ):
                        continue
                    h = line["bottom"] - line["top"]
                    mid = (line["x0"] + line["x1"]) / 2
                    if (
                        g[0] <= mid <= g[2]
                        and 0 <= line["top"] - g[3] <= h * 3
                        and ("(" in value or asset.get("visual_kind") == "graph")
                    ):
                        boxes.append(
                            [line["x0"], line["top"], line["x1"], line["bottom"]]
                        )
                box = bounds(boxes)
                if box != asset["bbox"]:
                    save_revision(dataset, q, asset, box, doc, asset_dir)
                    asset["bmat_oriented_label_evidence"] = {
                        "method": "pdf_text_matrix_and_nearest_graphic",
                        "label_bounds": runs,
                    }


def mark_trailing_rules(dataset, records):
    """Page control separators below all question text are not illustrations."""
    for q, pending in zip(dataset["questions"], records):
        at_section_end = q["question_number"] == dataset["extraction"].get(
            "expected_questions"
        ) or any(
            r["end_question"] == q["question_number"]
            for r in dataset["shared_information_ranges"]
        )
        for obj in q["images"]:
            page = dataset["pages"][obj["page"] - 1]
            b = obj["bbox"]
            ls = [
                l
                for l in pending["lines"]
                if l["page"] == obj["page"]
                and l.get("readable_text", l["text"]).strip()
            ]
            if not ls:
                continue
            height = median(l["bottom"] - l["top"] for l in ls)
            minimum_width = page["width"] * (0.4 if at_section_end else 0.5)
            if (
                b[2] - b[0] < minimum_width
                or b[3] - b[1] > height * 0.08
                or b[1] <= max(l["bottom"] for l in ls) + height
            ):
                continue
            if any(
                o is not obj
                and not o.get("decorative")
                and o["page"] == obj["page"]
                and abs(o["bbox"][3] - b[1]) < height * 2
                and not (
                    o["bbox"][2] - o["bbox"][0] >= minimum_width
                    and o["bbox"][3] - o["bbox"][1] <= height * 0.08
                    and o["bbox"][1] > max(l["bottom"] for l in ls) + height
                )
                for o in q["images"]
            ):
                continue
            obj.update(decorative=True)
            obj["notes"].append(
                "BMAT trailing page-control rule: thin wide (possibly multi-stroke) separator after all visible question/choice text, with section-end context for shorter rules and no neighboring non-rule graphic."
            )


def recover_math_options(dataset, records, asset_dir):
    """Preserve undecodable spatial math as complete option visuals, not fake text."""
    with pdfium.PdfDocument(dataset["input"]["path"]) as doc:
        for q, pending in zip(dataset["questions"], records):
            if not any("(cid:" in o["text"] for o in q["options"]):
                continue
            anchors = []
            for l in pending["lines"]:
                ts = words(l)
                if (
                    ts
                    and ts[0][1] in [o["label"] for o in q["options"]]
                    and all(
                        re.fullmatch(r"(?:\(cid:\d+\)|[\d.%+−*/= -])+", t)
                        for _, t in ts[1:]
                    )
                ):
                    anchors.append(
                        {"label": ts[0][1], "bbox": ts[0][0], "page": l["page"]}
                    )
            if (
                len(anchors) < 3
                or [a["label"] for a in anchors] != [o["label"] for o in q["options"]]
                or len({a["page"] for a in anchors}) != 1
            ):
                continue
            if (
                max(a["bbox"][0] for a in anchors) - min(a["bbox"][0] for a in anchors)
                > anchors[0]["bbox"][3] - anchors[0]["bbox"][1]
            ):
                continue
            grouped = {a["label"]: [] for a in anchors}
            height = anchors[0]["bbox"][3] - anchors[0]["bbox"][1]
            for l in pending["lines"]:
                if l["page"] != anchors[0]["page"]:
                    continue
                for b, t in words(l):
                    if (
                        b[1] < anchors[0]["bbox"][1] - height
                        or b[0] <= anchors[0]["bbox"][2]
                    ):
                        continue
                    a = min(
                        anchors,
                        key=lambda a: abs(
                            (a["bbox"][1] + a["bbox"][3] - b[1] - b[3]) / 2
                        ),
                    )
                    if re.fullmatch(r"(?:\(cid:\d+\)|[\d.%+−*/= -])+", t):
                        grouped[a["label"]].append(b)
            if not all(grouped.values()):
                continue
            q["raw"]["math_option_candidates"] = deepcopy(q["options"])
            # Include fraction numerators before the first label and denominators.
            boxes = [bounds([a["bbox"], *grouped[a["label"]]]) for a in anchors]
            replaced = [
                a
                for a in q["visual_assets"]
                if any(
                    a["page"] == anchors[0]["page"]
                    and contains(b, a.get("graphic_bbox", a["bbox"]), tolerance=1)
                    for b in boxes
                )
            ]
            q["raw"].setdefault("visual_revisions", []).extend(deepcopy(replaced))
            q["visual_assets"] = [a for a in q["visual_assets"] if a not in replaced]
            removed = {w for a in replaced for w in a["warnings"]}
            for option, a, b in zip(q["options"], anchors, boxes):
                native = [
                    o
                    for o in q["images"]
                    if o["page"] == a["page"]
                    and not o.get("decorative")
                    and contains(b, o["bbox"], tolerance=1)
                ]
                seed = {
                    "image_id": "math",
                    "bbox": [0, 0, 1, 1],
                    "page": a["page"],
                    "warnings": [],
                    "object_ids": [o["image_id"] for o in native],
                    "source_sha256": dataset["input"]["sha256"],
                    "source": "bmat",
                    "year": dataset["year"],
                    "question_number": q["question_number"],
                    "asset_type": "rendered_crop",
                    "detected_types": ["spatial_math_text"],
                    "belongs_to": "option",
                    "option_label": a["label"],
                    "association_method": "bmat_spatial_math_option_cells",
                    "placement": {"component": "option", "label": a["label"]},
                }
                save_revision(
                    dataset,
                    q,
                    seed,
                    [b[0] - 1, b[1] - 1, b[2] + 1, b[3] + 1],
                    doc,
                    asset_dir,
                )
                seed["graphic_bbox"] = b
                q["visual_assets"].append(seed)
                seed["asset_index"] = len(q["visual_assets"])
                seed["order_key"] = [a["page"], b[1], b[0]]
                for obj in native:
                    obj.update(
                        path=seed["path"], belongs_to="option", option_label=a["label"]
                    )
                option.update(
                    text="",
                    images=[seed.copy()],
                    warnings=[],
                    content_type="image",
                    page=a["page"],
                    label_bbox=a["bbox"],
                    association_method=seed["association_method"],
                )
            q["warnings"] = [w for w in q["warnings"] if w not in removed]
            # Extend structural answer start to the first fraction's numerator.
            start = min(
                l["block_start"]
                for l in pending["lines"]
                if l["page"] == anchors[0]["page"] and l["top"] >= boxes[0][1] - 0.1
            )
            q["raw"]["options_block"] = q["raw"]["question_block"][start:]
