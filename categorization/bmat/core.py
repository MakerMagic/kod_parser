"""Independent BMAT task attribution from CLEAN records; never invent matching.

The TSA concept model and content-bound review are reused without modifying TSA.
BMAT retains one dominant canonical label and separate upstream/skip state.
"""

import json
import re
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from categorization.model import features, question_modalities, view
from processors.normalization.bmat.backtest import load

OWNER = "bmat_categorization_v1"
CATALOG = Path(__file__).parents[1] / "patterns.json"


def _critical_thinking(question):
    result = {
        "category": None,
        "subcategories": [],
        "patterns": [],
        "status": "not_evaluated",
        "confidence": "unresolved",
        "rationale": "Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label.",
        "issues": [],
    }
    if question["bmat_filter"]["skip_from_pipeline"]:
        result.update(
            status="intentional_skip",
            confidence="high",
            rationale=question["bmat_filter"]["skip_reason"],
        )
        return result
    if question["cleaning_issues"]:
        result.update(
            status="needs_review",
            rationale="Upstream defects remain: "
            + ", ".join(sorted({i["code"] for i in question["cleaning_issues"]})),
        )
        result["issues"] = deepcopy(question["cleaning_issues"])
        return result
    v = view({"question": question})
    from parsers.bmat.semantic_filters import proposition_structure

    intent = re.split(r"(?m)^\s*1[.)]?\s+", v["stem"], maxsplit=1)[0]
    f = features({**v, "stem": intent})
    s = " ".join(intent.split())
    opts = v["options"]
    source_body = (
        (question.get("raw_record") or {})
        .get("raw_components", {})
        .get("main_body", v["body"].removesuffix(v["stem"]))
    )
    listed = proposition_structure(
        {
            "raw_components": {"main_question": v["stem"], "main_body": source_body},
            "options": opts,
        },
        expected_count=None,
    )
    list_context = bool(
        listed
        and len(source_body.split()) >= 30
        and re.search(r"\b(?:argument|reasoning|passage|above)\b", s, re.IGNORECASE)
    )
    evidence = {
        k: bool(f[k])
        for k in (
            "existing_claim",
            "new_inference",
            "needed_premise",
            "evidence_change",
            "reasoning_defect",
            "analogy_task",
            "principle_application",
            "argument_context",
        )
    }
    # A request to diagnose an erroneous inferential step is distinct from a
    # request to assess new evidence, even when diagnosis is phrased 'if true'.
    flaw = re.search(
        r"\b(?:wrong with|flaw\w*|weakness|errors? in|mistake in)\b", s, re.IGNORECASE
    )
    argument = re.search(
        r"\b(?:argument|reasoning|inference|hypothesis|theory|position|claim)\b",
        s,
        re.IGNORECASE,
    )
    prose_choices = sum(len(o["text"].split()) >= 4 for o in opts) >= 3 or list_context
    if list_context:
        evidence["argument_context"] = True
    if (
        re.search(r"\bmatch\w*\b.{0,35}\b(?:reasoning|argument)\b", s, re.IGNORECASE)
        and argument
        and prose_choices
    ):
        evidence["analogy_task"] = True
        evidence["argument_context"] = True
    impact_request = re.search(
        r"\b(?:would|could|if true)\b.{0,55}\b(?:weaken\w*|strengthen\w*|undermine\w*|cast doubt)\b",
        s,
        re.IGNORECASE,
    )
    if impact_request and argument and prose_choices:
        evidence["reasoning_defect"] = False
        evidence["evidence_change"] = True
        evidence["existing_claim"] = (
            False  # the conclusion is the object being weakened, not a requested identification
        )
        evidence["new_inference"] = False
        evidence["needed_premise"] = False
        evidence["argument_context"] = True
    if (
        flaw
        and argument
        and prose_choices
        and not evidence["analogy_task"]
        and not impact_request
    ):
        evidence["reasoning_defect"] = True
        evidence["evidence_change"] = False
        evidence["argument_context"] = True
    direct_assumption = re.search(
        r"\b(?:which|what)\b.{0,65}\bassumptions?\b", s, re.IGNORECASE
    )
    if direct_assumption and prose_choices and not flaw and not impact_request:
        evidence["needed_premise"] = True
        evidence["argument_context"] = True
    explicit_conclusion = re.search(
        r"\bconclusion\b.{0,50}\b(?:drawn|deduced|follows)\b|\b(?:drawn|deduced)\b.{0,30}\bconclusion\b",
        s,
        re.IGNORECASE,
    )
    if explicit_conclusion and prose_choices:
        evidence["new_inference"] = True
        evidence["needed_premise"] = (
            False  # 'Assuming ..., which conclusion?' is conditional data, not the requested operation.
        )
        evidence["argument_context"] = True
    stated_conclusion = re.search(
        r"\b(?:best|clearest)\s+(?:statement|expression)\s+of\s+(?:the\s+)?(?:main\s+)?conclusion\b",
        s,
        re.IGNORECASE,
    )
    if stated_conclusion and argument and prose_choices and not explicit_conclusion:
        evidence["existing_claim"] = True
        evidence["new_inference"] = False
        evidence["argument_context"] = True
    patterns = json.loads(CATALOG.read_text(encoding="utf-8"))["patterns"]
    keyed = {
        p["positive_indicators"][0]: p
        for p in patterns
        if p["category"] == "Critical Thinking"
    }
    active = [key for key in keyed if evidence.get(key)]
    if not active:
        if re.search(
            r"\b(?:inferen\w*|justif\w*|supported|conclu\w*|assumptions?|assumed|flaw\w*)\b",
            s,
            re.IGNORECASE,
        ):
            result.update(
                status="needs_review",
                rationale="Evidence/argument request lacks one unambiguous supported task intent; do not force inference versus conclusion or an unstated operation.",
            )
            result["issues"] = [
                {"code": "semantic_intent_unresolved", "reason": result["rationale"]}
            ]
        return result
    # Two/four-proposition combination questions are not the three-subpoint
    # exclusion; nor do we pretend a scalar intent resolves their full task.
    combined = not listed and (
        sum(
            bool(
                re.fullmatch(
                    r"[\d\s,&]+(?:and|only)?[\d\s,&]*|(?:both|neither|none|all)\b.*",
                    o["text"].strip(),
                    re.IGNORECASE,
                )
            )
            for o in opts
        )
        >= 2
    )
    if (
        len(active) != 1
        or not evidence["argument_context"]
        or combined
        or "visual" in question_modalities(question)
    ):
        reasons = []
        if len(active) != 1:
            reasons.append("competing requested operations: " + ", ".join(active))
        if not evidence["argument_context"]:
            reasons.append("passage/argument context is not sufficiently established")
        if combined:
            count = len(re.findall(r"(?m)^\s*[1-9][.)]?\s+", v["stem"]))
            reasons.append(
                f"combination-valued answer set ({count} numbered propositions); outside the exactly-three Subpoints exclusion, and scalar attribution does not resolve the complete task"
            )
        if "visual" in question_modalities(question):
            reasons.append(
                "meaningful question visual is incompatible with the current text-only Critical Thinking family"
            )
        result.update(
            status="needs_review",
            rationale="; ".join(reasons) + ".",
        )
        result["issues"] = [
            {"code": "semantic_structure_review", "reason": result["rationale"]}
        ]
    else:
        p = keyed[active[0]]
        result.update(
            category=p["category"],
            subcategories=[p["subcategory"]],
            patterns=[p["id"]],
            status="supported",
            confidence="high",
            rationale=p["description"],
        )
        if list_context:
            result["rationale"] += (
                f" Evaluate {len(listed['statements'])} listed propositions by the same requested operation; choose one combination-valued answer. This is not the exactly-three BMAT exclusion."
            )
    result["evidence"] = evidence
    return result


