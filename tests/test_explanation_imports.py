"""Exact import identity, immutable sources, visual evidence and real backtests."""

import json
from copy import deepcopy
from hashlib import sha256
from itertools import pairwise
from pathlib import Path

import pytest

from processors.explanations.validator import validate
from processors.matching.explanation_imports import (
    WORKSPACE,
    apply_visuals,
    import_text,
    load_sources,
    read_entries,
    visual_context,
)
from processors.matching.export_without_explanations import has_explanation


def sample():
    identifier = "blackstone_2017_4502/11_section_1_q1"
    record = {
        "identity": {"year": 2017, "section": "section_1", "question_number": 1},
        "status": "matched",
        "correct_answer": "B",
        "question": {
            "question_id": identifier,
            "options": [
                {"label": "A", "text": "First"},
                {"label": "B", "text": "Second"},
            ],
        },
        "final_explanation": {"status": "unavailable", "blocks": []},
    }
    entry = {
        "number": 1,
        "question_record": identifier,
        "main_reasoning": "The stated rule requires two conditions together, and only the second option supplies both of them.",
        "incorrect_options": {
            "A": "The first choice supplies just one condition, leaving the second necessary condition unsatisfied."
        },
    }
    return (
        {"records": [record]},
        entry,
        {"path": "supplied.json", "sha256": "preserved"},
    )


def test_identity_key_and_provenance_without_mutating_input():
    data, entry, reference = sample()
    before = deepcopy(data)
    updated, remaining = import_text(data, [(entry, reference)])
    assert not remaining and data == before
    result = updated["records"][0]
    assert result["question"] == before["records"][0]["question"]
    assert result["final_explanation"]["explanation_by_ai"] is True
    assert result["final_explanation"]["source_reference"] == reference
    assert result["final_explanation"]["blocks"][0]["text"] == entry["main_reasoning"]


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "wrong_record",
        "wrong_number",
        "wrong_answer",
        "unmatched",
        "existing",
    ],
)
def test_unsafe_imports_never_overwrite(change):
    data, entry, reference = sample()
    if change == "wrong_record":
        data["records"][0]["question"]["question_id"] = "different"
    elif change == "wrong_number":
        entry["number"] = 2
    elif change == "wrong_answer":
        entry["correct_answer"] = "A"
    elif change == "unmatched":
        data["records"][0]["status"] = "conflict"
    elif change == "existing":
        data["records"][0]["final_explanation"] = {
            "status": "available",
            "explanation_by_ai": False,
            "blocks": [{"type": "paragraph", "text": "Existing source explanation"}],
        }
    before = deepcopy(data)
    supplied = [(entry, reference)] * (2 if change == "duplicate" else 1)
    if change == "wrong_number":
        with pytest.raises(ValueError, match="Year/number"):
            import_text(data, supplied)
    else:
        updated, _ = import_text(data, supplied)
        assert updated["records"] == data["records"]
        assert all(
            e["status"] == "import_rejected"
            for e in updated["explanation_imports"]["audit"]
        )
    assert data == before


def test_recovery_preserves_objects_and_rejects_unaccounted_content(tmp_path):
    _, entry, _ = sample()
    path = tmp_path / "pasted.json"
    original = '{"explanations": [' + json.dumps(entry) + '\n{"not_generated": []}'
    path.write_text(original, encoding="utf-8")
    entries, warning = read_entries(path)
    assert warning.startswith("Malformed container") and entries[0][0] == entry
    start, end = entries[0][1]["character_range"]
    assert json.loads(original[start:end]) == entry
    assert path.read_text(encoding="utf-8") == original
    path.write_text(original + "meaningful lost content", encoding="utf-8")
    with pytest.raises(ValueError, match="Unaccounted"):
        read_entries(path)


def test_import_is_idempotent_and_changed_source_is_conflict():
    data, entry, reference = sample()
    first, _ = import_text(data, [(entry, reference)])
    second, _ = import_text(first, [(entry, reference)])
    assert second["records"] == first["records"]
    assert second["explanation_imports"]["audit"][0]["status"] == "imported_existing"
    changed, _ = import_text(first, [(entry, {**reference, "sha256": "changed"})])
    assert changed["records"] == first["records"]
    assert (
        "existing_explanation_conflict"
        in changed["explanation_imports"]["audit"][0]["errors"]
    )


