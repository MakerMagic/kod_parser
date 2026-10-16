"""Conservative structural proofs for disconnected body-visual components.

Do not enlarge the generic proximity radius: separately labelled choices and
unrelated diagrams can be closer than parts of one drawing. These proofs apply
only before the answer region, and keep ambiguous candidates separate.
"""

import re
from bisect import bisect_right
from itertools import pairwise
from statistics import mean, median

from .visual_structure import bounds, intersects, words

MEASUREMENT = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:mm|cm|km|m|ft|in|feet|inches)", re.IGNORECASE
)


def _box(line):
    return [line["x0"], line["top"], line["x1"], line["bottom"]]


def _contained(inner, outer, tolerance=0):
    return all(
        (
            inner[i] >= outer[i] - tolerance
            if i < 2
            else inner[i] <= outer[i] + tolerance
        )
        for i in range(4)
    )


def _text(line):
    return line.get("readable_text", line["text"])


def _prose(line):
    return len(_text(line).split()) >= 6


def _merge(groups, members, note):
    merged = {
        "bbox": bounds([g["bbox"] for g in members]),
        "objects": [obj for g in members for obj in g["objects"]],
        "grouping_notes": [
            note,
            *[n for g in members for n in g.get("grouping_notes", [])],
        ],
        "grouping_warnings": [
            w for g in members for w in g.get("grouping_warnings", [])
        ],
    }
    ids = {id(g) for g in members}
    return [g for g in groups if id(g) not in ids] + [merged]


def _levels(values, tolerance):
    clusters = []
    for value in sorted(values):
        if not clusters or value - mean(clusters[-1]) > tolerance:
            clusters.append([])
        clusters[-1].append(value)
    return [mean(c) for c in clusters]


def _regular(levels, size):
    gaps = [b - a for a, b in pairwise(levels)]
    return len(levels) >= 3 and min(gaps) >= 3 * size and max(gaps) <= 1.2 * min(gaps)


def _point_lattices(groups, lines):
    # Duplicate fill/stroke objects occupy the same cell; count geometry, not
    # PDF object count. A complete lattice alone is insufficient: it also needs
    # one internal centre label and a local measurement, without prose/anchors.
    points = []
    for group in groups:
        for obj in group["objects"]:
            b = obj["bbox"]
            w, h = b[2] - b[0], b[3] - b[1]
            if obj["object_type"] == "curve" and w > 0 and 0.85 <= h / w <= 1.15:
                points.append((obj, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, (w + h) / 2))
    barriers = sorted(line["top"] for line in lines if _prose(line))
    bands = {}
    for point in points:
        bands.setdefault(bisect_right(barriers, point[2]), []).append(point)
    for band in bands.values():
        sizes = []
        for point in sorted(band, key=lambda p: p[3]):
            if not sizes or point[3] > median(p[3] for p in sizes[-1]) * 1.2:
                sizes.append([])
            sizes[-1].append(point)
        for points in sizes:
            if len(points) < 9:
                continue
            size = median(p[3] for p in points)
            xs, ys = (_levels([p[axis] for p in points], size * 0.3) for axis in (1, 2))
            if not (_regular(xs, size) and _regular(ys, size)):
                continue
            cells = {
                (
                    min(range(len(xs)), key=lambda i: abs(xs[i] - p[1])),
                    min(range(len(ys)), key=lambda i: abs(ys[i] - p[2])),
                )
                for p in points
            }
            if len(cells) != len(xs) * len(ys):
                continue
            region = bounds([p[0]["bbox"] for p in points])
            centres = [
                box
                for line in lines
                for box, token in words(line)
                if token.lower().strip(".:;") in ("centre", "center")
                and _contained(box, region)
            ]
            measurements = [
                line
                for line in lines
                if MEASUREMENT.fullmatch(_text(line).strip())
                and _contained(
                    _box(line),
                    [
                        region[0] - size * 5,
                        region[1] - size * 5,
                        region[2] + size * 5,
                        region[3] + size * 5,
                    ],
                )
            ]
            if (
                len(centres) != 1
                or not measurements
                or any(_prose(l) and intersects(_box(l), region) for l in lines)
            ):
                continue
            members = [g for g in groups if _contained(g["bbox"], region, size * 0.3)]
            member_ids = {obj["image_id"] for g in members for obj in g["objects"]}
            if len(members) < 2 or not all(
                p[0]["image_id"] in member_ids for p in points
            ):
                continue
            # Never absorb a fragment of a larger/crossing drawing.
            if any(g not in members and intersects(g["bbox"], region) for g in groups):
                continue
            groups = _merge(
                groups,
                members,
                f"Complete {len(xs)}x{len(ys)} point lattice with one centre and measurement labels; prose-separated body region.",
            )
    return groups


