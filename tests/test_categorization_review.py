"""Frozen manual review is an audited annotation pass, not an ID rule engine."""

import re
from copy import deepcopy
from pathlib import Path

import pytest

from categorization.backtest import (
    inspect,
    load_categorized,
    render_html,
    report,
    update_guide,
)
from categorization.core import digest, read, validate_output, verify_refs
from categorization.review import LABELS, apply_review, in_scope

BASELINE = Path("inspections_categorization/before_rulebook_review.json")
ANNOTATIONS = Path("categorization/ps_review.json")


@pytest.fixture(scope="module")
def reviewed():
    if not BASELINE.exists() or not ANNOTATIONS.exists():
        pytest.skip("Optional frozen real review unavailable")
    baseline, annotations = read(BASELINE), read(ANNOTATIONS)
    result = apply_review(baseline, annotations, ANNOTATIONS)
    validate_output(result)
    return baseline, annotations, result


def test_complete_unique_population_and_all_three_assessments(reviewed):
    baseline, annotations, result = reviewed
    target = {r["record_key"] for r in baseline["records"] if in_scope(r)}
    decisions = annotations["decisions"]
    assert len(decisions) == len(target) == 260
    assert result["review_summary"]["all_needs_review"] == 262
    assert {d["record_key"] for d in decisions} == target
    for decision in decisions:
        assert set(decision["evaluated_subcategories"]) == {
            v[1] for v in LABELS.values()
        }
        assert len(decision["evidence"]) >= 60
        assert decision["matched_record_sha256"]
        assert decision["previous_categorization_sha256"]


def test_outside_review_population_byte_equivalent_and_all_upstream_preserved(reviewed):
    baseline, _, result = reviewed
    for old, new in zip(baseline["records"], result["records"], strict=True):
        if not in_scope(old):
            assert old == new
        else:
            assert {k: v for k, v in old.items() if k != "categorization"} == {
                k: v
                for k, v in new.items()
                if k not in {"categorization", "rulebook_review"}
            }
        assert old["question_view"] == new["question_view"]
        assert old["correct_answer"] == new["correct_answer"]
        assert old["final_explanation"] == new["final_explanation"]
    archive_file = Path(
        "inspections_categorization/representation_refinement/archive.json"
    )
    archived = read(archive_file) if archive_file.exists() else []
    for ref in baseline["inputs"]:
        try:
            verify_refs([ref])
        except ValueError:
            copies = [e["archive"] for e in archived if e["original"] == ref]
            assert (
                len(copies) == 1
            )  # An intentional upstream refresh must preserve exact old bytes.
            verify_refs(copies)


@pytest.mark.parametrize(
    "year,number,labels",
    [
        (2008, 6, {"Finding Procedures"}),  # Synchronised periodic states.
        (2009, 25, {"Relevant Selection"}),  # Applicable time zones, not recipient.
        (2009, 32, {"Identifying Similarity"}),  # Graph isomorphism.
        (2013, 26, {"Identifying Similarity"}),  # Unordered vs directed pairs.
        (2013, 43, {"Relevant Selection", "Finding Procedures"}),
        (2015, 38, {"Finding Procedures", "Identifying Similarity"}),
        (2015, 26, {"Finding Procedures"}),  # Generate filling states, not keyword IS.
        (2017, 26, {"Identifying Similarity"}),  # Folded vertex correspondence.
        (2019, 26, {"Finding Procedures"}),  # Roll a new cube state, not equivalence.
        (2022, 50, {"Identifying Similarity"}),  # Distance invariants across signs.
    ],
)
def test_materiality_and_procedure_equivalence_distinctions(
    reviewed, year, number, labels
):
    _, _, result = reviewed
    row = next(
        r
        for r in result["records"]
        if (r["identity"]["year"], r["identity"]["question_number"]) == (year, number)
    )
    c = row["categorization"]
    assert set(c["subcategories"]) == labels
    assert c["status"] == ("multi_label" if len(labels) > 1 else "classified")
    assert not c["issues"]
    assert c["confidence"]["human_approved"] is False


