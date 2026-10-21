"""A stream-late margin number must not turn its passage into the prior option."""

from pathlib import Path

import pytest

from parsers.bmat.parser import parse_pdf, repair_displaced_numbers


def test_real_2010_boundary_preserves_next_stimulus_and_exact_source_spans(tmp_path):
    path = Path("data/input/bmat/BMAT 2010 Section 1 Question Paper.pdf")
    if not path.exists():
        pytest.skip("Local source regression PDF is unavailable")
    data = parse_pdf(path, asset_dir=tmp_path / "assets")
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 36))
    q2, q3 = data["questions"][1:3]
    assert [o["label"] for o in q2["options"]] == list("ABCD")
    assert q2["options"][-1]["text"].strip() == (
        "Some of the arts (for example, opera) may be seen as non-egalitarian."
    )
    assert q2["page_reference"] == {"start_page": 3, "end_page": 3}
    assert "The pupils in a class" in q3["question_text"]
    assert "Lawrence 59 20" in q3["raw"]["question_block"]
    assert q3["visual_assets"], "The next question's chart must not be discarded"
    assert len(q3["visual_previews"]) == 1
    for q in (q2, q3):
        assert q["source_question_key"]["year"] == 2010
        assert (
            "\n".join(
                data["pages"][s["page"] - 1]["raw_text"][s["start"] : s["end"]]
                for s in q["raw"]["page_spans"]
            )
            == q["raw"]["question_block"]
        )


def test_no_reassignment_for_unaligned_cross_page_continuation():
    from copy import deepcopy

    previous = {
        "segments": [{"page": 1}, {"page": 2}],
        "lines": [{"page": 2, "x0": 80, "top": 60}],
    }
    current = {
        "number": 3,
        "lines": [{"text": "3", "page": 2, "x1": 60, "top": 300, "bottom": 312}],
    }
    records = [previous, current]
    before = deepcopy(records)
    repair_displaced_numbers(records, [])
    assert records == before
