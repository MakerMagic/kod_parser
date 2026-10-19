"""Task modelling, representation correspondence and safe review refresh."""

from copy import deepcopy
from pathlib import Path

import pytest

from categorization.core import file_ref, read
from categorization.model import features
from categorization.review import assessment_signature, refresh_review


def task(stem, body, *, visual=False, image_options=False):
    return {
        "stem": stem,
        "body": body,
        "explanation": "",
        "body_visual": visual,
        "modalities": ["text", "visual"] if visual or image_options else ["text"],
        "options": [
            {
                "label": c,
                "text": name,
                "images": [{"image_id": c}] if image_options else [],
            }
            for c, name in zip(
                "ABCDE", ("Running", "Cycling", "Hockey", "Tennis", "Squash")
            )
        ],
    }


def test_profile_selection_is_not_table_presence_or_numeric_similarity():
    data = task(
        "In which activity is the age ratio closest to that for swimming?",
        "The table gives numbers aged 12 and 17 in six activities.",
        visual=True,
    )
    assert features(data)["target_profile_selection"]
    assert not features({**data, "stem": "What is the sum of all table values?"})[
        "target_profile_selection"
    ]
    assert not features({**data, "body_visual": False})["target_profile_selection"]


def test_complete_units_and_nested_geometry_require_a_model_not_just_arithmetic():
    scoring = task(
        "Who raised a different amount?",
        "Pay is per complete 100 points. Alex receives £12 per 100 points; Robin receives £15 per 100 points. Their scores are 234 and 367.",
    )
    assert features(scoring)["discrete_unit_procedure"]
    assert not features({**scoring, "body": "The final totals are 24 and 45 pounds."})[
        "discrete_unit_procedure"
    ]
    frame = task(
        "What is the overall height?",
        "A picture is 40cm high. The mount is 6cm wide at the top and 9cm at the bottom. The frame has width 2cm on both sides of the mount.",
    )
    assert features(frame)["enclosure_composition"]
    assert not features(
        {
            **frame,
            "body": frame["body"] + " The formula height = 40+6+9+2+2 is supplied.",
        }
    )["enclosure_composition"]


def test_chart_correspondence_keeps_prescribed_statistic_but_not_transfer_simulation():
    chart = task(
        "Which chart best represents the monthly differences?",
        "The table gives monthly figures for two years.",
        visual=True,
        image_options=True,
    )
    assert features(chart)["representation_correspondence"]
    transfer = {
        **chart,
        "body": "3 people changed their vote from Alex to Robin. 2 people changed their vote from Robin to Sam. The table gives monthly figures.",
    }
    assert not features(transfer)["representation_correspondence"]
    assert features({**transfer, "stem": "Which chart could not show the votes?"})[
        "flow_balance_constraints"
    ]
    assert not features(
        {**chart, "body": "A train travels on a journey through three stations."}
    )["representation_correspondence"]
    filling = {
        **chart,
        "body": "A bath can be filled from the hot tap in 15 minutes or cold tap in 10 minutes. Both taps run before the cold tap is turned off.",
    }
    assert not features(filling)["representation_correspondence"]


def test_duty_roster_is_not_reading_a_finished_timetable():
    roster = task(
        "If Alex works Friday, then the nights when Robin is on duty are",
        "Three guards work five nights. Alex must work four nights; Robin works three nights. Regulations do not allow three consecutive shifts.",
    )
    assert features(roster)["roster_constraints"]
    assert not features(
        {
            **roster,
            "body": "The timetable directly lists Alex on Monday and Robin on Tuesday.",
        }
    )["roster_constraints"]


def test_metadata_only_refresh_preserves_assessment_but_not_changed_evidence(tmp_path):
    reference = tmp_path / "previous.json"
    reference.write_text("{}", encoding="utf-8")
    old = {
        "record_key": "stable",
        "question_view": {
            "main_question": "What is the answer?",
            "question_text": "Two finished totals are 10 and 20.",
            "options": [{"label": c, "text": "10"} for c in "ABCDE"],
            "raw_reference": {"path": "old.json", "sha256": "old"},
        },
        "correct_answer": "A",
        "final_explanation": None,
        "upstream": {
            "matching_status": "matched",
            "matching_issues": [],
            "cleaning_issues": [],
        },
        "categorization": {
            "status": "classified",
            "category": "Problem-Solving",
            "subcategories": ["Relevant Selection"],
            "issues": [],
        },
    }
    current = deepcopy(old)
    current["question_view"]["raw_reference"]["sha256"] = "new container hash"
    assert assessment_signature(current) == assessment_signature(old)
    current["categorization"]["subcategories"] = ["Finding Procedures"]
    previous = {
        "records": [old],
        "review_reference": file_ref(reference),
        "review_summary": {
            "all_needs_review": 0,
            "problem_solving_review": 0,
            "out_of_scope_review": 0,
        },
    }
    result = {"records": [current]}
    refresh_review(result, previous, reference)
    assert result["records"][0]["categorization"] == old["categorization"]
    changed = deepcopy(old)
    changed["correct_answer"] = "B"
    assert assessment_signature(changed) != assessment_signature(old)
    changed = deepcopy(old)
    changed["question_view"]["options"][0]["images"] = [
        {"sha256": "changed visual", "option_label": "B"}
    ]
    assert assessment_signature(changed) != assessment_signature(old)


