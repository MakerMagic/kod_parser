"""Independent matching, structured validation and explicitly selected inspections."""

import argparse
import json
from pathlib import Path

from .core import build, load, validate, write


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("inputs", nargs="+", type=Path)
    run.add_argument(
        "--output", type=Path, default=Path("data/merged/mathematics/questions.json")
    )
    run.add_argument(
        "--validation-output",
        type=Path,
        default=Path("data/merged/mathematics/validation.json"),
    )
    view = sub.add_parser("inspect")
    check = sub.add_parser("validate")
    retry = sub.add_parser(
        "retry", help="Retry only records without a validated matched answer"
    )
    retry.add_argument(
        "--validation-output",
        type=Path,
        default=Path("data/merged/mathematics/validation.json"),
    )
    retry.add_argument(
        "--retry-output",
        type=Path,
        default=Path("data/merged/mathematics/retry_validation.json"),
    )
    for cmd in (view, check, retry):
        cmd.add_argument(
            "--input", type=Path, default=Path("data/merged/mathematics/questions.json")
        )
    view.add_argument("--source")
    view.add_argument("--question", type=int)
    view.add_argument("--id", dest="identifier")
    view.add_argument("--issues", action="store_true")
    view.add_argument("--issue-code")
    view.add_argument("--sample", type=int)
    view.add_argument("--seed", type=int, default=0)
    view.add_argument("--width", type=int, choices=(1166, 1350), default=1166)
    view.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    if args.command == "run":
        paths = sorted(
            {
                p
                for x in args.inputs
                for p in (x.glob("*.raw.json") if x.is_dir() else [x])
            }
        )
        if not paths:
            p.error("No mathematics RAW JSON selected")
        if args.output.resolve() in {x.resolve() for x in paths}:
            raise ValueError("Matching cannot overwrite RAW")
        data = build(paths)
        write(args.output, data)
        write(args.validation_output, validate(data))
        print(json.dumps(data["summary"]))
    elif args.command == "retry":
        from .retry import retry_unmatched

        old = load(args.input)
        data, report = retry_unmatched(old)
        if data != old:
            write(args.input, data)
        write(args.validation_output, validate(data))
        write(args.retry_output, report)
        print(json.dumps(report, ensure_ascii=False))
    elif args.command == "validate":
        result = validate(load(args.input))
        print(json.dumps(result, ensure_ascii=False))
        return int(bool(result["problems"]))
    else:
        from .backtest import render_report, select

        data = load(args.input)
        rows = select(
            data,
            **{
                k: getattr(args, k)
                for k in (
                    "source",
                    "question",
                    "identifier",
                    "issues",
                    "issue_code",
                    "sample",
                    "seed",
                )
            },
        )
        if args.output.exists() or args.output.resolve().is_relative_to(
            Path("data").resolve()
        ):
            raise ValueError("Inspection needs a fresh output outside canonical data")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            render_report(data, rows, width=args.width), encoding="utf8"
        )
        print(len(rows), "selected previews ->", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
