"""Local raster recovery: structure, evidence and conservative uncertainty."""

import copy
import json
import subprocess
from pathlib import Path

import pytest

from parsers.mathematics.raster import (
    assemble,
    eligible,
    formula_signature,
    normalize_latex,
)
from parsers.mathematics.raster_formula_worker import payload_text
from parsers.mathematics.raster_worker import (
    model_fingerprint,
    protected_math_region,
    source_fidelity_status,
)


def component(text, y, *, kind="text", x=20, line=0, score=0.99):
    result = {
        "text": text,
        "type": kind,
        "line_number": line,
        "score": score,
        "position": [[x, y], [x + 80, y], [x + 80, y + 20], [x, y + 20]],
    }
    if kind != "text":
        result["verification"] = {"latex": text, "score": score}
    return result


def test_formula_worker_extracts_latex_not_source_path():
    result = {
        "res": {
            "input_path": "source-crop.png",
            "formula_res_list": [{"rec_formula": r"n^{\frac{1}{17}}"}],
        }
    }

    assert payload_text(result) == r"n^{\frac{1}{17}}"


def test_fingerprint_includes_secondary_formula_model_weights(tmp_path):
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"
    primary.mkdir()
    secondary.mkdir()
    (primary / "model.onnx").write_bytes(b"primary")
    weights = secondary / "inference.pdiparams"
    weights.write_bytes(b"first")

    before = model_fingerprint(primary, [secondary])
    weights.write_bytes(b"second")

    assert model_fingerprint(primary, [secondary]) != before


@pytest.fixture
def evidence():
    asset = {
        "id": "source",
        "path": "source.png",
        "sha256": "source-hash",
        "role": "source_preview",
        "bbox": [10, 20, 310, 320],
        "pixel_size": [600, 600],
        "page": 2,
    }
    question = {
        "id": "stable_q001",
        "question_number": 1,
        "content": [{"type": "unresolved_math"}],
        "options": [],
        "raw": {"native_text": "1.", "glyph_ids": ["p2_g0"]},
        "assets": [asset, {**asset, "id": "raster", "role": "body"}],
        "issues": [
            {"code": "option_boundary"},
            {
                "code": "raster_math_unverified",
                "method": "source_raster_text_preservation",
            },
        ],
    }
    items = [
        component("1.", 0),
        component("Evaluate", 50, line=1),
        component(r"\sqrt{\frac{x^{2}+1}{3}}", 50, kind="embedding", x=110, line=1),
    ]
    for index, label in enumerate("ABCDE", 2):
        items.extend(
            [
                component(f"({label})", 100 + index * 50, line=index),
                component(
                    r"\frac{1}{2}",
                    100 + index * 50,
                    kind="embedding",
                    x=110,
                    line=index,
                ),
            ]
        )
    for item in items:
        item["independent_source_verification"] = {
            "passed": True,
            "method": "fixture_source_review",
        }
        if item["type"] in {"embedding", "isolated"}:
            item["round_trip_verification"] = {
                "passed": True,
                "method": "fixture_calibrated_round_trip",
            }
    result = {
        "source_sha256": "source-hash",
        "implementation_sha256": "model-hash",
        "method": "local_pix2text_text_formula_layout",
        "recognitions": items,
        "figures": [],
        "warnings": [],
    }
    return question, asset, result


def crop(page, box, role, question, option=None):
    return {
        "id": f"{role}_{option}_{box}",
        "page": page,
        "bbox": box,
        "role": role,
        "option_label": option,
        "path": "component.png",
    }


def test_only_existing_whole_raster_issue_questions_are_eligible(evidence):
    q, _, _ = evidence
    assert eligible(q)
    q["issues"] = []
    assert not eligible(q)
    q["issues"] = [
        {"code": "raster_math_unverified", "method": "source_visual_preservation"}
    ]
    assert not eligible(q)  # separate formula imagery is a different root cause


