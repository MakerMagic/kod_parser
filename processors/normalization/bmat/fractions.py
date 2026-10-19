"""Conservative fraction rendering from stored RAW vector/glyph evidence only."""

from collections import Counter
from statistics import median


def key(c):
    return tuple(
        c[k] for k in ("text", "x0", "x1", "top", "bottom", "size", "fontname")
    )


def recover(option):
    items = option.get("glyph_layout", [])
    all_chars = {key(c): c for item in items for c in item["glyphs"]}
    if not items or Counter(
        "".join(c["text"] for c in all_chars.values()).replace(" ", "")
    ) != Counter("".join(option["text"].split())):
        return None
    found, used = [], set()
    for item in items:
        x0, y0, x1, y1 = item["bbox"]
        width, height = x1 - x0, y1 - y0
        diagonal = height > 2 and (
            0.35 < width / height < 1.5 or item.get("separator_is_text", False)
        )
        horizontal = height < 0.5 and width > 2
        if not (diagonal or horizontal):
            continue
        digits = [c for c in item["glyphs"] if c["text"].isdigit()]
        if diagonal:
            # Superscript numerator and subscript denominator flank a diagonal
            # native line. Full-height whole-number prefixes are not numerators.
            digits = [
                c
                for c in digits
                if c["size"] < height * 0.9
                and x0 - c["size"] * 1.5 <= c["x0"]
                and c["x1"] <= x1 + c["size"] * 3
            ]
            upper = [c for c in digits if (c["top"] + c["bottom"]) / 2 < (y0 + y1) / 2]
            lower = [c for c in digits if (c["top"] + c["bottom"]) / 2 > (y0 + y1) / 2]
        else:
            upper = [
                c
                for c in digits
                if x0 <= c["x0"]
                and c["x1"] <= x1
                and 0 <= y0 - c["bottom"] <= c["size"] * 0.8
            ]
            lower = [
                c
                for c in digits
                if x0 <= c["x0"]
                and c["x1"] <= x1
                and 0 <= c["top"] - y1 <= c["size"] * 0.8
            ]
        if not upper or not lower:
            continue
        if any(
            max(c["top"] for c in group) - min(c["top"] for c in group)
            > median(c["size"] for c in group) * 0.35
            for group in (upper, lower)
        ):
            continue
        if diagonal and max(c["x0"] for c in upper) >= min(c["x0"] for c in lower):
            continue
        ids = {key(c) for c in upper + lower}
        if item.get("separator_is_text"):
            ids.update(key(c) for c in item["glyphs"] if c["text"] in {"/", "⁄"})
        if ids & used:
            continue
        numerator = "".join(c["text"] for c in sorted(upper, key=lambda c: c["x0"]))
        denominator = "".join(c["text"] for c in sorted(lower, key=lambda c: c["x0"]))
        if not int(denominator):
            continue
        found.append(
            {
                "text": numerator + "/" + denominator,
                "x0": min(c["x0"] for c in upper + lower),
                "x1": max(c["x1"] for c in upper + lower),
                "native_bbox": item["bbox"],
                "numerator_glyphs": upper,
                "denominator_glyphs": lower,
                "method": "diagonal_fraction" if diagonal else "stacked_fraction",
            }
        )
        used |= ids
    if not found:
        return None
    rest = [c for k, c in all_chars.items() if k not in used]
    # Normal text must share a baseline; arbitrary multiline numbers are not a
    # fraction-containing answer merely because a small line is nearby.
    if (
        rest
        and max(c["bottom"] for c in rest) - min(c["bottom"] for c in rest)
        > median(c["size"] for c in rest) * 0.35
    ):
        return None
    events = [
        {"text": c["text"], "x0": c["x0"], "x1": c["x1"], "fraction": False}
        for c in rest
    ]
    events += [{**f, "fraction": True} for f in found]
    events.sort(key=lambda e: e["x0"])
    out = ""
    previous = None
    scale = median(c["size"] for c in all_chars.values())
    for event in events:
        if previous and (
            event["x0"] - previous["x1"] > scale * 0.15
            or event["fraction"]
            and previous["text"][-1:].isdigit()
        ):
            out += " "
        out += event["text"]
        previous = event
    return out, found
