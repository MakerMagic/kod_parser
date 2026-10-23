"""Independently extract local mathematics PDFs; no matching or HTML export."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from .source import VERSION, implementation_hash, parse_pdf


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inputs", nargs="+", type=Path)
    p.add_argument("--output-dir", type=Path, default=Path("data/raw/mathematics"))
    p.add_argument("--overwrite", action="store_true")
    p.add_argument(
        "--question",
        type=int,
        action="append",
        help="Re-extract only selected questions in an existing RAW source",
    )
    a = p.parse_args(argv)
    files = sorted(
        {
            p.resolve()
            for x in a.inputs
            for p in (x.glob("*.pdf") if x.is_dir() else [x])
        },
        key=lambda p: p.name,
    )
    if not files:
        p.error("No local math sources selected")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    for source in files:
        digest = sha256(source.read_bytes()).hexdigest()
        target = a.output_dir / f"{source.stem}_{digest[:12]}.raw.json"
        if a.question:
            if not target.exists() or not a.overwrite:
                p.error(
                    "Targeted extraction requires existing RAW JSON and --overwrite"
                )
            old = json.loads(target.read_text(encoding="utf8"))
            requested = set(a.question)
            if not requested <= {q["question_number"] for q in old["questions"]}:
                p.error("Selected question not present in the existing RAW source")
            updated = parse_pdf(
                source, asset_dir=a.output_dir / "assets", question_numbers=requested
            )
            replacements = {q["question_number"]: q for q in updated["questions"]}
            old["questions"] = [
                replacements.get(q["question_number"], q) for q in old["questions"]
            ]
            selected_glyphs = {
                gid for q in updated["questions"] for gid in q["raw"]["glyph_ids"]
            }
            advances = {
                c["id"]: c
                for page in updated["pages"]
                for c in page["glyphs"]
                if c["id"] in selected_glyphs and "pdf_text_x0" in c
            }
            for page in old["pages"]:
                for c in page["glyphs"]:
                    if c["id"] in advances:
                        for key in ("pdf_text_x0", "pdf_text_x1"):
                            c[key] = advances[c["id"]][key]
            old["schema_version"] = updated["schema_version"]
            updates = old["extraction"].setdefault("question_updates", {})
            for number in sorted(requested):
                updates[str(number)] = updated["extraction"]
            target.write_text(
                json.dumps(old, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
            )
            print(source.name, "updated questions", sorted(requested), flush=True)
            continue
        if target.exists() and not a.overwrite:
            old = json.loads(target.read_text(encoding="utf8"))
            if (
                old["source_document"]["sha256"] == digest
                and old["extraction"]["version"] == VERSION
                and old["extraction"].get("implementation_sha256")
                == implementation_hash()
            ):
                print(source.name, "cached", flush=True)
                continue
            raise FileExistsError(target)
        data = parse_pdf(source, asset_dir=a.output_dir / "assets")
        target.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )
        print(
            source.name,
            len(data["questions"]),
            "questions",
            len(data["answer_key"]["entries"]),
            "key entries",
            flush=True,
        )


if __name__ == "__main__":
    main()