def test_text_math_and_options_replace_whole_screenshot_without_mutating_input(
    evidence,
):
    q, a, result = evidence
    before = copy.deepcopy(q)
    out = assemble(q, a, result, crop)
    assert q == before
    assert out["id"] == q["id"] and out["raw"]["native_text"] == "1."
    assert out["raw"]["glyph_ids"] == ["p2_g0"]
    assert [o["label"] for o in out["options"]] == list("ABCDE")
    assert [b["type"] for b in out["content"]] == ["text", "math"]
    assert out["content"][1]["latex"] == r"\sqrt{\frac{x^{2}+1}{3}}"
    assert all(o["content"][0]["type"] == "math" for o in out["options"])
    assert not out["issues"]
    assert out["assets"][1]["role"] == "source_raster_evidence"
    assert not any(
        "(A)" in b.get("text", b.get("latex", ""))
        for o in out["options"]
        for b in o["content"]
    )


def test_disagreeing_formula_retains_component_issue_not_invented_latex(evidence):
    q, a, result = evidence
    result["recognitions"][4]["verification"]["latex"] = r"\frac{2}{3}"
    out = assemble(q, a, result, crop)
    assert out["options"][0]["content"][0]["type"] == "unresolved_math"
    assert "disagree" in out["issues"][0]["reason"]
    assert out["issues"][0]["option_label"] == "A"
    assert out["issues"][0]["field"] == "option"


def test_low_confidence_text_is_not_silently_accepted(evidence):
    q, a, result = evidence
    result["recognitions"][1]["score"] = 0.5
    out = assemble(q, a, result, crop)
    assert out["content"][0]["type"] == "unresolved_math"
    assert "confidence" in out["issues"][0]["reason"]


def test_genuine_visual_is_separate_and_before_source_text(evidence):
    q, a, result = evidence
    result["figures"] = [
        {"position": [[10, 25], [190, 45]], "type": "visual", "score": 0.99}
    ]
    out = assemble(q, a, result, crop)
    assert [b["type"] for b in out["content"]] == ["visual", "text", "math"]
    assert out["content"][0]["asset_id"] != "source"
    assert out["content"][0]["source"]["bbox"] == [15, 32.5, 105, 42.5]


def test_source_hash_and_complete_option_run_are_required(evidence):
    q, a, result = evidence
    result["source_sha256"] = "wrong"
    with pytest.raises(ValueError, match="does not match"):
        assemble(q, a, result, crop)
    result["source_sha256"] = a["sha256"]
    result["recognitions"] = result["recognitions"][:-2]
    with pytest.raises(ValueError, match="option-label run"):
        assemble(q, a, result, crop)


def test_side_by_side_body_visual_does_not_become_an_answer(evidence):
    q, a, result = evidence
    result["figures"] = [
        {"position": [[300, 45], [500, 500]], "type": "visual", "score": 0.99}
    ]
    out = assemble(q, a, result, crop)
    assert any(b["type"] == "visual" for b in out["content"])
    assert not any(b["type"] == "visual" for o in out["options"] for b in o["content"])


def test_genuine_answer_visual_stays_in_its_option(evidence):
    q, a, result = evidence
    result["figures"] = [
        {"position": [[300, 355], [500, 385]], "type": "visual", "score": 0.99}
    ]
    out = assemble(q, a, result, crop)
    assert not any(b["type"] == "visual" for b in out["content"])
    assert [
        o["label"]
        for o in out["options"]
        if any(b["type"] == "visual" for b in o["content"])
    ] == ["D"]


def test_formatting_normalization_does_not_change_math():
    first = normalize_latex(r"6 0 m \biggl(\frac{a}{b}\biggr)")
    second = normalize_latex(r"60m\left(\frac{a}{b}\right)")
    assert formula_signature(first) == formula_signature(second)
    assert formula_signature(r"\frac{a}{b}") != formula_signature(r"\frac{b}{a}")
    assert formula_signature("x^{2}") != formula_signature("x_{2}")


