"""Cleaning-only prompt/paragraph regressions; no PDF extraction or acquisition."""

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from processors.normalization.blackstone import clean_dataset, validate_clean
from processors.normalization.blackstone.backtest import (
    inspect_question,
    render_inspection,
)
from processors.normalization.blackstone.storage import load_clean, write_clean
from processors.normalization.blackstone.text import normalize_text


def case(tmp_path, text, option_text="First answer"):
    raw = {
        "question_id": "example",
        "question_number": 1,
        "question_text": text,
        "source_question_key": {"source": "blackstone", "year": 2030},
        "options": [
            {"label": "A", "text": option_text, "images": []},
            {"label": "B", "text": "Second answer", "images": []},
        ],
        "subpoints": [],
        "images": [],
        "visual_assets": [],
        "visual_previews": [],
        "page_reference": {"start_page": 1, "end_page": 1},
        "warnings": ["raw_uncertainty_retained"],
        "raw": {
            "question_block": text + "\nA First answer\nB Second answer",
            "options_block": "A First answer\nB Second answer",
        },
    }
    dataset = {"questions": [raw], "year": 2030, "input": {"filename": "example.pdf"}}
    path = tmp_path / "source.raw.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    before = path.read_bytes()
    original = deepcopy(dataset)
    result = clean_dataset(dataset, path)
    validate_clean(result)
    assert dataset == original and path.read_bytes() == before
    q = result["questions"][0]
    assert q["raw_record"] == raw and q["raw_warnings"] == raw["warnings"]
    assert q["options"] == raw["options"]
    return q, result, path


@pytest.mark.parametrize(
    "text,prompt,body",
    [
        (
            "There are several possible routes.\nBy how much is route A shorter?",
            "By how much is route A shorter?",
            "There are several possible routes.",
        ),
        (
            "The table shows language choices.\nWhat percentage take French? (Give your answer to\nthe nearest 1% if necessary).",
            "What percentage take French? (Give your answer to the nearest 1% if necessary).",
            "The table shows language choices.",
        ),
        (
            "The diagram has five pieces.\nWhich pieces fit?\n(The pieces must stay face up.)",
            "Which pieces fit?\n(The pieces must stay face up.)",
            "The diagram has five pieces.",
        ),
        (
            "Four maps are possible. Which\nmap has an error?",
            "Which\nmap has an error?",
            "Four maps are possible.",
        ),
        (
            "A car travels along two roads.\nIf both drivers leave together,\nhow long will the journey take?",
            "If both drivers leave together, how long will the journey take?",
            "A car travels along two roads.",
        ),
        (
            "There are several possible results.\nIdentify the correct answer.",
            "Identify the correct answer.",
            "There are several possible results.",
        ),
        (
            "The objects have different widths.\nWhich option is the narrowest.",
            "Which option is the narrowest.",
            "The objects have different widths.",
        ),
    ],
)
def test_prompt_tail_forms_preserve_context_and_explanatory_notes(
    tmp_path, text, prompt, body
):
    q, _, _ = case(tmp_path, text)
    assert q["main_question"] == prompt
    assert "\n".join(b["text"] for b in q["main_body"] if b["type"] == "text") == body
    assert not any(
        i["code"] == "ambiguous_body_question_split" for i in q["cleaning_issues"]
    )


@pytest.mark.parametrize(
    "text",
    [
        "The people travelled home.\nAll passengers arrived safely.",
        "The passage is complete.\nWhat I need is a calculator.",
        "The passage is complete.\nHow we travel is already decided.",
        "The passage ends with a conclusion.\nOn Monday, I asked which train would arrive first?",
        "Which object?\nWhat position?",
        "There are three answers.\nThe result must be between",
        "What percentage is correct??",
        "What percentage is correct? (An unfinished note",
        "Which option is correct? A separate concluding passage follows.",
    ],
)
def test_conclusions_and_ambiguous_stems_are_not_promoted(tmp_path, text):
    q, _, _ = case(tmp_path, text)
    assert q["main_question"] is None
    assert any(
        i["code"] == "ambiguous_body_question_split" for i in q["cleaning_issues"]
    )
    assert re.sub(r"\s+", " ", "\n".join(b["text"] for b in q["main_body"])) == re.sub(
        r"\s+", " ", text
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "The campaign organisers' advertisement reflects:",
        "The above argument rests on the implicit assumption that:",
        "This result represents:",
    ],
)
def test_colon_answer_completions_are_prompts(tmp_path, prompt):
    from processors.normalization.blackstone.structure import build_structure

    q, _, _ = case(tmp_path, "The passage provides the context.\n" + prompt)
    raw = deepcopy(q["raw_record"])
    for o in raw["options"]:
        o["text"] = "the change expressed as a percentage of the earlier quantity."
    issues = []
    body, main, accounting = build_structure(raw, lambda *args: issues.append(args))
    assert main == prompt
    assert body[0]["text"] == "The passage provides the context."
    assert not issues
    assert any(a["destination"] == "main_question" for a in accounting)


