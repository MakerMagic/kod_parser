"""Conservative paragraph/list projections with complete source-line accounting."""

import re

BULLET = re.compile(r"^\s*(?:[•●▪◦‣∙·\uf0b7]|[-–—](?=\s)|\d+[.)](?=\s))\s*(.+)$")
CHOICE = re.compile(
    r"^(?:(?:Answer|Option|Choice)\s+)?([A-Z])[).:–—-]\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)


def reference(line):
    return {k: line[k] for k in ("page", "line_id", "start", "end", "bbox")}


def structure(lines, correct_answer):
    label_rows = [
        i for i, line in enumerate(lines) if re.match(r"^[A-Z]\s*[-–—:]", line["text"])
    ]
    repeated = set()
    for i in label_rows:
        peers = [
            j
            for j in label_rows
            if abs(lines[i]["bbox"][0] - lines[j]["bbox"][0])
            <= (lines[i]["bbox"][3] - lines[i]["bbox"][1]) * 0.35
        ]
        if len({lines[j]["text"][0] for j in peers}) >= 2:
            repeated.update(peers)
    blocks, issues = [], []
    previous = None
    for index, line in enumerate(lines):
        value = line["text"]
        bullet = BULLET.match(value)
        aligned_list = bool(
            blocks
            and blocks[-1]["type"] == "list"
            and abs(
                line["bbox"][0] - blocks[-1]["items"][-1]["line_refs"][0]["bbox"][0]
            )
            <= (line["bbox"][3] - line["bbox"][1]) * 0.5
        )
        compact_dash = re.match(r"^[-–—]([A-Z][a-z]{2,}\b.*)$", value)
        uncertain_marker = aligned_list and bool(re.match(r"^©\s*[A-Z]", value))
        if (
            bullet
            or index in repeated
            or (compact_dash and aligned_list)
            or uncertain_marker
        ):
            if not blocks or blocks[-1]["type"] != "list":
                blocks.append({"type": "list", "items": [], "role": "other"})
            if uncertain_marker:
                issues.append(
                    "bullet_structure_ambiguous:unexpected_encoded_list_marker_preserved:"
                    f"page_{line['page']}_line_{line['line_id']}"
                )
            blocks[-1]["items"].append(
                {
                    "text": bullet[1]
                    if bullet
                    else compact_dash[1]
                    if compact_dash
                    else value,
                    "line_refs": [reference(line)],
                }
            )
        else:
            paragraph_break = (
                previous is None
                or previous["page"] != line["page"]
                and previous["text"].rstrip().endswith((".", "?", "!", ":"))
                or previous["page"] == line["page"]
                and (
                    line["bbox"][1] - previous["bbox"][3]
                    > max(5, (line["bbox"][3] - line["bbox"][1]) * 0.7)
                    or line["bbox"][0] - previous["bbox"][0]
                    > (line["bbox"][3] - line["bbox"][1]) * 0.7
                )
            )
            hanging = (
                blocks
                and blocks[-1]["type"] == "list"
                and previous
                and not paragraph_break
                and line["bbox"][0]
                >= blocks[-1]["items"][-1]["line_refs"][0]["bbox"][0] - 1
                and (
                    previous["page"] != line["page"]
                    or line["bbox"][1] - previous["bbox"][3]
                    <= max(5, (line["bbox"][3] - line["bbox"][1]) * 0.7)
                )
            )
            if hanging:
                item = blocks[-1]["items"][-1]
                item["text"] += "\n" + value
                item["line_refs"].append(reference(line))
            elif not blocks or blocks[-1]["type"] != "paragraph" or paragraph_break:
                blocks.append(
                    {
                        "type": "paragraph",
                        "text": value,
                        "role": "main",
                        "line_refs": [reference(line)],
                    }
                )
            else:
                blocks[-1]["text"] += "\n" + value
                blocks[-1]["line_refs"].append(reference(line))
        previous = line
    analysis = []
    for i, block in enumerate(blocks):
        block["order"] = i + 1
        if block["type"] != "list" or i == 0 or blocks[i - 1]["type"] != "paragraph":
            continue
        lead = blocks[i - 1]["text"]
        transition = (
            lead.rstrip().endswith(":")
            and re.search(
                r"\b(?:wrong|incorrect|other|eliminat\w*)\b", lead, re.IGNORECASE
            )
            and re.search(r"\b(?:answers?|choices?|options?)\b", lead, re.IGNORECASE)
        )
        if not transition:
            continue
        choices = [CHOICE.match(item["text"]) for item in block["items"]]
        labels = [m[1].upper() for m in choices if m]
        if (
            len(labels) < 2
            or len(labels) != len(choices)
            or len(set(labels)) != len(labels)
            or correct_answer in labels
        ):
            # The semantic list role is clear, but absent/conflicting letters
            # cannot justify assigning individual items to answer choices.
            blocks[i - 1]["role"] = "choice_transition"
            block["role"] = "incorrect_choices_unmapped"
            block["transition"] = lead
            issues.append(
                "bullet_structure_ambiguous:choice_transition_without_unique_incorrect_labels"
            )
            continue
        blocks[i - 1]["role"] = "choice_transition"
        block["role"] = "incorrect_choices"
        block["transition"] = lead
        for item, match in zip(block["items"], choices):
            item["label"] = match[1].upper()
            analysis.append(
                {
                    "label": item["label"],
                    "text": match[2],
                    "line_refs": item["line_refs"],
                    "list_order": block["order"],
                }
            )
    main = [b for b in blocks if b["type"] == "paragraph" and b["role"] == "main"]
    lists = [b for b in blocks if b["type"] == "list"]
    return {
        "main_explanation": "\n\n".join(b["text"] for b in main),
        "paragraphs": main,
        "blocks": blocks,
        "bulleted_blocks": lists,
        "choice_analysis": analysis,
        "other_lists": [
            b for b in lists if not b["role"].startswith("incorrect_choices")
        ],
    }, issues