def test_matching_inspection_cache_reloads_changed_input(monkeypatch, tmp_path):
    from processors.matching import backtest

    path = tmp_path / "questions.matched.json"
    path.write_text("first", encoding="utf-8")
    calls = []
    record = {
        "identity": {"year": 2030, "section": "section_1", "question_number": 1},
        "question": None,
        "answer": None,
        "issues": [],
    }

    def load(p):
        calls.append(p)
        return {"records": [deepcopy(record)], "issues": []}

    monkeypatch.setattr(backtest, "load_matched", load)
    cache = {}
    for _ in range(2):
        backtest.inspect_question(path, year=2030, question_number=1, cache=cache)
    assert len(calls) == 1
    path.write_text("different input bytes", encoding="utf-8")
    backtest.inspect_question(path, year=2030, question_number=1, cache=cache)
    assert len(calls) == 2


@pytest.fixture(scope="module")
def canonical():
    path = Path("data/categorized/blackstone/tsa.categorized.json")
    if not path.exists():
        pytest.skip("Optional real canonical dataset unavailable")
    return read(path)


@pytest.mark.parametrize(
    "year,number,labels",
    [
        (2014, 38, {"Relevant Selection"}),
        (2014, 50, {"Finding Procedures", "Identifying Similarity"}),
        (2016, 12, {"Finding Procedures"}),
        (2016, 32, {"Identifying Similarity"}),
        (2016, 38, {"Finding Procedures"}),
        (2017, 6, {"Finding Procedures"}),
        (2017, 20, {"Identifying Similarity"}),
        (2017, 38, {"Identifying Similarity"}),
        (2018, 20, {"Identifying Similarity"}),
        (2018, 50, {"Identifying Similarity"}),
    ],
)
def test_persisted_corrected_regression(canonical, year, number, labels):
    data = canonical
    assert data["logic"]["version"] == "4"
    row = next(
        r
        for r in data["records"]
        if (r["identity"]["year"], r["identity"]["question_number"]) == (year, number)
    )
    assert set(row["categorization"]["subcategories"]) == labels
    assert row["categorization"]["status"] in {"classified", "multi_label"}
    assert not row["categorization"]["issues"]


@pytest.mark.parametrize(
    "year,number,body_images,option_images",
    [
        (2014, 50, 1, 5),
        (2016, 32, 4, 5),
        (2017, 38, 0, 5),
        (2018, 20, 6, 0),
        (2018, 50, 2, 5),
        (2019, 32, 0, 5),
        (2019, 44, 1, 5),
    ],
)
def test_persisted_body_answer_separation(
    canonical, year, number, body_images, option_images
):
    row = next(
        r
        for r in canonical["records"]
        if (r["identity"]["year"], r["identity"]["question_number"]) == (year, number)
    )
    q = row["question_view"]
    body_ids = {b["asset_id"] for b in q["main_body"] if b["type"] == "visual"}
    answer_ids = {a["image_id"] for o in q["options"] for a in o.get("images", [])}
    assert len(body_ids) == body_images and len(answer_ids) == option_images
    assert not body_ids.intersection(answer_ids)
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    if option_images:
        assert all(len(o["images"]) == 1 and not o["text"] for o in q["options"])
        assert all(
            a["belongs_to"] == "option"
            and a["option_label"] == o["label"]
            and a.get("clean_asset")
            for o in q["options"]
            for a in o["images"]
        )
    assert not row["upstream"]["cleaning_issues"]


def test_persisted_sentence_completion_is_not_duplicated_in_body(canonical):
    row = next(
        r
        for r in canonical["records"]
        if (r["identity"]["year"], r["identity"]["question_number"]) == (2016, 12)
    )
    q = row["question_view"]
    expected = "If Robert is on duty on Friday night, then the nights when Sheila is on duty are"
    assert q["main_question"] == expected
    assert expected not in "\n".join(b.get("text", "") for b in q["main_body"])
