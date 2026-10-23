"""Optional, local-only raster text/formula recognition worker.

Run in the isolated OCR environment. No API, source upload, answer generation,
spell correction or mathematical simplification is performed.
"""

import argparse
import ast
import json
import os
import re
from hashlib import sha256
from itertools import pairwise
from pathlib import Path
from statistics import median


def plain_number(image, reading):
    """Use text OCR for unambiguous, single-baseline printed number glyphs."""
    import cv2
    import numpy as np

    text = reading["text"].strip()
    if reading["score"] < 0.95 or not re.fullmatch(r"[-−+]?\d+(?:[,.]\d+)*", text):
        return False
    _, _, stats, _ = cv2.connectedComponentsWithStats(
        (np.asarray(image.convert("L")) < 175).astype("uint8"), 8
    )
    ink = [s for s in stats[1:] if s[4] >= 3]
    if not ink:
        return False
    height = max(s[3] for s in ink)
    glyphs = [s for s in ink if s[3] >= height * 0.5]
    if len(glyphs) != sum(c.isdigit() for c in text):
        return False  # roots, slashes or extra/exponent glyphs cannot disappear
    centers = [s[1] + s[3] / 2 for s in glyphs]
    return (
        max(centers) - min(centers) < height * 0.25
        and min(s[3] for s in glyphs) >= height * 0.75
    )


def option_regions(image, labels):
    """Assign complete connected ink components, never slice fractions at rows."""
    import cv2
    import numpy as np

    if [re.sub(r"[^A-E]", "", w["text"]) for w in labels] != list("ABCDE"):
        return []
    centers = [w["y"] + w["height"] / 2 for w in labels]
    gaps = [b - a for a, b in pairwise(centers) if b - a > 8]
    gap = median(gaps) if gaps else median(w["height"] for w in labels) * 3
    start = centers[0] - gap * 0.65
    mask = (np.asarray(image.convert("L")) < 175).astype("uint8")
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    bars = [
        b
        for b in stats[1:]
        if b[2] >= 8 and b[3] <= 3 and b[2] >= b[3] * 3 and b[1] >= start
    ]
    # A relation/minus stroke is not a fraction bar. A real fraction has
    # separate source ink both above and below the bar, within its span.
    bars = [
        bar
        for bar in bars
        if any(
            c[4] >= 3
            and bar[0] <= c[0] + c[2] / 2 <= bar[0] + bar[2]
            and c[1] + c[3] <= bar[1]
            and bar[1] - (c[1] + c[3]) <= bar[2] * 0.9
            for c in stats[1:]
        )
        and any(
            c[4] >= 3
            and bar[0] <= c[0] + c[2] / 2 <= bar[0] + bar[2]
            and c[1] >= bar[1] + bar[3]
            and c[1] - (bar[1] + bar[3]) <= bar[2] * 0.9
            for c in stats[1:]
        )
    ]
    assigned = [[] for _ in labels]
    for x, y, width, height, area in stats[1:]:
        if area < 2 or y + height / 2 < start:
            continue
        choices = []
        for index, label in enumerate(labels):
            same_row = [
                other
                for other in labels
                if abs(other["y"] - label["y"]) < label["height"] * 0.6
            ]
            right = min(
                (other["x"] - 2 for other in same_row if other["x"] > label["x"]),
                default=image.width,
            )
            left = label["x"] + label["width"]
            if x >= left and x < right:
                choices.append((abs(y + height / 2 - centers[index]), index))
        if choices:
            nearby = [
                b
                for b in bars
                if b[0] <= x + width / 2 <= b[0] + b[2]
                and abs(y + height / 2 - b[1])
                < median(w["height"] for w in labels) * 1.6
            ]
            if nearby:
                bar = min(nearby, key=lambda b: abs(y + height / 2 - b[1]))
                index = min((abs(bar[1] - centers[i]), i) for _, i in choices)[1]
            else:
                _, index = min(choices)
            assigned[index].append([int(x), int(y), int(x + width), int(y + height)])
    regions = []
    for label, boxes in zip(labels, assigned, strict=True):
        box = None
        if boxes:
            box = [
                max(label["x"] + label["width"], min(b[0] for b in boxes) - 2),
                max(0, min(b[1] for b in boxes) - 2),
                min(image.width, max(b[2] for b in boxes) + 2),
                min(image.height, max(b[3] for b in boxes) + 2),
            ]
        regions.append((label, box))
    return regions


