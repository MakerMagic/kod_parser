"""Read-only cross-layer regression audit; writes only its owned QA result."""

import base64
import re
from collections import defaultdict
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from categorization.backtest import load_categorized
from categorization.core import MARKER, digest, file_ref, read, verify_refs, write_json

FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[1]


class HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections, self.text, self.images = [], [], defaultdict(list)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section":
            self.sections.append(attrs.get("id"))
        if tag == "img" and self.sections:
            src = attrs.get("src", "")
            assert src.startswith("data:image/png;base64,")
            self.images[self.sections[-1]].append(
                sha256(
                    base64.b64decode(src.split(",", 1)[1], validate=True)
                ).hexdigest()
            )

    def handle_endtag(self, tag):
        if tag == "section":
            self.sections.pop()

    def handle_data(self, text):
        self.text.append(text)


def norm(value):
    return " ".join(value.split())


def main():
    data = load_categorized(ROOT / "data/categorized/blackstone/tsa.categorized.json")
    before = read(FOLDER / "before.categorized.json")
    previous = {r["record_key"]: r for r in before["records"]}
    assert set(previous) == {r["record_key"] for r in data["records"]}
    archive = read(FOLDER / "archive.json")
    verify_refs([e["archive"] for e in archive])
    page_count, question_count, old_assets, explanation_count = 0, 0, {}, 0
    raw_changes, restored_answers = [], []
    for entry in archive:
        source = Path(entry["original"]["path"])
        old, new = read(entry["archive"]["path"]), read(source)
        if source.name.endswith(".raw.json"):
            assert [p["raw_text"] for p in old["pages"]] == [
                p["raw_text"] for p in new["pages"]
            ]
            assert len(old["questions"]) == len(new["questions"]) == 50
            page_count += len(old["pages"])
            for a, b in zip(old["questions"], new["questions"], strict=True):
                for field in (
                    "question_id",
                    "source_question_key",
                    "question_number",
                    "page_reference",
                ):
                    assert a[field] == b[field]
                assert a["raw"]["question_block"] == b["raw"]["question_block"]
                question_count += 1
                if digest(a) != digest(b):
                    raw_changes.append([old["year"], a["question_number"]])
                for asset in [
                    *a.get("visual_assets", []),
                    *a.get("visual_previews", []),
                ]:
                    if asset.get("path") and asset.get("sha256"):
                        old_assets[str((source.parent / asset["path"]).resolve())] = (
                            asset["sha256"]
                        )
        elif source.name.endswith(".matched.json"):
            verify_refs(
                [r for r in old["inputs"] if r["kind"] == "answer_intermediate"]
            )
            for a, b in zip(old["records"], new["records"], strict=True):
                assert a["identity"] == b["identity"]
                assert a.get("final_explanation") == b.get("final_explanation")
                explanation_count += 1
                if a.get("correct_answer") != b.get("correct_answer"):
                    assert a.get("correct_answer") is None and a["status"] != "matched"
                    assert (
                        b["status"] == "matched"
                        and b["correct_answer"] == b["answer"]["correct_answer"]
                    )
                    restored_answers.append(b["identity"])
    assert question_count == explanation_count == 750
    verify_refs([{"path": p, "sha256": h} for p, h in old_assets.items()])
    html_checks = []
    for row in data["records"]:
        if not (row.get("rulebook_review") or row.get("previous_categorization")):
            continue
        y, n = row["identity"]["year"], row["identity"]["question_number"]
        path = ROOT / "inspections_categorization" / f"{y}_q{n:03}.html"
        parser = HTML()
        content = path.read_text(encoding="utf-8")
        parser.feed(content)
        text = norm(" ".join(parser.text))
        assert "inspection_reference_unavailable" not in content, (y, n)
        for heading in (
            "Main Body",
            "Main Question",
            "Main Answers",
            "Correct Answer",
            "Categorization",
        ):
            assert heading in text, (y, n, heading)
        assert "Final Explanation" in text or "Full Explanation" in text
        q = row["question_view"]
        if q.get("main_question"):
            assert norm(q["main_question"]) in text
        for b in (row.get("final_explanation") or {}).get("blocks", []):
            if b.get("text"):
                assert norm(b["text"]) in text
        assert norm(row["categorization"]["rationale"]) in text
        assets = {a["image_id"]: a for a in q.get("visual_assets") or []}
        expected_body = [
            assets[b["asset_id"]]["sha256"]
            for b in q.get("main_body") or []
            if b["type"] == "visual"
        ]
        expected_options = [
            (a.get("clean_asset") or a)["sha256"]
            for o in q.get("options") or []
            for a in o.get("images") or []
        ]
        assert parser.images["main-body"] == expected_body, (y, n, "body image order")
        assert parser.images["main-answers"] == expected_options, (
            y,
            n,
            "option image order",
        )
        html_checks.append(
            {
                "identity": row["identity"],
                "html": file_ref(path),
                "body_images": len(expected_body),
                "option_images": len(expected_options),
            }
        )
    expected = defaultdict(set)
    for row in data["records"]:
        for issue in row["categorization"]["issues"]:
            expected[issue["code"].replace("_", " ").title()].add(
                (row["identity"]["year"], row["identity"]["question_number"])
            )
    issues = (ROOT / "docs/categorization_issues.md").read_text(encoding="utf-8")
    for block in re.split(r"\n## ", issues):
        match = re.match(r"(.+) \((\d+) questions\)", block)
        if not match:
            continue
        entries = [
            (int(y), int(q))
            for y, q in re.findall(r"^\| (\d{4}) \| (\d+) \|", block, re.MULTILINE)
        ]
        assert len(entries) == len(set(entries)) == int(match[2])
        assert set(entries) == expected[match[1]]
    all_rows = {
        (int(y), int(n))
        for y, n in re.findall(r"^\| (\d{4}) \| (\d+) \|", issues, re.MULTILINE)
    }
    assert all_rows == set().union(*expected.values())
    assert len(all_rows) == data["summary"]["unresolved"]
    for row in data["records"]:
        if row["categorization"]["status"] in {"classified", "multi_label"}:
            assert (
                row["identity"]["year"],
                row["identity"]["question_number"],
            ) not in all_rows
    # A report link may point at this QA file before its first validation run.
    missing, checked_links = [], 0
    for p in (
        ROOT / "docs/CATEGORIZATION_BACKTEST.MD",
        ROOT / "docs/categorization_issues.md",
        ROOT / "docs/MATCHING_HANDOFF.md",
    ):
        for target in re.findall(
            r"(?<!!)\[[^\]]*\]\(([^)]+)\)", p.read_text(encoding="utf-8")
        ):
            if target.startswith(("https:", "http:", "#")):
                continue
            target = (p.parent / target.split("#", 1)[0].strip("<>")).resolve()
            if target != FOLDER / "validation.json" and not target.exists():
                missing.append(str(target))
            checked_links += 1
    assert not missing, missing
    assert not data["comparison"]["counts"].get("previously_classified_now_review")
    tests = []
    # Earlier iteration logs remain traceable; only these final complete runs
    # establish the current regression result.
    for name in (
        "pipeline-regressions.xml",
        "categorization-tests.xml",
        "matching-tests.xml",
    ):
        path = FOLDER / name
        suites = ElementTree.parse(path).getroot().findall("testsuite")
        assert suites, name
        assert all(
            int(s.get("failures", "0")) == int(s.get("errors", "0")) == 0
            and int(s.get("skipped", "0")) == 0
            for s in suites
        ), name
        tests.append(
            {
                "report": file_ref(path),
                "passed": sum(int(s.get("tests", "0")) for s in suites),
                "failures": 0,
                "errors": 0,
                "skipped": 0,
            }
        )
    results = {
        "owner": MARKER,
        "stage": "categorization_representation_validation",
        "categorized_reference": file_ref(
            ROOT / "data/categorized/blackstone/tsa.categorized.json"
        ),
        "review_reference": data["review_reference"],
        "raw_pages_preserved": page_count,
        "raw_question_blocks_preserved": question_count,
        "old_asset_files_preserved": len(old_assets),
        "existing_final_explanations_unchanged": explanation_count,
        "restored_source_answers": restored_answers,
        "raw_changed_records": raw_changes,
        "categorization_changes": data["comparison"],
        "summary": data["summary"],
        "review_summary": data["review_summary"],
        "checked_html": len(html_checks),
        "local_links_checked": checked_links,
        "active_unique_issues": len(all_rows),
        "final_test_runs": tests,
        "html": html_checks,
    }
    write_json(FOLDER / "validation.json", results, overwrite=True)
    print(
        {
            k: v
            for k, v in results.items()
            if k
            not in {
                "html",
                "categorization_changes",
                "raw_changed_records",
                "owner",
                "stage",
                "categorized_reference",
                "review_reference",
            }
        }
    )


if __name__ == "__main__":
    main()
