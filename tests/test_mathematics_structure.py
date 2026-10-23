"""Cleaning-owned context/task boundaries and source-faithful prose reflow."""

from copy import deepcopy

import pytest

from processors.normalization.mathematics.structure import (
    MARKER,
    projection,
    reflow,
    split,
    token_ledger,
)


def prose(value, **extra):
    return {"type": "text", "text": value, **extra}


def formula(value, **extra):
    return {"type": "math", "latex": value, "display": False, **extra}


def test_wrapped_prose_joins_without_blind_newline_removal():
    blocks = [
        prose(
            "The length of each side of the square is increased\nby fifty percent.\n\nA new paragraph remains here."
        )
    ]
    assert (
        reflow(blocks)[0]["text"]
        == "The length of each side of the square is increased by fifty percent.\n\nA new paragraph remains here."
    )
    assert token_ledger(blocks) == token_ledger(reflow(blocks))


def test_geometry_joins_capitalized_wrap_and_preserves_paragraph_gap():
    lines = [
        "The students travelled from Oxford to",
        "London in two hours.",
        "Another journey took three hours.",
    ]
    glyphs, ids = {}, []
    for i, (text, top) in enumerate(zip(lines, (10, 24, 50))):
        name = f"g{i}"
        glyphs[name] = {
            "text": text,
            "top": top,
            "bottom": top + 10,
            "x0": 20,
            "x1": 200,
        }
        ids.append(name)
    block = prose("\n".join(lines), source={"glyph_ids": ids})
    assert (
        reflow([block], glyphs)[0]["text"]
        == "The students travelled from Oxford to London in two hours.\n\nAnother journey took three hours."
    )


def test_lists_data_rows_and_equations_are_not_flattened():
    blocks = [
        prose(
            "The following restrictions:\nCharles must stand in the middle.\nAretha must stand at the left.\nI. The first claim.\nII. The second claim."
        ),
        prose("Width 48 cm\nDepth 44 cm\nHeight 52 cm"),
        prose("1  2  3\n4  5  6"),
        formula("x+y=3", break_before=True),
        formula("x-y=1", break_before=True),
        {
            "type": "list",
            "items": [
                {"content": [prose("First item")]},
                {"content": [formula("x^2")]},
            ],
        },
    ]
    assert reflow(blocks) == blocks


@pytest.mark.parametrize(
    "task_text",
    ["What is the value of ", "Find ", "Calculate ", "Determine ", "Solve for "],
)
def test_request_ending_in_formula_separates_losslessly(task_text):
    blocks = [
        prose("A quantity is given. " + task_text),
        formula(r"\sqrt{\frac{x^{2}+1}{y_{1}}}"),
    ]
    before = deepcopy(blocks)
    body, prompt, reason = split(blocks)
    assert projection(body)[0] == "A quantity is given. "
    assert projection(prompt)[0].startswith(task_text)
    assert prompt[-1] == blocks[-1]
    assert token_ledger(body + prompt) == token_ledger(blocks)
    assert blocks == before and reason == "explicit_request"


def test_context_with_formulas_is_not_absorbed_into_prompt():
    blocks = [
        prose("Let "),
        formula("f(x)=x^2"),
        prose(" and "),
        formula("g(x)=x-1"),
        prose("Which of the following is equivalent to "),
        formula(r"\frac{f(x)}{g(x)}"),
        prose("?"),
    ]
    body, prompt, _ = split(blocks)
    assert body == blocks[:4]
    assert prompt == blocks[4:]


def test_math_punctuation_and_two_step_task_preserved():
    blocks = [
        prose("The lines meet at "),
        formula("(2,3)."),
        prose(" Calculate "),
        formula("a+b"),
        prose(". Give your answer in standard form."),
    ]
    body, prompt, _ = split(blocks)
    assert body == blocks[:2]
    assert prompt[0]["text"].strip() == "Calculate"
    assert prompt[-1] == blocks[-1]
    assert token_ledger(body + prompt) == token_ledger(blocks)


