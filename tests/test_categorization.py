"""Task distinctions, uncertainty, immutable handoff and inherited HTML QA."""

import json
import socket
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from categorization.backtest import render_html, report, save_inspection
from categorization.core import (
    ROOT,
    categorize,
    digest,
    freeze,
    load_handoff,
    read,
    summarize,
    validate_output,
    write_json,
)
from categorization.model import Model, attribute, features, view


def question(stem, body=None, options=None, explanation=""):
    return {
        "identity": {"year": 2090, "section": "section_1", "question_number": 1},
        "status": "matched",
        "correct_answer": "A",
        "issues": [],
        "question": {
            "question_id": "test_q1",
            "source_question_key": {
                "year": 2090,
                "section": "section_1",
                "question_number": 1,
            },
            "main_question": stem,
            "question_text": body
            or "The proposed policy is supported because it reduces costs. The author argues that all organisations should adopt this policy, despite possible alternatives.",
            "main_body": [],
            "cleaning_issues": [],
            "options": options
            or [
                {
                    "label": label,
                    "text": "A proposed statement about the policy and its supporting evidence.",
                }
                for label in "ABCDE"
            ],
        },
        "final_explanation": {
            "status": "available" if explanation else "unavailable",
            "blocks": [{"type": "paragraph", "role": "main", "text": explanation}]
            if explanation
            else [],
        },
    }


CT = [
    ("ct_main", "Which statement expresses the main conclusion of the argument?"),
    ("ct_infer", "Which conclusion is supported by the passage?"),
    ("ct_assume", "Which unstated assumption is required by the argument?"),
    ("ct_impact", "Which additional fact would weaken the argument?"),
    ("ct_error", "Which option identifies the reasoning error in the argument?"),
    ("ct_match", "Which argument has analogous reasoning to the original argument?"),
    ("ct_principle", "Which case illustrates the principle used in the argument?"),
]


@pytest.fixture
def toy_model():
    records = [(pid, question(stem)) for pid, stem in CT]
    records += [
        (
            "ps_procedure",
            question(
                "What is the latest time to leave home?",
                "The train takes 20 minutes. Allow 5 minutes to walk to the station and 4 hours at work before the 15:45 bus.",
                explanation="First subtract four hours. Then select the bus before 10:00. Finally subtract 5 minutes.",
            ),
        ),
        (
            "ps_select",
            question(
                "Which table value is above the required threshold?",
                "The table gives 12, 15, 18, 20, 21 and 30 for six groups.",
                explanation="Ignore the other rows and focus on the requested group.",
            ),
        ),
        (
            "ps_similarity",
            question(
                "Which example uses the same method of calculation?",
                "Sort four items by size and put each on the first of four 2GB discs that has room.",
            ),
        ),
        (
            "ps_similarity",
            question(
                "Which diagram is a reflection of the original shape?",
                "The diagram shows a shape and five proposed mirror images.",
            ),
        ),
    ]
    examples = [
        {
            "example_id": f"toy{i}",
            "view": view(r),
            "patterns": [pid],
            "rationale": "Synthetic cognitive-task fixture",
        }
        for i, (pid, r) in enumerate(records)
    ]
    return Model(examples, read(ROOT / "patterns.json")["patterns"])


@pytest.mark.parametrize("pid,stem", CT)
def test_critical_thinking_tasks(toy_model, pid, stem):
    c = attribute(question(stem), toy_model)
    assert c["category"] == "Critical Thinking"
    assert c["patterns"] == [pid]
    assert c["status"] == "classified"


@pytest.mark.parametrize(
    "stem,pid",
    [
        ("What is the author's principal claim in this argument?", "ct_main"),
        ("What new conclusion can we infer from the passage?", "ct_infer"),
        ("Which unspoken premise is necessary for the argument?", "ct_assume"),
        ("Which new fact would bolster the author's argument?", "ct_impact"),
        ("Which new fact undermines the argument?", "ct_impact"),
        ("Which argument exhibits a parallel flaw in reasoning?", "ct_match"),
    ],
)
def test_paraphrases_and_distinctions_not_exact_phrase_matching(toy_model, stem, pid):
    c = attribute(question(stem), toy_model)
    assert c["patterns"] == [pid]


