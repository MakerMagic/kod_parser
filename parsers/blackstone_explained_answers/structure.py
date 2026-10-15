"""Paragraphs and true hanging lists for the newer single-column source layout."""

import re

ITEM = re.compile(r"^\s*([•●▪◦‣♦◆]|[-–—](?=\s)|\d+[.)](?=\s))\s*(\S.*)$")


def reference(line):
    return {key: line[key] for key in ("page", "line_id", "start", "end", "bbox")}


def standalone_list_lead(lines, index):
    """Separate a complete lead-in only when real aligned list items follow."""
    if index == 0 or index + 2 >= len(lines):
        return False
    previous, line, first = lines[index - 1], lines[index], lines[index + 1]
    if not (
        line["text"].rstrip().endswith(":")
        and line["text"][:1].isupper()
        and previous["text"].rstrip().endswith((".", "!", "?", ")"))
        and ITEM.match(first["text"])
    ):
        return False
    scale = max(1, line["bbox"][3] - line["bbox"][1])
    content_x = first.get("content_x", first["bbox"][0] + scale * 0.75)
    for following in lines[index + 2 :]:
        if ITEM.match(following["text"]):
            return abs(following["bbox"][0] - first["bbox"][0]) <= scale * 0.4
        if abs(following["bbox"][0] - content_x) > scale * 0.6:
            return False
    return False


def structure(lines, correct_answer):
    del correct_answer  # No letter inference from ordinary source lists.
    blocks, warnings = [], []
    previous = anchor = None
    for index, line in enumerate(lines):
        value = line["text"]
        match = ITEM.match(value)
        height = max(1, line["bbox"][3] - line["bbox"][1])
        if match and match[1][0].isdigit():
            # A lone numerical sentence is not automatically an ordinal list.
            following = next(
                (
                    ITEM.match(l["text"])
                    for l in lines[index + 1 :]
                    if ITEM.match(l["text"])
                ),
                None,
            )
            prior = ITEM.match(anchor["text"]) if anchor else None
            repeated = (
                following
                and following[1][0].isdigit()
                and int(re.sub(r"\D", "", following[1]))
                == int(re.sub(r"\D", "", match[1])) + 1
            )
            continued = (
                prior
                and prior[1][0].isdigit()
                and int(re.sub(r"\D", "", match[1]))
                == int(re.sub(r"\D", "", prior[1])) + 1
            )
            if not repeated and not continued:
                match = None
        if match:
            if not blocks or blocks[-1]["type"] != "list":
                blocks.append({"type": "list", "role": "other", "items": []})
            blocks[-1]["items"].append(
                {"text": match[2], "line_refs": [reference(line)]}
            )
            anchor = line
        else:
            content_x = (
                anchor.get("content_x", anchor["bbox"][0] + height * 0.75)
                if anchor
                else None
            )
            hanging = bool(
                blocks
                and blocks[-1]["type"] == "list"
                and anchor
                and line["bbox"][0] >= content_x - height * 0.2
                and abs(line["bbox"][0] - content_x) <= height * 0.6
                and (
                    line["page"] != previous["page"]
                    or line["bbox"][1] - previous["bbox"][3] <= height * 0.8
                )
            )
            if hanging:
                item = blocks[-1]["items"][-1]
                item["text"] += "\n" + value
                item["line_refs"].append(reference(line))
            else:
                paragraph_break = (
                    not blocks
                    or blocks[-1]["type"] != "paragraph"
                    or standalone_list_lead(lines, index)
                    or previous
                    and previous["page"] == line["page"]
                    and line["bbox"][1] - previous["bbox"][3] > height * 0.7
                    or previous
                    and previous["page"] != line["page"]
                    and previous["text"].rstrip().endswith((".", "!", "?", ":"))
                )
                if paragraph_break:
                    blocks.append(
                        {
                            "type": "paragraph",
                            "role": "main",
                            "text": value,
                            "line_refs": [reference(line)],
                        }
                    )
                else:
                    blocks[-1]["text"] += "\n" + value
                    blocks[-1]["line_refs"].append(reference(line))
                anchor = None
            if value.strip() in set("•●▪◦‣♦◆©�"):
                warnings.append(
                    "bullet_structure_ambiguous:standalone_symbol_preserved"
                )
        previous = line
    for order, block in enumerate(blocks, 1):
        block["order"] = order
    paragraphs = [block for block in blocks if block["type"] == "paragraph"]
    lists = [block for block in blocks if block["type"] == "list"]
    return {
        "blocks": blocks,
        "paragraphs": paragraphs,
        "main_explanation": "\n\n".join(p["text"] for p in paragraphs),
        "bulleted_blocks": lists,
        "choice_analysis": [],
        "other_lists": lists,
    }, warnings
