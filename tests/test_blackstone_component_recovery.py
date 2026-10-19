"""General structural regressions, without source/question-ID runtime rules."""

from types import SimpleNamespace

import pytest

from parsers.blackstone.image_options import option_cell_owner, partition_option_objects
from parsers.blackstone.parser import _split_fields
from processors.normalization.blackstone.structure import completion_prompt_span


def anchors():
    return [
        {"label": label, "bbox": [x, y, x + 8, y + 11], "page": 1, "label_only": True}
        for label, x, y in (
            ("A", 80, 260),
            ("B", 317, 260),
            ("C", 80, 409),
            ("D", 317, 409),
            ("E", 80, 580),
        )
    ]


def test_near_following_anchor_does_not_claim_a_contained_composite():
    owner = option_cell_owner([350, 263, 495, 397], anchors(), 1)
    assert owner["label"] == "B"
    assert option_cell_owner([350, 263, 495, 430], anchors(), 1) is None
    assert option_cell_owner([140, 100, 210, 230], anchors(), 1) is None
    assert option_cell_owner([140, 280, 400, 380], anchors(), 1) is None


def test_incomplete_or_text_choice_anchors_cannot_force_visual_ownership():
    assert option_cell_owner([350, 263, 495, 397], anchors()[:-1], 1) is None
    text = [{**a, "label_only": False} for a in anchors()]
    assert option_cell_owner([350, 263, 495, 397], text, 1) is None


@pytest.mark.parametrize("blank_band", [True, False])
def test_native_raster_objects_need_a_blank_anchor_band_to_separate(blank_band):
    objects = [
        {"image_id": "upper", "kind": "raster", "bbox": [142, 259, 238, 406]},
        {"image_id": "lower", "kind": "raster", "bbox": [149, 400, 257, 567]},
    ]
    group = {"bbox": [142, 259, 257, 567], "objects": objects}
    bitmap = SimpleNamespace(width=600, height=800, stride=1800)
    pixels = bytes([255 if blank_band else 0]) * (bitmap.stride * bitmap.height)
    result = partition_option_objects(group, anchors(), 1, bitmap, pixels, (600, 800))
    if not blank_band:
        assert result is None
        return
    assert [g["option_override"] for g in result] == ["A", "C"]
    assert result[0]["bbox"][3] <= result[1]["bbox"][1]
    assert result[0]["objects"][0] == objects[0]
    assert result[1]["objects"][0] == objects[1]
    assert objects[1]["bbox"][1] == 400  # Never rewrite source object geometry.


def test_one_shared_drawing_crossing_options_stays_unresolved():
    group = {
        "bbox": [142, 259, 257, 567],
        "objects": [
            {"image_id": "shared", "kind": "vector", "bbox": [142, 259, 257, 567]}
        ],
    }
    assert (
        partition_option_objects(
            group, anchors(), 1, SimpleNamespace(width=600, height=800), b"", (600, 800)
        )
        is None
    )


def split(lines):
    block, records, offset = "\n".join(t for t, _ in lines), [], 0
    for text, readable in lines:
        records.append(
            {"text": text, "readable_text": readable, "x0": 80, "block_start": offset}
        )
        offset += len(text) + 1
    return block, _split_fields(block, records)


def test_decoded_label_rows_recover_boundary_after_encoded_body_words():
    block, (body, choices, options, _, _) = split(
        [
            ("1 Entry prices are shown.", "1 Entry prices are shown."),
            ("(cid:36)dults £7", "Adults £7"),
            ("(cid:38)hildren £4", "Children £4"),
            ("Which chart represents visitors?", "Which chart represents visitors?"),
            ("(cid:36) (cid:37)", "A B"),
            ("(cid:38) (cid:39)", "C D"),
            ("(cid:40)", "E"),
        ]
    )
    assert "(cid:36)dults £7" in body and "Which chart" in body
    assert [o["label"] for o in options] == list("ABCDE")
    assert choices.startswith("(cid:36) (cid:37)") and choices in block


def test_complete_aligned_text_answers_outrank_letters_inside_diagrams():
    _, (body, _, options, _, warnings) = split(
        [
            ("1 The cube has lettered faces.", "1 The cube has lettered faces."),
            ("A E A", "A E A"),
            ("Which two views are possible?", "Which two views are possible?"),
            *[
                (f"{label} {i} and {i + 1}", f"{label} {i} and {i + 1}")
                for i, label in enumerate("ABCDE", 1)
            ],
        ]
    )
    assert "A E A" in body and "Which two views" in body
    assert [o["label"] for o in options] == list("ABCDE")
    assert not warnings


@pytest.mark.parametrize(
    "prompt,values",
    [
        (
            "If Alex works on Friday, then the nights when Robin works are",
            [
                "Monday, Tuesday, Thursday.",
                "Monday, Tuesday, Friday.",
                "Monday, Wednesday, Friday.",
            ],
        ),
        (
            "If all packages are used, then the total number of containers is",
            ["12", "14", "18"],
        ),
    ],
)
def test_unpunctuated_conditional_completion_requires_parallel_answers(prompt, values):
    text = "All workers follow the supplied restrictions.\n" + prompt
    q = {
        "question_text": text,
        "options": [{"label": label, "text": t} for label, t in zip("ABC", values)],
    }
    span = completion_prompt_span(q)
    assert text[slice(*span)] == prompt


@pytest.mark.parametrize(
    "tail",
    [
        "The workers are",
        "The guard worked on Monday.",
        "If the conditions hold, then the data shown below are",
        "If the guard is working, then the following table is",
    ],
)
def test_final_body_line_or_data_leadin_is_not_a_completion_prompt(tail):
    q = {
        "question_text": "There are three workers.\n" + tail,
        "options": [
            {"label": label, "text": value}
            for label, value in zip("ABC", ("12", "14", "18"))
        ],
    }
    assert completion_prompt_span(q) is None
