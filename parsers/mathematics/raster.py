"""Recover only issue-bearing raster questions into the existing RAW contract.

The optional worker is local and offline. Its candidates are syntax checked and
formula re-reads must agree before a mathematical block is accepted. Native RAW
glyphs, source previews, IDs, keys and unselected questions remain unchanged.
"""

import argparse
import copy
import json
import re
import subprocess
import tempfile
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree as ET

from .latex import mathml, validate
from .raster_worker import model_fingerprint
from .source import Assets, validate_raw


def label_evidence(asset):
    """Build a source-backed A–E sequence from independent layout passes.

    Missing labels are never synthesized. When four labels establish a regular
    row/column, the predicted fifth location is re-read from the original crop
    at several scales and accepted only if OCR observes that literal label.
    """
    from PIL import Image

    from .ocr import calibrated_labels, recognize

    candidates = []
    for layout in (6, 11, 12, 4):
        try:
            data = recognize(asset["path"], layout)
        except (OSError, ValueError, subprocess.SubprocessError):
            continue
        for word in data.get("words", []):
            match = re.fullmatch(r"\(?([A-E])\)?[.)]?", word["text"].strip())
            if match:
                candidates.append(
                    {**word, "text": match[1], "evidence": f"tesseract_psm_{layout}"}
                )
    try:
        candidates.extend(calibrated_labels(asset["path"]))
    except (OSError, ValueError, subprocess.SubprocessError):
        pass

    def centers(words):
        return [(w["x"] + w["width"] / 2, w["y"] + w["height"] / 2) for w in words]

    # Merge repeated observations at the same location while retaining the
    # strongest independent text observation and its source coordinates.
    unique = []
    for word in sorted(candidates, key=lambda w: w.get("confidence", 0), reverse=True):
        if not word.get("width") or not word.get("height"):
            continue
        cx, cy = centers([word])[0]
        if any(
            old["text"] == word["text"]
            and abs(cx - (old["x"] + old["width"] / 2))
            < max(word["height"], old["height"])
            and abs(cy - (old["y"] + old["height"] / 2))
            < max(word["height"], old["height"])
            for old in unique
        ):
            continue
        unique.append(word)

    def sequence(words):
        if len({w["text"] for w in words}) != 5:
            return False
        points = centers(words)
        xspan = max(p[0] for p in points) - min(p[0] for p in points)
        yspan = max(p[1] for p in points) - min(p[1] for p in points)
        # Choose the dominant reading axis; require direct A–E evidence at
        # distinct, monotonically ordered source locations.
        ordered = (
            sorted(words, key=lambda w: (w["x"] + w["width"] / 2, w["y"]))
            if xspan > yspan * 1.4
            else sorted(words, key=lambda w: (w["y"] + w["height"] / 2, w["x"]))
        )
        return [w["text"] for w in ordered] == list("ABCDE")

    by_label = {
        letter: [w for w in unique if w["text"] == letter] for letter in "ABCDE"
    }
    if all(by_label.values()):
        best = [
            max(by_label[letter], key=lambda w: w.get("confidence", 0))
            for letter in "ABCDE"
        ]
        if sequence(best):
            return sorted(best, key=lambda w: (w["y"], w["x"]))

    # Infer one missing slot only from at least four directly observed labels
    # with a low-residual linear layout; OCR at the predicted location must
    # independently read the missing literal label.
    missing = [letter for letter in "ABCDE" if not by_label[letter]]
    present = [letter for letter in "ABCDE" if by_label[letter]]
    if len(missing) == 1 and len(present) >= 4:
        observed = [
            max(by_label[c], key=lambda w: w.get("confidence", 0)) for c in present
        ]
        points = centers(observed)
        xspan = max(p[0] for p in points) - min(p[0] for p in points)
        yspan = max(p[1] for p in points) - min(p[1] for p in points)
        axis = 0 if xspan > yspan * 1.4 else 1
        values = [p[axis] for p in points]
        indices = ["ABCDE".index(c) for c in present]
        mean_i, mean_v = sum(indices) / len(indices), sum(values) / len(values)
        slope = sum(
            (i - mean_i) * (v - mean_v) for i, v in zip(indices, values, strict=True)
        ) / sum((i - mean_i) ** 2 for i in indices)
        residual = max(
            abs(v - (mean_v + slope * (i - mean_i)))
            for i, v in zip(indices, values, strict=True)
        )
        median_size = sorted(w["height"] for w in observed)[len(observed) // 2]
        if abs(slope) >= median_size * 0.8 and residual <= median_size * 0.45:
            target_i = "ABCDE".index(missing[0])
            target_axis = mean_v + slope * (target_i - mean_i)
            other_axis = sum(p[1 - axis] for p in points) / len(points)
            half = max(2, median_size * 0.9)
            with tempfile.TemporaryDirectory(prefix="math-label-target-") as temp:
                path = Path(temp) / "target.png"
                with Image.open(asset["path"]) as image:
                    cx, cy = (
                        (target_axis, other_axis)
                        if axis == 0
                        else (other_axis, target_axis)
                    )
                    box = (
                        max(0, round(cx - half)),
                        max(0, round(cy - half)),
                        min(image.width, round(cx + half)),
                        min(image.height, round(cy + half)),
                    )
                    image.crop(box).resize(
                        (max(20, (box[2] - box[0]) * 3), max(20, (box[3] - box[1]) * 3))
                    ).save(path)
                try:
                    targeted = recognize(path, 6).get("words", [])
                except (OSError, ValueError, subprocess.SubprocessError):
                    targeted = []
            direct = next(
                (
                    w
                    for w in targeted
                    if re.fullmatch(rf"\(?{missing[0]}\)?[.)]?", w["text"].strip())
                ),
                None,
            )
            if direct:
                synthesized = {
                    "text": missing[0],
                    "x": box[0] + direct["x"] / 3,
                    "y": box[1] + direct["y"] / 3,
                    "width": direct["width"] / 3,
                    "height": direct["height"] / 3,
                    "confidence": direct.get("confidence", 0),
                    "evidence": "targeted_ocr_direct_read",
                    "targeted_read": True,
                }
                chosen = [*observed, synthesized]
                if sequence(chosen):
                    return sorted(chosen, key=lambda w: (w["y"], w["x"]))
    return sorted(unique, key=lambda w: (w["y"], w["x"]))


def question_number_mask(question, asset, pages):
    """Map the existing printed-number glyph anchor into source-preview pixels."""
    import re

    page = next((p for p in pages if p["page"] == asset["page"]), None)
    if not page:
        return _ocr_question_number_anchor(question, asset)
    glyphs = {g["id"]: g for g in page.get("glyphs", [])}
    source = [
        glyphs[g] for g in question.get("raw", {}).get("glyph_ids", []) if g in glyphs
    ]
    expected = str(question["question_number"])
    prefix = "".join(g["text"] for g in source if g["text"].strip())
    match = re.match(rf"^\s*{re.escape(expected)}[.)]?", prefix)
    if not match:
        return _ocr_question_number_anchor(question, asset)
    number_chars = match[0].strip()
    selected, consumed = [], ""
    for glyph in source:
        char = glyph["text"].strip()
        if not char:
            continue
        if len(consumed) >= len(number_chars):
            break
        if char != number_chars[len(consumed)]:
            return _ocr_question_number_anchor(question, asset)
        consumed += char
        sx = asset["pixel_size"][0] / (asset["bbox"][2] - asset["bbox"][0])
        sy = asset["pixel_size"][1] / (asset["bbox"][3] - asset["bbox"][1])
        selected.append(
            {
                "bbox": [
                    (glyph["x0"] - asset["bbox"][0]) * sx,
                    (glyph["top"] - asset["bbox"][1]) * sy,
                    (glyph["x1"] - asset["bbox"][0]) * sx,
                    (glyph["bottom"] - asset["bbox"][1]) * sy,
                ],
                "text": char,
                "glyph_id": glyph["id"],
            }
        )
    return (
        selected
        if consumed == number_chars and selected
        else _ocr_question_number_anchor(question, asset)
    )


def _ocr_question_number_anchor(question, asset):
    """Image-only fallback: recognize the expected printed anchor by geometry."""
    from .ocr import recognize

    width, height = asset["pixel_size"]
    candidates = []
    expected = str(question["question_number"])
    for layout in (6, 11, 12):
        try:
            words = recognize(asset["path"], layout).get("words", [])
        except (OSError, ValueError, subprocess.SubprocessError):
            continue
        for word in words:
            token = word["text"].strip()
            if (
                re.fullmatch(rf"{re.escape(expected)}[.)]", token)
                and word["x"] < width * 0.22
                and word["y"] < height * 0.25
            ):
                candidates.append(word)
    if not candidates:
        return []
    candidates.sort(key=lambda word: word.get("confidence", 0), reverse=True)
    best = candidates[0]
    if len(candidates) > 1:
        second = candidates[1]
        if (
            abs(best["x"] - second["x"]) > best["height"]
            or abs(best["y"] - second["y"]) > best["height"]
        ):
            return []
    return [
        {
            "bbox": [
                best["x"],
                best["y"],
                best["x"] + best["width"],
                best["y"] + best["height"],
            ],
            "text": expected,
            "glyph_id": None,
            "anchor_method": "local_ocr_top_left_exact_number_and_punctuation",
        }
    ]


def run_renderback(selected, cache, fingerprint, ocr_python, node):
    """Render candidate MathML locally and attach source-shape diagnostics."""
    from PIL import Image

    root = cache / "roundtrip"
    source_dir = root / "source_crops"
    source_dir.mkdir(parents=True, exist_ok=True)
    manifest_entries, targets = [], {}
    for path, _, question, asset in selected:
        candidate_path = cache / f"{asset['sha256']}_{fingerprint[:16]}.json"
        if not candidate_path.is_file():
            continue
        candidate = json.loads(candidate_path.read_text(encoding="utf8"))
        for index, item in enumerate(candidate.get("recognitions", [])):
            if item.get("type") not in {"embedding", "isolated"}:
                continue
            ident = f"{asset['sha256']}_{index:03}"
            points = item["position"]
            x0 = max(0, int(min(p[0] for p in points) - 4))
            y0 = max(0, int(min(p[1] for p in points) - 4))
            x1 = min(asset["pixel_size"][0], int(max(p[0] for p in points) + 5))
            y1 = min(asset["pixel_size"][1], int(max(p[1] for p in points) + 5))
            source_path = source_dir / f"{ident}.png"
            with Image.open(asset["path"]) as image:
                image.crop((x0, y0, x1, y1)).save(source_path)
            try:
                rendered_mathml = mathml(normalize_latex(item["text"]))
            except (ValueError, ET.ParseError) as error:
                item["round_trip_verification"] = {
                    "passed": False,
                    "reason": f"Candidate cannot be rendered as supported MathML: {error}",
                }
                candidate_path.write_text(
                    json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf8",
                )
                continue
            manifest_entries.append(
                {
                    "id": ident,
                    "mathml": rendered_mathml,
                    "source_path": str(source_path),
                }
            )
            targets[ident] = (candidate_path, candidate, index, item)
    if not manifest_entries:
        return
    manifest = root / f"renderback_{fingerprint[:16]}.json"
    manifest.write_text(
        json.dumps(manifest_entries, ensure_ascii=False), encoding="utf8"
    )
    output = root / f"results_{fingerprint[:16]}.json"
    try:
        subprocess.run(
            [
                str(ocr_python.resolve()),
                str(Path(__file__).with_name("raster_render_worker.py")),
                "--manifest",
                str(manifest),
                "--output",
                str(output),
                "--node",
                str(node.resolve()),
            ],
            check=True,
            timeout=240,
        )
        comparisons = json.loads(output.read_text(encoding="utf8"))
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        for _, candidate, _, item in targets.values():
            item["round_trip_verification"] = {
                "passed": False,
                "reason": f"Offline render-back failed: {error}",
            }
        for candidate_path, candidate, _, _ in targets.values():
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf8",
            )
        return
    for comparison in comparisons:
        target = targets.get(comparison["id"])
        if not target:
            continue
        candidate_path, candidate, index, item = target
        item["round_trip_verification"] = comparison["round_trip_verification"]
        item["round_trip_verification"]["rendered_asset"] = comparison["rendered_path"]
        item["round_trip_verification"]["source_asset"] = comparison["source_path"]
        candidate["recognitions"][index] = item
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )


