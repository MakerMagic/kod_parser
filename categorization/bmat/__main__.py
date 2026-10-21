"""BMAT CLEAN -> one canonical dominant category; never parse/match source PDFs."""

import argparse
import json
from pathlib import Path

from .backtest import report
from .core import build, write


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=["run", "report", "bind-review"])
    cli.add_argument("--year", type=int, help="Limit explicitly requested HTML exports")
    cli.add_argument(
        "--question", type=int, help="Limit explicitly requested HTML exports"
    )
    cli.add_argument(
        "--review-json", type=Path, default=Path("categorization/bmat/review.json")
    )
    cli.add_argument(
        "--model-json",
        type=Path,
        default=Path("data/categorized/blackstone/model.json"),
    )
    cli.add_argument(
        "--review-baseline",
        type=Path,
        default=Path("categorization/bmat/review_baseline.json"),
    )
    cli.add_argument(
        "--decisions", type=Path, default=Path("categorization/bmat/decisions.tsv")
    )
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
        "--issues", type=Path, default=Path("docs/critical_thinking_problem_solving/bmat/BMAT_CATEGORIZATION_ISSUES.md")
    )
    cli.add_argument(
        "--guide", type=Path, default=Path("docs/critical_thinking_problem_solving/bmat/BMAT_CATEGORIZATION_BACKTEST.md")
    )
    cli.add_argument(
        "--inspections", type=Path, default=Path("inspections/critical_thinking_problem_solving/bmat/categorization")
    )
    args = cli.parse_args(argv)
    if args.command == "bind-review":
        from .review import bind

        result = bind(args.review_baseline, args.decisions, args.review_json)
        print(json.dumps({"reviewed": len(result["decisions"])}))
        return 0
    if args.command == "run":
        write(
            args.output,
            build(
                args.clean_json,
                args.matched_json if args.matched_json.exists() else None,
                args.review_json if args.review_json.exists() else None,
                args.model_json if args.model_json.exists() else None,
            ),
        )
    print(
        json.dumps(
            report(
                args.output,
                args.issues,
                args.guide,
                args.inspections,
                render=args.command == "report",
                year=args.year,
                question=args.question,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
