"""Evidence-based BMAT exclusions, option ownership, fractions and QA regressions."""

import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_bmat import names, task

from categorization.bmat.backtest import read as read_categorized
from categorization.bmat.backtest import report as category_report
from categorization.bmat.core import attribution, build
from categorization.bmat.core import write as write_categorized
from parsers.bmat import parse_pdf
from parsers.bmat.semantic_filters import proposition_structure
from parsers.bmat.stabilize import anchors_for
from parsers.bmat.visuals import owner
from processors.normalization.bmat.backtest import load, render_html
from processors.normalization.bmat.fractions import recover


@pytest.mark.parametrize(
    "stem",
    [
        "Which claim is an inference supported by the passage?",
        "Which of the following claims does this finding justify?",
        "Which one can definitely be said about the dates?",
        "The above issue implies which of the following?",
        "Which of these can reliably be inferred from the passage?",
    ],
)
def test_inference_requires_requested_evidential_operation(stem):
    choices = [
        "The observed pattern is likely to continue.",
        "The result holds in every conceivable situation.",
        "There is no evidence about the dates.",
        "The claim follows from the reported evidence.",
    ]
    assert "Drawing Inferences" in names(task(stem, choices=choices))


@pytest.mark.parametrize(
    "stem,body",
    [
        (
            "Which one is the main conclusion?",
            "An inference implies a conclusion in this passage.",
        ),
        ("Which conclusion can be drawn from the passage?", "Evidence is supplied."),
        (
            "Which value does the function imply for y?",
            "The variables satisfy y = 2*x.",
        ),
        ("Which is definitely the cheapest journey?", "Fares are 10, 20, and 30."),
        (
            "Which finding would strengthen this inference?",
            "The passage makes a claim.",
        ),
    ],
)
def test_inference_lexical_false_positives(stem, body):
    assert "Drawing Inferences" not in names(task(stem, body))


def test_definite_implication_requires_premises_not_an_incidental_adverb():
    q = task(
        "Which one of the following statements is definitely true?",
        "Some Malgons are Zanders and all Zanders are Tvints.",
        [
            "All Zanders are both Malgons and Tvints.",
            "All Malgons are also always Tvints.",
            "Some Malgons must also be Tvints.",
            "Nothing follows from these membership relationships.",
        ],
    )
    assert "Drawing Inferences" in names(q)
    q["question_text"] = "A selection of train fares is shown."
    assert "Drawing Inferences" not in names(q)


def three_points(count=3, stem="Which statements identify a weakness in the argument?"):
    q = task(
        stem
        + "\n"
        + "\n".join(
            f"{i} The proposed evidence does not support this claim."
            for i in range(1, count + 1)
        ),
        "The passage offers a reason for its conclusion.",
        ["1 only", "2 only", "1 and 2 only", "1, 2, and 3"],
    )
    return q


def test_subpoints_requires_three_propositions_and_combination_choices():
    q = three_points()
    assert "Subpoints" in names(q)
    assert len(proposition_structure(q)["statements"]) == 3
    for count in (2, 4):
        assert "Subpoints" not in names(three_points(count))
    q["options"] = task("Other task")["options"]
    assert "Subpoints" not in names(q)
    q = three_points(stem="Which route reaches the destination fastest?")
    assert "Subpoints" not in names(q)
    for stem in (
        "Which statements, if true, weaken the above argument?",
        "Which claims are supported by the data?",
        "Which of the following can reliably be inferred from the passage?",
    ):
        found = names(three_points(stem=stem))
        assert "Subpoints" in found
        assert (
            "Drawing Inferences" not in found
        )  # combination choices are not free-standing claims


def clean_fixture(stem, choices=None):
    raw = task(
        stem,
        "The research evidence is used to establish an argument about what should happen.",
        choices
        or [
            "This claim is not supported by the stated evidence.",
            "There could be an unmeasured cause for the observed result.",
            "The author has assumed the connection that needs proof.",
            "This alternative is compatible with the original premise.",
        ],
    )
    return {
        "main_question": stem,
        "question_text": raw["question_text"],
        "main_body": [{"type": "text", "text": raw["question_text"]}],
        "options": [{**o, "images": []} for o in raw["options"]],
        "visual_assets": [],
        "images": [],
        "visual_previews": [],
        "bmat_filter": {"skip_from_pipeline": False},
        "cleaning_issues": [],
    }


