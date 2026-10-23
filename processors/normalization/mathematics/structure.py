"""Source-backed prose reflow and lossless context/task projection for CLEAN.

Math, images and lists are opaque tokens while detecting prose grammar. Their
contents are never converted to strings or rewritten by boundary detection.
"""

import re
from copy import deepcopy
from itertools import pairwise

from processors.normalization.blackstone.text import normalize_text, structured_line

VERSION = "5"
MARKER = "\ue000"
LIST = re.compile(r"^\s*(?:[IVX]+[.)]|\(?\d+[.)]|[•*–-]|[A-Z][.)])\s+")
REQUEST = re.compile(
    r"\b(?:what\b|which\b|how\s+(?:many|much|old|long)\b|when\s+will\b|"
    r"where\s+does\b|"
    r"(?:find|calculate|determine|evaluate|simplify|factorise|factorize|solve|"
    r"express|rearrange|describe|make|write|expand)\b|work\s+out\b|"
    r"use\b[^.!?\n]*?\bto\s+find\b|get\s+a\s+number\b)",
    re.IGNORECASE,
)
IMPERATIVE = re.compile(
    r"^(?:find|calculate|determine|evaluate|simplify|factorise|factorize|solve|"
    r"express|rearrange|describe|make|write|expand|work\s+out|use|get\s+a\s+number)\b",
    re.IGNORECASE,
)


def token_ledger(blocks):
    """Non-whitespace prose characters and exact math/assets/list structure.

    Used to prove that reflow/splitting has not lost, duplicated or rewritten
    any content; unlike a display hash this ignores PDF whitespace and metadata.
    """
    result = []
    for block in blocks:
        kind = block["type"]
        if kind == "text":
            value = re.sub(r"\s+", "", block["text"])
            if result and result[-1][0] == "text":
                result[-1] = ("text", result[-1][1] + value)
            elif value:
                result.append(("text", value))
        elif kind == "math":
            result.append((kind, block["latex"], block["display"]))
        elif kind == "visual":
            result.append((kind, block["asset_id"]))
        elif kind == "list":
            result.append(
                (
                    kind,
                    block.get("ordered"),
                    tuple(tuple(token_ledger(i["content"])) for i in block["items"]),
                )
            )
        else:
            result.append((kind,))
    return result


def _without_visuals(blocks):
    """Return the ordered text/math/list projection, omitting visual blocks."""
    result = []
    for block in blocks:
        if block["type"] == "visual":
            continue
        if block["type"] == "list":
            copied = deepcopy(block)
            copied["items"] = []
            for item in block["items"]:
                content = _without_visuals(item["content"])
                if content:
                    copied["items"].append({**deepcopy(item), "content": content})
            if copied["items"]:
                result.append(copied)
        else:
            result.append(deepcopy(block))
    return result


def _visual_ledger(blocks):
    """Return visual asset IDs in source order, including nested list items."""
    result = []
    for block in blocks:
        if block["type"] == "visual":
            result.append(block.get("asset_id"))
        elif block["type"] == "list":
            for item in block["items"]:
                result.extend(_visual_ledger(item["content"]))
    return result


def projection_is_lossless(original, body, question):
    """Check content preservation while permitting visuals to move to body.

    CLEAN deliberately owns this component rule: body visuals are allowed to be
    lifted out of a task sentence, while non-visual tokens and visual asset
    order must remain unchanged.
    """
    projected = body + (question or [])
    return (
        token_ledger(_without_visuals(original))
        == token_ledger(_without_visuals(projected))
        and _visual_ledger(original) == _visual_ledger(projected)
        and not _visual_ledger(question or [])
    )


def body_owns_visuals(body, question):
    """Move every question visual to Main Body without editing prompt text/math."""
    body = deepcopy(body)
    question = deepcopy(question) if question is not None else None
    if question is None:
        return body, None

    visuals = []

    def strip(blocks):
        result = []
        for block in blocks:
            if block["type"] == "visual":
                visuals.append(deepcopy(block))
            elif block["type"] == "list":
                copied = deepcopy(block)
                copied["items"] = []
                for item in block["items"]:
                    content = strip(item["content"])
                    if content:
                        copied["items"].append({**deepcopy(item), "content": content})
                if copied["items"]:
                    result.append(copied)
            else:
                result.append(deepcopy(block))
        return result

    question = strip(question)
    body.extend(visuals)
    return body, question or None