def attribution(question, model=None):
    from .attribution import problem_solving
    from .taxonomy import assign, special

    result = _critical_thinking(question)
    if result["status"] == "needs_review" and question["cleaning_issues"]:
        return result
    if label := special(question):
        name, reason, method = label
        return assign(result, name, reason, status="intentional_skip", method=method)
    if result["status"] == "supported":
        result["decision_method"] = "tsa_argument_intent_with_bmat_context"
        return result
    return problem_solving(question, result, model)


def build(inputs, matched_path=None, review_path=None, model_path=None):
    from categorization.core import file_ref
    from categorization.model import Model

    from .review import apply as apply_review
    from .review import load as load_review
    from .taxonomy import validate

    decisions = load_review(review_path) if review_path is not None else {}
    model = None
    if model_path is not None:
        trained = json.loads(Path(model_path).read_text(encoding="utf-8"))
        model = Model(trained["examples"], trained["patterns"]["patterns"])
    matching, matching_source = {}, None
    if matched_path is not None:
        from processors.matching.storage import load_matched

        matched_path = Path(matched_path).resolve()
        matched = load_matched(matched_path)
        for source in matched["inputs"]:
            if (
                sha256(Path(source["path"]).read_bytes()).hexdigest()
                != source["sha256"]
            ):
                raise ValueError("Stale BMAT matching context")
        matching_source = {
            "path": str(matched_path),
            "sha256": sha256(matched_path.read_bytes()).hexdigest(),
        }
        for index, record in enumerate(matched["records"]):
            identity = record["identity"]
            if (
                identity.get("source_family") != "bmat"
                or identity.get("section") != "section_1"
            ):
                raise ValueError("Not BMAT Section 1 matching context")
            key = (identity["year"], identity["question_number"])
            if key in matching:
                raise ValueError("Duplicate BMAT matching context")
            matching[key] = (index, record)
    paths = sorted(
        {
            p.resolve()
            for root in inputs
            for p in (
                Path(root).glob("*.clean.json") if Path(root).is_dir() else [Path(root)]
            )
        }
    )
    records, sources, seen = [], [], set()
    if not paths:
        raise ValueError("No BMAT CLEAN inputs")
    for path in paths:
        data = load(path)
        digest = sha256(path.read_bytes()).hexdigest()
        sources.append({"path": str(path), "sha256": digest})
        for index, q in enumerate(data["questions"]):
            if q["question_id"] in seen:
                raise ValueError("Duplicate BMAT identity")
            seen.add(q["question_id"])
            match = matching.get((q["metadata"]["year"], q["question_number"]))
            if matched_path is not None and (not match or match[1]["question"] != q):
                raise ValueError(
                    "BMAT matching question snapshot differs from categorization input"
                )
            records.append(
                {
                    "identity": deepcopy(q["source_question_key"]),
                    "question_id": q["question_id"],
                    "question": deepcopy(q),
                    "question_reference": {
                        "path": str(path),
                        "sha256": digest,
                        "json_pointer": f"/questions/{index}",
                    },
                    "matching_status": match[1]["status"] if match else "not_run",
                    "matching_reference": {
                        **matching_source,
                        "json_pointer": f"/records/{match[0]}",
                    }
                    if match
                    else None,
                    "categorization": attribution(q, model),
                }
            )
            row = records[-1]
            apply_review(row["categorization"], row, decisions)
            validate(row["categorization"])
    return {
        "owner": OWNER,
        "stage": "categorization",
        "input_stage": "clean",
        "scope": "Complete BMAT dominant-task categorization; one canonical category per eligible question, independent upstream/matching state retained",
        "taxonomy_reference": {
            "path": str(CATALOG.resolve()),
            "sha256": sha256(CATALOG.read_bytes()).hexdigest(),
        },
        "sources": sources,
        "matching_source": matching_source,
        "review_reference": file_ref(review_path) if review_path is not None else None,
        "model_reference": file_ref(model_path) if model_path is not None else None,
        "definition_references": [
            file_ref(
                Path(__file__).resolve().parents[2] / "parsers/bmat/skip_rules.py"
            ),
            file_ref(
                Path(__file__).resolve().parents[2] / "parsers/bmat/semantic_filters.py"
            ),
            file_ref(Path(__file__).parents[1] / "ps_attribution_rulebook.txt"),
        ],
        "records": records,
        "summary": dict(Counter(r["categorization"]["status"] for r in records)),
    }


