"""Rendering/integration only. No semantic question QA or upstream stage runs."""

import base64
import json
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser

import pytest

from processors.pre_final import render
from processors.pre_final.__main__ import main
from processors.pre_final.selection import load, select_many
from processors.pre_final.storage import ROOT


@pytest.fixture
def data():
    categories = {
        "ps_procedure": {"name": "Finding Procedures", "family": "Problem-Solving"},
        "ct_main": {
            "name": "Summarising the Main Conclusion",
            "family": "Critical Thinking",
        },
    }
    rows = []
    for i in range(6):
        rows.append(
            {
                "id": "fixture-" + str(i),
                "source": "TSA" if i % 2 else "BMAT",
                "year": 2021,
                "question_number": i + 1,
                "section": "section_1",
                "category": "ct_main" if i % 2 else "ps_procedure",
                "main_body": [
                    {
                        "type": "text",
                        "text": "Paragraph one.\n\nParagraph two. "
                        + "Passage content. " * 180,
                    }
                ],
                "main_question": "Which option?\nx² + y = 2 × 3",
                "main_answers": [
                    {
                        "label": "A",
                        "text": "First option\nwith a second line",
                        "asset_ids": [],
                    },
                    {"label": "B", "text": "Long option " * 80, "asset_ids": []},
                ],
                "correct_answer": "B",
                "explanation": {
                    "blocks": [{"type": "paragraph", "text": "EXPLANATION_ONLY"}],
                    "provenance": {"source_type": "supplied"},
                },
                "explanation_by_ai": i % 2 == 0,
                "assets": [],
                "provenance": {},
            }
        )
    return {
        "stage": "pre_final",
        "schema_version": "1",
        "questions": rows,
        "categories": categories,
    }


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.nodes = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


def test_load_prefinal_only_and_reject_wrong_stage(data, tmp_path):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load(path) == data
    data["stage"] = "matched"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="pre-final"):
        load(path)


def test_selectors_and_samples_are_explicit_and_reproducible(data):
    assert render.select(data, identifier="fixture-0")["id"] == "fixture-0"
    assert render.select(data, source="TSA", year=2021, question=2)["id"] == "fixture-1"
    first = select_many(data, sample=3)
    assert first == select_many(data, sample=3)
    assert len({q["id"] for q in first}) == 3
    assert all(
        q["category"] == "ps_procedure"
        for q in select_many(data, category="Finding Procedures", sample=5)
    )
    assert len(select_many(data, source="BMAT", sample=20)) == 3
    assert select_many(data, sample=6) != select_many(data, sample=6, seed=1)
    with pytest.raises(ValueError, match="Select an exact"):
        select_many(data)
    with pytest.raises(ValueError, match="No pre-final"):
        select_many(data, identifier="absent")
    with pytest.raises(ValueError, match="canonical category"):
        select_many(data, category="BMAT-specific", sample=1)


@pytest.mark.parametrize("count", [0, -1, 1.5])
def test_invalid_samples(data, count):
    with pytest.raises(ValueError, match="positive"):
        select_many(data, sample=count)


def test_only_selected_rendering_input_asserted_no_whole_bank_validation(data):
    data["questions"][1]["category"] = None
    assert render.select(data, identifier="fixture-0")["source"] == "BMAT"
    with pytest.raises(ValueError, match="fixture-1.*category"):
        render.select(data, identifier="fixture-1")


@pytest.mark.parametrize("source,ai", [("TSA", False), ("BMAT", True)])
@pytest.mark.parametrize("width", [1166, 1350])
def test_render_simulation_report_order_and_metadata(data, source, ai, width):
    row = next(q for q in data["questions"] if q["source"] == source)
    before = deepcopy(row)
    html = render.render_html(row, data["categories"], width=width)
    simulation, report = html.split("<section class='detailed-report'", 1)
    assert "class='body-pane'" in simulation and "class='question-pane'" in simulation
    assert "type='radio'" in simulation and "EXPLANATION_ONLY" not in simulation
    assert "EXPLANATION_ONLY" in report
    ids = [a["id"] for _, a in Tags(html).nodes if "id" in a]
    assert ids[:7] == [
        "source",
        "explanation-by-ai",
        "category",
        "main-body",
        "main-question",
        "main-answers",
        "correct-answer",
    ]
    assert f">{source}</p>" in report
    assert f">{str(ai).lower()}</p>" in report
    assert data["categories"][row["category"]]["name"] in report
    assert "x² + y = 2 × 3" in html and "with a second line" in html
    assert f"--preview-width:{width}px" in html
    assert row == before


def test_css_scroll_sizing_and_no_distortion(data):
    css = render.CSS.read_text(encoding="utf-8")
    assert "height:560px" in css and "overflow-y:auto" in css
    assert "overscroll-behavior:contain" in css and "min-width:0" in css
    assert "max-width:100%;width:auto;height:auto;object-fit:contain" in css
    assert "object-fit:cover" not in css and "text-overflow:ellipsis" not in css
    assert ":checked" in css
    with pytest.raises(ValueError, match="1166 or 1350"):
        render.render_html(data["questions"][0], data["categories"], width=1200)