def test_background_vocabulary_does_not_decide_task(toy_model):
    r = question(
        "Which example uses the same method of calculation?",
        "An argument about budgets mentions assumptions, errors and principles. Allocate 4 jobs to 3 machines at a cost of £20 each.",
    )
    c = attribute(r, toy_model)
    assert c["category"] == "Problem-Solving"
    assert c["patterns"] == ["ps_similarity"]
    r = question(
        "Which option identifies the reasoning error in the argument?",
        "The claim mentions a table with 30 prices and 20 graphs, but the author infers a causal connection from correlation. These facts allegedly prove the policy works.",
    )
    assert attribute(r, toy_model)["patterns"] == ["ct_error"]


def test_image_presence_does_not_change_classification(toy_model):
    r = question(
        "What is the latest time to leave home?",
        "The train takes 20 minutes. Allow 5 minutes to walk to the station and 4 hours at work before the 15:45 bus.",
        explanation="First subtract four hours. Then select the bus before 10:00. Finally subtract 5 minutes.",
    )
    before = attribute(r, toy_model)
    r["question"]["visual_assets"] = [{"image_id": "diagram", "path": "diagram.png"}]
    after = attribute(r, toy_model)
    assert before["category"] == after["category"]
    assert before["patterns"] == after["patterns"]
    assert after["patterns"] == ["ps_procedure"]


@pytest.mark.parametrize("location", ["body", "options", "assets"])
def test_structured_question_visual_excludes_text_only_families(toy_model, location):
    r = question(CT[0][1])
    image = {"image_id": "meaningful", "path": "diagram.png"}
    if location == "body":
        r["question"]["main_body"] = [{"type": "visual", "asset_id": "meaningful"}]
    elif location == "options":
        r["question"]["options"][0]["images"] = [image]
    else:
        r["question"]["visual_assets"] = [image]
    c = attribute(r, toy_model)
    assert c["category"] != "Critical Thinking"
    assert not any(p.startswith("ct_") for p in c["patterns"])
    assert c["status"] == "needs_review"  # No invented PS skill from an image.


def test_previews_and_explanation_images_do_not_exclude_text_thinking(toy_model):
    r = question(CT[0][1])
    r["question"]["visual_previews"] = [{"path": "full-page.png"}]
    r["question"]["images"] = [
        {"image_id": "white-border", "path": "full-page.png", "decorative": True},
        {"image_id": "preview-reference", "path": "full-page.png"},
    ]
    r["final_explanation"]["blocks"].append(
        {"type": "visual", "path": "explanation.png"}
    )
    assert attribute(r, toy_model)["patterns"] == ["ct_main"]


@pytest.mark.parametrize(
    "stem",
    [
        "Which shape is equivalent to the original after folding?",
        "Which diagram could be the unfolded shape?",
        "Which net could form this solid?",
        "Which figure is a rotation of the original shape?",
        "Which figure is a reflection of the original shape?",
        "Which could not be a view from one of the sides?",
        "Which diagram has the same arrangement as the original?",
        "Which diagram represents an equivalent structure?",
        "Which diagram has the same relationship between its shapes?",
    ],
)
def test_representation_equivalence_is_not_filtering_or_argument_matching(
    toy_model, stem
):
    r = question(
        stem,
        "A diagram shows a solid object. Five shapes show candidate configurations and arrangements.",
    )
    c = attribute(r, toy_model)
    assert c["category"] == "Problem-Solving"
    assert c["patterns"] == ["ps_similarity"], c


def test_transformation_word_does_not_replace_computation_or_procedure(toy_model):
    r = question(
        "What is the volume of this folded box?",
        "Fold the cardboard into a box. Its dimensions are 4 cm, 3 cm and 2 cm.",
    )
    assert not features(view(r))["spatial_equivalence"]
    r["question"]["main_question"] = (
        "Which shape faces up when the cube reaches the end position?"
    )
    assert not features(view(r))["spatial_equivalence"]