def write(path, data):
    path = Path(path)
    if (
        path.exists()
        and json.loads(path.read_text(encoding="utf-8")).get("owner") != OWNER
    ):
        raise ValueError("Refusing unrelated categorization overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def refresh_context(path, matched_path, review_path, model_path):
    """Refresh references and changed review decisions, not corpus recategorization."""
    from categorization.core import digest, file_ref, verify_refs
    from categorization.model import Model
    from processors.matching.storage import load_matched

    from .review import apply as apply_review
    from .review import load as load_review
    from .taxonomy import validate

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    decisions = load_review(review_path)
    matching = load_matched(matched_path)
    verify_refs([*data["sources"], *matching["inputs"]])
    model_data = json.loads(Path(model_path).read_text(encoding="utf-8"))
    model = Model(model_data["examples"], model_data["patterns"]["patterns"])
    positions = {
        r["question"]["question_id"]: (i, r)
        for i, r in enumerate(matching["records"])
        if r.get("question")
    }
    changed = []
    ref = file_ref(matched_path)
    for row in data["records"]:
        i, match = positions[row["question_id"]]
        if row["question"] != match["question"]:
            raise ValueError(
                "Changed question requires upstream propagation and fresh review"
            )
        row["matching_status"] = match["status"]
        row["matching_reference"] = {**ref, "json_pointer": f"/records/{i}"}
        decision = decisions.get(digest(row["question"]))
        old = row["categorization"].get("review", {})
        if decision and (
            old.get("proposed_category") != decision["category_id"]
            or row["categorization"]["rationale"] != decision["evidence"]
        ):
            row["categorization"] = attribution(row["question"], model)
            apply_review(row["categorization"], row, decisions)
            changed.append(row["identity"])
        validate(row["categorization"])
    data["matching_source"] = ref
    data["review_reference"] = file_ref(review_path)
    data["summary"] = dict(
        Counter(r["categorization"]["status"] for r in data["records"])
    )
    write(path, data)
    return changed
