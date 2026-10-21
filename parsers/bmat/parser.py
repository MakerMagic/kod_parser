"""Local BMAT PDF -> lossless RAW contract; no acquisition or normal categorization."""

import re
from bisect import bisect_left, bisect_right
from collections import Counter
from hashlib import sha256
from itertools import pairwise
from pathlib import Path
from statistics import median

import pdfplumber

from . import reuse

VERSION = "2"
ADMIN = re.compile(
    r"^(?:©|Copyright|BMAT(?:\s+\d{4}:)?\s*Section\s+1|\[?Turn over|BLANK PAGE|END OF (?:THE\s+)?(?:PAPER|QUESTIONS|TEST|TEXT|SECTION(?:\s+\d+)?)\s*$|_{8,}\s*$|Permission to reproduce)",
    re.IGNORECASE,
)
RANGE = re.compile(
    r"\bQuestions?\s+(\d+)\s*(?:to|through|[-–—]|\(cid:\d+\))\s*(\d+)\s*(?:refer|relate|apply|are based|use|concern)\b",
    re.IGNORECASE,
)
PROMPT = re.compile(
    r"^(?:Which|What|How|Why|When|Where|Who|Select|Choose|Identify|Calculate|Determine|Estimate|Express|Give|Write|State|(?:By|For|At|In|From|On)\s+(?:which|what|how)|To the nearest|Assuming|In the context of|On the basis of)\b",
    re.IGNORECASE,
)


def interpreted(line):
    return line.get("readable_text", line["text"])


def marker(line, kind):
    pattern = r"^(\d{1,2})(?:\s+|$)" if kind == "number" else r"^([A-Z])(?:\s+|$)"
    match = re.match(pattern, interpreted(line))
    if not match:
        return None
    raw = line["text"]
    encoded = re.match(
        r"^(?:\(cid:\d+\)){" + str(len(match[1])) + r"}(?:\(cid:3\)|[ \t])*", raw
    )
    if encoded:
        # Only the number/letter glyphs and immediately following separators.
        # A literal separator may precede an encoded first word containing CID3.
        end = encoded.end()
    else:
        end = match.end()
    return (int(match[1]) if kind == "number" else match[1]), end


def content_lines(page, lines):
    if page["page_number"] == 1:
        return []
    return [
        l
        for l in lines
        if 35 < l["top"]
        and l["bottom"] < page["height"] - 45
        and not ADMIN.match(interpreted(l))
        and not (
            interpreted(l).strip().isdigit()
            and l["x0"] > page["width"] * 0.35
            and (l["top"] < 55 or l["top"] > page["height"] * 0.85)
        )
    ]


