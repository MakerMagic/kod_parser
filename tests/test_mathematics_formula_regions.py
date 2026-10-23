"""Source geometry regressions for complete mathematical regions, not solutions."""

import json
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest

from parsers.mathematics.formulas import rule_contains
from parsers.mathematics.latex import mathml, validate
from parsers.mathematics.source import parse_pdf
from parsers.mathematics.structure import walk
from processors.matching.mathematics.backtest import render_report

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def corrected(tmp_path_factory):
    root = tmp_path_factory.mktemp("formula-regions")
    result = {}
    for test, numbers in (
        (1, {7, 28}),
        (2, {9, 16, 25, 26, 27, 29}),
        (3, {3, 6}),
        (4, {6, 30}),
        (5, {5, 10, 21}),
        (7, {7, 25}),
    ):
        result[test] = parse_pdf(
            ROOT / f"acquisition/local/mathematics/sky (trial)/Test_{test}.pdf",
            asset_dir=root / "assets",
            question_numbers=numbers,
        )
    return result


def question(data, number):
    return next(q for q in data["questions"] if q["question_number"] == number)


def formulas(blocks):
    return [b["latex"] for b in walk(blocks) if b["type"] == "math"]


def test_fraction_arrow_and_all_operators_are_one_source_expression(corrected):
    q = question(corrected[1], 7)
    assert r"a\Uparrow b=\frac{a-b}{a+2b}" in formulas(q["content"])
    assert not q["issues"]


def test_pi_numerators_and_complete_answer_sets_precede_option_baseline(corrected):
    q = question(corrected[1], 28)
    expected = [
        r"\{0,\frac{\pi }{3},\frac{5\pi }{3},2\pi \}",
        r"\{\frac{\pi }{6},\frac{5\pi }{6},\frac{5\pi }{3}\}",
        r"\{0,\frac{2\pi }{3},\frac{4\pi }{3},2\pi \}",
        r"\{\frac{\pi }{2},\frac{5\pi }{4},\frac{7\pi }{6}\}",
        r"\{\frac{\pi }{4},\frac{3\pi }{4}\}",
    ]
    assert [formulas(o["content"])[0] for o in q["options"]] == expected
    assert (
        q["options"][0]["content"][0]["source"]["bbox"][1]
        < q["options"][0]["source"]["bbox"][1] - 7
    )
    assert not q["issues"]


def test_native_system_keeps_both_inequalities_and_all_fractions(corrected):
    q = question(corrected[2], 9)
    expected = (
        r"\begin{cases}\frac{3}{4}(x-1)+\frac{7}{8}<\frac{1}{4}(x-1)+\frac{5}{2},"
        r"\\\frac{x}{4}-\frac{2x-3}{3}<2;\end{cases}"
    )
    assert formulas(q["content"]) == [expected]
    tree = fromstring(mathml(expected))
    assert len(list(tree.iter("{http://www.w3.org/1998/Math/MathML}mtr"))) == 2
    assert validate(r"\begin{cases}x=1\end{cases}")
    assert not q["issues"]


def test_fraction_exponents_and_vector_roots_remain_canonical_math(corrected):
    q = question(corrected[2], 16)
    assert formulas(q["content"]) == [r"\frac{e^{x}-e^{-x}}{e^{x}+e^{-x}}=\frac{1}{2}"]
    assert formulas(q["options"][1]["content"]) == [r"ln\sqrt{3}"]
    assert formulas(q["options"][3]["content"]) == [r"\frac{1}{2}ln\sqrt{3}"]
    assert not any(
        b["type"] in {"visual", "unresolved_math"}
        for o in q["options"]
        for b in o["content"]
    )
    assert not q["issues"]


def test_side_diagram_and_its_labels_do_not_become_answer_options(corrected):
    q = question(corrected[2], 25)
    assert len([b for b in q["content"] if b["type"] == "visual"]) == 1
    assert [formulas(o["content"])[0] for o in q["options"]] == [
        r"\sqrt{19}",
        r"2\sqrt{5}",
        r"\sqrt{21}",
        r"\sqrt{22}",
        r"\sqrt{23}",
    ]
    assert not q["issues"]


def test_brackets_inner_expression_and_exponents_stay_together(corrected):
    q = question(corrected[2], 26)
    assert formulas(q["content"])[0] == r"f(x)=(2+x)^{2}(2-x^{2})^{2}"
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert all(o["content"] for o in q["options"])
    assert not q["issues"]


def test_fraction_sine_denominator_and_upper_x_are_complete(corrected):
    q = question(corrected[2], 27)
    assert r"\frac{x}{sin^{2}x}" in formulas(q["options"][0]["content"])
    assert formulas(q["options"][3]["content"]) == [r"1+\frac{x}{sin^{2}x}"]
    assert not q["issues"]


