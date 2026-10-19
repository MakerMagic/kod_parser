"""Local, user-supplied BMAT explanation text -> existing answer-RAW contract."""

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path

from processors.matching.core import file_reference

YEAR = re.compile(r"^(20\d{2}):\s*$")
HEADER = re.compile(
    r"^(?:Question\s+(\d+)\s*[—–-]\s*(?:Answer\s+)?|(?:(\d+)\)\s*))([A-H])\s*$",
    re.IGNORECASE,
)
URL = re.compile(r"https?://[^\s)\]]+")


def parse(path):
    path = Path(path).resolve()
    text = path.read_text(encoding="utf-8")
    source = {
        **file_reference(path),
        "source_family": "bmat",
        "source_format": "task_supplied_bmat_explanations",
        "origin": "human_user_message_2026_10_19",
    }
    lines = text.splitlines()
    records, issues, current, year = [], [], None, None

    def finish(end):
        nonlocal current
        if current is None:
            return
        body = lines[current["start"] : end]
        notes, urls, kept = [], [], []
        for line in body:
            if re.match(r"^(?:Source:\s*)?\[", line) and URL.search(line):
                urls.extend(URL.findall(line))
            elif line.startswith("Review required:"):
                notes.append(line)
            else:
                kept.append(line)
                if "CAUTION:" in line or re.search(
                    r"(?:diagrams are needed|essential for visual verification)", line
                ):
                    notes.append(line)
        explanation = "\n".join(kept).strip()
        warnings = ["supplied_explicit_review_required"] if notes else []
        if re.search(
            r"(?m)^[A-H]\s*[–—-]\s*Wrong\s*\nThis option is correct", explanation
        ):
            warnings.append("contradictory_option_annotation")
        if re.search(
            r"(?m)^[A-H]\s*[–—-]\s*(?:Wrong|Correct)", explanation
        ) and re.search(r"(?m)^1\s*[–—-]\s*Wrong", explanation):
            warnings.append("unheaded_numbered_explanation_after_lettered_choices")
        if not explanation:
            warnings.append("explanation_missing")
        blocks = [
            {"type": "paragraph", "role": "full_explanation", "order": i, "text": p}
            for i, p in enumerate(re.split(r"\n\s*\n", explanation), 1)
            if p
        ]
        records.append(
            {
                "source_family": "bmat",
                "source": "bmat",
                "section": "section_1",
                "year": current["year"],
                "question_number": current["number"],
                "correct_answer": current["answer"],
                "source_document": {
                    **source,
                    "source_url": urls[0] if urls else None,
                    "line_start": current["start"],
                    "line_end": end,
                },
                "status": "unresolved" if warnings else "parsed",
                "warnings": warnings,
                "review_notes": notes,
                "answer_extraction": {
                    "method": "user_supplied_explicit_header",
                    "question_number_verified": True,
                    "raw_header": lines[current["start"] - 1],
                },
                "raw": {
                    "content_text": "\n".join(lines[current["start"] - 1 : end]),
                    "header": lines[current["start"] - 1],
                    "boundary": "next_explicit_question_or_year_header",
                },
                "source_assets": [],
                "visual_previews": [],
                "explanation_by_ai": False,
                "explanation": {
                    "presentation": "full_explanation",
                    "blocks": blocks,
                    "paragraphs": deepcopy(blocks),
                    "main_explanation": explanation,
                    "raw_text": explanation,
                    "visual_assets": [],
                    "bulleted_blocks": [],
                    "other_lists": [],
                    "incorrect_answers": [],
                },
            }
        )
        current = None

    for i, line in enumerate(lines):
        if y := YEAR.fullmatch(line):
            finish(i)
            year = int(y[1])
        elif h := HEADER.fullmatch(line):
            finish(i)
            if year is None:
                raise ValueError("Explanation header has no explicit year")
            current = {
                "year": year,
                "number": int(h[1] or h[2]),
                "answer": h[3].upper(),
                "start": i + 1,
            }
        elif current is None and line.strip():
            issues.append(
                {"code": "unassigned_source_text", "line": i + 1, "text": line}
            )
    finish(len(lines))
    return {
        "stage": "answer_raw",
        "source_family": "bmat",
        "source_document": source,
        "answers": records,
        "unresolved_sources": [],
        "issues": issues,
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path)
    cli.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/bmat_supplied_explanations/solutions.answers.json"),
    )
    args = cli.parse_args()
    data = parse(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "records": len(data["answers"]),
                "years": sorted({r["year"] for r in data["answers"]}),
                "review_required": sum(bool(r["warnings"]) for r in data["answers"]),
            }
        )
    )


if __name__ == "__main__":
    main()
