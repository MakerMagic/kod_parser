"""Separate clean output contracts and raw-directory write protection."""

import json
from pathlib import Path

from .cleaner import validate_clean
from .option_assets import prepare_option_assets


def clean_files(references):
    files = []
    for reference in references:
        path = Path(reference).resolve(strict=True)
        files.extend(sorted(path.rglob("*.clean.json")) if path.is_dir() else [path])
    files = list(dict.fromkeys(files))
    if not files:
        raise ValueError("No clean JSON files found")
    return files


def load_clean(path):
    dataset = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_clean(dataset)
    return dataset


def protect_output(output, raw_paths):
    output = Path(output).resolve()
    for reference in raw_paths:
        raw = Path(reference).resolve()
        if output == raw or output.is_relative_to(raw.parent):
            raise ValueError(
                "Clean/inspection/report output must be outside raw input directories"
            )
    if output.suffix.lower() == ".pdf" or output.name.endswith(".raw.json"):
        raise ValueError("Cleaning cannot write PDF or raw JSON output")
    return output


def write_clean(dataset, output, *, overwrite=False):
    validate_clean(dataset)
    output = protect_output(output, [dataset["raw_reference"]["path"]])
    if not output.name.endswith(".clean.json"):
        raise ValueError("Clean output must end in .clean.json")
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    if output.exists() and overwrite:
        previous = load_clean(output)
        if previous["raw_reference"]["path"] != dataset["raw_reference"]["path"]:
            raise ValueError(
                "Refusing to overwrite output belonging to another raw input"
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    dataset = prepare_option_assets(dataset, output)
    validate_clean(dataset)
    with output.open("w" if overwrite else "x", encoding="utf-8") as handle:
        json.dump(dataset, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return output
