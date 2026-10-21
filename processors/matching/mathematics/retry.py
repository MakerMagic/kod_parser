"""Retry only unmatched mathematics records using the existing stored-key matcher."""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from .core import load, match_document


def valid_match(q):
    labels = [o["label"] for o in q["options"]]
    return (
        q.get("matching", {}).get("status") == "matched"
        and q.get("correct_answer") in labels
        and len(set(labels)) == len(labels)
        and all(o.get("content") for o in q["options"])
        and not q["matching"].get("issues")
    )


def retry_unmatched(data):
    if (
        data.get("domain") != "mathematics"
        or data.get("stage") != "mathematics_matched"
    ):
        raise ValueError("Retry requires existing mathematics matched output")
    result = deepcopy(data)
    processed, unresolved, newly_matched = [], [], 0
    sources = {}
    for index, q in enumerate(data["questions"]):
        if valid_match(q):
            continue
        reference = q["raw_reference"]
        path = Path(reference["path"])
        if path not in sources:
            sources[path] = (sha256(path.read_bytes()).hexdigest(), load(path))
        digest, raw = sources[path]
        if digest != reference["sha256"]:
            raise ValueError("RAW reference changed; refusing stale matching input")
        if raw["source_document"]["id"] != q["source_document_id"]:
            raise ValueError("Stored RAW source identity mismatch")
        originals = [
            r
            for r in raw["questions"]
            if r["id"] == q["id"] and r["question_number"] == q["question_number"]
        ]
        if len(originals) != 1:
            raise ValueError("Stored RAW question identity is not unique")
        original = originals[0]
        if any(q.get(k) != v for k, v in original.items() if k != "issues"):
            raise ValueError(
                "Stored question differs from RAW; refusing to replace content"
            )
        rows, _ = match_document(
            {**raw, "questions": [original]},
            {k: reference[k] for k in ("path", "sha256")},
        )
        updated = deepcopy(q)
        updated["correct_answer"] = rows[0]["correct_answer"]
        updated["matching"] = rows[0]["matching"]
        updated["issues"] = [
            deepcopy(i) for i in q["issues"] if i["code"] != "answer_matching"
        ] + deepcopy(updated["matching"]["issues"])
        result["questions"][index] = updated
        processed.append(q["id"])
        if valid_match(updated):
            newly_matched += 1
        else:
            unresolved.append(
                {
                    "id": q["id"],
                    "source_pdf": raw["source_document"]["filename"],
                    "question_number": q["question_number"],
                    "key_answers": [
                        a["correct_answer"]
                        for a in raw["answer_key"]["entries"]
                        if a["question_number"] == q["question_number"]
                    ],
                    "issues": deepcopy(updated["matching"]["issues"]),
                }
            )
    result["summary"].update(
        {
            "matched": sum(
                q["matching"]["status"] == "matched" for q in result["questions"]
            ),
            "issue_questions": sum(bool(q["issues"]) for q in result["questions"]),
            "issues_by_code": dict(
                Counter(i["code"] for q in result["questions"] for i in q["issues"])
            ),
        }
    )
    report = {
        "domain": "mathematics",
        "stage": "mathematics_matching_retry_validation",
        "previously_unmatched": len(processed),
        "newly_matched": newly_matched,
        "still_unmatched": len(unresolved),
        "processed_ids": processed,
        "unresolved": unresolved,
    }
    return result, report
