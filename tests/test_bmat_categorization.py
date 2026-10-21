"""Complete dominant-task BMAT attribution, audited review and TSA isolation."""

import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_bmat_refinement import clean_fixture

from categorization.bmat.backtest import cell, read
from categorization.bmat.core import attribution, build
from categorization.bmat.review import apply, load
from categorization.bmat.taxonomy import ORDER, assign, categories, special, validate
from categorization.core import digest


@pytest.fixture(scope="module")
def current():
    return read("data/categorized/bmat/questions.categorized.json")


@pytest.mark.parametrize(
    "identifier,stem",
    [
        (
            "ct_main",
            "Which is the best statement of the conclusion of the above argument?",
        ),
        ("ct_infer", "Which conclusion can be drawn from the above passage?"),
        ("ct_assume", "What assumption underlies the decision described above?"),
        ("ct_impact", "Which evidence would strengthen this hypothesis?"),
        ("ct_error", "Which explains what is wrong with the above argument?"),
        ("ct_match", "Which argument matches the reasoning of the passage?"),
        (
            "ct_principle",
            "Which example illustrates the principle underlying the argument?",
        ),
    ],
)
def test_bmat_argument_intents_reuse_all_seven_tsa_classes(identifier, stem):
    result = attribution(clean_fixture(stem))
    assert result["patterns"] == [identifier], result
    validate(result)


@pytest.mark.parametrize("name", ORDER)
def test_each_existing_bmat_type_has_exact_canonical_identity(name):
    q = clean_fixture("Which assumption does the argument need?")
    q["bmat_filter"] = {
        "skip_from_pipeline": True,
        "primary_type": name,
        "skip_reason": "Verified source-specific evidence",
    }
    result = attribution(q)
    assert result["category"] == "BMAT-specific"
    assert result["patterns"] == result["subcategories"] == [name]
    validate(result)


def test_multiresponses_are_not_one_combination_valued_choice():
    q = clean_fixture("Select all that apply.")
    assert special(q)[0] == "Several correct answers"
    q["main_question"] = "Which two statements are true?"
    q["options"] = [
        {"label": l, "text": t, "images": []}
        for l, t in zip(
            "ABCD", ["1 and 2", "1 and 3", "2 and 3", "All of them"], strict=True
        )
    ]
    assert special(q) is None
    q["question_text"] = "\n".join(
        f"{i} These people have reported evidence about the result."
        for i in range(1, 4)
    )
    assert special(q)[0] == "Subpoints"
    q["question_text"] = "1 20 ml\n2 30 ml\n3 40 ml"
    assert special(q) is None
    q["question_text"] = "\n".join(
        f"{i} These people have reported evidence about the result."
        for i in range(1, 4)
    )
    q["main_question"] = "Which route reaches town fastest?"
    assert special(q) is None


@pytest.mark.parametrize(
    "changes",
    [
        {"patterns": ["invented"]},
        {
            "patterns": ["ps_select", "ps_procedure"],
            "subcategories": ["Relevant Selection", "Finding Procedures"],
        },
        {"subcategories": []},
        {"issues": [{"code": "still_uncertain"}]},
        {"category": "Something Else"},
    ],
)
def test_no_invalid_multilabel_or_unresolved_acceptance(changes):
    result = assign({}, "ps_select", "Applicable information is selected.")
    result.update(changes)
    with pytest.raises(ValueError):
        validate(result)


def test_subject_words_and_numbers_do_not_force_a_category():
    q = clean_fixture("Which result applies?", ["1", "2", "3", "4"])
    q["question_text"] = "There are 40 numbers and a principle in this table."
    q["main_body"] = [{"type": "text", "text": q["question_text"]}]
    result = attribution(q)
    assert result["status"] == "needs_review" and not result["patterns"]


def test_metadata_table_does_not_break_on_multiline_source_evidence():
    assert cell("\n[Source: a|b]\nCitation text\t") == "[Source: a/b] Citation text"


