"""Inspect question-to-final-option height using the parser's content viewport."""

import re


def measure(question, pages):
    spans = question["raw"]["page_spans"]
    result = {
        "threshold": 0.60,
        "status": "unresolved",
        "policy": "single_complete_question",
    }
    if len(spans) != 1:
        return {
            **result,
            "status": "not_applicable",
            "reason": "cross_page_question_not_measured_as_one_page",
        }
    page_number = spans[0]["page"]
    page = pages[page_number - 1]
    # Exactly the viewport used by parser.content_lines, not observed ink bounds
    # (which would make every short question occupy 100% of its own viewport).
    top, bottom = 35.0, page["height"] - 45.0
    result.update(
        page=page_number,
        content_top=top,
        content_bottom=bottom,
        usable_page_height=bottom - top,
        viewport_source="parser.content_lines",
    )
    options = question.get("options", [])
    labels = [o["label"] for o in options]
    if not labels or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]):
        return {**result, "reason": "final_answer_option_not_reliably_identified"}
    blocks = [
        b
        for b in question.get("layout_blocks", [])
        if b.get("bbox") and b.get("page", page_number) == page_number
    ]
    starts = [b["bbox"][1] for b in blocks if b.get("type") == "text"]
    ends = []
    for b in blocks:
        value = b.get("readable_text", b.get("text", "")).strip()
        # Layout projections can retain the preceding label for a source row;
        # the actual readable final-option anchor is stronger evidence.
        anchor = re.match(r"^" + re.escape(labels[-1]) + r"(?:\s|$)", value)
        if b.get("component") == "option" and (b.get("label") == labels[-1] or anchor):
            if not re.match(r"^(?:END OF|Turn over|Copyright|©)", value, re.IGNORECASE):
                ends.append(b["bbox"][3])
        elif b.get("component") == "visual_label" and b.get("label") == labels[-1]:
            ends.append(b["bbox"][3])
    for option in options:
        if option.get("label_bbox"):
            ends.append(option["label_bbox"][3])
        for asset in option.get("images", []):
            if asset.get("page") != page_number or asset.get("belongs_to") != "option":
                return {**result, "reason": "option_visual_geometry_ambiguous"}
            ends.append(asset["bbox"][3])
    if not starts or not ends:
        return {**result, "reason": "final_answer_option_geometry_missing"}
    qtop, final_bottom = min(starts), max(ends)
    if not top <= qtop < final_bottom <= bottom:
        return {**result, "reason": "question_outside_verified_content_viewport"}
    height = final_bottom - qtop
    return {
        **result,
        "status": "measured",
        "question_top": qtop,
        "final_option_bottom": final_bottom,
        "occupied_height": height,
        "occupancy_ratio": height / (bottom - top),
        "exceeds_threshold": height > 0.60 * (bottom - top),
    }
