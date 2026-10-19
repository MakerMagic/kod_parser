"""Local OCR of isolated first source-image line; never infer from reasoning."""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def first_line(image):
    grey = ImageOps.grayscale(image)
    ink = grey.point(lambda p: 255 if p < 170 else 0)
    rows = [
        y
        for y in range(min(image.height, max(150, image.width // 3)))
        if ink.crop((0, y, image.width, y + 1)).getbbox()
    ]
    if not rows:
        raise ValueError("No readable first source-image line")
    start, bottom = rows[0], rows[0] + 1
    for y in rows[1:]:
        if y - bottom > 4:
            break
        bottom = y + 1
    line_box = ink.crop((0, start, image.width, bottom)).getbbox()
    return [
        max(0, line_box[0] - 12),
        max(0, start - 12),
        min(image.width, line_box[2] + 12),
        min(image.height, bottom + 12),
    ]


def read_header(asset, cache_dir):
    root = Path(cache_dir)
    root.mkdir(parents=True, exist_ok=True)
    cached = root / (asset["sha256"] + "_v2.json")
    if cached.exists():
        result = json.loads(cached.read_text(encoding="utf-8"))
        if (
            result.get("source_sha256") != asset["sha256"]
            or result.get("version") != "2"
        ):
            raise ValueError("Image-header cache mismatch")
        return result
    if os.name != "nt":
        raise ValueError("Windows OCR unavailable; image header remains unresolved")
    with Image.open(asset["local_path"]) as original:
        bbox = first_line(original)
        with tempfile.TemporaryDirectory(prefix="bmat-source-header-") as folder:
            crop = original.crop(bbox).convert("RGB")
            ink = (
                ImageOps.grayscale(crop)
                .point(lambda p: 255 if p < 170 else 0)
                .getbbox()
            )
            # Windows OCR drops isolated short tokens. Fixed calibration words
            # share its baseline; neither supplies a number nor an answer letter.
            # Only the text *between* those markers is accepted as observed data.
            font = ImageFont.truetype(
                str(Path(os.environ["WINDIR"]) / "Fonts/arial.ttf"),
                max(16, round((ink[3] - ink[1]) * 1.1)),
            )
            left = 20 + round(font.getlength("Question "))
            right = left + ink[2] - ink[0] + round(font.getlength(" "))
            canvas = Image.new(
                "RGB",
                (right + round(font.getlength("source header")) + 30, crop.height + 70),
                "white",
            )
            canvas.paste(crop, (left - ink[0], 35 - ink[1]))
            draw = ImageDraw.Draw(canvas)
            for x, text in ((20, "Question"), (right, "source header")):
                draw.text(
                    (x, 35 - font.getbbox(text)[1]), text, font=font, fill="black"
                )
            temporary = Path(folder) / "header.png"
            canvas.save(temporary)
            try:
                result = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-File",
                        str(Path(__file__).with_suffix(".ps1")),
                        "-ImagePath",
                        str(temporary),
                    ],
                    capture_output=True,
                    timeout=20,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise ValueError("Local header OCR timeout") from error
    if result.returncode:
        raise ValueError("Local source-image header OCR failed")
    observed = json.loads(result.stdout.decode("utf-8-sig"))["lines"]
    text = " ".join(observed)
    match = re.fullmatch(r"Question\s+(.+?)\s+source\s+header", text, re.IGNORECASE)
    evidence = {
        "method": "local_windows_ocr_isolated_source_header",
        "version": "2",
        "source_sha256": asset["sha256"],
        "source_url": asset["source_url"],
        "bbox": bbox,
        "observed_calibration_text": observed,
        "lines": [match[1]] if match else [],
    }
    cached.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return evidence
