"""Preserve reviewed decisions across proven whitespace/boundary-only changes.

This is an explicit migration, not an alternative classifier or a relaxation of
normal content-hash checks. Only verified CLEAN prose case/terminal-punctuation
edits and whitespace may change; math, options, assets and identity remain exact.
"""

from copy import deepcopy

from categorization.core import digest
from processors.normalization.mathematics.structure import token_ledger
from processors.normalization.mathematics.text_quality import polish, sync_prose

from .core import semantic_content


def rebind_structure(reviews, previous_clean, cleaned, previous_categorized):
    before = {q["id"]: q for q in previous_clean["questions"]}
    decisions = {q["id"]: q for q in previous_categorized["questions"]}
    if set(before) != {q["id"] for q in cleaned["questions"]}:
        raise ValueError("Structural migration cannot change the source question set")
    result = deepcopy(reviews)
    changes = dict(result.get("structure_rebindings", {}))
    for q in cleaned["questions"]:
        old = before[q["id"]]
        for key in (
            "id",
            "source_document_id",
            "question_number",
            "assets",
            "raw",
            "regions",
            "issues",
        ):
            if old.get(key) != q.get(key):
                raise ValueError(f"Structural migration changed {key}: {q['id']}")
        # Only the explicitly verified CLEAN prose edits can extend the earlier
        # whitespace migration. Mathematical tokens remain exact.
        expected_content = old['content']
        if 'main_body' in old and 'main_question' in old:
            body, prompt, _ = polish(old['main_body'], old['main_question'])
            expected_content = sync_prose(old['content'], body, prompt)
        if token_ledger(expected_content) != token_ledger(q["content"]):
            raise ValueError("Structural migration changed body meaning/order")
        if [o["label"] for o in old["options"]] != [
            o["label"] for o in q["options"]
        ] or any(
            token_ledger(a["content"]) != token_ledger(b["content"])
            for a, b in zip(old["options"], q["options"], strict=True)
        ):
            raise ValueError("Structural migration changed options")
        old_hash, new_hash = (digest(semantic_content(row)) for row in (old, q))
        if old_hash == new_hash:
            continue
        stored = decisions.get(q["id"])
        if stored:
            if stored["content_sha256"] != old_hash:
                raise ValueError(
                    "Previous categorization does not bind to previous CLEAN"
                )
            decision = stored["assessment"]
        else:
            decision = reviews["assessments"].get(old_hash)
        if decision is None:
            continue  # An unreviewed question must remain unreviewed.
        existing = result["assessments"].get(new_hash)
        if existing is not None and existing != decision:
            raise ValueError(
                "Conflicting reviewed assessments after structural migration"
            )
        result["assessments"][new_hash] = deepcopy(decision)
        changes[old_hash] = new_hash
    result["structure_rebindings"] = dict(sorted(changes.items()))
    return result
