"""Native fraction/radical fidelity and source geometry regressions."""

import json
from pathlib import Path

import pytest

from parsers.mathematics.formulas import formula_bounds, recover
from parsers.mathematics.source import parse_pdf
from parsers.mathematics.structure import walk

ROOT = Path(__file__).resolve().parents[1]


def glyph(text, x, y, size=10):
    return {
        "text": text,
        "x0": x,
        "x1": x + 5,
        "top": y,
        "bottom": y + size,
        "size": size,
        "fontname": "Cambria Math",
    }


def test_fraction_slash_uses_geometry_and_preserves_inequality():
    chars = [
        glyph("p", 0, 10),
        glyph("≤", 8, 10),
        glyph("1", 18, 6),
        glyph("3", 28, 14),
        glyph("⁄", 23, 10),
    ]
    assert recover(chars, [])[0] == r"p\leq \frac{1}{3}"
    # A literal slash without raised/lowered operands is not guessed into a fraction.
    assert (
        recover([glyph("1", 0, 10), glyph("⁄", 5, 10), glyph("3", 10, 10)], [])[0]
        is None
    )


def test_stretched_radical_uses_vinculum_and_complete_fraction():
    chars = [glyph("√", 0, 10), glyph("3", 8, 6, 8), glyph("2", 8, 18, 8)]
    chars[0]["x1"] = 8
    rules = [
        {"x0": 8, "x1": 13, "top": 2, "bottom": 2.5},
        {"x0": 8, "x1": 13, "top": 15, "bottom": 15.5},
    ]
    assert recover(chars, rules)[0] == r"\sqrt{\frac{3}{2}}"
    box = formula_bounds(chars, rules)
    assert box[1] == 2 and box[3] == 26


def test_missing_or_ambiguous_radical_scope_stays_unresolved():
    assert (
        recover([glyph("√", 0, 0), glyph("x", 8, 0), glyph("+", 14, 0)], [])[0] is None
    )
    chars = [glyph("√", 0, 0), glyph("(", 8, 0), glyph("x", 14, 0), glyph(")", 20, 0)]
    chars[0]["x1"] = 8
    bar = {"x0": 8, "x1": 19, "top": -2, "bottom": -1.5}
    result, code, reason = recover(chars, [bar])
    assert (
        result is None
        and code == "uncertain_formula"
        and "delimiter boundary" in reason
    )


@pytest.fixture(scope="module")
def selected_source(tmp_path_factory):
    return parse_pdf(
        ROOT / "acquisition/local/mathematics/matdev/math_6.pdf",
        asset_dir=tmp_path_factory.mktemp("native-radicals") / "assets",
        question_numbers={9, 10, 16, 17},
    )


def question(data, number):
    return next(q for q in data["questions"] if q["question_number"] == number)


def test_inequality_options_are_canonical_latex_in_source_order(selected_source):
    q = question(selected_source, 9)
    expected = [
        r"0\leq p\leq \frac{1}{3}",
        r"\frac{1}{3}\leq p\leq \frac{2}{5}",
        r"\frac{1}{3}\leq p\leq 1",
        r"0\leq p\leq \frac{5}{6}",
        r"\frac{2}{5}\leq p\leq \frac{5}{6}",
    ]
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert [[b.get("latex") for b in o["content"]] for o in q["options"]] == [
        [v] for v in expected
    ]
    assert all(b["type"] == "math" for o in q["options"] for b in o["content"])
    assert not q["issues"]


def test_radical_options_complete_without_letters_or_image_fallback(selected_source):
    q = question(selected_source, 10)
    assert [o["content"][0].get("latex") for o in q["options"]] == [
        r"\sqrt{2}",
        r"\sqrt{\frac{3}{2}}",
        r"\sqrt{\frac{5}{2}}",
        r"\sqrt{3}",
        r"\sqrt{5}",
    ]
    assert all(b["type"] == "math" for o in q["options"] for b in o["content"])
    assert not q["issues"]
    # The genuine cube diagram remains the identical source asset.
    old = json.loads(
        next((ROOT / "data/raw/mathematics").glob("math_6_*.raw.json")).read_text(
            encoding="utf8"
        )
    )
    before = question(old, 10)
    old_visuals = [b["asset_id"] for b in before["content"] if b["type"] == "visual"]
    assert [b["asset_id"] for b in q["content"] if b["type"] == "visual"] == old_visuals
    for o in q["options"][1:3]:
        source = o["content"][0]["source"]
        page = next(p for p in selected_source["pages"] if p["page"] == source["page"])
        chars = [c for c in page["glyphs"] if c["id"] in source["glyph_ids"]]
        assert source["bbox"][1] < min(c["top"] for c in chars)


