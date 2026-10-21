"""Layout/context regressions for source explanation ownership, not matching."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from parsers.explained_answers.parser import validate_answers
from parsers.explained_answers.structure import structure
from processors.matching.backtest import inspect_question, render_inspection
from processors.matching.report import write_report

ROOT = Path(__file__).resolve().parents[1]
CONTROL_HASHES = {
    (2014, 6): "2fd8217c0af42faf3ab67a3d83260cf254fc8eb42b788b786dcb8e7d781c6581",
    (2015, 31): "8889c5cda5a0c345b316f482591fb14a24185592f6d96307cb2f77a94aa064b9",
    (2016, 1): "706e4197fc8983e0c26f1233b61a0121ec4e0e6348b3a98c9aa0cb8f349b68ae",
}


def lines(rows):
    offset, result = 0, []
    for index, (page, x, y, value) in enumerate(rows, 1):
        result.append(
            {
                "page": page,
                "line_id": index,
                "text": value,
                "bbox": [x, y, x + max(5, len(value) * 5), y + 12],
                "start": offset,
                "end": offset + len(value),
            }
        )
        offset += len(value) + 1
    return result


def test_isolated_attached_marker_is_not_a_list_on_its_own():
    explanation, warnings = structure(
        lines(
            [
                (1, 40, 0, "The main reasoning begins."),
                (1, 40, 20, "• The argument continues normally"),
                (1, 40, 36, "without introducing a separate list."),
            ]
        ),
        "E",
    )
    assert not explanation["other_lists"]
    assert "• The argument continues normally" in explanation["main_explanation"]
    assert any("isolated_marker_without_list_evidence" in w for w in warnings)


def test_confirmed_standalone_artifact_keeps_raw_reference():
    source = lines(
        [
            (1, 40, 0, "The values are as follows:"),
            (1, 40, 20, "♦"),
            (2, 60, 0, "• first value"),
            (2, 60, 16, "• second value"),
            (3, 40, 0, "The main explanation resumes here."),
        ]
    )
    explanation, warnings = structure(source, "E")
    artifact = explanation["blocks"][1]
    assert artifact["role"] == "list_marker_artifact"
    assert (
        artifact["text"] == "♦"
        and artifact["line_refs"][0]["start"] == source[1]["start"]
    )
    assert "♦" not in explanation["main_explanation"]
    assert len(explanation["other_lists"][0]["items"]) == 2
    assert "The main explanation resumes" in explanation["main_explanation"]
    assert not warnings


@pytest.mark.parametrize("symbol", ["©", "�", "♦"])
def test_unconfirmed_symbol_is_not_silently_discarded(symbol):
    source = lines(
        [
            (1, 40, 0, "The calculation continues:"),
            (1, 40, 20, symbol),
            (1, 40, 36, "This is ordinary explanatory prose."),
        ]
    )
    explanation, warnings = structure(source, "E")
    assert symbol in explanation["main_explanation"]
    assert not explanation["other_lists"] and warnings


def test_attached_real_marker_preserves_item_content_and_paragraphs():
    explanation, warnings = structure(
        lines(
            [
                (1, 40, 0, "Let us look at why the other options are wrong:"),
                (1, 70, 20, "♦ A- First reasoning paragraph."),
                (1, 70, 62, "A second paragraph explains this same choice."),
                (1, 70, 100, "♦ B- A different wrong choice."),
            ]
        ),
        "E",
    )
    assert [i["label"] for i in explanation["choice_analysis"]] == ["A", "B"]
    assert "\n\nA second paragraph" in explanation["choice_analysis"][0]["text"]
    assert not explanation["other_lists"] and not warnings


def test_incorrect_section_persists_across_separate_list_blocks():
    explanation, warnings = structure(
        lines(
            [
                (1, 40, 0, "Let us consider why the other answers are wrong:"),
                (1, 70, 20, "A- First incorrect choice."),
                (1, 70, 36, "B- Second incorrect choice."),
                (1, 70, 52, "♦"),
                (2, 70, 0, "• C- Third incorrect choice."),
                (2, 70, 16, "• D- Fourth incorrect choice."),
                (2, 40, 45, "Additional facts are as follows:"),
                (2, 65, 65, "• an independent fact"),
                (2, 65, 81, "• another independent fact"),
            ]
        ),
        "E",
    )
    assert [i["label"] for i in explanation["choice_analysis"]] == ["A", "B", "C", "D"]
    assert (
        len(
            [
                b
                for b in explanation["bulleted_blocks"]
                if b["role"] == "incorrect_choices"
            ]
        )
        == 2
    )
    assert len(explanation["other_lists"]) == 1
    assert "independent fact" in explanation["other_lists"][0]["items"][0]["text"]
    assert not warnings


def test_numbered_incorrect_items_wrap_across_pages_without_inventing_labels():
    explanation, warnings = structure(
        lines(
            [
                (1, 40, 0, "Let us look at why the other answer choices are wrong:"),
                (1, 50, 20, "1. First reasoning begins"),
                (2, 60, 0, "and continues on the next page."),
                (2, 50, 20, "2. Second reasoning begins"),
                (2, 60, 36, "and has a hanging continuation."),
            ]
        ),
        "A",
    )
    assert not explanation["other_lists"]
    block = explanation["bulleted_blocks"][0]
    assert block["role"] == "incorrect_choices_unmapped" and len(block["items"]) == 2
    assert "hanging continuation" in block["items"][1]["text"]
    assert not explanation["choice_analysis"] and not warnings


@pytest.mark.parametrize(
    "items",
    [
        ["1. First reason.", "3. Missing ordinal."],
        ["1. First reason.", "1. Duplicate ordinal."],
        ["2. First reason.", "3. Missing first item."],
        ["1. First reason.", "B- Mixed label."],
        ["• First reason.", "• No source option identifiers."],
    ],
)
def test_ambiguous_elimination_identifiers_remain_flagged(items):
    explanation, warnings = structure(
        lines(
            [(1, 40, 0, "Let us look at why the other options are wrong:")]
            + [(1, 60, 20 + 16 * i, value) for i, value in enumerate(items)]
        ),
        "A",
    )
    assert not explanation["choice_analysis"]
    assert any(
        "choice_transition_without_unique_incorrect_labels" in w for w in warnings
    )


def test_calculation_list_is_not_elimination_just_because_prior_sentence_is():
    explanation, warnings = structure(
        lines(
            [
                (
                    1,
                    40,
                    0,
                    "This eliminates two answer choices. Now consider the sums as follows:",
                ),
                (1, 40, 20, "♦ If 3 is removed, the sum is 18"),
                (1, 40, 36, "♦ If 5 is removed, the sum is 16"),
            ]
        ),
        "A",
    )
    assert len(explanation["other_lists"][0]["items"]) == 2
    assert not explanation["choice_analysis"] and not warnings


def test_legitimate_one_item_list_has_independent_introduction_evidence():
    explanation, warnings = structure(
        lines(
            [
                (1, 40, 0, "Keep the following note:"),
                (1, 65, 20, "• a legitimate separate list item"),
                (1, 40, 45, "The explanation resumes."),
            ]
        ),
        "E",
    )
    assert len(explanation["other_lists"][0]["items"]) == 1
    assert "The explanation resumes." in explanation["main_explanation"]
    assert not warnings


def test_reverse_hanging_list_does_not_swallow_main_paragraph():
    explanation, warnings = structure(
        lines(
            [
                (1, 44, 0, "The criteria are as follows:"),
                (1, 44, 20, "- An attendance figure must be adequate"),
                (1, 26, 36, "according to the target (including exceptions)."),
                (1, 44, 52, "- Another figure must be adequate"),
                (1, 26, 68, "according to the rule (including exceptions)"),
                (1, 44, 84, "We can now determine the answer."),
            ]
        ),
        "E",
    )
    assert len(explanation["other_lists"][0]["items"]) == 2
    assert "including exceptions)" in explanation["other_lists"][0]["items"][1]["text"]
    assert "We can now determine the answer." in explanation["main_explanation"]
    assert not warnings


def input_lines(data, answer):
    header = answer["raw"]["header"]
    return [
        l
        for span in answer["raw"]["page_spans"]
        for l in data["pages"][span["page"] - 1]["lines"]
        if span["start"] <= l["start"] < span["end"]
        and (l["page"], l["line_id"]) != (header["page"], header["line_id"])
    ]


@pytest.fixture(scope="module")
def corpus():
    files = list((ROOT / "data/raw/explained_answers").glob("*.answers.json"))
    if not files:
        pytest.skip("Generate the local answer intermediate for corpus validation")
    data = json.loads(files[0].read_text(encoding="utf-8"))
    projected = {
        (a["year"], a["question_number"]): structure(
            input_lines(data, a), a["correct_answer"]
        )
        for a in data["answers"]
    }
    return data, projected


@pytest.mark.parametrize("number", [9, 21, 33])
def test_reported_incorrect_sections_are_complete(corpus, number):
    explanation, warnings = corpus[1][(2016, number)]
    assert not explanation["other_lists"]
    block = explanation["bulleted_blocks"][0]
    assert block["role"] == "incorrect_choices_unmapped" and len(block["items"]) == 4
    assert all(len(item["line_refs"]) >= 1 for item in block["items"])
    # The source deliberately supplies ordinal numbers, not option letters.
    assert not explanation["choice_analysis"] and not warnings
    assert len(explanation["paragraphs"]) == 1


def test_q38_body_and_verified_marker_artifact(corpus):
    explanation, warnings = corpus[1][(2016, 38)]
    assert "Before you start trying to remember" in explanation["main_explanation"]
    assert "♦" not in explanation["main_explanation"]
    assert len(explanation["other_lists"][0]["items"]) == 5
    assert not any(
        "Before you start" in item["text"]
        for item in explanation["other_lists"][0]["items"]
    )
    assert any(
        b["role"] == "list_marker_artifact" and b["text"] == "♦"
        for b in explanation["blocks"]
    )
    assert any("unexpected_encoded_list_marker_preserved" in w for w in warnings)


@pytest.mark.parametrize("key", [(2014, 6), (2015, 31), (2016, 1)])
def test_already_correct_controls_stay_exactly_equal(corpus, key):
    original = next(
        a for a in corpus[0]["answers"] if (a["year"], a["question_number"]) == key
    )
    assert corpus[1][key] == (original["explanation"], original["warnings"])
    # Golden pre-change projections keep this check meaningful after reparsing.
    assert (
        sha256(
            json.dumps(corpus[1][key], ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        == CONTROL_HASHES[key]
    )


@pytest.mark.parametrize(
    "number", [10, 11, 15, 16, 17, 22, 23, 27, 28, 29, 34, 35, 39, 40, 41, 45, 46, 47]
)
def test_analogous_diamond_elimination_sections(corpus, number):
    explanation, warnings = corpus[1][(2016, number)]
    record = next(
        a
        for a in corpus[0]["answers"]
        if (a["year"], a["question_number"]) == (2016, number)
    )
    labels = [item["label"] for item in explanation["choice_analysis"]]
    assert (
        len(labels) == 4
        and len(set(labels)) == 4
        and record["correct_answer"] not in labels
    )
    assert not warnings
    tail = explanation["blocks"][
        next(
            i
            for i, b in enumerate(explanation["blocks"])
            if b["role"] == "choice_transition"
        )
        + 1 :
    ]
    assert all(
        b["role"].startswith("incorrect_choices") or b["role"] == "list_marker_artifact"
        for b in tail
    )


@pytest.mark.parametrize(
    "key,expected",
    [
        ((2016, 8), "1. To solve this question"),
        ((2015, 20), "57. As in graph D"),
        ((2014, 42), "1913. This average"),
    ],
)
def test_numeric_prose_is_not_a_list_just_because_it_starts_with_a_number(
    corpus, key, expected
):
    explanation, warnings = corpus[1][key]
    assert expected in explanation["main_explanation"]
    assert not explanation["other_lists"] and not warnings


def test_analogous_standalone_artifact_and_real_data_lists(corpus):
    explanation, warnings = corpus[1][(2016, 43)]
    assert any(b["role"] == "list_marker_artifact" for b in explanation["blocks"])
    assert [len(b["items"]) for b in explanation["other_lists"]] == [4, 4]
    assert "depreciation per mile" in explanation["main_explanation"]
    assert not warnings


def test_whole_source_html_inspection_shows_fixed_ownership_without_mutation():
    path = ROOT / "data/merged/blackstone/tsa_2008-2016.matched.json"
    if not path.exists():
        pytest.skip("Generate matched output before HTML integration validation")
    baseline = path.read_bytes()
    for number in (9, 21, 33, 38):
        result = inspect_question(path, year=2016, question_number=number)
        record = result["record"]
        candidate = (
            record["superseded_answer_candidates"][0]
            if record.get("superseded_answer_candidates")
            else {"record": record["answer"], "reference": record["answer_reference"]}
        )
        # Check PDF classification against the preserved PDF candidate, not a
        # manually supplied explanation with deliberately no PDF line spans.
        raw = json.loads(
            Path(candidate["reference"]["path"]).read_text(encoding="utf-8")
        )
        answer = candidate["record"]
        projected, notes = structure(input_lines(raw, answer), answer["correct_answer"])
        assert answer["explanation"] == projected
        assert answer["warnings"] == notes
        html = render_inspection(result, "html")
        import re

        sections = dict(
            re.findall(r"<section id='([^']+)'>(.*?)</section>", html, re.DOTALL)
        )
        if number == 38:
            assert "Before you start trying to remember" in sections["main-explanation"]
            assert "Before you start trying to remember" not in sections["other-lists"]
            assert "♦" not in sections["main-explanation"]
        else:
            assert "<li " not in sections["other-lists"]
            assert sections["incorrect-explanations"].count("<li ") == 4
            assert (
                "Items retained in source order; individual option letters are not inferred."
                in sections["incorrect-explanations"]
            )
            assert not result["record"]["answer"]["warnings"]
    assert path.read_bytes() == baseline


def test_all_source_lines_numbers_answers_and_raw_excerpts_are_preserved(corpus):
    original = corpus[0]
    updated = deepcopy(original)
    for answer in updated["answers"]:
        answer["explanation"], notes = corpus[1][
            (answer["year"], answer["question_number"])
        ]
        answer["warnings"] = notes
    validate_answers(updated)
    for before, after in zip(original["answers"], updated["answers"]):
        assert {
            k: v for k, v in before.items() if k not in {"explanation", "warnings"}
        } == {k: v for k, v in after.items() if k not in {"explanation", "warnings"}}
    assert len(updated["answers"]) == 450


def test_verified_numbered_sections_leave_generated_issues_but_real_issues_remain(
    tmp_path,
):
    path = ROOT / "data/merged/blackstone/tsa_2008-2016.matched.json"
    if not path.exists():
        pytest.skip("Generate matched output before report integration validation")
    data = json.loads(path.read_text(encoding="utf-8"))
    identities = {(i.get("year"), i.get("question_number")) for i in data["issues"]}
    assert not identities.intersection({(2016, 9), (2016, 21), (2016, 33)})
    assert (2014, 50) in identities
    assert not identities.intersection({(2016, 38), (2008, 12)})
    archived = {
        (r["identity"]["year"], r["identity"]["question_number"]): r
        for r in data["records"]
        if r.get("superseded_answer_candidates")
    }
    assert set(archived) == {(2016, 38), (2008, 12)}
    for record in archived.values():
        assert record["answer"]["provenance"]["origin"] == "user_supplied_manual"
        assert record["superseded_answer_candidates"][0]["record"]["warnings"]
    output = tmp_path / "issues.md"
    write_report(data, output)
    report = output.read_text(encoding="utf-8")
    assert "## Manually Superseded Source Findings (2 records)" in report
    assert (
        "bullet_structure_ambiguous:unexpected_encoded_list_marker_preserved" in report
    )
    for number in (9, 21, 33):
        assert f"| 2016 | section_1 | {number} |" not in report
    assert "| 2016 | 38 |" in report
    assert report == (ROOT / "docs/critical_thinking_problem_solving/tsa/MATCHING_2008-2016_ISSUES.md").read_text(
        encoding="utf-8"
    )
