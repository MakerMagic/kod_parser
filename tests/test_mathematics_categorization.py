"""Mathematics categorization contract; no upstream processing is executed."""

import copy
import json
from pathlib import Path

import pytest

from categorization.core import digest, read
from categorization.mathematics.__main__ import main
from categorization.mathematics.core import (
    OTHER,
    OTHER_TOPICS,
    build,
    eligible,
    semantic_content,
    taxonomy,
    validate_assessment,
)

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data/clean/mathematics/questions.json"
REVIEWS = ROOT / "data/categorized/mathematics/assessments.json"


@pytest.fixture(scope="module")
def source():
    return read(CLEAN)


@pytest.fixture(scope="module")
def reviews():
    return read(REVIEWS)["assessments"]


def decision(child="M4.2", alternative="M2.7"):
    return {
        "status": "categorized",
        "subcategory_id": child,
        "dominant_operation": "Simplify symbolic fractional indices",
        "alternative_subcategory_id": alternative,
        "why_not_alternative": "The base is symbolic, not a numerical power.",
    }


def test_official_hierarchy():
    catalog, parents, children = taxonomy()
    assert [(k, v["name"]) for k, v in parents.items()] == [
        ("M1", "Units"),
        ("M2", "Number"),
        ("M3", "Ratio and proportion"),
        ("M4", "Algebra"),
        ("M5", "Geometry"),
    ]
    assert catalog["source"]["sha256"]
    for parent, count in zip(parents, (2, 14, 11, 19, 19)):
        assert {s for s, v in children.items() if v["category_id"] == parent} == {
            f"{parent}.{i}" for i in range(1, count + 1)
        }
    assert all(v["description"] and v["source_page"] for v in children.values())


@pytest.mark.parametrize(
    "child,alternative",
    [
        ("M1.1", "M3.9"),
        ("M2.7", "M4.2"),
        ("M3.8", "M2.10"),
        ("M4.2", "M2.7"),
        ("M5.18", "M3.9"),
    ],
)
def test_each_parent_accepts_one_official_child(child, alternative):
    validate_assessment(decision(child, alternative), taxonomy()[2])


@pytest.mark.parametrize(
    "change",
    [
        {"subcategory_id": ["M4.2", "M2.7"]},
        {"subcategory_id": "Other"},
        {"subcategory_id": None},
        {"category_id": "M5"},
        {"categories": ["M4", "M2"]},
        {"subcategories": ["M4.2"]},
        {"alternative_subcategory_id": "M4.2"},
        {"alternative_subcategory_id": "M9.1"},
        {"dominant_operation": ""},
        {"why_not_alternative": ""},
        {"status": "guessed"},
    ],
)
def test_reject_invalid_classifier_output(change):
    value = decision()
    value.update(change)
    with pytest.raises(ValueError):
        validate_assessment(value, taxonomy()[2])


def test_uncertainty_requires_reason_and_no_guessed_label():
    value = {
        "status": "needs_review",
        "issue_code": "taxonomy_gap",
        "reason": "Probability is absent from the official specification.",
    }
    validate_assessment(value, taxonomy()[2])
    for change in (
        {"reason": ""},
        {"reason": ["ambiguous"]},
        {"subcategory_id": "M2.10"},
    ):
        with pytest.raises(ValueError):
            validate_assessment({**value, **change}, taxonomy()[2])


def test_reject_nonobject_classifier_output():
    with pytest.raises(TypeError):
        validate_assessment([decision()], taxonomy()[2])


def test_eligibility_excludes_any_upstream_issue(source):
    q = copy.deepcopy(next(q for q in source["questions"] if eligible(q)))
    for field in ("issues", "cleaning_issues"):
        changed = copy.deepcopy(q)
        changed[field] = [{"reason": "Unresolved upstream evidence"}]
        assert not eligible(changed)
    q["cleaning"]["status"] = "needs_review"
    assert not eligible(q)


