"""Disconnected drawings need structural evidence, never a larger global gap."""

import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
from test_blackstone_raw import write_pdf

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.backtest import collect_issues
from parsers.blackstone.visual_grouping import group_body_components


def obj(identifier, box, kind="curve"):
    return {"image_id": identifier, "bbox": box, "object_type": kind, "kind": "vector"}


def line(text, box, page=1):
    tokens = text.split()
    return {
        "text": text,
        "page": page,
        "x0": box[0],
        "top": box[1],
        "x1": box[2],
        "bottom": box[3],
        "word_texts": tokens,
        "word_boxes": [box] * len(tokens),
    }


def anchor(y=500, label="A"):
    return {"page": 1, "label": label, "bbox": [30, y, 40, y + 10]}


def dimension_case():
    shape = {
        "bbox": [100, 100, 180, 300],
        "objects": [obj("shape", [100, 100, 180, 300])],
    }
    dimension = {
        "bbox": [205, 100, 215, 300],
        "objects": [
            obj("shaft", [210, 106, 210, 294], "line"),
            obj("head1", [205, 100, 215, 108]),
            obj("head2", [205, 292, 215, 300]),
        ],
    }
    return [shape, dimension], [line("38 cm", [225, 185, 260, 197])]


@pytest.mark.parametrize("scale", [0.4, 1, 3.7])
@pytest.mark.parametrize("horizontal", [False, True])
def test_dimension_grouping_is_scale_and_orientation_independent(scale, horizontal):
    groups, lines = dimension_case()
    for group in groups:
        boxes = [group["bbox"], *[o["bbox"] for o in group["objects"]]]
        for b in boxes:
            if horizontal:
                b[:] = [b[1], b[0], b[3], b[2]]
            b[:] = [v * scale for v in b]
    for l in lines:
        b = [l["x0"], l["top"], l["x1"], l["bottom"]]
        if horizontal:
            b = [b[1], b[0], b[3], b[2]]
        l.update(line(l["text"], [v * scale for v in b]))
    before = deepcopy(groups)
    result = group_body_components(groups, lines, 1, [anchor(500 * scale)])
    assert len(result) == 1
    assert {o["image_id"] for o in result[0]["objects"]} == {
        "shape",
        "shaft",
        "head1",
        "head2",
    }
    assert groups == before
    assert "unique extent-aligned" in result[0]["grouping_notes"][0]


@pytest.mark.parametrize(
    "failure",
    [
        "no_heads",
        "no_measurement",
        "prose",
        "answer_region",
        "different_extent",
        "separate_image",
    ],
)
def test_geometry_does_not_merge_unproven_or_answer_components(failure):
    groups, lines = dimension_case()
    anchors = [anchor()]
    if failure == "no_heads":
        groups[1]["objects"] = groups[1]["objects"][:1]
    elif failure == "no_measurement":
        lines = []
    elif failure == "prose":
        lines.append(
            line(
                "This unrelated sentence separates the two images.",
                [183, 180, 204, 192],
            )
        )
    elif failure == "answer_region":
        anchors = [anchor(50)]
    elif failure == "different_extent":
        groups[0]["bbox"][3] = 220
        groups[0]["objects"][0]["bbox"][3] = 220
    else:
        groups[1]["objects"].append(obj("independent_drawing", [205, 120, 215, 150]))
    assert len(group_body_components(groups, lines, 1, anchors)) == 2


def test_ambiguous_dimension_ownership_is_reported_not_guessed():
    groups, lines = dimension_case()
    groups.append(
        {
            "bbox": [240, 100, 320, 300],
            "objects": [obj("other_shape", [240, 100, 320, 300])],
        }
    )
    result = group_body_components(groups, lines, 1, [anchor()])
    assert len(result) == 3
    annotation = next(
        g for g in result if any(o["image_id"] == "shaft" for o in g["objects"])
    )
    assert annotation["grouping_warnings"] == [
        "visual_grouping_uncertain:dimension_annotation_multiple_owners"
    ]


def lattice(x=100, y=100, n=4, prefix="point"):
    groups = []
    for row in range(n):
        for col in range(n):
            b = [x + col * 30, y + row * 30, x + col * 30 + 5, y + row * 30 + 5]
            groups.append(
                {
                    "bbox": b[:],
                    "objects": [
                        obj(f"{prefix}{row}_{col}", b[:]),
                        obj(f"{prefix}{row}_{col}_stroke", b[:]),
                    ],
                }
            )
    middle = x + (n - 1) * 15
    return groups, [
        line(
            "centre", [middle - 8, y + (n - 1) * 15, middle + 16, y + (n - 1) * 15 + 8]
        ),
        line("1m", [x + 10, y - 15, x + 25, y - 6]),
    ]


