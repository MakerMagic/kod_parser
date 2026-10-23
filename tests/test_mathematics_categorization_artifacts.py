"""Generated stage artifact completeness, zero issues and stage isolation."""

import copy
import json
from collections import Counter

import pytest

from categorization.core import read
from categorization.mathematics.artifacts import CANONICAL, generate, render
from categorization.mathematics.core import OTHER_TOPICS
from processors.stage_artifacts import (
    stage_paths,
    validate_stage_pairs,
    write_stage_pair,
)


def snapshot(rows):
    data = copy.deepcopy(read(CANONICAL))
    data["questions"] = copy.deepcopy(rows)
    cats = Counter(q["category"]["id"] for q in rows if q["category"])
    children = Counter(q["subcategory"]["id"] for q in rows if q["subcategory"])
    topics = Counter(
        q["assessment"]["topic"]
        for q in rows
        if q["category"] and q["category"]["id"] == "Other"
    )
    data["summary"].update(
        eligible=len(rows),
        categorized=sum(cats.values()),
        unresolved=sum(bool(q["categorization_issues"]) for q in rows),
        category_distribution=dict(cats),
        subcategory_distribution=dict(children),
        other_topic_distribution={t: topics[t] for t in OTHER_TOPICS},
    )
    return data


def save(path, data):
    path.write_text(json.dumps(data), encoding="utf8")
    return path


def test_canonical_issue_coverage_and_distributions(tmp_path):
    data = read(CANONICAL)
    before = CANONICAL.read_bytes()
    paths = generate(CANONICAL, tmp_path)
    back, issues = (p.read_text(encoding="utf8") for p in paths)
    findings = [(q, i) for q in data["questions"] for i in q["categorization_issues"]]
    assert len(findings) == 36
    assert f"Total issues: {len(findings)}" in issues
    assert issues.count("- Exact issue type:") == len(findings)
    for q, issue in findings:
        assert q["id"] in issues and q["source_pdf"] in issues
        assert f"Q{q['question_number']}" in issues
        assert issue["code"] in issues
        from categorization.mathematics.artifacts import md

        assert md(issue["reason"]) in issues
        assert q["id"] in back
    assert "categorized: 519" in back
    for child, count in data["summary"]["subcategory_distribution"].items():
        assert f"| {child} | {count} |" in back
    for topic, count in data["summary"]["other_topic_distribution"].items():
        assert f"| {topic} | {count} |" in back
    assert CANONICAL.read_bytes() == before
    first = [p.read_bytes() for p in paths]
    generate(CANONICAL, tmp_path)
    assert first == [p.read_bytes() for p in paths]


def test_resolved_issues_disappear_and_zero_pair_still_exists(tmp_path):
    rows = read(CANONICAL)["questions"]
    unresolved = next(q for q in rows if q["categorization_issues"])
    source = save(tmp_path / "questions.json", snapshot([unresolved]))
    docs = tmp_path / "docs"
    _, issue_path = generate(source, docs)
    assert unresolved["id"] in issue_path.read_text(encoding="utf8")
    save(source, snapshot([next(q for q in rows if q["category"])]))
    paths = generate(source, docs)
    assert all(p.exists() for p in paths)
    issues = issue_path.read_text(encoding="utf8")
    assert "Total issues: 0" in issues
    assert "No unresolved categorization issues currently exist." in issues
    assert unresolved["id"] not in issues


def test_multiple_findings_on_one_question_are_not_collapsed(tmp_path):
    q = copy.deepcopy(
        next(q for q in read(CANONICAL)["questions"] if q["categorization_issues"])
    )
    q["categorization_issues"].append(
        {"code": "additional_evidence", "reason": "A distinct missing component."}
    )
    source = save(tmp_path / "questions.json", snapshot([q]))
    _, issues = render(source)
    assert "Total issues: 2" in issues and "Affected questions: 1" in issues
    assert issues.count("- Exact issue type:") == 2


@pytest.mark.parametrize(
    "change",
    [
        {"categorized": 0},
        {"unresolved": 0},
        {"eligible": 0},
        {"category_distribution": {}},
        {"subcategory_distribution": {}},
        {"other_topic_distribution": {}},
    ],
)
def test_structured_count_mismatch_fails(tmp_path, change):
    data = read(CANONICAL)
    data["summary"].update(change)
    source = save(tmp_path / "questions.json", data)
    with pytest.raises(ValueError, match="disagree"):
        render(source)


def test_missing_or_stale_pair_fails_validation(tmp_path):
    expected = render(CANONICAL)
    with pytest.raises(ValueError, match="Missing or stale"):
        validate_stage_pairs([(tmp_path, "CATEGORIZATION", expected)])
    paths = write_stage_pair(tmp_path, "CATEGORIZATION", expected)
    paths[1].write_text("Total issues: 0\n", encoding="utf8")
    with pytest.raises(ValueError, match="Missing or stale"):
        validate_stage_pairs([(tmp_path, "CATEGORIZATION", expected)])


def test_all_executed_stages_are_independent(tmp_path):
    pair = ("# Generated backtesting\n", "# Issues\nTotal issues: 0\n")
    first = write_stage_pair(tmp_path, "CLEANING", pair)
    before = [p.read_bytes() for p in first]
    second = write_stage_pair(tmp_path, "CATEGORIZATION", render(CANONICAL))
    assert set(first).isdisjoint(second)
    assert before == [p.read_bytes() for p in first]
    specs = [
        (tmp_path, "CLEANING", pair),
        (tmp_path, "CATEGORIZATION", render(CANONICAL)),
    ]
    validate_stage_pairs(specs)
    with pytest.raises(ValueError, match="overlap"):
        validate_stage_pairs([specs[0], specs[0]])
    with pytest.raises(ValueError, match="both"):
        write_stage_pair(tmp_path, "MATCHING", (pair[0],))
    with pytest.raises(ValueError, match="stage name"):
        stage_paths(tmp_path, "../ISSUES")
