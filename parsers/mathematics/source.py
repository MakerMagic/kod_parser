"""One local source pass: lossless pages, owned content/assets and final-page key."""

import json
import re
from collections import Counter
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium

from .formulas import SUBS, SUPERS, bounds, formula_bounds, recover
from .structure import walk

VERSION = "2"
HEADER = re.compile(
    r"(?:\b(?:https?://|www\.)\S+|\bNUFYPET\s+Math\s+v\s*\d+(?:\.\d+)*)", re.IGNORECASE
)
NUMBER = re.compile(r"^(\d{1,3})[.)]?$")
LABEL = re.compile(r"^\(?([A-Z])\)?[.)]?$")


def implementation_hash():
    """Invalidate extraction caches after a source/layout implementation change."""
    names = (
        "source.py",
        "formulas.py",
        "latex.py",
        "ocr.py",
        "raster_ocr.cjs",
        "ocr_words.ps1",
        "structure.py",
    )
    return sha256(
        b"".join(Path(__file__).with_name(n).read_bytes() for n in names)
    ).hexdigest()


def issue(code, reason, **context):
    return {"code": code, "reason": reason, **context}


def is_math(c):
    if c["text"] in {"$", "£", "€"}:
        return False
    return (
        "math" in c["fontname"].lower()
        or "symbol" in c["fontname"].lower()
        or any(ord(x) > 0x1D400 for x in c["text"])
    )


def inside(c, box):
    return (
        box[0] <= (c["x0"] + c["x1"]) / 2 < box[2]
        and box[1] <= (c["top"] + c["bottom"]) / 2 < box[3]
    )


def figures_in_box(figures, box, anchors):
    result = []
    for b in figures:
        contained = sum(inside(a, b) for a in anchors)
        if contained >= 2:
            clipped = [
                max(b[0], box[0]),
                max(b[1], box[1]),
                min(b[2], box[2]),
                min(b[3], box[3]),
            ]
            if clipped[2] - clipped[0] > 2 and clipped[3] - clipped[1] > 2:
                result.append(clipped)
        elif inside({"x0": b[0], "x1": b[2], "top": b[1], "bottom": b[3]}, box):
            result.append(b)
    return result


def bands(chars, images):
    intervals = sorted(
        [(c["top"], c["bottom"]) for c in chars if c["text"].strip()]
        + [(b[1], b[3]) for b in images]
    )
    result = []
    for lo, hi in intervals:
        if result and lo <= result[-1][1] + 0.3:
            result[-1][1] = max(result[-1][1], hi)
        else:
            result.append([lo, hi])
    return result


def row_start(word, ink, *, split_tall=False):
    mid = (word["top"] + word["bottom"]) / 2
    found = next((i for i, b in enumerate(ink) if b[0] <= mid <= b[1]), None)
    if found is None:
        return word["top"] - 2
    lo = ink[found][0]
    if split_tall and ink[found][1] - lo > (word["bottom"] - word["top"]) * 2.5:
        # Neighboring rows can be connected by tall fractions/scripts. Such a
        # union is not a usable row boundary for every label it intersects.
        return word["top"] - 2
    return max(lo - 2, (lo + ink[found - 1][1]) / 2 if found else lo - 2)


def option_anchors(words):
    candidates = []
    for w in words:
        m = LABEL.fullmatch(w["text"]) or re.match(r"^\(([A-Z])\)", w["text"])
        if m and not "math" in w["fontname"].lower():
            a = {**w, "label": m[1]}
            if len(m[0]) < len(w["text"]) and w.get("chars"):
                a.update(
                    dict(
                        zip(
                            ("x0", "top", "x1", "bottom"),
                            bounds(w["chars"][: len(m[0])]),
                        )
                    )
                )
            # Word may split "D )" into two words. Only adjacent punctuation
            # on the label's baseline/in its prose font belongs to the marker.
            if w["text"] == m[1]:
                closing = next(
                    (
                        v
                        for v in words
                        if v["page"] == w["page"]
                        and v["text"] == ")"
                        and v["fontname"] == w["fontname"]
                        and 0 <= v["x0"] - w["x1"] <= (w["bottom"] - w["top"]) * 0.5
                        and abs(v["top"] - w["top"]) < (w["bottom"] - w["top"]) * 0.2
                    ),
                    None,
                )
                if closing:
                    a["x1"] = closing["x1"]
                    a["text"] += " )"
            candidates.append(a)
    rows = []
    for w in sorted(candidates, key=lambda w: (w["page"], w["top"], w["x0"])):
        if (
            rows
            and rows[-1][0]["page"] == w["page"]
            and w["top"] - rows[-1][0]["top"] < (w["bottom"] - w["top"]) * 0.8
        ):
            rows[-1].append(w)
        else:
            rows.append([w])
    candidates = [w for row in rows for w in sorted(row, key=lambda w: w["x0"])]
    runs = []
    for i, w in enumerate(candidates):
        if w["label"] != "A":
            continue
        run = []
        for candidate in candidates[i:]:
            if (
                run
                and candidate["label"] == "A"
                and (
                    len(candidate["text"]) > 1
                    or abs(candidate["x0"] - run[0]["x0"])
                    < (candidate["bottom"] - candidate["top"]) * 0.5
                )
            ):
                break
            if candidate["label"] == chr(65 + len(run)) and (
                not run
                or candidate["top"] > run[-1]["bottom"]
                or abs(candidate["x0"] - run[-1]["x0"])
                > (candidate["bottom"] - candidate["top"]) * 2
            ):
                run.append(candidate)
        if len(run) < 2:
            continue
        runs.append(run)
    return (
        max(
            runs,
            key=lambda r: (
                len(r),
                sum(a["fontname"] == r[0]["fontname"] for a in r),
                r[0]["page"],
                r[0]["top"],
            ),
        )
        if runs
        else []
    )


