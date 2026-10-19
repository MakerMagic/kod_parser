"""BMAT source geometry/ownership regressions; no live acquisition."""

import json
from pathlib import Path

import pytest

from parsers.bmat.encoding import decode_block
from parsers.bmat.parser import ADMIN, split_fields
from parsers.bmat.stabilize import (
    mark_trailing_rules,
    project_visual_text,
    prose_barriers,
)
from parsers.bmat.structure import components, prompt_start


@pytest.mark.parametrize(
    "text,expected",
    [
        ("If these dates are correct, when was the battle?", "If these dates"),
        ("A fact is given. If this is so,\nwhen was the battle?", "If this is so"),
        (
            "A fact is given. It is claimed in the passage that the structure is:",
            "It is claimed",
        ),
        (
            "A schedule is supplied. If Robert works on Friday, then Sheila's nights are",
            "If Robert",
        ),
        (
            "The cupboard has 2.5 litres of milk.\nAfter baking the cake, how many pancakes can I make?",
            "After baking",
        ),
        ("What percentage passes through? (to the nearest 1%)", "What percentage"),
    ],
)
def test_contextual_final_request(text, expected):
    start = prompt_start(text)
    assert start is not None and text[start:].startswith(expected)


@pytest.mark.parametrize(
    "text",
    [
        "The following data are supplied:\n12 14 16",
        "The ingredients are as follows:",
        "A single declarative sentence describes the scene.",
        "Someone asks what happened, but no question is being asked here.",
    ],
)
def test_no_blind_last_sentence_or_colon(text):
    assert prompt_start(text) is None


def test_prompt_only_has_explicit_body_semantics():
    q = {"question_text": "If these dates are correct, when was the battle?"}
    components(q)
    assert q["raw_components"]["main_body"] == "Equals question"
    assert q["raw_components"]["body_equals_question"] is True


@pytest.mark.parametrize(
    "body",
    [
        "If all matter was created at once, galaxies would move apart. However, they collide.",
        "After fifteen minutes Julia counted thirteen sheep. Tim counted their legs.",
        "The table below contains all the relevant figures:\n",
        "After the last event the score returned to:\n",
    ],
)
def test_conditional_body_and_visual_lead_in_do_not_swallow_prompt(body):
    q = {"question_text": body + "\nWhich option follows?"}
    components(q)
    assert q["raw_components"]["main_question"] == "Which option follows?"
    assert q["raw_components"]["main_body"].strip() == body.strip()


@pytest.mark.parametrize(
    "text",
    [
        "END OF TEST",
        "END OF THE TEXT",
        "END OF PAPER",
        "END OF QUESTIONS",
        "________________________",
    ],
)
def test_structural_end_markers(text):
    assert ADMIN.match(text)


@pytest.mark.parametrize(
    "text",
    [
        "At the end of the day, how many remained?",
        "The end of the text is quoted here.",
        "A road leads to the west end.",
    ],
)
def test_real_end_prose_is_preserved(text):
    assert not ADMIN.match(text)


def test_decode_partial_first_line_and_preserve_unknown():
    line = {
        "text": "7 At 7:30(cid:3031)am, the (cid:9999) remains.",
        "cid_substitutions": {"(cid:3031)": " "},
    }
    assert (
        decode_block(line["text"][2:], [line]) == "At 7:30 am, the (cid:9999) remains."
    )


def test_visual_ownership_uses_source_geometry_not_repeated_word_deletion():
    texts = [
        "1 caption",
        "caption",
        "Which item follows?",
        "A First",
        "B Second",
        "C Third",
    ]
    block = "\n".join(texts)
    lines = []
    offset = 0
    for i, t in enumerate(texts):
        lines.append(
            {
                "text": t,
                "block_start": offset,
                "page": 1,
                "x0": 50,
                "x1": 200,
                "top": 50 + i * 20,
                "bottom": 60 + i * 20,
                "word_boxes": [[50, 50 + i * 20, 100, 60 + i * 20]],
                "word_texts": [t],
            }
        )
        offset += len(t) + 1
    end = block.index("A First")
    q = {
        "question_text": block[2:end],
        "raw": {"question_block": block, "options_block": block[end:]},
        "options": [],
        "visual_assets": [
            {
                "image_id": "picture",
                "page": 1,
                "belongs_to": "question",
                "bbox": [40, 65, 210, 85],
                "graphic_bbox": [40, 40, 210, 100],
            }
        ],
    }
    pending = {"lines": lines, "segments": [{"page": 1, "start": 0, "text": block}]}
    project_visual_text(q, pending)
    assert q["question_text"].count("caption") == 1
    assert q["question_text"].startswith("caption")
    assert q["raw"]["question_block"] == block
    assert q["raw"]["visual_text_exclusions"][0]["start"] == len(texts[0]) + 1


