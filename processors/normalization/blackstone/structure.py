"""Derived display structure backed by stored text and raw layout references."""

import re
from copy import deepcopy

from .text import normalize_text

PROMPT = re.compile(
    r"^(?:Which|What|How|Why|Who|Where|When|Is|Are|Does|Do|Can|Could|"
    r"Should|Would|Will|Select|Choose|Identify|Determine|Calculate)\b"
)


def text_lines(text):
    result, offset = [], 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if content.strip():
            result.append(
                {
                    "text": content,
                    "span": {"start": offset, "end": offset + len(content)},
                }
            )
        offset += len(line)
    return result


def prompt_range(lines):
    """Require one explicit, complete prompt, not merely a final sentence."""
    candidates = [
        i for i, line in enumerate(lines) if PROMPT.match(line["text"].strip())
    ]
    complete = []
    for start in candidates:
        for end in range(start, len(lines)):
            if end > start and end in candidates:
                break
            text = lines[end]["text"].strip()
            if "?" in text:
                if text.endswith("?") and text.count("?") == 1:
                    complete.append((start, end + 1))
                break
    return complete[0] if len(complete) == 1 else None


def _line_mapping(question, lines):
    raw = question.get("raw") or {}
    block = raw.get("question_block", "")
    option_text = raw.get("options_block", "")
    boundary = len(block) - len(option_text)
    blocks = sorted(
        [
            b
            for b in question.get("layout_blocks", [])
            if b.get("type") == "text"
            and b.get("component") != "option"
            and isinstance(b.get("raw_span", {}).get("start"), int)
            and b["raw_span"]["start"] < boundary
        ],
        key=lambda b: b["raw_span"]["start"],
    )
    decoded = any(
        note.startswith("Structured text decoded from a verified shifted CID font")
        for note in raw.get("extraction_notes", [])
        if isinstance(note, str)
    )
    # Use upstream's already decoded structured lines, never infer a CID map.
    if decoded and len(blocks) == len(lines):
        return {b["block_id"]: i for i, b in enumerate(blocks)}
    mapping, cursor = {}, 0
    for b in blocks:
        value = b.get("text", "")
        if b["raw_span"]["start"] == 0:
            value = re.sub(rf"^{question.get('question_number')}\s+", "", value)
        if cursor < len(lines) and normalize_text(
            value, join_lines=False
        ) == normalize_text(lines[cursor]["text"], join_lines=False):
            mapping[b["block_id"]] = cursor
            cursor += 1
        elif b.get("component") != "visual_label":
            return None
    return mapping if cursor == len(lines) else None