def test_semantic_hash_ignores_identity_but_preserves_full_content(source):
    q = next(q for q in source["questions"] if eligible(q))
    original = digest(semantic_content(q))
    altered = copy.deepcopy(q)
    altered.update(id="different-id", question_number=999, source_document_id="another")
    assert digest(semantic_content(altered)) == original
    altered["options"][0]["content"].append({"type": "math", "latex": "x^{99}"})
    assert digest(semantic_content(altered)) != original
    visual = next(
        q
        for q in source["questions"]
        if eligible(q) and any(b["type"] == "visual" for b in q["content"])
    )
    altered = copy.deepcopy(visual)
    asset_id = next(b["asset_id"] for b in altered["content"] if b["type"] == "visual")
    next(a for a in altered["assets"] if a["id"] == asset_id)["sha256"] = (
        "changed-visual"
    )
    assert digest(semantic_content(altered)) != digest(semantic_content(visual))


@pytest.mark.parametrize(
    "pdf,number,expected",
    [
        ("math_10.pdf", 6, "M2.11"),  # numerical nested surds
        ("math_10.pdf", 4, "M4.7"),  # algebraic powers, formula subject
        ("math_10.pdf", 2, "M2.10"),  # fraction/percentage conversion
        ("math_10.pdf", 28, "M3.8"),  # percentage change
        ("math_2.pdf", 24, "M5.17"),  # geometry outweighs supporting arithmetic
        ("math_10.pdf", 17, "M5.18"),  # exact triangle trig, not general proportion
        ("math_10.pdf", 9, "M4.10"),  # line graph gradient
        ("math_10.pdf", 27, "M2.5"),  # set counting is not probability
        ("math_7.pdf", 22, "M5.19"),  # vector coefficients
        ("Test_8.pdf", 21, "M1.1"),  # compound rates
    ],
)
def test_reviewed_boundaries(source, reviews, pdf, number, expected):
    q = next(
        q
        for q in source["questions"]
        if q["question_number"] == number
        and source["sources"][q["source_document_id"]]["filename"] == pdf
    )
    value = reviews[digest(semantic_content(q))]
    assert value["subcategory_id"] == expected
    assert value["dominant_operation"] and value["why_not_alternative"]


def test_complete_coverage_invariants_and_reuse(reviews):
    data, validation = build(CLEAN, reviews)
    assert data["summary"]["eligible"] == 555
    assert data["summary"]["categorized"] + data["summary"]["unresolved"] == 555
    assert data["summary"]["excluded"] == 2
    assert len({q["id"] for q in data["questions"]}) == 555
    assert all(
        q["assessment"]["status"] != "missing_assessment" for q in data["questions"]
    )
    assert not any(
        i["code"] == "missing_assessment"
        for q in data["questions"]
        for i in q["categorization_issues"]
    )
    _, parents, children = taxonomy()
    for q in data["questions"]:
        if q["category"] == OTHER:
            assert q["subcategory"] is None
            assert q["assessment"]["topic"] in OTHER_TOPICS
            assert q["assessment"]["certainty"] == "confirmed"
            assert not q["categorization_issues"]
        elif q["category"]:
            assert q["category"] == parents[q["subcategory"]["category_id"]]
            assert q["subcategory"] == children[q["assessment"]["subcategory_id"]]
            assert not q["categorization_issues"]
        else:
            assert q["subcategory"] is None and q["categorization_issues"][0]["reason"]
    assert (
        sum(data["summary"]["subcategory_distribution"].values())
        + data["summary"]["category_distribution"]["Other"]
        == data["summary"]["categorized"]
    )
    assert len(validation["unresolved"]) == data["summary"]["unresolved"]
    # A rerun must retain all valid existing decisions without reclassification.
    rerun, _ = build(CLEAN, {}, data)
    assert [q for q in rerun["questions"] if q["category"]] == [
        q for q in data["questions"] if q["category"]
    ]


def test_cli_deterministic_and_input_immutable(tmp_path):
    before = CLEAN.read_bytes()
    args = [
        "--clean-json",
        str(CLEAN),
        "--assessments",
        str(REVIEWS),
        "--output-dir",
        str(tmp_path),
    ]
    assert main(args) == 0
    first = (tmp_path / "questions.json").read_bytes()
    assert (tmp_path / "inspection/CATEGORIZATION_BACKTESTING.md").is_file()
    assert (tmp_path / "inspection/CATEGORIZATION_ISSUES.md").is_file()
    assert main(args) == 0
    assert (tmp_path / "questions.json").read_bytes() == first
    assert CLEAN.read_bytes() == before


