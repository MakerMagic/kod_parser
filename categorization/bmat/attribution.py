"""BMAT evidence adapter over TSA's concept features and exemplar ranking.

Single dominant task is BMAT policy only. Low-evidence cases abstain for the
existing content-bound review procedure; neither numbers nor image presence
constitutes a Problem-Solving classification.
"""

import re

from categorization.model import REFINEMENT_RATIONALES, features, view

from .taxonomy import assign


def dependent_unit_rate_comparison(question):
    """Known compared entities, relative price, then two derived unit rates.

    The requested unit is explicit: ignoring an unused package mass is not a
    material applicability decision among competing tariffs/profiles.
    """
    stem = question.get("main_question") or ""
    body = question.get("question_text") or ""
    return bool(
        re.search(r"\bper\s+(?:day|week|month|hour|use|mile|km)\b", stem, re.IGNORECASE)
        and re.search(r"\b(?:how much (?:less|more)|difference)\b", stem, re.IGNORECASE)
        and re.search(r"\b(?:spend|cost|pay)\w*\b", stem, re.IGNORECASE)
        and len(re.findall(r"\blasts?\b", body, re.IGNORECASE)) >= 2
        and len(
            re.findall(
                r"\d+\s+(?:days?|weeks?|months?|hours?|uses?|miles?|km)\b",
                body,
                re.IGNORECASE,
            )
        )
        >= 2
        and re.search(
            r"\b(?:costs?|prices?|pays?)\b.{0,35}\b(?:more|less)\b", body, re.IGNORECASE
        )
    )


def problem_solving(question, result, model=None):
    v = view({"question": question})
    f = features(v)
    if model is not None:
        result["candidates"] = model.candidates(v)
    result["evidence"] = {k: bool(value) for k, value in f.items() if value}
    if dependent_unit_rate_comparison(question):
        result["evidence"]["dependent_unit_rate_comparison"] = True
        return assign(
            result,
            "ps_procedure",
            "Derive the second price from the relative cost, compute both explicitly requested unit rates and compare them. No competing applicability rules need selecting; the dependent rate procedure is material.",
        )
    if not f["argument_context"]:
        if (
            f["spatial_equivalence"]
            or f["representation_correspondence"]
            or f["method_equivalence"]
        ):
            return assign(
                result,
                "ps_similarity",
                "The requested output identifies a corresponding configuration/representation under an invariant; choosing an option is not data selection and a new state is not being computed.",
            )
        for name in (
            "roster_constraints",
            "flow_balance_constraints",
            "enclosure_composition",
        ):
            if f.get(name):
                return assign(result, "ps_procedure", REFINEMENT_RATIONALES[name])
        for name in (
            "constraint_simulation",
            "temporal_derivation",
            "relational_reconstruction",
        ):
            if f.get(name):
                return assign(
                    result,
                    "ps_procedure",
                    "The task requires a dependent constraint/time/relation process ("
                    + name
                    + "); the inputs alone do not give a finished applicable value or equivalent representation.",
                )
        if f.get("target_profile_selection") or f.get("scenario_tariff_selection"):
            return assign(
                result,
                "ps_select",
                "The scenario selects applicable rate/profile information from competing supplied data; highlighting that subset removes the material difficulty, leaving routine comparison.",
            )
    result.update(
        category=None,
        subcategories=[],
        patterns=[],
        status="needs_review",
        confidence="unresolved",
        rationale="TSA exemplar ranking alone does not establish the dominant task. Assess selection, procedure and equivalence against the complete BMAT question and source visuals.",
        issues=[
            {
                "code": "dominant_task_review",
                "reason": "Full task/materiality review is required; do not force the nearest lexical exemplar.",
            }
        ],
    )
    return result
