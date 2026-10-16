"""Merged snapshots are separate; inspection never rewrites input datasets."""

import json
from pathlib import Path


def load_matched(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("stage") != "matched" or data.get("schema_version") != "1":
        raise ValueError("Unsupported matched dataset")
    if not isinstance(data.get("records"), list) or not isinstance(
        data.get("issues"), list
    ):
        raise TypeError("Invalid merged record/issue structure")
    return data


def protect_output(data, output, *, merged_json=None):
    path = Path(output).resolve()
    protected = [Path(r["path"]).resolve().parent for r in data["inputs"]]
    if merged_json:
        protected.append(Path(merged_json).resolve().parent)
    for record in data["records"]:
        questions = [
            record.get("question"),
            *[c["record"] for c in record.get("question_candidates", [])],
        ]
        for question in questions:
            if question is None:
                continue
            protected.append(Path(question["raw_reference"]["path"]).resolve().parent)
        for doc in (
            record.get("question_document"),
            (record.get("answer") or {}).get("source_document"),
            *[c["document"] for c in record.get("superseded_answer_candidates", [])],
            *[c["document"] for c in record.get("question_candidates", [])],
            *[c["document"] for c in record.get("answer_candidates", [])],
        ):
            source = (doc or {}).get("input", doc or {})
            if source.get("path"):
                protected.append(Path(source["path"]).resolve().parent)
    if any(path.is_relative_to(folder) for folder in protected):
        raise ValueError("Output must be separate from input/source directories")