def test_independent_literal_read_can_confirm_single_scalar_but_not_expression(
    evidence,
):
    q, a, result = evidence
    scalar = result["recognitions"][2]
    scalar.update(
        text="a",
        verification={"latex": "{}^{a}", "score": 0.99},
        literal_verification={"text": "a", "score": 0.99},
    )
    out = assemble(q, a, result, crop)
    assert out["content"][1]["type"] == "math"
    scalar["text"] = "a+b"
    with_expression = assemble(q, a, result, crop)
    assert with_expression["content"][1]["type"] == "unresolved_math"


def test_source_line_breaks_are_stored_in_json(evidence):
    q, a, result = evidence
    next_line = component("Next line", 80, line=1.5)
    next_line["independent_source_verification"] = {
        "passed": True,
        "method": "fixture_source_review",
    }
    result["recognitions"].insert(3, next_line)
    out = assemble(q, a, result, crop)
    assert out["content"][-1]["text"] == "Next line"
    assert out["content"][-1]["break_before"] is True


def test_layout_figure_must_not_swallow_radicals_or_option_list():
    box = [[0, 0], [100, 0], [100, 100], [0, 100]]
    radical = {"box": [[10, 10], [90, 10], [90, 50], [10, 50]]}
    assert protected_math_region(box, [radical], [])
    marker = component("(A) expression", 10)
    assert protected_math_region(box, [], [marker])
    # A small axis label is not sufficient to turn a genuine graph into text.
    tiny = {"box": [[10, 10], [12, 10], [12, 12], [10, 12]]}
    assert not protected_math_region(box, [tiny], [])


def test_legacy_nested_root_encoding_preserves_every_observed_index():
    assert (
        normalize_latex(r"\root5 \of{\root4 \of{\root3 \of{\root n}}}=")
        == r"\sqrt[5]{\sqrt[4]{\sqrt[3]{\sqrt{n}}}}="
    )
    assert (
        normalize_latex(r"\root3 n") == r"\root3 n"
    )  # missing grouping is not invented


def test_question_number_mask_uses_source_anchor_and_refuses_touching_formula():
    code = r"""
import importlib.util,sys
from PIL import Image,ImageDraw
s=importlib.util.spec_from_file_location('worker',sys.argv[1]); w=importlib.util.module_from_spec(s); s.loader.exec_module(w)
image=Image.new('RGB',(120,100),'white'); d=ImageDraw.Draw(image); d.rectangle((8,8,17,25),fill='black'); d.rectangle((38,30,100,31),fill='black')
masked,evidence,warnings=w.isolate_question_number(image,[{'bbox':[7,7,19,27],'text':'7','glyph_id':'p2_g0'}])
assert not warnings and evidence[0]['glyph_id']=='p2_g0' and masked.getpixel((10,10))==(255,255,255) and image.getpixel((10,10))==(0,0,0)
touching=Image.new('RGB',(120,100),'white'); ImageDraw.Draw(touching).line((8,20,40,20),fill='black',width=1)
_,evidence,warnings=w.isolate_question_number(touching,[{'bbox':[7,7,19,27],'text':'7'}])
assert not evidence and 'touches adjacent' in warnings[0]
print('ok')
"""
    root = Path(__file__).resolve().parents[1]
    python = root / ".venv-math-ocr/Scripts/python.exe"
    if not python.is_file():
        pytest.skip("Optional local OCR environment not installed")
    subprocess.run(
        [str(python), "-c", code, str(root / "parsers/mathematics/raster_worker.py")],
        check=True,
        capture_output=True,
        timeout=30,
    )


