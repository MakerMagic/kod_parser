"""A scoped refresh must revalidate source content and answers, not only hashes."""

from copy import deepcopy

import pytest

from processors.matching.mathematics.core import load
from processors.matching.mathematics.refresh import ROOT, generate_artifacts, refresh
from processors.pre_final.storage import Store

RAW = next((ROOT / "data/raw/mathematics").glob("math_1_*.raw.json"))
MERGED = ROOT / "data/merged/mathematics/questions.json"
KEY = ROOT / "acquisition/local/mathematics/matdev/math_1_answers.json"


def test_persisted_repaired_selection_has_current_raw_and_verified_answers():
    validation = load(ROOT / "data/merged/mathematics/math_1_refresh_validation.json")
    key = load(KEY)
    raw = {q["id"]: q for q in load(RAW)["questions"]}
    selected = set(validation["selected_question_numbers"])
    rows = [
        q
        for q in load(MERGED)["questions"]
        if q["source_document_id"] == key["source_document_id"]
        and q["question_number"] in selected
    ]
    assert len(rows) == len(selected) == 28
    assert validation["issues"] == []
    for q in rows:
        assert Store().record(q["raw_reference"]) == raw[q["id"]]
        assert q["correct_answer"] == key["answers"][str(q["question_number"])]
        assert (
            Store().record(q["matching"]["key_reference"])["correct_answer"]
            == q["correct_answer"]
        )
        assert q["content"] == raw[q["id"]]["content"]
        assert q["options"] == raw[q["id"]]["options"]
        assert q["issues"] == []


def test_rebuild_current_question_and_key_instead_of_patching_hashes(tmp_path):
    original = load(MERGED)
    stale = deepcopy(original)
    row = next(
        q
        for q in stale["questions"]
        if q["id"] == "matdev_v1.1_9e6cc3f6b418fa0db4a7_q005"
    )
    row["content"] = [
        {"type": "unresolved_math", "reason": "Old multi-baseline fallback"}
    ]
    row["issues"] = [
        {"code": "uncertain_formula", "reason": "Old multi-baseline fallback"}
    ]
    row["raw_reference"]["sha256"] = "0" * 64
    row["correct_answer"] = "A"
    before = RAW.read_bytes()
    result, validation = refresh(stale, RAW, load(KEY), [5])
    new = next(q for q in result["questions"] if q["id"] == row["id"])
    raw = next(q for q in load(RAW)["questions"] if q["id"] == row["id"])
    assert RAW.read_bytes() == before
    assert new["content"] == raw["content"]
    assert new["options"] == raw["options"]
    assert new["issues"] == []
    assert new["correct_answer"] == "C"
    assert Store().record(new["raw_reference"]) == raw
    assert Store().record(new["matching"]["key_reference"])["correct_answer"] == "C"
    assert any(
        b.get("latex") == r"\begin{cases}2x+3y=5\\x+ay=2\end{cases}"
        for b in new["content"]
    )
    assert [q for q in result["questions"] if q["id"] != row["id"]] == [
        q for q in stale["questions"] if q["id"] != row["id"]
    ]
    assert validation["corrected_answers"] == [5]
    assert validation["verified_answers"] == 30
    assert refresh(result, RAW, load(KEY), [5])[0] == result
    paths = generate_artifacts(validation, tmp_path)
    assert "Total issues: 0" in paths[1].read_text(encoding="utf8")


def test_authoritative_native_key_disagreement_aborts_before_writing():
    key = load(KEY)
    key["answers"]["5"] = "A"
    with pytest.raises(ValueError, match="conflicts"):
        refresh(load(MERGED), RAW, key, [5])


def test_image_identity_and_selection_are_checked():
    key = load(KEY)
    key["image"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="image changed"):
        refresh(load(MERGED), RAW, key, [5])
    with pytest.raises(ValueError, match="selection"):
        refresh(load(MERGED), RAW, load(KEY), [999])


def test_invalid_option_content_cannot_be_admitted(monkeypatch):
    from processors.matching.mathematics import refresh as module

    original_build = module.build

    def broken(paths):
        data = original_build(paths)
        next(q for q in data["questions"] if q["question_number"] == 5)["options"][2][
            "content"
        ] = []
        return data

    monkeypatch.setattr(module, "build", broken)
    with pytest.raises(ValueError, match="cannot validate"):
        refresh(load(MERGED), RAW, load(KEY), [5])
