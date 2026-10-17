"""Ordered reading view, source preservation, ambiguity and real-format controls."""

import json
import re
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_matching import match_case as shared_matching_case

from processors.matching.backtest import (
    inspect_question,
    render_html,
    render_inspection,
)
from processors.matching.core import match_records
from processors.matching.explanation import build_final_explanation
from processors.matching.report import write_report


def paragraph(text, order=None, page=None, start=0):
    result = {"type": "paragraph", "role": "main", "text": text, "line_refs": []}
    if order is not None:
        result["order"] = order
    if page is not None:
        result["line_refs"] = [{"page": page, "start": start, "end": start + 5}]
    return result


def answer(blocks, warnings=None):
    paragraphs = [
        b for b in blocks if b["type"] == "paragraph" and b.get("role") == "main"
    ]
    lists = [b for b in blocks if b["type"] == "list"]
    return {
        "warnings": warnings or [],
        "explanation": {
            "blocks": blocks,
            "paragraphs": paragraphs,
            "main_explanation": "\n\n".join(b["text"] for b in paragraphs),
            "bulleted_blocks": lists,
            "other_lists": [b for b in lists if b.get("role") == "other"],
            "choice_analysis": [],
        },
    }


def test_interleaved_components_and_transitions_are_rendered_once():
    transition = paragraph("Why the alternatives fail:", 4)
    transition["role"] = "choice_transition"
    wrong = {
        "type": "list",
        "role": "incorrect_choices",
        "order": 5,
        "transition": transition["text"],
        "items": [
            {"label": "B", "text": "B — Wrong because\nit conflicts.", "line_refs": []}
        ],
    }
    blocks = [
        paragraph("Reasoning.", 1),
        {
            "type": "list",
            "role": "other",
            "items": [{"text": "An example"}],
            "order": 2,
        },
        paragraph("After the example.", 3),
        transition,
        wrong,
        paragraph("Conclusion.", 6),
    ]
    original = answer(blocks)
    original["explanation"]["choice_analysis"] = [
        {
            "label": "B",
            "text": "Wrong because\nit conflicts.",
            "line_refs": [],
            "list_order": 5,
        }
    ]
    before = deepcopy(original)
    final = build_final_explanation(
        original, {"path": "answers.json", "json_pointer": "/answers/4"}
    )
    assert final["status"] == "available"
    assert [
        {k: v for k, v in b.items() if k != "source_pointer"} for b in final["blocks"]
    ] == blocks
    assert final["blocks"][4]["items"][0]["label"] == "B"
    assert final["blocks"][4]["items"][0]["text"].endswith("\nit conflicts.")
    assert not final["unplaced_components"]
    assert original == before
    final["blocks"][0]["text"] = "mutated copy"
    assert original == before


def test_exact_aliases_not_legitimate_repeated_source_content_are_deduplicated():
    first, repeated = paragraph("Therefore.", 1, 1), paragraph("Therefore.", 2, 2)
    original = answer([first, deepcopy(first), repeated])
    final = build_final_explanation(original)
    assert final["status"] == "available"
    assert (
        len(final["blocks"]) == 2
    )  # Same words on different pages are not duplicates.
    assert len(final["deduplicated_blocks"]) == 1


def test_explicit_order_precedes_component_semantics_and_array_order():
    original = answer(
        [
            paragraph("Conclusion", 3, 3),
            paragraph("First", 1, 1),
            paragraph("Middle", 2, 2),
        ]
    )
    final = build_final_explanation(original)
    assert [b["text"] for b in final["blocks"]] == ["First", "Middle", "Conclusion"]


@pytest.mark.parametrize("canonical", [True, False])
def test_identical_text_without_provenance_is_not_silently_deleted(canonical):
    original = answer([paragraph("Repeated"), paragraph("Repeated")])
    if not canonical:
        original["explanation"]["blocks"] = []
    final = build_final_explanation(original)
    assert final["status"] == "uncertain"
    assert len(final["unplaced_components"]) == 2
    assert not final["deduplicated_blocks"]


def test_fallback_uses_source_spans_not_component_array_order():
    original = answer([])
    original["explanation"].update(
        {
            "paragraphs": [paragraph("Before", page=1), paragraph("After", page=2)],
            "main_explanation": "Before\n\nAfter",
            "bulleted_blocks": [
                {
                    "type": "list",
                    "role": "other",
                    "items": [
                        {
                            "text": "middle",
                            "line_refs": [{"page": 1, "start": 10, "end": 15}],
                        }
                    ],
                }
            ],
        }
    )
    final = build_final_explanation(original)
    assert final["status"] == "available"
    assert final["ordering"] == "source_line_order"
    assert [b["type"] for b in final["blocks"]] == ["paragraph", "list", "paragraph"]


