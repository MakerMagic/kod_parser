"""Only the explicitly approved composite changes effective body presentation."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from processors.normalization.blackstone import clean_dataset
from processors.normalization.blackstone.backtest import inspect_question, render_html
from processors.normalization.blackstone.body_assets import (
    MANIFEST,
    prepare_body_assets,
)
from processors.normalization.blackstone.issues import current_issues
from processors.normalization.blackstone.storage import load_clean, write_clean

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/blackstone/TSA_2022-aeb958e80a18.raw.json"


@pytest.fixture
def real_raw():
    if not RAW.exists():
        pytest.skip("Local question raw data unavailable")
    return json.loads(RAW.read_text(encoding="utf-8"))


def test_exact_supplied_png_order_raw_immutability_and_rerun(tmp_path, real_raw):
    original_hash = sha256(RAW.read_bytes()).hexdigest()
    original = deepcopy(real_raw)
    transformed = clean_dataset(real_raw, RAW)
    before = deepcopy(transformed)
    output = tmp_path / "clean/2022.clean.json"
    write_clean(transformed, output)
    first = load_clean(output)
    q = first["questions"][43]
    body_visuals = [b for b in q["main_body"] if b["type"] == "visual"]
    assert len(body_visuals) == 2  # pinned cards + independent game-history table
    assert body_visuals[0]["override_id"] == "user_supplied_tsa_2022_q044_cards"
    assert (
        body_visuals[1]["asset_id"]
        == before["questions"][43]["visual_assets"][16]["image_id"]
    )
    assert q["main_body"][0]["type"] == "text"
    assert q["main_body"][2]["type"] == "text"
    pinned = q["visual_assets"][-1]
    source = MANIFEST.parent / "tsa_2022_q044_cards.png"
    assert (output.parent / pinned["path"]).read_bytes() == source.read_bytes()
    assert len(pinned["provenance"]["replaced_raw_assets"]) == 16
    assert q["visual_assets"][:-1] == before["questions"][43]["visual_assets"]
    assert q["raw_record"] == original["questions"][43]
    assert not current_issues(q, clean_json=output)
    result = inspect_question(
        [output], source="TSA_2022.pdf", question_number=44, year=2022
    )
    html = render_html(result)
    section = html.split("<section id='main-body'>")[1].split("</section>")[0]
    assert section.count("<img ") == 2
    assert "User-supplied pinned composite" in section
    assert "game has progressed" in section
    for old, new in zip(before["questions"], first["questions"]):
        if old["question_number"] != 44:
            # Option derivative preparation is independent; body and all raw data stay exact.
            assert old["main_body"] == new["main_body"]
            assert old["raw_record"] == new["raw_record"]
    write_clean(clean_dataset(real_raw, RAW), output, overwrite=True)
    assert load_clean(output) == first
    assert prepare_body_assets(first, output) == first
    assert real_raw == original
    assert sha256(RAW.read_bytes()).hexdigest() == original_hash


@pytest.mark.parametrize("failure", ["image", "source", "group", "order"])
def test_invalid_override_keeps_originals_and_reports_issue(
    tmp_path, real_raw, failure
):
    clean = clean_dataset(real_raw, RAW)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rule = manifest["overrides"][0]
    if failure == "image":
        rule["image_sha256"] = "0" * 64
    elif failure == "source":
        rule["source_sha256"] = "0" * 64
    elif failure == "group":
        rule["replaced_asset_indices"].append(99)
    else:
        clean["questions"][43]["main_body"].insert(
            3, {"type": "text", "text": "Do not remove me"}
        )
    rule["image"] = "supplied.png"
    (tmp_path / "supplied.png").write_bytes(
        (MANIFEST.parent / "tsa_2022_q044_cards.png").read_bytes()
    )
    config = tmp_path / "body_visuals.json"
    config.write_text(json.dumps(manifest), encoding="utf-8")
    q_before = deepcopy(clean["questions"][43])
    out = prepare_body_assets(clean, tmp_path / "clean/q.clean.json", manifest=config)
    q = out["questions"][43]
    assert q["main_body"] == q_before["main_body"]
    assert q["visual_assets"] == q_before["visual_assets"]
    assert "pinned_body_visual_unresolved" in {i["code"] for i in q["cleaning_issues"]}


def test_missing_pinned_copy_is_live_issue(tmp_path, real_raw):
    output = tmp_path / "clean/q.clean.json"
    write_clean(clean_dataset(real_raw, RAW), output)
    q = load_clean(output)["questions"][43]
    (output.parent / q["visual_assets"][-1]["path"]).unlink()
    assert "broken_image_reference" in {
        i["code"] for i in current_issues(q, clean_json=output)
    }
