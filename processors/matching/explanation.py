"""Derive a reading view from source blocks, never from component display order."""

import re
from copy import deepcopy
from itertools import pairwise


def _text(value):
    """Comparison only: the stored/rendered content is never normalized here."""
    return " ".join(value.split())


def _refs(block):
    return block.get("line_refs", []) or [
        ref for item in block.get("items", []) for ref in item.get("line_refs", [])
    ]


def _range(block):
    refs = _refs(block)
    if not refs or any(
        not all(type(ref.get(k)) is int for k in ("page", "start", "end"))
        for ref in refs
    ):
        return None
    return min((r["page"], r["start"]) for r in refs), max(
        (r["page"], r["end"]) for r in refs
    )


def build_final_explanation(answer, answer_reference=None):
    """Keep source snapshots intact; uncertain leftovers never acquire a fake order.

    Component arrays are projections of ``blocks``, not additional content. Exact
    block/provenance equality prevents alias duplication without deleting genuine
    repetitions at different source positions. All pointers are answer-relative.
    """
    result = {
        "status": "unavailable",
        "ordering": "not_applicable",
        "blocks": [],
        "unplaced_components": [],
        "omitted_artifacts": [],
        "deduplicated_blocks": [],
        "source_reference": deepcopy(answer_reference),
        "source_warnings": deepcopy((answer or {}).get("warnings", [])),
        "issues": [],
        # Every source/manual explanation is explicitly non-AI.  An approved
        # text-only overlay replaces this derived view with True provenance.
        "explanation_by_ai": False,
        "source_type": "source_or_manual",
    }
    if not answer:
        result["reason"] = "no_unique_answer_selected"
        return result
    explanation = answer.get("explanation", {})
    if explanation.get("availability") == "not_supplied_by_source_format":
        result["reason"] = "not_supplied_by_source_format"
        return result

    def issue(code, reason, pointer=None):
        item = {"code": code, "reason": reason, "manual_review_required": True}
        if pointer:
            item["source_pointer"] = pointer
        if item not in result["issues"]:
            result["issues"].append(item)

    entries = []

    def add(block, pointer):
        # Only deduplicate exact aliases, not repeated words/sentences.
        for previous, original in entries:
            if block == previous and (
                (type(block.get("order")) is int and block["order"] > 0) or _refs(block)
            ):
                result["deduplicated_blocks"].append(
                    {"source_pointer": pointer, "represented_by": original}
                )
                return
        entries.append((deepcopy(block), pointer))

    for index, block in enumerate(explanation.get("blocks", [])):
        add(block, f"/explanation/blocks/{index}")

    canonical = bool(entries)
    for field in ("paragraphs", "bulleted_blocks", "other_lists"):
        for index, block in enumerate(explanation.get(field, [])):
            if any(
                block == existing
                and (canonical or not pointer.startswith(f"/explanation/{field}/"))
                for existing, pointer in entries
            ):
                continue
            pointer = f"/explanation/{field}/{index}"
            if canonical:
                result["unplaced_components"].append(
                    {"source_pointer": pointer, "value": deepcopy(block)}
                )
                issue(
                    "final_explanation_content_unplaced",
                    "A component has no identical source block; retained separately without guessing placement.",
                    pointer,
                )
            else:
                add(block, pointer)

    main = explanation.get("main_explanation", "")
    paragraphs = explanation.get("paragraphs", [])
    if main and _text(main) != _text("\n\n".join(p["text"] for p in paragraphs)):
        if not entries:
            add(
                {"type": "paragraph", "role": "main", "text": main},
                "/explanation/main_explanation",
            )
        else:
            # Never append this aggregate alongside paragraphs that may cover it.
            result["unplaced_components"].append(
                {"source_pointer": "/explanation/main_explanation", "value": main}
            )
            issue(
                "final_explanation_content_unplaced",
                "Main text disagrees with paragraph projection; original aggregate retained for review.",
            )

    for index, choice in enumerate(explanation.get("choice_analysis", [])):
        label = choice.get("label")
        represented = any(
            block.get("type") == "list"
            and block.get("role", "").startswith("incorrect_choices")
            and block.get("order") == choice.get("list_order")
            and any(
                item.get("label") == label
                and item.get("line_refs", []) == choice.get("line_refs", [])
                and _text(
                    re.sub(
                        r"^" + re.escape(label or "") + r"\s*[-–—.:)]\s*",
                        "",
                        item["text"],
                        count=1,
                    )
                )
                == _text(choice["text"])
                for item in block.get("items", [])
            )
            for block, _ in entries
        )
        if not represented:
            pointer = f"/explanation/choice_analysis/{index}"
            result["unplaced_components"].append(
                {"source_pointer": pointer, "value": deepcopy(choice)}
            )
            issue(
                "final_explanation_content_unplaced",
                "Option-specific explanation is not represented by an ordered list item.",
                pointer,
            )

    ordered = True
    orders = [block.get("order") for block, _ in entries]
    if (
        entries
        and all(type(n) is int and n > 0 for n in orders)
        and len(set(orders)) == len(orders)
    ):
        entries.sort(key=lambda pair: pair[0]["order"])
        result["ordering"] = "source_block_order"
    elif len(entries) == 1:
        result["ordering"] = "single_block"
    elif entries:
        ranges = [_range(block) for block, _ in entries]
        if all(ranges) and all(
            left[1] <= right[0] for left, right in pairwise(sorted(ranges))
        ):
            entries.sort(key=lambda pair: _range(pair[0])[0])
            result["ordering"] = "source_line_order"
        else:
            ordered = False
            result["ordering"] = "unresolved"
            issue(
                "final_explanation_order_uncertain",
                "No unique block order or non-overlapping source spans; components retained, no combined order asserted.",
            )

    # Source spans can contradict even explicit ordinal metadata. Do not hide it.
    positioned = [_range(block) for block, _ in entries if _range(block)]
    if ordered and any(left[1] > right[0] for left, right in pairwise(positioned)):
        ordered = False
        result["ordering"] = "unresolved"
        issue(
            "final_explanation_order_uncertain",
            "Block order conflicts with source text spans.",
        )

    assets = explanation.get("visual_assets", [])
    indices = [a.get("asset_index") for a in assets]
    for block, pointer in entries:
        if (
            block.get("type") == "visual"
            and indices.count(block.get("asset_index")) != 1
        ):
            issue(
                "final_explanation_visual_unresolved",
                "Visual block has no unique saved explanation asset.",
                pointer,
            )
    for index, asset in enumerate(assets):
        if not any(
            b.get("type") == "visual"
            and b.get("asset_index") == asset.get("asset_index")
            for b, _ in entries
        ):
            pointer = f"/explanation/visual_assets/{index}"
            result["unplaced_components"].append(
                {"source_pointer": pointer, "value": deepcopy(asset)}
            )
            issue(
                "final_explanation_visual_unresolved",
                "Saved visual has no ordered explanation block.",
                pointer,
            )

    seen_paragraphs = set()
    paragraph_texts = {
        _text(b.get("text", "")) for b, _ in entries if b.get("type") == "paragraph"
    }
    for block, pointer in entries:
        if not ordered:
            result["unplaced_components"].append(
                {"source_pointer": pointer, "value": block}
            )
            continue
        if block.get("role") == "list_marker_artifact":
            result["omitted_artifacts"].append(
                {"source_pointer": pointer, "value": block}
            )
            continue
        # A transition is usually both a paragraph and list metadata: render once.
        transition = block.get("transition")
        if (
            transition
            and _text(transition) not in seen_paragraphs
            and _text(transition) in paragraph_texts
        ):
            issue(
                "final_explanation_order_uncertain",
                "Transition metadata refers to a later paragraph; source order retained without inserting a duplicate.",
                pointer,
            )
        elif transition and _text(transition) not in seen_paragraphs:
            result["blocks"].append(
                {
                    "type": "paragraph",
                    "role": "choice_transition",
                    "text": transition,
                    "source_pointer": pointer + "/transition",
                }
            )
            seen_paragraphs.add(_text(transition))
        if block.get("type") == "paragraph":
            seen_paragraphs.add(_text(block.get("text", "")))
        elif block.get("type") not in ("list", "visual"):
            issue(
                "final_explanation_content_unplaced",
                "Unsupported block type retained for inspection.",
                pointer,
            )
        result["blocks"].append({**block, "source_pointer": pointer})

    result["status"] = (
        "uncertain"
        if result["issues"] or result["source_warnings"]
        else "available"
        if result["blocks"]
        else "unavailable"
    )
    if not result["blocks"] and not result["unplaced_components"]:
        result["reason"] = "explanation_content_unavailable"
    return result
