"""Geometry-backed prose wraps: capitals are not paragraph evidence."""

import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from processors.normalization.blackstone import clean_dataset, validate_clean
from processors.normalization.blackstone.backtest import inspect_question, render_html
from processors.normalization.blackstone.storage import write_clean
from processors.normalization.blackstone.text import normalize_text

ROOT = Path(__file__).resolve().parents[1]


def evidence(lines):
    return [
        {
            "text": text,
            "bbox": [80, 100 + i * 12, 500, 110 + i * 12],
            "page": 1,
            "component": "stimulus",
            "order": i + 1,
        }
        for i, text in enumerate(lines)
    ]


@pytest.mark.parametrize(
    "left,right",
    [
        ("The revenue was transferred into the", "Netherlands and Switzerland."),
        ("We arranged to meet again in", "London after the concert."),
        ("The new term begins on", "Monday after the holiday."),
        ("The new term begins in", "January."),
        ("The payments were collected by", "UNICEF for its emergency fund."),
        ("My neighbour was employed by", "Google for several years."),
        ("I discussed the plan with", "Amelia before the meeting."),
        (
            "The proposal was examined by National Health",
            "Service officials last year.",
        ),
        ("Their tax was paid in the", "UK."),
    ],
)
def test_names_are_joined_from_context_not_a_dictionary(left, right):
    raw = left + "\n" + right
    assert (
        normalize_text(raw, contextual_wraps=True, line_context=evidence([left, right]))
        == left + " " + right
    )
    # Without verified layout, syntactic plausibility does not silently force a join.
    assert normalize_text(raw, contextual_wraps=True) == raw


@pytest.mark.parametrize(
    "kind",
    [
        "gap",
        "indent",
        "style",
        "page",
        "component",
        "graphic",
        "invalid_bbox",
        "wrong_text",
    ],
)
def test_non_capitalization_boundary_signals_prevent_join(kind):
    lines = ["The item was delivered to", "London the following day."]
    context = evidence(lines)
    if kind == "gap":
        context[1]["bbox"] = [80, 140, 500, 150]
    elif kind == "indent":
        context[1]["bbox"] = [150, 112, 500, 122]
    elif kind == "style":
        context[1]["bbox"] = [80, 112, 500, 130]
    elif kind == "page":
        context[1]["page"] = 2
    elif kind == "component":
        context[1]["component"] = "question_body"
    elif kind == "graphic":
        context[1]["order"] = 3
    elif kind == "invalid_bbox":
        context[1]["bbox"][0] = float("nan")
    elif kind == "wrong_text":
        context[1]["text"] = "An unrelated raw text block"
    assert normalize_text(
        "\n".join(lines), contextual_wraps=True, line_context=context
    ) == "\n".join(lines)


@pytest.mark.parametrize(
    "lines",
    [
        ["The previous paragraph is complete.", "London has a different policy."],
        ["The first paragraph has ended.", "", "A second paragraph starts here."],
        ["The following rules apply to", "1. London residents", "2. Bristol residents"],
        ["The following rules apply to", "• London residents", "• Bristol residents"],
        ["The roads are shown in", "Which route is the shortest?"],
        [
            "If the home team wins, the participant scores 1.0 point",
            "If the away team wins, the participant scores 1.5 points",
        ],
        ["Departure Destination Price", "London Paris £100", "Bristol Rome £200"],
    ],
)
def test_real_paragraph_lists_questions_and_data_stay_separate(lines):
    raw = "\n".join(lines)
    assert (
        normalize_text(
            raw, contextual_wraps=True, line_context=evidence([x for x in lines if x])
        )
        == raw
    )


def test_unverified_continuation_is_reported_not_silently_repaired():
    lines = ["The consignment was being sent to", "London on the following day."]
    warnings = []
    assert normalize_text(
        "\n".join(lines), contextual_wraps=True, on_unresolved=warnings.append
    ) == "\n".join(lines)
    assert len(warnings) == 1 and "geometry is unavailable" in warnings[0]


def test_joining_a_short_name_does_not_enable_a_following_paragraph_join():
    lines = ["The goods were sent to", "France.", "another paragraph remains distinct."]
    context = evidence(lines)
    context[2]["bbox"] = [80, 140, 500, 150]
    assert (
        normalize_text("\n".join(lines), contextual_wraps=True, line_context=context)
        == "The goods were sent to France.\nanother paragraph remains distinct."
    )


