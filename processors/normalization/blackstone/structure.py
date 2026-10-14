"""Derived display structure backed by stored text and raw layout references."""

import re
from copy import deepcopy
from itertools import pairwise
from math import isfinite

from parsers.blackstone.cid_text import decode_cids

from .text import _row_kind, artifact_reason, normalize_text

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


def _question_marks(text):
    depth, positions = 0, []
    for i, char in enumerate(text):
        depth += char == "("
        depth -= char == ")"
        if depth < 0:
            return None
        if char == "?" and depth == 0:
            positions.append(i)
    return positions if depth == 0 else None


def _explanatory_tail(text):
    """Only balanced parenthetical notes and punctuation may follow the prompt."""
    text = text.strip()
    while text.startswith("("):
        depth = 0
        for i, char in enumerate(text):
            depth += char == "("
            depth -= char == ")"
            if depth == 0:
                text = text[i + 1 :].lstrip(" .;\n\t")
                break
        else:
            return False
    return not text


def _prompt_grammar(text):
    sentence = re.sub(r"\s+", " ", text).strip()
    if PROMPT.match(sentence):
        return True
    word = re.search(
        r"\b(?:which|what|how|who|where|when|why)\b", sentence, re.IGNORECASE
    )
    if not word or not sentence[0].isupper():
        return False
    prefix = sentence[: word.start()]
    if re.search(
        r"\b(?:ask(?:ed|s)?|wonder(?:ed|s)?|said|says|reported|discussed)\b",
        prefix,
        re.IGNORECASE,
    ):
        return False
    if re.match(
        r"^(?:If|Assuming|Given|According to|Based (?:on|upon)|Using|Depending on|Approximately)\b",
        prefix,
    ):
        return True
    return bool(
        re.match(r"^(?:At|By|During|For|From|In|Of|On|To|Over|After|Before)\b", prefix)
        and not re.search(
            r"\b(?:is|are|was|were|has|have|had|will|would|can|could|should|must)\b",
            prefix,
            re.IGNORECASE,
        )
    )


def _statement_request(text):
    """Period-ended requests need imperative or interrogative grammar evidence."""
    sentence = re.sub(r"\s+", " ", text).strip()
    if re.match(r"^(?:Select|Choose|Identify|Determine|Calculate)\b", sentence):
        return len(sentence.split()) >= 4
    word = re.search(
        r"\b(?:which|what|how|who|where|when|why)\b", sentence, re.IGNORECASE
    )
    if not word:
        return False
    clause = sentence[word.end() :]
    verb = re.search(
        r"\b(?:is|are|was|were|can|could|should|would|will|must|do|does|did|has|have)\b",
        clause,
        re.IGNORECASE,
    )
    return bool(
        verb
        and not re.search(
            r"\b(?:I|we|he|she|they|you|it)\b", clause[: verb.start()], re.IGNORECASE
        )
    )