def split_fields(block, lines):
    first = marker(lines[0], "number")
    begin = lines[0]["block_start"] + first[1]
    # Pure letter rows require geometric image association later, not text guesses.
    requests = [
        l["block_start"]
        for l in lines[1:]
        if interpreted(l).strip()[:1].isupper() and PROMPT.match(interpreted(l).strip())
    ]
    # Conditional prose inside a completed option is not another question.
    first_option = next(
        (
            l["block_start"]
            for l in lines[1:]
            if (m := marker(l, "option"))
            and m[0] == "A"
            and (len(interpreted(l).split()) > 2 or interpreted(l).strip() == "A")
        ),
        None,
    )
    hard_requests = {
        l["block_start"]
        for l in lines[1:]
        if re.match(
            r"^(?:Which|What|How|Why|Who|Whose|Select|Choose|Identify|Calculate|Determine)\b",
            interpreted(l).strip(),
        )
    }
    requests = [
        r
        for r in requests
        if first_option is None or r < first_option or r in hard_requests
    ]
    final_request = max(requests, default=begin)
    pure = [
        l
        for l in lines[1:]
        if l["block_start"] > final_request
        and re.fullmatch(r"[A-Z](?:\s+[A-Z])+", interpreted(l).strip())
    ]
    candidates = [
        (l, marker(l, "option"))
        for l in lines[1:]
        if l["block_start"] > final_request and marker(l, "option")
    ]
    sequences = []
    for i, (line, m) in enumerate(candidates):
        if m[0] != "A":
            continue
        aligned = [(l, x) for l, x in candidates[i:] if abs(l["x0"] - line["x0"]) <= 4]
        run = []
        for l, x in aligned:
            if x[0] != chr(65 + len(run)):
                break
            run.append((l, x))
        if len(run) >= 3:
            sequences.append(run)
    selected = (
        max(sequences, key=lambda seq: (len(seq), seq[0][0]["block_start"]))
        if sequences
        else []
    )
    if pure and (
        not selected
        or any(
            re.fullmatch(r"[A-Z](?:\s+[A-Z])+", interpreted(l).strip())
            for l, _ in selected
        )
    ):
        rows, labels = [], []
        for line in lines[1:]:
            value = interpreted(line).strip()
            if line["block_start"] <= final_request or not re.fullmatch(
                r"[A-Z](?:\s+[A-Z])*", value
            ):
                continue
            tokens = value.split()
            if tokens == list(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[len(labels) : len(labels) + len(tokens)]
            ):
                rows.append(line)
                labels.extend(tokens)
        if len(labels) >= 3:
            start = rows[0]["block_start"]
            choices = [
                {
                    "label": c,
                    "text": "",
                    "images": [],
                    "warnings": ["empty_option_text:may_be_image_only"],
                }
                for c in labels
            ]
            return (
                block[begin:start],
                block[start:],
                choices,
                [],
                ["multi_column_options:text_and_image_association_unresolved"],
            )
    if not selected and candidates:
        # Mixed chart rows A [axis] B [axis] require geometric recovery later.
        initial = next((i for i, (_, m) in enumerate(candidates) if m[0] == "A"), None)
        if initial is not None:
            selected = candidates[initial:]
    start = selected[0][0]["block_start"] if selected else len(block)
    options = []
    for i, (line, m) in enumerate(selected):
        end = selected[i + 1][0]["block_start"] if i + 1 < len(selected) else len(block)
        text = block[line["block_start"] + m[1] : end]
        options.append(
            {
                "label": m[0],
                "text": text,
                "images": [],
                "warnings": []
                if text.strip()
                else ["empty_option_text:may_be_image_only"],
            }
        )
    warnings = [] if selected else ["options_not_detected:requires_source_inspection"]
    if options and [o["label"] for o in options] != list(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(options)]
    ):
        warnings.append(
            "incomplete_or_ambiguous_options:noncontiguous_label_candidates"
        )
    return block[begin:start], block[start:], options, [], warnings


def raw_components(question):
    """Compatibility entry point for the BMAT-specific structural projection."""
    from .structure import components

    components(question)


