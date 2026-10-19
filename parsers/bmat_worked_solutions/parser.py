"""Parse saved BMAT Section 1 solution HTML, never request a live URL."""

import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from urllib.parse import urljoin

from parsers.html_tree import Node, entry

HEADER = re.compile(r"\s*(\d{1,2})\s*[.)]\s*([A-Z])\s*[.]?\s*", re.IGNORECASE)
TITLE = re.compile(
    r"\b(20\d{2})\s+Section\s*(\d)\s+Question\s*(\d{1,2})\b", re.IGNORECASE
)


def mathematical_text(node):
    if isinstance(node, str):
        return node
    if node.tag == "br":
        return "\n"
    text = "".join(mathematical_text(c) for c in node.children)
    if node.tag in {"sup", "sub"}:
        return ("^{" if node.tag == "sup" else "_{") + text + "}"
    if node.tag == "p":
        return "\n\n" + text + "\n\n"
    return text


def source_blocks(content, base):
    """DOM order, paragraphs/lists/visuals; stop at sharing/like/related widget."""
    blocks, stopped = [], None

    def boundary(n):
        return (
            n.has_class("sharedaddy")
            or n.has_class("sd-sharing")
            or n.has_class("sd-like")
            or n.attrs.get("id") == "jp-relatedposts"
            or n.tag in {"h2", "h3", "h4"}
            and re.fullmatch(r"Share\s+this\s*[:….]*", n.text().strip(), re.IGNORECASE)
        )

    def paragraph(text):
        if text.strip():
            blocks.append(
                {"type": "paragraph", "role": "full_explanation", "text": text.strip()}
            )

    def visit(n):
        nonlocal stopped
        if stopped:
            return
        if isinstance(n, str):
            paragraph(n)
            return
        if boundary(n):
            stopped = "share_or_equivalent_widget"
            return
        if n.tag in {"script", "style"}:
            return
        if n.tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote"}:
            pending = []

            def inline(child):
                if isinstance(child, str):
                    pending.append(child)
                elif child.tag == "img":
                    paragraph("".join(pending))
                    pending.clear()
                    visit(child)
                elif child.tag in {"sup", "sub"}:
                    pending.append(mathematical_text(child))
                elif child.tag == "br":
                    pending.append("\n")
                else:
                    for item in child.children:
                        inline(item)

            for child in n.children:
                inline(child)
            paragraph("".join(pending))
        elif n.tag in {"ul", "ol"}:
            items = [
                {"text": mathematical_text(c).strip(), "label": None}
                for c in n.children
                if isinstance(c, Node) and c.tag == "li"
            ]
            if items:
                for item, child in zip(
                    items,
                    (c for c in n.children if isinstance(c, Node) and c.tag == "li"),
                ):
                    urls = [
                        urljoin(
                            base,
                            v.attrs.get("data-orig-file") or v.attrs.get("src", ""),
                        )
                        for v in child.walk()
                        if v.tag == "img"
                    ]
                    if urls:
                        item["unrepresented_visual_urls"] = urls
                blocks.append(
                    {
                        "type": "list",
                        "role": "full_explanation",
                        "ordered": n.tag == "ol",
                        "items": items,
                    }
                )
        elif n.tag == "table":
            rows = [
                [
                    mathematical_text(c).strip()
                    for c in row.children
                    if isinstance(c, Node) and c.tag in {"td", "th"}
                ]
                for row in n.walk()
                if row.tag == "tr"
            ]
            blocks.append(
                {
                    "type": "paragraph",
                    "role": "table",
                    "text": "\n".join("\t".join(r) for r in rows),
                    "rows": rows,
                }
            )
        elif n.tag == "img":
            url = urljoin(base, n.attrs.get("data-orig-file") or n.attrs.get("src", ""))
            blocks.append(
                {"type": "visual", "source_url": url, "alt": n.attrs.get("alt", "")}
            )
        else:
            for c in n.children:
                visit(c)

    visit(content)
    for i, block in enumerate(blocks, 1):
        block["order"] = i
    return blocks, stopped or "entry_content_end"