@pytest.mark.parametrize(
    "year,number", [(2008, 30), (2010, 36), (2014, 38), (2017, 20), (2021, 48)]
)
def test_direct_calculation_or_numeric_similarity_is_not_forced(reviewed, year, number):
    _, _, result = reviewed
    row = next(
        r
        for r in result["records"]
        if (r["identity"]["year"], r["identity"]["question_number"]) == (year, number)
    )
    assert row["categorization"]["status"] == "needs_review"
    assert not row["categorization"]["subcategories"]
    assert (
        row["rulebook_review"]["remaining_review_reason"] == "below_semantic_threshold"
    )


@pytest.mark.parametrize(
    "year,number",
    [(2014, 50), (2016, 32), (2017, 38), (2018, 50), (2019, 32), (2021, 7)],
)
def test_incomplete_or_ambiguous_upstream_record_stays_review(reviewed, year, number):
    _, _, result = reviewed
    row = next(
        r
        for r in result["records"]
        if (r["identity"]["year"], r["identity"]["question_number"]) == (year, number)
    )
    assert row["categorization"]["status"] == "needs_review"
    assert any(
        i["code"].startswith("upstream_") or i["code"] == "insufficient_question_data"
        for i in row["categorization"]["issues"]
    )


@pytest.mark.parametrize(
    "year,number",
    [
        (2016, 48),
        (2021, 44),
        (2022, 19),
        (2022, 20),
        (2022, 42),
        (2022, 43),
        (2022, 44),
    ],
)
def test_explanation_or_source_conflict_remains_visible(reviewed, year, number):
    _, _, result = reviewed
    row = next(
        r
        for r in result["records"]
        if (r["identity"]["year"], r["identity"]["question_number"]) == (year, number)
    )
    assert row["categorization"]["status"] == "needs_review"
    assert (
        row["rulebook_review"]["remaining_review_reason"]
        == "explanation_question_conflict"
    )


@pytest.mark.parametrize(
    "damage",
    [
        "omit",
        "duplicate",
        "out_of_scope",
        "skip_assessment",
        "changed_visual",
        "forced_upstream",
    ],
)
def test_annotations_fail_closed(reviewed, damage):
    baseline, annotations, _ = reviewed
    a = deepcopy(annotations)
    if damage == "omit":
        a["decisions"].pop()
    elif damage == "duplicate":
        a["decisions"].append(deepcopy(a["decisions"][0]))
    elif damage == "out_of_scope":
        a["decisions"][0]["record_key"] = next(
            r["record_key"] for r in baseline["records"] if not in_scope(r)
        )
    elif damage == "skip_assessment":
        a["decisions"][0]["evaluated_subcategories"].pop()
    elif damage == "changed_visual":
        next(d for d in a["decisions"] if d["visual_references"])[
            "visual_references"
        ].pop()
    else:
        d = next(
            d
            for d in a["decisions"]
            if d["remaining_review_reason"] == "incomplete_extraction"
        )
        d.update(
            status="classified",
            patterns=["ps_select"],
            material_subcategories=["Relevant Selection"],
            remaining_review_reason=None,
        )
    with pytest.raises((ValueError, KeyError)):
        apply_review(baseline, a, ANNOTATIONS)


def test_changed_question_or_explanation_requires_new_review(reviewed):
    baseline, annotations, _ = reviewed
    b = deepcopy(baseline)
    next(r for r in b["records"] if in_scope(r))["correct_answer"] = "Z"
    with pytest.raises(ValueError, match="baseline"):
        apply_review(b, annotations, ANNOTATIONS)


