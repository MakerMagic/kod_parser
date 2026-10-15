"""Conservative paragraph/list projections with complete source-line accounting."""

import re

BULLET = re.compile(r"^\s*(?:[•●▪◦‣∙·♦◆■○\uf0b7]|[-–—](?=\s)|\d+[.)](?=\s))\s*(.+)$")
CHOICE = re.compile(
    r"^(?:(?:Answer|Option|Choice)\s+)?([A-Z])[).:–—-]\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)


def reference(line):
    return {k: line[k] for k in ("page", "line_id", "start", "end", "bbox")}


def height(line):
    return max(1, line["bbox"][3] - line["bbox"][1])


def marker(value):
    """Candidates are not list starts until layout/context corroborates them."""
    bullet = BULLET.match(value)
    if bullet:
        return bullet[1], value[: bullet.start(1)], False
    compact = re.match(r"^[-–—]([A-Z][a-z]{2,}\b.*)$", value)
    if compact:
        return compact[1], value[: compact.start(1)], False
    encoded = re.match(r"^©\s*[A-Z]", value)
    if encoded:
        return value, "©", True  # Keep undecoded meaningful text verbatim.
    if re.match(r"^[A-Z]\s*[-–—:]", value) and CHOICE.match(value):
        return value, value[: CHOICE.match(value).start(2)], False
    return None


def columns(line):
    left = line["bbox"][0]
    part = marker(line["text"])
    if part is None:
        return (left,)
    prefix = part[1].strip()
    # PDF text rows include the marker; wrapped rows often start at its text.
    # Use marker length and glyph height, not an unbounded x>=left condition.
    advance = height(line) * (0.8 if re.match(r"\d", prefix) else 0.55)
    if len(prefix) > 2:
        advance += height(line) * 0.25 * (len(prefix) - 2)
    return left, left + advance


def same_column(line, start):
    scale = max(height(line), height(start))
    if max(height(line), height(start)) > min(height(line), height(start)) * 1.8:
        return False
    return min(abs(line["bbox"][0] - x) for x in columns(start)) <= scale * 0.35


def continuation_column(line, start, previous):
    if same_column(line, start):
        return True
    # Some source lists wrap back to the prose baseline. Require both a
    # geometrically plausible reverse hang and an unfinished grammatical line.
    return bool(
        line["text"][:1].islower()
        and not previous["text"].rstrip().endswith((".", "?", "!", ":"))
        and abs(line["bbox"][0] - (start["bbox"][0] - height(start) * 1.25))
        <= max(height(start), height(line)) * 0.35
        and max(height(start), height(line)) <= min(height(start), height(line)) * 1.8
    )


def lead_tail(value):
    return re.split(r"(?<=[.!?])\s+", value.rstrip())[-1]


def introduction(value):
    value = lead_tail(value)
    return bool(
        value.rstrip().endswith(":")
        and re.search(
            r"\b(?:follow\w*|below|list|facts?|notes?|steps?|reasons?|observations?|consider|calculated)\b",
            value,
            re.IGNORECASE,
        )
    )


def elimination(value):
    value = lead_tail(value)
    return bool(
        value.rstrip().endswith(":")
        and re.search(
            r"\b(?:wrong|incorrect|other|eliminat\w*)\b", value, re.IGNORECASE
        )
        and re.search(r"\b(?:answers?|choices?|options?)\b", value, re.IGNORECASE)
    )


def repeated_start(lines, index):
    """Find another item in the same local run, not anywhere in the question."""
    start = lines[index]
    previous = start
    for next_line in lines[index + 1 :]:
        part = marker(next_line["text"])
        if part:
            return (
                abs(start["bbox"][0] - next_line["bbox"][0])
                <= max(height(start), height(next_line)) * 0.5
                or previous is not start
                and abs(previous["bbox"][0] - next_line["bbox"][0])
                <= max(height(previous), height(next_line)) * 0.35
            )
        if not continuation_column(next_line, start, previous) or introduction(
            next_line["text"]
        ):
            return False
        previous = next_line
    return False


def standalone_symbol(value):
    return value.strip() in set("•●▪◦‣∙·♦◆■○©\uf0b7�")


def source_numbered_list(block, source_lines):
    """An intact source ordinal list is not a failed A–E label extraction."""
    starts = [
        source_lines[(item["line_refs"][0]["page"], item["line_refs"][0]["line_id"])]
        for item in block["items"]
    ]
    numbers = [re.match(r"^\s*(\d+)[.)]\s+\S", line["text"]) for line in starts]
    return (
        len(starts) >= 2
        and all(numbers)
        and [int(match[1]) for match in numbers] == list(range(1, len(starts) + 1))
        and all(same_column(line, starts[0]) for line in starts[1:])
    )


def structure(lines, correct_answer):
    supported = {
        i
        for i in range(len(lines))
        if marker(lines[i]["text"]) and repeated_start(lines, i)
    }
    source_lines = {(l["page"], l["line_id"]): l for l in lines}
    blocks, issues = [], []
    previous = None
    for index, line in enumerate(lines):
        value = line["text"]
        part = marker(value)
        current_list = blocks[-1] if blocks and blocks[-1]["type"] == "list" else None
        first_ref = current_list["items"][-1]["line_refs"][0] if current_list else None
        start = (
            source_lines[(first_ref["page"], first_ref["line_id"])]
            if first_ref
            else None
        )
        last_ref = current_list["items"][-1]["line_refs"][-1] if current_list else None
        aligned_list = bool(
            start
            and (
                same_column(line, start)
                or len(current_list["items"][-1]["line_refs"]) > 1
                and abs(line["bbox"][0] - last_ref["bbox"][0]) <= height(line) * 0.35
            )
        )
        lead = (
            blocks[-1]["text"] if blocks and blocks[-1]["type"] == "paragraph" else ""
        )
        # A bare symbol is ignored only in a verified lead-in -> repeated-list
        # sequence. It still occupies an ordered raw-span-backed block.
        artifact = (
            standalone_symbol(value)
            and value.strip() not in {"©", "�"}
            and (
                introduction(lead)
                or elimination(lead)
                or current_list
                and index + 1 < len(lines)
                and same_column(lines[index + 1], start)
            )
            and index + 1 in supported
            and marker(lines[index + 1]["text"])
            and not marker(lines[index + 1]["text"])[2]
            and previous
            and abs(line["bbox"][0] - previous["bbox"][0])
            <= max(height(line), height(previous)) * 0.5
        )
        if artifact:
            blocks.append(
                {
                    "type": "paragraph",
                    "text": value,
                    "role": "list_marker_artifact",
                    "line_refs": [reference(line)],
                }
            )
            previous = line
            continue
        single_introduced = bool(
            (introduction(lead) or elimination(lead))
            and previous
            and line["bbox"][0] >= previous["bbox"][0]
            and part
            and not part[2]
        )
        indented_bullet = bool(
            part
            and part[1].strip() in set("•●▪◦‣∙·♦◆■○\uf0b7")
            and previous
            and line["bbox"][0] - previous["bbox"][0]
            > max(height(line), height(previous)) * 0.7
        )
        if part and (
            aligned_list
            or (index in supported and not part[2])
            or single_introduced
            or indented_bullet
        ):
            if not blocks or blocks[-1]["type"] != "list":
                blocks.append({"type": "list", "items": [], "role": "other"})
            if part[2]:
                issues.append(
                    "bullet_structure_ambiguous:unexpected_encoded_list_marker_preserved:"
                    f"page_{line['page']}_line_{line['line_id']}"
                )
            blocks[-1]["items"].append(
                {
                    "text": part[0],
                    "line_refs": [reference(line)],
                }
            )
        else:
            prior_lead = (
                next(
                    (
                        b["text"]
                        for b in reversed(blocks[:-1])
                        if b["type"] == "paragraph"
                        and b["role"] != "list_marker_artifact"
                    ),
                    "",
                )
                if current_list
                else ""
            )
            item_paragraph_gap = bool(
                previous
                and previous["page"] == line["page"]
                and line["bbox"][1] - previous["bbox"][3]
                > max(height(line), height(previous)) * 0.7
            )
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
            body_paragraph_start = bool(
                previous
                and paragraph_break
                and value[:1].isupper()
                and previous["text"].rstrip().endswith((".", "?", "!", ")"))
                and any(
                    b["type"] == "paragraph"
                    and b["role"] == "main"
                    and abs(line["bbox"][0] - b["line_refs"][0]["bbox"][0])
                    <= height(line) * 0.35
                    for b in blocks
                )
            )
            hanging = (
                current_list
                and previous
                and not part
                and not standalone_symbol(value)
                and continuation_column(line, start, previous)
                and not introduction(value)
                and not elimination(value)
                and not body_paragraph_start
                and (
                    previous["page"] != line["page"]
                    or elimination(prior_lead)
                    or line["bbox"][1] - previous["bbox"][3]
                    <= max(5, (line["bbox"][3] - line["bbox"][1]) * 0.7)
                )
            )
            if hanging:
                item = blocks[-1]["items"][-1]
                item["text"] += (
                    "\n\n"
                    if item_paragraph_gap
                    or previous["page"] != line["page"]
                    and previous["text"].rstrip().endswith((".", "?", "!"))
                    else "\n"
                ) + value
                item["line_refs"].append(reference(line))
            elif (
                not blocks
                or blocks[-1]["type"] != "paragraph"
                or paragraph_break
                or blocks[-1]["role"] == "list_marker_artifact"
            ):
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
            if standalone_symbol(value) or (
                part and (part[2] or part[1].strip() in set("•●▪◦‣∙·♦◆■○\uf0b7"))
            ):
                issues.append(
                    f"bullet_structure_ambiguous:isolated_marker_without_list_evidence:page_{line['page']}_line_{line['line_id']}"
                )
        previous = line
    analysis = []
    active_lead = active_start = None
    section_labels = set()
    for i, block in enumerate(blocks):
        block["order"] = i + 1
        if block["role"] == "list_marker_artifact":
            continue
        if block["type"] == "paragraph":
            active_lead = block if elimination(block["text"]) else None
            active_start = None
            section_labels = set()
            continue
        ref = block["items"][0]["line_refs"][0]
        this_start = source_lines[(ref["page"], ref["line_id"])]
        if active_start and not same_column(this_start, active_start):
            active_lead = active_start = None
        if active_lead is None:
            continue
        lead = active_lead["text"]
        active_start = this_start
        choices = [CHOICE.match(item["text"]) for item in block["items"]]
        labels = [m[1].upper() for m in choices if m]
        if (
            not labels
            or len(labels) != len(choices)
            or len(set(labels)) != len(labels)
            or correct_answer in labels
            or section_labels.intersection(labels)
        ):
            # The semantic list role is clear, but absent/conflicting letters
            # cannot justify assigning individual items to answer choices.
            active_lead["role"] = "choice_transition"
            block["role"] = "incorrect_choices_unmapped"
            block["transition"] = lead
            # Explicit elimination context and intact source numbering establish
            # the section without inventing letter mappings. Mixed, duplicate,
            # conflicting or malformed labels still require review.
            if (
                labels
                or section_labels
                or not source_numbered_list(block, source_lines)
            ):
                issues.append(
                    "bullet_structure_ambiguous:choice_transition_without_unique_incorrect_labels"
                )
            continue
        active_lead["role"] = "choice_transition"
        block["role"] = "incorrect_choices"
        block["transition"] = lead
        section_labels.update(labels)
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