def test_sample_report_one_document_unique_ids_and_radios(data):
    html = render.build_report(select_many(data, sample=3), data["categories"])
    nodes = Tags(html).nodes
    ids = [a["id"] for _, a in nodes if "id" in a]
    assert len(ids) == len(set(ids))
    assert len({a["name"] for t, a in nodes if t == "input"}) == 3
    assert html.count("<!doctype html>") == 1
    assert html.count("class='question-preview'") == 3
    assert "href='#q0-explanation'" in html


def test_body_option_explanation_images_use_existing_bytes(data, tmp_path):
    row = data["questions"][0]
    # Existing fixture pixels; no crops/transforms or explanation generation.
    pixels = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j0d0AAAAASUVORK5CYII="
    )
    path = tmp_path / "existing.png"
    path.write_bytes(pixels)
    row["assets"] = [
        {
            "id": role,
            "path": "existing.png",
            "sha256": sha256(pixels).hexdigest(),
            "role": role,
            "page": 1,
            "option_label": "A" if role == "option" else None,
        }
        for role in ("body", "option", "explanation")
    ]
    row["main_body"].append({"type": "visual", "asset_id": "body"})
    row["main_answers"][0].update(text="", asset_ids=["option"])
    row["explanation"]["blocks"].append({"type": "visual", "asset_id": "explanation"})
    html = render.render_html(row, data["categories"], root=tmp_path)
    images = [a for tag, a in Tags(html).nodes if tag == "img"]
    assert len(images) == 5  # body/option appear in both views, explanation below only
    assert all(
        a["src"].endswith(base64.b64encode(pixels).decode("ascii")) for a in images
    )
    assert path.read_bytes() == pixels
    path.unlink()
    with pytest.raises(ValueError, match="fixture-0.*asset (body|option)"):
        render.render_html(row, data["categories"], root=tmp_path)


def test_unsupported_fields_fail_without_repair(data):
    q = data["questions"][0]
    q["main_body"] = [{"type": "unsupported"}]
    with pytest.raises(ValueError, match="fixture-0.*main_body"):
        render.render_html(q, data["categories"])
    q["main_body"] = []
    q["explanation_by_ai"] = None
    with pytest.raises(ValueError, match="explanation_by_ai"):
        render.render_html(q, data["categories"])


def test_cli_one_file_sample_no_upstream_loads_or_writes(data, tmp_path):
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    before = path.read_bytes()
    output = tmp_path / "sample.html"
    main(
        [
            "inspect",
            "--input",
            str(path),
            "--sample",
            "2",
            "--category",
            "ps_procedure",
            "--width",
            "1350",
            "--output",
            str(output),
        ]
    )
    assert len(list(tmp_path.glob("*.html"))) == 1
    assert output.read_text(encoding="utf-8").count("class='question-preview'") == 2
    assert path.read_bytes() == before
    with pytest.raises(FileExistsError):
        main(
            [
                "inspect",
                "--input",
                str(path),
                "--id",
                "fixture-0",
                "--output",
                str(output),
            ]
        )


def test_optional_browser_open_is_explicit(data, tmp_path, monkeypatch):
    import webbrowser

    path = tmp_path / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url))
    output = tmp_path / "preview.html"
    main(
        [
            "inspect",
            "--input",
            str(path),
            "--id",
            "fixture-0",
            "--open",
            "--output",
            str(output),
        ]
    )
    assert opened == [output.resolve().as_uri()]


def test_no_renderer_imports_assembly_or_prior_stage_modules():
    import ast

    for name in (
        "render.py",
        "selection.py",
        "preview_content.py",
        "preview_report.py",
    ):
        path = ROOT / "processors/pre_final" / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [
            n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
        ]
        assert not any(
            i == "core"
            or any(
                stage in i
                for stage in ("parsers", "matching", "normalization", "categorization")
            )
            for i in imports
        )


def test_canonical_small_rendering_sample_unchanged():
    path = ROOT / "data/pre_final/questions.json"
    before = sha256(path.read_bytes()).hexdigest()
    data = load(path)
    rows = [
        next(
            q
            for q in data["questions"]
            if q["source"] == "TSA"
            and not any(a["role"] in ("body", "option") for a in q["assets"])
        ),
        next(
            q
            for q in data["questions"]
            if q["source"] == "BMAT" and any(a["role"] == "body" for a in q["assets"])
        ),
        next(
            q
            for q in data["questions"]
            if any(a["role"] == "option" for a in q["assets"])
        ),
    ]
    assets = {
        a["path"]: sha256((ROOT / a["path"]).read_bytes()).hexdigest()
        for q in rows
        for a in q["assets"]
    }
    for width in render.WIDTHS:
        html = render.build_report(rows, data["categories"], width=width)
        assert html.count("class='question-preview'") == 3
    assert sha256(path.read_bytes()).hexdigest() == before
    assert all(
        sha256((ROOT / p).read_bytes()).hexdigest() == value
        for p, value in assets.items()
    )