@pytest.mark.parametrize("mode", ["no_order", "overlap", "contradictory_order"])
def test_ambiguous_source_order_never_fabricates_a_combined_flow(mode):
    blocks = [paragraph("First"), paragraph("Second")]
    if mode == "overlap":
        blocks = [paragraph("First", page=1), paragraph("Second", page=1)]
    elif mode == "contradictory_order":
        blocks = [paragraph("First", 1, 2), paragraph("Second", 2, 1)]
    final = build_final_explanation(answer(blocks))
    assert final["status"] == "uncertain"
    assert not final["blocks"]
    assert [c["value"]["text"] for c in final["unplaced_components"]] == [
        "First",
        "Second",
    ]
    assert "final_explanation_order_uncertain" in {i["code"] for i in final["issues"]}


def test_missing_secondary_content_is_retained_and_reported_not_appended():
    original = answer([paragraph("Main", 1)])
    original["explanation"]["other_lists"] = [
        {"type": "list", "items": [{"text": "Extra"}]}
    ]
    final = build_final_explanation(original)
    assert final["status"] == "uncertain"
    assert len(final["blocks"]) == 1
    assert final["unplaced_components"][0]["value"]["items"][0]["text"] == "Extra"


def test_conflicting_main_projection_is_preserved_without_duplicate_paragraphs():
    original = answer([paragraph("Main", 1)])
    original["explanation"]["main_explanation"] = "Main plus unplaced content"
    final = build_final_explanation(original)
    assert final["status"] == "uncertain"
    assert [b["text"] for b in final["blocks"]] == ["Main"]
    assert final["unplaced_components"][0]["value"] == "Main plus unplaced content"


def test_missing_choice_mapping_is_not_silently_lost_or_relabeled():
    original = answer([paragraph("Main", 1)])
    original["explanation"]["choice_analysis"] = [
        {"label": "C", "text": "Unplaced reason", "list_order": 4}
    ]
    final = build_final_explanation(original)
    assert final["status"] == "uncertain"
    assert final["unplaced_components"][0]["value"]["label"] == "C"


def test_transition_metadata_is_used_only_when_not_already_in_source_paragraphs():
    original = answer(
        [
            paragraph("Reason", 1),
            {
                "type": "list",
                "role": "incorrect_choices_unmapped",
                "order": 2,
                "transition": "The other choices fail:",
                "items": [{"text": "First reason"}, {"text": "Second reason"}],
            },
        ]
    )
    final = build_final_explanation(original)
    assert [b["type"] for b in final["blocks"]] == ["paragraph", "paragraph", "list"]
    assert final["blocks"][1]["source_pointer"].endswith("/transition")
    assert all("label" not in i for i in final["blocks"][2]["items"])


def test_conflicting_transition_metadata_does_not_duplicate_or_move_source_text():
    original = answer(
        [
            {
                "type": "list",
                "role": "incorrect_choices",
                "order": 1,
                "items": [{"label": "B", "text": "B — Reason"}],
                "transition": "A later paragraph",
            },
            paragraph("A later paragraph", 2),
        ]
    )
    final = build_final_explanation(original)
    assert final["status"] == "uncertain"
    assert [b["type"] for b in final["blocks"]] == ["list", "paragraph"]
    assert final["issues"][0]["code"] == "final_explanation_order_uncertain"


def test_verified_marker_artifact_only_is_omitted_unknown_symbols_stay():
    artifact = paragraph("♦", 2)
    artifact["role"] = "list_marker_artifact"
    original = answer(
        [paragraph("Lead-in", 1), artifact, paragraph("© meaningful content", 3)]
    )
    final = build_final_explanation(original)
    assert [b["text"] for b in final["blocks"]] == ["Lead-in", "© meaningful content"]
    assert final["omitted_artifacts"][0]["value"] == artifact


def test_visual_order_and_missing_asset_reference():
    original = answer(
        [
            paragraph("Before", 1),
            {"type": "visual", "asset_index": 1, "order": 2},
            paragraph("After", 3),
        ]
    )
    final = build_final_explanation(original)
    assert final["status"] == "uncertain"
    assert final["issues"][0]["code"] == "final_explanation_visual_unresolved"
    original["explanation"]["visual_assets"] = [{"asset_index": 1, "path": "table.png"}]
    final = build_final_explanation(original)
    assert final["status"] == "available"
    assert [b["type"] for b in final["blocks"]] == ["paragraph", "visual", "paragraph"]
    original["explanation"]["visual_assets"].append(
        {"asset_index": 2, "path": "unplaced.png"}
    )
    assert build_final_explanation(original)["status"] == "uncertain"


def test_unavailable_answer_only_and_single_component():
    assert build_final_explanation(None)["reason"] == "no_unique_answer_selected"
    original = answer([])
    original["explanation"]["availability"] = "not_supplied_by_source_format"
    assert (
        build_final_explanation(original)["reason"] == "not_supplied_by_source_format"
    )
    original = answer([])
    original["explanation"]["main_explanation"] = "Only main.\n\nSecond paragraph."
    final = build_final_explanation(original)
    assert final["status"] == "available"
    assert final["blocks"][0]["text"] == original["explanation"]["main_explanation"]
    original["warnings"] = ["source_content_uncertain"]
    assert build_final_explanation(original)["status"] == "uncertain"


@pytest.fixture
def prepared_case(tmp_path):
    return shared_matching_case.__wrapped__(tmp_path)


