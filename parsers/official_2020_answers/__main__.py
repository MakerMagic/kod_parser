"""Parse a local official 2020 source independently of matching."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from .parser import PROFILE, parse_pdf


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("pdf", type=Path)
    cli.add_argument(
        "--output-dir", type=Path, default=Path("data/raw/official_2020_answers")
    )
    cli.add_argument("--overwrite", action="store_true")
    args = cli.parse_args(argv)
    source, folder = args.pdf.resolve(strict=True), args.output_dir.resolve()
    if folder.is_relative_to(source.parent):
        cli.error("Output must be separate from the source directory")
    digest = sha256(source.read_bytes()).hexdigest()
    output = folder / f"{source.stem}-{digest[:12]}.answers.json"
    if output.exists():
        if not args.overwrite:
            cli.error("Output exists; use --overwrite or a separate directory")
        if (
            json.loads(output.read_text(encoding="utf-8"))
            .get("parser", {})
            .get("profile")
            != PROFILE
        ):
            cli.error("Refusing to replace unrelated JSON")
    data = parse_pdf(source, asset_dir=folder / "assets", overwrite=args.overwrite)
    folder.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"{len(data['answers'])} records; {sum(a['correct_answer'] is not None for a in data['answers'])} resolved -> {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