def run_secondary_formula_reads(selected, cache, fingerprint, python, model_dir):
    """Run PP-FormulaNet only on math candidates, in its isolated local runtime."""
    from PIL import Image

    output_root = cache / "secondary"
    crops = output_root / "source_crops"
    crops.mkdir(parents=True, exist_ok=True)
    manifest_entries, targets = [], {}
    for _, _, _, asset in selected:
        candidate_path = cache / f"{asset['sha256']}_{fingerprint[:16]}.json"
        if not candidate_path.is_file():
            continue
        candidate = json.loads(candidate_path.read_text(encoding="utf8"))
        for index, item in enumerate(candidate.get("recognitions", [])):
            if item.get("type") not in {"embedding", "isolated"}:
                continue
            ident = f"{asset['sha256']}_{index:03}"
            points = item["position"]
            x0 = max(0, int(min(p[0] for p in points) - 5))
            y0 = max(0, int(min(p[1] for p in points) - 5))
            x1 = min(asset["pixel_size"][0], int(max(p[0] for p in points) + 6))
            y1 = min(asset["pixel_size"][1], int(max(p[1] for p in points) + 6))
            source_path = crops / f"{ident}.png"
            with Image.open(asset["path"]) as image:
                image.crop((x0, y0, x1, y1)).save(source_path)
            manifest_entries.append({"id": ident, "path": str(source_path)})
            targets[ident] = (candidate_path, candidate, index, item)
    if not manifest_entries:
        return
    manifest = output_root / f"manifest_{fingerprint[:16]}.json"
    output = output_root / f"results_{fingerprint[:16]}.json"
    manifest.write_text(
        json.dumps(manifest_entries, ensure_ascii=False), encoding="utf8"
    )
    subprocess.run(
        [
            str(python.resolve()),
            str(Path(__file__).with_name("raster_formula_worker.py")),
            "--manifest",
            str(manifest),
            "--model-dir",
            str(model_dir.resolve()),
            "--output",
            str(output),
        ],
        check=True,
        timeout=900,
    )
    for observation in json.loads(output.read_text(encoding="utf8")):
        target = targets.get(observation["id"])
        if not target:
            continue
        candidate_path, candidate, index, item = target
        readings = observation.get("recognized_latex", [])
        comparisons = []
        for latex in readings:
            try:
                comparisons.append(
                    formula_signature(normalize_latex(latex))
                    == formula_signature(normalize_latex(item["text"]))
                )
            except (ValueError, ET.ParseError):
                comparisons.append(False)
        item["independent_source_verification"] = {
            "passed": bool(readings) and all(comparisons),
            "method": "PaddleOCR_PP-FormulaNet_plus-S_local",
            "model": "PP-FormulaNet_plus-S",
            "recognized_latex": readings,
            "same_structure_as_primary": comparisons,
        }
        candidate["recognitions"][index] = item
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )


def run_independent_text_reads(selected, cache, fingerprint):
    """Cross-check text regions with local Tesseract on their exact source boxes."""
    import difflib
    import unicodedata

    from PIL import Image

    from .ocr import recognize

    evidence_root = cache / "independent_text"
    evidence_root.mkdir(parents=True, exist_ok=True)
    for _, _, _, asset in selected:
        candidate_path = cache / f"{asset['sha256']}_{fingerprint[:16]}.json"
        if not candidate_path.is_file():
            continue
        candidate = json.loads(candidate_path.read_text(encoding="utf8"))
        changed = False
        for index, item in enumerate(candidate.get("recognitions", [])):
            if item.get("type") != "text" or re.fullmatch(
                r"\(?[A-E]\)?[.)]?", item.get("text", "").strip()
            ):
                continue
            points = item["position"]
            x0 = max(0, int(min(p[0] for p in points) - 2))
            y0 = max(0, int(min(p[1] for p in points) - 2))
            x1 = min(asset["pixel_size"][0], int(max(p[0] for p in points) + 3))
            y1 = min(asset["pixel_size"][1], int(max(p[1] for p in points) + 3))
            crop_path = evidence_root / f"{asset['sha256']}_{index:03}.png"
            with Image.open(asset["path"]) as image:
                image.crop((x0, y0, x1, y1)).save(crop_path)
            try:
                words = recognize(crop_path, 6).get("words", [])
                observed = " ".join(word["text"].strip() for word in words).strip()
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                observed = ""
                reason = str(error)
            else:
                reason = None
            expected = " ".join(unicodedata.normalize("NFKC", item["text"]).split())
            actual = " ".join(unicodedata.normalize("NFKC", observed).split())
            similarity = difflib.SequenceMatcher(
                None, expected.casefold(), actual.casefold()
            ).ratio()
            item["independent_source_verification"] = {
                "passed": bool(expected) and expected.casefold() == actual.casefold(),
                "method": "local_tesseract_region_read_exact_text_agreement",
                "independent_text": observed,
                "normalized_similarity": similarity,
                "reason": reason
                or (
                    None
                    if expected.casefold() == actual.casefold()
                    else "Independent OCR text differs from primary candidate"
                ),
                "source_crop_path": str(crop_path.resolve()),
            }
            candidate["recognitions"][index] = item
            changed = True
        if changed:
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf8",
            )