def test_complete_labelled_lattices_stay_separate_across_prose():
    first, lines = lattice()
    second, more = lattice(y=250, n=5, prefix="later")
    groups = first + second
    lines += [
        line("The next diagram represents a different day.", [60, 215, 420, 227]),
        *more,
    ]
    result = group_body_components(groups, lines, 1, [anchor(450)])
    assert len(result) == 2
    assert sorted(len(g["objects"]) for g in result) == [32, 50]
    assert result[0]["bbox"][3] < 215 < result[1]["bbox"][1]


@pytest.mark.parametrize(
    "failure",
    ["missing_point", "no_centre", "two_centres", "no_measurement", "no_choices"],
)
def test_lattice_evidence_must_be_complete_and_unambiguous(failure):
    groups, lines = lattice()
    anchors = [anchor()]
    if failure == "missing_point":
        groups.pop()
    elif failure == "no_centre":
        lines = lines[1:]
    elif failure == "two_centres":
        lines.append(line("centre", [120, 110, 145, 118]))
    elif failure == "no_measurement":
        lines = lines[:1]
    else:
        anchors = []
    assert len(group_body_components(groups, lines, 1, anchors)) == len(groups)


@pytest.mark.parametrize("ambiguous", [False, True])
def test_real_pdf_renders_whole_dimension_with_labels_and_preserves_raw(
    tmp_path, monkeypatch, ambiguous
):
    def no_network(*args, **kwargs):
        raise AssertionError("Grouping must not acquire input")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    pdf = write_pdf(
        tmp_path / "dimensions.pdf",
        [
            [
                (50, 760, "Thinking Skills Assessment 2024 Section 1"),
                (50, 740, "Instructions to Candidates"),
                (50, 710, "1 Measure the complete diagram shown below."),
                (120, 655, "15cm"),
                (230, 550, "38cm"),
                (50, 420, "What is the required length?"),
                *[
                    (60, 390 - i * 22, f"{label} {i + 1} metres")
                    for i, label in enumerate("ABCDE")
                ],
            ]
        ],
        graphics_commands=[
            "100 500 m 180 500 l 160 650 l 100 640 l h S",
            "210 506 m 210 634 l S",
            "205 632 m 215 632 l 210 640 l h f",
            "205 508 m 215 508 l 210 500 l h f",
            *(["240 500 m 320 500 l 300 650 l 240 640 l h S"] if ambiguous else []),
        ],
    )
    data = parse_pdf(pdf, asset_dir=tmp_path / "assets")
    validate_raw(data)
    q = data["questions"][0]
    assert q["question_number"] == 1 and [o["label"] for o in q["options"]] == list(
        "ABCDE"
    )
    assert (
        q["raw"]["question_block"]
        and "Measure the complete diagram" in q["raw"]["question_block"]
    )
    if ambiguous:
        assert len(q["visual_assets"]) == 3
        findings = collect_issues(data, tmp_path / "dimensions.raw.json")
        assert any(
            "visual_grouping_uncertain:dimension_annotation_multiple_owners" in reason
            for row in findings
            for reason in row["reasons"]
        )
        return
    assert len(q["visual_assets"]) == 1
    asset = q["visual_assets"][0]
    assert "38cm" in [t["text"] for t in asset["visual_text"]]
    assert len(asset["object_ids"]) == 4


@pytest.fixture(scope="module")
def local_reparse(tmp_path_factory):
    root = Path("acquisition/local")
    sources = [root / f"TSA Oxford {year}.pdf" for year in (2016, 2019)]
    if not all(p.exists() for p in sources):
        pytest.skip("Local grouping regression PDFs unavailable")
    folder = tmp_path_factory.mktemp("grouping_pdfs")
    return {
        year: parse_pdf(source, asset_dir=folder / str(year) / "assets")
        for year, source in zip((2016, 2019), sources)
    }


