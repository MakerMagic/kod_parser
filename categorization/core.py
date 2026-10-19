"""Persistence/handoff and independent categorization; never parse or match."""

import json
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from processors.matching.storage import load_matched

from .model import Model, attribute, question_modalities, view

ROOT = Path(__file__).resolve().parent
MARKER = "tsa_categorization_v1"


def digest(value):
    return sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def file_ref(path):
    path = Path(path).resolve(strict=True)
    return {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def matched_files(references):
    paths = []
    for value in references:
        p = Path(value).resolve(strict=True)
        paths.extend(sorted(p.glob("*.matched.json")) if p.is_dir() else [p])
    if not paths:
        raise ValueError("No canonical matching inputs")
    return sorted(set(paths))


def identity(record):
    q = record.get("question") or {}
    return {
        **record["identity"],
        "question_id": q.get("question_id"),
        "source_question_key": q.get("source_question_key"),
    }


def record_key(record):
    return digest(identity(record))


def safe_output(path, protected):
    p = Path(path).resolve()
    if any(p.is_relative_to(Path(ref["path"]).resolve().parent) for ref in protected):
        raise ValueError(
            "Categorization output must be outside upstream input directories"
        )
    return p


def write_json(path, value, *, overwrite=False, protected=()):
    path = safe_output(path, protected)
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Output exists: {path}")
        old = read(path)
        if old.get("owner") != MARKER or old.get("stage") != value.get("stage"):
            raise ValueError("Refusing to overwrite an unrelated file")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def dependencies(record):
    """Hash references/assets without extracting any source document content."""
    found = []

    def walk(value):
        if isinstance(value, dict):
            if (
                isinstance(value.get("path"), str)
                and Path(value["path"]).is_absolute()
                and value.get("sha256")
            ):
                found.append({"path": value["path"], "sha256": value["sha256"]})
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(record)
    q = record.get("question") or {}
    if q:
        raw_parent = Path(q["raw_reference"]["path"]).parent
        clean_parent = Path(record["question_reference"]["path"]).parent
        assets = [
            *q.get("visual_assets", []),
            *q.get("visual_previews", []),
            *[a for o in q.get("options") or [] for a in o.get("images") or []],
        ]
        for asset in assets:
            base = (
                clean_parent
                if asset.get("path_base") == "clean_json_parent"
                else raw_parent
            )
            if asset.get("path") and asset.get("sha256"):
                found.append(
                    {
                        "path": str((base / asset["path"]).resolve()),
                        "sha256": asset["sha256"],
                    }
                )
            derived = asset.get("clean_asset") or {}
            if derived.get("path") and derived.get("sha256"):
                found.append(
                    {
                        "path": str((clean_parent / derived["path"]).resolve()),
                        "sha256": derived["sha256"],
                    }
                )
    answers = [(record.get("answer"), record.get("answer_reference"))]
    answers.extend(
        (c["record"], c["reference"])
        for c in record.get("superseded_answer_candidates", [])
    )
    answers.extend(
        (c["record"], c["reference"]) for c in record.get("answer_candidates", [])
    )
    for a, ref in answers:
        if not a or not ref:
            continue
        for asset in [
            *a.get("visual_previews", []),
            *a.get("explanation", {}).get("visual_assets", []),
        ]:
            if asset.get("path") and asset.get("sha256"):
                found.append(
                    {
                        "path": str(
                            (Path(ref["path"]).parent / asset["path"]).resolve()
                        ),
                        "sha256": asset["sha256"],
                    }
                )
    return found


def verify_refs(refs):
    checked = {}
    for ref in refs:
        path = Path(ref["path"]).resolve(strict=True)
        if path not in checked:
            checked[path] = sha256(path.read_bytes()).hexdigest()
        if checked[path] != ref["sha256"]:
            raise ValueError(f"Frozen input/reference changed: {path}")


def freeze(references):
    files = matched_files(references)
    sources, deps, summaries, seen = [], {}, [], set()
    counts = Counter()
    for path in files:
        data = load_matched(path)
        sources.append(file_ref(path))
        for ref in data.get("inputs", []):
            deps[(ref["path"], ref["sha256"])] = {
                "path": ref["path"],
                "sha256": ref["sha256"],
            }
        for index, record in enumerate(data["records"]):
            key = record_key(record)
            if key in seen:
                raise ValueError(
                    "Duplicate stable question identity in matching handoff"
                )
            seen.add(key)
            final = record.get("final_explanation") or {}
            counts[record["status"]] += 1
            counts[
                "explanation_available"
                if final.get("status") == "available"
                else "explanation_unavailable_or_uncertain"
            ] += 1
            if final.get("status") == "available":
                counts[
                    "ai_explanation"
                    if final.get("explanation_by_ai")
                    else "source_manual_explanation"
                ] += 1
            summaries.append(
                {
                    "record_key": key,
                    "identity": identity(record),
                    "matched_reference": {
                        **sources[-1],
                        "json_pointer": f"/records/{index}",
                        "record_sha256": digest(record),
                    },
                    "matching_status": record["status"],
                    "final_explanation_status": final.get("status"),
                    "matching_issue_codes": [
                        i["code"] for i in record.get("issues", [])
                    ],
                }
            )
            for ref in dependencies(record):
                deps[(ref["path"], ref["sha256"])] = ref
    refs = sorted(deps.values(), key=lambda r: (r["path"], r["sha256"]))
    verify_refs([*sources, *refs])
    return {
        "owner": MARKER,
        "stage": "matching_handoff",
        "schema_version": "1",
        "inputs": sources,
        "dependencies": refs,
        "records": summaries,
        "summary": {"records": len(summaries), **dict(sorted(counts.items()))},
        "preservation": "Canonical matched files remain authoritative, unchanged. Hash mismatch blocks downstream use; refresh explicitly after intentional upstream regeneration.",
        "limitations": [
            "A matched status is not proof that every upstream visual/text issue is resolved.",
            "graphics_present:option_association_not_resolved is informational in RAW QA; the broad matching upstream_review_required boolean alone is not an error count.",
            "Source/manual replacements, original superseded candidates, AI-import/visual reviews, pins, and unresolved matching conflicts remain in the referenced records.",
            "No matching inputs/explanations are regenerated by categorization.",
        ],
    }


def load_handoff(path):
    data = read(path)
    if data.get("owner") != MARKER or data.get("stage") != "matching_handoff":
        raise ValueError("Unsupported matching handoff")
    verify_refs([*data["inputs"], *data["dependencies"]])
    return data


def source_records(handoff):
    loaded = {r["path"]: load_matched(r["path"]) for r in handoff["inputs"]}
    result = []
    for item in handoff["records"]:
        ref = item["matched_reference"]
        record = loaded[ref["path"]]["records"][int(ref["json_pointer"].split("/")[-1])]
        if (
            digest(record) != ref["record_sha256"]
            or record_key(record) != item["record_key"]
        ):
            raise ValueError("Handoff pointer/content conflict")
        result.append((item, record))
    return result


def train(handoff, annotations):
    records = {
        (r["identity"]["year"], r["identity"]["question_number"]): (item, r)
        for item, r in source_records(handoff)
    }
    examples = []
    patterns = read(ROOT / "patterns.json")
    known = {p["id"] for p in patterns["patterns"]}
    for year, number, labels, rationale in annotations["examples"]:
        if not set(labels) <= known:
            raise ValueError("Unknown training pattern")
        item, r = records[(year, number)]
        examples.append(
            {
                "example_id": f"{year}_q{number}",
                "reference": item["matched_reference"],
                "patterns": labels,
                "rationale": rationale,
                "view": view(r),
            }
        )
    model = {
        "owner": MARKER,
        "stage": "categorization_model",
        "schema_version": "1",
        "patterns": patterns,
        "examples": examples,
        "reviewer": annotations["reviewer"],
        "training_method": "semantic_concept_profiles_and_learned_tfidf_exemplar_support",
        "limitations": "Assistant-reviewed seed labels, not an official gold set. Support scores are not calibrated correctness probabilities.",
    }
    model["model_sha256"] = digest(model)
    return model


def summarize(records):
    statuses = Counter(r["categorization"]["status"] for r in records)
    accepted = [
        r
        for r in records
        if r["categorization"]["status"] in {"classified", "multi_label"}
    ]
    return {
        "processed": len(records),
        "statuses": dict(sorted(statuses.items())),
        "categories_successful_only": dict(
            Counter(r["categorization"]["category"] for r in accepted)
        ),
        "subcategories_successful_only": dict(
            Counter(s for r in accepted for s in r["categorization"]["subcategories"])
        ),
        "selection_and_procedures": sum(
            set(r["categorization"]["subcategories"])
            == {"Relevant Selection", "Finding Procedures"}
            for r in accepted
        ),
        "unresolved": len(records) - len(accepted),
    }


def categorize(handoff, handoff_path, trained):
    if trained.get("owner") != MARKER or trained.get("stage") != "categorization_model":
        raise ValueError("Unsupported categorization model")
    if digest(
        {
            k: v
            for k, v in trained.items()
            if k not in {"model_sha256", "annotation_reference"}
        }
    ) != trained.get("model_sha256"):
        raise ValueError(
            "Model content differs from its version digest; retrain explicitly"
        )
    verify_refs([e["reference"] for e in trained["examples"]])
    model = Model(
        trained["examples"],
        trained["patterns"]["patterns"],
        trained["patterns"].get("categories"),
        trained["patterns"].get("semantic_families", []),
    )
    rows = []
    for item, r in source_records(handoff):
        q = r.get("question") or {}
        rows.append(
            {
                "record_key": item["record_key"],
                "identity": item["identity"],
                "matched_reference": item["matched_reference"],
                "question_view": {
                    k: deepcopy(q.get(k))
                    for k in (
                        "question_id",
                        "question_text",
                        "main_body",
                        "main_question",
                        "options",
                        "visual_assets",
                        "images",
                        "visual_previews",
                        "raw_reference",
                    )
                },
                "correct_answer": r.get("correct_answer"),
                "final_explanation": deepcopy(r.get("final_explanation")),
                "provenance": {
                    k: deepcopy(r.get(k))
                    for k in (
                        "question_reference",
                        "answer_reference",
                        "question_document",
                        "ai_explanation",
                    )
                },
                "upstream": {
                    "matching_status": r["status"],
                    "matching_issues": deepcopy(r.get("issues", [])),
                    "cleaning_issues": deepcopy(q.get("cleaning_issues", [])),
                    "raw_warnings": deepcopy(q.get("raw_warnings", [])),
                },
                "categorization": attribute(r, model),
            }
        )
    return {
        "owner": MARKER,
        "stage": "categorized",
        "schema_version": "1",
        "handoff_reference": file_ref(handoff_path),
        "inputs": handoff["inputs"],
        "logic": {
            "version": "4",
            "model_sha256": trained["model_sha256"],
            "pattern_sha256": digest(trained["patterns"]),
            "taxonomy": [
                {"category": p["category"], "subcategory": p["subcategory"]}
                for p in trained["patterns"]["patterns"]
            ],
            "category_metadata": trained["patterns"].get("categories", []),
            "code_sha256": {
                p.name: file_ref(p)["sha256"] for p in sorted(ROOT.glob("*.py"))
            },
            "confidence_meaning": "Evidence support, not a probability or manual approval.",
        },
        "records": rows,
        "summary": summarize(rows),
    }


def validate_output(data):
    if data.get("owner") != MARKER or data.get("stage") != "categorized":
        raise ValueError("Unsupported categorization output")
    patterns = (
        data.get("logic", {}).get("taxonomy")
        or read(ROOT / "patterns.json")["patterns"]
    )
    allowed = defaultdict(set)
    for p in patterns:
        allowed[p["category"]].add(p["subcategory"])
    seen = set()
    for r in data["records"]:
        if r["record_key"] in seen:
            raise ValueError("Duplicate categorized identity")
        seen.add(r["record_key"])
        c = r["categorization"]
        if c["status"] not in {
            "classified",
            "multi_label",
            "needs_review",
            "ambiguous",
            "unclassified",
        }:
            raise ValueError("Unknown categorization status")
        if len(c["subcategories"]) != len(set(c["subcategories"])):
            raise ValueError("Duplicate subcategory labels")
        if c["status"] in {"classified", "multi_label"}:
            if (
                not c["subcategories"]
                or not set(c["subcategories"]) <= allowed[c["category"]]
                or c["issues"]
            ):
                raise ValueError("Invalid accepted category/subcategory/issue state")
            if (len(c["subcategories"]) > 1) != (c["status"] == "multi_label"):
                raise ValueError("Multi-label status/array mismatch")
            metadata = {
                m["name"]: m for m in data.get("logic", {}).get("category_metadata", [])
            }
            if metadata and not set(
                question_modalities(r.get("question_view") or {})
            ) <= set(metadata[c["category"]]["modalities"]):
                raise ValueError(
                    "Accepted category is incompatible with question modality"
                )
            if (
                metadata
                and not metadata[c["category"]]["multi_label"]
                and len(c["subcategories"]) != 1
            ):
                raise ValueError(
                    "Competing tasks in a single-label category must remain ambiguous"
                )
        elif not c["issues"]:
            raise ValueError("Unresolved classification needs an explicit reason")
    if data["summary"] != summarize(data["records"]):
        raise ValueError("Categorization counts inconsistent")


def compare_previous(data, baseline, reference):
    """QA comparison only; never supply prior labels as classification evidence."""
    previous = {r["record_key"]: r for r in baseline["records"]}
    changes = []
    totals = Counter()
    accepted = {"classified", "multi_label"}
    for row in data["records"]:
        old = previous.get(row["record_key"])
        if not old:
            continue
        before, after = old["categorization"], row["categorization"]
        signature = lambda c: (c["category"], sorted(c["subcategories"]), c["status"])
        prompt = old.get(
            "main_question", (old.get("question_view") or {}).get("main_question")
        )
        if (
            signature(before) == signature(after)
            and prompt == row["question_view"]["main_question"]
        ):
            continue
        row["previous_categorization"] = {
            k: deepcopy(before[k]) for k in ("category", "subcategories", "status")
        }
        row["previous_main_question"] = prompt
        changes.append(
            {
                "identity": row["identity"],
                "record_key": row["record_key"],
                "previous": row["previous_categorization"],
                "current": {
                    k: deepcopy(after[k])
                    for k in ("category", "subcategories", "status")
                },
                "main_question_changed": prompt
                != row["question_view"]["main_question"],
            }
        )
        if before["status"] not in accepted and after["status"] in accepted:
            totals["previously_unresolved_resolved"] += 1
            totals[before["status"] + "_resolved"] += 1
        if (
            before["status"] in accepted
            and after["status"] in accepted
            and signature(before)[:2] != signature(after)[:2]
        ):
            totals["previously_classified_corrected"] += 1
        if before["status"] in accepted and after["status"] not in accepted:
            totals["previously_classified_now_review"] += 1
    data["comparison"] = {
        "baseline_reference": reference,
        "counts": dict(totals),
        "changes": changes,
    }
