"""Content-bound assistant review annotations, separate from learned attribution."""

import argparse
import csv
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

from .core import MARKER, digest, file_ref, read, summarize, verify_refs
from .model import question_modalities


def in_scope(row):
    c = row["categorization"]
    return c["status"] == "needs_review" and (
        c["category"] == "Problem-Solving"
        or (
            c["category"] is None
            and c["candidates"]
            and c["candidates"][0]["category"] == "Problem-Solving"
        )
    )


def prepare(baseline, baseline_path, rulebook_path):
    """Capture the complete review population before making any decisions."""
    rows = []
    for row in baseline["records"]:
        if row["categorization"]["status"] != "needs_review":
            continue
        rows.append(
            {
                "record_key": row["record_key"],
                "identity": row["identity"],
                "matched_reference": row["matched_reference"],
                "previous_categorization": deepcopy(row["categorization"]),
                "in_scope": in_scope(row),
                "modalities": question_modalities(row["question_view"]),
                "final_explanation_status": (row.get("final_explanation") or {}).get(
                    "status"
                ),
            }
        )
    keys = [r["record_key"] for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate stable review identity")
    return {
        "owner": MARKER,
        "stage": "categorization_review",
        "baseline_reference": file_ref(baseline_path),
        "rulebook_reference": file_ref(rulebook_path),
        "reviewer": "assistant_manual_rulebook_review",
        "records": rows,
        "decisions": [],
    }


LABELS = {
    "RS": ("ps_select", "Relevant Selection"),
    "FP": ("ps_procedure", "Finding Procedures"),
    "IS": ("ps_similarity", "Identifying Similarity"),
}
REVIEW_REASONS = {
    "below_semantic_threshold",
    "taxonomy_boundary",
    "incomplete_extraction",
    "ambiguous_visual_association",
    "explanation_question_conflict",
    "insufficient_semantic_evidence",
}
MODEL_UNCERTAINTY = {"problem_solving_skill_unresolved", "procedure_support_incomplete"}


def visual_references(row):
    """Bind all effective body/option images, not decorative or superseded assets."""
    q = row["question_view"]
    raw_base = Path(q["raw_reference"]["path"]).parent
    clean_base = Path(row["provenance"]["question_reference"]["path"]).parent
    by_id = {a["image_id"]: a for a in q.get("visual_assets") or []}
    assets = [
        ("body", by_id.get(b.get("asset_id")))
        for b in q.get("main_body") or []
        if b.get("type") == "visual"
    ]
    assets += [
        ("option_" + o["label"], a)
        for o in q.get("options") or []
        for a in o.get("images") or []
    ]
    assets += [("source_preview", a) for a in q.get("visual_previews") or []]
    result, missing = [], []
    for role, asset in assets:
        if not asset or not asset.get("path"):
            missing.append(role)
            continue
        base = clean_base if asset.get("path_base") == "clean_json_parent" else raw_base
        effective = asset.get("clean_asset") or asset
        if asset.get("clean_asset"):
            base = clean_base
        path = (base / effective["path"]).resolve()
        if not path.is_file():
            missing.append(str(path))
            continue
        ref = file_ref(path)
        if effective.get("sha256") and ref["sha256"] != effective["sha256"]:
            raise ValueError("Review asset changed: " + str(path))
        result.append({**ref, "role": role, "image_id": asset.get("image_id")})
    return result, missing


def bind_decisions(manifest, baseline, decisions_path):
    """Bind authored assessments to stable identities and exact input content."""
    verify_refs([manifest["baseline_reference"], manifest["rulebook_reference"]])
    population = {r["record_key"]: r for r in manifest["records"] if r["in_scope"]}
    rows = {r["record_key"]: r for r in baseline["records"]}
    by_display = {}
    for key in population:
        identity = rows[key]["identity"]
        display = (identity["year"], identity["question_number"])
        if display in by_display:
            raise ValueError("Ambiguous display identity; use stable record identities")
        by_display[display] = key
    decisions, seen = [], set()
    with Path(decisions_path).open(encoding="utf-8", newline="") as handle:
        for item in csv.DictReader(handle, delimiter="\t"):
            display = (int(item["year"]), int(item["question"]))
            if display not in by_display:
                raise ValueError("Decision outside frozen review population")
            key = by_display[display]
            if key in seen:
                raise ValueError("Duplicate review decision")
            seen.add(key)
            result, evidence = item["result"], item["evidence"].strip()
            unresolved = result.startswith("R:")
            reason = result[2:] if unresolved else None
            selected = [] if unresolved else result.split("+")
            if (unresolved and reason not in REVIEW_REASONS) or (
                not unresolved and (not selected or not set(selected) <= LABELS.keys())
            ):
                raise ValueError("Unknown review decision/category")
            if len(set(selected)) != len(selected) or len(evidence) < 60:
                raise ValueError("Missing substantive assessment or duplicate labels")
            row = rows[key]
            refs, missing = visual_references(row)
            if not unresolved and missing:
                raise ValueError("Required review asset is missing")
            if not unresolved and any(
                i["code"] not in MODEL_UNCERTAINTY
                for i in row["categorization"]["issues"]
            ):
                raise ValueError("Manual categorization cannot clear upstream blockers")
            decisions.append(
                {
                    "record_key": key,
                    "matched_record_sha256": row["matched_reference"]["record_sha256"],
                    "previous_categorization_sha256": digest(row["categorization"]),
                    "evaluated_subcategories": [v[1] for v in LABELS.values()],
                    "material_subcategories": [LABELS[s][1] for s in selected],
                    "patterns": [LABELS[s][0] for s in selected],
                    "status": "needs_review"
                    if unresolved
                    else "multi_label"
                    if len(selected) > 1
                    else "classified",
                    "confidence": "unresolved" if unresolved else "supported",
                    "evidence": evidence,
                    "remaining_review_reason": reason,
                    "visual_references": refs,
                    "missing_assets": missing,
                    "explanation_evidence": {
                        "status": (row.get("final_explanation") or {}).get("status"),
                        "sha256": digest(row.get("final_explanation")),
                        "use": "Supporting source excerpts and full blocks where a conflict was identified; not an independent certification of explanation correctness.",
                    },
                }
            )
    if seen != population.keys():
        raise ValueError("Every in-scope record needs an explicit decision")
    bound = deepcopy(manifest)
    bound["decisions"] = decisions
    bound["decision_source_reference"] = file_ref(decisions_path)
    bound["baseline_counts"] = {
        "all_needs_review": len(manifest["records"]),
        "problem_solving_review": len(population),
        "out_of_scope_review": len(manifest["records"]) - len(population),
    }
    return bound


def apply_review(baseline, annotations, annotation_path):
    """Apply only the complete frozen review set; do not rerun the classifier."""
    if (
        annotations.get("owner") != MARKER
        or annotations.get("stage") != "categorization_review"
    ):
        raise ValueError("Unsupported categorization review")
    verify_refs(
        [
            annotations["baseline_reference"],
            annotations["rulebook_reference"],
            annotations["decision_source_reference"],
        ]
    )
    if digest(baseline) != digest(read(annotations["baseline_reference"]["path"])):
        raise ValueError("Review baseline does not match")
    expected = {r["record_key"] for r in baseline["records"] if in_scope(r)}
    decisions = {d["record_key"]: d for d in annotations["decisions"]}
    if len(decisions) != len(annotations["decisions"]) or decisions.keys() != expected:
        raise ValueError("Incomplete, duplicate or out-of-scope review decisions")
    result = deepcopy(baseline)
    accepted = Counter()
    reasons = Counter()
    for row in result["records"]:
        decision = decisions.get(row["record_key"])
        if not decision:
            continue
        old = row["categorization"]
        if (
            digest(old) != decision["previous_categorization_sha256"]
            or row["matched_reference"]["record_sha256"]
            != decision["matched_record_sha256"]
        ):
            raise ValueError("Review input changed; reassessment required")
        if decision["explanation_evidence"]["sha256"] != digest(
            row.get("final_explanation")
        ):
            raise ValueError("Reviewed explanation changed")
        verify_refs(decision["visual_references"])
        actual_refs, missing = visual_references(row)
        if (
            actual_refs != decision["visual_references"]
            or missing != decision["missing_assets"]
        ):
            raise ValueError("Reviewed visual context changed")
        if set(decision["evaluated_subcategories"]) != {v[1] for v in LABELS.values()}:
            raise ValueError("All three subcategories must be assessed")
        new = deepcopy(old)
        status = decision["status"]
        if status not in {"classified", "multi_label", "needs_review"}:
            raise ValueError("Invalid review status")
        new.update(
            status=status,
            rationale=decision["evidence"],
            confidence={
                "level": decision["confidence"],
                "calibrated_probability": False,
                "human_approved": False,
                "method": "assistant_rulebook_review",
            },
        )
        if status == "needs_review":
            if (
                decision["material_subcategories"]
                or decision["patterns"]
                or decision["remaining_review_reason"] not in REVIEW_REASONS
            ):
                raise ValueError(
                    "Unresolved review needs an explicit reason and no forced label"
                )
            reasons[decision["remaining_review_reason"]] += 1
            # Replace the generic classifier uncertainty with the concrete finding;
            # never remove concrete upstream blockers.
            new["issues"] = [
                i for i in old["issues"] if i["code"] not in MODEL_UNCERTAINTY
            ]
            new["issues"].append(
                {
                    "code": "rulebook_" + decision["remaining_review_reason"],
                    "reason": decision["evidence"],
                    "manual_review_required": True,
                }
            )
        else:
            expected_labels = [
                LABELS[p][1] for p in LABELS if LABELS[p][0] in decision["patterns"]
            ]
            if (
                set(expected_labels) != set(decision["material_subcategories"])
                or not expected_labels
                or len(expected_labels) != len(decision["patterns"])
            ):
                raise ValueError("Review label/pattern mismatch")
            if (
                any(i["code"] not in MODEL_UNCERTAINTY for i in old["issues"])
                or missing
                or not row.get("correct_answer")
            ):
                raise ValueError(
                    "Review cannot bypass incomplete input or missing answer"
                )
            new.update(
                category="Problem-Solving",
                subcategories=decision["material_subcategories"],
                patterns=decision["patterns"],
                issues=[],
            )
            accepted.update(new["subcategories"])
        new["evidence"] = [
            *old["evidence"],
            {
                "field": "rulebook_review",
                "evaluated_subcategories": decision["evaluated_subcategories"],
                "material_subcategories": decision["material_subcategories"],
                "summary": decision["evidence"],
            },
        ]
        row["categorization"] = new
        row["rulebook_review"] = deepcopy(decision)
        row["rulebook_review"]["previous_categorization"] = deepcopy(old)
    result["review_reference"] = file_ref(annotation_path)
    result["logic"]["review_method"] = (
        "content_bound_assistant_annotations_no_classifier_retraining"
    )
    result["review_summary"] = {
        **annotations["baseline_counts"],
        "reviewed": len(decisions),
        "resolved": sum(d["status"] != "needs_review" for d in decisions.values()),
        "remaining_review": sum(reasons.values()),
        "resolved_subcategory_counts_overlapping": dict(accepted),
        "multi_label": sum(d["status"] == "multi_label" for d in decisions.values()),
        "remaining_reasons": dict(reasons),
    }
    result["summary"] = summarize(result["records"])
    return result


def compact(row):
    q = row["question_view"]
    return {
        "id": [row["identity"]["year"], row["identity"]["question_number"]],
        "prompt": q.get("main_question"),
        "body": [b for b in q.get("main_body") or [] if b.get("type") != "text"]
        + [
            {
                "text": "\n".join(
                    b.get("text", "")
                    for b in q.get("main_body") or []
                    if b.get("type") == "text"
                )
            }
        ],
        "options": [
            {
                "label": o["label"],
                "text": o.get("text"),
                "images": [a.get("image_id") for a in o.get("images") or []],
            }
            for o in q.get("options") or []
        ],
        "answer": row.get("correct_answer"),
        "explanation": [
            {k: b[k] for k in ("type", "text", "items") if k in b}
            for b in (row.get("final_explanation") or {}).get("blocks", [])
        ],
        "issues": row["upstream"],
    }


def assessment_signature(row):
    """Task evidence, excluding file-hash churn caused by other records in a PDF.

    Text, order, option/asset ownership, rendered asset hashes, correct answer,
    explanation and concrete upstream issues are retained. File references are
    rebound separately and verified by the current matching handoff.
    """
    source = row["question_view"]

    def asset(a):
        value = {
            k: a.get(k)
            for k in (
                "image_id",
                "sha256",
                "page",
                "bbox",
                "graphic_bbox",
                "belongs_to",
                "option_label",
                "visual_kind",
                "visual_text",
                "warnings",
            )
        }
        derived = a.get("clean_asset") or {}
        value["derived"] = {
            k: derived.get(k)
            for k in ("sha256", "pixel_crop_box", "removed_label_rect_px")
        }
        return value

    q = {
        "question_text": source.get("question_text"),
        "main_question": source.get("main_question"),
        "main_body": [
            {k: b.get(k) for k in ("type", "text", "asset_id", "order")}
            for b in source.get("main_body") or []
        ],
        "options": [
            {
                "label": o["label"],
                "text": o.get("text"),
                "images": [asset(a) for a in o.get("images") or []],
            }
            for o in source.get("options") or []
        ],
        "visual_assets": [asset(a) for a in source.get("visual_assets") or []],
        "source_previews": [asset(a) for a in source.get("visual_previews") or []],
    }
    return digest(
        {
            "question": q,
            "answer": row.get("correct_answer"),
            "explanation": row.get("final_explanation"),
            "upstream": {
                k: row["upstream"].get(k)
                for k in ("matching_status", "matching_issues", "cleaning_issues")
            },
        }
    )


def refresh_review(data, previous, previous_path):
    """Carry exact-evidence assessments, but re-evaluate every new pattern match.

    This is not an ID exception table. An unchanged task outside the refined
    semantic families retains its previous assessment, avoiding unrelated model
    drift. Changed evidence cannot inherit an obsolete manual approval.
    """
    from .model import REFINED_OPERATIONS, features, view

    old_rows = {r["record_key"]: r for r in previous["records"]}
    if set(old_rows) != {r["record_key"] for r in data["records"]}:
        raise ValueError("Review refresh requires the same stable question population")
    decisions, carried, reconsidered = [], 0, 0
    for row in data["records"]:
        old = old_rows[row["record_key"]]
        same = assessment_signature(row) == assessment_signature(old)
        profile = features(
            view(
                {
                    "question": row["question_view"],
                    "final_explanation": row["final_explanation"],
                }
            )
        )
        refined = [k for k in REFINED_OPERATIONS if profile[k]]
        blocking = any(
            i["code"].startswith("upstream_")
            or i["code"] == "insufficient_question_data"
            for i in row["categorization"]["issues"]
        )
        reviewed = old.get("rulebook_review")
        conflict = (
            reviewed
            and reviewed.get("remaining_review_reason")
            == "explanation_question_conflict"
        )
        retain = same and not blocking and (not refined or conflict)
        if retain:
            row["categorization"] = deepcopy(old["categorization"])
            carried += 1
        else:
            reconsidered += 1
        if not reviewed:
            continue
        c = row["categorization"]
        refs, missing = visual_references(row)
        accepted = c["status"] in {"classified", "multi_label"}
        if accepted and (missing or blocking):
            raise ValueError(
                "Review refresh cannot approve missing or blocked evidence"
            )
        reason = (
            None
            if accepted
            else reviewed.get("remaining_review_reason")
            if retain
            else (
                "incomplete_extraction"
                if blocking
                else "insufficient_semantic_evidence"
            )
        )
        decision = {
            **deepcopy(reviewed),
            "matched_record_sha256": row["matched_reference"]["record_sha256"],
            "previous_categorization_sha256": digest(old["categorization"]),
            "previous_categorization": deepcopy(old["categorization"]),
            "status": c["status"],
            "confidence": c["confidence"]["level"],
            "material_subcategories": c["subcategories"] if accepted else [],
            "patterns": c["patterns"] if accepted else [],
            "evidence": c["rationale"],
            "remaining_review_reason": reason,
            "visual_references": refs,
            "missing_assets": missing,
            "explanation_evidence": {
                **reviewed["explanation_evidence"],
                "sha256": digest(row["final_explanation"]),
            },
            "refresh": {
                "assessment_reused": bool(retain),
                "task_evidence_unchanged": same,
                "previous_evidence_sha256": assessment_signature(old),
                "current_evidence_sha256": assessment_signature(row),
                "refined_operations": refined,
            },
        }
        row["rulebook_review"] = decision
        decisions.append(decision)
    manifest = {
        "owner": MARKER,
        "stage": "categorization_review",
        "baseline_reference": file_ref(previous_path),
        "rulebook_reference": file_ref(
            Path(__file__).with_name("ps_attribution_rulebook.txt")
        ),
        "decision_source_reference": previous["review_reference"],
        "reviewer": "generalized_patterns_with_content_checked_prior_assessments",
        "decisions": decisions,
    }
    reasons = Counter(
        d["remaining_review_reason"] for d in decisions if d["remaining_review_reason"]
    )
    labels = Counter(
        label
        for d in decisions
        if not d["remaining_review_reason"]
        for label in d["material_subcategories"]
    )
    data["review_summary"] = {
        **{
            k: previous["review_summary"][k]
            for k in (
                "all_needs_review",
                "problem_solving_review",
                "out_of_scope_review",
            )
        },
        "reviewed": len(decisions),
        "resolved": sum(not d["remaining_review_reason"] for d in decisions),
        "remaining_review": sum(reasons.values()),
        "resolved_subcategory_counts_overlapping": dict(labels),
        "multi_label": sum(d["status"] == "multi_label" for d in decisions),
        "remaining_reasons": dict(reasons),
    }
    data["refinement_summary"] = {
        "evaluated": len(data["records"]),
        "unchanged_evidence_carried": carried,
        "reconsidered": reconsidered,
    }
    data["summary"] = summarize(data["records"])
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--explanations", action="store_true")
    p.add_argument("--visual-sheet", type=Path)
    p.add_argument("--effective-assets", action="store_true")
    p.add_argument("--questions", type=int, nargs="+")
    p.add_argument("--support", action="store_true")
    args = p.parse_args()
    selected = [
        r
        for r in read(args.baseline)["records"]
        if in_scope(r)
        and r["identity"]["year"] == args.year
        and (not args.questions or r["identity"]["question_number"] in args.questions)
    ]
    if args.visual_sheet:
        # Read-only review aid; never used as a question asset or model input.
        from PIL import Image, ImageDraw

        panels = []
        for row in selected:
            q = row["question_view"]
            if "visual" not in question_modalities(q):
                continue
            previews = (
                [a for a in visual_references(row)[0] if a["role"] != "source_preview"]
                if args.effective_assets
                else q.get("visual_previews") or []
            )
            for a in previews:
                asset_path = (
                    Path(a["path"])
                    if args.effective_assets
                    else Path(q["raw_reference"]["path"]).parent / a["path"]
                )
                image = Image.open(asset_path).convert("RGB")
                image.thumbnail((980, 1000))
                panel = Image.new("RGB", (1000, image.height + 36), "white")
                ImageDraw.Draw(panel).text(
                    (10, 8),
                    str(row["identity"]["year"])
                    + " Q"
                    + str(row["identity"]["question_number"])
                    + " "
                    + a.get("role", "source preview"),
                    fill="black",
                )
                panel.paste(image, (10, 32))
                panels.append(panel)
        for offset in range(0, len(panels), 2):
            group = panels[offset : offset + 2]
            sheet = Image.new("RGB", (1000, sum(im.height for im in group)), "#cccccc")
            y = 0
            for panel in group:
                sheet.paste(panel, (0, y))
                y += panel.height
            target = args.visual_sheet.with_name(
                args.visual_sheet.stem + f"_{offset // 2}.png"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(target)
            print(target)
        return
    for row in selected:
        if in_scope(row) and row["identity"]["year"] == args.year:
            c = compact(row)
            if args.support:
                blocks = (row.get("final_explanation") or {}).get("blocks", [])
                texts = [b.get("text", "") for b in blocks if b.get("text")]
                print(
                    json.dumps(
                        {
                            "id": c["id"],
                            "support_excerpt": [
                                t[:240]
                                for t in (
                                    [texts[0], texts[-1]] if len(texts) > 1 else texts
                                )
                            ],
                            "status": (row.get("final_explanation") or {}).get(
                                "status"
                            ),
                        },
                        ensure_ascii=False,
                    )
                )
                continue
            if not args.explanations:
                c.pop("explanation")
            # Body asset metadata stays available in the stored full record.
            c["body"] = [
                {k: b[k] for k in ("type", "text", "image_id", "path") if k in b}
                for b in c["body"]
            ]
            if not any(
                c["issues"].get(k) for k in ("matching_issues", "cleaning_issues")
            ):
                c.pop("issues")
            print(json.dumps(c, ensure_ascii=False))


if __name__ == "__main__":
    main()