def test_real_split_cases_are_complete_and_keep_other_visuals_separate(local_reparse):
    for data in local_reparse.values():
        validate_raw(data)
        assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
    q36 = local_reparse[2019]["questions"][35]
    assert len(q36["visual_assets"]) == 2
    drawing, table = q36["visual_assets"]
    assert len(drawing["object_ids"]) == 7
    assert {"15cm", "38cm"} <= {v["text"] for v in drawing["visual_text"]}
    assert table.get("visual_kind") == "table"
    assert len(table["object_ids"]) == 21
    assert drawing["bbox"][3] < table["bbox"][1]
    q37 = local_reparse[2016]["questions"][36]
    assert len(q37["visual_assets"]) == 2
    assert all("lattice" in " ".join(a["notes"]) for a in q37["visual_assets"])
    assert all(
        "centre" in [t["text"] for t in a["visual_text"]] for a in q37["visual_assets"]
    )
    assert q37["visual_assets"][0]["bbox"][3] < q37["visual_assets"][1]["bbox"][1]
    for q in (q36, q37):
        assert {o["image_id"] for o in q["images"] if not o.get("decorative")} == {
            identifier for a in q["visual_assets"] for identifier in a["object_ids"]
        }


def test_known_ambiguous_cases_remain_flagged(local_reparse, tmp_path):
    data = local_reparse[2019]
    q44 = data["questions"][43]
    assert any("shared_geometry_requires_review" in w for w in q44["warnings"])
    q32 = data["questions"][31]
    assert any("incomplete_or_ambiguous_options" in w for w in q32["warnings"])


def test_stored_graph_table_answer_and_complex_controls_are_not_regrouped():
    rawdir = Path("data/raw/blackstone")
    controls = [
        (2017, 14),
        (2017, 20),
        (2021, 26),
        (2021, 32),
        (2021, 37),
        (2022, 8),
        (2022, 20),
        (2022, 50),
        (2020, 36),
    ]
    for year, number in controls:
        files = list(rawdir.glob(f"*{year}*.raw.json"))
        if not files:
            continue
        data = json.loads(files[0].read_text(encoding="utf-8"))
        q = data["questions"][number - 1]
        groups = [
            {
                "bbox": a["graphic_bbox"],
                "objects": [o for o in q["images"] if o["image_id"] in a["object_ids"]],
            }
            for a in q["visual_assets"]
        ]
        lines = []
        anchors = []
        for block in q["layout_blocks"]:
            if block["type"] != "text":
                continue
            lines.append(line(block["text"], block["bbox"], block["page"]))
            if block["component"] == "option":
                anchors.append(
                    {
                        "page": block["page"],
                        "bbox": block["bbox"],
                        "label": block["label"],
                    }
                )
        before = sorted(
            tuple(sorted(o["image_id"] for o in g["objects"])) for g in groups
        )
        for page in {a["page"] for a in q["visual_assets"]}:
            result = group_body_components(groups, lines, page, anchors)
            assert (
                sorted(
                    tuple(sorted(o["image_id"] for o in g["objects"])) for g in result
                )
                == before
            ), (year, number)


def test_regenerated_clean_body_preserves_raw_traceability_and_order():
    from hashlib import sha256

    from processors.normalization.blackstone.backtest import (
        inspect_question,
        render_html,
    )

    for year, number in ((2016, 37), (2019, 36)):
        files = list(Path("data/clean/blackstone").glob(f"*{year}-*.clean.json"))
        if not files:
            pytest.skip("Run documented RAW and CLEAN regeneration commands")
        clean_path = files[0]
        digest = sha256(clean_path.read_bytes()).hexdigest()
        result = inspect_question(
            [clean_path],
            source=f"TSA Oxford {year}.pdf",
            year=year,
            question_number=number,
        )
        q = result["question"]
        assert not result["cleaning_issues"] and not result["raw_visual_issues"]
        assert (
            sha256(Path(q["raw_reference"]["path"]).read_bytes()).hexdigest()
            == q["raw_reference"]["sha256"]
        )
        raw = json.loads(Path(q["raw_reference"]["path"]).read_text(encoding="utf-8"))[
            "questions"
        ][number - 1]
        assert q["raw_record"] == raw
        visuals = [b for b in q["main_body"] if b["type"] == "visual"]
        assert [b["asset_id"] for b in visuals] == [
            a["image_id"] for a in raw["visual_assets"]
        ]
        assert len(visuals) == 2
        html = render_html(result)
        assert "Main Body" in html and "data:image/png;base64," in html
        if year == 2016:
            blocks = raw["layout_blocks"]
            first, second = [i for i, b in enumerate(blocks) if b["type"] == "visual"]
            assert any(
                "When I looked" in b.get("text", "") for b in blocks[first + 1 : second]
            )
            # Independent, pre-existing CLEAN prompt classification remains
            # unresolved: the declarative inter-diagram sentence is retained
            # in Main Question, not fixed by regrouping its surrounding assets.
            assert "When I looked" in q["main_question"]
        assert sha256(clean_path.read_bytes()).hexdigest() == digest