def parse_pdf(
    input_path, *, year=None, asset_dir=None, overwrite_assets=False, render=True
):
    path = Path(input_path).resolve(strict=True)
    pages, page_lines, excluded = [], [], {}
    math_layout = {}
    verified_fonts = set()
    with pdfplumber.open(path) as doc:
        metadata = dict(doc.metadata or {})
        for p in doc.pages:
            record, lines = reuse.read_page(p)
            # Preserve compact native separator + surrounding glyph geometry.
            # Fraction interpretation/normalization belongs to CLEAN, not RAW.
            math_layout[p.page_number] = []
            chars_by_x = sorted(p.chars, key=lambda c: c["x0"])
            char_x = [c["x0"] for c in chars_by_x]
            digit_sizes = [c["size"] for c in p.chars if c["text"].isdigit()]
            glyph_scale = median(digit_sizes) if digit_sizes else 12
            separators = [
                {
                    "x0": c["x0"],
                    "x1": c["x1"],
                    "top": c["top"],
                    "bottom": c["bottom"],
                    "pts": [(c["x1"], c["top"]), (c["x0"], c["bottom"])],
                    "separator_glyph": c,
                }
                for c in p.chars
                if c["text"] in {"/", "⁄"}
            ]
            for obj in [*p.lines, *separators]:
                width, height = obj["x1"] - obj["x0"], obj["bottom"] - obj["top"]
                if not (
                    1 < width < glyph_scale * 3 and 0 <= height < glyph_scale * 2.2
                ):
                    continue
                near = [
                    c
                    for c in chars_by_x[
                        bisect_right(char_x, obj["x0"] - 20) : bisect_left(
                            char_x, obj["x1"] + 35
                        )
                    ]
                    if c["text"].strip()
                    and obj["x0"] - 20 < c["x0"] < obj["x1"] + 35
                    and obj["top"] - 15 < c["top"] < obj["bottom"] + 10
                ]
                if sum(c["text"].isdigit() for c in near) < 2:
                    continue
                math_layout[p.page_number].append(
                    {
                        "page": p.page_number,
                        "bbox": [obj["x0"], obj["top"], obj["x1"], obj["bottom"]],
                        "points": [list(point) for point in obj["pts"]],
                        "separator_is_text": bool(obj.get("separator_glyph")),
                        "glyphs": [
                            {
                                k: c[k]
                                for k in (
                                    "text",
                                    "x0",
                                    "x1",
                                    "top",
                                    "bottom",
                                    "size",
                                    "fontname",
                                )
                            }
                            for c in near
                        ],
                    }
                )
            verified = reuse.supports_shifted_cids(record["raw_text"], len(p.chars))
            cid_fonts = {
                c["fontname"] for c in p.chars if c["text"].startswith("(cid:")
            }
            if verified:
                verified_fonts.update(cid_fonts)
            elif cid_fonts and cid_fonts <= verified_fonts:
                verified = True
            from .encoding import annotate_lines

            record["font_interpretation"] = annotate_lines(
                p, lines, verified, reuse.decode_cids
            )
            record["verified_shifted_cids"] = verified
            pages.append(record)
            excluded[record["page_number"]] = [
                l
                for l in lines
                if ADMIN.match(interpreted(l))
                or interpreted(l).strip() == str(record["page_number"])
                and l["x0"] > record["width"] * 0.35
                and (l["top"] < 55 or l["top"] > record["height"] * 0.85)
            ]
            page_lines.append(content_lines(record, lines))
            p.close()
    cover = pages[0]["raw_text"]
    if not re.search(
        r"Bio\s*Medical Admissions Test|Biomedical Admissions Test",
        cover,
        re.IGNORECASE,
    ) or not re.search(r"SECTION\s+1", cover, re.IGNORECASE):
        raise ValueError("Not a verified BMAT Section 1 paper")
    years = {int(v) for v in re.findall(r"\b20\d{2}\b", cover)}
    detected = next(iter(years)) if len(years) == 1 else None
    if year is not None and detected is not None and year != detected:
        raise ValueError("Supplied year conflicts with document cover")
    year = year if year is not None else detected
    if year is None:
        raise ValueError("Year unresolved: supply trusted metadata explicitly")
    expected_match = re.search(r"attempt all\s+(\d+)\s+questions", cover, re.IGNORECASE)
    expected = int(expected_match[1]) if expected_match else None
    paper = re.search(r"\b\d{4}/\d{2}\b", cover)
    dataset = {
        "source": "bmat",
        "year": year,
        "paper": paper[0] if paper else None,
        "variant": None,
        "section": "section_1",
        "document_role": "question_paper",
        "input": {
            "path": str(path),
            "filename": path.name,
            "sha256": sha256(path.read_bytes()).hexdigest(),
        },
        "acquisition": {"method": "unknown", "origin": None},
        "extraction": {
            "parser": "bmat_section_1",
            "parser_version": VERSION,
            "backend": "pdfplumber",
            "backend_version": pdfplumber.__version__,
            "pdf_metadata": metadata,
            "expected_questions": expected,
            "layout_profile": "thinking_skills"
            if "Thinking Skills" in cover
            else "aptitude_and_skills",
        },
        "pages": pages,
        "questions": [],
        "warnings": [],
        "shared_information_ranges": [],
        "unassigned_content": [],
    }
    candidates = [
        l
        for p, ls in zip(pages, page_lines)
        for l in ls
        if (m := marker(l, "number"))
        and 1 <= m[0] <= (expected or 60)
        and l["x0"] < p["width"] * 0.17
        and len(interpreted(l).split()) > 2
    ]
    columns = Counter(round(l["x0"] / 4) * 4 for l in candidates)
    first_labels = [l for l in candidates if marker(l, "number")[0] == 1]
    # Alternating inner/outer print margins differ by about 5.4 pt. Anchor on
    # the first real question's exact position, not a rounded table/subpoint
    # mode that may dominate the entire document.
    column = (
        first_labels[0]["x0"]
        if first_labels
        else columns.most_common(1)[0][0]
        if columns
        else 0
    )
    dataset["extraction"]["number_column_anchor"] = column
    first_box = (
        (first_labels[0].get("word_boxes") or [[0, 0, 6, 0]])[0]
        if first_labels
        else [0, 0, 6, 0]
    )
    tolerance = (first_box[2] - first_box[0]) * 1.5
    dataset["extraction"]["number_column_tolerance"] = tolerance
    pending, records, next_number = None, [], 1
    for page, lines in zip(pages, page_lines):
        if not lines or "BLANK PAGE" in page["raw_text"]:
            continue
        boundaries = {}
        for i, line in enumerate(lines):
            m = marker(line, "number")
            if m and abs(line["x0"] - column) <= tolerance and m[0] == next_number:
                boundaries[i] = m[0]
                next_number += 1
        ranges = {}
        for i, line in enumerate(lines):
            if not re.search(r"\bQuestions?\s+\d+", interpreted(line), re.IGNORECASE):
                continue
            declaration = interpreted(line)
            if i + 1 < len(lines):
                declaration += " " + interpreted(lines[i + 1])
            match = RANGE.search(declaration)
            if match:
                wrapped = match.end() > len(interpreted(line))
                entry = {
                    "start_question": int(match[1]),
                    "end_question": int(match[2]),
                    "page": page["page_number"],
                    "raw_text": line["text"]
                    + ("\n" + lines[i + 1]["text"] if wrapped else ""),
                    "bbox": [line["x0"], line["top"], line["x1"], line["bottom"]],
                    "affected_question_ids": [],
                }
                dataset["shared_information_ranges"].append(entry)
                if (
                    not 1
                    <= entry["start_question"]
                    <= entry["end_question"]
                    <= (expected or 100)
                ):
                    dataset["warnings"].append(
                        f"shared_information_range_unresolved:{entry['start_question']}-{entry['end_question']}"
                    )
                ranges[i] = entry
        cuts = sorted({0, len(lines), *boundaries, *ranges})
        for begin, end in pairwise(cuts):
            if begin in ranges:
                pending = None
            if begin in boundaries:
                pending = {
                    "number": boundaries[begin],
                    "segments": [],
                    "lines": [],
                    "images": [],
                }
                records.append(pending)
            start, stop = lines[begin]["start"], lines[end - 1]["end"]
            if end == len(lines):
                # Retain in-question terminal controls in the exact RAW span;
                # only the structured projection excludes them later.
                terminal = [
                    l["end"]
                    for l in excluded[page["page_number"]]
                    if l["start"] >= stop
                    and re.match(r"^(?:END OF|_{8,})", interpreted(l), re.IGNORECASE)
                    and l["bottom"] < page["height"] - 45
                ]
                stop = max([stop, *terminal])
            box = [
                0,
                max(35, lines[begin]["top"] - 6),
                page["width"],
                lines[end]["top"] - 6 if end < len(lines) else page["height"] - 45,
            ]
            segment = {
                "page": page["page_number"],
                "start": start,
                "end": stop,
                "bbox": box,
                "text": page["raw_text"][start:stop],
            }
            if pending is None:
                dataset["unassigned_content"].append(segment)
                continue
            offset = sum(len(s["text"]) + 1 for s in pending["segments"])
            pending["segments"].append(segment)
            pending["lines"].extend(
                {
                    **l,
                    "page": page["page_number"],
                    "block_start": offset + l["start"] - start,
                }
                for l in lines[begin:end]
            )
            pending["images"].extend(
                {**o, "belongs_to": "question"}
                for o in page["images"]
                if o["bbox"][1] < box[3] and o["bbox"][3] >= box[1]
            )
    repair_displaced_numbers(records, pages)
    for pending in records:
        pending["math_layout"] = [
            item
            for segment in pending["segments"]
            for item in math_layout.get(segment["page"], [])
            if segment["bbox"][1] <= item["bbox"][1] <= segment["bbox"][3]
        ]
        block = "\n".join(s["text"] for s in pending["segments"])
        text, options_block, options, subpoints, warnings = split_fields(
            block, pending["lines"]
        )
        from .encoding import decode_block

        text = decode_block(text, pending["lines"])
        for option in options:
            option["text"] = decode_block(option["text"], pending["lines"])
        key = {k: dataset[k] for k in ("source", "year", "paper", "variant", "section")}
        key["question_number"] = pending["number"]
        q = {
            "question_id": f"bmat_{year}_{dataset['paper'] or 'unspecified'}_section_1_q{pending['number']}",
            "source_question_key": key,
            "question_number": pending["number"],
            "page_reference": {
                "start_page": pending["segments"][0]["page"],
                "end_page": pending["segments"][-1]["page"],
            },
            "raw": {
                "question_block": block,
                "options_block": options_block,
                "page_spans": [
                    {k: v for k, v in s.items() if k != "text"}
                    for s in pending["segments"]
                ],
                "extraction_notes": [
                    "Exact default extraction spans; verified CID interpretation is additive only."
                ],
            },
            "question_text": text,
            "options": options,
            "subpoints": subpoints,
            "images": pending["images"],
            "warnings": warnings,
        }
        from .text_options import recover

        recover(
            q,
            pending,
            marker,
            lambda s, context=pending["lines"]: decode_block(s, context),
        )
        from .option_evidence import (
            inline_layout,
            recover_spatial_text,
            reject_data_rows,
        )

        reject_data_rows(q, pending)
        recover_spatial_text(q, pending)
        inline_layout(q, pending)
        question_marks = [l for l in pending["lines"] if "?" in interpreted(l)]
        request_end = question_marks[-1] if question_marks else None
        answer_objects = [
            i
            for i in pending["images"]
            if not i.get("decorative")
            and (
                request_end is None
                or i["page"] > request_end["page"]
                or i["page"] == request_end["page"]
                and i["bbox"][1] > request_end["bottom"]
            )
        ]
        audit_lines = [
            l
            for l in pending["lines"]
            if request_end is None or l["block_start"] > request_end["block_start"]
        ]
        q["option_audit"] = {
            "verified_dataset_rows_not_options": bool(
                q["raw"].get("option_rejection_evidence")
            ),
            "cover_allows_write_in": bool(
                re.search(r"write in words or numbers", cover, re.IGNORECASE)
            ),
            "possible_label_lines": sum(
                marker(l, "option") is not None
                or bool(re.match(r"^[A-Z][.)]\s", interpreted(l)))
                for l in audit_lines
            ),
            "meaningful_native_objects": sum(
                not i.get("decorative") for i in pending["images"]
            ),
            "answer_region_native_objects": len(answer_objects),
            "text_complete": not re.search(r"\(cid:|\ufffd", text),
            "bounded_by_numbered_items": pending["number"] < (expected or 0),
        }
        dataset["questions"].append(q)
    from .stabilize import mark_trailing_rules

    mark_trailing_rules(dataset, records)
    if render:
        # RAW provenance may have several stream fragments on one page. The
        # shared visual extractor expects one owning geometry per question/page;
        # otherwise a tiny number-only fragment marks that page's chart foreign.
        visual_records = []
        for pending in records:
            by_page = {}
            for segment in pending["segments"]:
                number, box = segment["page"], segment["bbox"]
                if number not in by_page:
                    by_page[number] = {**segment, "bbox": list(box)}
                else:
                    old = by_page[number]["bbox"]
                    by_page[number]["bbox"] = [
                        min(old[0], box[0]),
                        min(old[1], box[1]),
                        max(old[2], box[2]),
                        max(old[3], box[3]),
                    ]
            visual_records.append({**pending, "segments": list(by_page.values())})
        reuse.save_visuals(
            dataset,
            visual_records,
            asset_dir or Path("data/raw/bmat/assets"),
            overwrite=overwrite_assets,
            asset_prefix="bmat",
        )
        from .visuals import guard_body_boundary, recover_centered_options

        recover_centered_options(
            dataset,
            records,
            asset_dir or Path("data/raw/bmat/assets"),
            overwrite_assets,
        )
        from .option_evidence import recover_inline_cells

        recover_inline_cells(
            dataset, records, asset_dir or Path("data/raw/bmat/assets")
        )
        from .stabilize import recover_math_options, revise_visuals

        revise_visuals(dataset, records, asset_dir or Path("data/raw/bmat/assets"))
        recover_math_options(
            dataset, records, asset_dir or Path("data/raw/bmat/assets")
        )
        from .stabilize import recover_oriented_labels

        recover_oriented_labels(
            dataset, records, asset_dir or Path("data/raw/bmat/assets")
        )
        from .stabilize import reunite_swatch_legends

        reunite_swatch_legends(
            dataset, records, asset_dir or Path("data/raw/bmat/assets")
        )
    for q, pending in zip(dataset["questions"], records):
        if render:
            guard_body_boundary(q, pending)
            reuse.attach_visual_text(q, pending["lines"])
            reuse.add_layout(q, pending)
            by_span = {l["block_start"]: l for l in pending["lines"]}
            for layout in q["layout_blocks"]:
                if layout["type"] == "text":
                    line = by_span[layout["raw_span"]["start"]]
                    layout["readable_text"] = interpreted(line)
        else:
            q["visual_assets"], q["visual_previews"] = [], []
        # Shared exact-span admin projection: no source character is removed
        # from raw blocks/pages, and CID decoding remains a separate projection.
        end = len(q["raw"]["question_block"]) - len(q["raw"]["options_block"])
        begin = marker(pending["lines"][0], "number")[1]
        q["raw"]["text_question_candidate"] = q["raw"]["question_block"][begin:end]
        reuse.project_admin_exclusions(q, pending, excluded, [])
        q["question_text"] = decode_block(q["question_text"], pending["lines"])
        from .stabilize import project_visual_text

        project_visual_text(q, pending, excluded)
        from .structure import components

        components(q)
    if render:
        from .previews import refresh

        refresh(dataset, asset_dir or Path("data/raw/bmat/assets"))
    if [q["question_number"] for q in dataset["questions"]] != list(
        range(1, (expected or len(records)) + 1)
    ):
        dataset["warnings"].append(
            f"question_number_or_count_mismatch:expected_{expected}_found_{len(records)}"
        )
    from .skip_rules import annotate

    annotate(dataset)
    from .quality import findings

    base = Path(asset_dir or "data/raw/bmat/assets").resolve().parent
    for q in dataset["questions"]:
        q["parsing_issues"] = [
            {
                "code": w.split(":", 1)[0].split(" [", 1)[0],
                "reason": w,
                "manual_review_required": True,
            }
            for w in findings(dataset, q, base / "bmat.raw.json")
        ]
        q["pipeline_status"] = (
            "intentional_skip"
            if q["bmat_filter"]["skip_from_pipeline"]
            else "parser_review"
            if q["parsing_issues"] or dataset["warnings"]
            else "raw_ready"
        )
    validate_raw(dataset)
    return dataset