def option_top(anchor, ink, figures, anchors):
    """Word inline pictures can extend well above their adjacent option label."""
    top = row_start(anchor, ink, split_tall=True)
    right = min(
        (
            a["x0"]
            for a in anchors
            if abs(a["top"] - anchor["top"]) < 5 and a["x0"] > anchor["x0"] + 1
        ),
        default=float("inf"),
    )
    for box in figures:
        if (
            anchor["x1"] - 2 <= box[0] < right
            and min(box[3], anchor["bottom"]) > max(box[1], anchor["top"])
            and abs(box[3] - anchor["bottom"]) <= (anchor["bottom"] - anchor["top"])
            and sum(inside(a, box) for a in anchors) < 2
        ):
            top = min(top, box[1] - 1)
    return top


class Assets:
    def __init__(self, document, root, source):
        self.document, self.root, self.source = document, Path(root), source
        self.bitmaps = {}

    def crop(self, page, box, role, question, option=None):
        if page not in self.bitmaps:
            with (
                closing(self.document[page - 1]) as p,
                closing(p.render(scale=2)) as bitmap,
            ):
                self.bitmaps[page] = bitmap.to_pil().copy()
        pixels = self.bitmaps[page]
        shape = sha256(json.dumps(box, separators=(",", ":")).encode()).hexdigest()[:16]
        name = f"q{question:03}_p{page:03}_{role}_{option or 'body'}_{shape}.png"
        path = self.root / self.source["sha256"][:20] / name
        path.parent.mkdir(parents=True, exist_ok=True)
        box_px = [round(v * 2) for v in box]
        box_px[0] = max(0, box_px[0])
        box_px[1] = max(0, box_px[1])
        box_px[2] = min(pixels.width, box_px[2])
        box_px[3] = min(pixels.height, box_px[3])
        if box_px[2] <= box_px[0] or box_px[3] <= box_px[1]:
            raise ValueError("Empty source crop")
        if not path.exists():
            pixels.crop(box_px).save(path)
        return {
            "id": path.stem,
            "path": path.resolve().as_posix(),
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "role": role,
            "option_label": option,
            "page": page,
            "bbox": box,
            "pixel_size": [box_px[2] - box_px[0], box_px[3] - box_px[1]],
            "source_sha256": self.source["sha256"],
        }


def text_of(chars):
    result = []
    previous = None
    for c in chars:
        if (
            previous
            and abs(c["top"] - previous["top"])
            > max(c["size"], previous["size"]) * 0.65
        ):
            result.append("\n")
        result.append(c["text"])
        previous = c
    return "".join(result)


