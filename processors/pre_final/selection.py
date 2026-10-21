"""Select admitted pre-final records, not upstream eligibility or question quality."""

import json
import random
from pathlib import Path

CATEGORY_IDS = set(
    json.loads(Path(__file__).with_name("schema.json").read_text(encoding="utf-8"))[
        "$defs"
    ]["question"]["properties"]["category"]["enum"]
)


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        data.get("stage") != "pre_final"
        or data.get("schema_version") != "1"
        or not isinstance(data.get("questions"), list)
        or not isinstance(data.get("categories"), dict)
    ):
        raise ValueError("Rendering requires unified pre-final JSON v1")
    return data


def category_id(categories, value):
    if value is None:
        return None
    if value in CATEGORY_IDS and value in categories:
        return value
    matches = [
        key
        for key, item in categories.items()
        if key in CATEGORY_IDS and item["name"] == value
    ]
    if len(matches) != 1:
        raise ValueError("Use a canonical category ID or exact subcategory name")
    return matches[0]


def assert_renderable(question, categories):
    """Selected record only: field/structure support, never answer/category reasoning."""
    identifier = question.get("id", "<missing ID>")
    try:
        for field in ("id", "source", "main_question"):
            if not isinstance(question[field], str):
                raise TypeError(field + " must be text")
        if question["source"] not in ("TSA", "BMAT"):
            raise ValueError("source must be TSA/BMAT")
        if (
            question["category"] not in CATEGORY_IDS
            or question["category"] not in categories
        ):
            raise ValueError("category must be one canonical TSA category")
        definition = categories[question["category"]]
        if not isinstance(definition["name"], str) or not isinstance(
            definition["family"], str
        ):
            raise TypeError("category display metadata must be text")
        if type(question["explanation_by_ai"]) is not bool:
            raise ValueError("explanation_by_ai must be boolean")
        for field in (
            "year",
            "question_number",
            "correct_answer",
            "explanation",
            "provenance",
        ):
            if field not in question:
                raise ValueError("missing " + field)
        for field in ("main_body", "main_answers", "assets"):
            if not isinstance(question[field], list):
                raise TypeError(field + " must be an array")
        for block in question["main_body"]:
            if block["type"] not in {"text", "visual"}:
                raise ValueError("unsupported main_body block " + block["type"])
            if not isinstance(
                block["text" if block["type"] == "text" else "asset_id"], str
            ):
                raise TypeError("main_body text/asset_id must be text")
        for answer in question["main_answers"]:
            if (
                not isinstance(answer["text"], str)
                or not isinstance(answer["label"], str)
                or not isinstance(answer["asset_ids"], list)
            ):
                raise TypeError("main_answers requires label/text/asset_ids")
        for block in (question["explanation"] or {}).get("blocks", []):
            if block["type"] not in {"paragraph", "list", "visual"}:
                raise ValueError("unsupported explanation block " + block["type"])
            if block["type"] == "paragraph" and not isinstance(block["text"], str):
                raise TypeError("explanation paragraph must be text")
            if block["type"] == "visual" and not isinstance(block["asset_id"], str):
                raise TypeError("explanation visual requires asset_id")
            if block["type"] == "list" and not all(
                isinstance(i["text"], str) for i in block["items"]
            ):
                raise TypeError("explanation list items must be text")
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Cannot render {identifier}: {error}") from error


def select_many(
    data,
    *,
    identifier=None,
    source=None,
    year=None,
    question=None,
    category=None,
    sample=None,
    seed=0,
):
    if sample is not None and (type(sample) is not int or sample <= 0):
        raise ValueError("--sample must be a positive integer")
    if (
        sample is None
        and identifier is None
        and (source is None or year is None or question is None)
    ):
        raise ValueError(
            "Select an exact ID, source/year/question or an explicit --sample"
        )
    category = category_id(data["categories"], category)
    rows = [
        q
        for q in data["questions"]
        if (
            (identifier is None or q.get("id") == identifier)
            and (source is None or q.get("source") == source)
            and (year is None or q.get("year") == year)
            and (question is None or q.get("question_number") == question)
            and (category is None or q.get("category") == category)
        )
    ]
    if not rows:
        raise ValueError("No pre-final questions match the requested selectors")
    if sample is None:
        if len(rows) != 1:
            raise ValueError(
                "No unique pre-final question; refine identity or use --sample"
            )
    else:
        rows = random.Random(seed).sample(
            sorted(rows, key=lambda q: q["id"]), min(sample, len(rows))
        )
    for row in rows:
        assert_renderable(row, data["categories"])
    return rows


def select(data, **selectors):
    return select_many(data, **selectors)[0]
