"""Offline source-boundary, acquisition-cache and BMAT-only matching gates."""

import json
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace

import pytest

from acquisition.bmat_worked_solutions import INDEX, acquire, question_links
from parsers.bmat_worked_solutions.parser import parse_page
from processors.matching.bmat import core


def html(body, title="2017 Section 1 Question 12"):
    return f"<nav>Unrelated navigation</nav><h1 class='entry-title'>{title}</h1><div class='entry-content'>{body}</div><footer>Footer</footer>"


def page(tmp_path, body, **kw):
    path = tmp_path / "source.html"
    path.write_text(html(body), encoding="utf-8")
    return parse_page(
        path,
        year=2017,
        question_number=12,
        source_url="https://example.test/solution",
        **kw,
    )


def test_structured_explanation_order_and_widget_cutoff(tmp_path):
    result = page(
        tmp_path,
        "<p><span>12)</span> <b>c</b></p><p>First premise.</p><ul><li>One</li><li>Two<br>continued</li></ul><p>Conclusion.</p><div class='sharedaddy'><h3>Share this:</h3>BUTTONS</div><p>Related post</p>",
    )
    assert result["status"] == "parsed"
    assert result["correct_answer"] == "C"
    blocks = result["explanation"]["blocks"]
    assert [b["type"] for b in blocks] == ["paragraph", "list", "paragraph"]
    assert blocks[1]["items"][1]["text"] == "Two\ncontinued"
    assert "BUTTONS" not in result["explanation"]["raw_text"]
    assert "Related post" not in result["explanation"]["raw_text"]
    assert (
        result["source_document"]["sha256"]
        == sha256((tmp_path / "source.html").read_bytes()).hexdigest()
    )


def test_header_and_explanation_share_paragraph_without_losing_text(tmp_path):
    result = page(
        tmp_path,
        "<p>12) C<br>Premise.<br>Result.</p><h3>Share this...</h3><p>Not explanation</p>",
    )
    assert result["status"] == "parsed"
    assert result["explanation"]["blocks"][0]["text"] == "Premise.\nResult."
    assert "Not explanation" not in result["explanation"]["raw_text"]


@pytest.mark.parametrize(
    "header,warning",
    [
        ("11) C", "header_question_number_mismatch"),
        ("12) A & C", "malformed_answer_header"),
        ("12) 109", "malformed_answer_header"),
        ("The correct answer is C", "malformed_answer_header"),
    ],
)
def test_unsafe_header_never_inferred_from_prose(tmp_path, header, warning):
    result = page(tmp_path, f"<p>{header}</p><p>Option C is obviously correct.</p>")
    assert result["status"] == "unresolved" and warning in result["warnings"]
    assert result["correct_answer"] is None


def test_section_and_title_checks(tmp_path):
    assert (
        "non_section_1_source"
        in page(tmp_path, "<p>12) C</p>", section="section_2")["warnings"]
    )
    path = tmp_path / "other.html"
    path.write_text(
        html("<p>12) C</p>", "2018 Section 1 Question 12"), encoding="utf-8"
    )
    assert (
        "source_title_identity_mismatch"
        in parse_page(path, year=2017, question_number=12)["warnings"]
    )


def test_image_only_source_is_preserved_not_given_an_invented_answer(tmp_path):
    result = page(
        tmp_path,
        "<figure><img src='worked.png'></figure><div class='sharedaddy'>Share</div>",
    )
    assert result["status"] == "unresolved"
    assert (
        result["raw"]["source_blocks"][0]["source_url"]
        == "https://example.test/worked.png"
    )
    assert result["correct_answer"] is None


def test_split_anchor_and_empty_adjacent_link_are_detected():
    body = "<ul><li><a href='/a'>Question</a><a href='/a'> 7</a><a href='/b'></a></li></ul>"
    assert question_links(html(body), "https://example.test") == [
        (7, "https://example.test/a"),
        (7, "https://example.test/b"),
    ]