def project(
    chars,
    rules,
    figures,
    assets,
    page,
    question,
    field,
    option=None,
    *,
    math_context=False,
):
    # Actual bullet glyphs at aligned source line starts are structure, not
    # unknown mathematical symbols. Split before/after the indented item run.
    markers = [
        c
        for c in chars
        if c["text"] == "•"
        or c["text"] == "\uf0b7"
        and "symbol" in c["fontname"].lower()
    ]
    markers = [
        m
        for m in markers
        if not any(
            c["text"].strip()
            and c["x1"] <= m["x0"]
            and min(c["bottom"], m["bottom"]) > max(c["top"], m["top"])
            for c in chars
            if c is not m
        )
    ]
    if (
        len(markers) >= 2
        and max(m["x0"] for m in markers) - min(m["x0"] for m in markers) < 2
    ):
        markers.sort(key=lambda c: c["top"])
        last = markers[-1]
        stop = min(
            (
                c["top"]
                for c in chars
                if c["text"].strip()
                and c["top"] > last["bottom"]
                and c["x0"] <= last["x0"] + last["size"] * 0.3
            ),
            default=float("inf"),
        )
        result, saved, issues, items = [], [], [], []

        def part(lo, hi, exclude=()):
            cc = [
                c
                for c in chars
                if lo <= (c["top"] + c["bottom"]) / 2 < hi and c not in exclude
            ]
            ff = [f for f in figures if lo <= (f[1] + f[3]) / 2 < hi]
            bs, aa, ii = project(
                cc,
                rules,
                ff,
                assets,
                page,
                question,
                field,
                option,
                math_context=math_context,
            )
            saved.extend(aa)
            issues.extend(ii)
            return bs

        result.extend(part(float("-inf"), markers[0]["top"]))
        for i, marker in enumerate(markers):
            end = markers[i + 1]["top"] if i + 1 < len(markers) else stop
            items.append({"content": part(marker["top"], end, markers)})
        result.append(
            {
                "type": "list",
                "ordered": False,
                "items": items,
                "source": {
                    "page": page,
                    "bbox": bounds(markers),
                    "glyph_ids": [m["id"] for m in markers],
                    "method": "native_list_markers",
                },
            }
        )
        result.extend(part(stop, float("inf")))
        for i, block in enumerate(result, 1):
            block["order"] = i
        return result, saved, issues
    blocks = []
    saved = []
    issues = []
    owned_figures = []
    for fig in figures:
        if fig[2] - fig[0] < 2 or fig[3] - fig[1] < 2:
            continue
        asset = assets.crop(page, fig, "option" if option else "body", question, option)
        saved.append(asset)
        owned_figures.append((fig, asset))
        if (
            math_context
            and fig[3] - fig[1] <= 60
            and fig[2] - fig[0] > (fig[3] - fig[1]) * 1.5
        ):
            issues.append(
                issue(
                    "raster_math_unverified",
                    "Compact visual in an explicit formula/expression task remains source imagery; mathematical OCR transcription is not verified",
                    question_number=question,
                    page=page,
                    field=field,
                    option_label=option,
                    asset_id=asset["id"],
                    method="source_visual_preservation",
                )
            )
    chars = [c for c in chars if not any(inside(c, box) for box, _ in owned_figures)]
    forced = set()
    for i, c in enumerate(chars):
        if is_math(c):
            continue
        script = bool(c["text"] in SUPERS or c["text"] in SUBS)
        if i:
            prev = chars[i - 1]
            script |= (
                not is_math(prev)
                and not c["text"].isspace()
                and not prev["text"].isspace()
                and c["size"] < prev["size"] * 0.87
                and abs(c["top"] - prev["top"]) > prev["size"] * 0.15
                and -1 < c["x0"] - prev["x1"] < prev["size"] * 0.4
            )
        if script:
            lo = i
            while (
                lo > 0
                and not chars[lo - 1]["text"].isspace()
                and abs(chars[lo - 1]["x1"] - chars[lo]["x0"]) < 12
            ):
                lo -= 1
            hi = i + 1
            while (
                hi < len(chars)
                and not chars[hi]["text"].isspace()
                and abs(chars[hi - 1]["x1"] - chars[hi]["x0"]) < 12
            ):
                hi += 1
            forced.update(range(lo, hi))
    chunks = []
    line_starts = set()
    for index, c in enumerate(chars):
        math = is_math(c) or index in forced
        previous = chars[index - 1] if index else None
        separate_line = (
            previous
            and c["top"] - previous["bottom"] > max(c["size"], previous["size"]) * 0.3
            and c["x0"] < previous["x1"]
        )
        if separate_line and math and chunks and chunks[-1][0]:
            preceding = "".join(v["text"] for v in chunks[-1][1])
            separate_line = (
                any(v in preceding for v in "=<>≤≥")
                and not any(v in preceding for v in "∑∏∫{⁄")
                and c["x0"] <= chunks[-1][1][0]["x0"] + c["size"] * 2
            )
        if separate_line and any(
            r["x0"] - 0.8 <= min(previous["x0"], c["x0"])
            and max(previous["x1"], c["x1"]) <= r["x1"] + 0.8
            and previous["bottom"] <= r["top"] + 0.8
            and c["top"] >= r["bottom"] - 0.8
            for r in rules
        ):
            separate_line = False  # Numerator/denominator are one expression.
        figure_between = previous and any(
            previous["bottom"] <= f[1] and f[3] <= c["top"] for f, _ in owned_figures
        )
        same_paragraph = (
            not chunks
            or math
            or c["top"] - chunks[-1][1][-1]["bottom"] < c["size"] * 1.5
        )
        if (
            chunks
            and chunks[-1][0] == math
            and same_paragraph
            and not separate_line
            and not figure_between
        ):
            chunks[-1][1].append(c)
        else:
            chunks.append((math, [c]))
            if separate_line or figure_between:
                line_starts.add(c["id"])
    for math, chunk in chunks:
        if not any(c["text"].strip() for c in chunk):
            continue
        box = formula_bounds(chunk, rules) if math else bounds(chunk)
        evidence = {
            "page": page,
            "bbox": box,
            "glyph_ids": [c["id"] for c in chunk],
            "method": "native_glyph_geometry" if math else "native_text",
        }
        layout = {"break_before": True} if chunk[0]["id"] in line_starts else {}
        if not math:
            text = text_of(chunk)
            if "(cid:" in text or "�" in text:
                code, reason = (
                    "unmapped_glyph",
                    "Native prose contains an unmapped source glyph",
                )
            else:
                blocks.append(
                    {"type": "text", "text": text, "source": evidence, **layout}
                )
                continue
        else:
            latex, code, reason = recover(chunk, rules)
            if latex is not None:
                blocks.append(
                    {
                        "type": "math",
                        "latex": latex,
                        "display": field == "question"
                        and not any(
                            c["text"].strip()
                            and c not in chunk
                            and min(c["bottom"], box[3]) > max(c["top"], box[1])
                            for c in chars
                        ),
                        "confidence": "geometry_checked",
                        "syntax_valid": True,
                        "source": evidence,
                        **layout,
                    }
                )
                continue
        crop = [max(0, box[0] - 1), max(0, box[1] - 1), box[2] + 1, box[3] + 1]
        asset = assets.crop(page, crop, "formula_fallback", question, option)
        saved.append(asset)
        blocks.append(
            {
                "type": "unresolved_math",
                "diagnostic_asset_id": asset["id"],
                "raw_text": text_of(chunk),
                "display": field == "question",
                "source": evidence,
                "reason": reason,
                **layout,
            }
        )
        issues.append(
            issue(
                code,
                reason,
                question_number=question,
                page=page,
                field=field,
                option_label=option,
                method="native_glyph_geometry",
                asset_id=asset["id"],
            )
        )
    for box, asset in owned_figures:
        unresolved = any(i.get("asset_id") == asset["id"] for i in issues)
        at = next(
            (i for i, b in enumerate(blocks) if b["source"]["bbox"][1] > box[3]),
            len(blocks),
        )
        blocks.insert(
            at,
            {
                "type": "unresolved_math" if unresolved else "visual",
                "diagnostic_asset_id" if unresolved else "asset_id": asset["id"],
                "display": not any(
                    c["text"].strip()
                    and min(c["bottom"], box[3]) > max(c["top"], box[1])
                    for c in chars
                ),
                "source": {"page": page, "bbox": box, "method": "native_visual"},
            },
        )
    # Preserve PDF stream order for prose/formulas; place figures at their source
    # vertical position without sorting fraction numerator/denominator as prose.
    for i, b in enumerate(blocks, 1):
        b["order"] = i
        if i > 1 and b["source"]["bbox"][1] > blocks[i - 2]["source"]["bbox"][3] + 2:
            b["break_before"] = True
    return blocks, saved, issues