def _line_boxes(block, glyphs):
    source = block.get("source", {})
    values = [
        glyphs[g]
        for g in source.get("glyph_ids", [])
        if g in glyphs and glyphs[g]["text"].strip()
    ]
    rows = []
    for glyph in sorted(values, key=lambda g: (g["top"], g["x0"])):
        row = next((r for r in rows if abs(r[0]["top"] - glyph["top"]) < 2), None)
        if row is None:
            row = []
            rows.append(row)
        row.append(glyph)
    lines = [s for s in block["text"].splitlines() if s.strip()]
    if len(rows) != len(lines):
        return []
    result = []
    for text, row in zip(lines, rows):
        row.sort(key=lambda g: g["x0"])
        actual = "".join(g["text"] for g in row)
        if re.sub(r"\s+", "", text) != re.sub(r"\s+", "", actual):
            return []  # Never align uncertain geometry to a partial text block.
        result.append(
            [
                min(g["x0"] for g in row),
                min(g["top"] for g in row),
                max(g["x1"] for g in row),
                max(g["bottom"] for g in row),
            ]
        )
    return result


def _prose(line):
    return len(re.findall(r"[A-Za-z]{2,}", line)) >= 2


def _bare_math_line(line):
    return bool(
        re.fullmatch(
            r"(?:d[xyztu]|(?:sin|cos|tan|cot|sec|csc|log|ln|tg|ctg)(?:[xyz]|\([^)]*\)|[0-9.+-]+)?)[()]*",
            line.strip(),
        )
    )


def reflow_text(block, glyphs):
    """Join only prose wraps; retain paragraphs, source lists and aligned rows."""
    value = block["text"]
    if all(structured_line(s.strip()) for s in value.splitlines() if s.strip()) and any(
        re.search(r"\S[ \t]{2,}\S", s) for s in value.splitlines()
    ):
        return value
    lines = value.split("\n")
    boxes = _line_boxes(block, glyphs)
    pitches = [b[1] - a[1] for a, b in pairwise(boxes) if b[1] > a[1]]
    # The minimum regular pitch distinguishes paragraph gaps from line wraps,
    # including two-line paragraphs whose only gap is already a paragraph gap.
    pitch = min(pitches) if pitches else None
    result, previous, previous_box, index = [], "", None, 0
    protected = set()
    # Source-introduced unnumbered lists/constraints are semantic rows too.
    introduced = False
    for i, line in enumerate(lines):
        if introduced and line.strip():
            protected.add(i)
        if re.search(
            r"(?:following restrictions|following conditions|as follows)\s*:\s*$",
            line,
            re.IGNORECASE,
        ):
            introduced = True
        if introduced and REQUEST.search(line):
            introduced = False
            protected.discard(i)
    for i, line in enumerate(lines):
        current = line.strip()
        box = boxes[index] if current and boxes else None
        if current:
            index += 1
        if not current:
            result.append("")
            previous, previous_box = "", None
            continue
        terminal_stem = current == 'EXCEPT' and bool(re.search(r'\bfollowing\s*$', previous, re.I))
        variable_continuation = bool(
            re.search(r'\b(?:is|are|If|if)\s*$', previous)
            and re.fullmatch(r'[A-Za-z]{1,3}[?.]?', current)
            and re.search(r'\b[A-Za-z]{2,}\b', previous)
        )
        semantic = bool(
            LIST.match(current)
            or LIST.match(previous)
            or i in protected
            or i - 1 in protected
            or re.match(r"^(?:Width|Depth|Height)\s+", current)
            or re.match(r"^(?:Width|Depth|Height)\s+", previous)
            or (structured_line(current) and re.search(r"\S[ \t]{2,}\S", line))
            or (len(previous.split()) < 3 and previous.isupper())
            or (len(current.split()) < 3 and current.isupper() and len(current) > 1 and not terminal_stem and not variable_continuation)
            or _bare_math_line(previous)
            or _bare_math_line(current)
        )
        geometry_wrap = False
        paragraph = False
        if previous_box and box and pitch:
            h = max(previous_box[3] - previous_box[1], box[3] - box[1])
            delta = box[1] - previous_box[1]
            paragraph = (
                delta > min(1.4 * pitch, 1.85 * h) or box[0] > previous_box[0] + h * 1.2
            )
            geometry_wrap = 0 < delta <= min(1.4 * pitch, 1.85 * h) and not paragraph
        connector = bool(
            re.search(
                r"\b(?:and|or|of|the|a|an|from|to|for|with|between|formula)\s*$",
                previous,
                re.IGNORECASE,
            )
        )
        continuation = bool(
            previous
            and not semantic
            and not paragraph
            and (
                re.search(r"[A-Za-z]{2,}", previous)
                and re.search(r"[A-Za-z]{2,}", current)
                or connector
                or variable_continuation
                or terminal_stem
            )
            and re.search(r"[A-Za-z]", previous)
            and re.search(r"[A-Za-z]", current)
            and not previous.endswith((":", "?", "!"))
            and (
                geometry_wrap
                or current[0].islower()
                or variable_continuation
                or terminal_stem
                or connector
                and not REQUEST.match(current)
            )
        )
        if (
            previous in {",", "-"}
            and not semantic
            and current[0].islower()
            and _prose(current)
        ):
            continuation = True
        if (
            previous in {".", ",", ";"}
            and geometry_wrap
            and not semantic
            and _prose(current)
        ):
            continuation = True
        if continuation:
            result[-1] += " " + current
        else:
            if paragraph and result and result[-1]:
                result.append("")
            result.append(current)
        previous, previous_box = current, box
    normalized = "\n".join(
        line
        if structured_line(line.strip()) and re.search(r"\S[ \t]{2,}\S", line)
        else normalize_text(line, join_lines=False)
        for line in result
    )
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    # Keep cross-block separators, not PDF-wrap newlines at fragment boundaries.
    if value[:1].isspace():
        row_start = bool(
            re.match(
                r"^(?:[IVX]+[.)]|\(?\d+[.)]?|Width|Depth|Height)\s+", value.lstrip()
            )
        )
        normalized = (
            "\n\n"
            if value.startswith("\n\n")
            else "\n"
            if "\n" in value[: len(value) - len(value.lstrip())] and row_start
            else " "
        ) + normalized
    if value[-1:].isspace():
        normalized += (
            "\n\n"
            if value.endswith("\n\n")
            else "\n"
            if "\n" in value[len(value.rstrip()) :] and value.rstrip().endswith(":")
            else " "
        )
    return normalized


