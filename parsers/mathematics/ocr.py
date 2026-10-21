"""Raster option-label evidence only; ordinary OCR never invents mathematical text."""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def recognize(path, layout=11):
    model = Path(
        os.environ.get(
            "MATHEMATICS_OCR_MODEL_DIR",
            Path(__file__).resolve().parents[2] / "data/input/mathematics_ocr",
        )
    )
    node = shutil.which("node")
    if node and (model / "eng.traineddata").is_file():
        result = subprocess.run(
            [
                node,
                str(Path(__file__).with_name("raster_ocr.cjs")),
                str(path),
                str(model),
                str(layout),
            ],
            capture_output=True,
            timeout=45,
            check=False,
        )
        if not result.returncode:
            return json.loads(result.stdout.decode("utf8"))
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(Path(__file__).with_name("ocr_words.ps1")),
            "-ImagePath",
            str(path),
        ],
        capture_output=True,
        timeout=25,
        check=False,
    )
    if result.returncode:
        raise ValueError("Local raster-label OCR unavailable/failed")
    return json.loads(result.stdout.decode("utf-8-sig"))


def calibrated_labels(path):
    """OCR actual small ink components between fixed non-answer marker words."""
    with Image.open(path) as original:
        image = original.convert("RGB")
    bw = ImageOps.grayscale(image).point(lambda x: 255 if x < 210 else 0)
    pixels = bw.load()
    visited = set()
    components = []
    for y in range(image.height):
        for x in range(image.width):
            if not pixels[x, y] or (x, y) in visited:
                continue
            todo = [(x, y)]
            visited.add((x, y))
            points = []
            while todo:
                a, b = todo.pop()
                points.append((a, b))
                for u, v in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                    if (
                        0 <= u < image.width
                        and 0 <= v < image.height
                        and (u, v) not in visited
                        and pixels[u, v]
                    ):
                        visited.add((u, v))
                        todo.append((u, v))
            box = [
                min(a for a, b in points),
                min(b for a, b in points),
                max(a for a, b in points) + 1,
                max(b for a, b in points) + 1,
            ]
            if (
                6 <= box[3] - box[1] <= 45
                and box[2] - box[0] < 50
                and len(points) >= 10
            ):
                components.append(box)
    components.sort(key=lambda b: (b[1], b[0]))
    candidates = []
    for box in components:
        merged = False
        for old in candidates:
            h = min(box[3] - box[1], old[3] - old[1])
            overlap = min(box[3], old[3]) - max(box[1], old[1])
            gap = max(box[0] - old[2], old[0] - box[2], 0)
            if overlap > h * 0.55 and gap < h * 0.5:
                old[:] = [
                    min(old[0], box[0]),
                    min(old[1], box[1]),
                    max(old[2], box[2]),
                    max(old[3], box[3]),
                ]
                merged = True
                break
        if not merged:
            candidates.append(list(box))
    candidates = [b for b in candidates if b[2] - b[0] < 70][:36]
    font = ImageFont.truetype(str(Path(os.environ["WINDIR"]) / "Fonts/arial.ttf"), 28)
    canvas = Image.new("RGB", (650, max(70, len(candidates) * 65)), "white")
    draw = ImageDraw.Draw(canvas)
    for i, b in enumerate(candidates):
        crop = image.crop(b)
        ratio = 28 / max(1, crop.height)
        crop = crop.resize((round(crop.width * ratio), 28))
        draw.text((10, 65 * i + 10), f"Region {i}", font=font, fill="black")
        canvas.paste(crop, (180, 65 * i + 15))
        draw.text((195 + crop.width, 65 * i + 10), "source", font=font, fill="black")
    with tempfile.TemporaryDirectory(prefix="math-labels-") as folder:
        file = Path(folder) / "labels.png"
        canvas.save(file)
        result = recognize(file, 6)
    observed = []
    for line in result.get("lines", []):
        m = re.fullmatch(
            r"Region\s+(\d+)\s+([\[(]?[A-Z][\])]?)\s+source",
            line.strip(),
            re.IGNORECASE,
        )
        if m and int(m[1]) < len(candidates) and m[2].strip("()[]").isupper():
            b = candidates[int(m[1])]
            observed.append(
                {
                    "text": m[2],
                    "x": b[0],
                    "y": b[1],
                    "width": b[2] - b[0],
                    "height": b[3] - b[1],
                    "calibration_evidence": line,
                }
            )
    return observed


def words(asset):
    cache = Path(asset["path"]).with_suffix(".ocr_v3.json")
    if cache.exists():
        saved = json.loads(cache.read_text(encoding="utf8"))
        if saved.get("sha256") == asset["sha256"]:
            return saved["words"]
    if os.name != "nt":
        raise ValueError("Local Windows OCR unavailable")
    try:
        data = recognize(asset["path"])
    except subprocess.TimeoutExpired as error:
        raise ValueError("Local raster-label OCR timeout") from error
    if not any(re.fullmatch(r"\(?[A-E]\)?", w["text"]) for w in data["words"]):
        data["words"].extend(calibrated_labels(asset["path"]))
    box = asset["bbox"]
    sx = (box[2] - box[0]) / asset["pixel_size"][0]
    sy = (box[3] - box[1]) / asset["pixel_size"][1]
    out = [
        {
            "text": w["text"],
            "fontname": "OCR source raster",
            "page": asset["page"],
            "x0": box[0] + w["x"] * sx,
            "x1": box[0] + (w["x"] + w["width"]) * sx,
            "top": box[1] + w["y"] * sy,
            "bottom": box[1] + (w["y"] + w["height"]) * sy,
            "method": data.get("method", "windows_native_ocr"),
            "confidence": w.get("confidence"),
            "source_asset_id": asset["id"],
        }
        for w in data["words"]
    ]
    cache.write_text(
        json.dumps(
            {"sha256": asset["sha256"], "words": out, "observed_text": data["text"]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf8",
    )
    return out
