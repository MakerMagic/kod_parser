import json
from collections import Counter
from pathlib import Path

import pytest

from parsers.mathematics.raw_issues import collect, render

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/mathematics"


def test_raw_issue_report_covers_each_structured_issue():
    findings = collect(RAW.glob("*.raw.json"))
    report = render(findings)
    expected = Counter()
    for path in RAW.glob("*.raw.json"):
        data = json.loads(path.read_text(encoding="utf8"))
        expected.update(i["code"] for q in data["questions"] for i in q["issues"])
        expected.update(i["code"] for i in data.get("issues", []))
        expected.update(i["code"] for i in data.get("answer_key", {}).get("issues", []))
    assert len(findings) == sum(expected.values())
    assert Counter(item["category"] for item in findings) == expected
    assert report.count("\n- **") == len(findings)
    for item in findings:
        assert item["question_id"] in report
        assert item["source_pdf"] in report
        assert item["category"] in report
        assert item["reason"] in report
    assert "answer_matching" not in report
    assert report == (ROOT / "docs/mathematics/RAW_ISSUES.md").read_text(
        encoding="utf8"
    )
    assert not (ROOT / "docs/mathematics/ISSUES.md").exists()


def test_raw_issue_report_requires_question_link_and_concrete_reason(tmp_path):
    raw = {
        "domain": "mathematics",
        "stage": "mathematics_raw",
        "source_document": {"filename": "math_test.pdf"},
        "questions": [
            {
                "id": "math_test_q001",
                "question_number": 1,
                "issues": [
                    {
                        "code": "uncertain_formula",
                        "reason": "Fraction bar ambiguous",
                        "field": "question",
                        "page": 2,
                    }
                ],
            }
        ],
        "issues": [],
        "answer_key": {"issues": []},
    }
    path = tmp_path / "test.raw.json"
    path.write_text(json.dumps(raw), encoding="utf8")
    finding = collect([path])[0]
    report = render([finding])
    assert "math_test.pdf — Q1" in report
    assert "page 2" in report
    assert "Fraction bar ambiguous" in report
    assert "affected field: `question`" in report

    raw["questions"][0]["issues"][0].pop("reason")
    path.write_text(json.dumps(raw), encoding="utf8")
    with pytest.raises(ValueError, match="lacks a concrete reason"):
        collect([path])

    raw["questions"][0]["issues"] = []
    raw["issues"] = [{"code": "unlinked", "reason": "Cannot identify question"}]
    path.write_text(json.dumps(raw), encoding="utf8")
    with pytest.raises(ValueError, match="not linked to a question"):
        collect([path])
