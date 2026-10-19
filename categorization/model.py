"""Interpretable semantic features + learned exemplars, with abstention.

Task concepts combine a requested operation with its object/context. The model
learns pattern profiles from reviewed examples, not question-ID/phrase lookups.
TF-IDF stem evidence is secondary to concept-profile agreement. Similarity scores
are evidence support, not calibrated probabilities or claims of human review.
"""

import json
import math
import re
from collections import Counter
from functools import cache
from itertools import pairwise
from pathlib import Path

PROCEDURAL_CONTEXTS = (
    "temporal_derivation",
    "relational_reconstruction",
    "constraint_simulation",
)
REFINED_PROCEDURES = (
    "roster_constraints",
    "discrete_unit_procedure",
    "enclosure_composition",
    "unit_basis_conversion",
    "flow_balance_constraints",
)
REFINED_OPERATIONS = (
    *REFINED_PROCEDURES,
    "target_profile_selection",
    "representation_correspondence",
)
REFINEMENT_RATIONALES = {
    "roster_constraints": "Construct and test a multi-person duty schedule under individual totals and consecutive-night restrictions; no supplied-data subset or equivalent representation answers the request.",
    "discrete_unit_procedure": "First determine complete scoring/billing units, associate each entity with its own rate, then compare the derived totals. The required unit truncation and dependent calculation are not supplied as a finished formula.",
    "enclosure_composition": "Construct the requested outside dimension from nested layers, accounting for opposite edges and asymmetric margins; the final addition is routine only after that model is established.",
    "target_profile_selection": "Select the requested ratio/profile and benchmark rather than raw counts when comparing candidate table entries. Inspecting every candidate row does not remove this material choice of applicable information basis.",
    "representation_correspondence": "Recognise which alternative visual encodes the specified data or relationship, preserving ordering/shape correspondence. Routine preparation of an explicitly requested statistic is not independently substantial procedural construction.",
    "unit_basis_conversion": "Revenue intervals must first be converted through category-specific entry prices to visitor counts, before those counts can be matched to pie proportions; unit conversion and representation correspondence are independently material.",
    "flow_balance_constraints": "Combine all directed transfers into entity-level balance changes, then test candidate states against those conserved totals. The requested feasibility check requires constructing a process, not just matching a supplied data representation.",
}


@cache
def semantic_families():
    return json.loads(
        (Path(__file__).parent / "patterns.json").read_text(encoding="utf-8")
    ).get("semantic_families", [])


def family_evidence(stem, context, families=None):
    """Lexical evidence is accepted only with the declared structural context."""
    return {
        p["feature"]: bool(
            any(has(stem, x) for x in p["lexical_indicators"])
            and all(context.get(x) for x in p["requires_all"])
            and (
                not p.get("requires_any")
                or any(context.get(x) for x in p["requires_any"])
            )
            and not any(context.get(x) for x in p["counter_evidence"])
        )
        for p in (semantic_families() if families is None else families)
    }


def category_metadata():
    return json.loads(
        (Path(__file__).parent / "patterns.json").read_text(encoding="utf-8")
    )["categories"]


def question_modalities(q):
    """Question assets only: source screenshots/explanation images are not tasks."""

    def meaningful(a):
        return (
            isinstance(a, dict)
            and bool(a.get("path") or a.get("image_id") or a.get("asset_id"))
            and a.get("asset_type")
            not in {"rendered_question", "page_preview", "source_screenshot"}
            and a.get("role") not in {"decorative", "preview", "superseded"}
            and not a.get("decorative", False)
        )

    visual = any(
        b.get("type") in {"visual", "image", "table", "diagram"} and meaningful(b)
        for b in q.get("main_body") or []
    )
    visual = visual or any(
        meaningful(a) for o in q.get("options") or [] for a in o.get("images") or []
    )
    visual = visual or any(meaningful(a) for a in q.get("visual_assets") or [])
    preview_paths = {
        a.get("path") for a in q.get("visual_previews") or [] if a.get("path")
    }
    preview_ids = {
        a.get("image_id") for a in q.get("visual_previews") or [] if a.get("image_id")
    }
    visual = visual or any(
        meaningful(a)
        and a.get("path") not in preview_paths
        and a.get("asset_id") not in preview_ids
        for a in q.get("images") or []
    )
    return ["text", "visual"] if visual else ["text"]


def has(text, pattern):
    return bool(re.search(pattern, " ".join(text.split()), re.IGNORECASE))


def explanation_text(record):
    parts = []
    for block in (record.get("final_explanation") or {}).get("blocks", []):
        if block.get("role", "").startswith("incorrect_choices"):
            continue
        if block.get("text"):
            parts.append(block["text"])
        parts.extend(i["text"] for i in block.get("items", []) if i.get("text"))
    return "\n".join(parts)


