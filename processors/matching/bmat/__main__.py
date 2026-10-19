import argparse
import json
from pathlib import Path

from .backtest import report
from .core import run


def main(argv=None):
    cli = argparse.ArgumentParser(
        description="BMAT-only matching of current CLEAN and local parsed solutions"
    )
    cli.add_argument("command", choices=["run", "report"])
    cli.add_argument(
        "--supplied-answers",
        type=Path,
        default=Path("data/raw/bmat_supplied_explanations/solutions.answers.json"),
    )
    cli.add_argument("--clean-json", nargs="+", default=["data/clean/bmat"])
    cli.add_argument(
        "--answers",
        type=Path,
        default=Path("data/raw/bmat_worked_solutions/solutions.answers.json"),
    )
    cli.add_argument(
        "--output", type=Path, default=Path("data/merged/bmat/questions.matched.json")
    )
    cli.add_argument(
        "--issues", type=Path, default=Path("docs/BMAT_MATCHING_ISSUES.md")
    )
    cli.add_argument(
        "--guide", type=Path, default=Path("docs/BMAT_MATCHING_BACKTEST.md")
    )
    cli.add_argument(
        "--inspections", type=Path, default=Path("inspections_bmat_matching")
    )
    args = cli.parse_args(argv)
    if args.command == "run":
        result = run(
            args.clean_json,
            args.answers,
            args.output,
            args.supplied_answers if args.supplied_answers.exists() else None,
        )
        print(json.dumps(result["summary"]), flush=True)
    print(
        json.dumps(report(args.output, args.issues, args.guide, args.inspections)),
        flush=True,
    )


if __name__ == "__main__":
    main()
