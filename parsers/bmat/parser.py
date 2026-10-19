"""Local BMAT PDF -> lossless RAW contract; no acquisition or normal categorization."""

import re
from collections import Counter
from hashlib import sha256
from itertools import pairwise
from pathlib import Path

import pdfplumber

from . import reuse

VERSION = "1"
ADMIN = re.compile(
    r"^(?:©|Copyright|BMAT(?:\s+\d{4}:)?\s*Section\s+1|\[?Turn over|BLANK PAGE|END OF (?:PAPER|QUESTIONS)|Permission to reproduce)",
    re.IGNORECASE,
)
RANGE = re.compile(
    r"\bQuestions?\s+(\d+)\s*(?:to|through|[-–—]|\(cid:\d+\))\s*(\d+)\s+(?:refer|relate|apply|are based|use|concern)",
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
    """Raw line-order projection only; no paragraph normalization or rewriting."""
    text = question["question_text"]
    lines = text.splitlines(keepends=True)
    offset, starts = 0, []
    for line in lines:
        if line.strip()[:1].isupper() and PROMPT.match(line.strip()):
            starts.append(offset)
        offset += len(line)
    starts.extend(
        m.start()
        for m in re.finditer(r"\b(?:Which|What|How|Why|Who)\b", text)
        if m.start() == 0 or text[: m.start()].rstrip().endswith((".", "?", "!"))
    )
    starts.extend(
        m.start(1)
        for m in re.finditer(r"(?:^|(?<=[.!?])\s+)([A-Z][^?!.]*\?)", text)
        if re.search(r"\b(?:how|what|which|who|why)\b", m[1], re.IGNORECASE)
    )
    starts.extend(
        m.start()
        for m in re.finditer(r"\b(?:On the basis of|In the context of)\b", text)
        if re.search(
            r"\b(?:which|what|how|deduce)\b",
            text[m.end() : m.end() + 200],
            re.IGNORECASE,
        )
    )
    start = max(starts) if starts else None
    question["raw_components"] = {
        "main_body": text[:start] if start is not None else text,
        "main_question": text[start:] if start is not None else None,
        "method": "last_explicit_request_line" if start is not None else "unresolved",
        "normalization_applied": False,
    }


def parse_pdf(
    input_path, *, year=None, asset_dir=None, overwrite_assets=False, render=True
):
    path = Path(input_path).resolve(strict=True)
    pages, page_lines, excluded = [], [], {}
    with pdfplumber.open(path) as doc:
        metadata = dict(doc.metadata or {})
        for p in doc.pages:
            record, lines = reuse.read_page(p)
            verified = reuse.supports_shifted_cids(record["raw_text"], len(p.chars))
            for line in lines:
                if verified:
                    line["readable_text"] = reuse.decode_cids(line["text"])
                    line["word_texts"] = [
                        reuse.decode_cids(t) for t in line["word_texts"]
                    ]
            record["verified_shifted_cids"] = verified
            pages.append(record)
            excluded[record["page_number"]] = [
                l for l in lines if ADMIN.match(interpreted(l))
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
    for pending in records:
        block = "\n".join(s["text"] for s in pending["segments"])
        text, options_block, options, subpoints, warnings = split_fields(
            block, pending["lines"]
        )
        if any(
            pages[s["page"] - 1]["verified_shifted_cids"] for s in pending["segments"]
        ):
            text = reuse.decode_cids(text)
            for option in options:
                option["text"] = reuse.decode_cids(option["text"])
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
            reuse.decode_cids
            if any(
                pages[s["page"] - 1]["verified_shifted_cids"]
                for s in pending["segments"]
            )
            else lambda s: s,
        )
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
    if render:
        reuse.save_visuals(
            dataset,
            records,
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
    for q, pending in zip(dataset["questions"], records):
        if render:
            guard_body_boundary(q, pending)
            reuse.attach_visual_text(q, pending["lines"])
            reuse.add_layout(q, pending)
        else:
            q["visual_assets"], q["visual_previews"] = [], []
        # Shared exact-span admin projection: no source character is removed
        # from raw blocks/pages, and CID decoding remains a separate projection.
        end = len(q["raw"]["question_block"]) - len(q["raw"]["options_block"])
        begin = marker(pending["lines"][0], "number")[1]
        q["raw"]["text_question_candidate"] = q["raw"]["question_block"][begin:end]
        reuse.project_admin_exclusions(q, pending, excluded, [])
        if any(
            pages[s["page"] - 1]["verified_shifted_cids"] for s in pending["segments"]
        ):
            q["question_text"] = reuse.decode_cids(q["question_text"])
        raw_components(q)
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
