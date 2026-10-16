"""Import one explicitly approved manual JSON source into the answer contract.

Never infer missing explanations or modify PDF-derived answer intermediates.
"""

import argparse
import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path


def parse_manual(path):
    path = Path(path).resolve(strict=True)
    original = path.read_bytes()
    data = json.loads(original)
    if (
        data.get("origin") != "user_supplied_manual"
        or data.get("approval") != "single_question"
    ):
        raise ValueError("Manual source must explicitly approve one question")
    key = data["target_question_key"]
    for field in ("year", "section", "question_number"):
        if key[field] != data[field]:
            raise ValueError("Manual source identity conflicts with target question")
    text = data["explanation_text"]
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Manual explanation is missing; no automatic content fallback")
    if data["correct_answer"] not in tuple("ABCDE"):
        raise ValueError("Explicit correct answer is required; no answer inference")
    related = deepcopy(data["related_source_document"])
    related["path"] = str((path.parent / related["path"]).resolve(strict=True))
    if sha256(Path(related["path"]).read_bytes()).hexdigest() != related["sha256"]:
        raise ValueError("Related explanation source has changed")
    related["filename"] = Path(related["path"]).name
    evidence = []
    for item in data.get("evidence", []):
        item = deepcopy(item)
        item["path"] = str((path.parent / item["path"]).resolve(strict=True))
        if sha256(Path(item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Manual explanation evidence has changed")
        evidence.append(item)
    digest = sha256(original).hexdigest()
    source = {
        "path": str(path),
        "filename": path.name,
        "sha256": digest,
        "media_type": "application/json",
        "origin": data["origin"],
        "related_sources": [related, *evidence],
    }
    provenance = {
        k: data[k]
        for k in (
            "origin",
            "approval",
            "supplied_by",
            "verification",
            "correct_answer_origin",
        )
    }
    provenance["text_reference"] = {
        "path": str(path),
        "sha256": digest,
        "json_pointer": "/explanation_text",
    }
    if data.get("replaces_explanation"):
        provenance["replaces_explanation"] = deepcopy(data["replaces_explanation"])
    if data.get("preserved_source_fragments"):
        provenance["preserved_source_fragments"] = deepcopy(
            data["preserved_source_fragments"]
        )
    paragraph = {
        "type": "paragraph",
        "role": "main",
        "text": text,
        "line_refs": [],
        "order": 1,
    }
    blocks = deepcopy(data.get("explanation_blocks", [paragraph]))
    raw_parts = []
    for order, block in enumerate(blocks, 1):
        block.update(order=order, line_refs=[])
        if block["type"] == "paragraph" and block.get("role") == "main":
            raw_parts.append(block["text"])
        elif block["type"] == "list" and block.get("role") == "other":
            for item in block["items"]:
                raw = item.get("raw_text", item["text"])
                if re.sub(r"^[-•]\s*", "", raw) != item["text"]:
                    raise ValueError("Manual list item differs from supplied text")
                item["line_refs"] = []
                raw_parts.append(raw)
        else:
            raise ValueError("Unsupported manual explanation block")
    if " ".join(" ".join(raw_parts).split()) != " ".join(text.split()):
        raise ValueError("Manual blocks must preserve the entire supplied explanation")
    paragraphs = [b for b in blocks if b["type"] == "paragraph"]
    lists = [b for b in blocks if b["type"] == "list"]
    answer = {
        "answer_id": f"manual_{digest[:20]}_{data['year']}_{data['section']}_q{data['question_number']}",
        **{
            k: data[k]
            for k in (
                "year",
                "section",
                "question_number",
                "correct_answer",
                "target_question_key",
            )
        },
        "source_document": deepcopy(source),
        "paper": key.get("paper"),
        "variant": key.get("variant"),
        "provenance": provenance,
        "page_reference": {"start_page": None, "end_page": None},
        "raw": {
            "header": None,
            "span_base": "manual_source.explanation_text",
            "page_spans": [],
            "source_excerpt": text,
        },
        "explanation": {
            "main_explanation": "\n\n".join(p["text"] for p in paragraphs),
            "blocks": blocks,
            "paragraphs": paragraphs,
            "bulleted_blocks": lists,
            "choice_analysis": [],
            "other_lists": lists,
            "visual_assets": [],
        },
        "visual_previews": [],
        "warnings": [],
    }
    return {
        "stage": "answer_raw",
        "schema_version": "1",
        "parser": {"profile": "explicit_manual_explanation", "version": "1"},
        "source_document": source,
        "pages": [],
        "boundaries": [],
        "answers": [answer],
        "issues": [],
    }


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--overwrite", action="store_true")
    args = cli.parse_args(argv)
    data = parse_manual(args.source)
    output = args.output.resolve()
    protected = [
        args.source.resolve().parent,
        *[Path(r["path"]).parent for r in data["source_document"]["related_sources"]],
    ]
    if any(
        output.is_relative_to(folder) for folder in protected
    ) or not output.name.endswith(".answers.json"):
        cli.error("Manual intermediate must be a separate .answers.json output")
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if (
            not args.overwrite
            or existing.get("parser", {}).get("profile")
            != "explicit_manual_explanation"
        ):
            cli.error("Refusing to overwrite existing/unrelated output")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"1 explicitly manual explanation -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
