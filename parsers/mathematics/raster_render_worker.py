"""Compare local MathML render-backs with original source formula crops."""

import argparse
import json
import math
import os
import subprocess
from pathlib import Path


def trim_and_resize(path, height=96):
    import cv2
    import numpy as np

    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read formula image: {path}")
    ink = image < 210
    ys, xs = np.where(ink)
    if not len(xs):
        raise ValueError(f"Formula image contains no foreground: {path}")
    crop = ink[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1].astype("uint8")
    width = max(1, round(crop.shape[1] * height / crop.shape[0]))
    return cv2.resize(crop, (width, height), interpolation=cv2.INTER_NEAREST)


def shape_comparison(source_path, rendered_path):
    import cv2
    import numpy as np

    source = trim_and_resize(source_path)
    rendered = trim_and_resize(rendered_path)
    width = max(source.shape[1], rendered.shape[1])
    if width > 1800:
        return {
            "passed": False,
            "reason": "Formula shape comparison exceeds safe width",
        }
    left = np.zeros((96, width), dtype="uint8")
    right = np.zeros((96, width), dtype="uint8")
    left[
        :,
        (width - source.shape[1]) // 2 : (width - source.shape[1]) // 2
        + source.shape[1],
    ] = source
    right[
        :,
        (width - rendered.shape[1]) // 2 : (width - rendered.shape[1]) // 2
        + rendered.shape[1],
    ] = rendered
    left_edges = cv2.Canny(left * 255, 40, 120) > 0
    right_edges = cv2.Canny(right * 255, 40, 120) > 0
    if not left_edges.any() or not right_edges.any():
        return {
            "passed": False,
            "reason": "Formula render-back has no comparable contours",
        }
    left_distance = cv2.distanceTransform((~left_edges).astype("uint8"), cv2.DIST_L2, 3)
    right_distance = cv2.distanceTransform(
        (~right_edges).astype("uint8"), cv2.DIST_L2, 3
    )
    chamfer = (
        float(left_distance[right_edges].mean())
        + float(right_distance[left_edges].mean())
    ) / 2
    source_aspect = source.shape[1] / source.shape[0]
    rendered_aspect = rendered.shape[1] / rendered.shape[0]
    aspect_error = abs(math.log(max(1e-6, source_aspect / rendered_aspect)))
    return {
        "passed": False,  # thresholds require calibration on verified source crops
        "method": "symmetric_edge_chamfer_after_height_normalization",
        "symmetric_edge_distance": chamfer,
        "aspect_ratio_error": aspect_error,
        "source_aspect_ratio": source_aspect,
        "rendered_aspect_ratio": rendered_aspect,
        "calibration_status": "diagnostic_only_threshold_not_calibrated",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--node", type=Path, required=True)
    args = parser.parse_args(argv)
    runtime = (
        Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node"
    )
    env = os.environ.copy()
    env["NODE_PATH"] = str(runtime / "node_modules")
    image_dir = args.output.with_suffix("").with_name(args.output.stem + "_images")
    image_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(args.node),
            str(Path(__file__).with_name("raster_formula_render.cjs")),
            str(args.manifest),
            str(image_dir),
        ],
        check=True,
        timeout=180,
        env=env,
    )
    rendered = json.loads((image_dir / "manifest.json").read_text(encoding="utf8"))
    for entry in rendered:
        entry["round_trip_verification"] = shape_comparison(
            entry["source_path"], entry["rendered_path"]
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(rendered, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )


if __name__ == "__main__":
    main()
