"""On-demand mathematics RAW inspection through the established report adapter."""

import argparse
import json
from pathlib import Path

from processors.matching.mathematics.backtest import render_report, select


def load_raw(paths):
    sources, questions = {}, []
    for path in sorted({Path(p).resolve() for p in paths}):
        raw = json.loads(path.read_text(encoding="utf8"))
        if raw.get("stage") != "mathematics_raw" or raw.get("domain") != "mathematics":
            raise ValueError("RAW backtesting accepts mathematics RAW only")
        source = raw["source_document"]
        if source["id"] in sources:
            raise ValueError("Duplicate RAW source identity")
        sources[source["id"]] = source
        questions.extend(raw["questions"])
    if len({q["id"] for q in questions}) != len(questions):
        raise ValueError("Duplicate question IDs")
    return {
        "domain": "mathematics",
        "stage": "mathematics_raw",
        "sources": sources,
        "questions": questions,
    }


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--raw-json", nargs="+", type=Path, default=[Path("data/raw/mathematics")]
    )
    cli.add_argument("--test", type=int)
    cli.add_argument("--source")
    cli.add_argument("--question", type=int)
    cli.add_argument("--id", dest="identifier")
    cli.add_argument("--issues", action="store_true")
    cli.add_argument("--issue-code")
    cli.add_argument("--sample", type=int)
    cli.add_argument("--seed", type=int, default=0)
    cli.add_argument("--width", type=int, choices=(1166, 1350), default=1166)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args(argv)
    paths = [
        p for x in args.raw_json for p in (x.glob("*.raw.json") if x.is_dir() else [x])
    ]
    if not paths:
        cli.error("No mathematics RAW inputs")
    data = load_raw(paths)
    if args.test is not None:
        sources = {
            key: s
            for key, s in data["sources"].items()
            if s["source"] == "sky_trial" and s["version"] == str(args.test)
        }
        data = {
            **data,
            "sources": sources,
            "questions": [
                q for q in data["questions"] if q["source_document_id"] in sources
            ],
        }
    rows = (
        select(
            data,
            source=args.source,
            question=args.question,
            identifier=args.identifier,
            issues=args.issues,
            issue_code=args.issue_code,
            sample=args.sample,
            seed=args.seed,
        )
        if args.test is None
        or any(
            (
                args.source,
                args.question is not None,
                args.identifier,
                args.issues,
                args.issue_code,
                args.sample is not None,
            )
        )
        else data["questions"]
    )
    if not rows:
        cli.error("No selected RAW questions")
    if (
        args.output.exists()
        or args.output.resolve().is_relative_to(Path("data").resolve())
        or args.output.resolve() in {p.resolve() for p in paths}
    ):
        raise ValueError("Inspection needs fresh output outside canonical data")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(data, rows, width=args.width), encoding="utf8")
    print(f"{len(rows)} selected RAW questions -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