def real_data():
    path = Path("tmp/explanation_imports_before.matched.json")
    if not path.exists():
        path = Path("data/merged/blackstone/tsa_2017-2019.matched.json")
    if not path.exists():
        pytest.skip("Local question dataset unavailable")
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_inputs_all_recover_and_validate_with_unique_stable_ids():
    entries, warnings = load_sources(
        "docs/2017-2019_questions_text_with_explanation_ai_generated"
    )
    assert len(entries) == 150 and len(warnings) == 3
    assert len({e["question_record"] for e, _ in entries}) == 150
    data = real_data()
    result, remaining = import_text(data, entries)
    assert len(remaining) == 53
    assert (
        sum(
            e["status"].startswith("imported")
            for e in result["explanation_imports"]["audit"]
        )
        == 97
    )
    assert not any(
        e["status"] == "import_rejected" for e in result["explanation_imports"]["audit"]
    )
    for entry, reference in entries:
        assert (
            sha256(Path(reference["path"]).read_bytes()).hexdigest()
            == reference["sha256"]
        )


def test_visuals_bind_all_assets_and_reject_stale_or_incomplete_review(tmp_path):
    data = real_data()
    # Build a single-record candidate in an otherwise empty year manifest.
    original = json.loads(
        (WORKSPACE / "2017/candidates.json").read_text(encoding="utf-8")
    )
    original["questions"] = [e for e in original["questions"] if e["number"] == 7]
    explanations = json.loads(
        (WORKSPACE / "2017/explanations.json").read_text(encoding="utf-8")
    )
    explanations["explanations"] = [
        e for e in explanations["explanations"] if e["number"] == 7
    ]
    target = next(
        r
        for r in data["records"]
        if r["identity"] == {"year": 2017, "section": "section_1", "question_number": 7}
    )
    target["final_explanation"] = {"status": "unavailable", "blocks": []}
    for year in (2017, 2018, 2019):
        folder = tmp_path / str(year)
        folder.mkdir()
        (folder / "candidates.json").write_text(
            json.dumps(original if year == 2017 else {"questions": []}),
            encoding="utf-8",
        )
    path = tmp_path / "2017/explanations.json"
    for defect, error in (
        ("context", "visual_context_changed"),
        ("assets", "visual_review_incomplete"),
        ("length", "explanation_too_long"),
    ):
        broken = deepcopy(explanations)
        entry = broken["explanations"][0]
        if defect == "context":
            entry["context_sha256"] = "stale"
        elif defect == "assets":
            entry["review"]["assets_reviewed"] = []
        else:
            entry["main_reasoning"] = "A meaningful but overlong explanation. " * 100
        path.write_text(json.dumps(broken), encoding="utf-8")
        result = apply_visuals(data, tmp_path)
        assert error in result["visual_explanations"]["audit"][0]["errors"]
        assert not has_explanation(result["records"][data["records"].index(target)])


def test_actual_visual_candidates_and_accepted_backtest_content():
    data = json.loads(
        Path("data/merged/blackstone/tsa_2017-2019.matched.json").read_text(
            encoding="utf-8"
        )
    )
    from processors.matching.backtest import inspect_question, render_html

    for year in (2017, 2018, 2019):
        content = json.loads(
            (WORKSPACE / str(year) / "explanations.json").read_text(encoding="utf-8")
        )
        for entry in content["explanations"]:
            if entry.get("status") in ("rejected", "text_sufficient_illustration"):
                continue
            record = next(
                r
                for r in data["records"]
                if r["identity"]["year"] == year
                and r["identity"]["question_number"] == entry["number"]
            )
            value = {
                k: entry[k]
                for k in ("correct_answer", "main_reasoning", "incorrect_options")
            }
            if isinstance(value["incorrect_options"], dict):
                value["incorrect_options"] = [
                    {"label": k, "reason": v}
                    for k, v in value["incorrect_options"].items()
                ]
            assert not validate(
                value,
                options=record["question"]["options"],
                correct_answer=record["correct_answer"],
            )
    for year, number in ((2017, 1), (2017, 20), (2018, 26), (2019, 38)):
        result = inspect_question(
            "data/merged/blackstone/tsa_2017-2019.matched.json",
            year=year,
            question_number=number,
        )
        html = render_html(result)
        assert "Explanation by AI: True" in html and "Final Explanation" in html
        assert result["record"]["final_explanation"]["source_reference"]["path"]
        assert not any(
            i["code"] == "inspection_reference_unavailable"
            for i in result["live_inspection_issues"]
        )


