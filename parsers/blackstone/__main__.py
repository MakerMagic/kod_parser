"""Run the raw parser on files or a directory of existing PDFs."""

import argparse
import json
import sys
from pathlib import Path

from pdfminer.pdfdocument import PDFEncryptionError, PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError

from .backtest import write_report
from .parser import parse_pdf


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Existing PDFs or directories (searched recursively)",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/blackstone"))
    parser.add_argument(
        "--issues-report",
        type=Path,
        help="Separate Markdown issues report (default: OUTPUT_DIR/PARSING_ISSUES.md)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing raw outputs explicitly",
    )
    args = parser.parse_args(argv)
    failed = False
    written = 0
    files = {}
    for item in args.inputs:
        if not item.exists():
            print(f"Input does not exist: {item}", file=sys.stderr)
            failed = True
            continue
        candidates = (
            sorted(
                p for p in item.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"
            )
            if item.is_dir()
            else [item]
        )
        for candidate in candidates:
            files[candidate.resolve()] = (
                files.get(candidate.resolve(), False) or item.is_file()
            )
    for path, explicit in files.items():
        try:
            result = parse_pdf(path)
            if not explicit and not result["extraction"]["recognized_question_paper"]:
                print(f"Skipped unrecognized question paper: {path}", file=sys.stderr)
                continue
            args.output_dir.mkdir(parents=True, exist_ok=True)
            output = (
                args.output_dir
                / f"{path.stem}-{result['input']['sha256'][:12]}.raw.json"
            )
            with output.open(
                "w" if args.overwrite else "x", encoding="utf-8"
            ) as handle:
                json.dump(result, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            written += 1
            question_warnings = sum(
                bool(question["warnings"]) for question in result["questions"]
            )
            print(
                f"{path.name}: {len(result['questions'])} questions, {question_warnings} flagged records -> {output}"
            )
            for warning in result["warnings"]:
                print(f"  warning: {warning}")
            if not result["questions"] or any(
                warning.startswith("question_count_mismatch")
                for warning in result["warnings"]
            ):
                failed = True
        except (
            OSError,
            ValueError,
            TypeError,
            PDFSyntaxError,
            PDFEncryptionError,
            PDFPasswordIncorrect,
        ) as error:
            print(f"Failed {path}: {type(error).__name__}: {error}", file=sys.stderr)
            failed = True
    if not written:
        print("No raw outputs written", file=sys.stderr)
        failed = True
    else:
        report = args.issues_report or args.output_dir / "PARSING_ISSUES.md"
        try:
            issues = write_report([args.output_dir], report)
            print(f"Parsing issues: {len(issues)} review rows -> {report}")
        except (OSError, ValueError, TypeError) as error:
            print(
                f"Raw outputs written, but issues report failed: {error}",
                file=sys.stderr,
            )
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