@pytest.mark.parametrize(
    "stem,body,visual,expected",
    [
        (
            "If Alex works Friday, then the nights when Robin is on duty are",
            "Three guards work five nights. Alex must work four nights; Robin works three nights. Regulations do not allow three consecutive shifts.",
            False,
            "ps_procedure",
        ),
        (
            "In which activity is the age ratio closest to that for swimming?",
            "The table gives numbers aged 12 and 17 in six activities.",
            True,
            "ps_select",
        ),
        (
            "Which chart best represents the monthly differences?",
            "The table gives monthly figures for two years.",
            True,
            "ps_similarity",
        ),
        (
            "Which chart could not show the votes?",
            "3 people changed their vote from Alex to Robin. 2 people changed their vote from Robin to Sam. The table gives monthly figures.",
            True,
            "ps_procedure",
        ),
    ],
)
def test_unseen_semantic_analogues_reuse_tsa_features_without_question_ids(
    stem, body, visual, expected
):
    q = clean_fixture(stem, ["Running", "Cycling", "Hockey", "Tennis", "Squash"])
    q["question_text"] = body
    q["main_body"] = [{"type": "text", "text": body}]
    if visual:
        q["main_body"].append({"type": "visual", "path": "table.png"})
    assert attribution(q)["patterns"] == [expected]


@pytest.mark.parametrize("where", ["body", "option"])
def test_meaningful_visual_does_not_enter_text_only_critical_thinking(where):
    q = clean_fixture("Which assumption does the argument require?")
    asset = {
        "path": "test.png",
        "asset_type": "raster_image",
        "belongs_to": "question" if where == "body" else "option",
        "option_label": None if where == "body" else "A",
    }
    q["visual_assets"] = [asset]
    if where == "body":
        q["images"] = [asset]
    else:
        q["options"][0]["images"] = [asset]
    assert attribution(q)["category"] != "Critical Thinking"


def test_complete_dataset_single_category_and_explicit_exclusions(current):
    rows = current["records"]
    assert len(rows) == len({r["question_id"] for r in rows}) == 664
    assert current["summary"] == {
        "needs_review": 5,
        "supported": 316,
        "intentional_skip": 343,
    }
    for row in rows:
        validate(row["categorization"])
        assert row["identity"]["source"] == "bmat"
        assert row["categorization"]["status"] != "not_evaluated"
    accepted = [r for r in rows if r["categorization"]["status"] != "needs_review"]
    assert len(accepted) == 659
    assert {r["categorization"]["patterns"][0] for r in accepted} == set(categories())
    assert sum(r["question"]["bmat_filter"]["skip_from_pipeline"] for r in rows) == 335


@pytest.mark.parametrize(
    "year,number,label",
    [
        (2005, 11, "ps_similarity"),
        (2007, 25, "ps_select"),
        (2009, 7, "ps_procedure"),
        (2010, 18, "ps_procedure"),
        (2011, 24, "ct_infer"),
        (2013, 6, "ct_impact"),
        (2013, 26, "ps_procedure"),
        (2015, 24, "ct_impact"),
        (2016, 14, "ps_procedure"),
        (2016, 23, "ps_similarity"),
        (2017, 15, "ct_match"),
        (2020, 19, "ps_procedure"),
        (2020, 30, "ps_similarity"),
        (2021, 7, "ps_select"),
        (2021, 26, "ps_similarity"),
    ],
)
def test_reviewed_materiality_boundaries(current, year, number, label):
    row = next(
        r
        for r in current["records"]
        if r["identity"]["year"] == year and r["identity"]["question_number"] == number
    )
    assert row["categorization"]["patterns"] == [label]


def test_review_scope_complete_and_content_bound(current):
    decisions = load("categorization/bmat/review.json")
    assert len(decisions) == 178
    reviewed = [r for r in current["records"] if r["categorization"].get("review")]
    assert len(reviewed) == 178
    for row in reviewed:
        decision = decisions[digest(row["question"])]
        assert {"ps_select", "ps_procedure", "ps_similarity"} <= set(
            decision["evaluated_categories"]
        )
        assert len(decision["evidence"]) >= 60
    row = deepcopy(reviewed[0])
    # Same identifier but changed content must not inherit a manual label.
    row["question"]["main_question"] += " Changed."
    result = {"marker": "unchanged"}
    assert apply(result, row, decisions) == {"marker": "unchanged"}


