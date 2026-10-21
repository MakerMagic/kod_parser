"""Read-only regressions for the explicitly authorized answer-key correction."""

import json
from pathlib import Path

import pytest


def test_transcription_is_complete_and_uses_explicit_bmat_identity():
    source = json.loads(
        Path("processors/matching/manual_sources/bmat_2014_answers.json").read_text(
            encoding="utf8"
        )
    )
    assert (source["source_family"], source["year"], source["section"]) == (
        "bmat",
        2014,
        "section_1",
    )
    assert source["approval"] == "missing_answers_only"
    assert list(source["answers"]) == [str(n) for n in range(1, 36)]
    assert "".join(
        source["answers"].values()
    ) == "DCEBGBEBCDEDEFADD CFCC CDBBDEAE D CDBCB".replace(" ", "")


def test_canonical_answers_and_renderer_preserve_exclusion_policy():
    from processors.pre_final.render import render_html

    path = Path("data/pre_final/questions.json")
    matched_path = Path("data/merged/bmat/questions.matched.json")
    if not path.exists() or not matched_path.exists():
        pytest.skip("Local generated canonical datasets are unavailable")
    source = json.loads(
        Path("processors/matching/manual_sources/bmat_2014_answers.json").read_text(
            encoding="utf8"
        )
    )
    matched = json.loads(matched_path.read_text(encoding="utf8"))
    targets = [r for r in matched["records"] if r["identity"]["year"] == 2014]
    assert len(targets) == 35
    assert all(
        r["correct_answer"] == source["answers"][str(r["identity"]["question_number"])]
        for r in targets
    )
    assert sum(r["status"] == "intentionally_skipped" for r in targets) == 18
    data = json.loads(path.read_text(encoding="utf8"))
    included = [
        q for q in data["questions"] if q["source"] == "BMAT" and q["year"] == 2014
    ]
    assert len(included) == 17
    for q in included:
        assert q["correct_answer"] == source["answers"][str(q["question_number"])]
        assert q["explanation"] is None
    q2 = next(
        q
        for q in data["questions"]
        if q["source"] == "BMAT" and q["year"] == 2010 and q["question_number"] == 2
    )
    html = render_html(q2, data["categories"])
    assert (
        "Some of the arts (for example, opera) may be seen as non-egalitarian." in html
    )
    assert "The pupils in a class" not in html
    assert [o["label"] for o in q2["main_answers"]] == list("ABCD")
    assert len([a for a in q2["assets"] if a["role"] == "source_preview"]) == 1
    assert "Correct Answer" in render_html(included[0], data["categories"])
