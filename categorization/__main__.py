"""Independent matched -> categorization CLI. No provider/PDF processing."""

import argparse
from pathlib import Path

from .backtest import load_categorized, report, save_inspection, update_guide
from .core import (
    MARKER,
    ROOT,
    categorize,
    compare_previous,
    file_ref,
    freeze,
    load_handoff,
    read,
    train,
    validate_output,
    write_json,
)


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--matched-json", type=Path, nargs="+", required=True)
    f.add_argument("--output", type=Path, required=True)
    f.add_argument("--overwrite", action="store_true")
    t = sub.add_parser("train")
    t.add_argument("--handoff", type=Path, required=True)
    t.add_argument("--annotations", type=Path, default=ROOT / "seed_review.json")
    t.add_argument("--output", type=Path, required=True)
    t.add_argument("--overwrite", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--handoff", type=Path, required=True)
    r.add_argument("--model", type=Path, required=True)
    r.add_argument("--output", type=Path, required=True)
    r.add_argument(
        "--issues-report", type=Path, default=Path("docs/critical_thinking_problem_solving/tsa/categorization_issues.md")
    )
    r.add_argument("--overwrite", action="store_true")
    r.add_argument(
        "--review-from",
        type=Path,
        help="Previous reviewed output; carry only content-equivalent assessments outside new semantic families",
    )
    r.add_argument(
        "--review-manifest",
        type=Path,
        help="New content-bound review manifest after an intentional upstream refresh",
    )
    r.add_argument(
        "--compare-with",
        type=Path,
        help="Previous categorized output or saved QA baseline; comparison only",
    )
    i = sub.add_parser("inspect")
    i.add_argument("--categorized-json", type=Path, required=True)
    i.add_argument("--year", type=int, required=True)
    i.add_argument("--question", type=int, required=True)
    i.add_argument("--format", choices=["html", "json"], default="html")
    i.add_argument("--output", type=Path, required=True)
    i.add_argument("--overwrite", action="store_true")
    p = sub.add_parser("report")
    p.add_argument("--categorized-json", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("docs/critical_thinking_problem_solving/tsa/categorization_issues.md"))
    p.add_argument("--backtest-guide", type=Path)
    p.add_argument(
        "--review-inspections-dir",
        type=Path,
        help="Regenerate owned HTML inspections for every record in the frozen review pass",
    )
    b = sub.add_parser(
        "bind-review", help="Bind a complete authored review to frozen input content"
    )
    b.add_argument("--baseline", type=Path, required=True)
    b.add_argument("--manifest", type=Path, required=True)
    b.add_argument("--decisions", type=Path, required=True)
    b.add_argument("--output", type=Path, required=True)
    b.add_argument("--overwrite", action="store_true")
    v = sub.add_parser(
        "review",
        help="Apply only the frozen for-review set; never retrain/recategorize other rows",
    )
    v.add_argument("--baseline", type=Path, required=True)
    v.add_argument("--annotations", type=Path, required=True)
    v.add_argument("--output", type=Path, required=True)
    v.add_argument(
        "--issues-report", type=Path, default=Path("docs/critical_thinking_problem_solving/tsa/categorization_issues.md")
    )
    v.add_argument("--overwrite", action="store_true")
    args = cli.parse_args(argv)
    try:
        if args.command == "freeze":
            data = freeze(args.matched_json)
            write_json(
                args.output,
                data,
                overwrite=args.overwrite,
                protected=[*data["inputs"], *data["dependencies"]],
            )
            print(data["summary"])
        elif args.command == "train":
            h = load_handoff(args.handoff)
            data = train(h, read(args.annotations))
            data["annotation_reference"] = file_ref(args.annotations)
            write_json(
                args.output,
                data,
                overwrite=args.overwrite,
                protected=[*h["inputs"], *h["dependencies"]],
            )
            print(
                f"{len(data['examples'])} reviewed examples; model={data['model_sha256']}"
            )
        elif args.command == "run":
            if bool(args.review_from) != bool(args.review_manifest):
                raise ValueError(
                    "Review refresh requires both --review-from and --review-manifest"
                )
            if (
                args.output.exists()
                and read(args.output).get("review_reference")
                and not args.review_from
            ):
                raise ValueError(
                    "Reviewed output is protected; use the review command to reproduce it, not classifier overwrite"
                )
            h = load_handoff(args.handoff)
            data = categorize(h, args.handoff, read(args.model))
            data["model_reference"] = file_ref(args.model)
            if args.review_from:
                from .review import refresh_review

                previous = read(args.review_from)
                validate_output(previous)
                manifest = refresh_review(data, previous, args.review_from)
                write_json(
                    args.review_manifest,
                    manifest,
                    overwrite=args.overwrite,
                    protected=[
                        *h["inputs"],
                        *h["dependencies"],
                        file_ref(args.review_from),
                    ],
                )
                data["review_reference"] = file_ref(args.review_manifest)
            if args.compare_with:
                compare_previous(
                    data, read(args.compare_with), file_ref(args.compare_with)
                )
            validate_output(data)
            # Preflight both destinations before any output is written.
            from .core import safe_output

            safe_output(args.issues_report, [*h["inputs"], *h["dependencies"]])
            if args.issues_report.suffix.lower() != ".md":
                raise ValueError("Issues report must have .md extension")
            if args.issues_report.exists() and not args.issues_report.read_text(
                encoding="utf-8"
            ).startswith(f"<!-- {MARKER} -->"):
                raise ValueError("Refusing to overwrite an unrelated report")
            write_json(
                args.output,
                data,
                overwrite=args.overwrite,
                protected=[*h["inputs"], *h["dependencies"]],
            )
            report(data, args.issues_report)
            from .core import verify_refs

            verify_refs([*h["inputs"], *h["dependencies"]])
            print(data["summary"])
        elif args.command in {"bind-review", "review"}:
            from .review import apply_review, bind_decisions

            baseline = load_categorized(args.baseline)
            h = load_handoff(baseline["handoff_reference"]["path"])
            if args.command == "bind-review":
                data = bind_decisions(read(args.manifest), baseline, args.decisions)
            else:
                annotations = read(args.annotations)
                if file_ref(args.baseline) != annotations["baseline_reference"]:
                    raise ValueError("Review baseline path/content conflict")
                data = apply_review(baseline, annotations, args.annotations)
                compare_previous(data, baseline, file_ref(args.baseline))
                validate_output(data)
                from .core import safe_output

                safe_output(args.issues_report, [*h["inputs"], *h["dependencies"]])
                if args.issues_report.suffix.lower() != ".md" or (
                    args.issues_report.exists()
                    and not args.issues_report.read_text(encoding="utf-8").startswith(
                        f"<!-- {MARKER} -->"
                    )
                ):
                    raise ValueError("Refusing to overwrite unrelated issues report")
            write_json(
                args.output,
                data,
                overwrite=args.overwrite,
                protected=[*h["inputs"], *h["dependencies"], file_ref(args.baseline)],
            )
            if args.command == "review":
                report(data, args.issues_report)
                print(data["review_summary"])
        elif args.command == "inspect":
            save_inspection(
                load_categorized(args.categorized_json),
                year=args.year,
                question=args.question,
                output=args.output,
                format=args.format,
                overwrite=args.overwrite,
            )
            print(args.output)
        else:
            data = load_categorized(args.categorized_json)
            report(data, args.output)
            if args.review_inspections_dir:
                reviewed = [
                    r
                    for r in data["records"]
                    if r.get("rulebook_review") or r.get("previous_categorization")
                ]
                if not reviewed:
                    raise ValueError("No persisted rulebook review to inspect")
                cache = {}
                for index, row in enumerate(reviewed, 1):
                    year = row["identity"]["year"]
                    question = row["identity"]["question_number"]
                    save_inspection(
                        data,
                        year=year,
                        question=question,
                        output=args.review_inspections_dir
                        / f"{year}_q{question:03}.html",
                        overwrite=True,
                        cache=cache,
                    )
                    if index % 10 == 0 or index == len(reviewed):
                        print(
                            f"Review inspections: {index}/{len(reviewed)}", flush=True
                        )
            if args.backtest_guide:
                update_guide(data, args.backtest_guide)
    except (OSError, ValueError, KeyError, TypeError) as error:
        cli.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
