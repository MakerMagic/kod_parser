"""Offline Markdown export, provenance, unresolved records and link integrity."""

import ast
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from processors.matching.export_without_explanations import (
    export,
    has_explanation,
    render_year,
    select_records,
)


def record(number=1):
    return {
        "identity": {"year": 2017, "section": "section_1", "question_number": number},
        "status": "matched",
        "correct_answer": "B",
        "issues": [],
        "question": {
            "question_id": f"question-{number}",
            "main_body": [
                {
                    "type": "text",
                    "text": "First paragraph.\n\nSecond paragraph.\n1. One\n2. Two",
                }
            ],
            "main_question": "Which statement follows?",
            "question_text": "Original full text",
            "options": [
                {"label": "A", "text": "First line\nSecond line", "images": []},
                {"label": "B", "text": "Correct option", "images": []},
            ],
            "raw_reference": {"path": "raw.json"},
        },
        "answer": {
            "correct_answer": "B",
            "explanation": {"availability": "not_supplied_by_source_format"},
        },
        "final_explanation": {"status": "unavailable", "blocks": []},
    }


def test_existing_source_manual_ai_and_uncertain_content_are_not_exported():
    for field in (
        "main_explanation",
        "blocks",
        "paragraphs",
        "bulleted_blocks",
        "visual_assets",
    ):
        value = record()
        value["answer"]["explanation"][field] = "Preserved source content"
        assert has_explanation(value)
    for field in ("blocks", "unplaced_components"):
        value = record()
        value["final_explanation"].update(status="uncertain", explanation_by_ai=True)
        value["final_explanation"][field] = [{"text": "Existing explanation"}]
        assert has_explanation(value)
    assert not has_explanation(record())


def test_known_source_answer_in_conflict_is_kept_without_repairing_options():
    value = record()
    value.update(status="conflict", correct_answer=None)
    value["question"]["options"] = [{"label": "A", "text": "Unresolved choice"}]
    before = deepcopy(value)
    rows, omitted = select_records({"records": [value]}, {}, (2017,))
    assert rows[2017][0][1] == "B" and not omitted[2017]
    markdown = render_year(
        2017,
        rows[2017],
        [],
        {"records": [value]},
        Path("matched.json"),
        Path("export.md"),
    )
    assert "**Correct answer:** B" in markdown
    assert "Known source answer key shown without resolving" in markdown
    assert "#### B" not in markdown
    assert value == before


def test_content_spacing_and_missing_keys_are_explicit():
    good, missing = record(), record(2)
    missing["correct_answer"] = None
    missing["answer"]["correct_answer"] = None
    rows, omitted = select_records({"records": [good, missing]}, {}, (2017,))
    assert omitted[2017] == [(2, "missing_or_ambiguous_answer_key")]
    markdown = render_year(
        2017,
        rows[2017],
        omitted[2017],
        {"records": [good, missing]},
        Path("matched.json"),
        Path("export.md"),
    )
    assert "First paragraph.\n\nSecond paragraph.  \n1. One  \n2. Two" in markdown
    assert "First line  \nSecond line" in markdown
    assert "### Explanation" not in markdown
    assert "Total questions listed: 1" in markdown
    assert "Q2: missing_or_ambiguous_answer_key" in markdown


def test_duplicate_or_conflicting_answer_sources_are_never_forced():
    value = record()
    key = (2017, "section_1", 1)
    for sources in ([{"correct_answer": "C"}], [{"correct_answer": "B"}] * 2):
        rows, omitted = select_records({"records": [value]}, {key: sources}, (2017,))
        assert not rows[2017]
        assert omitted[2017] == [(1, "missing_or_ambiguous_answer_key")]


def test_missing_question_is_reported_when_key_exists():
    answer = {"correct_answer": "A", "source_document": {"filename": "Answers.pdf"}}
    rows, omitted = select_records(
        {"records": []}, {(2017, "section_1", 2): [answer]}, (2017,)
    )
    markdown = render_year(
        2017,
        rows[2017],
        omitted[2017],
        {"records": []},
        Path("matched.json"),
        Path("export.md"),
    )
    assert "[Unavailable in the cleaned record.]" in markdown
    assert "missing_question" in markdown
    assert "**Correct answer:** A" in markdown