def test_reports_and_html_keep_resolved_and_unresolved_audit(reviewed, tmp_path):
    _, _, result = reviewed
    report(result, tmp_path / "issues.md")
    issues = (tmp_path / "issues.md").read_text(encoding="utf-8")
    assert "Complete rulebook review pass" in issues
    assert "(0 questions)" not in issues
    guide = tmp_path / "BACKTEST.MD"
    guide.write_text("# Categorization backtesting\n", encoding="utf-8")
    update_guide(result, guide)
    text = guide.read_text(encoding="utf-8")
    assert "[HTML](../inspections_categorization/" not in text
    assert len([r for r in result["records"] if r.get("rulebook_review")]) == 260
    current = load_categorized("data/categorized/blackstone/tsa.categorized.json")
    for year, number in [(2015, 38), (2022, 42)]:
        html = render_html(inspect(current, year=year, question=number))
        for expected in [
            "Main Body",
            "Main Question",
            "Main Answers",
            "Correct Answer",
            "Final Explanation",
            "Rulebook review",
            "previous_categorization",
        ]:
            assert expected in html
    assert digest(result) == digest(apply_review(reviewed[0], reviewed[1], ANNOTATIONS))


def test_report_command_exports_only_persisted_review_population(monkeypatch, tmp_path):
    import categorization.__main__ as cli

    rows = [
        {
            "identity": {"year": 2010, "question_number": 1},
            "rulebook_review": {"status": "classified"},
        },
        {
            "identity": {"year": 2010, "question_number": 2},
            "rulebook_review": {"status": "needs_review"},
        },
        {"identity": {"year": 2010, "question_number": 3}},
    ]
    calls = []
    monkeypatch.setattr(cli, "load_categorized", lambda path: {"records": rows})
    monkeypatch.setattr(cli, "report", lambda *args: None)
    monkeypatch.setattr(cli, "update_guide", lambda *args: None)
    monkeypatch.setattr(
        cli, "save_inspection", lambda data, **kwargs: calls.append(kwargs)
    )
    assert (
        cli.main(
            [
                "report",
                "--categorized-json",
                "input.json",
                "--output",
                str(tmp_path / "issues.md"),
                "--review-inspections-dir",
                str(tmp_path),
                "--backtest-guide",
                str(tmp_path / "BACKTEST.MD"),
            ]
        )
        == 0
    )
    assert [c["question"] for c in calls] == [1, 2]
    assert all(c["overwrite"] for c in calls)
    assert calls[0]["output"] == tmp_path / "2010_q001.html"


def test_issue_report_contains_only_current_unique_unresolved_records(
    reviewed, tmp_path
):
    _, _, result = reviewed
    output = tmp_path / "issues.md"
    report(result, output)
    text = output.read_text(encoding="utf-8")
    unresolved = {
        (r["identity"]["year"], r["identity"]["question_number"])
        for r in result["records"]
        if r["categorization"]["issues"]
    }
    all_rows = {
        (int(year), int(question))
        for year, question in re.findall(r"^\| (\d{4}) \| (\d+) \|", text, re.MULTILINE)
    }
    assert all_rows == unresolved
    assert f"Active unresolved question records: **{len(unresolved)}**" in text
    assert "## Before / after categorization audit" not in text
    for group in re.split(r"\n## ", text):
        heading = re.match(r"(.+) \((\d+) questions\)", group)
        if not heading:
            continue
        rows = re.findall(r"^\| (\d{4}) \| (\d+) \|", group, re.MULTILINE)
        assert len(rows) == len(set(rows)) == int(heading[2])
        assert rows


def test_issue_report_does_not_silently_hide_accepted_record_issues(reviewed, tmp_path):
    _, _, result = reviewed
    damaged = deepcopy(result)
    accepted = next(
        r for r in damaged["records"] if r["categorization"]["status"] == "classified"
    )
    accepted["categorization"]["issues"] = [
        {"code": "still_unresolved", "reason": "Not resolved"}
    ]
    with pytest.raises(ValueError, match="still has unresolved issues"):
        report(damaged, tmp_path / "issues.md")