def test_display_math_and_text_image_order_survive_boundary_projection():
    image = {"type": "visual", "asset_id": "diagram", "break_before": True}
    system = formula(
        r"\begin{cases}x+y=3\\x-y=1\end{cases}", display=True, break_before=True
    )
    blocks = [
        prose("Given these equations:"),
        system,
        image,
        prose("Find the value of "),
        formula("x"),
    ]
    body, prompt, _ = split(reflow(blocks))
    assert body == blocks[:3] and prompt == blocks[3:]
    assert token_ledger(body + prompt) == token_ledger(blocks)


def test_visual_after_question_start_is_owned_by_body_without_losing_prompt_math():
    image = {"type": "visual", "asset_id": "supporting_diagram"}
    blocks = [
        prose("A shape has the following dimensions. "),
        prose("Find the area of "),
        image,
        formula(r"\frac{1}{2}bh", break_before=True),
        prose(" in square units."),
    ]
    body, question, _ = split(blocks)
    assert [b for b in body if b["type"] == "visual"] == [image]
    assert all(b["type"] != "visual" for b in question)
    assert projection(question)[0] == "Find the area of " + MARKER + " in square units."
    from processors.normalization.mathematics.structure import projection_is_lossless

    assert projection_is_lossless(blocks, body, question)


def test_visuals_nested_in_prompt_lists_are_lifted_to_body_in_order():
    from processors.normalization.mathematics.structure import body_owns_visuals

    question = [
        prose("Which figure matches this description?"),
        {
            "type": "list",
            "ordered": False,
            "items": [
                {"content": [prose("first"), {"type": "visual", "asset_id": "a"}]},
                {"content": [{"type": "visual", "asset_id": "b"}, prose("second")]},
            ],
        },
    ]
    body, prompt = body_owns_visuals([], question)
    assert [b["asset_id"] for b in body] == ["a", "b"]
    assert all(b["type"] != "visual" for b in prompt)
    assert prompt[1]["items"][0]["content"] == [prose("first")]
    assert prompt[1]["items"][1]["content"] == [prose("second")]


def test_false_inline_break_cleared_but_math_not_rewritten():
    blocks = [
        prose("A cone has a height of "),
        formula(r"2\sqrt{x}", break_before=True),
        prose(" units."),
    ]
    result = reflow(blocks)
    assert "break_before" not in result[1]
    assert result[1]["latex"] == blocks[1]["latex"]
    assert token_ledger(result) == token_ledger(blocks)


def test_fragmented_units_rows_and_list_prefixes_survive_reflow():
    blocks = [
        prose("A safe has dimensions:\nWidth "),
        formula("48"),
        prose(" cm\nDepth "),
        formula("44"),
        prose(" cm\nHeight "),
        formula("52"),
    ]
    result = reflow(blocks)
    assert "\nDepth " in result[2]["text"]
    assert "\nHeight " in result[4]["text"]
    assert token_ledger(result) == token_ledger(blocks)
    assert reflow([prose(" milk\nbottles, ")])[0]["text"] == " milk bottles, "
    assert (
        reflow([prose("determined by the formula\np ")])[0]["text"]
        == "determined by the formula p "
    )
    for fragment in ("dx\ndy)", "sinx\ncosx"):
        assert reflow([prose(fragment)])[0]["text"] == fragment


def test_inline_comma_does_not_force_next_prose_line():
    blocks = [
        prose("The spring has length "),
        formula("l"),
        prose(", "),
        prose("radius ", break_before=True),
        formula("r"),
    ]
    assert "break_before" not in reflow(blocks)[3]


def test_layout_change_invalidates_clean_cache_even_if_question_is_unchanged():
    from processors.normalization.mathematics.cleaner import clean_question, reusable

    raw = {
        "id": "q",
        "issues": [],
        "extraction_status": "extracted",
        "assets": [],
        "content": [prose("Find the value.", source={"glyph_ids": ["g"]})],
        "options": [
            {"label": label, "content": [formula("1")]} for label in ("A", "B")
        ],
    }
    glyphs = {
        "g": {"text": "Find the value.", "top": 10, "bottom": 20, "x0": 0, "x1": 100}
    }
    clean = clean_question(raw, {}, glyphs=glyphs)
    assert reusable(clean, raw, glyphs=glyphs)
    changed = deepcopy(glyphs)
    changed["g"]["top"] = 12
    assert not reusable(clean, raw, glyphs=changed)