@pytest.mark.parametrize(
    "lead",
    [
        "The cost of entry is as follows:",
        "The following table shows:",
        "The quoted data represents:",
        "The premises are:",
        "The argument is shown below:",
    ],
)
def test_colon_body_introductions_not_prompts(tmp_path, lead):
    from processors.normalization.blackstone.structure import build_structure

    q, _, _ = case(tmp_path, "Read the context.\n" + lead)
    raw = deepcopy(q["raw_record"])
    for o in raw["options"]:
        o["text"] = "the change expressed as a percentage of the earlier quantity."
    body, main, _ = build_structure(raw, lambda *args: None)
    assert main is None
    assert lead in body[0]["text"]


@pytest.mark.parametrize(
    "year,number,expected",
    [
        (2010, 32, "The campaign organisers' advertisement reflects:"),
        (2012, 16, "The above argument rests on the implicit assumption that:"),
        (
            2014,
            50,
            "Which one of the following pie charts shows the number of visitors in each age group that paid to enter the museum yesterday?",
        ),
    ],
)
def test_real_colon_structure_preserves_raw_and_options(year, number, expected):
    from processors.normalization.blackstone.structure import build_structure

    paths = list(Path("data/raw/blackstone").glob(f"TSA Oxford {year}-*.raw.json"))
    if not paths:
        pytest.skip("Local raw corpus absent")
    raw = json.loads(paths[0].read_text(encoding="utf-8"))["questions"][number - 1]
    before = deepcopy(raw)
    _, prompt, _ = build_structure(raw, lambda *args: None)
    assert prompt == expected
    assert raw == before


def test_colon_clause_before_a_body_visual_is_not_an_answer_prompt(tmp_path):
    from processors.normalization.blackstone.structure import (
        colon_prompt_span,
        text_lines,
    )

    q, _, _ = case(tmp_path, "The context is supplied.\nThe claim represents:")
    raw = deepcopy(q["raw_record"])
    for o in raw["options"]:
        o["text"] = "the change as a fraction of the original population."
    raw["layout_blocks"] = [
        {
            "block_id": f"b{i}",
            "order": i + 1,
            "type": "text",
            "component": "question_body",
            "text": line["text"],
            "raw_span": line["span"],
        }
        for i, line in enumerate(text_lines(raw["question_text"]))
    ]
    raw["layout_blocks"].append(
        {
            "block_id": "chart",
            "order": 3,
            "type": "visual",
            "component": "question_body",
        }
    )
    assert colon_prompt_span(raw) is None


@pytest.mark.parametrize(
    "verb", ["weaken", "strengthen", "undermine", "support", "challenge"]
)
def test_known_modal_joins_recovered_only_in_argument_prompt_context(tmp_path, verb):
    s = f"Which statement, if true, would{verb} the above argument?"
    q, _, _ = case(tmp_path, "The author makes a claim.\n" + s)
    assert q["main_question"] == s.replace("would" + verb, "would " + verb)
    assert q["question_text"].endswith(q["main_question"])
    assert q["raw_record"]["question_text"].endswith(s)
    assert any(
        "modal_impact_word_boundaries" in t["rules"] for t in q["transformations"]
    )


@pytest.mark.parametrize(
    "s",
    [
        "The shoulder is injured; the woodwind player could strengthen it.",
        "The label reads wouldweaken.",
        "Which would-be challenger supports the argument?",
        "Which policy would strengthen the above argument?",
        "Wouldstrengthen is a fictional label in this sentence.",
    ],
)
def test_modal_join_rule_does_not_split_legitimate_or_quoted_tokens(s):
    assert normalize_text(s, recover_modal_joins=True) == s


def test_auxiliary_negative_join_uses_same_closed_prompt_grammar(tmp_path):
    q, _, _ = case(
        tmp_path, "Two constraints are supplied.\nWhich of the statements isnot true?"
    )
    assert q["main_question"] == "Which of the statements is not true?"
    assert q["raw_record"]["question_text"].endswith("isnot true?")
    assert (
        normalize_text("The name isnot a word.", recover_modal_joins=True)
        == "The name isnot a word."
    )


