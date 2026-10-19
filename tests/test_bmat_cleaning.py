"""Stored BMAT RAW -> CLEAN, provenance, exclusions and inspection regressions."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from processors.normalization.bmat.backtest import inspect, load, report
from processors.normalization.bmat.cleaner import clean_dataset, validate_clean


def source(year):
    p = next(Path("data/raw/bmat").glob(f"bmat_{year}_*.raw.json"))
    return p, json.loads(p.read_text(encoding="utf-8"))


def clean(year):
    p = next(Path("data/clean/bmat").glob(f"bmat_{year}_*.clean.json"))
    return p, load(p)


@pytest.mark.parametrize("year", range(2003, 2022))
def test_all_current_clean_records_round_trip_without_mutating_raw(year):
    raw_path, raw = source(year)
    before = sha256(raw_path.read_bytes()).hexdigest()
    _, saved = clean(year)
    assert clean_dataset(raw, raw_path) == saved
    validate_clean(saved, raw)
    assert len(saved["questions"]) == len(raw["questions"])
    assert saved["raw_reference"]["sha256"] == before
    assert sha256(raw_path.read_bytes()).hexdigest() == before
    for q, r in zip(saved["questions"], raw["questions"]):
        assert q["raw_record"] == r
        assert q["bmat_filter"] == r["bmat_filter"]
        assert q["source_question_key"] == r["source_question_key"]
        assert q["visual_assets"] == r["visual_assets"]
        assert [o["images"] for o in q["options"]] == [
            o["images"] for o in r["options"]
        ]
        assert {i["code"] for i in q["cleaning_issues"] if i["origin"] == "raw"} >= {
            i["code"] for i in r["parsing_issues"]
        }


@pytest.mark.parametrize(
    "year,number,needle",
    [
        (2003, 36, "when was the Battle"),
        (2003, 38, "If this is so,"),
        (2004, 13, "molecular structure"),
        (2008, 22, "unstated assumption"),
        (2017, 18, "After baking"),
    ],
)
def test_prompts_and_completion_survive_cleaning(year, number, needle):
    _, data = clean(year)
    q = data["questions"][number - 1]
    assert needle in q["main_question"]
    assert not q["main_question"].startswith("Equals question")
    assert all(needle not in b.get("text", "") for b in q["main_body"])


@pytest.mark.parametrize(
    "year,number",
    [(2010, 12), (2012, 14), (2003, 12), (2009, 3), (2012, 3), (2004, 22), (2014, 7)],
)
def test_image_answers_remain_under_their_letters(year, number):
    _, data = clean(year)
    q = data["questions"][number - 1]
    body_ids = {b.get("asset_id") for b in q["main_body"]}
    for option in q["options"]:
        assert len(option["images"]) == 1
        a = option["images"][0]
        assert a["image_id"] not in body_ids
        assert a["option_label"] == option["label"]
        assert (
            a["sha256"]
            == sha256(
                (Path(q["raw_reference"]["path"]).parent / a["path"]).read_bytes()
            ).hexdigest()
        )


def test_table_and_axis_text_do_not_return_as_plain_prose():
    _, data = clean(2014)
    q = data["questions"][0]
    body = " ".join(b.get("text", "") for b in q["main_body"])
    assert "Facebook" not in body and "myspace.com" not in body
    assert any(b["type"] == "visual" for b in q["main_body"])
    assert "Facebook" in q["raw_record"]["raw"]["question_block"]
    for year, n, bad in [
        (2005, 24, "setadidnac"),
        (2010, 1, "thgieH"),
        (2019, 31, "27"),
        (2021, 14, "12"),
    ]:
        _, data = clean(year)
        q = data["questions"][n - 1]
        assert not any(i["origin"] == "cleaning" for i in q["cleaning_issues"])
        assert bad not in [b.get("text", "") for b in q["main_body"]]


def test_end_marker_stays_in_snapshot_not_readable_fields():
    _, data = clean(2014)
    q = data["questions"][34]
    assert "END OF TEST" in q["raw_record"]["raw"]["question_block"]
    assert "END OF TEST" not in q["question_text"] + q["main_question"] + "".join(
        o["text"] for o in q["options"]
    )


def test_unknown_font_is_not_guessed_or_made_eligible():
    for year, n in [(2017, 28)]:
        _, data = clean(year)
        q = data["questions"][n - 1]
        assert "(cid:" in q["question_text"]
        assert not q["pipeline_eligible"]
        assert any(
            i["origin"] == "raw" and i["code"] == "font_encoding_artifacts"
            for i in q["cleaning_issues"]
        )


def test_cleaning_does_not_open_pdfs(monkeypatch):
    import pdfplumber

    path, data = source(2014)

    def forbidden(*args, **kwargs):
        raise AssertionError("CLEAN must not parse PDFs")

    monkeypatch.setattr(pdfplumber, "open", forbidden)
    clean_dataset(data, path)


def test_inspection_shows_both_layers_and_owned_visuals(tmp_path):
    path, data = clean(2012)
    html = inspect(path, 14, tmp_path / "case.html").read_text(encoding="utf-8")
    assert all(
        label in html
        for label in [
            "Raw Main Body",
            "Clean Main Body",
            "Raw Main Question",
            "Clean Main Question",
            "Option A",
            "Option E",
            "Original Screenshot",
            "BMAT-specific category",
            "Source / Document Metadata",
        ]
    )
    assert "data:image/png;base64," in html
    assert data["questions"][13]["question_id"] in html


def test_report_counts_unique_records_separates_upstream(tmp_path):
    path, data = clean(2017)
    summary = report([path], tmp_path / "issues.md", tmp_path / "html")
    assert summary["records"] == 35
    assert summary["unique_cleaning_specific_issue_questions"] == 0
    assert summary["unique_upstream_issue_questions"] == sum(
        bool(q["raw_record"]["parsing_issues"]) for q in data["questions"]
    )


def test_stale_clean_output_cannot_be_shown_as_current(tmp_path):
    _, data = clean(2014)
    data = deepcopy(data)
    data["raw_reference"]["sha256"] = "0" * 64
    target = tmp_path / "stale.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Stale BMAT CLEAN"):
        load(target)
