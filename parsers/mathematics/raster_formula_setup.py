"""Prepare local PP-FormulaNet weights; never transfers question images."""

import argparse
import hashlib
import json
import os
import tarfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

MODEL_URL = "https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-FormulaNet_plus-S_infer.tar"
CHUNK_BYTES = 2 * 1024 * 1024


def download_archive(path):
    request = urllib.request.Request(MODEL_URL, method="HEAD")
    with urllib.request.urlopen(request, timeout=30) as response:
        size = int(response.headers["Content-Length"])
        etag = response.headers.get("ETag")
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("wb") as stream:
        stream.truncate(size)
    ranges = [
        (start, min(size, start + CHUNK_BYTES) - 1)
        for start in range(0, size, CHUNK_BYTES)
    ]

    def fetch(bounds):
        start, end = bounds
        headers = {"Range": f"bytes={start}-{end}"}
        if etag:
            headers["If-Range"] = etag
        for attempt in range(3):
            try:
                with urllib.request.urlopen(
                    urllib.request.Request(MODEL_URL, headers=headers), timeout=90
                ) as response:
                    data = response.read()
                    expected = end - start + 1
                    if response.status != 206 or len(data) != expected:
                        raise OSError(
                            f"Range response mismatch for bytes {start}-{end}"
                        )
                    return start, data
            except Exception:
                if attempt == 2:
                    raise

    with temporary.open("r+b") as stream, ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch, bounds) for bounds in ranges]
        for completed, future in enumerate(as_completed(futures), 1):
            start, data = future.result()
            stream.seek(start)
            stream.write(data)
            if completed % 10 == 0 or completed == len(futures):
                print(f"Downloaded {completed}/{len(futures)} model chunks", flush=True)
        stream.flush()
        os.fsync(stream.fileno())
    if temporary.stat().st_size != size:
        raise OSError("Model archive length does not match its HTTP Content-Length")
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("data/input/mathematics_ocr/formulanet_plus_s"),
    )
    parser.add_argument(
        "--download", action="store_true", help="Download public model weights only"
    )
    args = parser.parse_args(argv)
    required = ("inference.yml", "inference.pdiparams")
    if not all((args.model_dir / name).is_file() for name in required):
        if not args.download:
            parser.error("Missing PP-FormulaNet weights; use --download explicitly")
        archive = args.model_dir.with_suffix(".tar")
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.unlink(missing_ok=True)
        download_archive(archive)
        args.model_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as package:
            root = args.model_dir.resolve()
            for member in package.getmembers():
                target = (args.model_dir / member.name).resolve()
                if root not in target.parents and target != root:
                    raise ValueError("Unsafe model archive path")
            package.extractall(args.model_dir, filter="data")
        archive.unlink()
    candidates = [
        args.model_dir,
        *(path.parent for path in args.model_dir.rglob("inference.yml")),
    ]
    model_dir = next(
        (
            directory
            for directory in candidates
            if all((directory / name).is_file() for name in required)
        ),
        args.model_dir,
    )
    missing = [name for name in required if not (model_dir / name).is_file()]
    if missing:
        parser.error(f"Model archive lacks expected inference files: {missing}")
    manifest = {
        "model": "PP-FormulaNet_plus-S",
        "source_url": MODEL_URL,
        "files": {
            name: hashlib.sha256((model_dir / name).read_bytes()).hexdigest()
            for name in required
        },
    }
    (model_dir / "local_model_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf8"
    )
    print(
        f"Local PP-FormulaNet model is ready at {model_dir}; no question images were uploaded"
    )


if __name__ == "__main__":
    main()