def build_structure(question, issue):
    text = question.get("question_text")
    if not isinstance(text, str) or not text.strip():
        issue(
            "question_text_unavailable",
            "question_text",
            "No readable structured question text was supplied.",
        )
        lines = []
    else:
        lines = text_lines(text)
    prompt = prompt_range(lines)
    if prompt is None:
        issue(
            "ambiguous_body_question_split",
            "main_question",
            "No single complete explicit prompt; all supplied context retained in Main Body.",
        )
    assets = {a["image_id"]: a for a in question.get("visual_assets", [])}
    option_ids = {
        a.get("image_id")
        for o in (question.get("options") or [])
        for a in (o.get("images") or [])
    }
    mapping = _line_mapping(question, lines) if lines else {}
    layout = question.get("layout_blocks") or []
    body, accounting, used = [], [], set()

    def destination(i):
        return "main_question" if prompt and prompt[0] <= i < prompt[1] else "main_body"

    def add_text(indices, evidence=None):
        target = destination(indices[0])
        original = "\n".join(lines[i]["text"] for i in indices)
        if target != "main_question":
            body.append(
                {
                    "type": "text",
                    "text": original,
                    "source_blocks": evidence or [],
                    "line_indices": indices,
                }
            )

    def add_asset(asset, block=None):
        identifier = asset["image_id"]
        if identifier in used or identifier in option_ids:
            return
        used.add(identifier)
        component = (asset.get("placement") or {}).get(
            "component", asset.get("belongs_to")
        )
        if component in ("unknown", "option") or asset.get("belongs_to") == "option":
            issue(
                "visual_placement_unresolved",
                "main_body",
                "Asset has no reliable displayed option/body placement; preserved without reassignment.",
                asset.get("path"),
            )
        body.append(
            {
                "type": "visual",
                "asset_id": identifier,
                "raw_component": component,
                "source_blocks": [block] if block else [],
            }
        )

    if mapping is None or not layout:
        if assets:
            issue(
                "layout_alignment_unresolved",
                "main_body",
                "Readable structured text cannot be fully aligned to raw layout; text and all assets retained, visual insertion order requires review.",
            )
        for i in range(len(lines)):
            add_text([i])
            accounting.append(
                {
                    "line_index": i,
                    "structured_span": lines[i]["span"],
                    "destination": destination(i),
                }
            )
        for asset in question.get("visual_assets", []):
            add_asset(asset)
    else:
        orders = [b.get("order") for b in layout]
        if orders != list(range(1, len(orders) + 1)):
            issue(
                "layout_ordering_unresolved",
                "main_body",
                "Stored layout order is not contiguous; supplied order preserved.",
            )
        for block in layout:
            evidence = {
                key: deepcopy(block.get(key))
                for key in ("block_id", "page", "raw_span", "bbox", "order")
            }
            if block.get("type") == "visual":
                asset = assets.get(block.get("asset_id"))
                if asset:
                    add_asset(asset, evidence)
                else:
                    issue(
                        "broken_visual_block_reference",
                        "main_body",
                        "Layout references a visual not present in visual_assets.",
                    )
                continue
            i = mapping.get(block.get("block_id"))
            if i is None:
                continue
            owners = block.get("asset_ids") or []
            visual_text = (
                block.get("component") == "visual_label"
                and owners
                and all(a in assets for a in owners)
                and destination(i) != "main_question"
            )
            target = "visual" if visual_text else destination(i)
            accounting.append(
                {
                    "line_index": i,
                    "structured_span": lines[i]["span"],
                    "destination": target,
                    "source_block": evidence,
                    "asset_ids": owners if visual_text else [],
                }
            )
            if not visual_text:
                add_text([i], [evidence])
        for asset in question.get("visual_assets", []):
            if asset["image_id"] not in used and asset["image_id"] not in option_ids:
                issue(
                    "visual_ordering_unresolved",
                    "main_body",
                    "Asset absent from layout; retained after text for review.",
                    asset.get("path"),
                )
                add_asset(asset)
    # Merge only consecutive textual blocks. A graphic remains a real boundary.
    merged = []
    for block in body:
        if merged and block["type"] == merged[-1]["type"] == "text":
            previous = merged[-1]
            if block["line_indices"][0] == previous["line_indices"][-1] + 1:
                gap = text[
                    lines[previous["line_indices"][-1]]["span"]["end"] : lines[
                        block["line_indices"][0]
                    ]["span"]["start"]
                ]
                separator = "\n\n" if re.search(r"\n[ \t]*\n", gap) else "\n"
                previous["text"] += separator + block["text"]
                previous["source_blocks"].extend(block["source_blocks"])
                previous["line_indices"].extend(block["line_indices"])
                continue
        merged.append(block)
    for i, block in enumerate(merged, start=1):
        block["order"] = i
        if block["type"] == "text":
            block["text"] = normalize_text(block["text"])
    if sorted(a["line_index"] for a in accounting) != list(range(len(lines))):
        raise ValueError(
            "Cleaning structure failed to account for all supplied text lines"
        )
    return (
        merged,
        normalize_text(
            text[
                lines[prompt[0]]["span"]["start"] : lines[prompt[1] - 1]["span"]["end"]
            ]
        )
        if prompt
        else None,
        accounting,
    )
