"""Clean eligible stored mathematics RAW; no source extraction or matching."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from .artifacts import generate
from .cleaner import clean_dataset


def write(path, data):
    if path.exists():
        old = json.loads(path.read_text(encoding="utf8"))
        if old.get("domain") != "mathematics" or old.get("stage") != data["stage"]:
            raise ValueError("Refusing unrelated existing output")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
        newline="\n",
    )


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--raw-json", nargs="+", type=Path, required=True)
    cli.add_argument("--output-dir", type=Path, default=Path("data/clean/mathematics"))
    cli.add_argument("--docs-dir", type=Path)
    args = cli.parse_args(argv)
    paths = sorted(
        {
            p.resolve()
            for value in args.raw_json
            for p in (value.glob("*.raw.json") if value.is_dir() else [value])
        }
    )
    if not paths:
        cli.error("No mathematics RAW JSON selected")
    outputs = [args.output_dir / "questions.json", args.output_dir / "validation.json"]
    if any(
        p.resolve() in paths or p.resolve().is_relative_to(Path("data/raw").resolve())
        for p in outputs
    ):
        raise ValueError("Cleaning cannot overwrite RAW")
    before = {p: sha256(p.read_bytes()).hexdigest() for p in paths}
    existing = (
        json.loads(outputs[0].read_text(encoding="utf8"))
        if outputs[0].is_file()
        else None
    )
    run_stats = {}
    data, validation = clean_dataset(paths, existing, run_stats=run_stats)
    if any(
        sha256(p.read_bytes()).hexdigest() != digest for p, digest in before.items()
    ):
        raise ValueError("RAW changed during cleaning")
    write(outputs[0], data)
    write(outputs[1], validation)
    docs_dir = args.docs_dir or (
        Path("docs/mathematics")
        if args.output_dir.resolve() == Path("data/clean/mathematics").resolve()
        else args.output_dir
    )
    generate(data, validation, docs_dir)
    print(json.dumps({**data["summary"], "run": run_stats}))
    return int(bool(data["summary"]["review"]))


if __name__ == "__main__":
    raise SystemExit(main())
