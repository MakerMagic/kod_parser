"""Read-only BMAT acquisition/RAW/HTML audit and explicit determinism probes."""

import argparse
import base64
import json
import re
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

import pdfplumber

from categorization.backtest import load_categorized
from parsers.bmat import parse_pdf, validate_raw
from parsers.bmat.backtest import files, load, status
from processors.bmat.contracts import eligible_records

ROOT = Path(__file__).resolve().parents[1]


class HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            src = dict(attrs)["src"]
            assert src.startswith("data:image/png;base64,")
            assert base64.b64decode(src.split(",", 1)[1], validate=True).startswith(
                b"\x89PNG"
            )
            self.images += 1

    def handle_data(self, data):
        self.text.append(data)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--determinism", action="store_true")
    cli.add_argument("--test-report",nargs="+",type=Path,default=[ROOT/"inspections_bmat/regressions.xml"])
    args = cli.parse_args()
    manifest_path = ROOT / "data/input/bmat/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [r["year"] for r in manifest["files"]] == list(range(2003, 2022))
    source_hashes = {}
    for row in manifest["files"]:
        assert row["status"] in {"downloaded", "already_downloaded"}
        assert re.search(r"/Section(?:-|%20| )1/", row["source_url"], re.IGNORECASE), (
            row["source_url"]
        )
        assert sha256(Path(row["local_path"]).read_bytes()).hexdigest() == row["sha256"]
        source_hashes[row["year"]] = row["sha256"]
    paths = files([ROOT / "data/raw/bmat"])
    assert len(paths) == 19
    totals, tags, issues, ready, html_count, pages_count = (
        Counter(),
        Counter(),
        set(),
        0,
        0,
        0,
    )
    determinism = []
    for path in paths:
        data = load(path)
        validate_raw(data)
        assert data["input"]["sha256"] == source_hashes[data["year"]]
        assert not data["warnings"], (data["year"], data["warnings"])
        expected = data["extraction"]["expected_questions"]
        assert [q["question_number"] for q in data["questions"]] == list(
            range(1, expected + 1)
        )
        with pdfplumber.open(data["input"]["path"]) as doc:
            assert len(doc.pages) == len(data["pages"])
            for p, stored in zip(doc.pages, data["pages"]):
                assert (p.extract_text(layout=False) or "") == stored["raw_text"]
                pages_count += 1
                p.close()
        expected_ready = set()
        for q in data["questions"]:
            state, findings = status(data, q, path)
            assert [i["reason"] for i in q["parsing_issues"]] == findings
            assert (
                q["pipeline_status"]
                == {
                    "skipped": "intentional_skip",
                    "retained": "raw_ready",
                    "parser_review": "parser_review",
                }[state]
            )
            if state == "retained":
                expected_ready.add(q["question_id"])
            totals[state] += 1
            if findings:
                issues.add(q["question_id"])
            current_tags = [t["type"] for t in q["bmat_filter"]["types"]]
            assert len(current_tags) == len(set(current_tags))
            tags.update(current_tags)
            assets = {a["image_id"]: a for a in q["visual_assets"]}
            for a in [
                *q["visual_assets"],
                *q["visual_previews"],
                *q["raw"].get("visual_candidates", []),
            ]:
                if a.get("path"):
                    assert a["path"].startswith("assets/") and "bmat_" in a["path"]
                    assert (
                        sha256((path.parent / a["path"]).read_bytes()).hexdigest()
                        == a["sha256"]
                    )
            owned = set()
            for o in q["options"]:
                for a in o["images"]:
                    assert a["image_id"] in assets
                    assert (
                        a["option_label"] == o["label"] and a["belongs_to"] == "option"
                    )
                    assert a["image_id"] not in owned
                    owned.add(a["image_id"])
            assert not any(
                a["belongs_to"] == "question" and a["image_id"] in owned
                for a in q["visual_assets"]
            )
            html = (
                ROOT
                / f"inspections_bmat/{data['year']}_q{q['question_number']:03}.html"
            )
            parser = HTML()
            content = html.read_text(encoding="utf-8")
            parser.feed(content)
            visible = " ".join(" ".join(parser.text).split())
            assert "Raw Main Body" in visible and "Original source preview" in visible
            assert (
                state in visible
                and " ".join(q["raw"]["question_block"].split()) in visible
            )
            for t in current_tags:
                assert t in visible
            for o in q["options"]:
                if o["text"].strip():
                    assert " ".join(o["text"].split()) in visible
            assert parser.images >= len(q["visual_previews"])
            html_count += 1
        assert {q["question_id"] for q in eligible_records(data)} == expected_ready
        ready += len(expected_ready)
        for declared in data["shared_information_ranges"]:
            expected_ids = {
                q["question_id"]
                for q in data["questions"]
                if declared["start_question"]
                <= q["question_number"]
                <= declared["end_question"]
            }
            assert set(declared["affected_question_ids"]) == expected_ids
            assert len(declared["affected_question_ids"]) == len(expected_ids)
        if args.determinism and data["year"] in {2003, 2013, 2020}:
            repeated = parse_pdf(
                data["input"]["path"],
                asset_dir=ROOT / "inspections_bmat/determinism/assets",
                overwrite_assets=True,
            )
            assert repeated == data, data["year"]
            determinism.append(data["year"])
    assert sum(totals.values()) == html_count == 664
    qa = json.loads((ROOT / "inspections_bmat/status.json").read_text(encoding="utf-8"))
    assert qa["summary"]["questions"] == 664
    assert qa["summary"]["retained_without_parsing_issues"] == ready
    assert qa["summary"]["unique_parsing_issue_questions"] == len(issues)
    assert len(qa["records"]) == len({r["question_id"] for r in qa["records"]}) == 664
    links_checked = 0
    for document in [
        ROOT / "docs/BMAT_RAW_BACKTEST.md",
        ROOT / "docs/BMAT_RAW_ISSUES.md",
    ]:
        markdown = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown):
            if not target.startswith(("https:", "http:", "#")):
                assert (
                    (document.parent / target.strip("<>").split("#")[0])
                    .resolve()
                    .exists()
                ), target
                links_checked += 1
        if document.name == "BMAT_RAW_ISSUES.md":
            for section in re.split(r"\n### ", markdown)[1:]:
                match = re.match(r"(.+) \((\d+) unique questions\)", section)
                assert match
                rows = re.findall(r"^\| (\d{4}) \| \[(\d+)\]", section, re.MULTILINE)
                assert len(rows) == len(set(rows)) == int(match[2]), match[1]
    # Current TSA hash-locked handoff verifies all original question, raw/clean,
    # answer/explanation and image references without running any TSA stage.
    tsa = load_categorized(ROOT / "data/categorized/blackstone/tsa.categorized.json")
    assert len(tsa["records"]) == 750
    suites = [suite for path in args.test_report for suite in ElementTree.parse(path).getroot().findall("testsuite")]
    assert all(
        s.get("failures") == s.get("errors") == s.get("skipped") == "0" for s in suites
    )
    result = {
        "stage": "bmat_raw_validation",
        "source_pdfs_verified": 19,
        "raw_pages_preserved": pages_count,
        "questions_verified": 664,
        "html_verified": html_count,
        "status_counts": dict(totals),
        "skip_types_overlapping": dict(tags),
        "parsing_issue_questions": len(issues),
        "eligible_downstream": ready,
        "determinism_years": determinism,
        "tsa_hash_locked_records_unchanged": 750,
        "tests_passed": sum(int(s.get("tests", 0)) for s in suites),
        "test_reports": [str(p) for p in args.test_report],
        "local_report_links_checked": links_checked,
    }
    (ROOT / "inspections_bmat/validation.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
