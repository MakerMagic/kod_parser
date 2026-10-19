"""Conservative formatting rules; ambiguous encoding is retained, never guessed."""

import re
import unicodedata
from itertools import pairwise
from math import isfinite
from statistics import median


def _capitalized_wrap(previous, line, before, after, context, on_unresolved):
    """Capitalization is neutral: require unfinished prose AND continuous layout."""
    if (
        re.search(r"[.!?;:][\"'’”\])]*$", previous)
        or previous.startswith("[")
        or re.match(
            r"^(?:Which|What|How|Why|Who|Where|When|Select|Choose|Identify|Determine|Calculate)\b",
            line,
        )
        or re.match(r"^The (?:above|following)\b", line)
        or re.fullmatch(r"[A-Z][.)]?", line)
        or not any(word[0].islower() for word in previous.split() if word)
        or (line.isupper() and len(line.split()) > 2)
    ):
        return False
    connector = bool(
        re.search(
            r"\b(?:a|an|the|and|or|of|in|on|at|to|from|with|by|for|into|as|that|than|such|its|their|his|her|our|my)\s*$",
            previous,
            re.IGNORECASE,
        )
    )
    if not before or not after:
        if connector and on_unresolved:
            on_unresolved(
                "Capitalized continuation follows an unfinished phrase, but verified raw line geometry is unavailable; line break retained."
            )
        return False
    if (
        before.get("page") != after.get("page")
        or before.get("component") != after.get("component")
        or before.get("component") not in {"stimulus", "question_body"}
        or not isinstance(before.get("order"), int)
        or after.get("order") != before["order"] + 1
    ):
        return False  # Page, graphic, component and option boundaries are barriers.
    a, b = before.get("bbox"), after.get("bbox")
    if not all(
        isinstance(box, list)
        and len(box) == 4
        and all(type(v) in (int, float) and isfinite(v) for v in box)
        and box[0] < box[2]
        and box[1] < box[3]
        for box in (a, b)
    ):
        if connector and on_unresolved:
            on_unresolved(
                "Possible prose wrap has invalid raw line coordinates; line break retained."
            )
        return False
    h1, h2 = a[3] - a[1], b[3] - b[1]
    if max(h1, h2) > min(h1, h2) * 1.35:
        return False
    peers = [
        c
        for c in context
        if c
        and c.get("page") == before["page"]
        and c.get("component") == before["component"]
        and isinstance(c.get("bbox"), list)
        and len(c["bbox"]) == 4
        and all(type(v) in (int, float) and isfinite(v) for v in c["bbox"])
    ]
    pitches = [
        d["bbox"][1] - c["bbox"][1]
        for c, d in pairwise(peers)
        if 0.75 * h1 <= d["bbox"][1] - c["bbox"][1] <= 1.6 * h1
    ]
    pitch = median(pitches) if len(pitches) >= 2 else max(h1, h2) * 1.2
    if not 0.75 * min(h1, h2) <= b[1] - a[1] <= 1.35 * pitch:
        return False  # Additional paragraph spacing is not a wrapped line.
    if abs(b[0] - a[0]) > max(h1, h2) * 0.75 and not before.get(
        "initial_question_anchor"
    ):
        return False
    if re.match(r"^(If|Each|For|When|On|In)\b", previous) and (
        previous.split()[0] == line.split()[0]
        and re.search(r"\d", previous)
        and re.search(r"\d", line)
    ):
        return False  # Repeated conditional/data rows, not a single sentence.
    left = min((c["bbox"][0] for c in peers), default=a[0])
    right = max((c["bbox"][2] for c in peers), default=a[2])
    filled_line = a[2] - a[0] >= (right - left) * 0.8
    return connector or filled_line


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
    value,
    *,
    join_lines=True,
    separate_blocks=False,
    wrapped_lead_ins=True,
    contextual_wraps=False,
    line_context=None,
    on_unresolved=None,
    recover_modal_joins=False,
    recover_auxiliary_joins=False,
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
    supplied = (
        line_context
        if line_context and len(line_context) == sum(bool(line) for line in lines)
        else []
    )
    evidence = iter(supplied)
    context = []
    for line in lines:
        entry = next(evidence, None) if line else None
        if (
            entry
            and re.sub(
                r"[ \t\u00a0]+",
                " ",
                unicodedata.normalize("NFC", entry.get("text", "")),
            ).strip()
            != line
        ):
            entry = (
                None  # Never align a partial prompt/body fragment by line count alone.
            )
        context.append(entry)
    result = []
    legacy_previous = ""
    for i, line in enumerate(lines):
        if not line:
            if result and result[-1]:
                result.append("")
            legacy_previous = ""
            continue
        # Keep existing lowercase decisions independent of newly joined names;
        # otherwise joining a short proper-name line can accidentally enable
        # another, previously disallowed join at the next paragraph.
        previous = legacy_previous
        if (
            join_lines
            and i not in protected
            and i - 1 not in protected
            and previous
            and len(previous.split()) >= 4
            and not structured_line(previous)
            and not structured_line(line)
            and not previous.endswith(("-", "–", "—", ":", "?", "!"))
            and (
                line[0].islower()
                or contextual_wraps
                and line[0].isupper()
                and _capitalized_wrap(
                    lines[i - 1],
                    line,
                    context[i - 1],
                    context[i],
                    context,
                    on_unresolved,
                )
            )
        ):
            result[-1] += " " + line
            legacy_previous = previous + " " + line if line[0].islower() else line
        else:
            result.append(line)
            legacy_previous = line
    if separate_blocks and wrapped_lead_ins:
        # Joining a wrapped introduction can expose its lead-in phrase. Apply
        # the same evidence rule again without any further prose joining.
        result, _ = _introduced_blocks(result)
    result = "\n".join(result).strip()
    if recover_modal_joins:
        # A closed grammatical combination inside an answer request, not a
        # general dictionary splitter. Original extraction remains in RAW.
        result = re.sub(
            r"(\b(?:Which|What)\b[^?!.:\n]*?\b)(would|could|should|might)"
            r"(weaken|strengthen|undermine|support|challenge)"
            r"(?=\s+(?:(?:the|this|that|a|an)\s+)?(?:(?:above|following)\s+)?"
            r"(?:argument|reasoning|claim|conclusion)\b)",
            r"\1\2 \3",
            result,
            flags=re.IGNORECASE,
        )
    if recover_auxiliary_joins:
        result = re.sub(
            r"(\b(?:Which|What)\b[^?!.:\n]*?\b)(is|are|was|were|does|do)(not)"
            r"(?=\s+(?:true|false|possible|correct|consistent)\b)",
            r"\1\2 \3",
            result,
            flags=re.IGNORECASE,
        )
    return result


def artifact_reason(value):
    if not isinstance(value, str):
        return None
    if re.search(r"\(cid:\d+\)|\ufffd|[\ue000-\uf8ff]", value) or any(
        unicodedata.category(char) in {"Cc", "Cs"} and char not in "\t\n\r"
        for char in value
    ):
        return "Encoding tokens/control glyphs have no verified replacement; content retained."
    return None
