"""Parse a local worked-solutions PDF independently of matching."""

import argparse
import json
from pathlib import Path

from .parser import parse_pdf


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("pdf", type=Path)
    cli.add_argument(
        "--output-dir", type=Path, default=Path("data/raw/explained_answers")
    )
    cli.add_argument("--overwrite", action="store_true")
    args = cli.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Target names include the content digest, not filename-only identity.
    from hashlib import sha256

    digest = sha256(args.pdf.read_bytes()).hexdigest()
    output = args.output_dir / f"{args.pdf.stem}-{digest[:12]}.answers.json"
    if output.exists() and not args.overwrite:
        cli.error("Answer output exists; use --overwrite or an isolated directory")
    data = parse_pdf(
        args.pdf, asset_dir=args.output_dir / "assets", overwrite=args.overwrite
    )
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(data['answers'])} Section 1 entries -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