@pytest.fixture(scope="module")
def real_corpus():
    paths = sorted((ROOT / "data/clean/blackstone").glob("*.clean.json"))
    if not paths:
        pytest.skip("Local raw/clean questions unavailable")
    result = []
    for path in paths:
        old = json.loads(path.read_text(encoding="utf-8"))
        raw_path = Path(old["raw_reference"]["path"])
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        result.append((path, old, clean_dataset(raw, raw_path)))
    return result


@pytest.mark.parametrize(
    "year,number,expected",
    [
        (2019, 33, "into the Netherlands and Switzerland"),
        (2009, 31, "on Monday to Friday"),
        (2011, 27, "particularly in London"),
        (2012, 16, "Fiasco by Thomas E Ricks"),
        (2016, 12, "and Robert and Sheila"),
        (None, 18, "to Floyds customers"),
        (2018, 5, "from Germany"),
        (2020, 9, "Rhode Island University"),
        (2021, 31, "early January."),
        (2022, 49, "British Broadcasting Corporation (BBC)"),
        (2010, 31, "and Henry"),
        (2017, 33, "born in the UK"),
    ],
)
def test_real_names_and_analogous_issue_records(real_corpus, year, number, expected):
    q = next(
        q
        for _, _, d in real_corpus
        for q in d["questions"]
        if q["metadata"]["year"] == year and q["question_number"] == number
    )
    assert expected in " ".join(
        b["text"] for b in q["main_body"] if b["type"] == "text"
    )


def test_corpus_preserves_all_text_structure_trace_and_correct_controls(real_corpus):
    compact = lambda value: re.sub(r"\s+", " ", value or "").strip()

    def paragraphs(value):
        return {
            len(re.findall(r"\S+", value[: m.start()]))
            for m in re.finditer(r"\n\s*\n", value)
        }

    changed = 0
    for _, old, new in real_corpus:
        validate_clean(old)  # Previously written rule sets remain readable.
        for a, b in zip(old["questions"], new["questions"]):
            assert compact(a["question_text"]) == compact(b["question_text"])
            assert paragraphs(a["question_text"]) == paragraphs(b["question_text"])
            assert compact(a["main_question"]) == compact(b["main_question"])
            assert [
                compact(x["text"]) for x in a["main_body"] if x["type"] == "text"
            ] == [compact(x["text"]) for x in b["main_body"] if x["type"] == "text"]
            assert [
                paragraphs(x["text"]) for x in a["main_body"] if x["type"] == "text"
            ] == [paragraphs(x["text"]) for x in b["main_body"] if x["type"] == "text"]
            assert a["raw_record"] == b["raw_record"]
            assert a["raw_reference"] == b["raw_reference"]
            assert a["source_question_key"] == b["source_question_key"]
            assert a["raw_warnings"] == b["raw_warnings"]
            assert a["cleaning_issues"] == b["cleaning_issues"]
            options = deepcopy(a["options"])
            for option in options or []:
                for image in option.get("images") or []:
                    image.pop("clean_asset", None)
            assert options == b["options"]
            changed += (
                normalize_text(
                    b["raw_record"].get("question_text"), separate_blocks=True
                )
                != b["question_text"]
            )
            if (a["metadata"]["year"], a["question_number"]) in {
                (2011, 2),
                (2011, 37),
                (2019, 31),
                (2022, 26),
            }:
                assert a["main_body"] == b["main_body"]
    assert changed > 20  # Shared root cause, not a single-question patch.


def test_actual_stored_q33_html_and_legacy_upgrade(real_corpus, tmp_path):
    _, old, fresh = next(
        row for row in real_corpus if row[1]["document"].get("year") == 2019
    )
    raw_path = Path(old["raw_reference"]["path"])
    before = sha256(raw_path.read_bytes()).hexdigest()
    output = tmp_path / "2019.clean.json"
    legacy = deepcopy(old)
    legacy["cleaning"]["rules"].remove(
        "geometry_backed_capitalized_prose_wraps"
    ) if "geometry_backed_capitalized_prose_wraps" in legacy["cleaning"][
        "rules"
    ] else None
    for q in legacy["questions"]:
        q["question_text"] = normalize_text(
            q["raw_record"]["question_text"], separate_blocks=True
        )
    output.write_text(json.dumps(legacy), encoding="utf-8")
    write_clean(fresh, output, overwrite=True)
    result = inspect_question(
        [output], source="TSA Oxford 2019.pdf", question_number=33, year=2019
    )
    body = (
        render_html(result).split("<section id='main-body'>")[1].split("</section>")[0]
    )
    assert "into the Netherlands and Switzerland" in body
    assert "into the\nNetherlands" not in body
    assert sha256(raw_path.read_bytes()).hexdigest() == before