def tail_prompt_span(text, options):
    """Fallback for a unique sentence-aware answer request at the text tail."""
    labels = [o.get("label") for o in options]
    if (
        len(labels) < 2
        or any(not isinstance(label, str) or not label.strip() for label in labels)
        or len(set(labels)) != len(labels)
    ):
        return None
    if artifact_reason(text):
        return None
    marks = _question_marks(text)
    if marks is None or len(marks) > 1:
        return None
    end = len(text.rstrip())
    if marks:
        terminal = marks[0]
        if not _explanatory_tail(text[terminal + 1 :]):
            return None
    else:
        # Imperative/interrogative statements require an actual terminator,
        # not an unfinished stem that the options are expected to complete.
        if not text[:end].endswith((".", ")")):
            return None
        terminal = end - 1
    starts = {
        0,
        *(m.end() for m in re.finditer(r"[.!?]\s+|\n[ \t]*", text[: terminal + 1])),
    }
    candidates = []
    for start in sorted(starts):
        while start < end and text[start].isspace():
            start += 1
        candidate = text[start:end]
        core = text[start : terminal + 1]
        if not candidate or not _prompt_grammar(core):
            continue
        if re.search(r"[.!]\s+[A-Z]", core):
            continue  # Do not absorb a complete preceding setup sentence.
        rows = [line.strip() for line in core.splitlines() if line.strip()]
        if re.search(r":\s*\n", core) or any(
            _row_kind(a) and _row_kind(a) == _row_kind(b) for a, b in pairwise(rows)
        ):
            continue  # A lead-in/data block is body context, not a long prompt.
        if not marks and not _statement_request(core):
            continue
        candidates.append(start)
    if not candidates:
        return None
    # Wrapped fragments are one request only without a paragraph/sentence
    # boundary between them. Competing requests remain unresolved.
    first = candidates[0]
    if any(
        re.search(r"[.!?]\s+|\n\s*\n", text[first:start]) for start in candidates[1:]
    ):
        return None
    return first, end


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
    # Reuse the upstream VERIFIED map only as an equality view of raw evidence.
    # Never guess a font map or trust equal line counts: CID-only spaces and
    # graph-owned lines omitted upstream make counts differ legitimately.
    mapping, cursor = {}, 0
    for b in blocks:
        value = b.get("text", "")
        if decoded:
            span = b["raw_span"]
            end = span.get("end")
            if (
                not isinstance(value, str)
                or type(end) is not int
                or not 0 <= span["start"] <= end <= boundary
                or block[span["start"] : end] != value
            ):
                return None
            value = decode_cids(value)
        if b["raw_span"]["start"] == 0:
            # A standalone question-number anchor is metadata. It is absent
            # from structured body text, unlike a numeric line inside the body.
            if value.strip() == str(question.get("question_number")):
                continue
            value = re.sub(rf"^{question.get('question_number')}\s+", "", value)
        if not value.strip():
            continue  # An exact blank/decoded space is not a supplied text line.
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
    legacy = prompt_range(lines)
    prompt = (
        (lines[legacy[0]]["span"]["start"], lines[legacy[1] - 1]["span"]["end"])
        if legacy
        else tail_prompt_span(text, question.get("options") or [])
        if lines
        else None
    )
    if legacy and text[prompt[1] :].strip() and _explanatory_tail(text[prompt[1] :]):
        prompt = prompt[0], len(text.rstrip())
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

    def add_line(i, evidence=None, *, visual=False, owners=None):
        span = lines[i]["span"]
        cuts = sorted(
            {
                span["start"],
                span["end"],
                *(p for p in (prompt or ()) if span["start"] < p < span["end"]),
            }
        )
        for start, end in pairwise(cuts):
            target = (
                "main_question"
                if prompt and prompt[0] <= start and end <= prompt[1]
                else "main_body"
            )
            if visual and target != "main_question":
                target = "visual"
            entry = {
                "line_index": i,
                "structured_span": {"start": start, "end": end},
                "destination": target,
            }
            if evidence:
                entry.update(
                    source_block=evidence,
                    asset_ids=owners if target == "visual" else [],
                )
            accounting.append(entry)
            if target == "main_body" and text[start:end].strip():
                body.append(
                    {
                        "type": "text",
                        "text": text[start:end],
                        "source_blocks": [evidence] if evidence else [],
                        "line_indices": [i],
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
            add_line(i)
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
            )
            if visual_text:
                # Trust existing ownership only with consistent page/bounds
                # and unambiguous body assets, never merely nearby matching text.
                owned = [assets[a] for a in owners]
                box = block.get("bbox")
                boxes = [a.get("bbox") for a in owned]
                visual_text = (
                    isinstance(box, list)
                    and len(box) == 4
                    and all(isinstance(b, list) and len(b) == 4 for b in boxes)
                    and all(
                        type(v) in (int, float) and isfinite(v)
                        for b in [box, *boxes]
                        for v in b
                    )
                    and all(
                        a.get("page") == block.get("page")
                        and a.get("belongs_to") == "question"
                        and (a.get("placement") or {}).get("component")
                        not in ("unknown", "option")
                        and not any(
                            w.startswith(
                                (
                                    "visual_component_association_uncertain",
                                    "visual_multiple_option_images_merged",
                                    "visual_coordinate_space",
                                    "visual_crop_",
                                    "visual_neighbor_boundary_uncertain",
                                    "visual_question_boundary_overlap",
                                )
                            )
                            for w in a.get("warnings", [])
                        )
                        for a in owned
                    )
                    and min(b[0] for b in boxes) <= box[0]
                    and min(b[1] for b in boxes) <= box[1]
                    and max(b[2] for b in boxes) >= box[2]
                    and max(b[3] for b in boxes) >= box[3]
                )
            span = lines[i]["span"]
            has_body_text = bool(text[span["start"] : span["end"]].strip())
            if prompt:
                has_body_text = bool(
                    text[span["start"] : min(span["end"], prompt[0])].strip()
                    or text[max(span["start"], prompt[1]) : span["end"]].strip()
                )
            if (
                block.get("component") == "visual_label"
                and not visual_text
                and has_body_text
            ):
                issue(
                    "visual_text_ownership_unresolved",
                    "main_body",
                    "Stored visual-text ownership lacks safe body asset/page/bounds evidence; text retained for review.",
                )
            add_line(i, evidence, visual=visual_text, owners=owners)
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
            block["text"] = normalize_text(block["text"], separate_blocks=True)
    for i, line in enumerate(lines):
        parts = sorted(
            (a["structured_span"] for a in accounting if a["line_index"] == i),
            key=lambda p: p["start"],
        )
        if (
            not parts
            or parts[0]["start"] != line["span"]["start"]
            or parts[-1]["end"] != line["span"]["end"]
            or any(a["end"] != b["start"] for a, b in pairwise(parts))
        ):
            raise ValueError(
                "Cleaning structure failed to partition every supplied text line"
            )
    return (
        merged,
        normalize_text(text[prompt[0] : prompt[1]]) if prompt else None,
        accounting,
    )
