"""Offline mathematics stages, source fidelity, key identity and native MathML."""

import json
import shutil
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest

from parsers.mathematics.formulas import recover
from parsers.mathematics.latex import InvalidLatex, mathml, validate
from parsers.mathematics.source import option_anchors, option_top, parse_pdf, read_key
from processors.matching.mathematics.backtest import render_report, select
from processors.matching.mathematics.core import build, match_document
from processors.matching.mathematics.core import validate as validate_data

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "acquisition/local/mathematics/matdev"


def glyph(text, x, y, size=10):
    return {
        "text": text,
        "x0": x,
        "x1": x + size * 0.5,
        "top": y,
        "bottom": y + size,
        "size": size,
        "fontname": "Cambria Math",
    }


@pytest.mark.parametrize(
    "latex",
    [
        r"x^{2}+3x",
        r"x_{1}",
        r"\frac{a+b}{c}",
        r"\sqrt{9+4\sqrt{2}}",
        r"\sqrt[4]{2}",
        r"x\neq \pm \frac{1}{5}",
        r"\theta\leq 90^{\circ}",
    ],
)
def test_latex_subset_roundtrip_render(latex):
    assert validate(latex) == []
    assert fromstring(mathml(latex)).tag.endswith("math")


@pytest.mark.parametrize(
    "latex", ["", r"\frac{x}{", r"\unsupported{x}", r"x^^2", r"\(x\)", "(cid:3)", "�"]
)
def test_malformed_or_unsupported_latex_is_not_accepted(latex):
    assert validate(latex)
    with pytest.raises(InvalidLatex):
        mathml(latex)


def test_native_fraction_requires_bar_and_both_operands():
    chars = [glyph("1", 0, 0, 8), glyph("5", 0, 12, 8)]
    rule = {"x0": 0, "x1": 4, "top": 9, "bottom": 9.7}
    assert recover(chars, [rule])[0] == r"\frac{1}{5}"
    assert recover(chars, [])[0] is None


@pytest.mark.parametrize("script,top,expected", [("2", -3, "x^{2}"), ("1", 7, "x_{1}")])
def test_native_scripts_are_geometry_driven(script, top, expected):
    assert recover([glyph("x", 0, 0), glyph(script, 5, top, 7)], [])[0] == expected


def test_no_guess_for_unknown_glyph_or_matrix_baselines():
    assert recover([glyph("�", 0, 0)], [])[0] is None
    assert recover([glyph("x", 0, 0), glyph("y", 0, 24)], [])[0] is None


@pytest.mark.parametrize("labels", ["ABCD", "ABCDE", "ABCDEF", "ABCDEFGH"])
def test_option_anchors_use_observed_labels_with_baseline_variation(labels):
    words = [
        {
            "text": "(" + label + ")",
            "fontname": "Tahoma",
            "page": 2,
            "x0": 50 + 80 * i,
            "x1": 65 + 80 * i,
            "top": 100 + (i % 3) * 2,
            "bottom": 111 + (i % 3) * 2,
        }
        for i, label in enumerate(labels)
    ]
    assert "".join(a["label"] for a in option_anchors(words)) == labels


