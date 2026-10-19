"""BMAT CLEAN -> targeted task categorization; never parse/match source PDFs."""

import argparse
import json
from pathlib import Path

from .backtest import report
from .core import build, write


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=["run", "report"])
    cli.add_argument("--clean-json", nargs="+", default=["data/clean/bmat"])
    cli.add_argument(
        "--matched-json",
        type=Path,
        default=Path("data/merged/bmat/questions.matched.json"),
    )
    cli.add_argument(
        "--output",
        type=Path,
        default=Path("data/categorized/bmat/questions.categorized.json"),
    )
    cli.add_argument(
        "--issues", type=Path, default=Path("docs/BMAT_CATEGORIZATION_ISSUES.md")
    )
    cli.add_argument(
        "--guide", type=Path, default=Path("docs/BMAT_CATEGORIZATION_BACKTEST.md")
    )
    cli.add_argument(
        "--inspections", type=Path, default=Path("inspections_bmat_categorization")
    )
    args = cli.parse_args(argv)
    if args.command == "run":
        write(
            args.output,
            build(
                args.clean_json,
                args.matched_json if args.matched_json.exists() else None,
            ),
        )
    print(json.dumps(report(args.output, args.issues, args.guide, args.inspections)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
