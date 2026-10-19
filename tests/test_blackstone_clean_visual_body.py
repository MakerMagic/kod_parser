"""Visual text ownership and verified CID layout alignment, without PDFs."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_blackstone_cleaning import raw_case as make_raw_case

from processors.normalization.blackstone import clean_dataset, validate_clean
from processors.normalization.blackstone.backtest import (
    inspect_question,
    render_inspection,
)
from processors.normalization.blackstone.storage import write_clean
from processors.normalization.blackstone.structure import completion_prompt_span
from processors.normalization.blackstone.text import normalize_text


def encode(value):
    return "".join(f"(cid:{ord(c) - 29})" if c not in "\n" else c for c in value)


@pytest.fixture
def raw_case(tmp_path):
    return make_raw_case.__wrapped__(tmp_path)


def table_case(raw_case):
    path, data = raw_case
    q = data["questions"][0]
    text = "The rates are shown below.\n \nMen Women\n3 g or less 1 3\n \nWhich answer fits?\n"
    original = encode("12 " + text)
    options = q["raw"]["options_block"]
    q["raw"].update(
        question_block=original + options,
        extraction_notes=[
            "Structured text decoded from a verified shifted CID font; original CID tokens remain."
        ],
    )
    q["question_text"] = text
    asset = q["visual_assets"][0]
    asset["placement"] = {"component": "question_body"}
    blocks, offset = [], 0
    for index, line in enumerate(original.splitlines()):
        if index == 2:
            blocks.append(
                {
                    "block_id": "table",
                    "type": "visual",
                    "component": "question_body",
                    "asset_id": asset["image_id"],
                    "page": 3,
                    "bbox": asset["bbox"],
                }
            )
        inside = index in (2, 3)
        blocks.append(
            {
                "block_id": f"line_{index}",
                "type": "text",
                "component": "visual_label" if inside else "question_body",
                "text": line,
                "raw_span": {"start": offset, "end": offset + len(line)},
                "page": 3,
                "bbox": [110, 110 + (index - 2) * 20, 180, 122 + (index - 2) * 20]
                if inside
                else [50, 50 + index * 40, 500, 62 + index * 40],
                "asset_ids": [asset["image_id"]] if inside else [],
            }
        )
        offset += len(line) + 1
    for order, block in enumerate(blocks, 1):
        block["order"] = order
    q["layout_blocks"] = blocks
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, data


def body_text(q):
    return "\n".join(b["text"] for b in q["main_body"] if b["type"] == "text")


def test_verified_cid_table_ownership_preserves_prose_and_complete_accounting(raw_case):
    path, data = table_case(raw_case)
    before = deepcopy(data)
    payload = path.read_bytes()
    result = clean_dataset(data, path)
    q = result["questions"][0]
    assert [b["type"] for b in q["main_body"]] == ["text", "visual"]
    assert body_text(q) == "The rates are shown below."
    assert q["main_question"] == "Which answer fits?"
    assert [a["destination"] for a in q["content_accounting"]] == [
        "main_body",
        "visual",
        "visual",
        "main_question",
    ]
    assert not q["cleaning_issues"]
    assert "Men Women" in q["question_text"]  # Representation changes, not source text.
    assert q["raw_record"] == before["questions"][0]
    assert data == before and path.read_bytes() == payload
    validate_clean(result)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_verification",
        "wrong_span",
        "different_text",
        "same_count_different_text",
    ],
)
def test_no_count_only_or_unverified_cid_alignment(raw_case, fault):
    path, data = table_case(raw_case)
    q = data["questions"][0]
    if fault == "missing_verification":
        q["raw"]["extraction_notes"] = []
    elif fault == "wrong_span":
        q["layout_blocks"][0]["raw_span"]["end"] -= 1
    elif fault == "same_count_different_text":
        q["layout_blocks"] = [
            b
            for b in q["layout_blocks"]
            if b["type"] == "visual" or encode(" ") != b.get("text")
        ]
        q["question_text"] = q["question_text"].replace("The rates", "Other rates")
    else:
        q["question_text"] = q["question_text"].replace("The rates", "Other rates")
    cleaned = clean_dataset(data, path)["questions"][0]
    assert "layout_alignment_unresolved" in {
        i["code"] for i in cleaned["cleaning_issues"]
    }
    assert "Men Women" in body_text(cleaned)
    assert cleaned["raw_record"] == q


@pytest.mark.parametrize(
    "fault", ["unknown", "foreign_page", "outside_bounds", "missing_owner"]
)
def test_unsafe_visual_ownership_retains_text_and_review(raw_case, fault):
    path, data = table_case(raw_case)
    q = data["questions"][0]
    asset = q["visual_assets"][0]
    if fault == "unknown":
        asset.update(
            belongs_to="unknown",
            placement={"component": "unknown"},
            warnings=["visual_component_association_uncertain"],
        )
    elif fault == "foreign_page":
        asset["page"] = 4
    elif fault == "outside_bounds":
        asset["bbox"] = [300, 100, 400, 150]
    else:
        for b in q["layout_blocks"]:
            if b.get("component") == "visual_label":
                b["asset_ids"] = ["missing"]
    cleaned = clean_dataset(data, path)["questions"][0]
    assert "Men Women" in body_text(cleaned)
    assert "visual_text_ownership_unresolved" in {
        i["code"] for i in cleaned["cleaning_issues"]
    }
    assert cleaned["raw_warnings"] == q["warnings"]


def test_external_caption_warning_does_not_duplicate_known_internal_cells(raw_case):
    path, data = table_case(raw_case)
    q = data["questions"][0]
    warning = "visual_caption_boundary_uncertain:external_caption_preserved"
    q["visual_assets"][0]["warnings"] = [warning]
    q["warnings"].append(warning)
    cleaned = clean_dataset(data, path)["questions"][0]
    assert "Men Women" not in body_text(cleaned)
    assert warning in cleaned["raw_warnings"]
    assert cleaned["visual_assets"][0]["warnings"] == [warning]


@pytest.fixture(scope="module")
def corpus():
    root = Path(__file__).resolve().parents[1] / "data/raw/blackstone"
    paths = sorted(root.glob("*.raw.json"))
    if not paths:
        pytest.skip("Stored local raw outputs unavailable")
    return [
        (p, clean_dataset(json.loads(p.read_text(encoding="utf-8")), p)) for p in paths
    ]


@pytest.mark.parametrize(
    "year,number",
    [
        (2012, 19),
        (2012, 38),
        (2012, 25),
        (2013, 20),
        (2013, 38),
        (2014, 19),
        (2014, 25),
        (2014, 37),
        (2014, 49),
    ],
)
def test_targets_and_analogues_use_stored_visual_ownership(corpus, year, number):
    raw, data = next((p, d) for p, d in corpus if d["document"].get("year") == year)
    q = data["questions"][number - 1]
    assert not q["cleaning_issues"]
    assert q["main_question"]
    assert all(b["source_blocks"] for b in q["main_body"])
    visual = {a["image_id"]: a for a in q["visual_assets"]}
    for entry in q["content_accounting"]:
        if entry["destination"] == "visual":
            assert entry["asset_ids"] and all(a in visual for a in entry["asset_ids"])
    if number == 19 and year == 2012:
        assert "The table below shows" in body_text(q) and "2004." in body_text(q)
        assert "Men Women" not in body_text(q) and "3 g or less" not in body_text(q)
        assert (
            len([a for a in q["content_accounting"] if a["destination"] == "visual"])
            == 8
        )
    if number == 38 and year == 2012:
        assert [b["type"] for b in q["main_body"]] == ["text", "visual"]
        assert q["raw_warnings"] == ["graphics_present:option_association_not_resolved"]
        assert all(
            a["belongs_to"] == "question" and not a["warnings"]
            for a in q["visual_assets"]
        )
    assert q["raw_reference"]["sha256"] == sha256(raw.read_bytes()).hexdigest()


def test_ambiguous_actual_body_visuals_remain_flagged(corpus):
    root = Path(__file__).resolve().parents[1]
    for year, number in [(2018, 20), (2019, 44), (2016, 32)]:
        raw, current = next(
            (p, d) for p, d in corpus if d["document"].get("year") == year
        )
        archived = (
            root
            / "inspections_categorization/representation_refinement/original_inputs"
            / raw.name
        )
        if not archived.exists():
            pytest.skip("Optional original ambiguous RAW snapshots unavailable")
        original = json.loads(archived.read_text(encoding="utf-8"))
        # The cleaner must still refuse the unchanged ambiguous RAW input.
        # The live records were repaired upstream, not by relaxing CLEAN rules.
        q = clean_dataset(original, raw)["questions"][number - 1]
        assert "visual_placement_unresolved" in {
            i["code"] for i in q["cleaning_issues"]
        }
        assert any(
            "association_uncertain" in w or "shared_geometry" in w
            for w in q["raw_warnings"]
        )
        assert not current["questions"][number - 1]["cleaning_issues"]
    # A genuinely unresolved live control remains reviewable as well.
    _, specimen = next((p, d) for p, d in corpus if "specimen" in p.name)
    assert "visual_placement_unresolved" in {
        i["code"] for i in specimen["questions"][24]["cleaning_issues"]
    }


def test_all_36_alignment_cases_and_already_correct_controls(corpus):
    root = Path(__file__).resolve().parents[1]
    count = 0
    for raw, data in corpus:
        baseline = (
            root
            / "inspections_clean/visual_body_baseline_20261014"
            / (raw.name.removesuffix(".raw.json") + ".clean.json")
        )
        if not baseline.exists():
            continue
        old = json.loads(baseline.read_text(encoding="utf-8"))
        for q, b in zip(data["questions"], old["questions"]):
            if q["raw_record"] != b["raw_record"]:
                # This frozen cleaning baseline predates subsequent RAW visual
                # grouping fixes. Compare the cleaner on identical old inputs;
                # current RAW-to-clean grouping has its own regression tests.
                original = json.loads(raw.read_text(encoding="utf-8"))
                original["questions"] = [deepcopy(b["raw_record"])]
                q = clean_dataset(original, raw)["questions"][0]
            assert (
                q["raw_record"] == b["raw_record"]
                and q["raw_warnings"] == b["raw_warnings"]
            )
            # The frozen visual-only baseline predates the prose-wrap fix.
            # Content and structure remain exact; known PDF wraps may change.
            assert " ".join(q["question_text"].split()) == " ".join(
                normalize_text(
                    b["question_text"],
                    recover_modal_joins=True,
                    recover_auxiliary_joins=True,
                ).split()
            )
            completion = completion_prompt_span(
                {**q["raw_record"], "question_text": q["question_text"]}
            )
            recovered_completion = b["main_question"] is None and completion is not None
            if recovered_completion:
                assert q["main_question"] == q["question_text"][slice(*completion)]
                assert q["question_text"].rstrip().endswith(q["main_question"])
                assert " ".join(
                    (body_text(q) + " " + q["main_question"]).split()
                ) == " ".join(
                    normalize_text(
                        body_text(b),
                        recover_modal_joins=True,
                        recover_auxiliary_joins=True,
                    ).split()
                )
            elif (q["metadata"].get("year"), q["question_number"]) in {
                (2010, 32),
                (2012, 16),
            }:
                # Explicitly reviewed colon prompts were unresolved in this old
                # visual-only baseline; all their source text remains accounted.
                assert b["main_question"] is None
                assert q["main_question"] and q["main_question"].endswith(":")
                assert q["question_text"].rstrip().endswith(q["main_question"])
            else:
                assert " ".join((q["main_question"] or "").split()) == " ".join(
                    normalize_text(
                        b["main_question"] or "",
                        recover_modal_joins=True,
                        recover_auxiliary_joins=True,
                    ).split()
                )
            assert [(o["label"], o["text"]) for o in q["options"]] == [
                (o["label"], o["text"]) for o in b["options"]
            ]
            assert q["visual_assets"] == b["visual_assets"]
            if any(
                i["code"] == "layout_alignment_unresolved" for i in b["cleaning_issues"]
            ):
                count += 1
                assert not any(
                    i["code"] == "layout_alignment_unresolved"
                    for i in q["cleaning_issues"]
                )
            elif not b["cleaning_issues"]:
                # Exact alignment can add previously missing source-block
                # evidence; already-correct displayed content/order must not change.
                assert recovered_completion or [
                    {
                        k: " ".join(v.split()) if k == "text" else v
                        for k, v in block.items()
                        if k != "source_blocks"
                    }
                    for block in q["main_body"]
                ] == [
                    {
                        k: " ".join(v.split()) if k == "text" else v
                        for k, v in block.items()
                        if k != "source_blocks"
                    }
                    for block in b["main_body"]
                ]
                assert not q["cleaning_issues"]
    if count:
        assert count == 36


def test_target_html_text_json_inspections_are_read_only(corpus, tmp_path):
    raw, data = next((p, d) for p, d in corpus if d["document"].get("year") == 2012)
    output = write_clean(data, tmp_path / "2012.clean.json")
    before = raw.read_bytes(), output.read_bytes()
    for number in [19, 38]:
        result = inspect_question(
            [output], source="TSA Oxford 2012.pdf", year=2012, question_number=number
        )
        html = render_inspection(result, "html")
        body = html.split("id='main-body'")[1].split("</section>")[0]
        assert (
            "data:image/png;base64," in body
            and "layout_alignment_unresolved" not in html
        )
        if number == 19:
            assert "3 g or less" not in body and "The table below shows" in body
        assert render_inspection(result, "text") and render_inspection(result, "json")
    assert (raw.read_bytes(), output.read_bytes()) == before