def reflow(blocks, glyphs=None):
    result = deepcopy(blocks)
    glyphs = glyphs or {}
    for i, block in enumerate(result):
        if block["type"] == "text":
            block["text"] = reflow_text(block, glyphs)
        elif block["type"] == "list":
            for item in block["items"]:
                item["content"] = reflow(item["content"], glyphs)
        if not i or not block.get("break_before"):
            continue
        previous = result[i - 1]
        if previous["type"] in {"visual", "list"} or block["type"] in {
            "visual",
            "list",
        }:
            continue
        if block.get("display") or previous.get("display"):
            continue
        a, b = previous.get("text", "").rstrip(), block.get("text", "").lstrip()
        # A mathematical block following an unfinished prose fragment is inline;
        # two adjacent mathematical rows remain separate equations.
        inline = (
            previous["type"] == "text"
            and (re.search(r"[A-Za-z]{2,}", a) or a == "," and block["type"] == "text")
            and not a.endswith((".", "?", "!", ":"))
            and (block["type"] == "math" or b[:1].islower())
        ) or (
            previous["type"] == "math" and block["type"] == "text" and b[:1].islower()
        )
        if inline:
            block.pop("break_before", None)
            if previous["type"] == "text" and not previous["text"][-1:].isspace():
                previous["text"] += " "
    return result


def projection(blocks):
    parts, spans, offset = [], [], 0
    for index, block in enumerate(blocks):
        value = block["text"] if block["type"] == "text" else MARKER
        # Source punctuation attached to a formula is still a sentence boundary;
        # it is observed here, never removed from or added to the LaTeX block.
        if block["type"] == "math":
            ending = re.search(r"(?<!\\)([.!,;])\s*$", block["latex"])
            if ending:
                value += ending[1]
        parts.append(value)
        spans.append((offset, offset + len(value), index))
        offset += len(value)
    return "".join(parts), spans


def _sentence_start(text, position):
    starts = [0] + [
        m.end()
        for m in re.finditer(r"[.!?](?:\s+|(?=" + MARKER + r"))", text[:position])
    ]
    return starts[-1]


