"""Parse an existing answer-key PDF, independently of generic matching."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from .parser import PROFILE, parse_pdf


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("pdf", type=Path)
    cli.add_argument("--output-dir", type=Path, required=True)
    cli.add_argument("--overwrite", action="store_true")
    args = cli.parse_args(argv)
    try:
        source = args.pdf.resolve(strict=True)
        output_dir = args.output_dir.resolve()
        if output_dir.is_relative_to(source.parent):
            raise ValueError("Raw output must be separate from the source directory")
        digest = sha256(source.read_bytes()).hexdigest()
        output = output_dir / f"{source.stem}-{digest[:12]}.answers.json"
        if output.exists():
            previous = json.loads(output.read_text(encoding="utf-8"))
            if (
                not args.overwrite
                or previous.get("stage") != "answer_raw"
                or previous.get("parser", {}).get("profile") != PROFILE
            ):
                raise ValueError(
                    "Existing output requires --overwrite and the same source profile"
                )
        data = parse_pdf(
            source, asset_dir=output_dir / "assets", overwrite=args.overwrite
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"{len(data['answers'])} answers; {len(data['issues'])} issues -> {output}"
        )
    except (OSError, ValueError, TypeError, KeyError) as error:
        cli.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
