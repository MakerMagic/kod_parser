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


def normalize_text(value, *, join_lines=True):
    """NFC/common whitespace only; keep paragraphs, lists, tables and hyphens."""
    if not isinstance(value, str):
        return value
    value = unicodedata.normalize(
        "NFC", value.replace("\r\n", "\n").replace("\r", "\n")
    )
    lines = [re.sub(r"[ \t\u00a0]+", " ", line).strip() for line in value.split("\n")]
    result = []
    for line in lines:
        if not line:
            if result and result[-1]:
                result.append("")
            continue
        previous = result[-1] if result else ""
        if (
            join_lines
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
