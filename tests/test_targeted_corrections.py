"""Canonical-first workflow, supplied text, bounded categorization and crop QA."""

import importlib
import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_bmat_worked_solutions import candidate as candidate_fixture
from test_bmat_worked_solutions import supplied

from categorization.bmat.attribution import dependent_unit_rate_comparison
from categorization.bmat.core import attribution
from categorization.bmat.taxonomy import validate
from parsers.bmat.quality import findings
from parsers.bmat_supplied_explanations import parse
from processors.matching.bmat.supplied import apply

candidate = candidate_fixture


def test_permanent_policy_directs_development_to_canonical_data():
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "Read question data from canonical structured storage." in text
    assert (
        "explicit user request" in text
        and "canonical data/source assets cannot resolve it" in text
    )
    assert not Path("parsers/explanation_text.py").exists()
    assert not Path("parsers/explanation_text.ps1").exists()


@pytest.mark.parametrize(
    "module", ["categorization.bmat.__main__", "processors.matching.bmat.__main__"]
)
@pytest.mark.parametrize("command,expected", [("run", False), ("report", True)])
def test_stage_cli_does_not_implicitly_render_questions(
    monkeypatch, tmp_path, module, command, expected
):
    cli = importlib.import_module(module)
    captured = []
    monkeypatch.setattr(cli, "report", lambda *a, **kw: captured.append(kw) or {})
    if module.startswith("categorization"):
        monkeypatch.setattr(cli, "build", lambda *a: {})
        monkeypatch.setattr(cli, "write", lambda *a: None)
    else:
        monkeypatch.setattr(cli, "run", lambda *a, **kw: {"summary": {}})
    cli.main(
        [
            command,
            "--output",
            str(tmp_path / "output.json"),
            "--year",
            "2021",
            "--question",
            "25",
        ]
    )
    assert captured == [{"render": expected, "year": 2021, "question": 25}]


def test_backtesting_guides_are_instructions_not_question_catalogs():
    paths = list(Path("docs").rglob("*BACKTEST*.md")) + list(
        Path("docs/critical_thinking_problem_solving/tsa/2017-2019_questions_images_with_explanation_ai_generated").glob(
            "*/BACKTEST.md"
        )
    )
    assert len(paths) >= 12
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\]\([^)]*inspections[^)]*(?:q\d|_q\d)", text), path
        assert not re.search(r"^\|\s*20\d{2}\s*\|", text, re.MULTILINE), path
    assert "hundreds" not in Path("docs/critical_thinking_problem_solving/bmat/BMAT_CATEGORIZATION_BACKTEST.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize(
    "module", ["categorization.bmat.backtest", "processors.matching.bmat.backtest"]
)
def test_issue_refresh_never_calls_a_question_renderer(monkeypatch, tmp_path, module):
    tool = importlib.import_module(module)

    def forbidden(*args, **kwargs):
        raise AssertionError("Issue refresh must not render a question")

    if module.startswith("categorization"):
        monkeypatch.setattr(tool, "render_record", forbidden)
        monkeypatch.setattr(tool, "write_html", forbidden)
        path = "data/categorized/bmat/questions.categorized.json"
    else:
        monkeypatch.setattr(tool, "inspect", forbidden)
        path = "data/merged/bmat/questions.matched.json"
    tool.report(
        path,
        tmp_path / "issues.md",
        tmp_path / "guide.md",
        tmp_path / "html",
        render=False,
    )
    assert not (tmp_path / "html").exists()
    assert not re.search(
        r"^\|\s*20\d{2}\s*\|",
        (tmp_path / "guide.md").read_text(encoding="utf-8"),
        re.MULTILINE,
    )


def test_supplied_text_strips_links_and_boilerplate_not_reasoning(tmp_path):
    p = tmp_path / "user.txt"
    p.write_text(
        "2021:\nQuestion 25 — A\nCorrect answer: A\nFirst paragraph.\n\nA is correct because this is substantive reasoning.\nOriginal solution\nSource: https://example.test/ignored\n",
        encoding="utf-8",
    )
    answer = parse(p)["answers"][0]
    assert answer["correct_answer"] == "A"
    assert (
        answer["explanation"]["main_explanation"]
        == "First paragraph.\n\nA is correct because this is substantive reasoning."
    )
    assert len(answer["explanation"]["paragraphs"]) == 2
    assert answer["source_document"]["source_url"] is None
    assert not answer["explanation"]["visual_assets"]


def image_record(result):
    row = result["records"][0]
    row["answer"]["explanation"].update(
        blocks=[{"type": "visual", "asset_index": 1, "order": 1}],
        paragraphs=[],
        main_explanation="",
    )
    row["final_explanation"]["blocks"] = [
        {"type": "visual", "asset_index": 1, "order": 1}
    ]
    return row