def test_paragraph_barrier_includes_wrapped_short_tail_not_internal_label():
    def line(t, x, y):
        return {"text": t, "x0": x, "top": y, "bottom": y + 10}

    lines = [
        line("If two glass sheets are used, how much light passes", 80, 210),
        line("into the room? (to the nearest 1%)", 80, 222),
        line("15% reflected", 160, 160),
    ]
    ids = prose_barriers(lines, [150, 50, 350, 190])
    assert id(lines[0]) in ids and id(lines[1]) in ids
    assert id(lines[2]) not in ids


def test_year_at_start_of_wrapped_prompt_is_not_a_question_number():
    rows = [
        {
            "text": "20 Which one of these charts represents the number of accidents attended in",
            "x0": 55,
            "top": 50,
            "bottom": 61,
            "word_boxes": [[55, 50, 67, 61], [78, 50, 100, 61]],
            "word_texts": ["20", "Which"],
        },
        {
            "text": "2011 by category?",
            "x0": 78,
            "top": 63,
            "bottom": 74,
            "word_boxes": [[78, 63, 100, 74], [103, 63, 115, 74]],
            "word_texts": ["2011", "by"],
        },
    ]
    assert {id(r) for r in rows} <= prose_barriers(rows, [100, 94, 310, 250])


def test_explicit_visual_caption_is_not_a_prose_barrier():
    caption = {
        "text": "Figure 2 shows the complete change in measured pressure over time",
        "x0": 100,
        "top": 210,
        "bottom": 220,
    }
    assert id(caption) not in prose_barriers([caption], [100, 50, 400, 200])


def test_html_refresh_is_atomic_and_retries_only_bounded_sharing_errors(
    tmp_path, monkeypatch
):
    from parsers.bmat import backtest

    path = tmp_path / "question.html"
    path.write_text("old", encoding="utf-8")
    replace = backtest.os.replace
    calls = []

    def transient(source, destination):
        calls.append(1)
        assert path.read_text(encoding="utf-8") == "old"
        if len(calls) < 3:
            raise OSError(22, "Transient report sharing failure")
        replace(source, destination)

    monkeypatch.setattr(backtest.os, "replace", transient)
    monkeypatch.setattr(backtest.time, "sleep", lambda seconds: None)
    backtest.write_html(path, "new")
    assert len(calls) == 3 and path.read_text(encoding="utf-8") == "new"
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("graph_bar", [False, True])
def test_trailing_separator_group_ignores_blank_rows_but_not_neighboring_graph(
    graph_bar,
):
    objects = [
        {"bbox": [140, 500, 440, 500], "page": 1, "notes": [], "decorative": False},
        {"bbox": [140, 500.5, 440, 500.5], "page": 1, "notes": [], "decorative": False},
    ]
    if graph_bar:
        objects.append(
            {"bbox": [180, 480, 200, 500], "page": 1, "notes": [], "decorative": False}
        )
    q = {"question_number": 1, "images": objects}
    data = {
        "questions": [q],
        "pages": [{"width": 600}],
        "extraction": {"expected_questions": 1},
        "shared_information_ranges": [],
    }
    records = [
        {
            "lines": [
                {
                    "page": 1,
                    "text": "D Last complete answer",
                    "top": 450,
                    "bottom": 460,
                },
                {
                    "page": 1,
                    "text": "(cid:3)",
                    "readable_text": " ",
                    "top": 550,
                    "bottom": 560,
                },
            ]
        }
    ]
    mark_trailing_rules(data, records)
    assert objects[0]["decorative"] is (not graph_bar)
    assert objects[1]["decorative"] is (not graph_bar)


def test_conditional_option_text_does_not_hide_complete_answer_set():
    texts = [
        "1 A passage.",
        "Which statement follows?",
        "A First answer.",
        "B Second answer.",
        "C Third answer.",
        "D Fourth answer.",
        "E When a sentence is imposed, it has consequences.",
    ]
    offset = 0
    lines = []
    for t in texts:
        lines.append({"text": t, "x0": 80, "block_start": offset})
        offset += len(t) + 1
    options = split_fields("\n".join(texts), lines)[2]
    assert [o["label"] for o in options] == list("ABCDE")


def test_diagram_letters_before_real_request_are_not_options():
    texts = [
        "1 A map is shown.",
        "A",
        "B",
        "C",
        "D",
        "F",
        "E",
        "G",
        "The locations satisfy these constraints.",
        "Which town is the requested one?",
    ]
    offset = 0
    lines = []
    for t in texts:
        lines.append({"text": t, "x0": 80, "block_start": offset})
        offset += len(t) + 1
    body, _, options, _, _ = split_fields("\n".join(texts), lines)
    assert not options
    assert "Which town" in body