def protected_math_region(position, formulas, text_regions):
    """A layout 'figure' cannot swallow printed formulas or answer markers."""
    x0, y0 = min(p[0] for p in position), min(p[1] for p in position)
    x1, y1 = max(p[0] for p in position), max(p[1] for p in position)
    overlap = 0
    for formula in formulas:
        box = formula["box"]
        left, top = min(p[0] for p in box), min(p[1] for p in box)
        right, bottom = max(p[0] for p in box), max(p[1] for p in box)
        overlap += max(0, min(x1, right) - max(x0, left)) * max(
            0, min(y1, bottom) - max(y0, top)
        )
    if overlap / max(1, (x1 - x0) * (y1 - y0)) >= 0.15:
        return True
    for text in text_regions:
        if not re.match(r"^\s*(?:\([A-E]\)|[A-E][.)])", text["text"]):
            continue
        box = text["position"]
        left, top = min(p[0] for p in box), min(p[1] for p in box)
        if x0 <= left < x1 and y0 <= top < y1:
            return True
    return False


def isolate_question_number(image, anchors):
    """Mask only source-anchored printed-number glyphs that do not touch math.

    The original image remains immutable. If any connected foreground stroke
    crosses an anchor boundary, no mask is applied and the question is flagged.
    """
    import cv2
    import numpy as np
    from PIL import ImageDraw

    if not anchors:
        return (
            image.copy(),
            [],
            ["Printed question number has no source-coordinate anchor"],
        )
    gray = np.asarray(image.convert("L"))
    ink = gray < 175
    count, _labels, stats, _ = cv2.connectedComponentsWithStats(ink.astype("uint8"), 8)
    masks = []
    for anchor in anchors:
        x0, y0, x1, y1 = (round(v) for v in anchor["bbox"])
        # Include antialiasing around the PDF text bbox without widening into
        # nearby formula strokes. Crossing components make masking unsafe.
        x0, y0 = max(0, x0 - 1), max(0, y0 - 1)
        x1, y1 = min(image.width, x1 + 1), min(image.height, y1 + 1)
        if x1 <= x0 or y1 <= y0 or not ink[y0:y1, x0:x1].any():
            return (
                image.copy(),
                [],
                ["Printed-number anchor does not align with source ink"],
            )
        crossing = []
        for index in range(1, count):
            left, top, width, height, _area = stats[index]
            if (
                left < x1
                and left + width > x0
                and top < y1
                and top + height > y0
                and (left < x0 or left + width > x1 or top < y0 or top + height > y1)
            ):
                crossing.append(index)
        if crossing:
            return (
                image.copy(),
                [],
                [
                    "Printed-number ink touches adjacent content; masking would remove source pixels"
                ],
            )
        masks.append(
            {
                "bbox": [x0, y0, x1, y1],
                "text": anchor["text"],
                "glyph_id": anchor.get("glyph_id"),
            }
        )
    masked = image.copy()
    draw = ImageDraw.Draw(masked)
    for region in masks:
        draw.rectangle(region["bbox"], fill="white")
    return masked, masks, []


def component_ownership(image, recognitions, figures, number_masks):
    """Trace connected source ink to one recognition, figure, or anchor region."""
    import cv2
    import numpy as np

    ink = np.asarray(image.convert("L")) < 175
    count, _labels, stats, centroids = cv2.connectedComponentsWithStats(
        ink.astype("uint8"), 8
    )
    regions = []
    for index, item in enumerate(recognitions):
        points = np.asarray(item["position"]).reshape(-1, 2)
        regions.append(
            ("recognition", index, [*points.min(axis=0), *points.max(axis=0)])
        )
    for index, item in enumerate(figures):
        points = np.asarray(item["position"]).reshape(-1, 2)
        regions.append(("visual", index, [*points.min(axis=0), *points.max(axis=0)]))
    for index, item in enumerate(number_masks):
        regions.append(("question_number", index, item["bbox"]))

    components = []
    assigned_pixels = 0
    total_pixels = int(ink.sum())
    unassigned_pixels = 0
    for component_id in range(1, count):
        x, y, width, height, area = (int(v) for v in stats[component_id])
        cx, cy = (float(v) for v in centroids[component_id])
        intersections = []
        for kind, owner, box in regions:
            x0, y0, x1, y1 = (float(v) for v in box)
            overlap = max(0.0, min(x + width, x1) - max(x, x0)) * max(
                0.0, min(y + height, y1) - max(y, y0)
            )
            if overlap:
                intersections.append((overlap / max(1, area), kind, owner))
        intersections.sort(reverse=True)
        if intersections and (
            len(intersections) == 1 or intersections[0][0] - intersections[1][0] > 0.15
        ):
            _, kind, owner = intersections[0]
            assigned_pixels += area
        else:
            kind, owner = "unassigned", None
            unassigned_pixels += area
        components.append(
            {
                "id": component_id - 1,
                "bbox": [x, y, x + width, y + height],
                "area": area,
                "centroid": [cx, cy],
                "owner_type": kind,
                "owner_index": owner,
                "significant": area >= 3 or width >= 3 or height >= 3,
            }
        )
    return {
        "component_count": len(components),
        "components": components,
        "ink_pixel_count": total_pixels,
        "assigned_ink_pixel_count": assigned_pixels,
        "unassigned_ink_pixel_count": unassigned_pixels,
        "assigned_ink_fraction": assigned_pixels / max(1, total_pixels),
        "unassigned_significant_count": sum(
            c["owner_type"] == "unassigned" and c["significant"] for c in components
        ),
    }


