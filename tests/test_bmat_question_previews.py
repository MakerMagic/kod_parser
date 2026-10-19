"""General source-range, outline-marker and question-only preview regressions."""

import struct
from copy import deepcopy
from types import SimpleNamespace

import pytest

from parsers.bmat.encoding import annotate_lines, round_outline
from parsers.bmat.parser import RANGE
from parsers.bmat.previews import regions


@pytest.mark.parametrize(
    "text",
    [
        "Questions 19–22refer to the following information:",
        "Questions 8 to 11 refer to the following information",
        "Questions 32–35relate to the following passage",
    ],
)
def test_shared_declaration_does_not_require_extraction_whitespace(text):
    assert RANGE.search(text)


def test_range_reference_in_an_ordinary_sentence_is_not_a_declaration():
    assert not RANGE.search("Compare questions 4 and 5 before choosing.")


def test_preview_uses_question_content_not_page_span_and_excludes_controls():
    q = {
        "raw": {"page_spans": [{"page": 1, "bbox": [0, 35, 600, 797]}]},
        "options": [
            {"label": "A", "images": [{"page": 1, "bbox": [80, 400, 250, 500]}]}
        ],
        "visual_assets": [],
        "layout_blocks": [
            {
                "page": 1,
                "type": "text",
                "component": "question_body",
                "text": "18 The real question starts here",
                "bbox": [70, 300, 500, 312],
            },
            {
                "page": 1,
                "type": "text",
                "component": "option",
                "label": "A",
                "text": "A",
                "bbox": [70, 400, 78, 412],
            },
            {
                "page": 1,
                "type": "text",
                "component": "footer",
                "text": "16",
                "bbox": [300, 780, 310, 790],
            },
            {
                "page": 1,
                "type": "text",
                "component": "option",
                "text": "Turn over",
                "bbox": [450, 770, 510, 790],
            },
        ],
    }
    d = {
        "questions": [q],
        "pages": [{"width": 600, "height": 842}],
        "shared_information_ranges": [
            {
                "page": 1,
                "bbox": [50, 90, 500, 110],
                "start_question": 15,
                "end_question": 17,
            }
        ],
    }
    before = deepcopy(q)
    result = regions(d, q)[0]
    assert result["content_bbox"] == [70, 300, 500, 500]
    assert result["bbox"][1] > 280 and result["bbox"][3] < 520
    assert q == before


def test_cross_page_preview_keeps_only_owned_content_on_each_page():
    q = {
        "raw": {"page_spans": [{"page": 1}, {"page": 2}]},
        "options": [],
        "visual_assets": [],
        "layout_blocks": [
            {
                "page": 1,
                "type": "text",
                "component": "question_body",
                "text": "Question starts",
                "bbox": [50, 650, 500, 680],
            },
            {
                "page": 2,
                "type": "text",
                "component": "option",
                "label": "D",
                "text": "D Last option",
                "bbox": [50, 60, 500, 80],
            },
        ],
    }
    d = {
        "questions": [q],
        "pages": [{"width": 600, "height": 842}] * 2,
        "shared_information_ranges": [],
    }
    result = regions(d, q)
    assert (
        len(result) == 2 and result[0]["bbox"][1] > 600 and result[1]["bbox"][3] < 110
    )


def outline_fixture():
    # One native round glyph; no Unicode cmap or CID/character-number assumption.
    glyph = bytes.fromhex(
        "0001000000d302db03ae000b0021b9000301b4400e0907001a0d06190c0def212938182b2b4ee410e6003f4ded313001140623222635343633321602dbd69798d6d69897d6024198d6d69897d6d6"
    )
    raw = bytearray(128 + len(glyph))
    struct.pack_into(">H", raw, 18, 2048)
    struct.pack_into(">h", raw, 50, 0)
    struct.pack_into(">HH", raw, 64, 0, len(glyph) // 2)
    raw[128:] = glyph
    ttf = SimpleNamespace(
        tables={b"head": (0, 54), b"loca": (64, 4), b"glyf": (128, len(glyph))}
    )
    return raw, ttf


def test_native_outline_proves_small_filled_circle_not_a_guessed_cid():
    raw, ttf = outline_fixture()
    assert round_outline(raw, ttf, 0)["point_count"] == 12
    struct.pack_into(">h", raw, 128, 2)
    assert round_outline(raw, ttf, 0) is None


@pytest.mark.parametrize(
    "lead,proven,decode",
    [
        ("Goals are:", True, True),
        ("Goals are listed.", True, False),
        ("Goals are:", False, False),
    ],
)
def test_bullet_interpretation_requires_native_shape_repetition_and_list_context(
    monkeypatch, lead, proven, decode
):
    from parsers.bmat import encoding

    lines = [
        {
            "text": lead,
            "top": 20,
            "bottom": 30,
            "x0": 50,
            "x1": 300,
            "word_texts": [lead],
        }
    ]
    for i in range(3):
        lines.append(
            {
                "text": "(cid:9) a goal",
                "top": 40 + 15 * i,
                "bottom": 50 + 15 * i,
                "x0": 80,
                "x1": 300,
                "word_texts": ["(cid:9)", "a", "goal"],
            }
        )
    original = [l["text"] for l in lines]
    page = SimpleNamespace(
        chars=[
            {
                "text": "(cid:9)",
                "fontname": "native",
                "top": l["top"],
                "bottom": l["bottom"],
                "x0": 80,
                "x1": 87,
            }
            for l in lines[1:]
        ]
    )
    monkeypatch.setattr(
        encoding,
        "font_maps",
        lambda _: (
            {},
            [
                {
                    "font": "native",
                    "unmapped_round_glyphs": [{"cid": 9}] if proven else [],
                }
            ],
        ),
    )
    annotate_lines(page, lines, False, lambda s: s)
    assert all(l["readable_text"].startswith("•") == decode for l in lines[1:])
    assert [l["text"] for l in lines] == original