def parse_page(
    path,
    *,
    year,
    question_number,
    section="section_1",
    source_url="",
    assets=(),
    asset_dir=None,
    image_header=None,
):
    path = Path(path).resolve()
    payload = path.read_bytes()
    source = {
        "path": str(path),
        "sha256": sha256(payload).hexdigest(),
        "source_url": source_url,
        "source_family": "bmat",
        "source_format": "bmat_wordpress_worked_solutions",
        "explanations_supplied": True,
    }
    record = {
        "source_family": "bmat",
        "source": "bmat",
        "year": year,
        "section": section,
        "question_number": question_number,
        "correct_answer": None,
        "source_document": source,
        "warnings": [],
        "status": "unresolved",
        "raw": {},
        "visual_previews": [],
        "page_reference": {"source_url": source_url},
        "paper": None,
        "variant": None,
    }
    record["source_assets"] = deepcopy(list(assets))

    def reject(code):
        record["warnings"].append(code)
        return record

    if section != "section_1":
        return reject("non_section_1_source")
    try:
        root, content = entry(payload.decode("utf-8-sig"))
    except (ValueError, UnicodeError):
        return reject("source_text_malformed")
    titles = [n.text().strip() for n in root.walk() if n.has_class("entry-title")]
    record["source_title"] = "\n".join(titles)
    parsed_title = TITLE.search(record["source_title"])
    if not parsed_title or tuple(map(int, parsed_title.groups())) != (
        year,
        1,
        question_number,
    ):
        return reject("source_title_identity_mismatch")
    blocks, end = source_blocks(content, source_url)
    record["raw"] = {
        "content_text": content.text(),
        "source_blocks": deepcopy(blocks),
        "boundary": end,
    }
    image_first = bool(blocks and blocks[0]["type"] == "visual")
    if image_first and image_header:
        asset = next(
            (
                a
                for a in assets
                if a["source_url"] == blocks[0]["source_url"]
                and a.get("status") == "acquired"
            ),
            None,
        )
        if (
            not asset
            or sha256(Path(asset["local_path"]).read_bytes()).hexdigest()
            != asset["sha256"]
        ):
            return reject("answer_header_image_unavailable")
        try:
            evidence = image_header(asset)
        except (ValueError, OSError) as error:
            record["raw"]["header_extraction_error"] = str(error)
            return reject("answer_header_image_unresolved")
        record["raw"]["header_extraction"] = evidence
        if evidence.get("source_sha256") != asset["sha256"]:
            return reject("image_header_provenance_mismatch")
        header_text = " ".join(evidence["lines"])
        remainder = []
    elif not blocks or blocks[0]["type"] != "paragraph":
        return reject("answer_header_image_only_or_missing")
    else:
        header_text, *remainder = blocks[0]["text"].split("\n", 1)
    match = HEADER.fullmatch(header_text)
    if not match:
        return reject("malformed_answer_header")
    if int(match[1]) != question_number:
        return reject("header_question_number_mismatch")
    record["correct_answer"] = match[2].upper()
    record["answer_extraction"] = {
        "method": "source_image_header_ocr" if image_first else "html_header",
        "question_number_verified": True,
        "raw_header": header_text,
    }
    record["raw"]["header"] = header_text
    if not image_first:
        blocks.pop(0)
    if remainder and remainder[0].strip():
        blocks.insert(
            0, {"type": "paragraph", "role": "full_explanation", "text": remainder[0]}
        )
    visual_assets = []
    supplied = {a["source_url"]: a for a in assets}
    if any(
        i.get("unrepresented_visual_urls") for b in blocks for i in b.get("items", [])
    ):
        record["warnings"].append("inline_list_visual_requires_review")
    for i, block in enumerate(blocks, 1):
        block["order"] = i
        if block["type"] != "visual":
            continue
        asset = supplied.get(block["source_url"], {})
        local = Path(asset.get("local_path", "__unavailable__"))
        if (
            asset.get("status") != "acquired"
            or not local.is_file()
            or sha256(local.read_bytes()).hexdigest() != asset.get("sha256")
        ):
            record["warnings"].append("explanation_asset_missing_or_changed")
            continue
        if local.suffix != ".png":
            if local.suffix not in {".jpg", ".jpeg"} or asset_dir is None:
                record["warnings"].append("explanation_asset_requires_rendering")
                continue
            from PIL import Image

            target = Path(asset_dir) / (asset["sha256"] + ".png")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                with Image.open(local) as image:
                    image.convert("RGB").save(target, format="PNG")
            local = target
        index = len(visual_assets) + 1
        from parsers.blackstone.visual_inspection import read_png

        try:
            read_png(local)
        except (OSError, ValueError):
            record["warnings"].append("explanation_asset_invalid_png")
            continue
        visual_assets.append(
            {
                "asset_index": index,
                "path": str(local.resolve()),
                "sha256": sha256(local.read_bytes()).hexdigest(),
                "original_source": deepcopy(asset),
                "source_url": block["source_url"],
                "page": 1,
                "bbox": None,
            }
        )
        block["asset_index"] = index
    raw_text = "\n\n".join(
        b.get("text", "\n".join(x["text"] for x in b.get("items", [])))
        for b in blocks
        if b["type"] != "visual"
    )
    paragraphs = [deepcopy(b) for b in blocks if b["type"] == "paragraph"]
    record["explanation"] = {
        "presentation": "full_explanation",
        "blocks": blocks,
        "main_explanation": "\n\n".join(b["text"] for b in paragraphs),
        "raw_text": raw_text,
        "paragraphs": paragraphs,
        "bulleted_blocks": [],
        "choice_analysis": [],
        "other_lists": [],
        "visual_assets": visual_assets,
    }
    if not blocks:
        return reject("explanation_missing")
    record["status"] = "parsed" if not record["warnings"] else "unresolved"
    return record


def parse_manifest(path, *, asset_dir=None, image_header=None):
    path = Path(path).resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (
        manifest.get("source_family") != "bmat"
        or manifest.get("section") != "section_1"
    ):
        raise ValueError("Not a BMAT Section 1 acquired manifest")
    result = {
        "stage": "answer_raw",
        "schema_version": "1",
        "source_family": "bmat",
        "parser": "bmat_wordpress_v2",
        "source_document": {
            "path": str(path),
            "sha256": sha256(path.read_bytes()).hexdigest(),
        },
        "answers": [],
        "unresolved_sources": [],
        "issues": deepcopy(manifest["issues"]),
    }
    for row in manifest["questions"]:
        if row.get("source_family") != "bmat" or row.get("section") != "section_1":
            raise ValueError("Acquired row is not a BMAT Section 1 source")
        if row["status"] != "acquired":
            result["unresolved_sources"].append(row)
            continue
        local = Path(row["local_path"])
        if sha256(local.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Acquired HTML changed: " + str(local))
        record = parse_page(
            local,
            year=row["year"],
            question_number=row["question_number"],
            source_url=row["source_url"],
            assets=row.get("assets", []),
            asset_dir=asset_dir,
            image_header=image_header,
        )
        result[
            "answers" if record["status"] == "parsed" else "unresolved_sources"
        ].append(record)
    return result