def update_candidate_fidelity(candidate):
    """Recompute acceptance after independent reads and visual comparison."""
    labels = [
        re.sub(r"[^A-E]", "", item.get("text", "").strip())
        for item in candidate.get("recognitions", [])
        if item.get("type") == "text"
        and re.fullmatch(r"\(?[A-E]\)?[.)]?", item.get("text", "").strip())
    ]
    blockers = []
    if labels != list("ABCDE"):
        blockers.append("A–E labels lack a unique, direct source-backed sequence")
    geometry = candidate.get("source_geometry", {})
    ownership = geometry.get("component_ownership", {})
    if not geometry.get("question_number_masks"):
        blockers.append("printed question number has no safe source mask")
    if ownership.get("unassigned_significant_count", 0):
        blockers.append("significant source components remain unassigned")
    if candidate.get("warnings"):
        blockers.extend(candidate["warnings"])
    content = [
        item
        for item in candidate.get("recognitions", [])
        if not re.fullmatch(r"\(?[A-E]\)?[.)]?", item.get("text", "").strip())
    ]
    for item in content:
        if not item.get("independent_source_verification", {}).get("passed"):
            blockers.append(
                "primary and independent recognizers do not confirm every content region"
            )
        if item.get("type") in {"embedding", "isolated"}:
            visual = item.get("round_trip_verification", {})
            if not visual.get("passed"):
                blockers.append(
                    visual.get(
                        "reason",
                        "source-vs-rendered formula comparison is not calibrated/passing",
                    )
                )
    candidate["source_fidelity"] = {
        "status": "unresolved"
        if any("A–E" in b or "unassigned" in b for b in blockers)
        else "needs_review"
        if blockers
        else "verified",
        "blockers": list(dict.fromkeys(blockers)),
        "option_label_sequence": labels,
        "content_region_count": len(content),
        "independently_verified_content_count": sum(
            item.get("independent_source_verification", {}).get("passed", False)
            for item in content
        ),
    }


def eligible(question):
    return not question["options"] and any(
        i["code"] == "raster_math_unverified"
        and i.get("method") == "source_raster_text_preservation"
        for i in question["issues"]
    )


def rectangle(position):
    return [
        min(p[0] for p in position),
        min(p[1] for p in position),
        max(p[0] for p in position),
        max(p[1] for p in position),
    ]


def formula_signature(latex):
    """Ignore presentation-only grouping/spacing, never mathematical structure."""
    root = ET.fromstring(mathml(latex))

    def visit(node):
        tag = node.tag.split("}")[-1]
        if tag in {"math", "mrow"}:
            return tuple(x for child in node for x in visit(child))
        if not len(node):
            text = (node.text or "").strip()
            return ((tag, text),) if text else ()
        return ((tag, tuple(visit(child) for child in node)),)

    # Whitespace in generated LaTeX between consecutive digits is not a
    # multiplication sign; the source recognizer routinely emits "6 0".
    return visit(root)


def normalize_latex(latex):
    """Formatting only: delimiter sizes and whitespace between printed digits."""
    value = re.sub(r"\\(?:bigg|Bigg|big|Big)[lr]?\b", "", latex)
    value = re.sub(r"(?<=\d)\s+(?=\d)", "", value).strip()
    value = re.sub(r"\\(?:dfrac|tfrac)\b", r"\\frac", value)
    value = re.sub(r"\\(?:displaystyle|textstyle)\b", "", value)
    # Pix2Text's legacy root tokens are an OCR encoding, not a solution method.
    # Explicit indices are retained. Ambiguous numeric roots without \\of stay
    # unsupported instead of guessing a missing index/operand.
    for match in reversed(list(re.finditer(r"\\root(?![A-Za-z])", value))):
        start = match.end()
        tail = value[start:]
        index = re.match(r"\s*([0-9]+|[A-Za-z])\s*\\of\s*", tail)
        if index:
            arg = start + index.end()
            if arg < len(value) and value[arg] == "{":
                depth, end = 1, arg + 1
                while end < len(value) and depth:
                    depth += (value[end] == "{") - (value[end] == "}")
                    end += 1
                if not depth:
                    value = (
                        value[: match.start()]
                        + r"\sqrt["
                        + index[1]
                        + "]"
                        + value[arg:end]
                        + value[end:]
                    )
        else:
            atom = re.match(r"\s+([A-Za-z])(?=\s*[^A-Za-z]|$)", tail)
            if atom:
                value = (
                    value[: match.start()]
                    + r"\sqrt{"
                    + atom[1]
                    + "}"
                    + value[start + atom.end() :]
                )
    return value


