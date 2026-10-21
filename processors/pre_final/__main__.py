"""Independently runnable assembly/validation and explicitly selected rendering."""

import argparse
import json
from pathlib import Path

from .render import inspect
from .storage import ROOT


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument(
        "--tsa",
        type=Path,
        default=ROOT / "data/categorized/blackstone/tsa.categorized.json",
    )
    build.add_argument(
        "--bmat",
        type=Path,
        default=ROOT / "data/categorized/bmat/questions.categorized.json",
    )
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
    view.add_argument("--category")
    view.add_argument("--sample", type=int)
    view.add_argument("--seed", type=int, default=0)
    view.add_argument("--width", type=int, choices=[1166, 1350], default=1166)
    view.add_argument(
        "--open", action="store_true", help="Open the requested preview in the browser"
    )
    view.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "build":
        from .core import run

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
        from .core import validate

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
            category=args.category,
            sample=args.sample,
            seed=args.seed,
            width=args.width,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding="utf-8", newline="\n")
        if args.open:
            import webbrowser

            webbrowser.open(args.output.resolve().as_uri())
        print(str(args.output))


if __name__ == "__main__":
    main()