@pytest.mark.parametrize(
    "stem,subcategory",
    [
        (
            "Which explains what is wrong with this argument?",
            "Detecting Reasoning Errors",
        ),
        (
            "Which one, if true, gives a reason why the argument might be flawed?",
            "Detecting Reasoning Errors",
        ),
        (
            "Which fact would strengthen the above argument?",
            "Assessing the Impact of Additional Evidence",
        ),
        (
            "Which fact would weaken the above argument?",
            "Assessing the Impact of Additional Evidence",
        ),
        (
            "Which is an unstated assumption upon which the above argument is based?",
            "Identifying an Assumption",
        ),
        (
            "Which could be drawn as a conclusion from the above passage?",
            "Drawing a Conclusion",
        ),
        (
            "Assuming the sample is representative, which conclusion can be drawn from the passage?",
            "Drawing a Conclusion",
        ),
        (
            "What assumption underlies the decision described above?",
            "Identifying an Assumption",
        ),
        (
            "Which is the best statement of the conclusion of the above argument?",
            "Summarising the Main Conclusion",
        ),
        (
            "Which new fact would weaken the already flawed argument?",
            "Assessing the Impact of Additional Evidence",
        ),
        (
            "Which fact, if true, would weaken the main conclusion of the above argument?",
            "Assessing the Impact of Additional Evidence",
        ),
    ],
)
def test_existing_tsa_categories_are_reused(stem, subcategory):
    result = attribution(clean_fixture(stem))
    assert result["status"] == "supported", result
    assert result["category"] == "Critical Thinking"
    assert result["subcategories"] == [subcategory]


def test_skip_precedence_and_upstream_defect_not_auto_resolved():
    q = clean_fixture("Which is the unstated assumption of the argument?")
    q["bmat_filter"] = {"skip_from_pipeline": True, "skip_reason": "Three subpoints"}
    assert attribution(q)["status"] == "intentional_skip"
    q["bmat_filter"] = {"skip_from_pipeline": False}
    q["cleaning_issues"] = [{"code": "missing_asset"}]
    assert attribution(q)["status"] == "needs_review"


def test_conditional_assuming_is_not_an_assumption_question():
    q = clean_fixture(
        "Assuming equal speeds, how long would it take to complete three laps?",
        choices=["10 minutes", "20 minutes", "30 minutes", "40 minutes"],
    )
    a = attribution(q)
    assert a["status"] == "not_evaluated" and not a["issues"]


def glyph(t, x, y, size=8):
    return {
        "text": t,
        "x0": x,
        "x1": x + 4,
        "top": y,
        "bottom": y + size,
        "size": size,
        "fontname": "Fixture",
    }


def test_stacked_fraction_cleaning_and_non_fraction_control():
    option = {
        "text": "3\n4",
        "glyph_layout": [
            {
                "bbox": [20, 100, 25, 100],
                "points": [[20, 100], [25, 100]],
                "glyphs": [glyph("3", 20, 91), glyph("4", 20, 103)],
            }
        ],
    }
    original = deepcopy(option)
    assert recover(option)[0] == "3/4"
    assert option == original
    option["glyph_layout"][0]["bbox"] = [20, 80, 25, 80]
    assert recover(option) is None
    option = original
    option["text"] += " omitted prose"
    assert recover(option) is None  # no silently lost surrounding content


def test_diagonal_fraction_preserves_sign_mixed_number_and_units():
    chars = [
        glyph("-", 0, 95, 12),
        glyph("1", 5, 95, 12),
        glyph("1", 12, 96, 7),
        glyph("3", 16, 102, 7),
        glyph("k", 24, 95, 12),
        glyph("m", 28, 95, 12),
    ]
    option = {
        "text": "-11 km\n3",
        "glyph_layout": [{"bbox": [11, 96, 21, 108], "glyphs": chars}],
    }
    text, evidence = recover(option)
    assert text == "-1 1/3 km"
    assert evidence[0]["method"] == "diagonal_fraction"


def test_zero_height_ticks_are_valid_native_geometry_not_missing_objects():
    cell = {
        "page": 1,
        "label": "A",
        "bbox": [10, 10, 20, 20],
        "cell": [0, 10, 100, 100],
    }
    assert owner([25, 30, 60, 30], [cell], 1) == cell
    assert owner([25, 99, 60, 101], [cell], 1) is None