def test_matching_stores_derived_view_and_reports_uncertain_order(
    prepared_case, tmp_path
):
    clean, path, source = prepared_case
    original = source["answers"][0]
    original["explanation"] = answer([paragraph("First"), paragraph("Second")])[
        "explanation"
    ]
    path.write_text(json.dumps(source), encoding="utf-8")
    data = match_records([clean], [path], years={2008})
    r = data["records"][0]
    assert (
        r["status"] == "matched"
    )  # Explanation uncertainty is not a false key conflict.
    assert r["answer"] == original
    assert r["final_explanation"]["status"] == "uncertain"
    assert r["final_explanation"]["source_reference"] == r["answer_reference"]
    report = tmp_path / "issues.md"
    write_report(data, report)
    assert "## Final Explanation Order Uncertain (1 records)" in report.read_text()
    assert "First" in render_html({"record": r, "live_inspection_issues": []})


def test_old_matched_json_gets_an_in_memory_view_only(prepared_case, tmp_path):
    data = match_records([prepared_case[0]], [prepared_case[1]], years={2008})
    data["records"][0].pop("final_explanation")
    path = tmp_path / "old.matched.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    digest = sha256(path.read_bytes()).hexdigest()
    result = inspect_question(path, year=2008, question_number=12)
    assert result["record"]["final_explanation"]["status"] == "available"
    assert result["record"]["answer"] == data["records"][0]["answer"]
    assert "<h2>Final Explanation</h2>" in render_html(result)
    assert sha256(path.read_bytes()).hexdigest() == digest


@pytest.fixture(scope="module")
def real_datasets():
    paths = sorted(Path("data/merged/blackstone").glob("*.matched.json"))
    if not paths:
        pytest.skip("Local matched validation data unavailable")
    return [(p, json.loads(p.read_text(encoding="utf-8"))) for p in paths]


def test_all_local_records_preserve_every_original_block_and_projection(real_datasets):
    statuses = Counter()
    official_2020 = Counter()
    for _, data in real_datasets:
        for r in data["records"]:
            a = r.get("answer")
            before = deepcopy(a)
            final = build_final_explanation(a, r.get("answer_reference"))
            if r["identity"]["year"] == 2020:
                official_2020[final["status"]] += 1
            else:
                statuses[final["status"]] += 1
            assert a == before
            assert not final["issues"], r["identity"]
            assert not final["unplaced_components"], r["identity"]
            expected = [
                b
                for b in a["explanation"]["blocks"]
                if b.get("role") != "list_marker_artifact"
            ]
            assert [
                {k: v for k, v in b.items() if k != "source_pointer"}
                for b in final["blocks"]
            ] == expected
    assert statuses == {"available": 550, "unavailable": 150}
    if official_2020:
        assert official_2020 == {"available": 50}


@pytest.mark.parametrize(
    "year,number",
    [
        (2008, 1),
        (2008, 7),
        (2008, 12),
        (2016, 1),
        (2016, 3),
        (2016, 9),
        (2016, 21),
        (2016, 22),
        (2016, 33),
        (2016, 38),
        (2016, 46),
        (2017, 1),
        (2019, 25),
        (2021, 1),
        (2021, 10),
        (2021, 48),
        (2022, 6),
        (2022, 18),
        (2022, 37),
        (2022, 45),
        (2022, 46),
    ],
)
def test_real_html_json_and_text_inspection_are_read_only(real_datasets, year, number):
    path, _ = next((p, d) for p, d in real_datasets if year in d["matching"]["years"])
    digest = sha256(path.read_bytes()).hexdigest()
    result = inspect_question(path, year=year, question_number=number)
    final = result["record"]["final_explanation"]
    html = render_html(result)
    section = re.search(
        r"<section id='final-explanation'>(.*?)</section>", html, re.DOTALL
    )[1]
    assert "<h2>Final Explanation</h2>" in section
    for ident in (
        "main-explanation",
        "incorrect-explanations",
        "other-lists",
        "explanation-order",
    ):
        assert f"id='{ident}'" in html
    for block in final["blocks"]:
        if block["type"] == "list":
            assert "<ul>" in section
            for item in block["items"]:
                if item.get("label"):
                    assert f"data-option='{item['label']}'" in section
    if (year, number) == (2021, 48):
        assert "data:image/png;base64," in section
        assert section.count("<figure") == 1
    if (year, number) == (2022, 45):
        assert (
            section.index("Three possible combinations")
            < section.index("<ul>")
            < section.index("The scores of 30")
        )
    if (year, number) == (2016, 1):
        assert section.count("Let us look at why the other options are wrong:") == 1
    if (year, number) == (2022, 46):
        assert "Manually supplied by the user" in section
    if year in (2017, 2019):
        if final.get("explanation_by_ai"):
            assert final["status"] == "available" and final["blocks"]
            assert "Explanation by AI: True" in html
            assert final["source_reference"]["path"]
        else:
            assert "answers only" in section
    for fmt in ("text", "json"):
        assert (
            json.loads(render_inspection(result, fmt))["record"]["final_explanation"]
            == final
        )
    assert sha256(path.read_bytes()).hexdigest() == digest