def view(record):
    q = record.get("question") or {}
    return {
        "stem": q.get("main_question") or "",
        "body": q.get("question_text") or "",
        "options": q.get("options") or [],
        "explanation": explanation_text(record),
        "modalities": question_modalities(q),
        "body_visual": any(b.get("type") == "visual" for b in q.get("main_body") or []),
    }


def features(v, *, families=None):
    s, b, e = v["stem"], v["body"], v["explanation"]
    option_text = [o.get("text") or "" for o in v["options"]]
    argument = has(s, r"\b(argument|reasoning|passage|author|premises?|claims?)\b")
    long_options = sum(len(t.split()) >= 8 for t in option_text) >= 3
    argument_support = long_options or (
        sum(len(t.split()) >= 5 for t in option_text) >= 3 and len(b.split()) >= 45
    )
    infer_request = has(
        s, r"\b(conclud\w*|infer\w*|deduc\w*|drawn|follows?|supported)\b"
    )
    source_reference = has(
        s, r"\b(argument|reasoning|passage|author|information|above|given|supplied)\b"
    )
    direction_relations = len(
        re.findall(
            r"\b(?:is|lies|situated|located)\s+(?:due\s+)?(?:north|south|east|west)(?:-[a-z]+)?\s+of\b",
            b,
            re.IGNORECASE,
        )
    )
    calendar = has(
        b,
        r"\b(month|January|February|March|April|May|June|July|August|September|October|November|December)\b",
    ) and has(
        b,
        r"\b(days?|weeks?|Monday\w*|Tuesday\w*|Wednesday\w*|Thursday\w*|Friday\w*|Saturday\w*|Sunday\w*)\b",
    )
    bounded_calendar = (
        calendar
        and len(
            re.findall(
                r"\b(?:\d+|one|two|three|four|five|six|seven)\s+(?:days|weeks|Mondays|Tuesdays|Wednesdays|Thursdays|Fridays|Saturdays|Sundays)\b",
                b,
                re.IGNORECASE,
            )
        )
        >= 2
    )
    formal_rules = len(
        re.findall(
            r"\b(?:must|only|at least|at most|exactly|before|after|cannot|no more than)\b",
            b,
            re.IGNORECASE,
        )
    ) >= 2 and has(
        b,
        r"\b(seats?|positions?|arrang\w*|rows?|teams?|players?|order|allocat\w*|schedules?)\b",
    )
    argument = argument or (
        infer_request
        and source_reference
        and argument_support
        and not formal_rules
        and not bounded_calendar
        and not direction_relations
        and not has(s, r"\b(graph|table|chart|diagram)\b")
    )
    temporal_chain = (
        len(re.findall(r"\b(?:minutes?|hours?)\b", b, re.IGNORECASE)) >= 3
        and len(
            re.findall(
                r"\b(?:late|delay\w*|slower|faster|fast|slow|behind|ahead|longer|anticipated|expected)\b",
                b,
                re.IGNORECASE,
            )
        )
        >= 2
        and has(b, r"\b(clock|watch|local time|train|taxi|travel)\b")
    )
    quantitative = (
        len(re.findall(r"\d+(?:[.:]\d+)?", b)) >= 3
        or has(
            b,
            r"[%£$]|\b(percent|prices?|costs?|rates?|lengths?|discs?|quantities|proportions?)\b",
        )
        or (
            has(b, r"\b(two|three|four|five|six|seven|eight|nine|ten|twelve|hundred)\b")
            and has(
                b, r"\b(dials?|letters?|workers?|items?|points?|scores?|quantities)\b"
            )
        )
    )
    spatial = has(
        s + " " + b,
        r"\b(cubes?|shapes?|views?|fold\w*|unfold\w*|nets?|tiles?|rotat\w*|reflect\w*|diagrams?|graphs?|arrangements?|configurations?|solid|octahedron|prism|sheet of paper)\b",
    )
    dataset = len(re.findall(r"\d+(?:[.:]\d+)?", b)) >= 12 or has(
        b, r"\b(table|charts?|graphs?|timetable|price list|specifications|figures)\b"
    )
    arithmetic_steps = sum(
        bool(re.search(r"\d[^\n]{0,65}[=×÷][^\n]*\d", line)) for line in e.splitlines()
    )
    steps = has(e, r"\b(first|start|previously)\b") and has(
        e, r"\b(then|next|finally|remaining|now|therefore)\b"
    )
    restrictive = has(
        s,
        r"\b(least|cheapest|largest|smallest|which|who|greater|more|above|below|sufficient|false|not true)\b",
    )
    relevance = has(
        e,
        r"\b(ignore|unnecessary|irrelevant|not necessary|only (?:need|have) to (?:consider|look)|focus on|only[^.!?]*possibilities|don.t satisfy|eliminate the.{0,35}requirements)\b",
    )
    central = has(s, r"\b(main|principal|central|primary)\b")
    conclusion = has(s, r"\b(conclusion|claim|point|assertion)\b")
    infer = infer_request or has(s, r"\b(warranted|draw)\b")
    analogy = has(s, r"\b(parallel\w*|analog\w*|same|similar)\b") and has(
        s, r"\b(reasoning|argument|flaw|inference)\b"
    )
    option_arguments = (
        sum(
            has(t, r"\b(if|therefore|because|thus|so)\b") and len(t.split()) >= 12
            for t in option_text
        )
        >= 3
    )
    analogy = analogy or (
        has(s, r"\billustrat\w*\b") and has(s, r"\bflaw\b") and option_arguments
    )
    context = {
        "argument_referent": argument_support
        and (
            argument
            or (
                source_reference
                and has(
                    b, r"\b(should|ought|morally|justice|deserve\w*|wrong|rights?)\b"
                )
            )
        ),
        "principle_object": has(s, r"\b(principle|rule)\b")
        or (
            has(s, r"\b(author|advocat\w*|recommend\w*)\b")
            and has(b, r"\b(should|ought|morally|must)\b")
        ),
        "competing_task": has(
            s,
            r"\b(main conclusion|principal claim|assum\w*|flaw|reasoning error|concluded|infer\w*)\b",
        ),
        "argument_target": source_reference and argument_support,
        "prospective_input": has(
            s,
            r"\b(if true|would|new|additional|challenge|cast doubt|convincing|supports?|strengthens?|weakens?|undermines?)\b",
        ),
        "inference_direction": has(
            s, r"\b(supported by|follows? from|can (?:reliably )?be concluded)\b"
        ),
        "nonargument": not argument,
        "temporal_chain": temporal_chain,
        "direction_chain": direction_relations >= 2,
        "constraint_system": bounded_calendar or formal_rules,
        "usage_tariff_context": (
            dataset
            and quantitative
            and has(
                b, r"\b(tariffs?|plans?|rental|standing charge|fixed.{0,15}charge)\b"
            )
            and has(
                b,
                r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|hundred)\s+(?:minutes?|units?|journeys?|calls?|hours?)\b",
            )
            and has(b, r"\b(per|each|every)\s+(?:month|week|day)|monthly\b")
            and len(re.findall(r"\b(?:tariff|rental|charge|plan)\b", b, re.IGNORECASE))
            >= 3
        ),
    }
    semantic = family_evidence(s, context, families)
    principle = semantic.get("principle_application", False)
    argument = argument or principle or semantic.get("evidence_change", False)
    equivalence = (
        has(s, r"\b(same|equivalent|identical)\b")
        and has(s, r"\b(method|calculation|offers?|discounts?)\b")
    ) or (
        has(s, r"\b(same|equivalent)\b")
        and has(s, r"\bas that above\b")
        and quantitative
        and not argument
    )
    # Recognition of a corresponding representation, not the act of choosing,
    # counting folds/steps, building an arrangement, or superficial resemblance.
    spatial_object = spatial and has(
        s + " " + b,
        r"\b(cubes?|shapes?|views?|nets?|diagrams?|dice|die|paper|solid|octahedron|prism|configuration|arrangement|patterns?|objects?)\b",
    )
    choice_request = has(s, r"\b(which|what|identify|choose|select|match)\b")
    representation = has(
        s,
        r"\b(views?|viewed|unfold\w*|fold\w*|rotat\w*|reflect\w*|mirror|cut.out|nets?)\b",
    )
    correspondence = has(
        s, r"\b(same|identical|equivalent|correspond\w*|match\w*)\b"
    ) and has(
        s,
        r"\b(structure|relationship|configuration|arrangement|patterns?|shapes?|objects?|diagrams?|dice|die)\b",
    )
    correspondence = correspondence or (
        has(s, r"\bsame information\b")
        and has(s, r"\b(different form|another representation)\b")
    )
    quantitative_request = has(
        s,
        r"\b(how (?:many|much|long)|volume|area|number of|minimum|maximum|cost|time|distance|speed)\b",
    )
    dynamic_state = has(
        s, r"\b(end position|next move|next turn|after \d+|how many turns)\b"
    )
    spatial_equivalence = bool(
        choice_request
        and spatial_object
        and (representation or correspondence)
        and not quantitative_request
        and not dynamic_state
        and not argument
    )
    relational_equivalence = bool(
        choice_request
        and not argument
        and correspondence
        and has(
            b,
            r"\b(mapping|pairs?|sequence|correspond\w*|relationship|configuration|arrangement)\b",
        )
    )
    image_options = sum(bool(o.get("images")) for o in v["options"]) >= 3
    visual_source = bool(v.get("body_visual"))
    chart_target = (
        choice_request
        and has(s, r"\b(charts?|graphs?|diagrams?)\b")
        and has(s, r"\b(represent\w*|shows?|illustrat\w*|correspond\w*)\b")
    )
    transfer_process = (
        len(
            re.findall(
                r"\b(?:chang\w*|transfer\w*|mov\w*)\b[^.!?\n]{0,70}\bfrom\b[^.!?\n]{0,45}\bto\b",
                b,
                re.IGNORECASE,
            )
        )
        >= 2
    )
    state_model = has(
        b, r"\b(fill\w*|empty\w*|taps?|flow\w*|mixtures?|recipes?)\b"
    ) and has(
        b, r"\b(before|after|turn\w*|changes?|new|less|more|increas\w*|decreas\w*)\b"
    )
    fixed_representation = (
        chart_target
        and (visual_source or dataset)
        and not transfer_process
        and not state_model
        and not spatial_equivalence
        and not has(b, r"\b(journey|travels?|moves?|rolls?|turns? (?:left|right))\b")
    )
    container_mapping = (
        image_options
        and visual_source
        and has(s, r"\bcontainers?\b.*\brepresent\w*\b")
        and has(
            b, r"\bgraphs?\b.*\b(?:depth|height)\b|\b(?:depth|height)\b.*\bgraphs?\b"
        )
    )
    complementary_shapes = (
        image_options
        and has(b, r"\bidentical\b")
        and has(b, r"\bfit together\b.*\bcomplete (?:disc|disk|circle)\b")
        and choice_request
    )
    axis_mapping = (
        image_options
        and visual_source
        and has(s, r"\baxis\b.*\brevers\w*\b")
        and has(s, r"\bsymmetr\w*\b")
    )
    representation_correspondence = bool(
        not argument
        and not dynamic_state
        and (
            fixed_representation
            or container_mapping
            or complementary_shapes
            or axis_mapping
        )
    )
    target_profile = bool(
        dataset
        and visual_source
        and not argument
        and has(b, r"\b(numbers?|counts?|aged|children|people)\b")
        and has(s, r"\b(proportion|ratio|percentage)\b")
        and has(s, r"\b(nearest|closest|most similar)\b")
        and has(s, r"\b(that for|as (?:that|for)|compared (?:with|to))\b")
        and sum(
            bool(t) and len(t.split()) <= 4 and not re.search(r"\d", t)
            for t in option_text
        )
        >= 3
        and not image_options
    )
    roster = bool(
        not argument
        and has(b, r"\b(duty|shifts?|guards?|roster)\b")
        and has(b, r"\bconsecutive\b")
        and has(b, r"\b(?:must|not allow|no more than|at most)\b")
        and has(s, r"\b(nights?|days?|duty|shifts?)\b")
        and len(
            re.findall(
                r"\b(?:two|three|four|five|six|\d+)\s+(?:nights?|days?|shifts?)\b",
                b,
                re.IGNORECASE,
            )
        )
        >= 2
    )
    discrete = bool(
        quantitative
        and not argument
        and has(b, r"\b(?:per|each)\s+(?:complete|whole|full)\s+\d+\b")
        and len(re.findall(r"\bper\s+\d+\b", b, re.IGNORECASE)) >= 2
        and has(s, r"\b(who|which|amount|total|earned|raised|paid)\b")
    )
    enclosure = bool(
        quantitative
        and not argument
        and has(
            s,
            r"\b(overall|total|outside|external)\b.*\b(height|width|length|dimensions?)\b",
        )
        and len(
            re.findall(r"\b(frame|mount|border|margin|surround\w*)\b", b, re.IGNORECASE)
        )
        >= 3
        and has(b, r"\b(top|bottom|sides?)\b")
        and has(b, r"\b(high|wide|height|width)\b")
        and not has(b, r"\bformula\b|\bheight\s*=")
    )
    unit_conversion = bool(
        representation_correspondence
        and has(s, r"\bnumber of (?:visitors|people|customers)\b")
        and has(b, r"\b(takings|revenue|receipts)\b")
        and has(b, r"\b(cost of entry|admission|entry (?:cost|price|fee))\b")
    )
    f = {
        "argument_context": float(argument and argument_support),
        "propositional_options": float(long_options),
        "quantitative_context": float(
            quantitative or bounded_calendar or temporal_chain
        ),
        "numerical_options": float(
            sum(bool(re.search(r"\d", t)) and len(t.split()) <= 6 for t in option_text)
            >= 3
        ),
        "conditional_options": float(
            sum(has(t, r"\b(if|unless|only if|therefore)\b") for t in option_text) >= 3
        ),
        "existing_claim": float(
            (central or has(s, r"\b(express\w*|summari\w*|restate\w*|encapsulat\w*)\b"))
            and conclusion
            and not infer
        ),
        "new_inference": float(
            infer
            and not central
            and (argument or conclusion)
            and not semantic.get("evidence_change")
        ),
        "needed_premise": float(
            has(s, r"\b(assum\w*|unstated|implicit|unspoken|presuppos\w*)\b")
            and argument
        ),
        "evidence_change": float(semantic.get("evidence_change", False)),
        "reasoning_defect": float(
            has(s, r"\b(flaw\w*|error|mistake|invalid|defect)\b")
            and argument
            and not analogy
        ),
        "analogy_task": float(analogy),
        "principle_application": float(principle),
        "data_filter": float(dataset and restrictive and not argument),
        "relevance_witness": float(relevance and not argument),
        "spatial_filter": float(
            spatial
            and has(s, r"\b(view|views|shapes?|patterns?)\b")
            and has(s, r"\b(possible|cannot|could|may|not)\b")
            and not argument
        ),
        "dependent_calculation": float(
            arithmetic_steps >= 2 and quantitative and not argument
        ),
        "rule_process": float(
            has(b, r"\b(repeat\w*|each time|procedure|process|adjacent bits)\b")
            and quantitative
            and not argument
        ),
        "constraint_construction": float(
            has(s, r"\b(possible|not possible|impossible|could|combinations)\b")
            and has(b, r"\b(only|no more than|at most|must)\b")
            and has(b, r"\b(after|before|events|scores?|points|constraints)\b")
            and quantitative
            and not argument
        ),
        "backward_schedule": float(
            has(s, r"\b(latest|earliest|leave|arrive|miss out)\b")
            and has(b, r"\b(time|minutes?|hours?|bus|train|activities)\b")
            and not argument
        ),
        "spatial_process": float(
            spatial
            and (
                steps
                or has(
                    b, r"\b(increase|decrease|rotate|turn|moves?|travels?|journey)\b"
                )
            )
            and not argument
        ),
        "method_equivalence": float(equivalence and not analogy and not principle),
        "spatial_equivalence": float(spatial_equivalence),
        "relational_equivalence": float(relational_equivalence),
        "representation_correspondence": float(representation_correspondence),
        "target_profile_selection": float(target_profile),
        "roster_constraints": float(roster),
        "discrete_unit_procedure": float(discrete),
        "enclosure_composition": float(enclosure),
        "unit_basis_conversion": float(unit_conversion),
        "flow_balance_constraints": float(
            transfer_process
            and (quantitative or len(re.findall(r"\b\d+\b", b)) >= 2)
            and not argument
            and choice_request
            and has(s, r"\b(could|cannot|can not|possible|must)\b")
        ),
        "data_inventory": float(dataset),
        "explicit_stages": float(steps and quantitative and not argument),
        "resource_optimization": float(
            has(s, r"\b(least|cheapest|minimum|maximum)\b")
            and has(b, r"\b(tickets?|pieces?|lengths?|workers?|packs?|cost|prices?)\b")
            and arithmetic_steps >= 2
            and not argument
        ),
        "filtered_comparison": float(
            dataset
            and not argument
            and (
                long_options
                or has(
                    s,
                    r"\b(more than|less than|above|below|larger|greater|fall|increas\w*|highest|lowest|rank)\b",
                )
            )
        ),
        "route_selection": float(
            has(b, r"\btimetable\b")
            and has(b, r"\b(station|stopping|routes?)\b")
            and has(s, r"\b(latest|earliest|leave|arrive)\b")
            and not argument
        ),
        "information_sufficiency": float(
            has(s, r"\binformation\b")
            and has(s, r"\b(sufficient|necessary|need|required)\b")
            and quantitative
            and not argument
        ),
        "percentage_basis_selection": float(
            quantitative
            and has(
                s, r"\b(reflects?|represents?|expresses?|denominator|reference|basis)\b"
            )
            and sum(has(t, r"\bpercentage of\b") for t in option_text) >= 3
            and has(b, r"\b(percent|percentage|%)")
        ),
        "construction_witness": float(
            quantitative
            and not argument
            and has(e, r"\b(combinations?|make up|allocate|distribute)\b")
            and has(
                e,
                r"\b(calculate|construct|systematic\w*|process|figure out|cost|minimum)\b",
            )
            and has(b, r"\b(stamps?|coins?|tickets?|pieces?|packets?|resources?)\b")
        ),
        "derived_cost_comparison": float(
            quantitative
            and dataset
            and not argument
            and has(
                s, r"\b(difference|most expensive|least expensive|highest|lowest)\b"
            )
            and has(
                b, r"\b(total floor|land area|construction price|per square metre)\b"
            )
        ),
    }
    for key in PROCEDURAL_CONTEXTS:
        f[key] = float(semantic.get(key, False))
    f["scenario_tariff_selection"] = float(
        semantic.get("scenario_tariff_selection", False)
    )
    return f


