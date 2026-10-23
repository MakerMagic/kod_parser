"""Explicit preparation of public OCR weights, never acquisition of source PDFs."""

import argparse
import json
import urllib.request
from hashlib import sha256
from pathlib import Path

MODELS = {
    "cnocr-ppocr-en_PP-OCRv3": ["en_PP-OCRv3_rec_infer.onnx"],
    "cnstd-ppocr-en_PP-OCRv3_det": ["en_PP-OCRv3_det_infer.onnx"],
    "pix2text-mfd-1.5": ["pix2text-mfd-1.5.onnx"],
    "pix2text-mfr-1.5": [
        "config.json",
        "decoder_model.onnx",
        "encoder_model.onnx",
        "generation_config.json",
        "preprocessor_config.json",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
    ],
    "pix2text-layout-docyolo": ["doclayout_yolo_docstructbench_imgsz1024.pt"],
}


def normalize_detector(path):
    """Symbolic dimensions remain dynamic; no nodes/weights/pixels are changed.

    CnSTD 1.2.8 compares input dimensions numerically and fails on symbolic names.
    ONNX's equivalent numeric dynamic dimensions let that check work correctly.
    """
    import onnx

    model = onnx.load(str(path))
    graph = model.graph.SerializeToString()
    for item in model.graph.input:
        for dimension in item.type.tensor_type.shape.dim:
            if dimension.HasField("dim_param"):
                dimension.ClearField("dim_param")
                dimension.dim_value = -1
    output = path.with_name("en_PP-OCRv3_det_dynamic.onnx")
    onnx.save(model, str(output))
    return {
        "source_sha256": sha256(path.read_bytes()).hexdigest(),
        "normalized_sha256": sha256(output.read_bytes()).hexdigest(),
        "original_graph_sha256": sha256(graph).hexdigest(),
        "method": "symbolic_dynamic_input_dimensions_to_numeric_dynamic",
    }


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--models", type=Path, default=Path("data/input/mathematics_ocr/models")
    )
    cli.add_argument(
        "--download",
        action="store_true",
        help="Explicitly fetch missing public model weights; no source question is uploaded",
    )
    args = cli.parse_args(argv)
    manifest = {}
    for repo, names in MODELS.items():
        for name in names:
            file = args.models / repo / name
            if not file.is_file():
                if not args.download:
                    cli.error(
                        f"Missing local weight: {file}; use --download explicitly"
                    )
                file.parent.mkdir(parents=True, exist_ok=True)
                url = f"https://huggingface.co/breezedeus/{repo}/resolve/main/{name}"
                temporary = file.with_suffix(file.suffix + ".partial")
                print("Downloading public model", repo, name, flush=True)
                with (
                    urllib.request.urlopen(url, timeout=60) as response,
                    temporary.open("wb") as stream,
                ):
                    while chunk := response.read(1024 * 1024):
                        stream.write(chunk)
                temporary.replace(file)
            manifest[f"{repo}/{name}"] = sha256(file.read_bytes()).hexdigest()
    original = args.models / "cnstd-ppocr-en_PP-OCRv3_det/en_PP-OCRv3_det_infer.onnx"
    manifest["detector_metadata_normalization"] = normalize_detector(original)
    (args.models.parent / "model_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf8"
    )
    print("Local model files verified; question data was not transmitted", flush=True)


if __name__ == "__main__":
    main()