def prompt_start(text):
    candidates = []
    for match in REQUEST.finditer(text):
        start = match.start()
        word = match[0].lower()
        sentence = _sentence_start(text, start)
        prefix = text[sentence:start]
        suffix = text[start:]
        if IMPERATIVE.match(word):
            # Exclude reported/contextual verbs, not just matching task keywords.
            if (
                prefix.strip()
                and not re.search(
                    r"(?:[,:;]\s*|\bthen\s+|\band\s+|\bto\s+|[\n]\s*)$",
                    prefix,
                    re.IGNORECASE,
                )
                and text[start : start + 1].islower()
                and not re.match(r"\s*(?:If|Given|Using)\b", prefix, re.IGNORECASE)
                and not re.fullmatch(r"[\s" + MARKER + r"]*", prefix)
            ):
                continue
            if re.search(
                r"\b(?:to|will|can|could|must|should|would|asked to)\s*$",
                prefix,
                re.IGNORECASE,
            ):
                continue
            if not suffix[len(match[0]) :].strip(" .:\n"):
                continue
        else:
            if word == "what" and not re.match(
                r"what\s+(?:is|are|will|was|were|would|should|could|can|do|does|percent|fraction|percentage)\b",
                suffix,
                re.IGNORECASE,
            ):
                continue
            if word == "which" and not re.match(
                r"which\s+(?:of|one|pair|value|expression|formula|number|point|lake)\b",
                suffix,
                re.IGNORECASE,
            ):
                continue
            if re.search(
                r"\b(?:know|knows|known|ask|asked|wonder|wondered|shows?|indicates?)\s*$",
                prefix,
                re.IGNORECASE,
            ):
                continue
            # A source sentence such as "The result is what percent ...?" is
            # itself the task, whereas a preceding conditional is supporting data.
            if re.search(
                r"\b(?:is|was|were|are|receives?|includes?|equals?|has|have)\s*$",
                prefix,
                re.IGNORECASE,
            ) and not re.match(
                r"\s*(?:If|Assum|Given|When|Using)\b", prefix, re.IGNORECASE
            ):
                start = sentence
            # Keep prepositional qualifiers that are part of the request.
            qualifier = re.search(
                r"\b(?:by|for|in|at)\s*$", text[:start], re.IGNORECASE
            )
            if qualifier:
                start = qualifier.start()
        candidates.append(start)
    if candidates:
        # The first genuine request owns any subsequent answer instructions,
        # mathematical rows, numbered claims or parenthetical qualifications.
        return min(candidates), "explicit_request"
    # Source prompts can be declarative stems completed by the answer options.
    tail = text.rstrip(" \n" + MARKER)
    if re.search(
        r"\b(?:is|are|was|will be|would be|could be|must be|EXCEPT|divisible by|dimensions|an integer if)(?:\s*[….:]+)?\s*$",
        tail,
        re.IGNORECASE,
    ):
        end = len(tail.rstrip(". …:"))
        start = _sentence_start(text, end)
        leads = list(
            re.finditer(
                r"\b(?:The|That|This|Then)\s+(?:simple form|value|area|equation|sum|result|common factor|computer answer)\b",
                text[start:end],
            )
        )
        if leads:
            start += leads[-1].start()
        if re.search(r"[A-Za-z]{2,}", text[start:]):
            return start, "answer_completed_request"
    marks = [m.start() for m in re.finditer(r"\?", text)]
    if marks:
        start = _sentence_start(text, marks[-1])
        if len(re.findall(r"[A-Za-z]{2,}", text[start : marks[-1]])) >= 3:
            return start, "interrogative_sentence"
    return None, "no_separate_source_request"


def split(blocks):
    text, spans = projection(blocks)
    start, reason = prompt_start(text)
    if start is None:
        return deepcopy(blocks), None, reason
    body, prompt = [], []
    for lo, hi, index in spans:
        block = blocks[index]
        if hi <= start:
            body.append(deepcopy(block))
        elif lo >= start:
            prompt.append(deepcopy(block))
        else:
            for target, value, span in (
                (body, block["text"][: start - lo], [0, start - lo]),
                (prompt, block["text"][start - lo :], [start - lo, hi - lo]),
            ):
                if value.strip():
                    fragment = deepcopy(block)
                    fragment["text"] = value
                    fragment["clean_text_span"] = span
                    target.append(fragment)
    body, prompt = body_owns_visuals(body, prompt or None)
    if not projection_is_lossless(blocks, body, prompt):
        raise ValueError("Context/task boundary lost or duplicated source content")
    return body, prompt, reason