@pytest.mark.parametrize(
    "blocks",
    [
        [formula(r"\sqrt{2}+1=?")],
        [prose("For all "), formula("x"), prose(", "), formula("x+x=")],
        [formula(r"\begin{cases}x+y=3\\x-y=1\end{cases}", display=True)],
    ],
)
def test_genuine_no_separate_prompt_stays_null(blocks):
    body, prompt, reason = split(blocks)
    assert body == blocks and prompt is None
    assert reason == "no_separate_source_request"


def test_existing_correct_boundary_is_preserved():
    from processors.normalization.mathematics.cleaner import clean_question

    raw = {
        "id": "q",
        "issues": [],
        "extraction_status": "extracted",
        "assets": [],
        "content": [prose("Context. "), prose("Find x.")],
        "main_body": [prose("Context. ")],
        "main_question": [prose("Find x.")],
        "options": [
            {"label": label, "content": [formula("1")]} for label in ("A", "B")
        ],
    }
    result = clean_question(raw, {})
    assert result["main_body"] == raw["main_body"]
    assert result["main_question"] == raw["main_question"]
    assert result["content_structure"]["decision"] == "preserved_explicit_boundary"
    false_null = deepcopy(raw)
    false_null["main_body"] = false_null["content"]
    false_null["main_question"] = None
    recovered = clean_question(false_null, {})
    assert recovered["main_question"] is not None
    assert projection(recovered["main_question"])[0] == "Find x."


def test_explicit_boundary_visual_moves_to_body_but_question_text_stays():
    from processors.normalization.mathematics.cleaner import clean_question

    image = {"type": "visual", "asset_id": "diagram"}
    raw = {
        "id": "q-image-boundary",
        "issues": [],
        "extraction_status": "extracted",
        "assets": [{"id": "diagram"}],
        "content": [prose("Context. "), prose("Find x. "), image, formula("x")],
        "main_body": [prose("Context. ")],
        "main_question": [prose("Find x. "), image, formula("x")],
        "options": [
            {"label": label, "content": [formula("1")]} for label in ("A", "B")
        ],
    }
    result = clean_question(raw, {})
    assert [b["asset_id"] for b in result["main_body"] if b["type"] == "visual"] == ["diagram"]
    assert all(b["type"] != "visual" for b in result["main_question"])
    assert projection(result["main_question"])[0] == "Find x. " + MARKER


def test_review_migration_requires_exact_math_and_character_conservation():
    from categorization.core import digest
    from categorization.mathematics.bindings import rebind_structure
    from categorization.mathematics.core import semantic_content

    old = {
        "id": "q",
        "assets": [],
        "content": [prose("Find the\nvalue of "), formula(r"\sqrt{x}")],
        "options": [],
    }
    new = {**old, "content": reflow(old["content"])}
    decision = {
        "status": "needs_review",
        "reason": "A taxonomy boundary",
        "issue_code": "taxonomy_boundary",
    }
    old_hash = digest(semantic_content(old))
    reviews = {"assessments": {old_hash: decision}}
    categorized = {
        "questions": [{"id": "q", "content_sha256": old_hash, "assessment": decision}]
    }
    migrated = rebind_structure(
        reviews, {"questions": [old]}, {"questions": [new]}, categorized
    )
    assert migrated["assessments"][digest(semantic_content(new))] == decision
    bad = deepcopy(new)
    bad["content"][-1]["latex"] = r"\sqrt{x+1}"
    with pytest.raises(ValueError, match="meaning"):
        rebind_structure(
            reviews, {"questions": [old]}, {"questions": [bad]}, categorized
        )