def source_fidelity_status(
    recognitions, labels, number_masks, number_warnings, warnings, ownership
):
    """Hard-gate candidates on source evidence; confidence alone never passes."""
    observed = [
        re.sub(r"[^A-E]", "", item["text"].strip())
        for item in recognitions
        if item.get("type") == "text"
        and re.fullmatch(r"\(?[A-E]\)?[.)]?", item["text"].strip())
    ]
    blockers = []
    if observed != list("ABCDE"):
        blockers.append("A–E labels lack a unique, direct source-backed sequence")
    if not number_masks or number_warnings:
        blockers.append(
            "printed question number was not safely isolated from source ink"
        )
    if ownership["unassigned_significant_count"]:
        blockers.append("significant source components remain unassigned")
    blockers.extend(warnings)
    content = [
        item
        for item in recognitions
        if not re.fullmatch(r"\(?[A-E]\)?[.)]?", item.get("text", "").strip())
    ]
    if not content:
        blockers.append("no body or option content was reconstructed")
    unverified = []
    for index, item in enumerate(content):
        if not item.get("independent_source_verification", {}).get("passed"):
            unverified.append(index)
        if item.get("type") in {"embedding", "isolated"} and not item.get(
            "round_trip_verification", {}
        ).get("passed"):
            unverified.append(index)
    if unverified:
        blockers.append(
            "recognition lacks independent source and/or render-back verification"
        )
    status = (
        "unresolved"
        if any(
            phrase in " ".join(blockers)
            for phrase in ("A–E labels", "no body or option", "unassigned")
        )
        else "needs_review"
        if blockers
        else "verified"
    )
    return {
        "status": status,
        "blockers": list(dict.fromkeys(blockers)),
        "independently_verified_content_count": len(content) - len(unverified),
        "content_region_count": len(content),
        "option_label_sequence": observed,
        "number_anchor_count": len(number_masks),
        "assigned_ink_fraction": ownership["assigned_ink_fraction"],
    }


def model_fingerprint(root, external_model_dirs=()):
    fingerprint = sha256(Path(__file__).read_bytes())
    module = ast.parse(Path(__file__).with_name("raster.py").read_text(encoding="utf8"))
    evidence = next(
        n
        for n in module.body
        if isinstance(n, ast.FunctionDef) and n.name == "label_evidence"
    )
    fingerprint.update(ast.dump(evidence).encode())
    fingerprint.update(Path(__file__).with_name("ocr.py").read_bytes())
    for name in (
        "raster_formula_worker.py",
        "raster_render_worker.py",
        "raster_formula_render.cjs",
    ):
        path = Path(__file__).with_name(name)
        if path.is_file():
            fingerprint.update(path.read_bytes())
    for p in sorted(
        p for p in root.rglob("*") if p.suffix in {".onnx", ".pt", ".json"}
    ):
        fingerprint.update(p.relative_to(root).as_posix().encode())
        fingerprint.update(sha256(p.read_bytes()).digest())
    for model_index, model_root in enumerate(external_model_dirs):
        model_root = Path(model_root)
        if not model_root.is_dir():
            raise ValueError(f"Secondary model directory is missing: {model_root}")
        for path in sorted(p for p in model_root.rglob("*") if p.is_file()):
            fingerprint.update(f"secondary:{model_index}:".encode())
            fingerprint.update(path.relative_to(model_root).as_posix().encode())
            fingerprint.update(sha256(path.read_bytes()).digest())
    return fingerprint.hexdigest()