def test_rotated_axis_letters_do_not_replace_upright_answer_anchors():
    labels = []

    def row(letter, y, *, rotated=False):
        box = [10, y, 18, y + 30 if rotated else y + 10]
        value = {
            "block_start": len(labels),
            "text": letter,
            "page": 1,
            "top": y,
            "bottom": y + 10,
            "word_boxes": [box],
            "word_texts": [letter],
        }
        labels.append(value)

    row("A", 20)
    row("B", 40, rotated=True)
    row("B", 100)
    row("C", 200)
    q = {
        "options": [{"label": s} for s in "ABC"],
        "raw": {"question_block": "ABBC", "options_block": "ABBC"},
    }
    anchors = anchors_for(q, {"lines": labels})
    assert [a["bbox"][1] for a in anchors] == [20, 100, 200]


def source(year, number):
    p = next(Path("data/raw/bmat").glob(f"bmat_{year}_*.raw.json"))
    d = json.loads(p.read_text(encoding="utf-8"))
    return p, d["questions"][number - 1]


def test_q35_current_crop_ownership_and_visual_prose_regression():
    _, q = source(2003, 35)
    assert not q["parsing_issues"]
    assert all(len(o["images"]) == 1 for o in q["options"])
    assert (
        q["options"][0]["images"][0]["bbox"][2]
        < q["options"][1]["images"][0]["bbox"][0]
    )
    assert len([a for a in q["visual_assets"] if a["belongs_to"] == "question"]) == 1
    assert "bi deaths" in q["raw"]["question_block"]
    assert "bi deaths" not in q["question_text"]
    assert "total population" in q["raw_components"]["main_question"]
    assert q["bmat_filter"]["skip_from_pipeline"]


def test_q7_data_rows_are_not_answer_options():
    _, q = source(2011, 7)
    assert not q["options"] and not q["parsing_issues"]
    assert "No Question" in {t["type"] for t in q["bmat_filter"]["types"]}
    assert len(q["raw"]["rejected_option_candidates"]) == 8
    assert "A 2 189" in q["raw"]["question_block"]
    assert "Boeing" not in q["question_text"]
    # Counter-example: a genuine table-form answer list is NOT a data-row skip.
    _, other = source(2009, 25)
    assert [o["label"] for o in other["options"]] == list("ABCD")
    assert "No Question" not in {t["type"] for t in other["bmat_filter"]["types"]}


def test_q5_fractions_plain_text_and_source_unchanged():
    path = next(Path("data/clean/bmat").glob("bmat_2004_*.clean.json"))
    d = load(path)
    q = d["questions"][4]
    assert [o["text"] for o in q["options"]] == [
        "1/2 km",
        "2/3 km",
        "1km",
        "1 1/3 km",
        "1 1/2 km",
    ]
    assert q["raw_record"]["options"][0]["text"] != "1/2 km"
    assert not q["cleaning_issues"]


@pytest.mark.parametrize(
    "year,number,expected",
    [
        (2007, 7, ["1/60", "1/48", "1/32", "1/20", "1/10"]),
        (2007, 26, ["1/6", "1/4", "1/2", "2/3", "3/4"]),
        (2010, 23, ["4/21", "8/21", "6/35", "9/35", "12/35", "18/35"]),
    ],
)
def test_analogous_raised_fraction_rows_belong_to_their_own_options(
    year, number, expected
):
    p = next(Path("data/clean/bmat").glob(f"bmat_{year}_*.clean.json"))
    data = load(p)
    q = data["questions"][number - 1]
    assert [o["text"] for o in q["options"]] == expected
    assert q["main_question"].endswith("?")
    raw = q["raw_record"]
    assert raw["raw"]["field_method"] == "complete_choice_labels_and_numeric_glyph_rows"
    assert raw["raw"].get("spatial_text_candidates")
    assert not q["cleaning_issues"]
    for option in raw["options"]:
        for line in option["source_lines"]:
            span = line["raw_span"]
            assert (
                raw["raw"]["question_block"][span["start"] : span["end"]]
                == line["text"]
            )


def test_tsa_clean_structure_is_reused_with_one_bmat_section():
    path = next(Path("data/clean/bmat").glob("bmat_2004_*.clean.json"))
    data = load(path)
    html = render_html(data, data["questions"][4], path)
    ids = re.findall(r"<section id='([^']+)'", html)
    assert ids == [
        "main-body",
        "main-question",
        "main-answers",
        "original-screenshot",
        "metadata",
        "availability",
        "issues",
        "bmat-specific",
    ]
    assert "1/2 km" in html and "Raw Main Answers" in html
    assert "Raw/original record and clean transformation evidence" in html


