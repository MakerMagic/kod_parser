"""Future stages consume only validated, non-excluded BMAT structured records."""

STAGES = {
    "acquire": {"module": "acquisition.bmat", "output": "data/input/bmat"},
    "raw": {"module": "parsers.bmat", "output": "data/raw/bmat"},
    "clean": {"module": None, "input": "data/raw/bmat", "output": "data/clean/bmat"},
    "match": {"module": None, "input": "data/clean/bmat", "output": "data/merged/bmat"},
    "categorize": {
        "module": None,
        "input": "data/merged/bmat",
        "output": "data/categorized/bmat",
    },
}


def eligible_records(dataset):
    from parsers.bmat.parser import validate_raw

    validate_raw(dataset)
    if dataset["warnings"]:
        return []
    return [
        q
        for q in dataset["questions"]
        if not q["bmat_filter"]["skip_from_pipeline"]
        and not q["parsing_issues"]
        and q["pipeline_status"] == "raw_ready"
    ]
