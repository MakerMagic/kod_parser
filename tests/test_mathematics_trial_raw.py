"""Trial-set RAW segmentation, leading visuals and shared formula regressions."""

import json
from hashlib import sha256
from pathlib import Path

import pytest

from parsers.mathematics.backtest import load_raw
from parsers.mathematics.backtest import main as inspect_main
from parsers.mathematics.layout import profile
from parsers.mathematics.raw_issues import collect
from parsers.mathematics.source import parse_pdf
from parsers.mathematics.structure import walk

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "acquisition/local/mathematics/sky (trial)"
CASES = {
    1: [20, 23],
    2: [7, 20, 21],
    3: [12],
    4: [4, 9, 12, 13, 14, 16, 20, 23],
    5: [8, 11, 20, 28],
    6: [21, 28],
    7: [4],
}


def saved(test):
    return next((ROOT / "data/raw/mathematics").glob(f"Test_{test}_*.raw.json"))


@pytest.fixture(scope="module")
def parsed(tmp_path_factory):
    output = tmp_path_factory.mktemp("trial-parser")
    result = {}
    for number, questions in CASES.items():
        requested = set(questions) | ({24} if number == 1 else set())
        result[number] = parse_pdf(
            INPUT / f"Test_{number}.pdf",
            asset_dir=output / "assets",
            question_numbers=requested,
        )
    return result


@pytest.mark.parametrize("test,number", [(t, n) for t, ns in CASES.items() for n in ns])
def test_leading_diagram_belongs_to_next_question_in_source_order(parsed, test, number):
    data = parsed[test]
    q = next(q for q in data["questions"] if q["question_number"] == number)
    first = q["content"][0]
    assert first["type"] == "visual"
    assert first["order"] == 1
    box = first["source"]["bbox"]
    assert q["regions"][0]["bbox"][1] <= box[1]
    source = json.loads(saved(test).read_text(encoding="utf8"))
    previous = next(
        q for q in source["questions"] if q["question_number"] == number - 1
    )
    assert not any(
        a["bbox"] == box and a["page"] == first["source"]["page"]
        for a in previous["assets"]
        if a["role"] in {"body", "option"}
    )
    if test == 3:
        assert sum(b["type"] == "visual" for b in q["content"]) == 1


@pytest.mark.parametrize("number", range(1, 9))
def test_complete_numbering_cover_exclusion_and_source_identity(number):
    data = json.loads(saved(number).read_text(encoding="utf8"))
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 31))
    assert len({q["id"] for q in data["questions"]}) == 30
    assert data["source_document"]["source"] == "sky_trial"
    assert data["source_document"]["version"] == str(number)
    assert data["pages"][0]["role"] == "cover"
    assert all(r["page"] != 1 for q in data["questions"] for r in q["regions"])
    assert not data["issues"]
    assert data["pages"][-1]["role"] == ("answer_key" if number == 8 else "questions")


def test_formula_order_scripts_and_full_vector_roots_reuse_existing_math_engine(parsed):
    q = next(q for q in parsed[1]["questions"] if q["question_number"] == 24)
    assert [o["content"][0]["latex"] for o in q["options"]] == [
        r"\sqrt{\frac{V}{3}}",
        r"\sqrt[3]{\frac{V}{3}}",
        r"\sqrt{\frac{2V}{3}}",
        r"\sqrt[3]{\frac{2V}{3}}",
        r"\sqrt[3]{\frac{4V}{3}}",
    ]
    assert not q["issues"]
    assert all(b["type"] == "math" for o in q["options"] for b in o["content"])
    for o in q["options"]:
        block = o["content"][0]
        page = parsed[1]["pages"][block["source"]["page"] - 1]
        glyphs = [c for c in page["glyphs"] if c["id"] in block["source"]["glyph_ids"]]
        root = next(c for c in glyphs if c["text"] == "√")
        assert root["method"] == "connected_vector_radical"
        assert block["source"]["bbox"][1] <= root["top"]
    q20 = next(q for q in parsed[1]["questions"] if q["question_number"] == 20)
    assert q20["options"][0]["content"][0]["latex"] == "5a^{2}+10"
    q23 = next(q for q in parsed[1]["questions"] if q["question_number"] == 23)
    assert q23["options"][0]["content"][0]["latex"] == r"r(4+\sqrt{2})"


def test_raster_math_is_not_accepted_as_visual_or_invented_latex():
    data = json.loads(saved(8).read_text(encoding="utf8"))
    for number in (1, 7, 13):
        q = next(q for q in data["questions"] if q["question_number"] == number)
        assert q["extraction_status"] == "review"
        blocks = list(walk(q["content"]))
        assert any(b["type"] == "unresolved_math" for b in blocks)
        assert any(i["code"] == "raster_math_unverified" for i in q["issues"])
    q13 = next(q for q in data["questions"] if q["question_number"] == 13)
    assert any(i["code"] == "ocr_question_number" for i in q13["issues"])


def test_raw_backtest_selects_raw_without_matching_or_mutating_data(
    tmp_path, monkeypatch
):
    import pdfplumber

    monkeypatch.setattr(
        pdfplumber, "open", lambda *a, **k: pytest.fail("RAW preview opened PDF")
    )
    path = saved(3)
    before = sha256(path.read_bytes()).hexdigest()
    data = load_raw([path])
    assert data["stage"] == "mathematics_raw"
    for width in (1166, 1350):
        out = tmp_path / f"preview-{width}.html"
        assert (
            inspect_main(
                [
                    "--raw-json",
                    str(path),
                    "--test",
                    "3",
                    "--question",
                    "12",
                    "--width",
                    str(width),
                    "--output",
                    str(out),
                ]
            )
            == 0
        )
        html = out.read_text(encoding="utf8")
        assert "question-preview" in html and "detailed-report" in html
        assert "Test_3.pdf" in html and "sky_trial" in html
        assert html.count("class='question-preview'") == 1
    with pytest.raises(ValueError, match="explicit"):
        inspect_main(
            ["--raw-json", str(path), "--output", str(tmp_path / "unselected.html")]
        )
    assert sha256(path.read_bytes()).hexdigest() == before


def test_trial_raw_findings_have_question_source_page_field_and_reason():
    findings = collect([saved(n) for n in range(1, 9)])
    assert findings
    assert all(
        f["question_id"]
        and f["source_pdf"]
        and f["page"]
        and f["field"]
        and f["reason"]
        for f in findings
    )


def test_content_identity_never_depends_on_filename():
    assert profile("Trial SET #2 (math)", "abc")["id"] == "sky_trial_v2_abc"
    with pytest.raises(ValueError, match="content-derived identity"):
        profile("Unrecognized cover", "abc")
