"""Stored-evidence RAW quality gate, separate from intentional exclusions."""

import re

from .reuse import visual_issues


def findings(data, question, path):
    issues = []
    no_choices_expected = any(
        t["type"] == "No Question" for t in question["bmat_filter"]["types"]
    )
    for w in question["warnings"]:
        if (
            w.startswith("graphics_present:")
            or no_choices_expected
            and w.startswith("options_not_detected:")
        ):
            continue
        issues.append(w)
    if re.search(
        r"\(cid:|\ufffd",
        question["question_text"]
        + "\n"
        + "\n".join(o["text"] for o in question["options"]),
    ):
        issues.append("font_encoding_artifacts:unverified_glyphs_preserved")
    for option in question["options"]:
        if not option["text"].strip() and not option["images"]:
            issues.append("option_content_unresolved:" + option["label"])
    for code, asset in visual_issues(
        question, path, {p["page_number"]: p for p in data["pages"]}
    ):
        if code.startswith("visual_option_anchor_not_left_of_image:"):
            label = code.rsplit(":", 1)[1]
            candidates = [
                a for a in question["visual_assets"] if a.get("option_label") == label
            ]
            if len(candidates) == 1 and candidates[0].get("association_method") in {
                "bmat_complete_above_label_cells",
                "bmat_complete_anchor_envelopes",
                "bmat_spatial_math_option_cells",
            }:
                continue
        issues.append(code + (" [" + asset + "]" if asset else ""))
    if not question["raw_components"]["main_question"] and not no_choices_expected:
        issues.append("raw_prompt_boundary_unresolved")
    return list(dict.fromkeys(issues))


def status(data, q, path):
    issues = findings(data, q, path)
    return "skipped" if q["bmat_filter"][
        "skip_from_pipeline"
    ] else "parser_review" if issues or data["warnings"] else "retained", issues
