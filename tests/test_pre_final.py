"""New-stage contracts: no upstream writes, no report inputs or implicit rendering."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from processors.pre_final import core, render
from processors.pre_final.storage import ROOT, InvalidInput, Store, write_owned


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}


@pytest.fixture
def inputs(tmp_path):
    """Small canonical source contracts; no PDFs, network, model or stage run."""
    write(
        tmp_path / core.CATALOG,
        json.loads((ROOT / core.CATALOG).read_text(encoding="utf-8")),
    )
    paths = {}
    for source in ("TSA", "BMAT"):
        family = "blackstone" if source == "TSA" else "bmat"
        key = {
            "source": family,
            "year": 2021,
            "section": "section_1",
            "paper": None,
            "variant": None,
            "question_number": 25,
        }
        raw_ref = write(tmp_path / f"data/raw/{family}/paper.json", {"questions": []})
        q = {
            "question_id": family + "_2021_q25",
            "question_number": 25,
            "source_question_key": key,
            "main_body": [{"type": "text", "text": "Price £3.00. Lasts 40 days."}],
            "main_question": "How much less per day?",
            "options": [
                {"label": "A", "text": "1p", "images": [], "warnings": []},
                {"label": "B", "text": "2p", "images": [], "warnings": []},
            ],
            "visual_assets": [],
            "visual_previews": [],
            "raw_warnings": [],
            "cleaning_issues": [],
            "raw_reference": raw_ref,
        }
        clean_ref = {
            **write(tmp_path / f"data/clean/{family}/paper.json", {"questions": [q]}),
            "json_pointer": "/questions/0",
        }
        final = {
            "status": "available",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "£3.00 / 40 = 7.5p.\n\nSubtract the daily rates.",
                }
            ],
            "source_warnings": [],
            "issues": [],
            "explanation_by_ai": False,
        }
        m = {
            "identity": {**key, "source_family": family},
            "question": q,
            "status": "matched",
            "question_reference": clean_ref,
            "correct_answer": "A",
            "final_explanation": final,
            "issues": [],
            "answer": None,
        }
        match_ref = {
            **write(
                tmp_path / f"data/merged/{family}/questions.json", {"records": [m]}
            ),
            "json_pointer": "/records/0",
        }
        c = {
            "category": "Problem-Solving",
            "subcategories": ["Finding Procedures"],
            "patterns": ["ps_procedure"],
            "status": "classified" if source == "TSA" else "supported",
            "issues": [],
        }
        if source == "TSA":
            record = {
                "identity": {
                    "year": 2021,
                    "section": "section_1",
                    "question_number": 25,
                    "source_question_key": key,
                },
                "matched_reference": match_ref,
                "question_view": q,
                "correct_answer": "A",
                "final_explanation": final,
                "categorization": c,
            }
        else:
            record = {
                "identity": key,
                "matching_reference": match_ref,
                "question": q,
                "matching_status": "matched",
                "categorization": c,
            }
        path = tmp_path / f"data/categorized/{family}/questions.json"
        write(
            path,
            {
                "stage": "categorized" if source == "TSA" else "categorization",
                "records": [record],
            },
        )
        paths[source] = path
    return tmp_path, paths


def change_category(inputs, source, transform):
    _root, paths = inputs
    data = json.loads(paths[source].read_text(encoding="utf-8"))
    transform(data["records"][0])
    write(paths[source], data)


def change_match(inputs, source, transform):
    _root, paths = inputs
    data = json.loads(paths[source].read_text(encoding="utf-8"))
    row = data["records"][0]
    field = "matched_reference" if source == "TSA" else "matching_reference"
    path = Path(row[field]["path"])
    match = json.loads(path.read_text(encoding="utf-8"))
    transform(match["records"][0])
    m = match["records"][0]
    clean_path = Path(m["question_reference"]["path"])
    m["question_reference"] = {
        **write(clean_path, {"questions": [m["question"]]}),
        "json_pointer": "/questions/0",
    }
    row[field] = {**write(path, match), "json_pointer": "/records/0"}
    if source == "TSA":
        row.update(
            question_view=m["question"],
            correct_answer=m["correct_answer"],
            final_explanation=m["final_explanation"],
        )
    else:
        row.update(question=m["question"], matching_status=m["status"])
    write(paths[source], data)


def test_both_sources_unified_and_no_earlier_stage_or_renderer_called(
    inputs, monkeypatch
):
    root, paths = inputs

    def forbidden(*args, **kwargs):
        raise AssertionError("Assembly must not render")

    monkeypatch.setattr(render, "render_html", forbidden)
    protected = {p: p.read_bytes() for p in root.rglob("*.json")}
    first, findings = core.run(paths, root=root)
    second, _ = core.run(dict(reversed(list(paths.items()))), root=root)
    assert first["questions"] == second["questions"]
    assert first["summary"] == {"total": 2, "by_source": {"BMAT": 1, "TSA": 1}}
    assert findings["excluded_total"] == 0
    assert len({q["id"] for q in first["questions"]}) == 2
    assert all(q["difficulty"] is None for q in first["questions"])
    assert all(set(q) == set(first["questions"][0]) for q in first["questions"])
    assert all(p.read_bytes() == content for p, content in protected.items())
    assert not list(root.rglob("*.html"))
    assert not list(root.rglob("*.md"))


@pytest.mark.parametrize("source", ["TSA", "BMAT"])
@pytest.mark.parametrize("issue", ["raw", "clean", "match", "explanation", "category"])
def test_unresolved_issues_excluded(inputs, source, issue):
    if issue == "category":
        change_category(
            inputs,
            source,
            lambda r: r["categorization"].update(issues=[{"code": "review"}]),
        )
    else:

        def change(m):
            if issue == "raw":
                m["question"]["raw_warnings"] = [
                    "visual_neighbor_boundary_uncertain:content_bounds_overlap"
                ]
            elif issue == "clean":
                m["question"]["cleaning_issues"] = [{"code": "missing_prompt"}]
            elif issue == "match":
                m["issues"] = [{"code": "answer_conflict"}]
            else:
                m["final_explanation"]["status"] = "uncertain"

        change_match(inputs, source, change)
    data, findings = core.build(inputs[1], root=inputs[0])
    assert all(q["source"] != source for q in data["questions"])
    assert findings["excluded_total"] == 1


@pytest.mark.parametrize(
    "patterns",
    [[], ["bogus"], ["ps_select", "ps_procedure"], ["ps_procedure", "ps_procedure"]],
)
def test_missing_invalid_or_multiple_categories_excluded(inputs, patterns):
    change_category(
        inputs, "BMAT", lambda r: r["categorization"].update(patterns=patterns)
    )
    _, findings = core.build(inputs[1], root=inputs[0])
    assert "invalid_or_missing_category" in findings["exclusions"][0]["reasons"]


def test_bmat_specific_never_mapped(inputs):
    change_category(
        inputs,
        "BMAT",
        lambda r: r["categorization"].update(
            category="BMAT-specific",
            subcategories=["too long"],
            patterns=["too long"],
            status="intentional_skip",
        ),
    )
    result, findings = core.build(inputs[1], root=inputs[0])
    assert result["summary"]["by_source"] == {"TSA": 1}
    assert "intentional_skip" in findings["exclusions"][0]["reasons"]


def test_information_notice_is_not_issue_but_unknown_review_flag_blocks(inputs):
    def informational(m):
        m["question"]["raw_warnings"] = [
            "graphics_present:option_association_not_resolved"
        ]
        m["matching"] = {"upstream_review_required": True}

    change_match(inputs, "TSA", informational)
    data, findings = core.build(inputs[1], root=inputs[0])
    assert len(data["questions"]) == 2 and not findings["exclusions"]
    change_match(inputs, "TSA", lambda m: m["question"].update(raw_warnings=[]))
    _, findings = core.build(inputs[1], root=inputs[0])
    assert "upstream_review_required" in findings["exclusions"][0]["reasons"]


def test_no_invented_answer_or_prompt(inputs):
    change_match(inputs, "BMAT", lambda m: m.update(correct_answer=None))
    _, findings = core.build(inputs[1], root=inputs[0])
    assert findings["exclusions"][0]["reasons"] == ["correct_answer_missing_or_invalid"]
    change_match(
        inputs,
        "BMAT",
        lambda m: (
            m.update(correct_answer="A"),
            m["question"].update(main_question=""),
        ),
    )
    _, findings = core.build(inputs[1], root=inputs[0])
    assert findings["exclusions"][0]["reasons"] == ["required_question_content_missing"]


def test_source_scope_and_stale_snapshots(inputs):
    change_category(inputs, "BMAT", lambda r: r["identity"].update(source="blackstone"))
    _, findings = core.build(inputs[1], root=inputs[0])
    assert "source_identity_invalid" in findings["exclusions"][0]["reasons"]
    change_category(
        inputs, "TSA", lambda r: r["question_view"].update(main_question="Changed!")
    )
    _, findings = core.build(inputs[1], root=inputs[0])
    assert any(
        "categorization_snapshot_changed" in e["reasons"]
        for e in findings["exclusions"]
    )


def test_duplicate_id_rejects_all_occurrences(inputs):
    root, paths = inputs
    data = json.loads(paths["TSA"].read_text(encoding="utf-8"))
    data["records"].append(deepcopy(data["records"][0]))
    write(paths["TSA"], data)
    result, findings = core.build(paths, root=root)
    assert result["summary"]["by_source"] == {"BMAT": 1}
    assert findings["excluded_total"] == 2
    assert all("duplicate_identity" in e["reasons"] for e in findings["exclusions"])


def test_ids_intrinsic_not_content_filename_or_order():
    base = {
        "source": "TSA",
        "year": 2021,
        "section": "section_1",
        "paper": "4502/01",
        "variant": None,
        "question_number": 25,
    }
    assert core.stable_id(base) == core.stable_id(
        {**base, "text": "different", "filename": "renamed.pdf"}
    )
    changes = [
        {"source": "BMAT"},
        {"year": 2020},
        {"section": "section_2"},
        {"paper": "4502:01"},
        {"paper": None},
        {"paper": "null"},
        {"variant": "A"},
        {"question_number": 26},
    ]
    ids = [core.stable_id(base)] + [core.stable_id({**base, **d}) for d in changes]
    assert len(set(ids)) == len(ids)


def test_ai_and_character_range_provenance_preserved(inputs):
    root, paths = inputs
    ref = write(root / "source_explanation.json", {"text": "Original explanation"})

    def update(m):
        m["final_explanation"].update(
            explanation_by_ai=True, source_reference={**ref, "character_range": [0, 20]}
        )

    change_match(inputs, "TSA", update)
    data, findings = core.build(paths, root=root)
    q = next(q for q in data["questions"] if q["source"] == "TSA")
    assert q["explanation_by_ai"] is True
    assert q["explanation"]["provenance"]["source_reference"]["character_range"] == [
        0,
        20,
    ]
    assert "\n\n" in q["explanation"]["blocks"][0]["text"]
    assert not findings["exclusions"]


def test_explicit_unavailable_explanation_allowed(inputs):
    change_match(
        inputs,
        "TSA",
        lambda m: m["final_explanation"].update(status="unavailable", blocks=[]),
    )
    result, _ = core.build(inputs[1], root=inputs[0])
    assert (
        next(q for q in result["questions"] if q["source"] == "TSA")["explanation"]
        is None
    )


def test_renderer_reads_prefinal_only_with_correct_order(inputs):
    root, paths = inputs
    data, _ = core.run(paths, root=root)
    # Upstream is no longer accessible. A pre-final inspector must still work.
    for path in paths.values():
        path.unlink()
    html = render.inspect(
        root / "data/pre_final/questions.json",
        root=root,
        source="BMAT",
        year=2021,
        question=25,
    )
    order = [
        html.index("id='" + s + "'")
        for s in (
            "source",
            "explanation-by-ai",
            "category",
            "main-body",
            "main-question",
            "main-answers",
            "correct-answer",
            "explanation",
        )
    ]
    assert order == sorted(order)
    assert ">BMAT</p>" in html and "Finding Procedures" in html
    assert "BMAT-specific" not in html
    assert "£3.00 / 40 = 7.5p.\n\nSubtract the daily rates." in html
    with pytest.raises(ValueError, match="Select an exact"):
        render.select(data)


def test_write_protects_upstream_and_unrelated_files(tmp_path):
    data = {"owner": "pre_final_v1", "stage": "pre_final"}
    with pytest.raises(ValueError, match="upstream"):
        write_owned(tmp_path / "data/categorized/sensitive.json", data, tmp_path)
    path = tmp_path / "other.json"
    write(path, {"owner": "not-yours"})
    with pytest.raises(ValueError, match="unrelated"):
        write_owned(path, data, tmp_path)


def test_stale_asset_rejected(tmp_path):
    store = Store(tmp_path)
    path = tmp_path / "asset.png"
    path.write_bytes(b"pixels")
    with pytest.raises(InvalidInput, match="asset.png"):
        store.check({"path": str(path), "sha256": "0" * 64})


def test_visual_associations_and_clean_crop_are_preserved(inputs):
    root, paths = inputs
    raw = root / "data/raw/bmat/body.png"
    raw.write_bytes(b"body pixels")
    option = root / "data/raw/bmat/answer.png"
    option.write_bytes(b"raw answer pixels")
    clean = root / "data/clean/bmat/answer_clean.png"
    clean.write_bytes(b"validated clean answer pixels")
    image = {
        "image_id": "body",
        "path": "body.png",
        "sha256": sha256(raw.read_bytes()).hexdigest(),
        "page": 1,
        "bbox": [1, 2, 3, 4],
    }
    answer = {
        "image_id": "answer",
        "path": "answer.png",
        "sha256": sha256(option.read_bytes()).hexdigest(),
        "page": 1,
        "bbox": [1, 4, 3, 6],
        "option_label": "A",
        "clean_asset": {
            "path": "answer_clean.png",
            "path_base": "clean_json_parent",
            "sha256": sha256(clean.read_bytes()).hexdigest(),
        },
    }

    def change(m):
        q = m["question"]
        q["visual_assets"] = [image, answer]
        q["main_body"].append({"type": "visual", "asset_id": "body"})
        q["options"][0].update(text="", images=[answer])

    change_match(inputs, "BMAT", change)
    data, findings = core.build(paths, root=root)
    q = next(q for q in data["questions"] if q["source"] == "BMAT")
    assert not findings["exclusions"]
    assert q["main_body"][-1] == {"type": "visual", "asset_id": "body"}
    assert q["main_answers"][0]["asset_ids"] == ["answer"]
    assert q["assets"][1]["path"] == "data/clean/bmat/answer_clean.png"
    assert [(a["role"], a["option_label"]) for a in q["assets"]] == [
        ("body", None),
        ("option", "A"),
    ]
    html = render.render_html(q, data["categories"], root=root)
    assert "data:image/png;base64," in html
    clean.write_bytes(b"changed crop")
    with pytest.raises(InvalidInput, match="answer_clean.png"):
        render.render_html(q, data["categories"], root=root)


def test_existing_explanation_lists_are_not_flattened(inputs):
    def change(m):
        m["final_explanation"]["blocks"] = [
            {
                "type": "list",
                "ordered": True,
                "role": "main",
                "items": [
                    {"text": "First calculation", "label": None},
                    {"text": "Second calculation", "label": "B"},
                ],
            }
        ]

    change_match(inputs, "TSA", change)
    data, _ = core.build(inputs[1], root=inputs[0])
    q = next(q for q in data["questions"] if q["source"] == "TSA")
    assert q["explanation"]["blocks"][0]["items"][1] == {
        "text": "Second calculation",
        "label": "B",
    }
    html = render.render_html(q, data["categories"], root=inputs[0])
    assert "<ol>" in html and "B: Second calculation" in html


def test_formal_schema_and_native_validator_agree(inputs):
    result, _ = core.build(inputs[1], root=inputs[0])
    schema = core.SCHEMA["$defs"]["question"]
    assert set(schema["required"]) == set(result["questions"][0])
    assert set(schema["properties"]["category"]["enum"]) == set(result["categories"])
    broken = deepcopy(result)
    broken["questions"][0]["difficulty"] = "easy"
    with pytest.raises(ValueError, match="difficulty"):
        core.validate(broken)
    broken = deepcopy(result)
    broken["categories"]["unsupported"] = {"name": "Other", "family": "BMAT-specific"}
    with pytest.raises(ValueError, match="ten canonical"):
        core.validate(broken)


def test_clean_snapshot_is_validated_not_only_its_file_hash(inputs):
    change_category(inputs, "TSA", lambda r: None)
    root, paths = inputs
    data = json.loads(paths["TSA"].read_text(encoding="utf-8"))
    ref = data["records"][0]["matched_reference"]
    matched = json.loads(Path(ref["path"]).read_text(encoding="utf-8"))
    clean = matched["records"][0]["question_reference"]
    clean["sha256"] = write(
        Path(clean["path"]), {"questions": [{"different": "question"}]}
    )["sha256"]
    data["records"][0]["matched_reference"]["sha256"] = write(
        Path(ref["path"]), matched
    )["sha256"]
    write(paths["TSA"], data)
    _, findings = core.build(paths, root=root)
    assert findings["exclusions"][0]["reasons"] == ["clean_snapshot_changed"]


def test_current_persisted_dataset_invariants_and_input_hashes():
    data = json.loads(
        (ROOT / "data/pre_final/questions.json").read_text(encoding="utf-8")
    )
    core.validate(data)
    assert set(data["summary"]["by_source"]) == {"TSA", "BMAT"}
    assert len(data["categories"]) == 10
    store = Store()
    for ref in [*data["inputs"], data["taxonomy_reference"]]:
        store.check(ref)
    for q in data["questions"]:
        ref = q["provenance"]["categorized_reference"]
        row = store.record(
            {**store.reference(ref["path"]), "json_pointer": ref["json_pointer"]}
        )
        assert not core.gate(row, q["source"], data["categories"])
        m = store.record(row.get("matched_reference") or row.get("matching_reference"))
        assert not core.issue_reasons(row, m["question"], m)
        assert q["correct_answer"] == m["correct_answer"]
        assert q["id"] == m["question"]["question_id"]
        assert q["main_question"] == m["question"]["main_question"]
        for asset in q["assets"]:
            store.check(asset)


def test_full_rerun_identical_without_writes():
    first = (ROOT / "data/pre_final/questions.json").read_bytes()
    data, findings = core.build()
    regenerated = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    assert sha256(regenerated).hexdigest() == sha256(first).hexdigest()
    assert len(findings["exclusions"]) + len(data["questions"]) == 1414
    keys = [
        (e["reference"]["path"], e["reference"]["json_pointer"])
        for e in findings["exclusions"]
    ]
    assert len(keys) == len(set(keys))
