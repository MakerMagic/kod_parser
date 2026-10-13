"""Run independent Blackstone cleaning on stored raw JSON only."""

import argparse
import sys
from hashlib import sha256
from pathlib import Path

from parsers.blackstone.backtest import load_raw, raw_files

from .cleaner import clean_dataset
from .issues import write_report
from .storage import protect_output, write_clean


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-json", nargs="+", required=True, type=Path)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/clean/blackstone")
    )
    parser.add_argument(
        "--issues-report", type=Path, default=Path("docs/CLEANING_ISSUES.md")
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace only existing clean outputs for the same raw input",
    )
    args = parser.parse_args(argv)
    try:
        files = raw_files(args.raw_json)
        protect_output(args.output_dir, files)
        protect_output(args.issues_report, files)
        for raw in files:
            digest = sha256(raw.read_bytes()).hexdigest()
            clean = clean_dataset(load_raw(raw), raw, raw_sha256=digest)
            output = args.output_dir / (
                raw.name.removesuffix(".raw.json") + ".clean.json"
            )
            write_clean(clean, output, overwrite=args.overwrite)
            if sha256(raw.read_bytes()).hexdigest() != digest:
                raise ValueError("Raw input changed during cleaning")
            print(f"{raw.name}: {len(clean['questions'])} clean records -> {output}")
        count = write_report([args.output_dir], args.issues_report)
        print(f"Cleaning report: {count} categorized records -> {args.issues_report}")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"Cleaning failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
