"""Population-level explanation coverage and preservation regressions."""
import json
from hashlib import sha256
from copy import deepcopy
from pathlib import Path

import pytest

from parsers.mathematics.structure import walk
from processors.explanations.mathematics import (
    INPUT, OUTPUT, ROOT, artifacts, build, validate_complete, validate_explanation,
)


def read(path):
    return Path(path).read_text(encoding="utf-8-sig")


@pytest.fixture(scope="module")
def population():
    return json.loads(read(INPUT)), json.loads(read(OUTPUT))


def test_full_rendered_population_has_one_explanation_or_concrete_blocker(population):
    source, output = population
    rendering = json.loads(read(ROOT / "data/question_rendering/mathematics/validation.json"))
    assert rendering["summary"]["renderable"] == len(source["questions"])
    assert rendering["issues"] == []
    counts = validate_complete(source, output)
    assert counts["eligible_without_explanation"] == 0
    assert counts["eligible_questions"] == len(output["questions"])
    assert counts["blocking_questions"] == len(output["issues"])
    assert counts["total_questions"] == counts["eligible_questions"] + counts["blocking_questions"]


def test_imported_text_is_byte_for_byte_preserved_and_every_ai_flag_true(population):
    source, output = population
    inputs = json.loads(read(ROOT / "inspections/mathematics/TEXT_ONLY_QUESTIONS_AI_MATH_EXPLANATIONS"))
    supplied = {r["id"]: r["explanation"] for r in inputs}
    imported = [r for r in output["questions"] if r.get("explanation_origin") == "user_supplied_ai"]
    assert imported
    qs = {q["id"]: q for q in source["questions"]}
    for row in imported:
        assert row["final_explanation"]["blocks"][0]["text"] == supplied[row["id"]]
    for row in output["questions"]:
        assert row["final_explanation"]["explanation_by_ai"] is True
        assert validate_explanation(qs[row["id"]], row) == []


def test_image_questions_are_explained_and_valid_prior_records_preserved(population):
    source, output = population
    by_id = {q["id"]: q for q in source["questions"]}
    direct = [r for r in output["questions"] if r.get("explanation_origin") == "assistant_direct"]
    image_direct = [
        r for r in direct
        if any(b["type"] == "visual" for b in walk(
            by_id[r["id"]]["main_body"] + (by_id[r["id"]]["main_question"] or [])
            + [b for a in by_id[r["id"]]["main_answers"] for b in a["content"]]
        ))
    ]
    assert len(image_direct) > 100
    preserved = [r for r in output["questions"] if "explanation_origin" not in r]
    assert len(preserved) == 74
    prior_corrections = json.loads(read(ROOT / "data/explanations/mathematics/prior_explanation_corrections.json"))
    assert len(prior_corrections) == 4
    for row in prior_corrections:
        assert row["id"] == row["original"]["id"] == row["corrected"]["id"]


def test_publisher_and_stage_artifacts_are_deterministic(population):
    source, output = population
    rebuilt = build(source, existing=output)
    assert rebuilt == output
    backtesting, issues = artifacts(rebuilt)
    assert backtesting == read(ROOT / "docs/mathematics/EXPLANATION_BACKTESTING.md")
    assert issues == read(ROOT / "docs/mathematics/EXPLANATION_ISSUES.md")
    assert f"Total issues: {len(rebuilt['issues'])}" in issues


def test_completeness_rejects_silent_missing_or_placeholder(population):
    source, output = population
    bad = deepcopy(output)
    bad["questions"].pop()
    with pytest.raises(ValueError, match="missing"):
        validate_complete(source, bad)
    bad = deepcopy(output)
    bad["issues"][0]["code"] = "explanation_not_yet_authored"
    with pytest.raises(ValueError, match="authoring"):
        validate_complete(source, bad)


def test_upstream_and_supplied_inputs_and_preserved_records_are_unchanged(population):
    _, output = population
    audit = json.loads(read(ROOT / "data/explanations/mathematics/completion_audit.json"))
    for path, expected in audit["protected_hashes"].items():
        assert sha256((ROOT / path).read_bytes()).hexdigest() == expected
    rows = {r["id"]: r for r in output["questions"]}
    for qid, expected in audit["preserved_record_sha256"].items():
        actual = json.dumps(rows[qid], ensure_ascii=False, sort_keys=True).encode("utf8")
        assert sha256(actual).hexdigest() == expected
