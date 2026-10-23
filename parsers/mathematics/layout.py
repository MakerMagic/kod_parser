"""Source-evidenced layout adapters sharing the mathematics RAW pipeline."""

import re
from collections import defaultdict
from statistics import median


def profile(cover, digest):
    version = re.search(r"NUFYPET\s+Math\s+v\s*(\d+(?:\.\d+)*)", cover, re.IGNORECASE)
    if version:
        return {
            "source": "matdev",
            "version": version[1],
            "id": f"matdev_v{version[1]}_{digest[:20]}",
        }
    trial = re.search(r"Trial\s+SET\s*#\s*(\d+)\s*\(math\)", cover, re.IGNORECASE)
    if trial:
        return {
            "source": "sky_trial",
            "version": trial[1],
            "id": f"sky_trial_v{trial[1]}_{digest[:20]}",
        }
    raise ValueError("Unrecognized mathematics source; no content-derived identity")


def numbered_marks(words, chars, minimum=1):
    """Number + printed dot at the shared left margin, independent of font names."""
    found = []
    for w in words:
        match = re.fullmatch(r"(\d{1,3})([.)])?", w["text"])
        if not match:
            continue
        if int(match[1]) < minimum:
            continue
        marker = dict(w, number=int(match[1]))
        if not match[2]:
            punctuation = [
                c
                for c in chars
                if c["text"] in {".", ")"}
                and -1 <= c["x0"] - w["x1"] < 3
                and abs(c["top"] - w["top"]) < (w["bottom"] - w["top"]) * 0.45
            ]
            if not punctuation:
                continue
            marker["x1"] = min(punctuation, key=lambda c: c["x0"])["x1"]
            marker["bottom"] = max(
                marker["bottom"], min(punctuation, key=lambda c: c["x0"])["bottom"]
            )
        found.append(marker)
    margin = min((w["x0"] for w in found), default=0)
    ordered = sorted(
        (w for w in found if abs(w["x0"] - margin) < 5),
        key=lambda w: (w["top"], w["x0"]),
    )
    result = []
    for w in ordered:
        if not result or w["number"] > result[-1]["number"]:
            result.append(w)
    return result


def white_background(obj):
    color = obj.get("non_stroking_color")
    return (
        obj.get("fill")
        and not obj.get("stroke")
        and (color == 1 or color in ((1, 1, 1), (0, 0, 0, 0)))
    )


def vector_radicals(lines, chars, page):
    """Recognize a connected radical hook/riser/bar with glyphs beneath the bar."""
    roots, used = [], set()
    for bi, bar in enumerate(lines):
        if bar["bottom"] - bar["top"] > 0.3 or bar["x1"] - bar["x0"] < 2:
            continue
        for ri, rise in enumerate(lines):
            pts = rise.get("pts", [])
            if len(pts) != 2:
                continue
            left, right = sorted(pts)
            h = left[1] - right[1]
            if not (
                3 < h < 45
                and 0.5 < right[0] - left[0] < h * 0.65
                and abs(right[0] - bar["x0"]) < 0.8
                and abs(right[1] - bar["top"]) < 0.8
            ):
                continue
            checks = []
            for ci, check in enumerate(lines):
                cp = sorted(check.get("pts", []))
                if (
                    len(cp) == 2
                    and 0.3 < cp[1][0] - cp[0][0] < 6
                    and cp[0][1] < cp[1][1]
                    and abs(cp[1][0] - left[0]) < 0.8
                    and abs(cp[1][1] - left[1]) < 0.8
                ):
                    checks.append((ci, cp))
            rad = [
                c
                for c in chars
                if c["text"].strip()
                and bar["x0"] - 0.8 <= c["x0"]
                and c["x1"] <= bar["x1"] + 0.8
                and bar["top"] - 1 <= c["top"] < left[1]
            ]
            if len(checks) != 1 or not rad:
                continue
            ci, cp = checks[0]
            hook = [
                (i, o)
                for i, o in enumerate(lines)
                if abs(o["x1"] - cp[0][0]) < 0.8
                and abs(o["top"] - cp[0][1]) < 0.8
                and o["x0"] < cp[0][0]
                and o["x1"] - o["x0"] < 4
            ]
            if len(hook) != 1:
                continue
            hi, tip = hook[0]
            if any(c["text"] == "√" and abs(c["x1"] - bar["x0"]) < 2 for c in chars):
                continue
            scale = max(c["size"] for c in rad)
            fractions = [
                r
                for r in lines
                if r["bottom"] - r["top"] < 0.3
                and bar["x0"] - 0.8 <= r["x0"]
                and r["x1"] <= bar["x1"] + 0.8
                and bar["top"] + 1 < r["top"] < left[1]
                and any(c["bottom"] < r["top"] + 0.8 for c in rad)
                and any(c["top"] > r["bottom"] - 0.8 for c in rad)
            ]
            baseline = (
                max(fractions, key=lambda r: r["x1"] - r["x0"])["top"] + scale * 0.5
                if fractions
                else median(c["bottom"] for c in rad if c["size"] >= scale * 0.9)
            )
            roots.append(
                {
                    "text": "√",
                    "id": f"p{page}_vroot{bi}",
                    "fontname": "vector_math",
                    "size": scale,
                    "baseline": baseline,
                    "x0": tip["x0"],
                    "x1": bar["x0"],
                    "top": bar["top"],
                    "bottom": left[1],
                    "method": "connected_vector_radical",
                    "line_ids": [hi, ci, ri, bi],
                }
            )
            used.update((hi, ci, ri))
            break
    return roots, used


