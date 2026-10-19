"""Independently parse existing BMAT PDFs; never download or run later stages."""

import argparse
import json
from pathlib import Path

from .parser import parse_pdf


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("inputs", nargs="+", type=Path)
    cli.add_argument("--output-dir", type=Path, default=Path("data/raw/bmat"))
    cli.add_argument("--overwrite", action="store_true")
    cli.add_argument(
        "--no-assets",
        action="store_true",
        help="Diagnostic text probe only; not a completed RAW run",
    )
    args = cli.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    for path in sorted(
        {
            p.resolve()
            for item in args.inputs
            for p in (item.glob("*.pdf") if item.is_dir() else [item])
        }
    ):
        try:
            data = parse_pdf(
                path,
                asset_dir=args.output_dir / "assets",
                overwrite_assets=args.overwrite,
                render=not args.no_assets,
            )
            output = (
                args.output_dir
                / f"bmat_{data['year']}_{data['input']['sha256'][:12]}.raw.json"
            )
            with output.open(
                "w" if args.overwrite else "x", encoding="utf-8"
            ) as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            print(path.name, len(data["questions"]), data["warnings"], flush=True)
            if data["warnings"]:
                failures.append(
                    {
                        "input": str(path),
                        "raw_output": str(output),
                        "error": "Document structural review required",
                        "warnings": data["warnings"],
                    }
                )
        except (OSError, ValueError, TypeError) as error:
            failures.append(
                {"input": str(path), "error": type(error).__name__ + ": " + str(error)}
            )
            print("FAILED", failures[-1], flush=True)
    (args.output_dir / "run_failures.json").write_text(
        json.dumps(failures, indent=2) + "\n", encoding="utf-8"
    )
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
