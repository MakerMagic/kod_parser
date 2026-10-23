"""Persist validated content-bound mathematics classifications from CLEAN."""

import argparse
import json
from pathlib import Path

from categorization.core import file_ref, read

from .artifacts import generate
from .core import build


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clean-json", type=Path, default=Path("data/clean/mathematics/questions.json")
    )
    parser.add_argument(
        "--assessments",
        type=Path,
        default=Path("data/categorized/mathematics/assessments.json"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/categorized/mathematics")
    )
    parser.add_argument("--docs-dir", type=Path)
    args = parser.parse_args(argv)
    clean_ref = file_ref(args.clean_json)
    review_ref = file_ref(args.assessments)
    output = args.output_dir.resolve()
    upstream = args.clean_json.resolve().parent
    project = Path(__file__).resolve().parents[2]
    protected = [
        upstream,
        *(project / "data" / name for name in ("raw", "clean", "merged", "pre_final")),
    ]
    if any(output == path or output.is_relative_to(path) for path in protected):
        raise ValueError("Categorization cannot overwrite upstream or later-stage data")
    targets = [output / "questions.json", output / "validation.json"]
    if args.assessments.resolve() in targets or args.clean_json.resolve() in targets:
        raise ValueError("Output would overwrite an input")
    reviews = read(args.assessments)
    if reviews.get("stage") != "mathematics_semantic_assessments":
        raise ValueError("Expected content-bound mathematics semantic assessments")
    previous = read(targets[0]) if targets[0].exists() else None
    data, validation = build(args.clean_json, reviews["assessments"], previous)
    data["assessment_reference"] = review_ref
    if (
        file_ref(args.clean_json) != clean_ref
        or file_ref(args.assessments) != review_ref
    ):
        raise ValueError("Input changed during categorization; no output written")
    output.mkdir(parents=True, exist_ok=True)
    for path, value in zip(targets, (data, validation)):
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    generate(targets[0], args.docs_dir)
    print(json.dumps(data["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
