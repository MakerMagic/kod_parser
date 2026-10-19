import argparse
import json
from pathlib import Path

from .parser import parse_manifest


def main():
    cli = argparse.ArgumentParser(
        description="Parse only locally acquired BMAT worked solutions"
    )
    cli.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/input/bmat_worked_solutions/manifest.json"),
    )
    cli.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/bmat_worked_solutions/solutions.answers.json"),
    )
    args = cli.parse_args()
    from .image_header import read_header

    result = parse_manifest(
        args.manifest,
        asset_dir=args.output.parent / "assets",
        image_header=lambda asset: read_header(
            asset, args.output.parent / "image_headers"
        ),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "parsed": len(result["answers"]),
                "unresolved": len(result["unresolved_sources"]),
            }
        )
    )


if __name__ == "__main__":
    main()