def test_review_rejects_unseen_or_upstream_broken_visual_context(current):
    decisions = load("categorization/bmat/review.json")
    row = deepcopy(
        next(r for r in current["records"] if r["categorization"].get("review"))
    )
    key = digest(row["question"])
    bad = deepcopy(decisions)
    bad[key]["visual_references"] = []
    with pytest.raises(ValueError, match="visual context"):
        apply({}, row, bad)
    row["question"]["cleaning_issues"] = [{"code": "broken"}]
    bad = {digest(row["question"]): decisions[key]}
    with pytest.raises(ValueError, match="upstream defects"):
        apply({}, row, bad)


def test_persisted_review_cannot_be_relabelled_as_another_valid_category(
    current, tmp_path
):
    row = deepcopy(
        next(
            r
            for r in current["records"]
            if r["categorization"].get("review")
            and r["categorization"]["status"] == "supported"
        )
    )
    assign(row["categorization"], "ct_main", row["categorization"]["rationale"])
    data = {**current, "records": [row], "summary": {"supported": 1}}
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="differs from verified review"):
        read(path)


def test_stage_rerun_round_trips_content_bound_categories_and_metadata(current):
    source = next(Path("data/clean/bmat").glob("bmat_2017_*.clean.json"))
    rebuilt = build(
        [source],
        "data/merged/bmat/questions.matched.json",
        "categorization/bmat/review.json",
        "data/categorized/blackstone/model.json",
    )
    expected = {
        r["question_id"]: r for r in current["records"] if r["identity"]["year"] == 2017
    }
    assert len(rebuilt["records"]) == len(expected) == 35
    for row in rebuilt["records"]:
        assert row == expected[row["question_id"]]


def test_issue_rows_equal_current_unique_unresolved_and_inspection_fields(current):
    issues = Path("docs/critical_thinking_problem_solving/bmat/BMAT_CATEGORIZATION_ISSUES.md").read_text(encoding="utf-8")
    listed = [
        (int(y), int(n)) for y, n in re.findall(r"\| (\d{4}) \| (\d+) \|", issues)
    ]
    expected = {
        (r["identity"]["year"], r["identity"]["question_number"])
        for r in current["records"]
        if r["categorization"]["status"] == "needs_review"
    }
    assert set(listed) == expected and len(listed) == len(expected) == 5
    row = next(
        r
        for r in current["records"]
        if r["identity"]["year"] == 2021 and r["identity"]["question_number"] == 26
    )
    assert row["question"]["main_question"] and row["question"]["options"]
    assert row["question"]["visual_previews"]
    assert row["categorization"]["patterns"] == ["ps_similarity"]


def test_previous_tsa_results_and_upstream_files_remain_byte_identical():
    protected = Path("inspections/critical_thinking_problem_solving/bmat/categorization/full_pass/protected_hashes.json")
    if not protected.exists():
        pytest.skip("Optional before/after workspace audit unavailable")
    for path, expected in json.loads(protected.read_text(encoding="utf-8")).items():
        if (
            Path(path).resolve()
            == Path("data/merged/bmat/questions.matched.json").resolve()
        ):
            continue  # Explicit supplied-text import updates this separate stage.
        assert sha256(Path(path).read_bytes()).hexdigest() == expected, path


def test_canonical_asset_references_resolve_without_any_reports(current):
    checked = set()
    for row in current["records"]:
        question = row["question"]
        base = Path(question["raw_reference"]["path"]).parent
        for asset in [*question["visual_assets"], *question["visual_previews"]]:
            path = Path(asset["path"])
            if not path.is_absolute():
                path = base / path
            if path not in checked:
                assert sha256(path.read_bytes()).hexdigest() == asset["sha256"]
                checked.add(path)
    assert len(checked) >= 664