def test_percentage_reference_selection_generalizes_without_identity(real):
    _, _, model, records = real
    r = deepcopy(records[(2010, 32)])
    r["identity"]["year"] = 2099
    r["question"]["main_question"] = (
        "Which reference denominator expresses the reported percentage?"
    )
    r["question"]["question_text"] = (
        "The population fraction falls from 25% to 20%. The report calls this a 20% reduction."
    )
    r["final_explanation"] = {"blocks": []}
    c = attribute(r, model)
    assert c["patterns"] == ["ps_select"]


def test_similarity_can_coexist_with_material_information_selection():
    r = question(
        "Which diagram has the same arrangement after reflection?",
        "The table supplies 12, 15, 18, 20, 21 and 30 for the different configurations. The original shape is shown in a diagram.",
        explanation="Ignore the unrelated rows and focus on the requested group. Compare the reflected configuration.",
    )
    p = read(ROOT / "patterns.json")
    m = Model(
        [
            {
                "example_id": "dual-fixture",
                "view": view(r),
                "patterns": ["ps_select", "ps_similarity"],
                "rationale": "Synthetic material data filtering plus representation equivalence.",
            }
        ],
        p["patterns"],
        p["categories"],
    )
    c = attribute(r, m)
    assert c["status"] == "multi_label"
    assert set(c["patterns"]) == {"ps_select", "ps_similarity"}


def test_new_profile_category_uses_metadata_and_existing_schema(toy_model):
    from categorization.model import category_metadata

    r = question(
        "Which table value is above the required threshold?",
        "The table gives 12, 15, 18, 20, 21 and 30 for six groups.",
    )
    patterns = [
        {
            "id": "future",
            "category": "Future family",
            "subcategory": "Data comparison",
            "cognitive_task": "Compare data",
            "description": "A future supported task.",
            "positive_indicators": ["data_filter"],
            "counter_indicators": [],
        }
    ]
    meta = category_metadata() + [
        {
            "name": "Future family",
            "engine": "profile",
            "modalities": ["text", "visual"],
            "multi_label": True,
        }
    ]
    m = Model(
        [
            {
                "example_id": "new",
                "view": view(r),
                "patterns": ["future"],
                "rationale": "fixture",
            }
        ],
        patterns,
        meta,
    )
    assert attribute(r, m)["category"] == "Future family"


def test_missing_explanation_not_automatic_failure(toy_model):
    r = question("Which unstated assumption is required by the argument?")
    assert not r["final_explanation"]["blocks"]
    assert attribute(r, toy_model)["status"] == "classified"


def test_missing_question_unresolved_match_and_ambiguous_operation_stay_unresolved(
    toy_model,
):
    r = question("")
    assert attribute(r, toy_model)["status"] == "needs_review"
    r = question(CT[0][1])
    r["status"] = "conflict"
    assert attribute(r, toy_model)["status"] == "needs_review"
    r = question("Which option identifies the assumption and the flaw in the argument?")
    c = attribute(r, toy_model)
    assert c["status"] == "ambiguous"
    assert not c["subcategories"]


def test_ids_are_never_runtime_classification_rules(toy_model):
    r = question(CT[0][1])
    before = attribute(r, toy_model)
    r["identity"] = {"year": 2020, "section": "section_1", "question_number": 38}
    r["question"]["question_id"] = "arbitrary_renamed_record"
    assert attribute(r, toy_model) == before


def test_wrong_option_math_does_not_drive_procedure_features():
    r = question(
        "Which table value is above the threshold?",
        "The table gives 10, 20 and 30.",
        explanation="Select the relevant row.",
    )
    r["final_explanation"]["blocks"].append(
        {
            "type": "list",
            "role": "incorrect_choices",
            "items": [{"text": "1 + 2 = 3\n4 + 5 = 9\n8 + 4 = 12"}],
        }
    )
    assert not features(view(r))["dependent_calculation"]


@pytest.fixture(scope="module")
def real():
    handoff = Path("data/categorized/blackstone/matching_handoff.json")
    trained = Path("data/categorized/blackstone/model.json")
    if not handoff.exists() or not trained.exists():
        pytest.skip("Optional real matching handoff unavailable")
    h = load_handoff(handoff)
    t = read(trained)
    m = Model(t["examples"], t["patterns"]["patterns"])
    datasets = [read(ref["path"]) for ref in h["inputs"]]
    records = {
        (r["identity"]["year"], r["identity"]["question_number"]): r
        for d in datasets
        for r in d["records"]
    }
    return h, t, m, records