def test_changed_content_does_not_reuse_classification(source, reviews, tmp_path):
    previous, _ = build(CLEAN, reviews)
    altered = copy.deepcopy(source)
    q = next(q for q in altered["questions"] if eligible(q))
    q["content"].append({"type": "text", "text": "Changed content invalidates review"})
    path = tmp_path / "clean.json"
    path.write_text(json.dumps(altered), encoding="utf8")
    data, _ = build(path, reviews, previous)
    row = next(r for r in data["questions"] if r["id"] == q["id"])
    assert row["category"] is None
    assert row["categorization_issues"][0]["code"] == "missing_assessment"


def test_cli_rejects_upstream_output():
    with pytest.raises(ValueError, match="cannot overwrite"):
        main(["--output-dir", str(ROOT / "data/raw/mathematics")])


def other_decision(topic="Probability"):
    return {
        "status": "categorized",
        "category_id": "Other",
        "subcategory_id": None,
        "topic": topic,
        "certainty": "confirmed",
        "dominant_operation": "Compute an event probability",
        "evidence": "What is the probability of rolling a six?",
    }


@pytest.mark.parametrize("topic", OTHER_TOPICS)
def test_other_has_no_subcategory(topic):
    validate_assessment(other_decision(topic), taxonomy()[2])


@pytest.mark.parametrize(
    "change",
    [
        {"topic": "Trigonometry"},
        {"topic": "Other"},
        {"topic": ["Probability", "Statistics"]},
        {"certainty": "likely"},
        {"certainty": None},
        {"evidence": ""},
        {"dominant_operation": ""},
        {"subcategory_id": "Other"},
        {"subcategory_id": "M2.5"},
        {"categories": ["Other"]},
    ],
)
def test_reject_unapproved_or_uncertain_other(change):
    with pytest.raises(ValueError):
        validate_assessment({**other_decision(), **change}, taxonomy()[2])


def test_other_counts_and_uncertain_examples(reviews):
    data, validation = build(CLEAN, reviews)
    assert data["summary"]["categorized"] == 519
    assert data["summary"]["unresolved"] == 36
    assert data["summary"]["other_topic_distribution"] == {
        "Probability": 31,
        "Statistics": 10,
        "Calculus": 17,
        "Logarithms": 7,
    }
    rows = {(q["source_pdf"], q["question_number"]): q for q in data["questions"]}
    assert ("Test_2.pdf", 24) not in rows
    cleaned = read(CLEAN)
    uncertain = next(
        q
        for q in cleaned["questions"]
        if q["question_number"] == 24
        and cleaned["sources"][q["source_document_id"]]["filename"] == "Test_2.pdf"
    )
    assert uncertain["cleaning"]["status"] == "review"
    assert uncertain["cleaning_issues"][0]["code"] == "question_boundary_ambiguous"
    assert any(e["id"] == uncertain["id"] for e in validation["excluded"])
    assert (
        rows["Test_1.pdf", 27]["category"] is None
    )  # trig is not an approved fallback
    assert rows["Test_5.pdf", 9]["category"] is None  # absent equation is not Other
    assert rows["Test_1.pdf", 22]["assessment"]["topic"] == "Calculus"
    assert rows["math_10.pdf", 18]["assessment"]["topic"] == "Probability"
    assert all(
        q["categorization_issues"][0]["reason"] for q in validation["unresolved"]
    )


def test_valid_official_decisions_cannot_be_displaced_by_fallback(reviews):
    original, _ = build(CLEAN, reviews)
    official = [
        q for q in original["questions"] if q["category"] and q["category"] != OTHER
    ]
    assert len(official) == 454
    replacements = {q["content_sha256"]: other_decision() for q in official}
    result, _ = build(CLEAN, replacements, original)
    assert [
        q for q in result["questions"] if q["category"] and q["category"] != OTHER
    ] == official