def test_foreign_option_asset_label_remains_unsafe():
    data = real_data()
    record = deepcopy(
        next(
            r
            for r in data["records"]
            if r["identity"]
            == {"year": 2017, "section": "section_1", "question_number": 20}
        )
    )
    assert not visual_context(record)[1]
    record["question"]["options"][0]["images"][0]["option_label"] = "B"
    assert "conflicting_option_asset_label" in visual_context(record)[1]


def test_illustrations_do_not_make_text_sufficient_questions_image_dependent():
    data = json.loads(
        Path("data/merged/blackstone/tsa_2017-2019.matched.json").read_text(
            encoding="utf-8"
        )
    )
    for year, number in ((2018, 14), (2019, 6)):
        record = next(
            r
            for r in data["records"]
            if r["identity"]["year"] == year
            and r["identity"]["question_number"] == number
        )
        assert record["question"]["visual_assets"]
        assert not has_explanation(record)
        assert (
            record["ai_explanation"]["generation_status"]
            == "skipped_text_sufficient_illustration"
        )


def test_quantitative_visual_examples_independently():
    # Data transcribed during visual review, not inferred from the answer key.
    sales = [123, 106, 87, 114, 90, 106, 124, 113, 131, 77, 92, 75]
    differences = [b - a for a, b in pairwise(sales)]
    assert max(differences) == 27 and differences.index(27) == 2
    assert 903 - 689 == 214
    assert (6 * 0.75) / 0.6 - 6 == 1.5
    segment_counts = [6, 2, 5, 5, 4, 5, 6, 3, 7, 6]
    assert (
        max(
            segment_counts[h // 10]
            + segment_counts[h % 10]
            + segment_counts[m // 10]
            + segment_counts[m % 10]
            for h in range(24)
            for m in range(60)
        )
        == 26
    )
    tariffs = [0, 80, 120, 170, 240, 350, 420, 520, 620]
    best = [0] + [10**6] * 8
    for total in range(1, 9):
        best[total] = min(
            best[max(0, total - hours)] + tariffs[hours] for hours in range(1, 9)
        )
    assert best[8] == 460
    assert 10 * 6 + 21 * 4 == 144
    assert (2.5 + 2 + 2 * (2.5 + 2) / 2) * 2 * 3 * 4 + 20 == 236
    # Every legal first move in the pictured 3x3 card grid is beaten by a
    # disjoint adjacent average. This checks the guarantee, not just four options.
    grid = [[5, 1, 8], [3, 6, 2], [9, 7, 4]]
    edges = [
        (grid[y][x], grid[ny][nx])
        for y in range(3)
        for x in range(3)
        for ny, nx in ((y + 1, x), (y, x + 1))
        if ny < 3 and nx < 3
    ]
    for first in edges:
        assert max(
            sum(second) / 2 for second in edges if not set(second) & set(first)
        ) > abs(first[0] - first[1])
    # Exact ticket-package optimum: 16 adult fares and 8 under-16 children.
    from functools import lru_cache

    packages = (
        [(1, 0, 30), (0, 1, 20)]
        + [(2, c, 90) for c in range(3)]
        + [(8 - c, c, 175) for c in range(2, 9)]
        + [(8 - c, c, 200) for c in range(9)]
    )

    @lru_cache(None)
    def cost(adults, children):
        if adults == children == 0:
            return 0
        return min(
            price + cost(adults - a, children - c)
            for a, c, price in packages
            if a <= adults and c <= children
        )

    assert cost(16, 8) == 525