def engine_config(root):
    return {
        "languages": ["en"],
        "text": {
            "rec_model_fp": str(
                root / "cnocr-ppocr-en_PP-OCRv3/en_PP-OCRv3_rec_infer.onnx"
            ),
            "det_model_fp": str(
                root / "cnstd-ppocr-en_PP-OCRv3_det/en_PP-OCRv3_det_dynamic.onnx"
            ),
            "rec_root": str(root / "text_rec"),
            "det_root": str(root / "text_det"),
        },
        "mfd": {"model_path": str(root / "pix2text-mfd-1.5/pix2text-mfd-1.5.onnx")},
        "formula": {"model_dir": str(root / "pix2text-mfr-1.5")},
    }


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--manifest", type=Path, required=True)
    cli.add_argument("--models", type=Path, required=True)
    cli.add_argument("--cache", type=Path, required=True)
    cli.add_argument("--secondary-model-dir", type=Path)
    args = cli.parse_args(argv)
    home = args.models.resolve().parent
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "DO_NOT_TRACK": "1",
            "YOLO_CONFIG_DIR": str(home / "yolo"),
        }
    )
    import numpy as np
    import torch
    from PIL import Image, ImageDraw
    from pix2text.doc_yolo_layout_parser import DocYoloLayoutParser
    from pix2text.layout_parser import ElementType
    from pix2text.text_formula_ocr import TextFormulaOCR

    torch.set_num_threads(2)
    root = args.models.resolve()
    fingerprint = model_fingerprint(
        root,
        [args.secondary_model_dir] if args.secondary_model_dir else (),
    )
    engine = TextFormulaOCR.from_config(
        engine_config(root), enable_spell_checker=False, device="cpu"
    )
    layout = DocYoloLayoutParser(
        model_fp=str(
            root / "pix2text-layout-docyolo/doclayout_yolo_docstructbench_imgsz1024.pt"
        ),
        device="cpu",
    )
    args.cache.mkdir(parents=True, exist_ok=True)
    for asset in json.loads(args.manifest.read_text(encoding="utf8")):
        path = Path(asset["path"])
        digest = sha256(path.read_bytes()).hexdigest()
        if digest != asset["sha256"]:
            raise ValueError("Source crop hash changed")
        output = args.cache / f"{digest}_{fingerprint[:16]}.json"
        if output.exists():
            print(asset["id"], "cached", flush=True)
            continue
        with Image.open(path) as source:
            image = source.convert("RGB")
        masked, number_masks, number_warnings = isolate_question_number(
            image, asset.get("question_number_masks", [])
        )
        warnings = list(number_warnings)
        regions, _ = layout.parse(masked.copy(), resized_shape=1024)
        has_visual = any(
            r["type"] in {ElementType.FIGURE, ElementType.TABLE} for r in regions
        )
        math_regions = (
            engine.mfd(
                masked.copy(),
                resized_shape=(round(masked.height * 768 / masked.width), 768),
            )
            if has_visual
            else []
        )
        text_regions = engine.text_ocr.ocr(np.array(image)) if has_visual else []
        figures = []
        for region in regions:
            if region["type"] not in {ElementType.FIGURE, ElementType.TABLE}:
                continue
            if protected_math_region(region["position"], math_regions, text_regions):
                continue
            box = np.asarray(region["position"]).reshape(-1, 2)
            left, top = box.min(axis=0)
            right, bottom = box.max(axis=0)
            area = (right - left) * (bottom - top)
            if area > image.width * image.height * 0.55:
                warnings.append(
                    "Layout model proposed an over-large visual region; retained for component review, not accepted as a whole-question image"
                )
                continue
            figures.append(
                {
                    "type": "visual",
                    "position": [
                        [max(0, left - 4), max(0, top - 4)],
                        [min(image.width, right + 4), min(image.height, bottom + 4)],
                    ],
                    "score": float(region.get("score", 0)),
                    "kind": str(region["type"]),
                }
            )
        masked = masked.copy()
        draw = ImageDraw.Draw(masked)
        for figure in figures:
            draw.rectangle([tuple(p) for p in figure["position"]], fill="white")
        labels = asset.get("label_words", [])
        separated = option_regions(masked, labels)
        recognized = []
        if separated:
            # Body stops before the first complete answer ink component. The
            # full component, including superscripts/vincula, supplies its box.
            answer_top = min(
                (box[1] for _, box in separated if box),
                default=min(w["y"] for w in labels),
            )
            body = masked.crop((0, 0, image.width, answer_top))
            recognized = engine.recognize(body, return_text=False, resized_shape=768)
            first_line = max((r["line_number"] for r in recognized), default=-1) + 1
            for index, (label, box) in enumerate(separated):
                line = first_line + index
                x, y, w, h = (label[k] for k in ("x", "y", "width", "height"))
                recognized.append(
                    {
                        "type": "text",
                        "text": "(" + re.sub(r"[^A-E]", "", label["text"]) + ")",
                        "line_number": line,
                        "position": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                        "score": label.get("confidence", 0) / 100
                        if "confidence" in label
                        else None,
                        "label_evidence": label,
                    }
                )
                if box is None:
                    continue
                patch = masked.crop(tuple(box))
                plain = engine.text_ocr.recognize_only(np.array(patch))
                prose = re.findall(r"[A-Za-z]{3,}", plain["text"])
                if plain_number(patch, plain):
                    recognized.append(
                        {
                            "type": "text",
                            "text": plain["text"].strip(),
                            "score": float(plain["score"]),
                            "line_number": line,
                            "position": [
                                [box[0], box[1]],
                                [box[2], box[1]],
                                [box[2], box[3]],
                                [box[0], box[3]],
                            ],
                            "recognizer": "local_cnocr_single_baseline_number",
                        }
                    )
                elif any(
                    word.lower()
                    not in {"sin", "cos", "tan", "log", "cot", "sec", "csc"}
                    for word in prose
                ):
                    parts = engine.recognize(patch, return_text=False)
                    for part in parts:
                        part["position"] = np.asarray(part["position"]) + [
                            box[0],
                            box[1],
                        ]
                        part["line_number"] = line
                    recognized.extend(parts)
                else:
                    math = engine.latex_ocr.recognize(patch)
                    recognized.append(
                        {
                            "type": "embedding",
                            "text": math["text"],
                            "score": float(math["score"]),
                            "line_number": line,
                            "position": [
                                [box[0], box[1]],
                                [box[2], box[1]],
                                [box[2], box[3]],
                                [box[0], box[3]],
                            ],
                        }
                    )
        else:
            recognized = engine.recognize(masked, return_text=False, resized_shape=768)
        formulas = [r for r in recognized if r["type"] in {"embedding", "isolated"}]
        patches = []
        for item in formulas:
            box = np.asarray(item["position"]).reshape(-1, 2)
            left, top = box.min(axis=0)
            right, bottom = box.max(axis=0)
            pad = max(2, min(5, (bottom - top) * 0.08))
            # A second source crop, not a guessed/repaired formula. Padding is
            # bounded by the source region and neighboring component centers.
            left, top = max(0, left - pad), max(0, top - pad)
            right, bottom = (
                min(image.width, right + pad),
                min(image.height, bottom + pad),
            )
            patches.append(
                masked.crop(
                    (int(left), int(top), int(right + 0.999), int(bottom + 0.999))
                )
            )
        if patches:
            checks = engine.latex_ocr.recognize(patches, batch_size=1)
            for item, check in zip(formulas, checks, strict=True):
                item["verification"] = {
                    "latex": check["text"],
                    "score": float(check["score"]),
                }
                if re.fullmatch(r"[A-Za-z]|[0-9]+", item["text"].strip()):
                    box = np.asarray(item["position"]).reshape(-1, 2)
                    lo, hi = box.min(axis=0), box.max(axis=0)
                    patch = masked.crop(
                        (int(lo[0]), int(lo[1]), int(hi[0] + 0.999), int(hi[1] + 0.999))
                    )
                    literal = engine.text_ocr.recognize_only(np.array(patch))
                    item["literal_verification"] = {
                        "text": literal["text"],
                        "score": float(literal["score"]),
                    }
        ownership = component_ownership(image, recognized, figures, number_masks)
        coverage = ownership["assigned_ink_fraction"]
        if ownership["unassigned_significant_count"]:
            warnings.append(
                f"{ownership['unassigned_significant_count']} significant source ink components have no unique body/option/visual/number owner"
            )

        def serial(value):
            if hasattr(value, "tolist"):
                return value.tolist()
            raise TypeError(type(value).__name__)

        result = {
            "source_sha256": digest,
            "implementation_sha256": fingerprint,
            "method": "local_pix2text_text_formula_layout",
            "recognitions": recognized,
            "figures": figures,
            "warnings": warnings,
            "ink_coverage": coverage,
            "source_geometry": {
                "pixel_size": [image.width, image.height],
                "pdf_bbox": asset.get("bbox"),
                "coordinate_units_per_pixel": [
                    (asset["bbox"][2] - asset["bbox"][0]) / image.width,
                    (asset["bbox"][3] - asset["bbox"][1]) / image.height,
                ],
                "question_number_masks": number_masks,
                "component_ownership": ownership,
            },
            "source_fidelity": source_fidelity_status(
                recognized,
                labels,
                number_masks,
                number_warnings,
                warnings,
                ownership,
            ),
        }
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=serial) + "\n",
            encoding="utf8",
        )
        print(
            asset["id"],
            "recognized",
            len(recognized),
            "components",
            len(figures),
            "visuals",
            flush=True,
        )


if __name__ == "__main__":
    main()