def read_key(page, raw_text, number):
    entries = []
    issues = []
    if not re.search(r"Answer\s*key", raw_text, re.IGNORECASE):
        issues.append(
            issue(
                "answer_key_structure",
                "Last page lacks an answer-key heading",
                page=number,
            )
        )
    for line in page.extract_text_lines():
        match = re.fullmatch(r"\s*(\d+)\s+([A-Z])\s*", line["text"])
        if match:
            entries.append(
                {
                    "question_number": int(match[1]),
                    "correct_answer": match[2],
                    "page": number,
                    "bbox": [line[k] for k in ("x0", "top", "x1", "bottom")],
                    "raw_text": line["text"],
                    "method": "native_key_row",
                }
            )
        elif re.match(r"^\d+\s", line["text"]):
            issues.append(
                issue(
                    "answer_key_structure",
                    "Ambiguous answer-key row preserved",
                    page=number,
                    raw_text=line["text"],
                )
            )
    for n, count in Counter(e["question_number"] for e in entries).items():
        if count > 1:
            issues.append(
                issue(
                    "answer_key_duplicate",
                    "Multiple source key rows",
                    question_number=n,
                    page=number,
                )
            )
    return {"page": number, "raw_text": raw_text, "entries": entries, "issues": issues}


def parse_pdf(
    path, *, asset_dir=Path("data/raw/mathematics/assets"), question_numbers=None
):
    path = Path(path).resolve(strict=True)
    digest = sha256(path.read_bytes()).hexdigest()
    source = {
        "path": path.as_posix(),
        "filename": path.name,
        "sha256": digest,
        "source": "matdev",
    }
    pages = []
    questions = []
    findings = []
    all_regions = []
    with pdfplumber.open(path) as pdf, pdfium.PdfDocument(path) as rendered:
        if len(pdf.pages) < 3:
            raise ValueError("A combined source needs cover, questions and key")
        cover = pdf.pages[0].extract_text() or ""
        version = re.search(
            r"NUFYPET\s+Math\s+v\s*(\d+(?:\.\d+)*)", cover, re.IGNORECASE
        )
        if not version:
            raise ValueError("Unrecognized mathematics source; no version identity")
        source["version"] = version[1]
        source["id"] = f"matdev_v{version[1]}_{digest[:20]}"
        source["pdf_metadata"] = dict(pdf.metadata or {})
        assets = Assets(rendered, asset_dir, source)
        current = None
        next_number = 1
        for pi, page in enumerate(pdf.pages, 1):
            raw = page.extract_text() or ""
            chars = [
                {
                    k: c[k]
                    for k in ("text", "fontname", "size", "x0", "x1", "top", "bottom")
                }
                | {"id": f"p{pi}_g{i}"}
                for i, c in enumerate(page.chars)
            ]
            role = (
                "cover"
                if pi == 1
                else "answer_key"
                if pi == len(pdf.pages)
                else "questions"
            )
            exclusions = [
                {
                    "bbox": [l[k] for k in ("x0", "top", "x1", "bottom")],
                    "text": l["text"],
                    "reason": "repeated_header",
                }
                for l in page.extract_text_lines()
                if l["top"] < 85
                and (
                    re.search(r"NUFYPET\s+Math\s+v\s*\d", l["text"], re.IGNORECASE)
                    or re.fullmatch(
                        r"(?:https?://|www\.)\S+\s*", l["text"], re.IGNORECASE
                    )
                )
            ]
            pages.append(
                {
                    "page": pi,
                    "role": role,
                    "width": page.width,
                    "height": page.height,
                    "raw_text": raw,
                    "glyphs": chars,
                    "exclusions": exclusions,
                }
            )
            if role == "cover":
                continue
            if role == "answer_key":
                key = read_key(page, raw, pi)
                continue
            body = [
                c for c in chars if not any(inside(c, x["bbox"]) for x in exclusions)
            ]
            visible = [c for c in body if c["text"].strip()]
            words = [
                {**w, "page": pi}
                for w in page.extract_words(
                    extra_attrs=["fontname"],
                    return_chars=True,
                    x_tolerance=1,
                    y_tolerance=3,
                )
                if not any(inside(w, x["bbox"]) for x in exclusions)
            ]
            marks = [
                {**w, "number": int(m[1])}
                for w in words
                if (m := NUMBER.fullmatch(w["text"]))
                and "bold" in w["fontname"].lower()
            ]
            marks.sort(key=lambda m: (m["top"], m["x0"]))
            for mark in marks:
                dot = next(
                    (
                        c
                        for c in body
                        if c["text"] in {".", ")"}
                        and abs(c["top"] - mark["top"]) < 1
                        and 0 <= c["x0"] - mark["x1"] < 2
                    ),
                    None,
                )
                if dot:
                    mark["x1"] = dot["x1"]
            margin = min((w["x0"] for w in marks), default=0)
            marks = [w for w in marks if abs(w["x0"] - margin) < 8]
            figures = [
                [o[k] for k in ("x0", "top", "x1", "bottom")] for o in page.images
            ]
            # Filled thin rectangles are Word's native fraction/radical bars.
            rules = [
                {k: r[k] for k in ("x0", "x1", "top", "bottom")}
                for r in [*page.rects, *page.lines]
                if 0 <= r["bottom"] - r["top"] <= 1.6 and r["x1"] - r["x0"] >= 2
            ]
            pages[-1]["formula_rules"] = rules
            pages[-1]["native_figures"] = figures
            pages[-1]["native_objects"] = [
                {
                    "type": kind,
                    "object_id": j,
                    "bbox": [o[k] for k in ("x0", "top", "x1", "bottom")],
                }
                for kind, objects in (
                    ("image", page.images),
                    ("rect", page.rects),
                    ("line", page.lines),
                    ("curve", page.curves),
                )
                for j, o in enumerate(objects)
            ]
            complex_vectors = [
                o
                for o in pages[-1]["native_objects"]
                if o["type"] in {"line", "curve"}
                or o["type"] == "rect"
                and o["bbox"][3] - o["bbox"][1] > 1.6
            ]
            if complex_vectors:
                from parsers.blackstone.visuals import _regions

                groups = _regions([{"bbox": o["bbox"]} for o in complex_vectors], gap=2)
                for group in groups:
                    # Table/grid borders do not replace native cell text with
                    # a large composite image. Their geometry stays in RAW.
                    enclosed = [w for w in words if inside(w, group["bbox"])]
                    box = group["bbox"]
                    if (
                        box[2] - box[0] > 2
                        and box[3] - box[1] > 2
                        and sum(len(w["text"]) > 3 for w in enclosed) < 10
                    ):
                        figures.append(group["bbox"])
            # Raster envelopes can include white padding that overlaps the next
            # numbered line. Only native glyph bands define numbered cuts;
            # complete native figures retain independent source bounds below.
            ink = bands(body, [])
            cuts = [(row_start(w, ink), w) for w in marks]
            if (
                current is not None
                and cuts
                and cuts[0][0]
                > min((c["top"] for c in visible), default=cuts[0][0]) + 3
            ):
                cuts.insert(0, (min(c["top"] for c in visible), None))
            if not cuts and current is not None:
                cuts = [(min((c["top"] for c in visible), default=55), None)]
            if not cuts and any(c["text"].strip() for c in body):
                findings.append(
                    issue(
                        "question_boundary",
                        "Question-page content has no reliable numbered anchor",
                        page=pi,
                    )
                )
            for i, (top, anchor) in enumerate(cuts):
                bottom = cuts[i + 1][0] if i + 1 < len(cuts) else page.height - 35
                if anchor is not None:
                    n = anchor["number"]
                    if n != next_number:
                        findings.append(
                            issue(
                                "question_numbering",
                                f"Expected {next_number}, found {n}",
                                page=pi,
                                question_number=n,
                            )
                        )
                    next_number = n + 1
                    current = {
                        "id": f"{source['id']}_q{n:03}",
                        "source_document_id": source["id"],
                        "question_number": n,
                        "regions": [],
                        "issues": [],
                        "assets": [],
                        "content": [],
                        "options": [],
                    }
                    questions.append(current)
                if current is None:
                    continue
                region = {
                    "page": pi,
                    "bbox": [0, top, page.width, bottom],
                    "chars": [
                        c for c in body if inside(c, [0, top, page.width, bottom])
                    ],
                    "words": [
                        w for w in words if inside(w, [0, top, page.width, bottom])
                    ],
                    "rules": rules,
                    "figures": [
                        b for b in figures if top <= (b[1] + b[3]) / 2 < bottom
                    ],
                    "anchor": anchor,
                }
                current["regions"].append({"page": pi, "bbox": region["bbox"]})
                all_regions.append((current, region))
            page.close()
        # Process questions only after cross-page ownership is known.
        for q in questions:
            if (
                question_numbers is not None
                and q["question_number"] not in question_numbers
            ):
                continue
            regions = [r for owner, r in all_regions if owner is q]
            for r in regions:
                if r["chars"]:
                    support = formula_bounds(r["chars"], r["rules"])
                    # Source rules can extend into the whitespace above a
                    # numbered line. Retain them in this question's geometry.
                    r["bbox"][1] = min(r["bbox"][1], support[1] - 1)
            math_context = bool(
                re.search(
                    r"\b(?:formula|expression|rearrange|simplify|evaluate)\b",
                    " ".join(text_of(r["chars"]) for r in regions),
                    re.IGNORECASE,
                )
            )
            all_words = [w for r in regions for w in r["words"]]
            anchors = option_anchors(all_words)
            if not anchors and any(r["figures"] for r in regions):
                from .ocr import words as raster_words

                evidence = []
                for r in regions:
                    for fig in r["figures"]:
                        asset = assets.crop(
                            r["page"], fig, "ocr_source", q["question_number"]
                        )
                        q["assets"].append(asset)
                        try:
                            evidence.extend(raster_words(asset))
                        except ValueError as error:
                            q["issues"].append(
                                issue(
                                    "ocr_unavailable",
                                    str(error),
                                    question_number=q["question_number"],
                                    page=r["page"],
                                )
                            )
                observed = option_anchors(evidence)
                q["ocr_evidence"] = evidence
                # An incomplete alphabetic prefix is not a complete source
                # answer set. Retain the raster rather than invent its suffix.
                counts = Counter(
                    w["text"].strip("()[]")
                    for w in evidence
                    if re.fullmatch(r"\(?[A-E]\)?", w["text"])
                )
                if [a["label"] for a in observed] == list("ABCDE") and all(
                    counts[c] == 1 for c in "ABCDE"
                ):
                    anchors = observed
                    q["issues"].append(
                        issue(
                            "ocr_option_labels",
                            "Source-raster option labels require visual review; OCR is not used as mathematical text",
                            question_number=q["question_number"],
                            method="local_raster_label_recognition",
                        )
                    )
            if not anchors:
                q["issues"].append(
                    issue(
                        "option_boundary",
                        "No reliable contiguous source option anchors",
                        question_number=q["question_number"],
                        field="options",
                        page=regions[0]["page"] if regions else None,
                    )
                )
            q["options"] = [
                {
                    "label": a["label"],
                    "content": [],
                    "source": {
                        "page": a["page"],
                        "bbox": [a[k] for k in ("x0", "top", "x1", "bottom")],
                    },
                }
                for a in anchors
            ]
            for r in regions:
                local = [a for a in anchors if a["page"] == r["page"]]
                ink = bands(r["chars"], [])
                starts = {
                    a["label"]: option_top(a, ink, r["figures"], local) for a in local
                }
                for a in local:
                    row = [
                        b
                        for b in local
                        if abs(b["top"] - a["top"]) < (a["bottom"] - a["top"]) * 0.8
                    ]
                    start = min(starts[b["label"]] for b in row)
                    for b in row:
                        starts[b["label"]] = start
                opt_top = min(starts.values(), default=r["bbox"][3])
                owned = r["chars"]
                if r["anchor"]:
                    a = r["anchor"]
                    owned = [
                        c
                        for c in owned
                        if not inside(c, [a[k] for k in ("x0", "top", "x1", "bottom")])
                    ]
                assigned = set()
                for opt, a in zip(q["options"], anchors):
                    if a["page"] != r["page"]:
                        continue
                    row = [b for b in local if starts[b["label"]] == starts[a["label"]]]
                    right = min(
                        (b["x0"] - 0.5 for b in row if b["x0"] > a["x0"] + 1),
                        default=r["bbox"][2],
                    )
                    next_row = min(
                        (
                            starts[b["label"]]
                            for b in local
                            if starts[b["label"]] > starts[a["label"]] + 1
                        ),
                        default=r["bbox"][3],
                    )
                    box = [a["x0"] - 0.5, starts[a["label"]], right, next_row]
                    cc = [
                        c
                        for c in owned
                        if inside(c, box)
                        and not inside(c, [a[k] for k in ("x0", "top", "x1", "bottom")])
                    ]
                    assigned.update(c["id"] for c in cc)
                    ff = figures_in_box(r["figures"], box, local)
                    blocks, saved, issues = project(
                        cc,
                        r["rules"],
                        ff,
                        assets,
                        r["page"],
                        q["question_number"],
                        "option",
                        opt["label"],
                        math_context=math_context,
                    )
                    opt["content"].extend(blocks)
                    q["assets"].extend(saved)
                    q["issues"].extend(issues)
                main = [
                    c
                    for c in owned
                    if (c["top"] + c["bottom"]) / 2 < opt_top
                    and c["id"] not in assigned
                ]
                figures = figures_in_box(
                    r["figures"],
                    [r["bbox"][0], r["bbox"][1], r["bbox"][2], opt_top],
                    local,
                )
                previous_option = next(
                    (
                        o
                        for o in reversed(q["options"])
                        if o["source"]["page"] < r["page"]
                    ),
                    None,
                )
                blocks, saved, issues = project(
                    main,
                    r["rules"],
                    figures,
                    assets,
                    r["page"],
                    q["question_number"],
                    "option" if previous_option else "question",
                    previous_option["label"] if previous_option else None,
                    math_context=math_context,
                )
                (
                    previous_option["content"] if previous_option else q["content"]
                ).extend(blocks)
                q["assets"].extend(saved)
                q["issues"].extend(issues)
                ink_boxes = (
                    [
                        formula_bounds(
                            [c for c in r["chars"] if c["text"].strip()], r["rules"]
                        )
                    ]
                    if any(c["text"].strip() for c in r["chars"])
                    else []
                )
                ink_boxes.extend(r["figures"])
                if ink_boxes:
                    box = [
                        max(0, min(b[0] for b in ink_boxes) - 2),
                        max(r["bbox"][1], min(b[1] for b in ink_boxes) - 2),
                        min(r["bbox"][2], max(b[2] for b in ink_boxes) + 2),
                        min(r["bbox"][3], max(b[3] for b in ink_boxes) + 2),
                    ]
                    q["assets"].append(
                        assets.crop(
                            r["page"], box, "source_preview", q["question_number"]
                        )
                    )
            q["raw"] = {
                "glyph_ids": [c["id"] for r in regions for c in r["chars"]],
                "native_text": "\n".join(text_of(r["chars"]) for r in regions),
            }
            for content in [q["content"], *[o["content"] for o in q["options"]]]:
                for index, block in enumerate(content, 1):
                    block["order"] = index
            # Native raw glyphs are never silently discarded by the projection.
            # Number/option anchors are structural; text inside saved visuals is
            # represented by that visual. Anything else receives a lossless crop.
            blocks = list(
                walk([*q["content"], *[b for o in q["options"] for b in o["content"]]])
            )
            covered = {g for b in blocks for g in b["source"].get("glyph_ids", [])}
            for r in regions:
                structural = [a for a in anchors if a["page"] == r["page"]]
                if r["anchor"]:
                    structural.append(r["anchor"])
                boxes = [
                    [a[k] for k in ("x0", "top", "x1", "bottom")] for a in structural
                ]
                boxes.extend(
                    b["source"]["bbox"]
                    for b in blocks
                    if b["type"] in {"visual", "unresolved_math"}
                    and b["source"]["page"] == r["page"]
                )
                lost = [
                    c
                    for c in r["chars"]
                    if c["text"].strip()
                    and c["id"] not in covered
                    and not any(inside(c, b) for b in boxes)
                ]
                if lost:
                    box = bounds(lost)
                    asset = assets.crop(
                        r["page"],
                        [box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1],
                        "unassigned_content",
                        q["question_number"],
                    )
                    q["assets"].append(asset)
                    q["issues"].append(
                        issue(
                            "content_assignment",
                            "Source glyphs retained in RAW and diagnostic crop but lack reliable field ownership",
                            page=r["page"],
                            question_number=q["question_number"],
                            glyph_ids=[c["id"] for c in lost],
                            asset_id=asset["id"],
                        )
                    )
            q["extraction_status"] = "review" if q["issues"] else "extracted"
    data = {
        "domain": "mathematics",
        "source": "matdev",
        "stage": "mathematics_raw",
        "schema_version": "2",
        "extraction": {
            "version": VERSION,
            "implementation_sha256": implementation_hash(),
            "method": "native_text_and_glyph_geometry",
            "first_page_skipped": True,
            "answer_key_page_excluded": True,
        },
        "source_document": source,
        "pages": pages,
        "questions": [
            q
            for q in questions
            if question_numbers is None or q["question_number"] in question_numbers
        ],
        "answer_key": key,
        "issues": findings,
    }
    validate_raw(data)
    return data


