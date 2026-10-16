"""Execute one explicit pilot; there is no full-batch command."""

import argparse
from pathlib import Path

from processors.matching.storage import load_matched, protect_output

from .generator import run_pilot, save_snapshot, select_pilot, write_report


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--matched-json", type=Path, required=True)
    cli.add_argument(
        "--question", action="append", required=True, metavar="YEAR:NUMBER"
    )
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--report", type=Path, required=True)
    cli.add_argument("--overwrite", action="store_true")
    cli.add_argument(
        "--calibration",
        action="store_true",
        help="Explicit small reasoning calibration of 1–4 questions, not a full pilot",
    )
    cli.add_argument(
        "--resume-from",
        type=Path,
        help="Preserve prior results and retry only selected provider-failed/pending pilot questions",
    )
    cli.add_argument(
        "--quality-regenerations",
        type=int,
        choices=(0, 1),
        default=1,
        help="At most one additional generation after local validation rejection",
    )
    args = cli.parse_args(argv)
    try:
        identities = [
            (int(year), "section_1", int(number))
            for year, number in (value.split(":") for value in args.question)
        ]
        data = load_matched(args.matched_json)
        resume = load_matched(args.resume_from) if args.resume_from else None
        if resume is None:
            select_pilot(data, identities, calibration=args.calibration)
        if not args.output.name.endswith(".matched.json"):
            raise ValueError("Pilot output must end in .matched.json")
        if args.output.exists() and not args.overwrite:
            raise ValueError(
                "Pilot snapshot exists; inspect it or explicitly use --overwrite"
            )
        if args.output.exists() and not load_matched(args.output).get(
            "explanation_pilot"
        ):
            raise ValueError("Refusing to replace a non-pilot matched snapshot")
        for path in (args.output, args.report):
            protect_output(data, path, merged_json=args.matched_json)
        if args.report.suffix != ".md":
            raise ValueError("Pilot report must be Markdown")
        if args.report.exists() and not args.report.read_text(
            encoding="utf-8"
        ).startswith("<!-- explanation-pilot-report -->"):
            raise ValueError("Refusing to replace an unrelated report")
        # Provider selection is confined to this composition boundary.
        from .providers.gemini import GeminiProvider

        provider = GeminiProvider()
        print("Generation model: " + provider.model, flush=True)
        result = run_pilot(
            data,
            identities,
            provider,
            resume=resume,
            calibration=args.calibration,
            quality_regenerations=args.quality_regenerations,
            checkpoint=lambda snapshot: save_snapshot(
                snapshot, args.output, input_path=args.matched_json
            ),
        )
        write_report(result, args.report)
        print(result["explanation_pilot"]["counts"])
        metrics = result["explanation_pilot"]["metrics"]
        print(
            f"Generation availability: {metrics['received_output']}/{metrics['selected']}"
        )
        print(
            f"Explanation quality: {metrics['accepted']}/{metrics['quality_evaluated']} accepted (provider failures excluded)"
        )
        print(f"Overall completed: {metrics['accepted']}/{metrics['selected']}")
        print("STOP: manual pilot review required; no further questions processed.")
        return (
            0
            if result["explanation_pilot"]["counts"].get("accepted")
            == metrics["selected"]
            else 1
        )
    except (ValueError, TypeError, OSError) as error:
        cli.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