def test_join_rule_upgrade_preserves_declared_legacy_clean_outputs(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    _, current, raw = case(
        raw_dir, "The context is available.\nWhich statement isnot true?"
    )
    legacy = deepcopy(current)
    legacy["cleaning"]["rules"].remove("auxiliary_negation_word_boundaries")
    legacy["questions"][0]["question_text"] = legacy["questions"][0][
        "question_text"
    ].replace("is not", "isnot")
    legacy["questions"][0]["main_question"] = legacy["questions"][0][
        "main_question"
    ].replace("is not", "isnot")
    target = tmp_path / "clean/version.clean.json"
    target.parent.mkdir()
    target.write_text(json.dumps(legacy), encoding="utf-8")
    assert load_clean(target) == legacy
    before = raw.read_bytes()
    write_clean(current, target, overwrite=True)
    assert load_clean(target)["questions"][0]["main_question"].endswith("is not true?")
    assert raw.read_bytes() == before


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "The charges are as follows:\nOrder value: less than £25 - £4.50\n£25 to £49 - £8.50",
            "The charges are as follows:\n\nOrder value: less than £25 - £4.50\n£25 to £49 - £8.50",
        ),
        (
            "Points are awarded as follows:\nfirst place 7 points\nsecond place 5 points\nthird place 3 points",
            "Points are awarded as follows:\n\nfirst place 7 points\nsecond place 5 points\nthird place 3 points",
        ),
        (
            "The readings are shown below.\nGas Electricity\nOctober 2842 5368\nNovember 3029 5874",
            "The readings are shown below.\n\nGas Electricity\nOctober 2842 5368\nNovember 3029 5874",
        ),
        (
            "Below is part of a flight itinerary with\na change of flight and a wait. All times are local\ntimes.\nDEPART LONDON 22:30 30.01.04\nDEPART DUBAI 14:30 31.01.04",
            "Below is part of a flight itinerary with a change of flight and a wait. All times are local times.\n\nDEPART LONDON 22:30 30.01.04\nDEPART DUBAI 14:30 31.01.04",
        ),
        (
            "The rules are as follows:\n1. Keep the paper flat\n2. Do not turn it over",
            "The rules are as follows:\n\n1. Keep the paper flat\n2. Do not turn it over",
        ),
        (
            "The readings are shown below.\n\nGas Electricity\nOctober 2842 5368\nNovember 3029 5874",
            "The readings are shown below.\n\nGas Electricity\nOctober 2842 5368\nNovember 3029 5874",
        ),
        (
            "The message is clear:\nplease continue walking\ntowards the station.",
            "The message is clear:\nplease continue walking\ntowards the station.",
        ),
        (
            "The claim is as follows:\nThe result is not fixed.\nWe have 10 seats.\nWe have 20 chairs.",
            "The claim is as follows:\nThe result is not fixed.\nWe have 10 seats.\nWe have 20 chairs.",
        ),
    ],
)
def test_introduced_data_blocks_not_colon_only(text, expected):
    result = normalize_text(text, separate_blocks=True)
    assert result == expected
    assert normalize_text(result, separate_blocks=True) == result


def test_partial_raw_line_has_exact_nonoverlapping_accounting(tmp_path):
    text = "Four maps are possible. Which\nmap has an error?"
    q, _, _ = case(tmp_path, text)
    parts = [a for a in q["content_accounting"] if a["line_index"] == 0]
    assert [p["destination"] for p in parts] == ["main_body", "main_question"]
    assert parts[0]["structured_span"]["end"] == parts[1]["structured_span"]["start"]
    assert (
        "".join(
            text[p["structured_span"]["start"] : p["structured_span"]["end"]]
            for p in parts
        )
        == text.splitlines()[0]
    )


def test_new_body_spacing_does_not_change_multiline_answer_rules(tmp_path):
    option = "The rates are as follows:\n£1 - £2\n£3 - £4"
    q, _, _ = case(tmp_path, "Which schedule is correct?", option)
    assert q["options"][0]["text"] == option
    assert normalize_text(option) == option


def test_existing_clean_output_upgrades_with_declared_rules_and_raw_immutability(
    tmp_path,
):
    directory = tmp_path / "raw"
    directory.mkdir()
    text = "Below is part of a flight itinerary with\na change of flight and a wait. All times are local\ntimes.\nDEPART LONDON 22:30 30.01.04\nDEPART DUBAI 14:30 31.01.04\nWhat is the total time?"
    _, dataset, raw = case(directory, text)
    previous = deepcopy(dataset)
    previous["cleaning"]["rules"].remove("wrapped_structured_introductions")
    previous["questions"][0]["question_text"] = normalize_text(
        text, separate_blocks=True, wrapped_lead_ins=False
    )
    output = tmp_path / "clean/example.clean.json"
    output.parent.mkdir()
    output.write_text(json.dumps(previous), encoding="utf-8")
    assert load_clean(output) == previous
    before = raw.read_bytes()
    write_clean(dataset, output, overwrite=True)
    assert "times.\n\nDEPART" in load_clean(output)["questions"][0]["question_text"]
    assert raw.read_bytes() == before