def test_unresolved_visuals_remain_visible_without_moving_into_main_body():
    path = next(Path("data/clean/bmat").glob("bmat_2021_*.clean.json"))
    data = load(path)
    q = data["questions"][7]
    before = deepcopy(q["main_body"])
    html = render_html(data, q, path)
    assert "Unresolved asset — not Main Body" in html
    assert q["main_body"] == before
    assert html.index("Unresolved asset — not Main Body") > html.index("id='issues'")


def test_categorization_persists_real_input_references_without_claiming_matching():
    data = build(["data/clean/bmat"])
    assert len({r["question_id"] for r in data["records"]}) == 664
    for r in data["records"]:
        assert r["matching_status"] == "not_run"
        assert (
            sha256(Path(r["question_reference"]["path"]).read_bytes()).hexdigest()
            == r["question_reference"]["sha256"]
        )
    for year, number, sub in [
        (2003, 28, "Detecting Reasoning Errors"),
        (2007, 28, "Detecting Reasoning Errors"),
        (2006, 4, "Identifying an Assumption"),
        (2004, 19, "Drawing a Conclusion"),
    ]:
        r = next(
            r
            for r in data["records"]
            if r["identity"]["year"] == year
            and r["identity"]["question_number"] == number
        )
        assert r["categorization"]["subcategories"] == [sub], r["categorization"]


def test_current_report_has_unique_unresolved_entries_and_no_stale_skip(tmp_path):
    path = next(Path("data/clean/bmat").glob("bmat_2011_*.clean.json"))
    data = build([path])
    output = tmp_path / "classified.json"
    write_categorized(output, data)
    issues, guide = tmp_path / "issues.md", tmp_path / "backtest.md"
    summary = category_report(output, issues, guide, tmp_path / "html")
    text = issues.read_text(encoding="utf-8")
    expected = {
        r["identity"]["question_number"]
        for r in data["records"]
        if r["categorization"]["status"] == "needs_review"
    }
    listed = [int(x) for x in re.findall(r"\| 2011 \| \[(\d+)\]", text)]
    assert len(listed) == len(set(listed)) == summary["unique_review_questions"]
    assert set(listed) == expected and 7 not in listed
    before = issues.read_bytes()
    category_report(output, issues, guide, tmp_path / "html")
    assert issues.read_bytes() == before


@pytest.mark.parametrize("defect", ["summary", "taxonomy"])
def test_report_rejects_stale_taxonomy_or_inaccurate_counts(tmp_path, defect):
    source = next(Path("data/clean/bmat").glob("bmat_2003_*.clean.json"))
    data = build([source])
    if defect == "summary":
        data["summary"] = {}
    else:
        data["taxonomy_reference"]["sha256"] = "0" * 64
    path = tmp_path / "bad.categorized.json"
    write_categorized(path, data)
    with pytest.raises(ValueError, match="taxonomy|summary"):
        read_categorized(path)


def test_empty_input_is_not_a_completed_categorization(tmp_path):
    with pytest.raises(ValueError, match="No BMAT CLEAN inputs"):
        build([tmp_path])


@pytest.mark.parametrize(
    "year,number,expected",
    [
        (2006, 16, "Identifying an Assumption"),
        (2017, 17, "Detecting Reasoning Errors"),
        (2018, 15, "Drawing a Conclusion"),
        (2018, 30, "Assessing the Impact of Additional Evidence"),
    ],
)
def test_two_or_four_proposition_combinations_are_not_an_invented_exclusion(
    year, number, expected
):
    path = next(Path("data/clean/bmat").glob(f"bmat_{year}_*.clean.json"))
    q = load(path)["questions"][number - 1]
    result = attribution(q)
    assert result["status"] == "supported", result
    assert result["subcategories"] == [expected]
    assert not q["bmat_filter"]["skip_from_pipeline"]
    assert "Subpoints" not in {t["type"] for t in q["bmat_filter"]["types"]}


def test_native_and_glyph_separator_points_round_trip_as_json(tmp_path):
    path = next(Path("data/raw/bmat").glob("bmat_2020_*.raw.json"))
    source = json.loads(path.read_text(encoding="utf-8"))
    data = parse_pdf(source["input"]["path"], asset_dir=tmp_path / "assets")
    assert json.loads(json.dumps(data, ensure_ascii=False)) == data
    assert data == source