def tokens(text):
    stop = {
        "which",
        "one",
        "of",
        "the",
        "following",
        "above",
        "below",
        "is",
        "are",
        "a",
        "an",
        "in",
        "to",
        "for",
        "that",
        "this",
        "it",
        "be",
        "as",
        "with",
        "from",
        "by",
        "and",
        "or",
        "would",
        "could",
        "most",
        "best",
        "what",
        "how",
        "does",
        "do",
        "can",
        "not",
    }
    words = [w for w in re.findall(r"[a-z]+", text.lower()) if w not in stop]
    return words + [a + "_" + b for a, b in pairwise(words)]


def cosine(a, b):
    denom = math.sqrt(sum(v * v for v in a.values()) * sum(v * v for v in b.values()))
    return sum(v * b.get(k, 0) for k, v in a.items()) / denom if denom else 0


class Model:
    def __init__(self, examples, patterns, categories=None, families=None):
        self.examples = examples
        self.patterns = {p["id"]: p for p in patterns}
        self.families = semantic_families() if families is None else families
        self.categories = {
            c["name"]: c
            for c in (categories if categories is not None else category_metadata())
        }
        documents = [set(tokens(e["view"]["stem"])) for e in examples]
        df = Counter(token for doc in documents for token in doc)
        self.idf = {
            t: math.log((len(examples) + 1) / (n + 1)) + 1 for t, n in df.items()
        }
        self.vectors = [
            (
                e,
                features(e["view"], families=self.families),
                self.vector(e["view"]["stem"]),
            )
            for e in examples
        ]

    def vector(self, text):
        return {
            t: (1 + math.log(n)) * self.idf[t]
            for t, n in Counter(tokens(text)).items()
            if t in self.idf
        }

    def candidates(self, v, *, leave_out=None):
        f, stem = features(v, families=self.families), self.vector(v["stem"])
        # Per-source roles have equal scale; number of words/images cannot
        # swamp the requested operation. No identity enters the model.
        intent_keys = {
            "existing_claim",
            "new_inference",
            "needed_premise",
            "evidence_change",
            "reasoning_defect",
            "analogy_task",
            "principle_application",
            "method_equivalence",
            "spatial_equivalence",
            "relational_equivalence",
            *REFINED_OPERATIONS,
        }
        scores = {}
        for e, ef, es in self.vectors:
            if leave_out and e["example_id"] == leave_out:
                continue
            # Give requested cognitive operations more weight than topic/setup.
            left = {k: value * (3 if k in intent_keys else 1) for k, value in f.items()}
            right = {
                k: value * (3 if k in intent_keys else 1) for k, value in ef.items()
            }
            score = 0.78 * cosine(left, right) + 0.22 * cosine(stem, es)
            for pattern in e["patterns"]:
                scores.setdefault(pattern, []).append(
                    {
                        "score": round(score, 5),
                        "example_id": e["example_id"],
                        "review_rationale": e["rationale"],
                    }
                )
        ranked = []
        for pid, neighbors in scores.items():
            neighbors.sort(key=lambda r: (-r["score"], r["example_id"]))
            ranked.append(
                {
                    "pattern": pid,
                    "category": self.patterns[pid]["category"],
                    "subcategory": self.patterns[pid]["subcategory"],
                    "cognitive_task": self.patterns[pid]["cognitive_task"],
                    "score": neighbors[0]["score"],
                    "neighbors": neighbors[:2],
                }
            )
        return sorted(ranked, key=lambda row: (-row["score"], row["pattern"]))