def test_raw_and_derived_visual_references_remain_traceable(tmp_path):
    value = record()
    raw = tmp_path / "raw" / "raw.json"
    clean = tmp_path / "clean" / "clean.json"
    for path in (raw, clean):
        path.parent.mkdir()
        path.write_text("{}", encoding="utf-8")
    (raw.parent / "graphic.png").write_bytes(b"raw")
    (clean.parent / "graphic-clean.png").write_bytes(b"clean")
    value["question"]["raw_reference"]["path"] = str(raw)
    value["question_reference"] = {"path": str(clean)}
    value["question"]["options"][0]["images"] = [
        {
            "image_id": "image",
            "path": "graphic.png",
            "clean_asset": {
                "path": "graphic-clean.png",
                "path_base": "clean_json_parent",
            },
        }
    ]
    rows, omitted = select_records({"records": [value]}, {}, (2017,))
    markdown = render_year(
        2017,
        rows[2017],
        omitted[2017],
        {"records": [value]},
        tmp_path / "matched.json",
        tmp_path / "export.md",
    )
    assert "graphic-clean.png" in markdown and "Raw asset:" in markdown
    assert "raw/graphic.png" in markdown


def test_real_export_completeness_and_determinism(tmp_path):
    source = Path("data/merged/blackstone/tsa_2017-2019.matched.json")
    if not source.exists():
        pytest.skip("Local matched dataset unavailable")
    original = source.read_bytes()
    counts = export(source, tmp_path)
    assert {year: values["exported"] for year, values in counts.items()} == {
        2017: 50,
        2018: 50,
        2019: 50,
    }
    snapshots = {path: path.read_bytes() for path in tmp_path.glob("*.md")}
    export(source, tmp_path)
    assert all(path.read_bytes() == content for path, content in snapshots.items())
    assert source.read_bytes() == original
    for year in counts:
        content = (tmp_path / f"{year}_questions_without_explanations.md").read_text(
            encoding="utf-8"
        )
        assert list(
            map(int, re.findall(r"^## Question (\d+)$", content, re.MULTILINE))
        ) == list(range(1, 51))
        for target in re.findall(r"\]\(<([^>]+)>\)", content):
            assert (tmp_path / target).resolve().exists(), target
    assert (
        "**Correct answer:** B"
        in (tmp_path / "2018_questions_without_explanations.md")
        .read_text(encoding="utf-8")
        .split("## Question 20\n")[1]
        .split("## Question 21\n")[0]
    )


def test_exporter_never_imports_generation_or_providers():
    tree = ast.parse(
        Path("processors/matching/export_without_explanations.py").read_text(
            encoding="utf-8"
        )
    )
    imports = [
        ast.unparse(node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert not any(
        "gemini" in value
        or "processors.explanations" in value
        or "ai_explanations" in value
        for value in imports
    )


def test_organized_ai_markdown_and_its_links_are_local_and_valid():
    folder = Path("docs/ai_explanations")
    for path in folder.glob("*.md"):
        if path.name != "README.md":
            assert not (folder.parent / path.name).exists()
        content = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\]\((?:<([^>]+)>|([^\s)]+))\)", content):
            target = match[1] or match[2]
            if target.startswith(("http:", "https:", "#")):
                continue
            target = target.split("#", 1)[0]
            assert (path.parent / target).resolve().exists(), (path, target)


def test_stale_input_hash_is_not_silently_exported(tmp_path):
    source = tmp_path / "matched.json"
    raw = tmp_path / "raw.json"
    raw.write_text("{}", encoding="utf-8")
    source.write_text(
        json.dumps(
            {
                "stage": "matched",
                "schema_version": "1",
                "records": [],
                "issues": [],
                "inputs": [
                    {"kind": "answer_intermediate", "path": str(raw), "sha256": "stale"}
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="stale or changed"):
        export(source, tmp_path / "exports")


def test_report_writers_accept_relocated_paths_without_generation(tmp_path):
    from processors.explanations.generator import write_report

    report = tmp_path / "docs" / "ai_explanations" / "EXPLANATION_PILOT_ISSUES.md"
    write_report(
        {
            "explanation_pilot": {
                "run_number": 1,
                "audit": [
                    {
                        "identity": {
                            "year": 2017,
                            "section": "section_1",
                            "question_number": 1,
                        },
                        "status": "provider_failure_exhausted",
                        "metadata": {"failure_code": "rate_limited"},
                    }
                ],
            }
        },
        report,
    )
    assert report.is_file() and "Provider Failure Exhausted" in report.read_text(
        encoding="utf-8"
    )
