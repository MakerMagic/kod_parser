"""Stored-only mathematics cleaning and bounded answer retry regressions."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from parsers.mathematics.structure import walk
from processors.matching.mathematics.core import build, load
from processors.matching.mathematics.retry import retry_unmatched
from processors.normalization.mathematics.__main__ import main as clean_main
from processors.normalization.mathematics.cleaner import clean_dataset, clean_question


def question(number=1):
    return {
        "id": f"source_q{number}",
        "source_document_id": "source",
        "question_number": number,
        "issues": [],
        "extraction_status": "extracted",
        "assets": [],
        "content": [{"type": "text", "text": "  Find x.\r\nKeep this line.  "}],
        "options": [
            {
                "label": label,
                "content": [{"type": "math", "latex": formula, "display": False}],
            }
            for label, formula in [("A", r"\sqrt{\frac{3}{2}}"), ("B", "x^{2}")]
        ],
        "raw": {"text": "untouched original"},
        "regions": [],
    }


def stored(tmp_path, questions=None):
    qs = questions if questions is not None else [question(1), question(2)]
    raw = {
        "domain": "mathematics",
        "stage": "mathematics_raw",
        "schema_version": "2",
        "source_document": {
            "id": "source",
            "source": "matdev",
            "filename": "paper.pdf",
            "sha256": "stable-source-sha",
        },
        "pages": [{"page": 1, "role": "answer_key"}],
        "questions": qs,
        "answer_key": {
            "entries": [
                {"question_number": q["question_number"], "correct_answer": "A"}
                for q in qs
            ],
            "issues": [],
        },
        "issues": [],
    }
    path = tmp_path / "paper.raw.json"
    path.write_text(json.dumps(raw), encoding="utf8")
    return path


def test_cleaning_keeps_math_assets_lists_provenance_and_inline_spaces():
    raw = question()
    raw["assets"] = [{"id": "diagram", "path": "existing.png", "sha256": "source-hash"}]
    raw["content"] = [
        {"type": "text", "text": "Let "},
        {"type": "math", "latex": r"\sqrt{\frac{x+1}{y}}", "display": False},
        {"type": "text", "text": " be given.\r\nThen:"},
        {
            "type": "visual",
            "asset_id": "diagram",
            "display": True,
            "source": {"bbox": [1, 2, 3, 4]},
        },
        {
            "type": "list",
            "ordered": False,
            "items": [
                {"content": [{"type": "text", "text": "first"}]},
                {"content": [{"type": "math", "latex": "x^{2}", "display": False}]},
            ],
        },
    ]
    before = deepcopy(raw)
    reference = {
        "path": "stored.json",
        "sha256": "original",
        "json_pointer": "/questions/0",
    }
    clean = clean_question(raw, reference)
    assert raw == before
    expected = deepcopy(before)
    expected["content"][2]["text"] = " be given.\nThen:"
    assert {k: clean[k] for k in raw} == expected
    assert clean["raw_reference"] == reference
    assert clean["cleaning"]["status"] == "cleaned" and not clean["cleaning_issues"]


def test_cleaning_excludes_raw_findings_and_incomplete_extraction(tmp_path):
    qs = [question(n) for n in (1, 2, 3)]
    qs[1]["issues"] = [
        {"code": "uncertain_formula", "reason": "Uncertain radical scope"}
    ]
    qs[2]["extraction_status"] = "review"
    path = stored(tmp_path, qs)
    before = path.read_bytes()
    data, validation = clean_dataset([path])
    assert [q["id"] for q in data["questions"]] == [qs[0]["id"]]
    assert data["summary"]["eligible"] == data["summary"]["cleaned"] == 1
    assert len(validation["excluded"]) == 2
    assert validation["excluded"][0]["reasons"] == qs[1]["issues"]
    assert path.read_bytes() == before


def test_cleaning_records_new_problems_without_forcing_success():
    raw = question()
    raw["options"][0]["content"][0]["latex"] = r"\sqrt{"
    cleaned = clean_question(raw, {})
    assert cleaned["cleaning"]["status"] == "review"
    assert cleaned["cleaning_issues"][0]["code"] == "malformed_latex"
    assert cleaned["options"] == raw["options"]
    raw["issues"] = [{"code": "raw_issue"}]
    with pytest.raises(ValueError, match="completed RAW"):
        clean_question(raw, {})


def test_cleaning_cli_is_reproducible_and_cannot_overwrite_raw(tmp_path):
    path = stored(tmp_path)
    target = tmp_path / "clean"
    args = ["--raw-json", str(path), "--output-dir", str(target)]
    assert clean_main(args) == 0
    first = (target / "questions.json").read_bytes()
    artifacts = {
        name: (target / name).read_bytes()
        for name in ("CLEANING_BACKTESTING.md", "CLEANING_ISSUES.md")
    }
    assert b"Total issues: 0" in artifacts["CLEANING_ISSUES.md"]
    assert clean_main(args) == 0
    assert (target / "questions.json").read_bytes() == first
    assert all(
        (target / name).read_bytes() == content for name, content in artifacts.items()
    )
    input_named_like_output = tmp_path / "questions.json"
    input_named_like_output.write_bytes(path.read_bytes())
    with pytest.raises(ValueError, match="cannot overwrite RAW"):
        clean_main(
            ["--raw-json", str(input_named_like_output), "--output-dir", str(tmp_path)]
        )


def test_retry_matches_only_unmatched_and_preserves_valid_answer(tmp_path, monkeypatch):
    path = stored(tmp_path)
    data = build([path])
    # A pre-existing valid answer is never reconsidered, even against a key.
    data["questions"][0]["correct_answer"] = "B"
    data["questions"][1]["correct_answer"] = None
    data["questions"][1]["matching"]["status"] = "unmatched"
    original = deepcopy(data)
    from processors.matching.mathematics import retry

    actual = retry.match_document
    seen = []

    def bounded(raw, reference):
        seen.extend(q["id"] for q in raw["questions"])
        return actual(raw, reference)

    monkeypatch.setattr(retry, "match_document", bounded)
    result, report = retry_unmatched(data)
    assert seen == ["source_q2"]
    assert data == original and result["questions"][0] == original["questions"][0]
    assert result["questions"][1]["correct_answer"] == "A"
    assert report["newly_matched"] == report["previously_unmatched"] == 1
    assert report["still_unmatched"] == 0


def test_retry_retains_unresolved_reason_when_options_missing(tmp_path):
    q = question()
    q["options"] = []
    q["issues"] = [{"code": "option_boundary", "reason": "No reliable option anchors"}]
    data = build([stored(tmp_path, [q])])
    result, report = retry_unmatched(data)
    assert result == data
    assert report["unresolved"][0]["key_answers"] == ["A"]
    assert (
        "complete extracted options" in report["unresolved"][0]["issues"][0]["reason"]
    )
    assert report["still_unmatched"] == 1 and report["newly_matched"] == 0


def test_retry_rejects_changed_source_without_modifying_existing_matches(tmp_path):
    path = stored(tmp_path)
    data = build([path])
    data["questions"][1]["matching"]["status"] = "unmatched"
    data["questions"][1]["correct_answer"] = None
    before = deepcopy(data)
    path.write_text(path.read_text(encoding="utf8") + "\n", encoding="utf8")
    with pytest.raises(ValueError, match="RAW reference changed"):
        retry_unmatched(data)
    assert data == before


def test_current_clean_output_covers_exact_eligible_raw_set_without_pdf_access(
    monkeypatch,
):
    import pdfplumber

    monkeypatch.setattr(
        pdfplumber, "open", lambda *a, **k: pytest.fail("Stored stage opened a PDF")
    )
    paths = sorted(Path("data/raw/mathematics").glob("*.raw.json"))
    if not paths:
        pytest.skip("Local mathematics data unavailable")
    before = {p: sha256(p.read_bytes()).hexdigest() for p in paths}
    saved = load("data/clean/mathematics/questions.json")
    result, validation = clean_dataset(paths, existing=saved)
    assert result == saved
    eligible = {
        q["id"]
        for p in paths
        for q in load(p)["questions"]
        if not q["issues"] and q["extraction_status"] == "extracted"
    }
    assert {q["id"] for q in result["questions"]} == eligible
    assert len(eligible) == len(result["questions"])
    originals = {q["id"]: q for p in paths for q in load(p)["questions"]}
    for q in result["questions"]:
        original = originals[q["id"]]
        for key in (
            "id",
            "source_document_id",
            "question_number",
            "assets",
            "regions",
            "raw",
        ):
            assert q[key] == original[key]
        assert [o["label"] for o in q["options"]] == [
            o["label"] for o in original["options"]
        ]
        before_blocks = list(walk(original["content"])) + [
            b for o in original["options"] for b in walk(o["content"])
        ]
        after_blocks = list(walk(q["content"])) + [
            b for o in q["options"] for b in walk(o["content"])
        ]
        for before_block, after_block in zip(before_blocks, after_blocks, strict=True):
            assert before_block["type"] == after_block["type"]
            if before_block["type"] not in {"text", "list"}:
                assert {
                    k: v for k, v in before_block.items() if k != "break_before"
                } == {k: v for k, v in after_block.items() if k != "break_before"}
        assert q["main_question"] is None or q["main_question"]
        from processors.normalization.mathematics.structure import (
            projection_is_lossless,
        )

        assert projection_is_lossless(q["content"], q["main_body"], q["main_question"])
    assert result["summary"]["cleaned"] + result["summary"]["review"] == len(eligible)
    assert {q["id"] for q in result["questions"] if q["cleaning_issues"]} == {
        q["id"] for q in validation["issues"]
    }
    assert all(sha256(p.read_bytes()).hexdigest() == h for p, h in before.items())


@pytest.mark.parametrize(
    "latex,display",
    [
        (r"\frac{x+1}{y-2}", False),
        (r"\sqrt[3]{\sqrt{x^{2}+1}}", True),
        (r"a_{n+1}^{2}\geq\pi", False),
        (r"\begin{cases}x+y=3\\x-y=1\end{cases}", True),
        (r"\sin(x)+f(2,3)=25\%", False),
    ],
)
def test_cleaning_never_rewrites_math_or_joins_formula_blocks(latex, display):
    raw = question()
    formula = {"type": "math", "latex": latex, "display": display}
    raw["content"] = [
        {"type": "text", "text": " Let  "},
        deepcopy(formula),
        {"type": "text", "text": "  be given.\n\n\nThen:\n"},
        {**deepcopy(formula), "break_before": True},
    ]
    raw["options"][0]["content"] = [deepcopy(formula)]
    cleaned = clean_question(raw, {})
    assert not cleaned["cleaning_issues"]
    assert cleaned["content"][0]["text"] == " Let "
    assert cleaned["content"][2]["text"] == " be given.\n\nThen:\n"
    assert cleaned["content"][1] == raw["content"][1]
    assert cleaned["content"][3] == raw["content"][3]
    assert cleaned["options"] == raw["options"]
    again = clean_question({k: cleaned[k] for k in raw}, {})
    assert again["content"] == cleaned["content"]


def test_shared_prose_normalization_preserves_numeric_columns_and_lists():
    raw = question()
    raw["content"] = [
        {"type": "text", "text": "  First\u00a0\u00a0line.\r\n\r\n\r\nNext\tline.  "}
    ]
    assert clean_question(raw, {})["content"][0]["text"] == "First line.\n\nNext line."
    raw["content"][0]["text"] = "1  2  3\n4  5  6"
    assert clean_question(raw, {})["content"] == raw["content"]
    raw["content"] = [
        {
            "type": "list",
            "ordered": True,
            "items": [
                {"content": [{"type": "text", "text": "  one  item  "}]},
                {"content": [{"type": "math", "latex": "x_{1}", "display": False}]},
            ],
        }
    ]
    result = clean_question(raw, {})
    assert result["content"][0]["items"][0]["content"][0]["text"] == "one item"
    assert result["content"][0]["items"][1] == raw["content"][0]["items"][1]


def test_unknown_text_encoding_creates_located_issue_without_guessing():
    raw = question()
    raw["content"][0]["text"] = "Let (cid:99) be given."
    result = clean_question(raw, {})
    assert result["content"] == raw["content"]
    assert result["cleaning_issues"] == [
        {
            "code": "encoding_artifact_unresolved",
            "reason": "Encoding tokens/control glyphs have no verified replacement; content retained.",
            "field": "content[0]",
        }
    ]


def test_incremental_cleaning_reuses_valid_rows_and_processes_only_new(
    tmp_path, monkeypatch
):
    from processors.normalization.mathematics import cleaner

    first = question(1)
    path = stored(tmp_path, [first])
    previous, _ = clean_dataset([path])
    original_cleaned = deepcopy(previous["questions"][0])
    path = stored(tmp_path, [first, question(2)])
    actual = cleaner.clean_question
    seen = []

    def track(raw, reference, **kwargs):
        seen.append(raw["id"])
        return actual(raw, reference, **kwargs)

    monkeypatch.setattr(cleaner, "clean_question", track)
    stats = {}
    result, _ = clean_dataset([path], previous, run_stats=stats)
    assert seen == ["source_q2"]
    assert stats == {
        "reused_valid": 1,
        "processed_new": 1,
        "retried_review_or_stale": 0,
    }
    reused = deepcopy(result["questions"][0])
    assert reused.pop("raw_reference") != original_cleaned.pop("raw_reference")
    assert reused == original_cleaned
    seen.clear()
    rerun, _ = clean_dataset([path], result)
    assert rerun == result and seen == []
    changed = deepcopy(first)
    changed["options"][0]["content"][0]["latex"] = "x+3"
    stored(tmp_path, [changed, question(2)])
    refreshed, _ = clean_dataset([path], result)
    assert seen == ["source_q1"]
    assert refreshed["questions"][0]["options"] == changed["options"]