def current(year):
    paths = list(Path("data/raw/bmat").glob(f"bmat_{year}_*.raw.json"))
    assert len(paths) == 1
    return json.loads(paths[0].read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "year,number,labels",
    [
        (2003, 12, "ABCD"),
        (2004, 22, "ABCD"),
        (2009, 3, "ABCDE"),
        (2010, 12, "ABCDE"),
        (2011, 1, "ABCDE"),
        (2012, 3, "ABCDEF"),
        (2012, 14, "ABCDE"),
        (2014, 7, "ABCDEF"),
    ],
)
def test_real_complete_option_image_ownership(year, number, labels):
    q = current(year)["questions"][number - 1]
    assert [o["label"] for o in q["options"]] == list(labels)
    for o in q["options"]:
        assert len(o["images"]) == 1
        a = o["images"][0]
        assert a["belongs_to"] == "option" and a["option_label"] == o["label"]
        box = o["label_bbox"]
        assert a["bbox"][0] <= box[0] and box[2] <= a["bbox"][2]
    assert not any(
        i["code"] in {"option_content_unresolved", "multi_column_options"}
        for i in q["parsing_issues"]
    )


def test_real_prompt_marker_and_whitespace_regressions():
    q = current(2003)["questions"][35]
    assert q["raw_components"]["main_body"] == "Equals question"
    assert "when was" in q["raw_components"]["main_question"]
    assert current(2003)["questions"][37]["raw_components"]["main_question"].startswith(
        "If this is so,"
    )
    assert (
        current(2004)["questions"][12]["raw_components"]["main_question"]
        .rstrip()
        .endswith("is:")
    )
    assert current(2004)["questions"][2]["raw_components"]["main_question"].startswith(
        "What is the smallest"
    )
    q = current(2014)["questions"][34]
    assert "7:30 am" in q["question_text"]
    assert all("END OF TEST" not in o["text"] for o in q["options"])
    assert "END OF TEST" in q["raw"]["question_block"]


def test_real_body_text_crop_and_full_page():
    q = current(2014)["questions"][0]
    assert "Facebook" not in q["question_text"]
    assert "Facebook" in q["raw"]["question_block"]
    assert q["visual_assets"][0]["bbox"][3] < 335
    for y, n in [(2005, 13), (2020, 8)]:
        q = current(y)["questions"][n - 1]
        assert q["raw_components"]["main_question"]
        assert not any(
            "caption" in i["code"] or "unrelated_text" in i["code"]
            for i in q["parsing_issues"]
        )
    q = current(2017)["questions"][17]
    assert q["raw_components"]["main_question"].startswith("After baking")
    assert any(t["type"] == "too long" for t in q["bmat_filter"]["types"])
    q = current(2012)["questions"][19]
    assert q["raw_components"]["main_question"].strip().endswith("2011 by category?")
    assert q["options"][0]["images"][0]["bbox"][1] > 80


def test_real_oriented_axes_and_page_controls_are_owned_upstream():
    for year, n, forbidden in [
        (2005, 24, "setadidnac"),
        (2010, 1, "thgieH"),
        (2019, 31, "27"),
        (2021, 14, "12"),
    ]:
        q = current(year)["questions"][n - 1]
        assert forbidden not in [
            line.strip() for line in q["question_text"].splitlines()
        ]
        assert forbidden in q["raw"]["question_block"]
        assert q["raw"].get("visual_text_exclusions") or q["raw"].get(
            "structural_exclusions"
        )


def test_verified_empty_ink_spacing_not_guessed_math_or_unknown_font():
    d = current(2014)
    for n in [19, 20, 21, 23, 30, 35]:
        q = d["questions"][n - 1]
        assert "(cid:3031)" not in q["question_text"] + "".join(
            o["text"] for o in q["options"]
        )
        assert "(cid:3031)" in q["raw"]["question_block"]
    # The Wingball list marker is now proven by its native outline and list
    # geometry. An unrelated unknown Arial glyph remains unresolved.
    for year, n in [(2017, 28)]:
        assert any(
            i["code"] == "font_encoding_artifacts"
            for i in current(year)["questions"][n - 1]["parsing_issues"]
        )


def test_parenthetical_write_in_is_not_a_failed_image_choice():
    for year, n in [(2005, 21), (2008, 19)]:
        q = current(year)["questions"][n - 1]
        assert any(t["type"] == "No Question" for t in q["bmat_filter"]["types"])
        assert not q["parsing_issues"]
    q = current(2005)["questions"][7]
    assert not any(t["type"] == "No Question" for t in q["bmat_filter"]["types"])
    assert any(i["code"] == "options_not_detected" for i in q["parsing_issues"])
