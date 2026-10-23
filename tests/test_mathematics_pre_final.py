"""Assembly-only regression coverage; the blocked rendering gate must hold."""

import json
from copy import deepcopy

import pytest

from processors.pre_final import mathematics as stage
from processors.pre_final.mathematics_artifacts import generate, render
from processors.pre_final.storage import ROOT, InvalidInput, Store, digest

CAT = ROOT / "data/categorized/mathematics/questions.json"
CLEAN = ROOT / "data/clean/mathematics/questions.json"
MATCHED = ROOT / "data/merged/mathematics/questions.json"


@pytest.fixture(scope="module")
def assembled():
    before = [p.read_bytes() for p in (CAT, CLEAN, MATCHED)]
    result = stage.build(CAT, CLEAN, MATCHED)
    assert before == [p.read_bytes() for p in (CAT, CLEAN, MATCHED)]
    return result


def test_full_dataset_eligibility_and_blocking_gate(assembled):
    data, validation = assembled
    assert data["summary"]["categorized_candidates"] == 519
    assert data["summary"]["matched_candidates"] == 519
    assert data["summary"]["included"] == 519
    assert data["summary"]["blocked_questions"] == 0
    assert data["summary"]["blocking_issues"] == 0
    assert data["summary"]["excluded_by_reason"] == {"categorization_not_eligible": 36}
    assert data["summary"]["ready_for_rendering"]
    stage.assert_ready(data)
    included = {q["id"] for q in data["questions"]}
    assert included.isdisjoint(q["id"] for q in validation["issues"])
    assert included.isdisjoint(q["id"] for q in validation["exclusions"])
    assert validation["issues"] == []


def test_complete_structured_validation(assembled):
    data, _ = assembled
    assert stage.validate_dataset(data) is data
    assert len({q["id"] for q in data["questions"]}) == len(data["questions"])
    assert len(
        {(q["source_document_id"], q["question_number"]) for q in data["questions"]}
    ) == len(data["questions"])
    for q in data["questions"]:
        assert q["id"] == f"{q['source_document_id']}_q{q['question_number']:03d}"
        assert q["correct_answer"] in [o["label"] for o in q["main_answers"]]
        assert q["main_question"] is None or q["main_question"]
        assert q["content_layout"] == "body_and_question"
        assert not {"year", "section", "explanation_by_ai", "difficulty"} & q.keys()


def test_exact_order_latex_assets_and_answers_preserved(assembled):
    data, _ = assembled
    clean = {
        q["id"]: q for q in json.loads(CLEAN.read_text(encoding="utf8"))["questions"]
    }
    matches = {
        q["id"]: q for q in json.loads(MATCHED.read_text(encoding="utf8"))["questions"]
    }
    for q in data["questions"]:
        original = clean[q["id"]]
        assert q["main_body"] == original["main_body"]
        assert q["main_question"] == original["main_question"]
        assert q["main_answers"] == original["options"]
        assert q["assets"] == original["assets"]
        assert q["correct_answer"] == matches[q["id"]]["correct_answer"]
    assert any(
        any(b["type"] == "math" for b in q["main_body"]) for q in data["questions"]
    )
    assert any(
        any(b["type"] == "visual" for b in q["main_body"]) for q in data["questions"]
    )


def one_question(assembled):
    data = deepcopy(assembled[0])
    data["questions"] = data["questions"][:1]
    data["summary"]["included"] = 1
    return data


@pytest.mark.parametrize(
    "field", ["id", "category", "main_body", "correct_answer", "assets", "provenance"]
)
def test_missing_required_fields_fail(assembled, field):
    data = one_question(assembled)
    del data["questions"][0][field]
    with pytest.raises(ValueError, match="required"):
        stage.validate_dataset(data)


def test_invalid_official_parent_and_other_fail(assembled):
    data = one_question(assembled)
    original = next(
        q for q in assembled[0]["questions"] if q["category"]["id"] != "Other"
    )
    data["questions"][0] = deepcopy(original)
    data["questions"][0]["category"] = {"id": "M9", "name": "Invalid"}
    with pytest.raises(ValueError, match="parent/child"):
        stage.validate_dataset(data)
    other = next(q for q in assembled[0]["questions"] if q["category"]["id"] == "Other")
    data["questions"][0] = deepcopy(other)
    assert data["questions"][0]["subcategory"] is None
    data["questions"][0]["categorization_evidence"]["certainty"] = "likely"
    with pytest.raises(ValueError, match="confirmed"):
        stage.validate_dataset(data)


def test_invalid_latex_option_order_correct_answer_and_asset_reference(assembled):
    q = deepcopy(assembled[0]["questions"][0])
    q["main_body"].append({"type": "math", "latex": r"\frac{1}{", "display": True})
    q["main_body"].append({"type": "visual", "asset_id": "missing"})
    q["main_answers"].reverse()
    q["correct_answer"] = "Z"
    codes = {p["code"] for p in stage.structural_issues(q, Store())}
    assert {
        "invalid_latex",
        "invalid_options",
        "invalid_correct_answer",
        "missing_asset_reference",
    } <= codes


def test_asset_hash_and_component_validation(assembled):
    q = deepcopy(assembled[0]["questions"][0])
    q["assets"][0]["sha256"] = "0" * 64
    q["main_body"].append({"type": "visual", "asset_id": q["assets"][0]["id"]})
    codes = {p["code"] for p in stage.structural_issues(q, Store())}
    assert {"invalid_asset", "asset_association"} <= codes


