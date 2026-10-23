"""Offline PP-FormulaNet secondary reads for selected local formula crops."""

import argparse
import json
import os
from pathlib import Path


def payload_text(value):
    """Read formula text from PaddleX result shapes without guessing a key."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in (
            "rec_formula",
            "prunedResult",
            "rec_text",
            "latex",
            "formula",
            "text",
        ):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for key in ("res", "formula_res_list", "result", "results", "data"):
            if key not in value:
                continue
            text = payload_text(value[key])
            if text:
                return text
        for key, candidate in value.items():
            if key in {"input_path", "image", "img", "path", "page_index"}:
                continue
            if not isinstance(candidate, (dict, list, tuple)):
                continue
            text = payload_text(candidate)
            if text:
                return text
    if isinstance(value, (list, tuple)):
        for candidate in value:
            text = payload_text(candidate)
            if text:
                return text
    return ""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.model_dir.is_dir():
        parser.error(
            f"Local PP-FormulaNet model directory is missing: {args.model_dir}"
        )
    model_dir = next(
        (
            path.parent
            for path in [
                args.model_dir / "inference.yml",
                *args.model_dir.rglob("inference.yml"),
            ]
            if (path.parent / "inference.pdiparams").is_file()
        ),
        None,
    )
    if model_dir is None:
        parser.error(
            f"No complete local PP-FormulaNet model found under {args.model_dir}"
        )
    os.environ.update(
        {
            "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "True",
            "HF_HUB_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "DO_NOT_TRACK": "1",
        }
    )
    from paddleocr import FormulaRecognitionPipeline

    pipeline = FormulaRecognitionPipeline(
        formula_recognition_model_name="PP-FormulaNet_plus-S",
        formula_recognition_model_dir=str(model_dir.resolve()),
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_layout_detection=False,
        device="cpu",
    )
    output = []
    for entry in json.loads(args.manifest.read_text(encoding="utf8")):
        if not Path(entry["path"]).is_file():
            raise ValueError("Secondary formula crop is missing")
        predictions = pipeline.predict(entry["path"])
        texts = [payload_text(getattr(item, "json", item)) for item in predictions]
        recognized = [text for text in texts if text]
        output.append(
            {**entry, "recognized_latex": recognized, "model": "PP-FormulaNet_plus-S"}
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )


if __name__ == "__main__":
    main()
