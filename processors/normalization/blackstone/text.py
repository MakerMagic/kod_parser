"""Conservative formatting rules; ambiguous encoding is retained, never guessed."""

import re
import unicodedata


def structured_line(line):
    """Lists, numeric rows and isolated symbols must retain their line breaks."""
    return bool(
        re.match(r"^(?:\d+[.)]|[•*\-]|[A-Z][.)])\s", line)
        or len(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", line)) >= 2
        and len(line.split()) <= 12
        or not re.search(r"\w", line)
    )


def _row_kind(line):
    if re.match(r"^(?:\d+[.)]|[•*\-]|[A-Z][.)])\s", line):
        return "list"
    if len(line.split()) > 12 or re.search(r"[.!?]$", line):
        return None
    numbers = re.findall(r"\d+(?:[.,]\d+)?", line)
    if not numbers:
        return None
    if re.search(r"[£$€]\s*\d|\d+(?:[.,]\d+)?\s*(?:p|%)\b", line):
        return "value"
    if re.fullmatch(r"\d+(?:st|nd|rd|th)?(?:\s*\([^)]*\))?", line):
        return "numeric_list"
    if len(numbers) >= 2 or re.search(
        r"(?:\s[-–—:]\s|\b(?:points?|mins?|minutes|hours|days)\b)", line, re.IGNORECASE
    ):
        return "data"
    return None


def _introduced_blocks(lines):
    breaks, protected = set(), set()
    for i, line in enumerate(lines):
        if not line or _row_kind(line):
            continue
        lead = (
            line.endswith(":")
            and len(line.split()) >= 3
            or re.search(
                r"\b(?:following|follows|shown|displayed|below)\b", line, re.IGNORECASE
            )
            and line.endswith((":", "."))
        )
        if not lead:
            continue
        # Allow short table headings, but never skip intervening prose/visuals.
        rows = lines[i + 1 :]
        start = 0
        while start < len(rows) and not rows[start]:
            start += 1
        already_separated = start > 0
        while start < len(rows) and not _row_kind(rows[start]):
            header = rows[start]
            if (
                not header
                or len(header.split()) > 8
                or re.search(
                    r"[.!?:]$|\b(?:is|are|was|were|will|can|could|should|must)\b",
                    header,
                    re.IGNORECASE,
                )
            ):
                break
            start += 1
        if start + 1 >= len(rows):
            continue
        kind = _row_kind(rows[start])
        if kind and _row_kind(rows[start + 1]) == kind:
            if not already_separated:
                breaks.add(i + 1)
            while start < len(rows) and _row_kind(rows[start]) == kind:
                protected.add(i + 1 + start)
                start += 1
    result, mapped = [], set()
    for i, line in enumerate(lines):
        if i in breaks:
            result.append("")
        if i in protected:
            mapped.add(len(result))
        result.append(line)
    return result, mapped


def normalize_text(
    value, *, join_lines=True, separate_blocks=False, wrapped_lead_ins=True
):
    """NFC/common whitespace only; keep paragraphs, lists, tables and hyphens."""
    if not isinstance(value, str):
        return value
    value = unicodedata.normalize(
        "NFC", value.replace("\r\n", "\n").replace("\r", "\n")
    )
    lines = [re.sub(r"[ \t\u00a0]+", " ", line).strip() for line in value.split("\n")]
    protected = set()
    if separate_blocks:
        lines, protected = _introduced_blocks(lines)
    result = []
    for i, line in enumerate(lines):
        if not line:
            if result and result[-1]:
                result.append("")
            continue
        previous = result[-1] if result else ""
        if (
            join_lines
            and i not in protected
            and i - 1 not in protected
            and previous
            and len(previous.split()) >= 4
            and not structured_line(previous)
            and not structured_line(line)
            and not previous.endswith(("-", "–", "—", ":", "?", "!"))
            and line[0].islower()
        ):
            result[-1] += " " + line
        else:
            result.append(line)
    if separate_blocks and wrapped_lead_ins:
        # Joining a wrapped introduction can expose its lead-in phrase. Apply
        # the same evidence rule again without any further prose joining.
        result, _ = _introduced_blocks(result)
    return "\n".join(result).strip()


def artifact_reason(value):
    if not isinstance(value, str):
        return None
    if re.search(r"\(cid:\d+\)|\ufffd|[\ue000-\uf8ff]", value) or any(
        unicodedata.category(char) in {"Cc", "Cs"} and char not in "\t\n\r"
        for char in value
    ):
        return "Encoding tokens/control glyphs have no verified replacement; content retained."
    return None