def attribute(record, model, *, leave_out=None):
    v = view(record)
    f = features(v, families=model.families)
    ranked = model.candidates(v, leave_out=leave_out)
    result = {
        "category": None,
        "subcategories": [],
        "status": "unclassified",
        "patterns": [],
        "candidates": ranked[:5],
        "evidence": [],
        "rationale": "",
        "confidence": {"level": "unresolved", "calibrated_probability": False},
        "issues": [],
    }

    def issue(code, reason):
        result["issues"].append(
            {"code": code, "reason": reason, "manual_review_required": True}
        )

    q = record.get("question") or {}
    eligible = {
        name
        for name, c in model.categories.items()
        if set(v["modalities"]) <= set(c["modalities"])
    }
    eligible_ranked = [r for r in ranked if r["category"] in eligible]
    if record.get("status") != "matched":
        issue(
            "upstream_match_unresolved",
            "Matching is not successful; no categorization approved.",
        )
    if not v["stem"].strip() or not v["body"].strip() or len(v["options"]) < 2:
        issue(
            "insufficient_question_data",
            "Readable question prompt/body/options are missing or incomplete.",
        )
    if any(
        not (o.get("text") or "").strip() and not o.get("images") for o in v["options"]
    ):
        issue(
            "insufficient_question_data",
            "At least one option has neither usable text nor a saved visual.",
        )
    if any(
        i["code"]
        in {
            "ambiguous_body_question_split",
            "option_content_unavailable",
            "option_labels_unresolved",
            "encoding_artifact_unresolved",
        }
        for i in q.get("cleaning_issues", [])
    ):
        issue(
            "upstream_structure_unresolved",
            "Concrete cleaning ambiguity affects the evidence needed for categorization.",
        )
    if result["issues"]:
        result["status"] = "needs_review"
        return result
    argument_operations = [
        k
        for k in (
            "existing_claim",
            "new_inference",
            "needed_premise",
            "evidence_change",
            "reasoning_defect",
            "analogy_task",
            "principle_application",
        )
        if f[k]
    ]
    ct = [
        r
        for r in eligible_ranked
        if model.categories[r["category"]]["engine"] == "argument"
    ]
    ps = [
        r
        for r in eligible_ranked
        if model.categories[r["category"]]["engine"] == "problem_solving"
    ]
    if ct and f["argument_context"] and argument_operations:
        result["category"] = ct[0]["category"]
        # An analogous flaw is a mapping task, not a competing diagnosis task.
        if f["analogy_task"]:
            f["reasoning_defect"] = 0
        viable = [
            r
            for r in ct
            if any(
                f.get(k)
                for k in model.patterns[r["pattern"]]["positive_indicators"]
                if k != "argument_context" and k != "conditional_options"
            )
            and not any(
                f.get(k) for k in model.patterns[r["pattern"]]["counter_indicators"]
            )
        ]
        if (
            viable
            and viable[0]["score"] >= 0.70
            and (len(viable) == 1 or viable[0]["score"] - viable[1]["score"] >= 0.12)
        ):
            selected = [viable[0]]
        else:
            selected = []
            result["status"] = "ambiguous"
            issue(
                "competing_critical_thinking_patterns",
                "Requested argument operation has competing or weak learned pattern support.",
            )
    elif ps and (
        "visual" in v["modalities"]
        or (
            not f["argument_context"]
            and any(
                f[k]
                for k in (
                    "quantitative_context",
                    "spatial_filter",
                    "spatial_process",
                    "method_equivalence",
                    "spatial_equivalence",
                    "relational_equivalence",
                    "numerical_options",
                    *PROCEDURAL_CONTEXTS,
                    *REFINED_OPERATIONS,
                )
            )
        )
    ):
        result["category"] = ps[0]["category"]
        # A table is setup, not proof that selecting irrelevant information is
        # material. Multiple independent checks must support each PS label.
        material_selection = (
            (f["spatial_filter"] and not f["spatial_equivalence"])
            or f["filtered_comparison"]
            or f["route_selection"]
            or f["information_sufficiency"]
            or f["percentage_basis_selection"]
            or f["scenario_tariff_selection"]
            or f["target_profile_selection"]
            or (
                f["relevance_witness"]
                and (f["data_inventory"] or f["quantitative_context"])
            )
        )
        material_procedure = (
            f["rule_process"]
            or f["constraint_construction"]
            or f["backward_schedule"]
            or (f["spatial_process"] and not f["spatial_equivalence"])
            or f["dependent_calculation"]
            or f["explicit_stages"]
            or f["construction_witness"]
            or any(f[k] for k in PROCEDURAL_CONTEXTS)
            or any(f[k] for k in REFINED_PROCEDURES)
        )
        if f["information_sufficiency"]:
            # Explanatory algebra can justify an information-sufficiency choice;
            # it does not turn a request for data into a requested computation.
            material_procedure = False
        support = {
            "ps_select": material_selection,
            "ps_procedure": material_procedure,
            "ps_similarity": (f["method_equivalence"] and f["quantitative_context"])
            or f["spatial_equivalence"]
            or f["relational_equivalence"],
            # Refined representation tasks prepare a specified statistic, then
            # recognise its encoding; they do not merely compare magnitudes.
        }
        support["ps_similarity"] = (
            support["ps_similarity"] or f["representation_correspondence"]
        )
        if f["representation_correspondence"]:
            support["ps_select"] = False
            if not f["unit_basis_conversion"]:
                support["ps_procedure"] = False
        if any(
            f[k]
            for k in (
                "roster_constraints",
                "discrete_unit_procedure",
                "enclosure_composition",
            )
        ):
            support["ps_select"] = False
        if f["target_profile_selection"]:
            support["ps_similarity"] = False
            support["ps_procedure"] = False
        if f["method_equivalence"]:
            support["ps_procedure"] = support["ps_select"] = False
        independent_domain_evidence = any(
            f[k]
            for k in (
                "quantitative_context",
                "spatial_filter",
                "spatial_process",
                "method_equivalence",
                "spatial_equivalence",
                "relational_equivalence",
                "numerical_options",
                *PROCEDURAL_CONTEXTS,
                *REFINED_OPERATIONS,
            )
        )
        selected = [
            r
            for r in ps
            if independent_domain_evidence
            and support.get(r["pattern"])
            and r["score"] >= 0.70
        ]
        # Independent calculations inside a data-filter explanation do not
        # establish a dependent procedure. Prefer review over a false dual label.
        if (
            len(selected) > 1
            and not support["ps_similarity"]
            and not (
                f["backward_schedule"]
                or f["rule_process"]
                or f["explicit_stages"]
                or f["resource_optimization"]
                or f["construction_witness"]
            )
        ):
            selected = [r for r in selected if r["pattern"] != "ps_procedure"]
        independent_procedure = any(
            f[k]
            for k in (
                "rule_process",
                "constraint_construction",
                "backward_schedule",
                "spatial_process",
                "explicit_stages",
                "resource_optimization",
                "construction_witness",
                *PROCEDURAL_CONTEXTS,
            )
        )
        if (
            not support["ps_similarity"]
            and material_selection
            and material_procedure
            and independent_procedure
            and len(selected) == 1
        ):
            selected = []
            result["status"] = "needs_review"
            issue(
                "potential_multi_label_unresolved",
                "Both material selection and a non-trivial procedure have evidence, but learned support does not justify the complete multi-label result; no single label is forced.",
            )
        if (f["construction_witness"] or f["derived_cost_comparison"]) and not any(
            r["pattern"] == "ps_procedure" for r in selected
        ):
            selected = []
            result["status"] = "needs_review"
            issue(
                "procedure_support_incomplete",
                "Filtering alone would omit a required construction/derived-cost procedure; model or readable visual evidence does not establish the complete skill attribution.",
            )
        if not selected:
            result["status"] = "needs_review"
            issue(
                "problem_solving_skill_unresolved",
                "Numerical/spatial task is clear, but material selection versus procedure/equivalence is not sufficiently evidenced.",
            )
    else:
        # Future profile-driven families can use the same attribution/QA schema
        # without pretending their semantics are either an argument or a procedure.
        selected = [
            r
            for r in eligible_ranked
            if model.categories[r["category"]]["engine"] == "profile"
            and r["score"] >= 0.70
            and all(
                f.get(k) for k in model.patterns[r["pattern"]]["positive_indicators"]
            )
            and not any(
                f.get(k) for k in model.patterns[r["pattern"]]["counter_indicators"]
            )
        ]
        if selected and len({r["category"] for r in selected}) == 1:
            result["category"] = selected[0]["category"]
        else:
            selected = []
            issue(
                "top_level_pattern_uncovered",
                "No corroborated cognitive-task profile; candidate similarities alone do not justify a label.",
            )
    if selected:
        result["patterns"] = [r["pattern"] for r in selected]
        result["subcategories"] = list(
            dict.fromkeys(model.patterns[r["pattern"]]["subcategory"] for r in selected)
        )
        result["status"] = (
            "multi_label" if len(result["subcategories"]) > 1 else "classified"
        )
        result["rationale"] = " ".join(
            model.patterns[r["pattern"]]["description"] for r in selected
        )
        refined = [k for k in REFINED_OPERATIONS if f[k]]
        if refined:
            result["rationale"] = " ".join(REFINEMENT_RATIONALES[k] for k in refined)
        result["confidence"] = {
            "level": "supported",
            "support_score": min(r["score"] for r in selected),
            "calibrated_probability": False,
            "human_approved": False,
        }
    result["evidence"] = [
        {"field": "main_question", "quote": v["stem"]},
        {"field": "task_profile", "indicators": [k for k, value in f.items() if value]},
        {
            "field": "semantic_pattern_evidence",
            "families": [
                {
                    k: p[k]
                    for k in (
                        "feature",
                        "semantic_intent",
                        "requires_all",
                        "counter_evidence",
                        "modality",
                        "confidence_contribution",
                    )
                }
                for p in model.families
                if f.get(p["feature"])
            ],
        },
        {
            "field": "modality_eligibility",
            "modalities": v["modalities"],
            "eligible_categories": sorted(eligible),
        },
        {
            "field": "explanation",
            "used_as": "secondary_evidence_only",
            "available": bool(v["explanation"]),
            "excerpt": v["explanation"][:280],
        },
    ]
    return result