def test_component_ownership_tracks_unassigned_and_number_ink():
    code = r"""
import importlib.util,sys
from PIL import Image,ImageDraw
s=importlib.util.spec_from_file_location('worker',sys.argv[1]); w=importlib.util.module_from_spec(s); s.loader.exec_module(w)
image=Image.new('L',(100,60),'white'); d=ImageDraw.Draw(image)
d.rectangle((5,5,15,20),fill=0); d.rectangle((30,30,50,40),fill=0); d.rectangle((80,50,85,55),fill=0)
regions=[{'position':[[4,4],[16,4],[16,21],[4,21]]},{'position':[[29,29],[51,29],[51,41],[29,41]]}]
ownership=w.component_ownership(image,regions,[],[])
assert ownership['component_count']==3 and ownership['unassigned_significant_count']==1
assert ownership['assigned_ink_fraction']<1
print('ok')
"""
    root = Path(__file__).resolve().parents[1]
    python = root / ".venv-math-ocr/Scripts/python.exe"
    if not python.is_file():
        pytest.skip("Optional local OCR environment not installed")
    subprocess.run(
        [str(python), "-c", code, str(root / "parsers/mathematics/raster_worker.py")],
        check=True,
        capture_output=True,
        timeout=30,
    )


def test_fidelity_gate_never_accepts_valid_latex_without_visual_evidence():
    labels = [{"text": f"({letter})", "type": "text"} for letter in "ABCDE"]
    content = [{"text": r"\sqrt{x}", "type": "embedding"}]
    ownership = {"assigned_ink_fraction": 1.0, "unassigned_significant_count": 0}
    result = source_fidelity_status(content + labels, labels, [{}], [], [], ownership)
    assert result["status"] == "needs_review"
    assert any("render-back" in reason for reason in result["blockers"])
    content[0]["independent_source_verification"] = {"passed": True}
    content[0]["round_trip_verification"] = {"passed": True}
    result = source_fidelity_status(content + labels, labels, [{}], [], [], ownership)
    assert result["status"] == "verified"


def test_infinity_number_ambiguity_remains_a_component_issue(evidence):
    q, a, result = evidence
    result["recognitions"][4].update(
        text=r"n^{\frac{1}{\infty}}",
        verification={"latex": r"n^{\frac{1}{\infty}}", "score": 0.99},
    )
    out = assemble(q, a, result, crop)
    assert out["options"][0]["content"][0]["type"] == "unresolved_math"
    assert "small digit" in out["issues"][0]["reason"]


def test_real_connected_components_keep_fraction_extents_and_inequality_rows():
    root = Path(__file__).resolve().parents[1]
    python = root / ".venv-math-ocr/Scripts/python.exe"
    if not python.is_file():
        pytest.skip("Optional local OCR environment not installed")
    code = r"""
import importlib.util,json,sys
from PIL import Image,ImageDraw
s=importlib.util.spec_from_file_location('worker',sys.argv[1]); w=importlib.util.module_from_spec(s); s.loader.exec_module(w)
image=Image.new('L',(150,420),'white'); d=ImageDraw.Draw(image)
labels=[{'text':'('+c+')','x':5,'y':100+i*60,'width':20,'height':20} for i,c in enumerate('ABCDE')]
for i in range(5):
    y=100+i*60
    d.rectangle((44,y-25,50,y-12),fill=0); d.rectangle((40,y,65,y+1),fill=0); d.rectangle((44,y+10,50,y+23),fill=0)
regions=w.option_regions(image,labels)
assert regions[0][1][1]==73 and regions[1][1][1]==133
assert regions[0][1][3]==126 and regions[1][1][3]==186
number=Image.new('L',(80,25),'white'); n=ImageDraw.Draw(number)
for x in (5,20): n.rectangle((x,4,x+7,20),fill=0)
assert w.plain_number(number,{'text':'60','score':0.99})
assert not w.plain_number(number,{'text':'6','score':0.99})
print(json.dumps({'fraction_bounds':True,'extra_glyph_protection':True}))
"""
    result = subprocess.run(
        [str(python), "-c", code, str(root / "parsers/mathematics/raster_worker.py")],
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert json.loads(result.stdout)["fraction_bounds"]