def test_question_image_is_a_structural_issue(assembled):
    q = deepcopy(
        next(
            row
            for row in assembled[0]["questions"]
            if any(b["type"] == "visual" for b in row["main_body"])
        )
    )
    body_visual = next(b for b in q["main_body"] if b["type"] == "visual")
    q["main_question"] = [deepcopy(body_visual)]
    codes = {p["code"] for p in stage.structural_issues(q, Store())}
    assert "image_in_main_question" in codes


def test_duplicates_are_rejected(assembled):
    data = one_question(assembled)
    data["questions"].append(deepcopy(data["questions"][0]))
    data["summary"]["included"] = 2
    with pytest.raises(ValueError, match="Duplicate"):
        stage.validate_dataset(data)


def test_changed_content_is_not_a_presentation_correction(assembled):
    data = one_question(assembled)
    data["questions"][0]["main_body"].append({"type": "text", "text": "Invented text"})
    with pytest.raises(ValueError, match="changed upstream"):
        stage.validate_dataset(data)


def test_build_deterministic(assembled):
    assert digest(stage.build(CAT, CLEAN, MATCHED)) == digest(assembled)


def test_source_prefix_build_can_assemble_only_the_second_set():
    merged = json.loads(MATCHED.read_text(encoding="utf8"))
    source_ids = {
        source_id
        for source_id, source in merged["sources"].items()
        if source["filename"].startswith("Test_")
    }
    data, _ = stage.build(CAT, CLEAN, MATCHED, source_document_ids=source_ids)
    assert data["summary"]["source_document_ids"] == sorted(source_ids)
    assert data["questions"]
    assert all(q["source_pdf"].startswith("Test_") for q in data["questions"])
    assert data["summary"]["included"] == 180
    assert data["summary"]["blocking_issues"] == 0


def test_cli_generates_only_second_set_prefinal_and_artifacts(tmp_path):
    output, docs = tmp_path / "second-set", tmp_path / "inspection"
    assert (
        stage.main(
            [
                "--source-prefix",
                "Test_",
                "--output-dir",
                str(output),
                "--docs-dir",
                str(docs),
            ]
        )
        == 0
    )
    data = json.loads((output / "questions.json").read_text(encoding="utf8"))
    assert data["summary"]["included"] == 180
    assert all(q["source_pdf"].startswith("Test_") for q in data["questions"])
    assert "Total issues: 0" in (docs / "PRE_FINAL_ISSUES.md").read_text(
        encoding="utf8"
    )


def test_cli_writes_pair_but_no_rendering_when_blocked(tmp_path, monkeypatch):
    original_load = Store.load

    def stale_matching(self, path):
        data = original_load(self, path)
        if self.path(path) == MATCHED.resolve() and not getattr(
            self, "_stale_injected", False
        ):
            data = deepcopy(data)
            q = next(
                row
                for row in data["questions"]
                if row["id"] == "matdev_v1.1_9e6cc3f6b418fa0db4a7_q005"
            )
            q["raw_reference"]["sha256"] = "0" * 64
            q["issues"].append(
                {
                    "code": "uncertain_formula",
                    "reason": "Regression: stale unresolved formula",
                }
            )
            self.documents[self.path(path)] = data
            self._stale_injected = True
        return data

    monkeypatch.setattr(Store, "load", stale_matching)
    out, docs = tmp_path / "pre_final", tmp_path / "docs"
    args = ["--output-dir", str(out), "--docs-dir", str(docs)]
    assert stage.main(args) == 2
    before = [(out / p).read_bytes() for p in ("questions.json", "validation.json")]
    assert (docs / "PRE_FINAL_BACKTESTING.md").is_file()
    assert "Total issues: 2" in (docs / "PRE_FINAL_ISSUES.md").read_text(
        encoding="utf8"
    )
    assert not list(tmp_path.rglob("*.html"))
    assert not list(tmp_path.rglob("QUESTION_RENDERING*.md"))
    assert stage.main(args) == 2
    assert before == [
        (out / p).read_bytes() for p in ("questions.json", "validation.json")
    ]
    assert render(out) == render(out)
    data = json.loads((out / "questions.json").read_text(encoding="utf8"))
    assert data["summary"]["blocked_questions"] == 1
    with pytest.raises(InvalidInput, match="prohibit"):
        stage.assert_ready(data)


def test_zero_issue_prefinal_still_generates_pair(assembled, tmp_path):
    data, findings = deepcopy(assembled)
    data["summary"].update(
        blocking_issues=0, blocked_questions=0, ready_for_rendering=True
    )
    findings["summary"] = data["summary"]
    findings["issues"] = []
    (tmp_path / "questions.json").write_text(json.dumps(data), encoding="utf8")
    (tmp_path / "validation.json").write_text(json.dumps(findings), encoding="utf8")
    paths = generate(tmp_path, tmp_path / "docs")
    assert "Total issues: 0" in paths[1].read_text(encoding="utf8")
    stage.assert_ready(data)


def test_schema_contract_is_mathematics_specific():
    schema = stage.SCHEMA["$defs"]["question"]
    assert schema["properties"]["source"]["const"] == "Mathematics"
    assert "Other" in schema["properties"]["category"]["properties"]["id"]["enum"]
    assert schema["properties"]["main_body"]["items"]["$ref"] == "#/$defs/block"