def test_acquisition_is_section_one_only_and_reuses_verified_cache(tmp_path):
    pages = {
        INDEX: html("<a href='/year'>2017 Worked solutions</a>"),
        "https://bmatworkedsolutions.wordpress.com/year": html(
            "<a href='/one'>Section 1</a><a href='/two'>Section 2</a>"
        ),
        "https://bmatworkedsolutions.wordpress.com/one": html(
            "<a href='/q'>Question 12</a>"
        ),
        "https://bmatworkedsolutions.wordpress.com/q": html(
            "<p>12) C</p><p>Reason</p>"
        ),
    }
    calls = []

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url, **kw):
            calls.append(url)
            return SimpleNamespace(
                content=pages[url].encode(),
                headers={"Content-Type": "text/html"},
                url=url,
                raise_for_status=lambda: None,
            )

    result = acquire(tmp_path, years=[2017], workers=1, client_factory=Client)
    assert len(result["questions"]) == 1 and not result["issues"]
    assert not any("/two" in u for u in calls)
    count = len(calls)
    acquire(tmp_path, years=[2017], workers=1, client_factory=Client)
    assert len(calls) == count
    assert (
        acquire(tmp_path, years=[2017, 2018], workers=1, client_factory=Client)[
            "years"
        ][1]["status"]
        != "acquired"
    )


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    question = {
        "question_number": 12,
        "question_id": "stable_bmat_2017_12",
        "metadata": {"source": "bmat", "year": 2017, "section": "section_1"},
        "source_question_key": {
            "source": "bmat",
            "year": 2017,
            "section": "section_1",
            "question_number": 12,
        },
        "bmat_filter": {"skip_from_pipeline": False},
        "cleaning_issues": [],
        "raw_record": {"parsing_issues": []},
        "pipeline_eligible": True,
        "pipeline_status": "clean_ready",
        "main_question": "Which conclusion follows?",
        "options": [{"label": x, "text": x} for x in "ABCDE"],
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    parsed = page(
        tmp_path, "<p>12) C</p><p>The premises imply the conclusion in C.</p>"
    )
    data = {
        "stage": "answer_raw",
        "source_family": "bmat",
        "source_document": core.file_reference(manifest),
        "answers": [parsed],
        "unresolved_sources": [],
        "issues": [],
    }
    answer_path = tmp_path / "answer.json"
    clean_path = tmp_path / "clean.json"
    clean_path.write_text("{}", encoding="utf-8")
    clean = {"document": {"source": "bmat"}, "questions": [question]}
    monkeypatch.setattr(core, "files", lambda _: [clean_path])
    monkeypatch.setattr(core, "load", lambda _: clean)

    def build(previous=None):
        answer_path.write_text(json.dumps(data), encoding="utf-8")
        return core.build([clean_path], answer_path, previous=previous)

    return question, data, build, clean


def test_only_issue_free_bmat_target_is_attached_with_provenance(candidate):
    q, source, build, _ = candidate
    result = build()
    r = result["records"][0]
    assert r["status"] == "matched" and r["correct_answer"] == "C"
    assert r["question"] == q
    assert r["final_explanation"]["status"] == "available"
    assert r["final_explanation"]["explanation_by_ai"] is False
    assert r["answer"]["source_document"] == source["answers"][0]["source_document"]
    assert build(previous=result)["records"] == result["records"]


@pytest.mark.parametrize("kind", ["raw", "clean", "skip", "incomplete"])
def test_upstream_and_skipped_targets_are_never_force_matched(candidate, kind):
    q, _, build, _ = candidate
    if kind == "raw":
        q["raw_record"]["parsing_issues"].append({"code": "bad_raw"})
    elif kind == "clean":
        q["cleaning_issues"].append({"code": "bad_clean"})
    elif kind == "skip":
        q["bmat_filter"]["skip_from_pipeline"] = True
    else:
        q["main_question"] = None
    r = build()["records"][0]
    assert r["status"] != "matched" and r["answer"] is None
    assert r["answer_candidates"] and not r["final_explanation"]["blocks"]


def test_tsa_target_and_wrong_year_are_not_bmat_matches(candidate):
    _q, data, build, clean = candidate
    clean["document"]["source"] = "blackstone"
    with pytest.raises(ValueError, match="TSA/non-BMAT"):
        build()
    clean["document"]["source"] = "bmat"
    data["answers"][0]["year"] = 2018
    statuses = {r["status"] for r in build()["records"]}
    assert statuses == {"source_missing", "target_missing"}


def test_duplicate_source_and_existing_answer_conflict_remain_explicit(candidate):
    _q, data, build, _ = candidate
    accepted = build()
    data["answers"].append(deepcopy(data["answers"][0]))
    assert build()["records"][0]["status"] == "duplicate_source"
    data["answers"].pop()
    data["answers"][0]["correct_answer"] = "B"
    record = build(previous=accepted)["records"][0]
    assert record["status"] == "answer_explanation_conflict"
    assert record["correct_answer"] == "C"
    assert record["final_explanation"] == accepted["records"][0]["final_explanation"]
    assert record["issues"][0]["worked_answer"] == "B"


def test_unresolved_source_and_out_of_range_answer_are_not_accepted(candidate):
    _, data, build, _ = candidate
    data["answers"][0]["correct_answer"] = "H"
    assert build()["records"][0]["status"] == "answer_incompatible"
    data["unresolved_sources"] = data.pop("answers")
    data["answers"] = []
    data["unresolved_sources"][0]["status"] = "unresolved"
    result = build()
    assert result["records"][0]["status"] == "source_unresolved"
    assert result["summary"]["unique_parsed_question_identities"] == 0


def test_backtest_exposes_only_accepted_explanation_and_explicit_deferred_status(
    candidate, monkeypatch
):
    from processors.matching.bmat import backtest

    q, _, build, _ = candidate
    monkeypatch.setattr(
        backtest,
        "question_html",
        lambda *args: (
            "<body><main><h2>Main Body</h2><h2>Main Question</h2><h2>Main Answers</h2></main></body>"
        ),
    )
    accepted = build()["records"][0]
    shown = backtest.inspect(json.loads(json.dumps(accepted)))
    assert (
        "Main Explanation" in shown
        and "Final Explanation" in shown
        and "premises imply" in shown
    )
    assert "Correct Answer" in shown and "Explanation Source" in shown
    assert shown.count("The premises imply the conclusion in C.") == 1
    assert "Explanation by AI: False" in shown and "BMAT Matching Identity" in shown
    q["raw_record"]["parsing_issues"] = [{"code": "genuine_raw_defect"}]
    deferred = build()["records"][0]
    shown = backtest.inspect(deferred)
    assert "deferred_upstream_issue" in shown and "not a successful match" in shown
    assert "No accepted explanation attached" in shown


def test_lists_preserve_math_and_paragraph_boundaries(tmp_path):
    result = page(
        tmp_path,
        "<p>12) C</p><p>Reason:</p><ol><li><p>x<sup>2</sup></p><p>then y<sub>1</sub></p></li></ol><p>Conclusion.</p>",
    )
    item = result["explanation"]["blocks"][1]["items"][0]["text"]
    assert "x^{2}" in item and "y_{1}" in item and "\n\n" in item


@pytest.mark.parametrize("number,expected", [(12, "parsed"), (11, "unresolved")])
def test_source_image_header_requires_number_hash_and_keeps_full_visual(
    tmp_path, number, expected
):
    from PIL import Image

    asset = tmp_path / "worked.png"
    Image.new("RGB", (200, 150), "white").save(asset)
    digest = sha256(asset.read_bytes()).hexdigest()
    source = {
        "source_url": "https://example.test/worked.png",
        "local_path": str(asset),
        "sha256": digest,
        "status": "acquired",
    }
    result = page(
        tmp_path,
        "<figure><img src='worked.png'></figure><div class='sharedaddy'>Share</div>",
        assets=[source],
        image_header=lambda _: {
            "lines": [f"{number}) C"],
            "source_sha256": digest,
            "bbox": [0, 0, 100, 40],
        },
    )
    assert result["status"] == expected
    if expected == "parsed":
        assert result["answer_extraction"]["method"] == "source_image_header_ocr"
        assert result["explanation"]["blocks"][0]["type"] == "visual"
        assert result["explanation"]["visual_assets"][0]["sha256"] == digest
        assert sha256(asset.read_bytes()).hexdigest() == digest


def test_source_header_region_stops_at_first_ink_line_not_prose():
    from PIL import Image, ImageDraw

    from parsers.bmat_worked_solutions.image_header import first_line

    image = Image.new("RGB", (300, 200), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((30, 20, 80, 35), fill="black")
    draw.rectangle((10, 80, 260, 95), fill="black")
    bbox = first_line(image)
    assert bbox[1] < 20 and 35 < bbox[3] < 80


def supplied(tmp_path, body, answer="C"):
    from parsers.bmat_supplied_explanations import parse

    path = tmp_path / "provided.txt"
    path.write_text(f"2017:\nQuestion 12 — Answer {answer}\n{body}\n", encoding="utf-8")
    output = tmp_path / "provided.answers.json"
    output.write_text(json.dumps(parse(path)), encoding="utf-8")
    return output


def test_supplied_parser_preserves_text_and_does_not_invent_unheaded_question(tmp_path):
    from parsers.bmat_supplied_explanations import parse

    source = tmp_path / "source.txt"
    source.write_text(
        "2011:\n16) D\nA – Wrong\nA reason.\n1 – Wrong\nUnheaded human-rights explanation.\n2020:\nQuestion 1 — Answer D\nA premise.\n\nA result.\nReview required: uncertain source\n",
        encoding="utf-8",
    )
    data = parse(source)
    assert [(a["year"], a["question_number"]) for a in data["answers"]] == [
        (2011, 16),
        (2020, 1),
    ]
    assert (
        "unheaded_numbered_explanation_after_lettered_choices"
        in data["answers"][0]["warnings"]
    )
    assert "Unheaded human-rights" in data["answers"][0]["raw"]["content_text"]
    assert (
        data["answers"][1]["explanation"]["main_explanation"]
        == "A premise.\n\nA result."
    )
    assert data["answers"][1]["review_notes"] and all(
        not a["explanation"]["visual_assets"] for a in data["answers"]
    )


def test_supplied_variant_does_not_overwrite_existing_explanation(candidate, tmp_path):
    from processors.matching.bmat.supplied import apply

    _, _, build, _ = candidate
    data = build()
    before = deepcopy(data["records"][0]["final_explanation"])
    apply(data, supplied(tmp_path, "A user-supplied paraphrase of the reasoning."))
    assert data["records"][0]["final_explanation"] == before
    assert data["supplied_import_summary"]["statuses"] == {"existing_preserved": 1}


def test_supplied_missing_explanation_attaches_and_roundtrips_without_images(
    candidate, tmp_path
):
    from processors.matching.bmat.supplied import apply

    _, source, build, _ = candidate
    source["answers"] = []
    path = supplied(tmp_path, "The supplied premises establish the conclusion in C.")
    first = apply(build(), path)
    r = first["records"][0]
    assert r["status"] == "matched" and r["correct_answer"] == "C"
    assert r["answer"]["source_document"]["origin"] == "human_user_supplied_text"
    assert not r["answer"]["explanation"]["visual_assets"]
    assert apply(build(previous=first), path, previous=first) == first


def test_changed_supplied_explanation_is_a_conflict_not_silent_replacement(
    candidate, tmp_path
):
    from processors.matching.bmat.supplied import apply

    _, source, build, _ = candidate
    source["answers"] = []
    first = apply(build(), supplied(tmp_path, "The original provided reasoning."))
    second = apply(
        build(previous=first),
        supplied(tmp_path, "A changed supplied explanation."),
        previous=first,
    )
    assert second["records"][0]["status"] == "explanation_review_required"
    assert (
        second["records"][0]["final_explanation"]
        == first["records"][0]["final_explanation"]
    )
    assert (
        second["records"][0]["supplied_imports"][0]["import_status"]
        == "explanation_conflict"
    )


@pytest.mark.parametrize("kind", ["skip", "raw", "conflict", "review", "duplicate"])
def test_supplied_source_never_bypasses_exclusions_conflicts_or_review(
    candidate, tmp_path, kind
):
    from processors.matching.bmat.supplied import apply

    q, source, build, _ = candidate
    if kind == "skip":
        q["bmat_filter"]["skip_from_pipeline"] = True
    if kind == "raw":
        q["raw_record"]["parsing_issues"] = [{"code": "upstream_defect"}]
    if kind in {"review", "duplicate"}:
        source["answers"] = []
    body = "A supplied explanation."
    if kind == "review":
        body += "\nReview required: contradictory source answer"
    path = supplied(tmp_path, body, "B" if kind == "conflict" else "C")
    if kind == "duplicate":
        data = json.loads(path.read_text(encoding="utf-8"))
        data["answers"].append(deepcopy(data["answers"][0]))
        path.write_text(json.dumps(data), encoding="utf-8")
    result = apply(build(), path)
    assert result["records"][0]["status"] != "matched"
    if kind == "conflict":
        assert result["records"][0]["correct_answer"] == "C"
    else:
        assert not result["records"][0]["final_explanation"]["blocks"]
