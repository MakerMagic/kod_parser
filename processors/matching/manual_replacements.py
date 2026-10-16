"""Only an explicit, fingerprint-pinned manual explanation can supersede a source.

No manual-source preference and no arbitrary duplicate selection: one approved
manual record must identify exactly one unchanged PDF candidate, with the same
answer and question identity. All original content/warnings remain archived.
"""

import json
from hashlib import sha256


def select_manual_replacement(candidates, question_key=None):
    if len(candidates) != 2:
        return candidates, []
    manual = [
        c
        for c in candidates
        if c["record"].get("provenance", {}).get("replaces_explanation")
        and c["record"]["provenance"].get("origin") == "user_supplied_manual"
        and c["record"]["provenance"].get("approval") == "single_question"
    ]
    if len(manual) != 1:
        return candidates, []
    chosen = manual[0]
    original = next(c for c in candidates if c is not chosen)
    a, b = chosen["record"], original["record"]
    pin = a["provenance"]["replaces_explanation"]
    fingerprint = sha256(
        json.dumps(b["explanation"], ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if (
        original["document"].get("media_type") == "application/json"
        or pin.get("answer_id") != b["answer_id"]
        or pin.get("source_sha256") != b["source_document"]["sha256"]
        or pin.get("explanation_sha256") != fingerprint
        or a["correct_answer"] != b["correct_answer"]
        or any(a.get(k) != b.get(k) for k in ("year", "section", "question_number"))
        or any(
            a.get(k) is not None and b.get(k) is not None and a[k] != b[k]
            for k in ("paper", "variant")
        )
        or not question_key
        or a.get("target_question_key") != question_key
    ):
        return candidates, []
    for fragment in a["provenance"].get("preserved_source_fragments", []):
        originals = [
            p for p in b["explanation"]["blocks"] if p.get("order") == fragment["order"]
        ]
        if len(originals) != 1 or originals[0].get("text") != fragment["text"]:
            return candidates, []
        if not any(
            p.get("text") == fragment["text"] for p in a["explanation"]["blocks"]
        ):
            return candidates, []
    return [chosen], [original]
