"""Question-only source previews from owned layout; no question re-extraction."""

import argparse
import json
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from statistics import median

import pypdfium2 as pdfium

from parsers.blackstone.visuals import _save_crop


def content_bounds(question, page_number):
    from .parser import ADMIN

    boxes = []
    for block in question.get("layout_blocks", []):
        if block.get("page") != page_number or not block.get("bbox"):
            continue
        text = block.get("readable_text", block.get("text", "")).strip()
        if block.get("type") == "text" and (
            ADMIN.match(text)
            or block.get("component") in {"footer", "header", "administration"}
        ):
            continue
        boxes.append(block["bbox"])
    boxes.extend(
        a["bbox"] for a in question.get("visual_assets", []) if a["page"] == page_number
    )
    for option in question.get("options", []):
        if option.get("page") == page_number and option.get("label_bbox"):
            boxes.append(option["label_bbox"])
        boxes.extend(
            a["bbox"] for a in option.get("images", []) if a["page"] == page_number
        )
    if not boxes:
        return None
    return [
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    ]


def regions(dataset, question):
    result = []
    # Source-order recovery can create several exact spans on the same page.
    # Preview the owned page region once, not once per provenance span.
    for number in dict.fromkeys(s["page"] for s in question["raw"]["page_spans"]):
        page = dataset["pages"][number - 1]
        box = content_bounds(question, number)
        if box is None:
            continue
        heights = [
            b["bbox"][3] - b["bbox"][1]
            for b in question.get("layout_blocks", [])
            if b.get("page") == number
            and b.get("type") == "text"
            and b["bbox"][3] > b["bbox"][1]
        ]
        pad = min(12, max(2, median(heights) * 0.6 if heights else 6))
        lower, upper = 35, page["height"] - 45
        for other in dataset["questions"]:
            if other is question:
                continue
            neighbor = content_bounds(other, number)
            if neighbor and neighbor[3] <= box[1]:
                lower = max(lower, (neighbor[3] + box[1]) / 2)
            if neighbor and neighbor[1] >= box[3]:
                upper = min(upper, (neighbor[1] + box[3]) / 2)
        # Existing shared declarations form authoritative boundaries; do not
        # extend padding into a different question's shared stimulus.
        for shared in dataset["shared_information_ranges"]:
            if shared["page"] == number and shared["bbox"][1] >= box[3]:
                upper = min(upper, shared["bbox"][1])
        crop = [
            max(0, box[0] - pad),
            max(lower, box[1] - pad),
            min(page["width"], box[2] + pad),
            min(upper, box[3] + pad),
        ]
        result.append(
            {
                "page": number,
                "bbox": crop,
                "content_bbox": box,
                "method": "owned_layout_body_and_all_options_with_page_neighbor_shared_barriers",
            }
        )
    return result


def refresh(dataset, asset_dir, *, numbers=None):
    root = Path(asset_dir).resolve()
    selected = [
        q
        for q in dataset["questions"]
        if numbers is None or q["question_number"] in numbers
    ]
    requests = {}
    for q in selected:
        q["raw"].setdefault("preview_candidates", deepcopy(q["visual_previews"]))
        q["visual_previews"] = []
        for i, region in enumerate(regions(dataset, q), 1):
            requests.setdefault(region["page"], []).append((q, i, region))
    with pdfium.PdfDocument(dataset["input"]["path"]) as document:
        for number, work in requests.items():
            with (
                closing(document[number - 1]) as page,
                closing(page.render(scale=2, rev_byteorder=True)) as bitmap,
            ):
                pixels = bytes(bitmap.buffer)
                for q, order, region in work:
                    shape = sha256(repr(region["bbox"]).encode()).hexdigest()[:12]
                    stem = f"bmat_{dataset['year']}_q{q['question_number']:03}_p{number:03}_question_only_{shape}"
                    path = root / dataset["input"]["sha256"][:20] / (stem + ".png")
                    dimensions = _save_crop(
                        bitmap, pixels, region["bbox"], page.get_size(), path, False
                    )
                    q["visual_previews"].append(
                        {
                            "image_id": stem,
                            "path": path.relative_to(root.parent).as_posix(),
                            "page": number,
                            "bbox": region["bbox"],
                            "asset_type": "rendered_question",
                            "detected_types": [],
                            "asset_index": order,
                            "order_key": [number, region["bbox"][1], region["bbox"][0]],
                            "source_sha256": dataset["input"]["sha256"],
                            "source": "bmat",
                            "year": dataset["year"],
                            "question_number": q["question_number"],
                            "belongs_to": "question",
                            "option_label": None,
                            "object_ids": [],
                            "notes": [
                                "Question-owned source context only; original preview remains preserved in RAW candidates."
                            ],
                            "warnings": [],
                            "pixel_size": dimensions,
                            "sha256": sha256(path.read_bytes()).hexdigest(),
                            "boundary_evidence": region,
                        }
                    )


def main():
    from .parser import validate_raw

    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("inputs", nargs="+", type=Path)
    cli.add_argument("--question", nargs="+", type=int)
    args = cli.parse_args()
    for path in sorted(
        {
            p
            for root in args.inputs
            for p in (root.glob("*.raw.json") if root.is_dir() else [root])
        }
    ):
        data = json.loads(path.read_text(encoding="utf-8"))
        validate_raw(data)
        refresh(data, path.parent / "assets", numbers=args.question)
        validate_raw(data)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"{data['year']}: source previews refreshed without question reparse",
            flush=True,
        )


if __name__ == "__main__":
    main()