def numeric_source(value, asset, position):
    """Validate a literal number's sign/separators against original source ink.

    No arithmetic is performed. Digit identities still come from recognition;
    geometry only prevents dropped signs and comma/decimal substitutions.
    """
    from PIL import Image

    literal = re.sub(
        r"\\(?:mathrm|mathit|mathbf|text)|\\[,!; ]|[{}\s]", "", value
    ).replace("−", "-")
    if not re.fullmatch(r"[-+]?\d+(?:[,.]\d+)*", literal):
        return value, None, None
    rectangle_px = rectangle(position)
    with Image.open(asset["path"]) as original:
        image = original.convert("L").crop(tuple(round(v) for v in rectangle_px))
    pixels = image.point(lambda p: 1 if p < 175 else 0).load()
    seen, boxes = set(), []
    for y in range(image.height):
        for x in range(image.width):
            if not pixels[x, y] or (x, y) in seen:
                continue
            todo, points = [(x, y)], []
            seen.add((x, y))
            while todo:
                a, b = todo.pop()
                points.append((a, b))
                for u in range(max(0, a - 1), min(image.width, a + 2)):
                    for v in range(max(0, b - 1), min(image.height, b + 2)):
                        if pixels[u, v] and (u, v) not in seen:
                            seen.add((u, v))
                            todo.append((u, v))
            boxes.append(
                [
                    min(p[0] for p in points),
                    min(p[1] for p in points),
                    max(p[0] for p in points) + 1,
                    max(p[1] for p in points) + 1,
                ]
            )
    if not boxes:
        return value, None, "Numeric recognition has no source ink"
    height = max(b[3] - b[1] for b in boxes)
    glyphs = sorted(
        [b for b in boxes if b[3] - b[1] >= height * 0.6], key=lambda b: b[0]
    )
    digits = re.sub(r"\D", "", literal)
    if len(glyphs) != len(digits):
        return (
            value,
            None,
            "Numeric digit count does not match complete source glyph components",
        )
    baseline = sorted(b[3] for b in glyphs)[len(glyphs) // 2]
    centers = [(b[1] + b[3]) / 2 for b in glyphs]
    minus = [
        b
        for b in boxes
        if b[3] - b[1] <= height * 0.25
        and b[2] - b[0] >= height * 0.35
        and b[2] <= glyphs[0][0] + 1
        and abs((b[1] + b[3]) / 2 - sum(centers) / len(centers)) < height * 0.3
    ]
    if literal.startswith("-") and not minus:
        return value, None, "Recognized numeric minus lacks a complete source sign"
    punctuation = [
        b
        for b in boxes
        if b not in glyphs
        and b not in minus
        and glyphs[0][0] < (b[0] + b[2]) / 2 < glyphs[-1][2]
    ]
    gaps = {}
    for b in punctuation:
        if b[3] - b[1] >= height * 0.6 or b[2] - b[0] >= height * 0.6:
            return (
                value,
                None,
                "Numeric source contains an unassigned mathematical component",
            )
        gap = sum((g[0] + g[2]) / 2 < (b[0] + b[2]) / 2 for g in glyphs)
        if gap in gaps:
            old = gaps[gap]
            gaps[gap] = [
                min(old[0], b[0]),
                min(old[1], b[1]),
                max(old[2], b[2]),
                max(old[3], b[3]),
            ]
        else:
            gaps[gap] = b
    separators = {}
    for gap, b in gaps.items():
        if b[3] < baseline - height * 0.25:
            return (
                value,
                None,
                "Numeric punctuation is above the decimal baseline and remains ambiguous",
            )
        separators[gap] = "," if b[3] > baseline + max(1, height * 0.04) else "."
    output = "-" if minus else "+" if literal.startswith("+") else ""
    for index, char in enumerate(digits, 1):
        output += char + separators.get(index, "")
    evidence = {
        "method": "source_numeric_sign_and_separator_geometry",
        "recognized": value,
        "source_pixel_bbox": rectangle_px,
        "digit_boxes": glyphs,
        "minus_boxes": minus,
        "separator_boxes": gaps,
    }
    return output, evidence, None


def assemble(question, asset, result, crop):
    """Map positioned OCR components to RAW blocks; no question-specific rules."""
    if result["source_sha256"] != asset["sha256"]:
        raise ValueError("Recognition evidence does not match source crop")
    q = copy.deepcopy(question)
    original_assets = {a["id"] for a in q["assets"]}
    q["content"], q["options"] = [], []
    q["issues"] = [
        i
        for i in q["issues"]
        if not (
            i["code"] == "option_boundary"
            or i["code"] == "raster_math_unverified"
            and i.get("method") == "source_raster_text_preservation"
        )
    ]

    def source(position):
        b = rectangle(position)
        pixel_box = list(b)
        sx = (asset["bbox"][2] - asset["bbox"][0]) / asset["pixel_size"][0]
        sy = (asset["bbox"][3] - asset["bbox"][1]) / asset["pixel_size"][1]
        b = [
            asset["bbox"][0] + b[0] * sx,
            asset["bbox"][1] + b[1] * sy,
            asset["bbox"][0] + b[2] * sx,
            asset["bbox"][1] + b[3] * sy,
        ]
        b = [
            max(asset["bbox"][0], b[0]),
            max(asset["bbox"][1], b[1]),
            min(asset["bbox"][2], b[2]),
            min(asset["bbox"][3], b[3]),
        ]
        if b[2] <= b[0] or b[3] <= b[1]:
            raise ValueError("Recognized component outside source crop")
        return {
            "page": asset["page"],
            "bbox": b,
            "method": result["method"],
            "source_asset_id": asset["id"],
            "recognition_sha256": result["implementation_sha256"],
            "source_pixel_bbox": pixel_box,
            "coordinate_transform": {
                "pdf_units_per_pixel": [sx, sy],
                "pixel_origin_pdf": asset["bbox"][:2],
            },
        }

    items = copy.deepcopy(result["recognitions"])
    component_map = result.get("source_geometry", {}).get("component_ownership", {})
    for item_index, item in enumerate(items):
        item["source_component_ids"] = [
            component["id"]
            for component in component_map.get("components", [])
            if component.get("owner_type") == "recognition"
            and component.get("owner_index") == item_index
        ]
    labels = []
    for item in items:
        label = re.fullmatch(r"\(?([A-E])\)?[.)]?", item["text"].strip())
        if item["type"] == "text" and label:
            labels.append((item, label[1]))
    if [label for _, label in labels] != list("ABCDE"):
        raise ValueError("OCR did not observe exactly one ordered A–E option-label run")
    label_ids = {id(item) for item, _ in labels}
    # Source label geometry, rather than vertical cuts through tall fractions,
    # establishes ownership. Components sharing a source line stay together.
    label_lines = {item["line_number"]: label for item, label in labels}
    options = {}
    for item, label in labels:
        option = {"label": label, "content": [], "source": source(item["position"])}
        options[label] = option
        q["options"].append(option)
    body_end = min(item["line_number"] for item, _ in labels)
    last_line = {}
    for item in items:
        if id(item) in label_ids:
            continue
        line = item["line_number"]
        value = item["text"].strip()
        if line < body_end and re.fullmatch(rf"{q['question_number']}[.)]?", value):
            continue
        preceding = [(n, label) for n, label in label_lines.items() if n <= line]
        label = max(preceding)[1] if preceding else None
        target = options[label]["content"] if label else q["content"]
        src = source(item["position"])
        src["recognition_line"] = line
        src["recognition_score"] = float(item["score"])
        src["source_component_ids"] = item.get("source_component_ids", [])
        problems = []
        is_formula = item["type"] in {"embedding", "isolated"}
        if is_formula:
            src["raw_latex"] = value
            value = normalize_latex(value)
            check = item.get("verification", {})
            verified_latex = normalize_latex(check.get("latex", ""))
            numeric, numeric_evidence, numeric_issue = numeric_source(
                value, asset, item["position"]
            )
            if numeric_issue:
                problems.append(numeric_issue)
            if numeric_evidence:
                src["numeric_source_verification"] = numeric_evidence
                if re.sub(r"\D", "", verified_latex) == re.sub(
                    r"\D", "", value
                ) and re.fullmatch(r"[\d+\-.,\s{}]+", verified_latex):
                    verified_latex = numeric
                value = numeric
            denominator = r"(\\frac\s*\{[^{}]+\}\s*\{)\s*\\infty\s*(\})"
            if re.search(denominator, value) or re.search(denominator, verified_latex):
                problems.append(
                    "Raster infinity token in a fraction denominator could not be independently distinguished from small digit glyphs"
                )
            problems.extend(validate(value))
            if not numeric_evidence and re.fullmatch(
                r"\s*[-+]?\s*\d+\s*\.\s*\d{3}\s*", value
            ):
                problems.append(
                    "Raster decimal/thousands separator lacks independent numeric-source verification"
                )
            literal = item.get("literal_verification", {})
            scalar_agreement = bool(
                re.fullmatch(r"[A-Za-z]|[0-9]+", value)
                and literal.get("text") == value
                and literal.get("score", 0) >= 0.95
            )
            if scalar_agreement:
                src["literal_verification"] = literal
            elif not check or validate(verified_latex):
                problems.append(
                    "Independent padded-source formula read is missing or invalid"
                )
            elif not problems and formula_signature(value) != formula_signature(
                verified_latex
            ):
                problems.append("Original and padded-source formula reads disagree")
            if min(float(item["score"]), float(check.get("score", 0))) < 0.80:
                problems.append("Formula recognition confidence below 0.80")
            secondary = item.get("independent_source_verification", {})
            if not secondary.get("passed"):
                problems.append(
                    "Independent PP-FormulaNet read is missing or differs from the primary formula"
                )
            round_trip = item.get("round_trip_verification", {})
            if not round_trip.get("passed"):
                problems.append(
                    round_trip.get(
                        "reason",
                        "Source-to-rendered formula comparison is not calibrated and passing",
                    )
                )
            src["verification"] = check
        else:
            number, evidence, numeric_issue = numeric_source(
                value, asset, item["position"]
            )
            if evidence:
                src["numeric_source_verification"] = evidence
                value = number
            if numeric_issue:
                problems.append(numeric_issue)
        if not is_formula and float(item["score"]) < 0.90:
            problems.append("Text recognition confidence below 0.90")
        elif not is_formula and not item.get("independent_source_verification", {}).get(
            "passed"
        ):
            problems.append(
                "Independent local OCR text read differs from or is missing for the primary candidate"
            )
        elif not is_formula and (
            re.search(r"[=<>√±^]", value)
            or re.search(
                r"\b(?:sin|cos|tan|cot|sec|csc|log|ln)\s*(?:[0-9θϑπ]|[A-Za-z](?![A-Za-z])|[({])",
                value,
            )
        ):
            problems.append(
                "Formula-like symbols were returned by text OCR outside the mathematical detector"
            )
        if problems:
            evidence = crop(
                src["page"],
                src["bbox"],
                "raster_component_evidence",
                q["question_number"],
                label,
            )
            q["assets"].append(evidence)
            reason = "; ".join(problems)
            q["issues"].append(
                {
                    "code": "raster_math_unverified",
                    "reason": reason,
                    "question_number": q["question_number"],
                    "page": src["page"],
                    "field": "option" if label else "question",
                    "option_label": label,
                    "asset_id": evidence["id"],
                    "method": result["method"],
                }
            )
            block = {
                "type": "unresolved_math",
                "raw_text": value,
                "diagnostic_asset_id": evidence["id"],
                "display": False,
                "source": src,
                "reason": reason,
            }
        elif is_formula:
            block = {
                "type": "math",
                "latex": value,
                "display": item["type"] == "isolated",
                "confidence": "local_model_source_reread_agreement",
                "syntax_valid": True,
                "source": src,
            }
        else:
            block = {"type": "text", "text": value, "source": src}
        # Preserve physical line boundaries in JSON, not report-only <br> hacks.
        if target and last_line.get(label) != line:
            block["break_before"] = True
        elif target:
            if target[-1]["type"] == "text":
                target[-1]["text"] += " "
            elif block["type"] == "text":
                block["text"] = " " + block["text"]
        target.append(block)
        last_line[label] = line
    for item in result.get("figures", []):
        src = source(item["position"])
        box = src["bbox"]
        # Figure association uses the observed label baseline only after layout
        # recognition has identified the genuine visual component.
        cy = (rectangle(item["position"])[1] + rectangle(item["position"])[3]) / 2
        candidates = [
            (rectangle(a["position"])[1], label)
            for a, label in labels
            if rectangle(a["position"])[1] <= cy
        ]
        label = max(candidates)[1] if candidates else None
        body_boxes = [b["source"]["bbox"] for b in q["content"]]
        first_label_top = min(source(a["position"])["bbox"][1] for a, _ in labels)
        if (
            (
                body_boxes
                and box[1] < max(b[3] for b in body_boxes)
                and box[3] > min(b[1] for b in body_boxes)
            )
            or box[3] < first_label_top
            or (not body_boxes and box[1] < first_label_top)
        ):
            label = None
        visual = crop(
            src["page"], box, "option" if label else "body", q["question_number"], label
        )
        q["assets"].append(visual)
        target = options[label]["content"] if label else q["content"]
        block = {
            "type": "visual",
            "asset_id": visual["id"],
            "display": True,
            "source": src,
        }
        insertion = len(target)
        for index, existing in enumerate(target):
            line = existing["source"].get("recognition_line")
            peers = [b for b in target if b["source"].get("recognition_line") == line]
            top = min(b["source"]["bbox"][1] for b in peers)
            left = min(b["source"]["bbox"][0] for b in peers)
            if top > box[1] + 2 or abs(top - box[1]) <= 2 and left > box[2]:
                insertion = index
                break
        target.insert(insertion, block)
    if not q["content"] or any(not o["content"] for o in q["options"]):
        raise ValueError("OCR returned an empty body or option")
    for warning in result.get("warnings", []):
        q["issues"].append(
            {
                "code": "raster_math_unverified",
                "reason": warning,
                "question_number": q["question_number"],
                "page": asset["page"],
                "field": "question",
                "asset_id": asset["id"],
                "method": result["method"],
            }
        )
    for blocks in [q["content"], *[o["content"] for o in q["options"]]]:
        for index, block in enumerate(blocks, 1):
            block["order"] = index
    # Original whole-question images remain traceable diagnostic evidence only;
    # they no longer stand in for canonical body/option content.
    for a in q["assets"]:
        if a["id"] in original_assets and a["role"] == "body":
            a["role"] = "source_raster_evidence"
    q["raw"]["raster_recognition"] = {
        "method": result["method"],
        "source_asset_id": asset["id"],
        "source_sha256": asset["sha256"],
        "implementation_sha256": result["implementation_sha256"],
        "source_geometry": result.get("source_geometry"),
        "source_fidelity": result.get(
            "source_fidelity",
            {
                "status": "needs_review",
                "reason": "No source-fidelity validation record",
            },
        ),
    }
    q["extraction_status"] = (
        "review"
        if q["issues"] or result.get("source_fidelity", {}).get("status") != "verified"
        else "extracted"
    )
    return q


def restore_cached(data, asset_dir):
    """Native-parser reruns reuse verified local evidence, never invoke models.

    Without an exact model/code/source cache match, normal unresolved RAW
    preservation remains in force. No network or optional ML imports occur.
    """
    root = Path(__file__).resolve().parents[2] / "data/input/mathematics_ocr"
    candidates = [q for q in data["questions"] if eligible(q)]
    if not candidates or not (root / "results").is_dir():
        return 0
    fingerprint = model_fingerprint(root / "models")
    entries = []
    for q in candidates:
        asset = next((a for a in q["assets"] if a["role"] == "source_preview"), None)
        if asset:
            cache = root / "results" / f"{asset['sha256']}_{fingerprint[:16]}.json"
            if cache.is_file():
                entries.append((q, asset, cache))
    if not entries:
        return 0
    import pypdfium2 as pdfium

    replacements = {}
    with pdfium.PdfDocument(data["source_document"]["path"]) as pdf:
        crops = Assets(pdf, asset_dir, data["source_document"])
        for q, asset, cache in entries:
            try:
                candidate = assemble(
                    q, asset, json.loads(cache.read_text(encoding="utf8")), crops.crop
                )
            except ValueError:
                continue
            if (
                candidate["extraction_status"] == "extracted"
                and not candidate["issues"]
            ):
                replacements[q["id"]] = candidate
    data["questions"] = [replacements.get(q["id"], q) for q in data["questions"]]
    return len(replacements)


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--raw-json", type=Path, nargs="+", required=True)
    cli.add_argument("--question", type=int, action="append")
    cli.add_argument("--ocr-python", type=Path, required=True)
    cli.add_argument(
        "--models", type=Path, default=Path("data/input/mathematics_ocr/models")
    )
    cli.add_argument(
        "--cache", type=Path, default=Path("data/input/mathematics_ocr/results")
    )
    cli.add_argument("--apply", action="store_true")
    cli.add_argument("--secondary-python", type=Path)
    cli.add_argument("--formulanet-model-dir", type=Path)
    cli.add_argument("--skip-renderback", action="store_true")
    args = cli.parse_args(argv)
    if bool(args.secondary_python) != bool(args.formulanet_model_dir):
        cli.error(
            "--secondary-python and --formulanet-model-dir must be supplied together"
        )
    fingerprint = model_fingerprint(
        args.models.resolve(),
        [args.formulanet_model_dir.resolve()]
        if args.formulanet_model_dir
        else (),
    )
    documents = [(p, json.loads(p.read_text(encoding="utf8"))) for p in args.raw_json]
    selected = [
        (p, d, q, next(a for a in q["assets"] if a["role"] == "source_preview"))
        for p, d in documents
        for q in d["questions"]
        if eligible(q) and (not args.question or q["question_number"] in args.question)
    ]
    if not selected:
        cli.error("No selected whole-raster RAW-issue questions")
    with tempfile.TemporaryDirectory(prefix="math-raster-") as temp:
        manifest = Path(temp) / "crops.json"
        prepared = []
        for _, document, question, asset in selected:
            prepared.append(
                {
                    **asset,
                    "question_number": question["question_number"],
                    "question_id": question["id"],
                    "question_number_masks": question_number_mask(
                        question, asset, document.get("pages", [])
                    ),
                    "label_words": label_evidence(asset),
                }
            )
        manifest.write_text(json.dumps(prepared), encoding="utf8")
        worker_command = [
            str(args.ocr_python.resolve()),
            str(Path(__file__).with_name("raster_worker.py")),
            "--manifest",
            str(manifest),
            "--models",
            str(args.models.resolve()),
            "--cache",
            str(args.cache.resolve()),
        ]
        if args.formulanet_model_dir:
            worker_command.extend(
                ["--secondary-model-dir", str(args.formulanet_model_dir.resolve())]
            )
        subprocess.run(worker_command, check=True)
    if args.secondary_python:
        run_secondary_formula_reads(
            selected,
            args.cache,
            fingerprint,
            args.secondary_python,
            args.formulanet_model_dir,
        )
    run_independent_text_reads(selected, args.cache, fingerprint)
    node = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
    )
    if not args.skip_renderback and node.is_file():
        run_renderback(selected, args.cache, fingerprint, args.ocr_python, node)
    elif not args.skip_renderback:
        print(
            "Local Edge/Playwright unavailable; render-back validation was not run",
            flush=True,
        )
    for _, _, _, asset in selected:
        candidate_path = args.cache / f"{asset['sha256']}_{fingerprint[:16]}.json"
        if candidate_path.is_file():
            candidate = json.loads(candidate_path.read_text(encoding="utf8"))
            update_candidate_fidelity(candidate)
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf8",
            )
    import pypdfium2 as pdfium

    for path, data in documents:
        changed = 0
        with pdfium.PdfDocument(data["source_document"]["path"]) as pdf:
            crops = Assets(pdf, path.parent / "assets", data["source_document"])
            for i, q in enumerate(data["questions"]):
                entry = next(
                    (
                        a
                        for p, _, target, a in selected
                        if p == path and target["id"] == q["id"]
                    ),
                    None,
                )
                if entry is None:
                    continue
                result_path = args.cache / f"{entry['sha256']}_{fingerprint[:16]}.json"
                result = json.loads(result_path.read_text(encoding="utf8"))
                try:
                    replacement = assemble(q, entry, result, crops.crop)
                except ValueError as error:
                    print(q["id"], "unresolved:", str(error), flush=True)
                    continue
                if (
                    replacement["extraction_status"] == "extracted"
                    and not replacement["issues"]
                ):
                    data["questions"][i] = replacement
                    changed += 1
                else:
                    print(
                        q["id"],
                        "withheld:",
                        replacement["raw"]["raster_recognition"]["source_fidelity"],
                        flush=True,
                    )
                print(
                    q["id"],
                    "structured",
                    len(replacement["issues"]),
                    "remaining findings",
                    flush=True,
                )
        validate_raw(data)
        if args.apply and changed:
            data["extraction"].setdefault("raster_recognition", {})[
                "implementation_sha256"
            ] = sha256(Path(__file__).read_bytes()).hexdigest()
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
            )
        print(
            path.name,
            changed,
            "questions",
            "saved" if args.apply else "validated, not saved",
            flush=True,
        )


if __name__ == "__main__":
    main()