def test_body_radicals_keep_nested_source_scope_and_full_bounds(selected_source):
    q16, q17 = question(selected_source, 16), question(selected_source, 17)
    m16 = next(b for b in q16["content"] if b["type"] == "math")
    m17 = next(b for b in q17["content"] if b["type"] == "math")
    assert (
        m16["latex"]
        == r"\sqrt{\frac{2\times 10^{3}+8\times 10^{2}}{\frac{1}{2500}+3\times 10^{-4}}}"
    )
    assert m17["latex"] == r"\sqrt{\frac{2}{x}+1}=y-3"
    assert not q16["issues"] and not q17["issues"]
    assert q17["regions"][0]["bbox"][1] <= m17["source"]["bbox"][1]
    preview = next(a for a in q17["assets"] if a["role"] == "source_preview")
    assert preview["bbox"][1] <= m17["source"]["bbox"][1]
    assert all(
        b["type"] not in {"visual", "unresolved_math"} for b in walk(q16["content"])
    )


def test_radical_recovery_keeps_numbering_options_and_raw_glyphs(selected_source):
    old = json.loads(
        next((ROOT / "data/raw/mathematics").glob("math_6_*.raw.json")).read_text(
            encoding="utf8"
        )
    )
    for q in selected_source["questions"]:
        original = question(old, q["question_number"])
        assert q["id"] == original["id"] and q["raw"] == original["raw"]
        assert [o["label"] for o in q["options"]] == [
            o["label"] for o in original["options"]
        ]


@pytest.mark.parametrize(
    "source,number,option,expected",
    [
        (2, 30, "C", r"\sqrt{\frac{p+qr}{r^{2}}}"),
        (3, 11, "A", r"\pm 2\sqrt{\frac{y+10}{5}}+6"),
        (7, 18, "A", "10" + r"\sqrt{\frac{1}{8-π}}"),
        (9, 28, None, r"y=1+\sqrt{\frac{x+3}{x}}"),
    ],
)
def test_existing_issue_analogues_recover_only_source_supported_scope(
    tmp_path, source, number, option, expected
):
    raw = parse_pdf(
        ROOT / f"acquisition/local/mathematics/matdev/math_{source}.pdf",
        asset_dir=tmp_path / "assets",
        question_numbers={number},
    )
    q = raw["questions"][0]
    blocks = (
        next(o["content"] for o in q["options"] if o["label"] == option)
        if option
        else q["content"]
    )
    assert any(b.get("latex") == expected for b in blocks)
    assert not q["issues"]


def test_ambiguous_source_radical_keeps_issue_and_full_diagnostic_trace(tmp_path):
    raw = parse_pdf(
        ROOT / "acquisition/local/mathematics/matdev/math_12.pdf",
        asset_dir=tmp_path / "assets",
        question_numbers={13},
    )
    q = raw["questions"][0]
    unresolved = next(b for b in q["content"] if b["type"] == "unresolved_math")
    assert "delimiter boundary" in unresolved["reason"]
    assert any(
        i.get("asset_id") == unresolved["diagnostic_asset_id"] for i in q["issues"]
    )
    assert unresolved["raw_text"] and unresolved["source"]["glyph_ids"]


def test_unbarred_literal_roots_preserve_explicit_source_scope():
    text = "4=√(x+√(x+√(x+√(x+...))))"
    assert recover([glyph(c, i * 5, 0) for i, c in enumerate(text)], [])[0] == (
        r"4=\sqrt{(x+\sqrt{(x+\sqrt{(x+\sqrt{(x+...)})})})}"
    )
    assert (
        recover([glyph(c, i * 5, 0) for i, c in enumerate("(R√3)/16")], [])[0]
        == r"(R\sqrt{3})/16"
    )
    assert recover([glyph(c, i * 5, 0) for i, c in enumerate("√(x+3")], [])[0] is None


def test_math4_literal_roots_are_text_and_real_diagram_is_preserved(tmp_path):
    raw = parse_pdf(
        ROOT / "acquisition/local/mathematics/matdev/math_4.pdf",
        asset_dir=tmp_path / "assets",
        question_numbers={7, 10},
    )
    q7, q10 = question(raw, 7), question(raw, 10)
    assert not q7["issues"] and not q10["issues"]
    math = next(b for b in q7["content"] if b["type"] == "math")
    assert math["latex"].count(r"\sqrt{") == 4
    assert math["latex"].count("(") == math["latex"].count(")") == 4
    assert [o["content"][0]["latex"] for o in q10["options"]] == [
        r"(R\sqrt{3})/4",
        "R/4",
        r"(R\sqrt{3})/8",
        "R/8",
        r"(R\sqrt{3})/16",
    ]
    assert any(b["type"] == "visual" for b in q10["content"])
    from processors.matching.mathematics.backtest import render_question

    for q in (q7, q10):
        rendered = render_question(q, raw["source_document"])
        assert "<msqrt>" in rendered
        assert "Formula extraction unresolved" not in rendered
