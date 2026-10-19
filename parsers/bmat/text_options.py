"""Recover vertically centred text-choice labels without changing source text."""

from copy import deepcopy
from itertools import pairwise


def recover(question, pending, marker, decode):
    options = question["options"]
    if len(options) < 3 or [o["label"] for o in options] != list(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(options)]
    ):
        return
    block = question["raw"]["question_block"]
    start = len(block) - len(question["raw"]["options_block"])
    anchors = [
        (l, marker(l, "option"))
        for l in pending["lines"]
        if l["block_start"] >= start
        and marker(l, "option")
        and marker(l, "option")[0] in {o["label"] for o in options}
    ]
    if [m[0] for _, m in anchors] != [o["label"] for o in options]:
        return
    if not any(l.get("readable_text", l["text"]).strip() == m[0] for l, m in anchors):
        return
    if max(l["x0"] for l, _ in anchors) - min(l["x0"] for l, _ in anchors) > 4:
        return
    if len({l["page"] for l, _ in anchors}) != 1 or any(
        b["top"] <= a["bottom"] for (a, _), (b, _) in pairwise(anchors)
    ):
        return
    first = anchors[0][0]
    height = first["bottom"] - first["top"]
    if any(
        not obj.get("decorative")
        and obj["page"] == first["page"]
        and obj["bbox"][3] > first["top"] - height
        for obj in question["images"]
    ):
        return
    candidates = [
        l
        for l in pending["lines"]
        if l["page"] == first["page"]
        and l["top"] >= first["top"] - height * 1.5
        and l["x0"] >= first["x0"] - 1
    ]
    if sum(len(l.get("readable_text", l["text"]).split()) >= 5 for l in candidates) < 3:
        return
    groups = {o["label"]: [] for o in options}
    anchor_by_start = {l["block_start"]: m for l, m in anchors}
    for line in candidates:
        centre = (line["top"] + line["bottom"]) / 2
        nearest = min(
            anchors,
            key=lambda item: abs((item[0]["top"] + item[0]["bottom"]) / 2 - centre),
        )
        label = nearest[1][0]
        own_marker = anchor_by_start.get(line["block_start"])
        if own_marker:
            label = own_marker[0]
        offset = line["block_start"] + (own_marker[1] if own_marker else 0)
        text = block[offset : line["block_start"] + len(line["text"])]
        if text.strip():
            groups[label].append(
                {
                    "text": text,
                    "raw_span": {
                        "start": offset,
                        "end": line["block_start"] + len(line["text"]),
                    },
                    "page": line["page"],
                    "bbox": [line["x0"], line["top"], line["x1"], line["bottom"]],
                }
            )
    if not all(groups.values()):
        return
    earliest = min(
        [r["raw_span"]["start"] for g in groups.values() for r in g]
        + [l["block_start"] for l, _ in anchors]
    )
    first_word = marker(pending["lines"][0], "number")[1]
    question["raw"]["text_field_candidates"] = {
        "question_text": question["question_text"],
        "options": deepcopy(options),
        "options_block": question["raw"]["options_block"],
    }
    question["question_text"] = decode(block[first_word:earliest])
    question["raw"]["options_block"] = block[earliest:]
    question["raw"]["field_method"] = "vertically_centred_text_option_labels"
    for option in options:
        option["text"] = "\n".join(decode(r["text"]) for r in groups[option["label"]])
        option["source_lines"] = groups[option["label"]]