def test_explicit_supplied_text_preference_does_not_need_ocr(candidate, tmp_path):
    _, _, build, _ = candidate
    data = build()
    image_record(data)
    source = supplied(tmp_path, "Supplied reasoning.\n\nA separate calculation step.")
    ordinary = deepcopy(data)
    apply(ordinary, source)
    assert ordinary["records"][0]["final_explanation"]["blocks"][0]["type"] == "visual"
    apply(data, source, prefer_text=True)
    row = data["records"][0]
    assert row["status"] == "matched"
    assert [b["text"] for b in row["final_explanation"]["blocks"]] == [
        "Supplied reasoning.",
        "A separate calculation step.",
    ]
    assert all(b["type"] != "visual" for b in row["final_explanation"]["blocks"])
    assert row["answer_candidates"][0]["superseded_by"] == "explicit_user_supplied_text"


def test_supplied_caution_remains_reviewed_on_rerun(candidate, tmp_path):
    _, _, build, _ = candidate
    data = build()
    image_record(data)
    source = supplied(
        tmp_path, "Faithfully supplied text.\nReview required: needs confirmation."
    )
    apply(data, source, prefer_text=True)
    assert data["records"][0]["status"] == "explanation_review_required"
    rerun = build()
    apply(rerun, source, previous=data, prefer_text=True)
    assert rerun["records"][0]["status"] == "explanation_review_required"
    assert (
        rerun["records"][0]["final_explanation"]["blocks"][0]["text"]
        == "Faithfully supplied text."
    )


def test_latest_64_explanations_are_text_only_and_properly_deferred():
    source = json.loads(
        Path("data/raw/bmat_supplied_explanations/solutions.answers.json").read_text(
            encoding="utf-8"
        )
    )
    answers = {
        (a["year"], a["question_number"]): a
        for a in source["answers"]
        if a["year"] in (2020, 2021)
    }
    assert len(answers) == 64
    data = json.loads(
        Path("data/merged/bmat/questions.matched.json").read_text(encoding="utf-8")
    )
    for row in data["records"]:
        key = row["identity"]["year"], row["identity"]["question_number"]
        if key not in answers:
            continue
        a = answers[key]
        assert a["correct_answer"] not in ("", None)
        assert not a["explanation"]["visual_assets"]
        assert not re.search(
            r"https?://|Original solution|(?m:^Correct answer:)",
            a["explanation"]["main_explanation"],
        )
        if row["status"] in {"matched", "explanation_review_required"}:
            assert row["correct_answer"] == a["correct_answer"]
            assert row["answer"]["explanation"] == a["explanation"]
            assert all(
                b["type"] != "visual" for b in row["final_explanation"]["blocks"]
            )
        else:
            assert row["status"] in {"intentionally_skipped", "deferred_upstream_issue"}
            assert row["supplied_imports"]


def test_q25_and_new_relative_unit_rate_analogue_are_procedural():
    data = json.loads(
        Path("data/categorized/bmat/questions.categorized.json").read_text(
            encoding="utf-8"
        )
    )
    row = next(
        r
        for r in data["records"]
        if r["identity"]["year"] == 2021 and r["identity"]["question_number"] == 25
    )
    assert row["categorization"]["patterns"] == ["ps_procedure"]
    q = deepcopy(row["question"])
    q["question_text"] = (
        "One detergent container costs £4 and lasts for 20 days. A second lasts for 30 days but costs 60p more."
    )
    q["main_question"] = "How much less do I spend per day with the second container?"
    assert dependent_unit_rate_comparison(q)
    assert attribution(q)["patterns"] == ["ps_procedure"]
    q["question_text"] = (
        "The table lists ten tariffs; only the weekend tariff applies to this customer."
    )
    assert not dependent_unit_rate_comparison(q)


@pytest.fixture(scope="module")
def q26():
    path = next(Path("data/raw/bmat").glob("bmat_2021_*.raw.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    return path, data, data["questions"][25]


def test_q26_correct_crops_pass_live_checker_unchanged(q26):
    path, data, q = q26
    assert q["parsing_issues"] == [] and findings(data, q, path) == []
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    for option in q["options"]:
        assert len(option["images"]) == 1
        asset = option["images"][0]
        assert asset["option_label"] == option["label"]
        assert (
            sha256((path.parent / asset["path"]).read_bytes()).hexdigest()
            == asset["sha256"]
        )


@pytest.mark.parametrize("defect", ["missing", "foreign_label", "mapping"])
def test_genuine_crop_defects_are_not_suppressed(q26, defect):
    path, data, original = q26
    q = deepcopy(original)
    if defect == "missing":
        q["options"][0]["images"] = []
        expected = "option_content_unresolved:A"
    elif defect == "foreign_label":
        q["visual_assets"][0]["bbox"][2] = 400
        expected = "foreign_option_letter_in_crop:A"
    else:
        q["visual_assets"][0]["option_label"] = "B"
        expected = "visual_image_option_mapping_inconsistent:A"
    assert any(expected in issue for issue in findings(data, q, path))


def test_no_issue_free_multi_tsa_primary_assignments_and_bmat_types_preserved():
    data = json.loads(
        Path("data/categorized/bmat/questions.categorized.json").read_text(
            encoding="utf-8"
        )
    )
    for row in data["records"]:
        validate(row["categorization"])
    assert (
        sum(r["categorization"]["category"] == "BMAT-specific" for r in data["records"])
        == 343
    )
