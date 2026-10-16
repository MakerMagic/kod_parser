"""Execute one explicit pilot; there is no full-batch command."""

import argparse
from pathlib import Path

from processors.matching.storage import load_matched, protect_output

from .generator import run_pilot, save_snapshot, select_pilot, write_report


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--matched-json", type=Path, required=True)
    cli.add_argument("--question", action="append", required=True, metavar="YEAR:NUMBER")
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--report", type=Path, required=True)
    cli.add_argument("--overwrite", action="store_true")
    args = cli.parse_args(argv)
    try:
        identities = [(int(year), "section_1", int(number)) for year, number in
                      (value.split(":") for value in args.question)]
        data = load_matched(args.matched_json)
        select_pilot(data, identities)
        if not args.output.name.endswith(".matched.json"):
            raise ValueError("Pilot output must end in .matched.json")
        if args.output.exists() and not args.overwrite:
            raise ValueError("Pilot snapshot exists; inspect it or explicitly use --overwrite")
        for path in (args.output, args.report):
            protect_output(data, path, merged_json=args.matched_json)
        if args.report.suffix != ".md":
            raise ValueError("Pilot report must be Markdown")
        # Provider selection is confined to this composition boundary.
        from .providers.gemini import GeminiProvider

        result = run_pilot(data, identities, GeminiProvider(), checkpoint=lambda snapshot: save_snapshot(snapshot, args.output, input_path=args.matched_json))
        write_report(result, args.report)
        print(result["explanation_pilot"]["counts"])
        print("STOP: manual pilot review required; no further questions processed.")
        return 0 if result["explanation_pilot"]["counts"].get("accepted") == len(identities) else 1
    except (ValueError, TypeError, OSError) as error:
        cli.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