def repair_displaced_numbers(records, pages):
    """Recover a left-margin number emitted after its same-baseline stimulus.

    PDF stream order can put a standalone number after an entire table. Move
    exact page spans, not prose, and require positive same-baseline geometry.
    Ordinary cross-page answer continuations have no such numbered anchor.
    """
    for previous, current in pairwise(records):
        anchor = current["lines"][0]
        if interpreted(anchor).strip() != str(current["number"]):
            continue
        page = anchor["page"]
        tail = [l for l in previous["lines"] if l["page"] == page]
        if not tail or tail[0]["x0"] <= anchor["x1"]:
            continue
        height = anchor["bottom"] - anchor["top"]
        if abs(tail[0]["top"] - anchor["top"]) > height * 0.3:
            continue
        moved = [s for s in previous["segments"] if s["page"] == page]
        head = current["segments"][0]
        if (
            len(moved) != 1
            or moved[0]["end"] > anchor["start"]
            or not any(s["page"] != page for s in previous["segments"])
        ):
            continue
        raw = pages[page - 1]["raw_text"]
        first = {
            **head,
            "end": anchor["end"],
            "text": raw[anchor["start"] : anchor["end"]],
        }
        first["bbox"] = [anchor["x0"], anchor["top"], anchor["x1"], anchor["bottom"]]
        body = {
            **moved[0],
            "bbox": [
                min(l["x0"] for l in tail),
                min(l["top"] for l in tail),
                max(l["x1"] for l in tail),
                max(l["bottom"] for l in tail),
            ],
        }
        rest_start = anchor["end"]
        if raw[rest_start : rest_start + 1] == "\n":
            rest_start += 1
        rest = {**head, "start": rest_start, "text": raw[rest_start : head["end"]]}
        previous["segments"] = [s for s in previous["segments"] if s["page"] != page]
        previous["lines"] = [l for l in previous["lines"] if l["page"] != page]
        current["segments"] = [first, body, rest, *current["segments"][1:]]
        all_lines = [anchor, *tail, *current["lines"][1:]]
        offset = 0
        ordered = []
        for segment in current["segments"]:
            for line in all_lines:
                if (
                    line["page"] == segment["page"]
                    and segment["start"] <= line["start"] < segment["end"]
                ):
                    ordered.append(
                        {
                            **line,
                            "block_start": offset + line["start"] - segment["start"],
                        }
                    )
            offset += len(segment["text"]) + 1
        current["lines"] = ordered


def validate_raw(dataset):
    reuse.validate_contract(dataset)
    if dataset["source"] != "bmat" or dataset["section"] != "section_1":
        raise ValueError("Invalid BMAT family identity")
    for q in dataset["questions"]:
        flags = q["bmat_filter"]
        if flags["skip_from_pipeline"] != bool(flags["types"]):
            raise ValueError("Skip tags and pipeline flag disagree")
        if flags["status"] == "normal" and not q["options"]:
            raise ValueError(
                "No options must be reviewed or explicitly evidenced as No Question"
            )
