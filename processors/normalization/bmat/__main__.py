"""Independent BMAT cleaning CLI; local stored RAW JSON only."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from .cleaner import clean_dataset


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--raw-json", nargs="+", type=Path, required=True)
    cli.add_argument("--output-dir", type=Path, default=Path("data/clean/bmat"))
    cli.add_argument("--overwrite", action="store_true")
    args = cli.parse_args(argv)
    paths = sorted(
        {
            p.resolve()
            for value in args.raw_json
            for p in (value.glob("*.raw.json") if value.is_dir() else [value])
        }
    )
    if not paths:
        cli.error("No RAW files selected")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        digest = sha256(path.read_bytes()).hexdigest()
        data = json.loads(path.read_text(encoding="utf-8"))
        output = args.output_dir / (path.name.removesuffix(".raw.json") + ".clean.json")
        if output.resolve() == path:
            raise ValueError("Cannot overwrite RAW input")
        if output.exists():
            previous = json.loads(output.read_text(encoding="utf-8"))
            if (
                not args.overwrite
                or previous.get("cleaning", {}).get("processor") != "bmat"
                or previous["document"]["input"]["sha256"] != data["input"]["sha256"]
            ):
                raise ValueError("Refusing unrelated/existing clean output")
        result = clean_dataset(data, path, raw_sha256=digest)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("RAW input changed")
        print(
            f"{data['year']}: {len(result['questions'])} clean records -> {output}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