@pytest.mark.parametrize(
    "year,number,expected",
    [
        (2020, 7, ["ps_select"]),
        (2020, 8, ["ps_select"]),
        (2020, 13, ["ps_select"]),
        (2020, 19, ["ps_select", "ps_procedure"]),
        (2020, 26, ["ps_similarity"]),
        (2020, 31, ["ps_select", "ps_procedure"]),
        (2020, 32, ["ps_procedure"]),
        (2020, 38, ["ps_procedure"]),
        (2020, 44, ["ps_select"]),
        (2020, 50, ["ps_similarity"]),
        (2011, 8, ["ps_procedure"]),
        (2011, 38, ["ps_select"]),
        (2012, 20, ["ps_similarity"]),
        (2012, 26, ["ps_similarity"]),
        (2014, 32, ["ps_similarity"]),
        (2008, 8, ["ps_similarity"]),
        (2009, 50, ["ps_similarity"]),
        (2016, 8, ["ps_similarity"]),
        (2017, 44, ["ps_similarity"]),
        (2018, 44, ["ps_similarity"]),
        (2019, 44, ["ps_similarity"]),
        (2019, 50, ["ps_similarity"]),
    ],
)
def test_reviewed_real_selection_procedure_similarity_distinctions(
    real, year, number, expected
):
    _, _, model, records = real
    c = attribute(records[(year, number)], model)
    assert set(c["patterns"]) == set(expected), c


@pytest.mark.parametrize(
    "year,number,pid",
    [
        (2017, 1, "ct_main"),
        (2017, 3, "ct_error"),
        (2017, 4, "ct_infer"),
        (2017, 5, "ct_assume"),
        (2017, 9, "ct_impact"),
        (2017, 22, "ct_match"),
        (2021, 4, "ct_principle"),
        (2021, 22, "ct_impact"),
        (2021, 12, "ps_procedure"),
        (2021, 14, "ps_select"),
    ],
)
def test_held_out_years_not_used_for_training(real, year, number, pid):
    _, trained, model, records = real
    assert f"{year}_q{number}" not in {e["example_id"] for e in trained["examples"]}
    assert attribute(records[(year, number)], model)["patterns"] == [pid]


def test_recovered_colon_prompts_are_real_stored_upstream_structure(real):
    _, _, model, records = real
    for key, prompt in [
        ((2010, 32), "The campaign organisers' advertisement reflects:"),
        ((2012, 16), "The above argument rests on the implicit assumption that:"),
    ]:
        r = records[key]
        assert r["question"]["main_question"] == prompt
        assert not any(
            i["code"] == "ambiguous_body_question_split"
            for i in r["question"]["cleaning_issues"]
        )
        assert all(prompt not in b.get("text", "") for b in r["question"]["main_body"])
        c = attribute(r, model)
        assert c["status"] == "classified", c
    assert attribute(records[(2012, 16)], model)["patterns"] == ["ct_assume"]
    assert attribute(records[(2010, 32)], model)["patterns"] == ["ps_select"]


def test_all_current_visual_questions_exclude_current_text_only_categories(real):
    from categorization.model import question_modalities

    _, _, model, records = real
    for r in records.values():
        if "visual" in question_modalities(r.get("question") or {}):
            assert attribute(r, model)["category"] != "Critical Thinking"


