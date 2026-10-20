"""Independently runnable assembly/validation and explicitly selected rendering."""

import argparse
import json
from pathlib import Path

from .core import DEFAULT_INPUTS, run, validate
from .render import inspect
from .storage import ROOT


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--tsa", type=Path, default=ROOT / DEFAULT_INPUTS["TSA"])
    build.add_argument("--bmat", type=Path, default=ROOT / DEFAULT_INPUTS["BMAT"])
    build.add_argument(
        "--output", type=Path, default=ROOT / "data/pre_final/questions.json"
    )
    build.add_argument(
        "--validation-output",
        type=Path,
        default=ROOT / "data/pre_final/validation.json",
    )
    check = commands.add_parser("validate")
    check.add_argument(
        "--input", type=Path, default=ROOT / "data/pre_final/questions.json"
    )
    view = commands.add_parser("inspect")
    view.add_argument(
        "--input", type=Path, default=ROOT / "data/pre_final/questions.json"
    )
    view.add_argument("--id", dest="identifier")
    view.add_argument("--source", choices=["TSA", "BMAT"])
    view.add_argument("--year", type=int)
    view.add_argument("--question", type=int)
    view.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "build":
        result, findings = run(
            {"TSA": args.tsa, "BMAT": args.bmat},
            output=args.output,
            validation_output=args.validation_output,
        )
        print(
            json.dumps(
                {
                    "included": result["summary"],
                    "excluded": findings["excluded_total"],
                    "reasons": findings["reason_counts_overlapping"],
                }
            )
        )
    elif args.command == "validate":
        data = validate(json.loads(args.input.read_text(encoding="utf-8")))
        print(json.dumps(data["summary"]))
    else:
        if any(
            args.output.resolve().is_relative_to(ROOT / "data" / name)
            for name in ("input", "raw", "clean", "merged", "categorized", "pre_final")
        ):
            raise ValueError(
                "Inspection output must be outside canonical data directories"
            )
        if args.output.exists():
            raise FileExistsError("Use a new filename for a user-requested inspection")
        html = inspect(
            args.input,
            identifier=args.identifier,
            source=args.source,
            year=args.year,
            question=args.question,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding="utf-8")
        print(str(args.output))


if __name__ == "__main__":
    main()
