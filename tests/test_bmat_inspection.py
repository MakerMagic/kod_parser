"""Canonical repair, matched-context and issue-lifecycle inspection regressions."""

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from categorization.bmat import backtest, core
from processors.normalization.bmat.backtest import load


def clean(year):
    path = next(Path("data/clean/bmat").glob(f"bmat_{year}_*.clean.json"))
    return path, load(path)


def test_resolved_visual_options_survive_cleaning_without_generic_issue():
    _, data = clean(2015)
    q = data["questions"][17]
    raw = q["raw_record"]
    assert not q["cleaning_issues"] and not raw["parsing_issues"]
    assert [o["label"] for o in q["options"]] == list("ABCDEF")
    for original, option in zip(raw["options"], q["options"], strict=True):
        assert len(option["images"]) == 1
        assert option["images"] == original["images"]
        assert option["images"][0]["option_label"] == option["label"]
        assert option["images"][0]["belongs_to"] == "option"
    assert {s["page"] for s in raw["raw"]["page_spans"]} == {15}
    assert q["bmat_filter"]["primary_type"] == "too long"
    assert q["bmat_filter"]["too_long_measurement"]["occupancy_ratio"] > 0.60
    assert "(cid:120)" in raw["raw"]["question_block"]
    assert "(cid:" not in raw["question_text"]
    preview = q["visual_previews"][0]
    assert preview["page"] == 15 and preview["bbox"][3] < 670
    assert "question_only" in preview["path"]
    assert raw["raw"]["preview_candidates"]


def test_shared_declaration_stops_previous_question_without_losing_stimulus():
    _, data = clean(2015)
    q = data["questions"][30]["raw_record"]
    assert {s["page"] for s in q["raw"]["page_spans"]} == {22}
    assert "RSPCA" not in q["options"][-1]["text"]
    path = Path(data["raw_reference"]["path"])
    source = json.loads(path.read_text(encoding="utf-8"))
    ranges = {
        (r["start_question"], r["end_question"])
        for r in source["shared_information_ranges"]
    }
    assert {(19, 22), (32, 35)} <= ranges
    assert any("RSPCA" in str(item) for item in source["unassigned_content"])


def test_category_report_uses_persisted_matched_context_and_rejects_stale_link(
    tmp_path,
):
    path, _ = clean(2017)
    data = core.build([path], "data/merged/bmat/questions.matched.json")
    output = tmp_path / "categorized.json"
    core.write(output, data)
    summary = backtest.report(
        output, tmp_path / "issues.md", tmp_path / "guide.md", tmp_path / "html"
    )
    html = (tmp_path / "html/2017_q001.html").read_text(encoding="utf-8")
    assert "Correct Answer" in html and "Main Explanation" in html
    assert "Final Explanation" in html and "Explanation Source" in html
    assert "original-screenshot" in html and "BMAT-specific" in html
    assert "Matching status: matched" in html
    assert "Matching: not run" not in html
    assert summary["records"] == 35
    data["matching_source"]["sha256"] = "0" * 64
    core.write(output, data)
    with pytest.raises(ValueError, match="matching context"):
        backtest.read(output)


def test_issue_regeneration_removes_only_genuinely_resolved_rows(tmp_path, monkeypatch):
    from hashlib import sha256

    _, resolved = clean(2015)
    _, unresolved = clean(2003)
    q = deepcopy(resolved["questions"][17])
    other = deepcopy(unresolved["questions"][0])
    old = deepcopy(q)
    old["bmat_filter"]["skip_from_pipeline"] = False
    old["cleaning_issues"] = [{"code": "font_encoding_artifacts"}]
    dataset = {"questions": [old, other]}
    source = tmp_path / "source.clean.json"
    source.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(core, "load", lambda _: dataset)
    monkeypatch.setattr(backtest, "load", lambda _: dataset)
    monkeypatch.setattr(
        backtest,
        "render_html",
        lambda *a: (
            "<main><details><summary>Raw/original record</summary></details></main>"
        ),
    )
    out, issues = tmp_path / "out.json", tmp_path / "issues.md"

    def refresh():
        core.write(out, core.build([source]))
        return backtest.report(out, issues, tmp_path / "guide.md", tmp_path / "html")

    assert refresh()["unique_review_questions"] == 2
    assert "| 2015 | 18 |" in issues.read_text(encoding="utf-8")
    dataset["questions"][0] = q
    assert refresh()["unique_review_questions"] == 1
    text = issues.read_text(encoding="utf-8")
    assert "| 2015 | 18 |" not in text
    assert re.findall(r"\| 2003 \| (\d+) \|", text) == ["1"]
    assert "visual_neighbor_boundary_uncertain" in text
    assert (
        core.build([source])["sources"][0]["sha256"]
        == sha256(source.read_bytes()).hexdigest()
    )
