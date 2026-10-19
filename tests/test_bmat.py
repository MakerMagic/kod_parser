"""Offline acquisition, raw contracts, semantic exclusions and source regressions."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests
from test_blackstone_raw import write_pdf

from acquisition.bmat.__main__ import INDEX, YEARS, Papers, acquire
from parsers.bmat import parse_pdf, validate_raw
from parsers.bmat.backtest import inspect, report
from parsers.bmat.parser import marker, split_fields
from parsers.bmat.skip_rules import annotate, semantic_tags
from parsers.bmat.text_options import recover
from parsers.bmat.visuals import owner
from processors.bmat.contracts import eligible_records


def task(stem, body="Facts are supplied.", choices=None):
    return {
        "question_text": body + "\n" + stem,
        "raw_components": {"main_question": stem},
        "options": [
            {"label": chr(65 + i), "text": t}
            for i, t in enumerate(
                choices
                or ["First claim", "Second claim", "Third claim", "Fourth claim"]
            )
        ],
    }


def names(q):
    return {t["type"] for t in semantic_tags(q)}


@pytest.mark.parametrize(
    "stem,body,choices,label",
    [
        (
            "Which expression gives the value of x?",
            "The variables satisfy x = 2*y + 3.",
            None,
            "Variable-related question",
        ),
        (
            "Which function of t gives the value of p?",
            "The function is p = 3*t.",
            None,
            "Variable-related question",
        ),
        (
            "Choose two of the statements that must be true.",
            "Facts.",
            None,
            "Several correct answers",
        ),
        ("Select all that apply.", "Facts.", None, "Several correct answers"),
        (
            "Which one would best explain why these results are not incompatible?",
            "The measurements differ.",
            None,
            "Explanation",
        ),
        (
            "Which could not be a possible explanation for this?",
            "There is an observed result.",
            None,
            "Explanation",
        ),
        (
            "Which fact gives support to the explanation offered?",
            "A causal explanation has been offered.",
            None,
            "Explanation",
        ),
        (
            "Which phrase most logically completes the argument?",
            "The argument says ___.",
            None,
            "Complete the text",
        ),
        (
            "Which answer follows?",
            "The passage is quoted.\n[ Source : A journal ]",
            None,
            "Source",
        ),
        (
            "Which condition describes the rule?",
            "Rule.",
            [
                "necessary but not sufficient",
                "sufficient but not necessary",
                "both necessary and sufficient",
                "neither necessary nor sufficient",
            ],
            "Necessary and Sufficient Conditions",
        ),
    ],
)
def test_semantic_positive(stem, body, choices, label):
    assert label in names(task(stem, body, choices))


@pytest.mark.parametrize(
    "q,forbidden",
    [
        (
            task(
                "Which view shows the garden?",
                "Field X has a 4 x 5 grid. Field Y is adjacent.",
            ),
            "Variable-related question",
        ),
        (
            task(
                "What number replaces y?",
                "A table has a single missing entry labelled y.",
            ),
            "Variable-related question",
        ),
        (
            task(
                "Which two statements are true?",
                choices=["1 and 2 only", "1 and 3 only", "2 and 3 only", "1, 2 and 3"],
            ),
            "Several correct answers",
        ),
        (
            task(
                "Which two numbers form the correct pair?",
                choices=["2 and 3", "3 and 4", "4 and 5", "5 and 6"],
            ),
            "Several correct answers",
        ),
        (
            task("Which identifies the flaw that explains this reasoning error?"),
            "Explanation",
        ),
        (
            task("Which conclusion follows?", "The explanation mentions success."),
            "Explanation",
        ),
        (task("What is the cost?", "The data label is ___."), "Complete the text"),
        (
            task("Which source of energy is cheapest?", "The source of heat is gas."),
            "Source",
        ),
        (
            task("Which conclusion follows?", "A necessary investment is described."),
            "Necessary and Sufficient Conditions",
        ),
        ({**task("Which option is correct?"), "options": []}, "No Question"),
    ],
)
def test_semantic_negative(q, forbidden):
    assert forbidden not in names(q)


def test_verified_no_question_requires_native_and_cover_evidence():
    q = {
        **task("How many cabbages are there?"),
        "options": [],
        "option_audit": {
            "cover_allows_write_in": True,
            "possible_label_lines": 0,
            "meaningful_native_objects": 0,
            "text_complete": True,
            "bounded_by_numbered_items": True,
        },
    }
    assert "No Question" in names(q)
    for key, bad in [
        ("cover_allows_write_in", False),
        ("possible_label_lines", 4),
        ("meaningful_native_objects", 3),
        ("text_complete", False),
        ("bounded_by_numbered_items", False),
    ]:
        copy = deepcopy(q)
        copy["option_audit"][key] = bad
        assert "No Question" not in names(copy)


def response(url, payload, error=False):
    def raise_status():
        if error:
            raise requests.HTTPError("Unavailable")

    return SimpleNamespace(
        url=url,
        content=payload,
        text=payload.decode(errors="replace"),
        raise_for_status=raise_status,
    )


def test_acquisition_only_requested_scope_and_idempotence(tmp_path):
    html = (
        "<h4>Practice Papers</h4><h5>Section 1:</h5><a href='mock.pdf'>BMAT 2003 Section 1 Question Paper</a><h4>Past Papers</h4><h5>Section 1:</h5>"
        + "".join(
            f"<a href='https://pmt.physicsandmathstutor.com/{y}.pdf'>BMAT {y} Section 1 Question Paper</a>"
            for y in range(2003, 2023)
        )
        + "<a href='answer.pdf'>BMAT 2017 Section 1 Answer Key</a><h5>Section 2:</h5><a href='bad.pdf'>BMAT 2017 Section 1 Question Paper</a>"
    )
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        return response(
            url,
            html.encode()
            if url == INDEX
            else b"%PDF-1.4\nminimal acquisition fixture\n%%EOF",
        )

    session = SimpleNamespace(get=get)
    data = acquire(tmp_path, session=session)
    assert [r["year"] for r in data["files"]] == list(YEARS)
    assert all(r["status"] == "downloaded" for r in data["files"])
    assert len(calls) == 20
    again = acquire(tmp_path, session=session)
    assert len(calls) == 21 and all(
        r["status"] == "already_downloaded" for r in again["files"]
    )
    first = data["files"][0]
    assert sha256(Path(first["local_path"]).read_bytes()).hexdigest() == first["sha256"]


def test_acquisition_failure_and_missing_year_are_recorded(tmp_path):
    session = SimpleNamespace(
        get=lambda url, **kw: response(url, b"<h4>Past Papers</h4><h5>Section 1:</h5>")
    )
    data = acquire(tmp_path, session=session)
    assert len(data["files"]) == 19 and all(
        r["status"] == "failed" for r in data["files"]
    )
    assert all("found 0" in r["error"] for r in data["files"])
    parser = Papers()
    parser.feed(
        "<h4>Past Papers</h4><h5>Section 1:</h5><a href='one'>BMAT 2017 Section 1 Question Paper</a><a href='two'>BMAT 2017 Section 1 Question Paper</a>"
    )
    assert (
        len(parser.links) == 2
    )  # Ambiguity is preserved, not silently deduplicated by year.


def fixture_pdf(tmp_path):
    cover = [
        (50, 740, "Biomedical Admissions Test 2009"),
        (50, 710, "SECTION 1 Aptitude and Skills"),
        (50, 680, "You should attempt all 2 questions."),
    ]
    first = [
        (50, 740, "Questions 1 to 2 refer to the following information"),
        (80, 710, "All objects follow a rule."),
        (50, 650, "1 Which claim follows?"),
        (80, 620, "A First claim"),
        (80, 590, "B Second claim"),
        (80, 560, "C Third claim"),
        (80, 530, "D Fourth claim"),
    ]
    second = [
        (50, 740, "2 How many objects are required?"),
        (80, 710, "A 2"),
        (80, 680, "B 3"),
        (80, 650, "C 4"),
        (80, 620, "D 5"),
    ]
    return write_pdf(tmp_path / "arbitrary-name.pdf", [cover, first, second])


def test_cross_page_shared_range_raw_fidelity_determinism_and_inspection(tmp_path):
    path = fixture_pdf(tmp_path)
    assets = tmp_path / "raw/assets"
    data = parse_pdf(path, asset_dir=assets)
    again = parse_pdf(path, asset_dir=assets, overwrite_assets=True)
    assert data == again
    assert [q["question_number"] for q in data["questions"]] == [1, 2]
    assert not data["warnings"]
    assert all(q["bmat_filter"]["skip_from_pipeline"] for q in data["questions"])
    assert len(data["shared_information_ranges"][0]["affected_question_ids"]) == 2
    assert eligible_records(data) == []
    validate_raw(data)
    raw = tmp_path / "raw/test.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    before = raw.read_bytes()
    assert inspect(raw, 1, tmp_path / "inspect.html") == "skipped"
    html = (tmp_path / "inspect.html").read_text(encoding="utf-8")
    assert "Shared Information Range" in html and "Original source preview" in html
    summary = report([raw], tmp_path / "issues.md")
    assert summary["questions"] == summary["unique_intentional_skips"] == 2
    assert raw.read_bytes() == before
    bad = deepcopy(data)
    bad["questions"][0]["raw"]["question_block"] += "invented text"
    with pytest.raises(ValueError, match="page spans"):
        validate_raw(bad)


@pytest.mark.parametrize(
    "height,spans,expected", [(690, 1, True), (230, 1, False), (690, 2, False)]
)
def test_full_page_is_layout_not_length_or_continuation(height, spans, expected):
    q = task("Which answer follows?")
    q.update(
        question_id="stable",
        question_number=1,
        raw={"page_spans": [{"page": i + 1} for i in range(spans)]},
        layout_blocks=[
            {
                "type": "text",
                "component": "question_body",
                "page": 1,
                "bbox": [50, 50, 500, 70],
            },
            {
                "type": "text",
                "component": "option",
                "label": "D",
                "page": 1,
                "text": "D Fourth claim",
                "bbox": [50, height - 10, 500, height],
            },
        ],
    )
    d = {
        "questions": [q],
        "pages": [{"page_number": 1, "height": 800}],
        "shared_information_ranges": [],
        "extraction": {"expected_questions": 1},
    }
    annotate(d)
    assert any(t["type"] == "too long" for t in q["bmat_filter"]["types"]) == expected


def test_centred_owner_rejects_shared_objects_and_body_geometry():
    cells = [
        {
            "label": "A",
            "page": 1,
            "bbox": [90, 100, 100, 112],
            "cell": [0, 100, 150, 300],
        },
        {
            "label": "B",
            "page": 1,
            "bbox": [190, 100, 200, 112],
            "cell": [150, 100, 300, 300],
        },
    ]
    assert owner([60, 130, 130, 250], cells, 1)["label"] == "A"
    assert owner([60, 30, 130, 80], cells, 1) is None
    assert owner([60, 130, 230, 250], cells, 1) is None


def test_alternating_print_margin_is_not_replaced_by_numbered_body_column(tmp_path):
    cover = [
        (50, 740, "Biomedical Admissions Test 2008"),
        (50, 710, "SECTION 1"),
        (50, 680, "attempt all 2 questions"),
    ]
    page1 = [
        (55, 740, "1 A set of statements is shown."),
        *[(80, 710 - i * 20, f"{i + 1} Some numerical body data") for i in range(6)],
        (80, 550, "Which answer follows?"),
        *[(80, 520 - i * 20, c + " A claim") for i, c in enumerate("ABCD")],
    ]
    page2 = [
        (49.6, 740, "2 What value is needed?"),
        *[(75, 700 - i * 20, c + " 3") for i, c in enumerate("ABCD")],
    ]
    source = write_pdf(tmp_path / "parity.pdf", [cover, page1, page2])
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    assert [q["question_number"] for q in data["questions"]] == [1, 2]
    assert not data["warnings"]


def test_alphabetical_passage_is_not_answer_options():
    texts = [
        "1 A code is shown below.",
        *[f"{c} {chr(78 + i)}" for i, c in enumerate("ABCDEFGHIJKLM")],
        "How many labels are incorrect?",
        *[f"{c} {i}" for i, c in enumerate("ABCDE", 1)],
    ]
    block = "\n".join(texts)
    lines, offset = [], 0
    for text in texts:
        lines.append({"text": text, "x0": 80, "block_start": offset})
        offset += len(text) + 1
    body, _, choices, _, _ = split_fields(block, lines)
    assert "M Z" in body
    assert [o["label"] for o in choices] == list("ABCDE")
    assert [o["text"].strip() for o in choices] == list("12345")


@pytest.mark.parametrize("separator", [" ", "(cid:3)", "(cid:3) "])
def test_mixed_cid_separator_does_not_eat_first_word(separator):
    for label, kind, glyph in [("8", "number", 27), ("A", "option", 36)]:
        raw = (
            f"(cid:{glyph})"
            + separator
            + "(cid:55)(cid:75)(cid:72)(cid:3)(cid:73)(cid:76)(cid:85)(cid:86)(cid:87)"
        )
        value, end = marker({"text": raw, "readable_text": label + " The first"}, kind)
        assert str(value) == label
        assert raw[end:].startswith("(cid:55)(cid:75)(cid:72)")


def field_lines(texts):
    lines, offset = [], 0
    for text in texts:
        lines.append({"text": text, "x0": 80, "block_start": offset})
        offset += len(text) + 1
    return "\n".join(texts), lines


def test_graph_tick_alphabets_do_not_become_extra_options():
    block, lines = field_lines(
        [
            "1 Which graph is correct?",
            "A B",
            "A B C D E A B C D E",
            "C D",
            "A B C D E A B C D E",
            "E",
            "A B C D E",
        ]
    )
    assert [o["label"] for o in split_fields(block, lines)[2]] == list("ABCDE")


def test_lowercase_relative_clause_in_option_is_not_a_new_request():
    block, lines = field_lines(
        [
            "1 Some information.",
            "Which one follows?",
            "A A student needs a special interest",
            "which will impress the tutors.",
            "B A parent must be truthful.",
            "C A school has good results.",
            "D A worker arrives on time.",
            "E An adult reads quickly.",
        ]
    )
    choices = split_fields(block, lines)[2]
    assert [o["label"] for o in choices] == list("ABCDE")
    assert "which will impress" in choices[0]["text"]


def test_vertically_centred_prose_labels_keep_first_lines_and_exact_spans():
    texts = [
        "1 A passage is supplied.",
        "Which answer follows?",
        "The first claim begins on this line",
        "A",
        "and continues on this second line.",
        "The next claim has its first line here",
        "B",
        "and its continuation is important.",
        "The final claim begins before its label",
        "C",
        "and also has a second line.",
    ]
    block, lines = field_lines(texts)
    for i, l in enumerate(lines):
        l.update(page=1, top=60 + i * 10, bottom=69 + i * 10, x1=500)
        if l["text"] not in "ABC":
            l["x0"] = 110 if i >= 2 else 80
    body, opts, choices, _, _ = split_fields(block, lines)
    q = {
        "question_text": body,
        "raw": {"question_block": block, "options_block": opts},
        "options": choices,
        "images": [],
    }
    recover(q, {"lines": lines}, marker, lambda t: t)
    assert q["options"][0]["text"].startswith("The first claim")
    assert q["options"][1]["text"].startswith("The next claim")
    assert "The first claim" not in q["question_text"]
    assert "The next claim" not in q["options"][0]["text"]
    assert q["raw"]["question_block"] == block
    for o in q["options"]:
        for line in o["source_lines"]:
            assert (
                block[slice(line["raw_span"]["start"], line["raw_span"]["end"])]
                == line["text"]
            )


@pytest.mark.parametrize("wrapped", [False, True])
def test_range_after_options_does_not_steal_preceding_answer(tmp_path, wrapped):
    cover = [
        (50, 740, "Biomedical Admissions Test 2009"),
        (50, 710, "SECTION 1"),
        (50, 680, "attempt all 3 questions"),
    ]
    pages = []
    for n in range(1, 4):
        rows = [
            (50, 740, f"{n} Which statement follows?"),
            *[
                (80, 700 - i * 24, c + " A complete statement")
                for i, c in enumerate("ABCD")
            ],
        ]
        if n == 1:
            rows.append(
                (
                    50,
                    540,
                    "Questions 2 to 3"
                    + ("" if wrapped else " refer to the following information"),
                )
            )
            if wrapped:
                rows.append((80, 520, "refer to the following information"))
            rows.append((80, 500, "All objects are square."))
        pages.append(rows)
    source = write_pdf(tmp_path / "shared.pdf", [cover, *pages])
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    assert not data["warnings"]
    assert [o["label"] for o in data["questions"][0]["options"]] == list("ABCD")
    assert data["questions"][0]["options"][-1]["text"].strip() == "A complete statement"
    assert not data["questions"][0]["bmat_filter"]["skip_from_pipeline"]
    assert all(
        q["bmat_filter"]["primary_type"] == "Shared Information Range"
        for q in data["questions"][1:]
    )
    before = deepcopy(data)
    annotate(data)
    assert data == before


@pytest.mark.parametrize("year,count", [(2003, 40), (2013, 35), (2017, 35), (2020, 32)])
def test_real_pilot_numbering_and_raw_spans(year, count):
    paths = list(Path("inspections_bmat/pilot").glob(f"bmat_{year}_*.raw.json"))
    if not paths:
        pytest.skip("Optional local BMAT pilot unavailable")
    d = json.loads(paths[0].read_text(encoding="utf-8"))
    validate_raw(d)
    assert [q["question_number"] for q in d["questions"]] == list(range(1, count + 1))
    assert all(q["source_question_key"]["source"] == "bmat" for q in d["questions"])