def test_pipeline_preservation_round_trip_reports_and_no_pdf_or_network(
    real, tmp_path, monkeypatch
):
    h, t, _, records = real
    import pdfplumber
    import pypdfium2

    def forbidden(*args, **kwargs):
        raise AssertionError("Categorization must not extract PDFs or call providers")

    monkeypatch.setattr(pdfplumber, "open", forbidden)
    monkeypatch.setattr(pypdfium2, "PdfDocument", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    import processors.matching.core

    monkeypatch.setattr(processors.matching.core, "match_records", forbidden)
    before = {
        r["path"]: sha256(Path(r["path"]).read_bytes()).hexdigest()
        for r in [*h["inputs"], *h["dependencies"]]
    }
    data = categorize(h, Path("data/categorized/blackstone/matching_handoff.json"), t)
    validate_output(data)
    assert len(data["records"]) == len(records) == 750
    assert data["summary"] == summarize(data["records"])
    assert any(r["categorization"]["status"] == "multi_label" for r in data["records"])
    path = tmp_path / "data/result.json"
    write_json(path, data)
    assert read(path) == data
    report(data, tmp_path / "issues.md")
    text = (tmp_path / "issues.md").read_text(encoding="utf-8")
    for code in {
        i["code"] for r in data["records"] for i in r["categorization"]["issues"]
    }:
        affected = {
            r["record_key"]
            for r in data["records"]
            if any(i["code"] == code for i in r["categorization"]["issues"])
        }
        assert (
            f"## {code.replace('_', ' ').title()} ({len(affected)} questions)" in text
        )
    assert "(0 questions)" not in text
    assert before == {p: sha256(Path(p).read_bytes()).hexdigest() for p in before}
    for r in data["records"]:
        original = records[(r["identity"]["year"], r["identity"]["question_number"])]
        assert r["correct_answer"] == original.get("correct_answer")
        assert r["final_explanation"] == original.get("final_explanation")


def test_frozen_handoff_detects_changed_input(tmp_path):
    p = tmp_path / "matched/source.matched.json"
    p.parent.mkdir()
    r = question(CT[0][1])
    r["question"] = None
    p.write_text(
        json.dumps(
            {
                "stage": "matched",
                "schema_version": "1",
                "records": [r],
                "inputs": [],
                "issues": [],
            }
        ),
        encoding="utf-8",
    )
    h = freeze([p])
    target = tmp_path / "downstream/handoff.json"
    write_json(target, h, protected=h["inputs"])
    assert load_handoff(target)["summary"]["records"] == 1
    p.write_bytes(p.read_bytes() + b" ")
    with pytest.raises(ValueError, match="changed"):
        load_handoff(target)
    with pytest.raises(ValueError, match="outside"):
        write_json(p, h, protected=h["inputs"])


def test_real_html_retains_matching_content_visuals_and_multilabel(real):
    h, trained, model, records = real
    record = records[(2020, 31)]
    item = next(
        r
        for r in h["records"]
        if r["identity"]["year"] == 2020 and r["identity"]["question_number"] == 31
    )
    row = {
        "categorization": attribute(record, model),
        "matched_reference": item["matched_reference"],
    }
    before = digest(record)
    html = render_html(
        {
            "categorization_record": row,
            "logic": {"model_sha256": trained["model_sha256"]},
            "matching_inspection": {"record": record, "live_inspection_issues": []},
        }
    )
    assert (
        "Relevant Selection + Finding Procedures" in html
        or "Finding Procedures + Relevant Selection" in html
    )
    assert "<h2>Main Body</h2>" in html
    assert "<h2>Main Question</h2>" in html
    assert "<h2>Main Answers</h2>" in html
    assert "<h2>Full Explanation</h2>" in html
    assert "data:image/png;base64," in html
    assert "matching/source detail" in html.lower()
    assert "<details><summary>Evidence / detected patterns</summary>" in html
    assert before == digest(record)


@pytest.mark.parametrize("year,number", [(2015, 49), (2016, 13), (2021, 48)])
def test_filtering_does_not_hide_required_but_unsupported_procedure(real, year, number):
    _, _, model, records = real
    c = attribute(records[(year, number)], model)
    assert c["status"] == "needs_review"
    assert not c["subcategories"]
    assert any(
        i["code"]
        in {"procedure_support_incomplete", "potential_multi_label_unresolved"}
        for i in c["issues"]
    )


def test_model_tampering_and_bad_multilabel_schema_rejected(real):
    h, trained, _, _ = real
    changed = deepcopy(trained)
    changed["examples"][0]["patterns"] = ["ps_select"]
    with pytest.raises(ValueError, match="digest"):
        categorize(
            h, Path("data/categorized/blackstone/matching_handoff.json"), changed
        )
    data = categorize(
        h, Path("data/categorized/blackstone/matching_handoff.json"), trained
    )
    accepted = next(
        r for r in data["records"] if r["categorization"]["status"] == "classified"
    )
    accepted["categorization"]["subcategories"] *= 2
    with pytest.raises(ValueError, match="Duplicate subcategory"):
        validate_output(data)


def test_multilabel_survives_new_wording_and_identity(real):
    _, _, model, records = real
    record = deepcopy(records[(2020, 31)])
    record["identity"] = {"year": 2099, "section": "section_1", "question_number": 99}
    record["question"]["main_question"] = (
        "Which combined ticket price is impossible for one purchase?"
    )
    c = attribute(record, model)
    assert c["status"] == "multi_label"
    assert set(c["subcategories"]) == {"Relevant Selection", "Finding Procedures"}


def test_inspection_regeneration_only_overwrites_owned_exports(
    real, tmp_path, monkeypatch
):
    h, t, _, _ = real
    data = categorize(h, Path("data/categorized/blackstone/matching_handoff.json"), t)
    target = tmp_path / "review.html"
    save_inspection(data, year=2020, question=31, output=target)
    with pytest.raises(FileExistsError):
        save_inspection(data, year=2020, question=31, output=target)
    save_inspection(data, year=2020, question=31, output=target, overwrite=True)
    target.write_text("Unrelated user content", encoding="utf-8")
    with pytest.raises(FileExistsError):
        save_inspection(data, year=2020, question=31, output=target, overwrite=True)
    assert target.read_text(encoding="utf-8") == "Unrelated user content"


def test_regenerable_comparison_guide_and_future_family_labels(tmp_path):
    from categorization.backtest import update_guide
    from categorization.core import compare_previous

    row = {
        "record_key": "same-stable-identity",
        "identity": {"year": 2099, "question_number": 1},
        "question_view": {"main_question": "Which form?"},
        "categorization": {
            "category": "Future family",
            "subcategories": ["New skill"],
            "status": "classified",
        },
    }
    old = {
        "records": [
            {
                "record_key": row["record_key"],
                "main_question": None,
                "categorization": {
                    "category": None,
                    "subcategories": [],
                    "status": "unclassified",
                },
            }
        ]
    }
    data = {"inputs": [], "records": [row], "summary": {"processed": 1}}
    compare_previous(data, old, {"path": "baseline.json", "sha256": "test"})
    assert data["comparison"]["counts"]["previously_unresolved_resolved"] == 1
    target = tmp_path / "guide.md"
    target.write_text(
        "# Categorization backtesting\n\nMaintained commands.", encoding="utf-8"
    )
    update_guide(data, target)
    once = target.read_text(encoding="utf-8")
    update_guide(data, target)
    assert target.read_text(encoding="utf-8") == once
    assert "Future family / New skill" not in once and "Maintained commands." in once
    assert data["records"][0]["categorization"]["category"] == "Future family"


@pytest.mark.parametrize(
    "stem,pid",
    [
        (
            "Which option best matches the principle underlying the argument?",
            "ct_principle",
        ),
        (
            "Which statement identifies the principle underlying the argument?",
            "ct_principle",
        ),
        ("Which example exemplifies the general rule advocated above?", "ct_principle"),
        (
            "Which fact presents the strongest challenge to the above argument?",
            "ct_impact",
        ),
        ("Which new fact would cast doubt on the argument?", "ct_impact"),
        ("Which new fact makes the argument less convincing?", "ct_impact"),
        ("Which new fact would support the argument?", "ct_impact"),
        ("Which statement can reasonably be concluded from the passage?", "ct_infer"),
        ("What can be inferred from the passage?", "ct_infer"),
        ("Which statement follows from the supplied information?", "ct_infer"),
    ],
)
def test_generalized_intent_families_paraphrases(toy_model, stem, pid):
    c = attribute(question(stem), toy_model)
    assert c["patterns"] == [pid], c


def test_intent_counterevidence_prevents_keyword_classification(toy_model):
    r = question(
        "Which statement expresses the main conclusion of the passage?",
        "The principle is much discussed, but the author argues that a different policy should be adopted because it reduces waste.",
    )
    assert attribute(r, toy_model)["patterns"] == ["ct_main"]
    assert attribute(
        question("Which argument parallels the reasoning above?"), toy_model
    )["patterns"] == ["ct_match"]
    r = question(
        "Which challenge could not occur in this tournament?",
        "Five players must occupy seats in a fixed order. Only one player may move after each turn.",
    )
    assert not features(view(r))["evidence_change"]
    assert not features(
        view(question("Which statement, if true, weakens the argument?"))
    )["constraint_simulation"]
    numeric = question(
        "Which rule is applied to the calculation above?",
        "The calculation takes 30, adds 15 and divides the result by 5.",
    )
    assert not features(view(numeric))["principle_application"]


@pytest.mark.parametrize(
    "stem",
    [
        "Which conclusion can be drawn from the table above?",
        "Which information can be inferred from the graph above?",
    ],
)
def test_data_inference_is_not_promoted_to_written_argument(stem):
    r = question(stem, "The table shows 15, 20, 25, 40 and 60 for different regions.")
    assert not features(view(r))["argument_context"]


@pytest.mark.parametrize(
    "year,number,pid",
    [
        (2014, 23, "ct_principle"),
        (2014, 36, "ps_procedure"),
        (2013, 8, "ps_procedure"),
        (2013, 33, "ct_impact"),
        (2009, 39, "ct_infer"),
        (2009, 30, "ps_procedure"),
        (2009, 17, "ct_impact"),
        (2009, 13, "ps_select"),
        (2012, 47, "ct_principle"),
        (2016, 23, "ct_principle"),
        (2018, 47, "ct_principle"),
        (2010, 4, "ct_infer"),
        (2012, 4, "ct_infer"),
        (2019, 39, "ct_infer"),
        (2009, 38, "ps_select"),
        (2013, 32, "ps_select"),
    ],
)
def test_real_semantic_regressions_and_analogues(real, year, number, pid):
    _, _, m, records = real
    c = attribute(records[(year, number)], m)
    assert c["patterns"] == [pid], c
    if (year, number) == (2009, 17):
        assert "would weaken" in records[(year, number)]["question"]["main_question"]
        assert (
            "wouldweaken"
            in records[(year, number)]["question"]["raw_record"]["question_text"]
        )


def test_procedural_domains_generalize_without_true_keyword_alone(real):
    _, _, m, records = real
    for key in [(2014, 36), (2013, 8), (2009, 30)]:
        r = deepcopy(records[key])
        r["identity"]["year"] = 2099
        r["final_explanation"] = {"blocks": []}
        c = attribute(r, m)
        assert c["patterns"] == ["ps_procedure"], c
    r = deepcopy(records[(2009, 30)])
    r["question"]["main_question"] = "Which statement must be true?"
    assert attribute(r, m)["patterns"] == ["ps_procedure"]


def test_persisted_refinement_preserves_unaffected_previous_assignments(real):
    from categorization.model import REFINED_OPERATIONS

    baseline = Path("inspections/critical_thinking_problem_solving/tsa/categorization/before_semantic_refinement.json")
    if not baseline.exists():
        pytest.skip("Optional prior categorization audit absent")
    _, _, model, records = real
    current = {
        (r["identity"]["year"], r["identity"]["question_number"]): r["categorization"]
        for r in read("data/categorized/blackstone/tsa.categorized.json")["records"]
    }
    accepted = 0
    for row in read(baseline)["records"]:
        old = row["categorization"]
        if old["status"] not in {"classified", "multi_label"}:
            continue
        k = row["identity"]["year"], row["identity"]["question_number"]
        new = current[k]
        assert new["status"] in {"classified", "multi_label"}, k
        profile = features(view(records[k]), families=model.families)
        if not any(profile[name] for name in REFINED_OPERATIONS):
            assert new["category"] == old["category"] and set(
                new["subcategories"]
            ) == set(old["subcategories"]), k
        else:
            assert any(e["field"] == "task_profile" for e in new["evidence"]), k
        accepted += 1
    assert accepted == 469
