"""Recover readable text from the shifted CID fonts in some exam PDFs.

The original pdfplumber output remains in page and question raw spans. This
module only supplies readable structured fields when the page shows the
character-code pattern used by the embedded Arial subsets.
"""

import re

CID = re.compile(r"\(cid:(\d+)\)")
# These glyphs were checked against the rendered source pages. Ordinary ASCII
# glyphs use their Unicode code point minus 29 in the affected font subsets.
SPECIAL = {
    122: "•",
    131: "°",
    133: "£",
    139: "©",
    177: "–",
    179: "“",
    180: "”",
    181: "‘",
    182: "’",
}
ENGLISH_EVIDENCE = (
    "(cid:87)(cid:75)(cid:72)",  # the
    "(cid:68)(cid:81)(cid:71)",  # and
    "(cid:82)(cid:73)",  # of
)


def supports_shifted_cids(raw_text, character_count):
    """Gate the mapping on a dominant CID font and repeated language evidence."""
    tokens = len(CID.findall(raw_text))
    return (
        tokens >= 20
        and tokens / max(character_count, 1) > 0.5
        and any(pattern in raw_text for pattern in ENGLISH_EVIDENCE)
    )


def decode_cids(value):
    """Decode verified glyph codes, retaining unknown tokens for review."""

    def glyph(match):
        code = int(match[1])
        if 3 <= code <= 97:
            return chr(code + 29)
        return SPECIAL.get(code, match[0])

    return CID.sub(glyph, value)