def test_skewed_font_advance_controls_membership_without_clipping_ink():
    c = {
        "text": "m",
        "x0": 88.7,
        "x1": 100.8,
        "top": 118.5,
        "bottom": 129.3,
        "size": 10.8,
        "pdf_text_x0": 88.9,
        "pdf_text_x1": 97.3,
    }
    assert rule_contains(c, {"x0": 73.8, "x1": 98.4})
    assert not rule_contains(
        {**c, "pdf_text_x0": 101, "pdf_text_x1": 110}, {"x0": 73.8, "x1": 98.4}
    )


@pytest.mark.parametrize(
    "test,number,expected",
    [
        (3, 3, r"\frac{3^{x}+3^{x}+3^{x}}{6^{x}+6^{x}+6^{x}}=?"),
        (3, 6, r"\sqrt{2}⋅\sqrt[3]{4}⋅\sqrt[6]{32}=?"),
        (4, 6, r"\frac{\sqrt[3]{2}⋅\sqrt[4]{8}⋅\sqrt[6]{4}}{2⋅\sqrt[12]{2}}=?"),
        (5, 5, r"(2k^{\frac{1}{2}})^{-2}"),
        (7, 7, r"(\sqrt[4]{\frac{ab}{\sqrt{ab}}})^{2}=?"),
        (7, 25, r"(\frac{\pi }{2}+x)."),
    ],
)
def test_analogous_recorded_issues_keep_scripts_delimiters_and_full_radicals(
    corrected, test, number, expected
):
    q = question(corrected[test], number)
    assert expected in formulas(q["content"])
    assert not q["issues"]


def test_skewed_m_stays_inside_its_fraction_and_integral_uncertainty_remains(corrected):
    q = question(corrected[5], 21)
    assert formulas(q["options"][0]["content"]) == [r"\frac{m}{1-m}"]
    assert formulas(q["options"][4]["content"]) == [r"\frac{4-m}{1-4m}"]
    partial = question(corrected[4], 30)
    assert len(partial["issues"]) == 1
    assert partial["issues"][0]["field"] == "question"
    assert formulas(partial["options"][1]["content"]) == [r"\frac{\pi }{2}"]


def test_inverse_function_spaces_do_not_split_fraction_or_join_the_next_line(corrected):
    q = question(corrected[5], 10)
    assert (
        formulas(q["content"])[0] == r"f(x)=\frac{x-3}{2},f^{-1}(x)+f^{-1}(2x)=12⇒x=?"
    )
    note = next(b for b in q["content"] if b.get("latex") == r"(f^{-1}(x)")
    assert note["break_before"]
    assert not q["issues"]


def test_all_math_bounds_retain_source_glyph_extents(corrected):
    for data in corrected.values():
        glyphs = {c["id"]: c for p in data["pages"] for c in p["glyphs"]}
        for q in data["questions"]:
            for b in walk(
                [*q["content"], *[b for o in q["options"] for b in o["content"]]]
            ):
                if b["type"] != "math":
                    continue
                x0, y0, x1, y1 = b["source"]["bbox"]
                for gid in b["source"]["glyph_ids"]:
                    c = glyphs[gid]
                    assert x0 <= c["x0"] <= c["x1"] <= x1
                    assert y0 <= c["top"] <= c["bottom"] <= y1


def test_shared_backtest_projects_system_and_fraction_math_from_same_raw(corrected):
    data = corrected[2]
    q = question(data, 9)
    html = render_report(
        {"sources": {data["source_document"]["id"]: data["source_document"]}}, [q]
    )
    assert "mtable" in html and "mfrac" in html and q["id"] in html
    assert "data-latex='\\begin{cases}" in html


def test_targeted_regeneration_preserves_unselected_records_and_source_geometry(
    tmp_path,
):
    from parsers.mathematics.__main__ import main

    source = ROOT / "acquisition/local/mathematics/sky (trial)/Test_1.pdf"
    path = next((ROOT / "data/raw/mathematics").glob("Test_1_*.raw.json"))
    before = json.loads(path.read_text(encoding="utf8"))
    target = tmp_path / path.name
    target.write_text(json.dumps(before), encoding="utf8")
    main([str(source), "--output-dir", str(tmp_path), "--overwrite", "--question", "7"])
    after = json.loads(target.read_text(encoding="utf8"))
    selected = set(question(before, 7)["raw"]["glyph_ids"])
    assert before["answer_key"] == after["answer_key"]
    for a, b in zip(before["questions"], after["questions"]):
        assert a["id"] == b["id"]
        if a["question_number"] != 7:
            assert a == b
    for oldpage, newpage in zip(before["pages"], after["pages"]):
        for a, b in zip(oldpage["glyphs"], newpage["glyphs"]):
            assert all(b[key] == value for key, value in a.items())
            if a["id"] not in selected:
                assert a == b
    assert not question(after, 7)["issues"]