def math_hints(chars):
    """Mixed legacy fonts: numeric/operator tokens and adjacent math letters."""
    font_text = defaultdict(str)
    for c in chars:
        font_text[c["fontname"]] += c["text"]
    prose_fonts = {
        font
        for font, text in font_text.items()
        if len(
            {
                word.lower()
                for word in re.findall(r"[a-zA-Z]{4,}", text)
                if re.search(
                    r"[a-z]{4,}",
                    re.sub(r"sin|cos|tan|cot|ctg|log|ln|sec|csc", "", word),
                    re.IGNORECASE,
                )
            }
        )
        >= 2
    }
    for c in chars:
        t = c["text"]
        c["geometry_order"] = True
        c["math_hint"] = bool(t.strip()) and (
            t.isdigit()
            or "italic" in c["fontname"].lower()
            or "symbol" in c["fontname"].lower()
            or c["fontname"] not in prose_fonts
            or c["text"] in "⇑↑"
            or "\uf8eb" <= t <= "\uf8fe"
            or t in "√∛∜=<>≤≥±×÷∠π∞∑∫"
        )
    for c in chars:
        if len(c["text"]) == 1 and c["text"].isalpha() and not c["math_hint"]:
            neighbours = [
                n
                for n in chars
                if n is not c
                and n["text"].strip()
                and abs(
                    n.get("pdf_baseline", n["bottom"])
                    - c.get("pdf_baseline", c["bottom"])
                )
                < c["size"] * 0.6
                and min(abs(n["x1"] - c["x0"]), abs(c["x1"] - n["x0"])) < 1.5
            ]
            if any(n["math_hint"] for n in neighbours) and not any(
                n["text"].isalpha() and not n["math_hint"] for n in neighbours
            ):
                c["math_hint"] = True
    # A whole word containing operators is math only when it has no prose word.
    groups = []
    for c in chars:
        if not c["text"].strip():
            if groups and groups[-1]:
                groups.append([])
        else:
            if not groups:
                groups.append([])
            groups[-1].append(c)
    for group in groups:
        text = "".join(c["text"] for c in group)
        if re.search(r"[=+*/<>~−]", text) and not re.search(
            r"[A-Za-z]{3,}", re.sub(r"sin|cos|tan|cot|log|ln|sec|csc", "", text)
        ):
            for c in group:
                c["math_hint"] = True
    start = 0
    while start < len(chars):
        if not chars[start]["text"].isspace():
            start += 1
            continue
        end = start
        while end < len(chars) and chars[end]["text"].isspace():
            end += 1
        if (
            start
            and end < len(chars)
            and chars[start - 1].get("math_hint")
            and chars[end].get("math_hint")
        ):
            for c in chars[start:end]:
                c["math_hint"] = True
        start = end


def leading_figure_cuts(cuts, figures, words, option_anchors):
    """Move a completed-answer gap's next-question cut above its leading figure."""
    result = []
    for index, (top, anchor) in enumerate(cuts):
        previous = cuts[index - 1][0] if index else float("-inf")
        candidates = [
            b
            for b in figures
            if previous < b[1]
            and b[3] <= anchor["top"] + (anchor["bottom"] - anchor["top"]) * 0.6
        ]
        if candidates:
            clusters = []
            for b in sorted(candidates, key=lambda b: b[1]):
                if clusters and b[1] <= max(v[3] for v in clusters[-1]) + 8:
                    clusters[-1].append(b)
                else:
                    clusters.append([b])
            candidates = clusters[-1]
            before = [
                w for w in words if previous <= w["top"] < min(b[1] for b in candidates)
            ]
            opts = option_anchors(before)
            # At page start there is no preceding numbered question; otherwise
            # require a complete contiguous option sequence before the figure.
            if (not index and not before) or (
                len(opts) >= 4
                and opts[-1]["bottom"] < min(b[1] for b in candidates) - 2
                and anchor["top"] - max(b[3] for b in candidates)
                < (anchor["bottom"] - anchor["top"]) * 2.5
            ):
                top = min(top, min(b[1] for b in candidates) - 1)
        result.append((top, anchor))
    return result


def condition_figures(figures, chars, anchors):
    """A diagram starting beside the condition stays whole above/beside options."""
    body, answers = [], []
    if not anchors:
        return body, list(figures)
    first = min(anchors, key=lambda a: a["top"])
    height = first["bottom"] - first["top"]
    for box in figures:
        if not (
            box[1] < first["top"] - height
            and (box[1] + box[3]) / 2 < first["top"]
            and box[3] - box[1] > height * 1.5
            and not any(
                box[0] <= (a["x0"] + a["x1"]) / 2 <= box[2]
                and box[1] <= (a["top"] + a["bottom"]) / 2 <= box[3]
                for a in anchors
            )
            and any(
                c["text"].strip()
                and not c.get("math_hint")
                and c["top"] < first["top"] - height
                and min(c["bottom"], box[3]) > max(c["top"], box[1])
                and (c["x1"] < box[0] or c["x0"] > box[2])
                for c in chars
            )
        ):
            answers.append(box)
            continue
        labels = [
            c
            for c in chars
            if c["text"].strip()
            and (c.get("math_hint") or c["text"].isupper())
            and max(box[0] - c["x1"], c["x0"] - box[2], 0) <= c["size"]
            and max(box[1] - c["bottom"], c["top"] - box[3], 0) <= c["size"]
        ]
        body.append(
            [
                min([box[0], *[c["x0"] for c in labels]]) - 1,
                min([box[1], *[c["top"] for c in labels]]) - 1,
                max([box[2], *[c["x1"] for c in labels]]) + 1,
                max([box[3], *[c["bottom"] for c in labels]]) + 1,
            ]
        )
    return body, answers
