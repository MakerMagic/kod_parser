"""Bind supplied, content-reviewed explanations to canonical mathematics IDs.

No generation, matching by text, provider calls, or upstream mutation occurs.
Review decisions are data bound to the exact supplied explanation digest.
"""

from collections import Counter
from copy import deepcopy
from hashlib import sha256

from .mathematics import validate_explanation


def text_digest(text):
    return sha256(text.encode("utf8")).hexdigest()


def record(question, text, *, origin="assistant_direct", source=None):
    qid = question["id"]
    row = {
        k: question[k]
        for k in ("id", "source_pdf", "question_number", "content_sha256", "correct_answer")
    }
    row["explanation_origin"] = origin
    if source:
        row["import_source"] = deepcopy(source)
    row["final_explanation"] = {
        "status": "available", "ordering": "ai_generated_block_order",
        "blocks": [{"type": "paragraph", "role": "main", "order": 1, "text": text}],
        "unplaced_components": [], "omitted_artifacts": [], "issues": [],
        "source_type": "ai_generated_text_only", "explanation_by_ai": True,
        "source_reference": {
            "stage": "mathematics_pre_final", "question_id": qid,
            "content_sha256": question["content_sha256"],
        },
    }
    return row


def import_reviewed(data, existing, supplied, decisions, *, source):
    questions = {q["id"]: q for q in data["questions"]}
    counts = Counter(x.get("id") for x in supplied)
    result = deepcopy(existing)
    stored = {r["id"]: r for r in result.get("questions", [])}
    audit = []
    for item in supplied:
        qid, text = item.get("id"), item.get("explanation")
        entry = {"id": qid, "source": deepcopy(source)}
        if counts[qid] != 1:
            entry.update(status="duplicate_id", reason="Supplied ID occurs more than once")
        elif qid not in questions:
            entry.update(status="unknown_id", reason="ID absent from canonical mathematics PRE-FINAL")
        elif text is None:
            entry.update(status="no_explanation_supplied", reason="Supplied explanation is null")
        elif not isinstance(text, str) or not text.strip():
            entry.update(status="invalid_supplied_text", reason="Explanation must be a nonempty string")
        else:
            entry["explanation_sha256"] = text_digest(text)
            decision = decisions.get(qid, {})
            if (
                decision.get("explanation_sha256") != entry["explanation_sha256"]
                or decision.get("question_content_sha256") != questions[qid]["content_sha256"]
            ):
                entry.update(status="unreviewed", reason="No content review bound to this exact supplied text")
            elif decision.get("status") != "approved":
                entry.update(status="content_conflict", reason=decision.get("reason", "No approval"))
            elif qid in stored and not validate_explanation(questions[qid], stored[qid]):
                entry.update(status="existing_preserved", reason="A valid existing explanation was preserved")
            else:
                candidate = record(questions[qid], text, origin="user_supplied_ai", source=source)
                errors = validate_explanation(questions[qid], candidate)
                if errors:
                    entry.update(status="validation_failed", reason=", ".join(errors))
                else:
                    stored[qid] = candidate
                    entry.update(status="imported", reason="ID, source content, derivation and stored option reviewed")
        audit.append(entry)
    result["questions"] = sorted(stored.values(), key=lambda r: r["id"])
    return result, audit