def test_multirow_options_do_not_accept_roman_numeral_prose():
    words = [
        {
            "text": f"({c})",
            "fontname": "Tahoma",
            "page": 2,
            "x0": 50 + 100 * (i % 2),
            "x1": 65 + 100 * (i % 2),
            "top": 100 + 70 * (i // 2),
            "bottom": 111 + 70 * (i // 2),
        }
        for i, c in enumerate("ABCDEF")
    ]
    words.insert(
        1,
        {
            "text": "I",
            "fontname": "Tahoma",
            "page": 2,
            "x0": 70,
            "x1": 73,
            "top": 115,
            "bottom": 126,
        },
    )
    assert "".join(a["label"] for a in option_anchors(words)) == "ABCDEF"


def test_images_above_labels_are_not_shifted_to_the_next_row():
    a = {"x0": 85, "x1": 92, "top": 258, "bottom": 269}
    b = {"x0": 324, "x1": 332, "top": 252, "bottom": 263}
    assert option_top(a, [[258, 269]], [[93, 143, 282, 267]], [a, b]) == 142
    # A tall body diagram crossing an option row is not an inline option.
    assert option_top(a, [[258, 269]], [[421, 58, 539, 348]], [a, b]) == 256


def test_answer_key_rows_preserve_duplicates_and_ambiguity():
    class Page:
        def extract_text_lines(self):
            return [
                {"text": s, "x0": 10, "x1": 50, "top": i * 20, "bottom": i * 20 + 10}
                for i, s in enumerate(["1 B", "1 C", "2 ?"])
            ]

    data = read_key(Page(), "Answer key", 9)
    assert len(data["entries"]) == 2
    assert {i["code"] for i in data["issues"]} == {
        "answer_key_duplicate",
        "answer_key_structure",
    }


def test_matching_is_exact_by_source_and_number_and_reports_bad_keys():
    raw = {
        "domain": "mathematics",
        "stage": "mathematics_raw",
        "questions": [
            {
                "id": "s_q1",
                "question_number": 1,
                "options": [{"label": "A"}, {"label": "B"}],
                "issues": [],
            }
        ],
        "answer_key": {"entries": [{"question_number": 2, "correct_answer": "B"}]},
    }
    rows, orphan = match_document(raw, {"path": "stored.json", "sha256": "abc"})
    assert rows[0]["correct_answer"] is None and len(orphan) == 1
    raw["answer_key"]["entries"] = [{"question_number": 1, "correct_answer": "B"}] * 2
    assert match_document(raw, {})[0][0]["matching"]["status"] == "ambiguous"
    raw["domain"] = "BMAT"
    with pytest.raises(ValueError):
        match_document(raw, {})


def test_matching_output_identifies_mixed_source_sets(tmp_path):
    paths = []
    for source, number in (("matdev", 1), ("sky_trial", 2)):
        raw = {
            "domain": "mathematics",
            "stage": "mathematics_raw",
            "source_document": {
                "id": f"{source}_v1",
                "source": source,
                "filename": f"{source}.pdf",
            },
            "pages": [{"page": 1, "role": "cover"}],
            "questions": [
                {
                    "id": f"{source}_q{number:03}",
                    "source_document_id": f"{source}_v1",
                    "question_number": number,
                    "options": [
                        {"label": "A", "content": [{"type": "text", "text": "a"}]},
                        {"label": "B", "content": [{"type": "text", "text": "b"}]},
                    ],
                    "issues": [],
                }
            ],
            "answer_key": {"entries": [], "issues": []},
            "issues": [],
        }
        path = tmp_path / f"{source}.raw.json"
        path.write_text(json.dumps(raw), encoding="utf8")
        paths.append(path)

    result = build(paths)

    assert result["source"] == "multiple"
    assert result["summary"]["questions"] == 2
    assert {source["source"] for source in result["sources"].values()} == {
        "matdev",
        "sky_trial",
    }


@pytest.fixture(scope="module")
def pilot(tmp_path_factory):
    if not (INPUTS / "math_1.pdf").exists():
        pytest.skip("Local mathematics acceptance PDFs not available")
    root = tmp_path_factory.mktemp("mathematics")
    paths = []
    raws = {}
    for n in (1, 5, 6, 11, 12):
        p = INPUTS / f"math_{n}.pdf"
        raw = parse_pdf(p, asset_dir=root / "assets")
        target = root / f"math_{n}.raw.json"
        target.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf8")
        paths.append(target)
        raws[n] = raw
    return root, paths, raws


def test_pilot_source_roles_and_numbering_raw_preservation(pilot):
    _, _, raws = pilot
    for raw in raws.values():
        assert [q["question_number"] for q in raw["questions"]] == list(range(1, 31))
        assert raw["pages"][0]["role"] == "cover"
        assert raw["pages"][-1]["role"] == "answer_key"
        assert "www.mathdevelopment.kz" in raw["pages"][1]["raw_text"]
        assert len(raw["answer_key"]["entries"]) == 30
        assert not raw["issues"]
        for q in raw["questions"]:
            assert all(r["page"] not in (1, len(raw["pages"])) for r in q["regions"])
            assert "NUFYPET" not in q["raw"]["native_text"]
            labels = [o["label"] for o in q["options"]]
            assert 4 <= len(labels) <= 8
            assert labels == list("ABCDEFGH"[: len(labels)])
            assert q["raw"]["glyph_ids"]
            assert any(a["role"] == "source_preview" for a in q["assets"])


def test_actual_fraction_powers_radical_and_image_options(pilot):
    _, _, raws = pilot
    qq = raws[1]["questions"]
    assert any(b.get("latex") == "a=6-b^{3}" for b in qq[1]["content"])
    assert any(b.get("latex") == r"c\neq \pm \frac{1}{5}" for b in qq[3]["content"])
    assert any(
        b.get("latex") == r"\frac{5с^{2}-24с-5}{1-25с^{2}}=" for b in qq[3]["content"]
    )
    assert any(b.get("latex") == r"\sqrt{9+4\sqrt{2}}" for b in qq[5]["content"])
    assert any(
        b.get("latex") == r"3+2\sqrt[4]{2}" for b in qq[5]["options"][1]["content"]
    )
    assert all(
        any(b["type"] == "visual" for b in o["content"]) for o in qq[6]["options"]
    )
    assert not qq[4]["issues"]
    assert any(
        b.get("latex") == r"\begin{cases}2x+3y=5\\x+ay=2\end{cases}"
        for b in qq[4]["content"]
    )
    # The source really prints 910 on one baseline; never infer an exponent.
    assert any(b.get("latex") == "910" for b in raws[12]["questions"][5]["content"])


def test_tall_inline_option_images_belong_to_their_own_labels(pilot):
    q = pilot[2][6]["questions"][26]
    assets = {a["id"]: a for a in q["assets"]}
    assert all(o["content"] for o in q["options"])
    for o in q["options"]:
        for b in o["content"]:
            if b["type"] == "visual":
                assert assets[b["asset_id"]]["option_label"] == o["label"]
                assert b["source"]["bbox"][1] < o["source"]["bbox"][1]
    assert not any(i["code"] == "content_assignment" for i in q["issues"])
    assert any(i["code"] == "raster_math_unverified" for i in q["issues"])


def test_inline_and_display_math_are_explicit_and_source_based(pilot):
    questions = pilot[2][1]["questions"]
    math = [
        b
        for raw in pilot[2].values()
        for q in raw["questions"]
        for b in q["content"]
        if b["type"] == "math"
    ]
    assert any(b["display"] for b in math)
    assert any(not b["display"] for b in math)
    assert all(isinstance(b["display"], bool) for b in math)
    inline = next(
        b for b in questions[3]["content"] if b.get("latex") == r"c\neq \pm \frac{1}{5}"
    )
    assert not inline["display"]


def test_small_superscripts_and_fractional_exponents_preserve_source_geometry(pilot):
    q = pilot[2][6]["questions"]
    assert any(
        b.get("latex") == r"(\frac{2x^{\frac{3}{2}}y^{3}}{\sqrt{z}})^{2}"
        for b in q[5]["content"]
    )
    assert any(
        b.get("latex")
        == r"\frac{3.246\times 10^{6}+3.246\times 10^{4}}{1.623\times 10^{11}}"
        for b in q[13]["content"]
    )


def test_eight_observed_choices_accept_source_answer_h():
    raw = {
        "domain": "mathematics",
        "stage": "mathematics_raw",
        "questions": [
            {
                "id": "s_q1",
                "question_number": 1,
                "options": [{"label": c} for c in "ABCDEFGH"],
                "issues": [],
            }
        ],
        "answer_key": {"entries": [{"question_number": 1, "correct_answer": "H"}]},
    }
    row = match_document(raw, {})[0][0]
    assert row["correct_answer"] == "H" and row["matching"]["status"] == "matched"


def test_matching_reruns_without_opening_a_pdf(pilot, monkeypatch):
    _, paths, _ = pilot
    import pdfplumber

    monkeypatch.setattr(
        pdfplumber, "open", lambda *a, **k: pytest.fail("Matching reopened a PDF")
    )
    a = build(paths)
    b = build(reversed(paths))
    assert a == b
    assert a["summary"]["matched"] == 150
    assert not validate_data(a)["problems"]
    duplicate = paths[0].parent / "duplicate.raw.json"
    shutil.copyfile(paths[0], duplicate)
    with pytest.raises(ValueError):
        build([paths[0], duplicate])


def test_ids_stay_stable_when_local_file_is_renamed(pilot):
    root, _, raws = pilot
    destination = root / "renamed.pdf"
    shutil.copyfile(INPUTS / "math_1.pdf", destination)
    again = parse_pdf(destination, asset_dir=root / "assets")
    assert [q["id"] for q in again["questions"]] == [
        q["id"] for q in raws[1]["questions"]
    ]


def test_inspection_is_selected_offline_and_math_only(pilot):
    _, paths, _ = pilot
    data = build(paths)
    q = select(data, source="math_1", question=4)
    html = render_report(data, q)
    assert html.count("<article class='question-preview'") == 1
    assert "<mfrac>" in html and "Correct Answer" in html
    assert "Original question screenshot" in html and "data:image/png;base64," in html
    assert "https://" not in html and "<script" not in html
    assert (
        "BMAT-specific" not in html
        and "Critical Thinking" not in html
        and "Category" not in html
    )
    assert "max-width:100%" in html and "height:auto" in html
    assert select(data, sample=3, seed=5) == select(data, sample=3, seed=5)
    assert all(q["issues"] for q in select(data, issues=True, sample=2))
    with pytest.raises(ValueError):
        select(data)
    assert select(data, identifier=q[0]["id"])[0]["id"] == q[0]["id"]


def test_grid_rows_table_and_body_diagram_do_not_merge_options(pilot):
    qq = pilot[2][11]["questions"]
    for number, labels in [(10, "ABCDEF"), (25, "ABCDEFGH"), (28, "ABCDEF")]:
        q = qq[number - 1]
        assert [o["label"] for o in q["options"]] == list(labels)
        assert all(o["content"] for o in q["options"])
        assert not any(i["code"] == "content_assignment" for i in q["issues"])
    assert any("Condition (1)" in b.get("text", "") for b in qq[24]["content"])
    assert all(
        any("congruent" in b.get("text", "") for b in o["content"])
        for o in qq[24]["options"]
    )
    assert any("joining three cubes" in b.get("text", "") for b in qq[27]["content"])


def test_option_prose_a_and_money_are_not_false_anchors_or_formula_errors(pilot):
    qq = pilot[2][5]["questions"]
    assert len(qq[25]["options"]) == 5
    assert "horizontal line" in qq[25]["options"][0]["content"][0]["text"]
    assert all(len(qq[12]["options"][i]["content"]) > 0 for i in range(6))
    assert not any(
        i["code"] in {"content_assignment", "malformed_latex"}
        for q in (qq[21], qq[25])
        for i in q["issues"]
    )


def test_persisted_full_corpus_coverage_and_honest_unresolved_cases(monkeypatch):
    path = ROOT / "data/merged/mathematics/questions.json"
    if not path.exists():
        pytest.skip("Generated local full corpus unavailable")
    import pdfplumber

    monkeypatch.setattr(
        pdfplumber,
        "open",
        lambda *a, **k: pytest.fail("Matching/validation reopened PDF"),
    )
    current = json.loads(path.read_text(encoding="utf8"))
    from processors.matching.mathematics import supplied

    raw_paths = sorted((ROOT / "data/raw/mathematics").glob("Test_*.raw.json"))
    rebuilt = supplied.replace_test_sources(current, build(raw_paths))
    key_path = ROOT / "data/merged/mathematics/second_set_answer_key.json"
    key_data = supplied.load(key_path)
    again, scoped_validation = supplied.update_matching(rebuilt, key_data, key_path)
    assert supplied.validate_update(
        again, scoped_validation, key_data, key_path, raw_paths
    )
    assert current == again
    assert current["source"] == "multiple"
    assert current["summary"]["questions"] == 600
    assert current["summary"]["answer_key_entries"] == 384
    assert current["summary"]["sources"] == 20
    assert current["summary"]["matched"] == 568
    result = validate_data(current)
    assert not result["duplicate_ids"]
    assert result["source_issues"]
    assert {
        code: sum(problem["code"] == code for problem in result["problems"])
        for code in {problem["code"] for problem in result["problems"]}
    } == {
        "option_structure": 32,
        "source_count_mismatch": 8,
        "source_coverage": 8,
    }
    matdev = [
        s
        for s in result["by_source"].values()
        if s["questions"] == 30 and s["key_entries"] == 30
    ]
    trial = [
        s for s in result["by_source"].values() if s["key_entries"] < s["questions"]
    ]
    assert len(matdev) == 12 and sum(s["matched"] for s in matdev) == 358
    assert len(trial) == 8 and sum(s["questions"] for s in trial) == 240
    assert sum(s["key_entries"] for s in trial) == 24
    assert sum(s["matched"] for s in trial) == 210
    for q in current["questions"]:
        assets = {a["id"]: a for a in q["assets"]}
        for i in q["issues"]:
            if i["code"] == "uncertain_formula":
                assert Path(assets[i["asset_id"]]["path"]).is_file()