def validate_raw(data):
    from .latex import validate as validate_latex

    if data["stage"] != "mathematics_raw" or data["domain"] != "mathematics":
        raise ValueError("Not mathematics RAW")
    ids = [q["id"] for q in data["questions"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate question IDs")
    by_id = {c["id"]: c for p in data["pages"] for c in p["glyphs"]}
    for q in data["questions"]:
        if any(n["page"] in {1, data["answer_key"]["page"]} for n in q["regions"]):
            raise ValueError("Cover/key leaked into questions")
        if any(g not in by_id for g in q["raw"]["glyph_ids"]):
            raise ValueError("Unknown raw glyph reference")
        assets = {a["id"] for a in q["assets"]}
        for block in walk(
            [*q["content"], *[b for o in q["options"] for b in o["content"]]]
        ):
            if block["type"] == "list":
                if len(block["items"]) < 2 or any(
                    not i["content"] for i in block["items"]
                ):
                    raise ValueError("Incomplete native list structure")
            elif block["type"] == "math":
                if validate_latex(block["latex"]):
                    raise ValueError("Invalid stored mathematics")
            elif block["type"] == "visual":
                if block["asset_id"] not in assets:
                    raise ValueError("Missing source visual asset")
            elif block["type"] == "unresolved_math":
                aid = block["diagnostic_asset_id"]
                if aid not in assets or not any(
                    i.get("asset_id") == aid for i in q["issues"]
                ):
                    raise ValueError(
                        "Unresolved mathematics lacks diagnostic evidence/RAW issue"
                    )
            elif block["type"] != "text":
                raise ValueError("Unknown RAW content block")