def _dimension_axis(group):
    b = group["bbox"]
    w, h = b[2] - b[0], b[3] - b[1]
    if min(w, h) <= 0 or max(w, h) < 8 * min(w, h):
        return None
    axis = 1 if h > w else 0
    length, thickness = b[axis + 2] - b[axis], b[3 - axis] - b[1 - axis]
    shafts = [
        o
        for o in group["objects"]
        if o["object_type"] == "line"
        and o["bbox"][axis + 2] - o["bbox"][axis] > length * 0.75
        and o["bbox"][3 - axis] - o["bbox"][1 - axis] < thickness * 0.2
    ]
    heads = [
        o
        for o in group["objects"]
        if o["object_type"] == "curve"
        and max(o["bbox"][2] - o["bbox"][0], o["bbox"][3] - o["bbox"][1])
        <= thickness * 1.5
    ]
    if len(shafts) != 1 or len(heads) != 2 or len(group["objects"]) != 3:
        return None
    shaft = shafts[0]["bbox"]
    centre = (shaft[1 - axis] + shaft[3 - axis]) / 2
    if not all(o["bbox"][1 - axis] <= centre <= o["bbox"][3 - axis] for o in heads):
        return None
    if not all(
        any(
            o["bbox"][axis] - thickness <= shaft[end] <= o["bbox"][axis + 2] + thickness
            for o in heads
        )
        for end in (axis, axis + 2)
    ):
        return None
    return axis, thickness


def group_body_components(groups, lines, page, anchors):
    """Merge only proven body lattices or uniquely owned dimension annotations."""
    choices = [a for a in anchors if a["page"] == page]
    if not choices or len(groups) < 2:
        return groups
    answer_top = min(a["bbox"][1] for a in choices)
    page_lines = [l for l in lines if l["page"] == page]
    body = [g for g in groups if g["bbox"][3] < answer_top]
    body_ids = {id(g) for g in body}
    other = [g for g in groups if id(g) not in body_ids]
    body = _point_lattices(body, [l for l in page_lines if l["bottom"] < answer_top])
    for annotation in body[:]:
        detected = _dimension_axis(annotation)
        if not detected or annotation not in body:
            continue
        axis, thickness = detected
        b = annotation["bbox"]
        length = b[axis + 2] - b[axis]
        reach = [
            b[0] - 3 * thickness,
            b[1] - 3 * thickness,
            b[2] + 3 * thickness,
            b[3] + 3 * thickness,
        ]
        if not any(
            MEASUREMENT.fullmatch(_text(l).strip()) and intersects(_box(l), reach)
            for l in page_lines
        ):
            continue
        owners = []
        for owner in body:
            if owner is annotation or _dimension_axis(owner):
                continue
            m = owner["bbox"]
            if not any(
                o["object_type"] in ("curve", "rect")
                and min(o["bbox"][2] - o["bbox"][0], o["bbox"][3] - o["bbox"][1])
                > thickness * 2
                for o in owner["objects"]
            ):
                continue
            span = max(length, m[axis + 2] - m[axis])
            if (
                max(abs(m[axis] - b[axis]), abs(m[axis + 2] - b[axis + 2]))
                > 0.15 * span
            ):
                continue
            gap = max(b[1 - axis] - m[3 - axis], m[1 - axis] - b[3 - axis], 0)
            if gap <= 0 or gap > 0.65 * min(m[2] - m[0], m[3] - m[1]):
                continue
            region = bounds([b, m])
            if any(
                _prose(l) and intersects(_box(l), region) and not _contained(_box(l), m)
                for l in page_lines
            ):
                continue
            if any(
                g is not owner and g is not annotation and intersects(g["bbox"], region)
                for g in body
            ):
                continue
            owners.append(owner)
        if len(owners) == 1:
            body = _merge(
                body,
                [owners[0], annotation],
                "Detached dimension arrow joined to its unique extent-aligned body visual; paired heads, measurement label and prose barriers verified.",
            )
        elif len(owners) > 1:
            annotation.setdefault("grouping_warnings", []).append(
                "visual_grouping_uncertain:dimension_annotation_multiple_owners"
            )
    return sorted([*body, *other], key=lambda g: (g["bbox"][1], g["bbox"][0]))