# Every newly resolved member of the original 75-row Body / Prompt category.
FIXED = {
    2008: [20, 34, 43, 44, 49],
    2009: [20, 32, 44, 48],
    2010: [6, 19, 24, 25, 48],
    2011: [12, 18, 24, 37, 43, 44],
    2012: [8, 18, 19, 26, 43],
    2013: [6, 8, 20, 30, 42, 50],
    2014: [36, 38, 43, 44],
    2015: [13, 48, 50],
    2016: [31, 38],
    2017: [2, 14, 26, 44, 49],
    2018: [7, 8, 36, 38, 48, 50],
    2019: [13, 18, 48],
    2020: [25, 37, 44],
    2021: [25, 50],
    None: [12, 19, 30],
    2022: [12, 24, 31],
}


@pytest.fixture(scope="module")
def corpus():
    root = Path(__file__).resolve().parents[1]
    paths = list((root / "data/raw/blackstone").glob("*.raw.json"))
    if len(paths) != 16:
        pytest.skip("Local raw corpus unavailable")
    return [
        (p, clean_dataset(json.loads(p.read_text(encoding="utf-8")), p)) for p in paths
    ]


def test_all_analogous_issue_group_members_and_existing_prompt_controls(corpus):
    resolved = []
    for path, dataset in corpus:
        year = dataset["document"].get("year")
        for q in dataset["questions"]:
            if q["question_number"] in FIXED.get(year, []):
                assert q["main_question"] and "?" in q["main_question"], (
                    year,
                    q["question_number"],
                )
                assert not any(
                    i["code"] == "ambiguous_body_question_split"
                    for i in q["cleaning_issues"]
                )
                resolved.append((year, q["question_number"]))
        baseline = (
            path.parents[3]
            / "inspections_clean/tail_structure_baseline_20261014"
            / path.name.replace(".raw.json", ".clean.json")
        )
        if baseline.exists():
            old = json.loads(baseline.read_text(encoding="utf-8"))
            if old["raw_reference"]["sha256"] != dataset["raw_reference"]["sha256"]:
                continue  # A baseline for a different raw revision is not a clean-only control.
            for a, b in zip(old["questions"], dataset["questions"]):
                if a["main_question"] is not None:
                    if (year, b["question_number"]) in {(2013, 12), (2016, 50)}:
                        assert b["main_question"].startswith(a["main_question"] + "\n(")
                    else:
                        assert a["main_question"] == b["main_question"]
                assert (
                    a["raw_record"] == b["raw_record"]
                    and a["visual_assets"] == b["visual_assets"]
                )
    assert len(resolved) == 65
    specimen = next(d for _, d in corpus if d["document"].get("year") is None)
    assert (
        specimen["questions"][18]["main_question"]
        == "During which month did I use the most gas?"
    )
    assert "Gas Electricity" in specimen["questions"][18]["question_text"]
    for number in [2, 7, 13, 18, 20]:
        assert specimen["questions"][number - 1]["main_question"] is None


def test_2011_targets_html_and_answer_format_are_read_only(corpus, tmp_path):
    raw, dataset = next((p, d) for p, d in corpus if d["document"].get("year") == 2011)
    path = write_clean(dataset, tmp_path / "2011.clean.json")
    raw_bytes, clean_bytes = raw.read_bytes(), path.read_bytes()
    for number in [37, 43]:
        result = inspect_question(
            [path], source="TSA Oxford 2011.pdf", year=2011, question_number=number
        )
        q = result["question"]
        html = render_inspection(result, "html")
        body = html.split("id='main-body'")[1].split("</section>")[0]
        prompt = html.split("id='main-question'")[1].split("</section>")[0]
        assert (
            q["main_question"]
            and q["main_question"] in prompt
            and q["main_question"] not in body
        )
        assert "data:image/png;base64," in html
        if number == 37:
            assert "as follows:\n\nOrder value:" in q["main_body"][0]["text"]
            assert "By how much" in q["main_question"]
        else:
            assert "nearest 1% if necessary)." in q["main_question"]
            assert any(b["type"] == "visual" for b in q["main_body"])
        assert render_inspection(result, "text") and json.loads(
            render_inspection(result, "json")
        )
    assert raw.read_bytes() == raw_bytes and path.read_bytes() == clean_bytes
