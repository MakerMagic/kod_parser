"""Match existing clean JSON and answer intermediates, without PDF extraction."""

import argparse
import json
from pathlib import Path

from .core import existing_question_source_conflicts, match_records
from .report import write_report
from .storage import load_matched, protect_output


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--clean-json", nargs="+", type=Path, required=True)
    cli.add_argument("--answers-json", nargs="+", type=Path, required=True)
    cli.add_argument(
        "--output",
        type=Path,
        default=Path("data/merged/blackstone/tsa_2008-2016.matched.json"),
    )
    cli.add_argument(
        "--issues-report", type=Path, default=Path("docs/critical_thinking_problem_solving/tsa/MATCHING_2008-2016_ISSUES.md")
    )
    cli.add_argument("--question-source", default="blackstone")
    cli.add_argument("--years", nargs="+", type=int, default=list(range(2008, 2017)))
    cli.add_argument("--overwrite", action="store_true")
    cli.add_argument("--explanation-imports", type=Path)
    cli.add_argument("--visual-explanations", type=Path)
    args = cli.parse_args(argv)
    if args.visual_explanations and not args.explanation_imports:
        cli.error("--visual-explanations requires --explanation-imports")
    if set(args.years) != set(range(2008, 2017)) and (
        args.output.resolve()
        == Path("data/merged/blackstone/tsa_2008-2016.matched.json").resolve()
        or args.issues_report.resolve()
        == Path("docs/critical_thinking_problem_solving/tsa/MATCHING_2008-2016_ISSUES.md").resolve()
    ):
        cli.error(
            "Set separate --output and --issues-report paths for the selected years"
        )
    from processors.normalization.blackstone.storage import clean_files

    from .core import answer_files

    protected = [*clean_files(args.clean_json), *answer_files(args.answers_json)]
    for output in (args.output, args.issues_report):
        if any(output.resolve().is_relative_to(p.parent) for p in protected):
            cli.error("Outputs must be separate from clean/answer input directories")
    if not args.output.name.endswith(".matched.json"):
        cli.error("Merged output must end in .matched.json")
    if args.output.exists() and not args.overwrite:
        cli.error("Merged output exists; use --overwrite or an isolated output")
    if args.output.exists():
        load_matched(args.output)  # Do not replace an unrelated JSON file.
    data = match_records(
        args.clean_json,
        args.answers_json,
        years=set(args.years),
        question_source=args.question_source,
    )
    if args.explanation_imports:
        from .explanation_imports import (
            apply_visuals,
            import_text,
            load_sources,
            write_reports,
        )

        entries, source_warnings = load_sources(args.explanation_imports)
        data, _ = import_text(data, entries)
        data["explanation_imports"]["source_warnings"] = source_warnings
        if args.visual_explanations:
            data = apply_visuals(data, args.visual_explanations)
            write_reports(data, args.visual_explanations, source_warnings)
    if args.output.exists():
        conflicts = existing_question_source_conflicts(data, load_matched(args.output))
        if conflicts:
            data["issues"].extend(conflicts)
            protect_output(data, args.issues_report)
            write_report(data, args.issues_report)
            cli.error(
                "Existing answer/explanation conflicts; matched output left unchanged; see issues report"
            )
    for output in (args.output, args.issues_report):
        protect_output(data, output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(data, args.issues_report)
    from collections import Counter

    print(
        f"Readiness={data['readiness']['ready']}; statuses={dict(Counter(r['status'] for r in data['records']))}; output={args.output}"
    )
    return 0 if data["readiness"]["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
