"""Mathematics Question Rendering from canonical PRE-FINAL JSON only."""

import argparse
import json
import random
from collections import Counter
from html import escape
from pathlib import Path

from parsers.mathematics.latex import mathml
from parsers.mathematics.structure import walk
from processors.stage_artifacts import write_stage_pair

from .preview_content import QuestionContent, text
from .preview_layout import WIDTHS, answer_option, document, simulation_frame
from .preview_report import report_section
from .storage import ROOT

INPUT = ROOT / "data/pre_final/mathematics/questions.json"
OUTPUT = ROOT / "data/question_rendering/mathematics/validation.json"
DOCS = ROOT / "docs/mathematics"
SAMPLE = ROOT / "inspections/mathematics/question_rendering/representative.html"

MATH_CSS = (
    ".math-stream{min-width:0;overflow-wrap:anywhere}"
    ".math-text{white-space:pre-wrap;overflow-wrap:anywhere}"
    ".math-inline{display:inline-block;max-width:100%;vertical-align:middle;"
    "font-family:'Cambria Math',STIX Two Math,serif}"
    ".math-display{display:block;max-width:100%;margin:10px 0;"
    "font-family:'Cambria Math',STIX Two Math,serif}"
    ".math-stream figure{display:block}"
    ".math-stream figure img{max-width:100%;width:auto;height:auto;object-fit:contain}"
    ".source-list{margin:8px 0;padding-left:24px}"
    ".answer-option math{max-width:100%;font-size:1em}"
    ".answer-option .math-display{margin:2px 0}"
    ".math-report-body{line-height:1.6}"
)


class RenderingInputError(ValueError):
    def __init__(self, question, code, field, reason, responsible_stage="pre-final"):
        super().__init__(f"{question['id']} {field}: {reason}")
        self.issue = {
            "id": question.get("id"),
            "source_document_id": question.get("source_document_id"),
            "source_pdf": question.get("source_pdf"),
            "question_number": question.get("question_number"),
            "code": code,
            "field": field,
            "reason": reason,
            "responsible_stage": responsible_stage,
        }


def load(path=INPUT):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    if (
        data.get("stage") != "mathematics_pre_final"
        or data.get("domain") != "mathematics"
    ):
        raise ValueError(
            "Mathematics rendering accepts mathematics PRE-FINAL JSON only"
        )
    if not summary.get("ready_for_rendering") or summary.get("blocking_issues"):
        raise ValueError("PRE-FINAL has blocking issues; rendering cannot begin")
    if summary.get("included") != len(data.get("questions", [])):
        raise ValueError("PRE-FINAL included count does not match question records")
    return data


def category_name(question):
    category = question.get("category")
    if (
        not isinstance(category, dict)
        or not isinstance(category.get("id"), str)
        or not isinstance(category.get("name"), str)
    ):
        raise RenderingInputError(
            question,
            "invalid_category",
            "category",
            "PRE-FINAL category requires its canonical ID and display name",
        )
    return category["name"]


def assert_renderable(question, sources):
    for field in (
        "id",
        "source_document_id",
        "source_pdf",
        "question_number",
        "content_layout",
        "main_body",
        "main_question",
        "main_answers",
        "correct_answer",
        "category",
        "subcategory",
        "assets",
        "provenance",
    ):
        if field not in question:
            raise RenderingInputError(
                question,
                "missing_field",
                field,
                "Required mathematics PRE-FINAL field is absent",
            )
    if (
        question["content_layout"] != "body_and_question"
        or not isinstance(question["main_body"], list)
        or (
            question["main_question"] is not None
            and not isinstance(question["main_question"], list)
        )
        or not (question["main_body"] or question["main_question"])
    ):
        raise RenderingInputError(
            question,
            "unsupported_content_layout",
            "content_layout",
            "Mathematics PRE-FINAL must provide the CLEAN-derived context/task fields",
        )
    if (
        question["source"] != "Mathematics"
        or question["source_document_id"] not in sources
    ):
        raise RenderingInputError(
            question,
            "invalid_source",
            "source_document_id",
            "Source document does not resolve in PRE-FINAL",
        )
    category_name(question)
    answers = question["main_answers"]
    labels = [answer.get("label") for answer in answers]
    if labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]) or len(labels) < 2:
        raise RenderingInputError(
            question,
            "invalid_answers",
            "main_answers",
            "Answer labels must be complete and in source order",
        )
    if question["correct_answer"] not in labels:
        raise RenderingInputError(
            question,
            "invalid_correct_answer",
            "correct_answer",
            "Stored answer does not identify an answer option",
        )
    assets = {asset.get("id"): asset for asset in question["assets"]}
    if None in assets or len(assets) != len(question["assets"]):
        raise RenderingInputError(
            question,
            "invalid_assets",
            "assets",
            "Asset identifiers must be present and unique",
        )
    for field, blocks in [
        ("main_body", question["main_body"]),
        ("main_question", question["main_question"]),
        *[(f"main_answers.{a['label']}", a["content"]) for a in answers],
    ]:
        if field == "main_question" and blocks is None:
            continue
        if field == "main_question" and any(
            block["type"] == "visual" for block in walk(blocks or [])
        ):
            raise RenderingInputError(
                question,
                "image_in_main_question",
                field,
                "Question visuals must be stored in Main Body; Main Question is text/LaTeX only",
                "CLEAN",
            )
        if not isinstance(blocks, list) or (not blocks and field != "main_body"):
            raise RenderingInputError(
                question,
                "empty_content",
                field,
                "Required source-ordered content is empty",
            )
        try:
            for block in walk(blocks):
                kind = block["type"]
                if kind == "math":
                    mathml(block["latex"], display=block["display"])
                elif kind == "text":
                    if not isinstance(block.get("text"), str):
                        raise ValueError("Text block lacks text")
                elif kind == "visual":
                    asset_id = block.get("asset_id")
                    if asset_id not in assets:
                        raise ValueError(f"Visual asset {asset_id} is absent")
                elif kind == "list":
                    if not isinstance(block.get("items"), list):
                        raise ValueError("List block lacks ordered items")
                else:
                    raise ValueError(f"Unsupported content block type: {kind}")
        except (KeyError, TypeError, ValueError) as error:
            raise RenderingInputError(
                question, "unsupported_content", field, str(error), "RAW parsing"
            ) from error
    return assets


class MathematicsContent:
    def __init__(self, question, *, root=ROOT):
        self.question = question
        self.shared = QuestionContent(question, root=root)

    def blocks(self, blocks, *, caption=False):
        parts = []
        for block in blocks:
            kind = block["type"]
            if kind == "text":
                rendered = (
                    "<span class='math-text'>" + escape(block["text"]) + "</span>"
                )
            elif kind == "math":
                cls = "math-display" if block["display"] else "math-inline"
                rendered = (
                    "<span class='"
                    + cls
                    + "'>"
                    + mathml(block["latex"], display=block["display"])
                    + "</span>"
                )
            elif kind == "visual":
                rendered = self.shared.figure(block["asset_id"], caption=caption)
            elif kind == "list":
                tag = "ol" if block.get("ordered") else "ul"
                rendered = (
                    "<"
                    + tag
                    + " class='source-list'>"
                    + "".join(
                        "<li class='math-stream'>"
                        + self.blocks(item["content"], caption=caption)
                        + "</li>"
                        for item in block["items"]
                    )
                    + "</"
                    + tag
                    + ">"
                )
            else:
                raise ValueError(f"Unsupported mathematics block: {kind}")
            if block.get("break_before"):
                rendered = "<div class='source-block'>" + rendered + "</div>"
            parts.append(rendered)
        return "<div class='math-stream'>" + "".join(parts) + "</div>"

    def body(self, *, caption=False):
        return self.blocks(self.question["main_body"], caption=caption)

    def answer(self, answer, *, caption=False):
        return self.blocks(answer["content"], caption=caption)

    def prompt(self, *, caption=False):
        return (
            self.blocks(self.question["main_question"], caption=caption)
            if self.question["main_question"]
            else ""
        )


def render_one(question, sources, *, root=ROOT, position=1, count=1):
    assert_renderable(question, sources)
    content = MathematicsContent(question, root=root)
    category = category_name(question)
    body = content.body()
    answers = "".join(
        answer_option(answer["label"], content.answer(answer), position)
        for answer in question["main_answers"]
    )
    prefix = "" if count == 1 else f"q{position - 1}-"
    simulation = simulation_frame(
        body,
        content.prompt(),
        answers,
        source="Mathematics · " + question["source_pdf"],
        heading="Question preview",
        badge=category,
        question_number=question["question_number"],
        report_prefix=prefix,
        position=position,
        count=count,
        body_label="MAIN BODY",
    )
    section = lambda key, title, value: report_section(key, title, value, prefix=prefix)
    report = [
        "<section class='detailed-report' aria-label='Detailed question report'><h2>Detailed report</h2>"
    ]
    report += [
        section("source", "Source", text("Mathematics · " + question["source_pdf"])),
        section("category", "Category", text(category)),
        section(
            "main-body",
            "Main Body",
            "<div class='math-report-body'>" + content.body(caption=True) + "</div>",
        ),
        section(
            "main-question",
            "Main Question",
            content.prompt(caption=True)
            if question["main_question"]
            else text("null — no separate source task statement"),
        ),
        section(
            "main-answers",
            "Main Answers",
            "".join(
                "<div class='report-answer' data-option='"
                + escape(a["label"], quote=True)
                + "'><strong>"
                + escape(a["label"])
                + ":</strong>"
                + content.answer(a, caption=True)
                + "</div>"
                for a in question["main_answers"]
            ),
        ),
        section("correct-answer", "Correct Answer", text(question["correct_answer"])),
    ]
    trace = {
        "id": question["id"],
        "source_document_id": question["source_document_id"],
        "source_pdf": question["source_pdf"],
        "question_number": question["question_number"],
        "content_layout": question["content_layout"],
        "category_id": question["category"]["id"],
        "subcategory_id": question["subcategory"]["id"]
        if question["subcategory"]
        else None,
        "provenance": question["provenance"],
    }
    report += [
        section(
            "traceability",
            "Question identity / provenance",
            "<pre>"
            + escape(json.dumps(trace, ensure_ascii=False, indent=2))
            + "</pre>",
        ),
        "</section>",
    ]
    return (
        "<article class='question-preview' data-question-id='"
        + escape(question["id"], quote=True)
        + "'>"
        + simulation
        + "".join(report)
        + "</article>"
    )


def build_report(questions, sources, *, root=ROOT, width=1166):
    if width not in WIDTHS:
        raise ValueError("Supported preview widths: 1166 or 1350")
    if not questions:
        raise ValueError("No selected mathematics questions")
    articles = [
        render_one(q, sources, root=root, position=i, count=len(questions))
        for i, q in enumerate(questions, 1)
    ]
    return document(articles, width=width, extra_css=MATH_CSS)


def select_many(
    data,
    *,
    identifier=None,
    source=None,
    question=None,
    category=None,
    sample=None,
    seed=0,
    issues=False,
    issue_code=None,
    issue_rows=(),
):
    if sample is not None and (type(sample) is not int or sample <= 0):
        raise ValueError("--sample must be a positive integer")
    issue_ids = {
        row["id"]
        for row in issue_rows
        if issue_code is None or row["code"] == issue_code
    }
    if issues or issue_code:
        candidates = issue_ids
    else:
        candidates = None
    if (
        sample is None
        and identifier is None
        and source is None
        and question is None
        and category is None
        and candidates is None
    ):
        raise ValueError(
            "Select an ID, source/test, question, category, issue or explicit --sample"
        )
    rows = []
    for q in data["questions"]:
        names = {q["source_pdf"], q["source_document_id"], Path(q["source_pdf"]).stem}
        if identifier is not None and q["id"] != identifier:
            continue
        if source is not None and source not in names:
            continue
        if question is not None and q["question_number"] != question:
            continue
        if category is not None and category not in {
            q["category"]["id"],
            q["category"]["name"],
        }:
            continue
        if candidates is not None and q["id"] not in candidates:
            continue
        rows.append(q)
    rows.sort(key=lambda q: q["id"])
    if not rows:
        raise ValueError("No mathematics pre-final questions match the selection")
    if sample is not None:
        rows = random.Random(seed).sample(rows, min(sample, len(rows)))
        rows.sort(key=lambda q: q["id"])
    elif len(rows) != 1:
        raise ValueError("Selection is not unique; refine selectors or choose --sample")
    return rows


def representative_sample(data, limit=9):
    rows = data["questions"]

    def payload(q):
        blocks = list(walk(q["main_body"] + (q["main_question"] or []))) + [
            b for a in q["main_answers"] for b in walk(a["content"])
        ]
        formulas = [b["latex"] for b in blocks if b["type"] == "math"]
        kinds = {b["type"] for b in blocks}
        return blocks, formulas, kinds

    predicates = [
        lambda q, b, f, k: not f and "visual" not in k,
        lambda q, b, f, k: any("\\frac" in x for x in f),
        lambda q, b, f, k: any("\\sqrt" in x for x in f),
        lambda q, b, f, k: any("^" in x or "_" in x for x in f),
        lambda q, b, f, k: any(x.get("display") for x in b if x["type"] == "math"),
        lambda q, b, f, k: "visual" in k,
        lambda q, b, f, k: any("\\begin" in x for x in f),
        lambda q, b, f, k: (
            max(
                (
                    len(json.dumps(a["content"], ensure_ascii=False))
                    for a in q["main_answers"]
                ),
                default=0,
            )
            > 1000
        ),
    ]
    selected = []
    for predicate in predicates:
        candidate = next(
            (
                q
                for q in rows
                if q["id"] not in {x["id"] for x in selected}
                and predicate(q, *payload(q))
            ),
            None,
        )
        if candidate:
            selected.append(candidate)
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        selected += [q for q in rows if q["id"] not in {x["id"] for x in selected}][
            : limit - len(selected)
        ]
    return sorted(selected, key=lambda q: q["id"])


def audit(data, *, root=ROOT):
    seen = set()
    findings = []
    counts = Counter()
    per_source = Counter()
    for q in data["questions"]:
        identity = (q.get("source_document_id"), q.get("question_number"))
        if q.get("id") in seen or identity in seen:
            findings.append(
                {
                    "id": q.get("id"),
                    "source_pdf": q.get("source_pdf"),
                    "question_number": q.get("question_number"),
                    "code": "duplicate_identity",
                    "field": "id/source_document_id/question_number",
                    "reason": "Duplicate stable identity in PRE-FINAL",
                    "responsible_stage": "pre-final",
                }
            )
        seen.add(q.get("id"))
        seen.add(identity)
        per_source[q.get("source_pdf", "<missing>")] += 1
        try:
            assert_renderable(q, data["sources"])
            content = MathematicsContent(q, root=root)
            content.body()
            content.prompt()
            for answer in q["main_answers"]:
                content.answer(answer)
            for asset in q["assets"]:
                content.shared.figure(asset["id"], caption=False)
            for block in [
                *walk(q["main_body"]),
                *walk(q["main_question"] or []),
                *(b for a in q["main_answers"] for b in walk(a["content"])),
            ]:
                counts[block["type"]] += 1
        except (ValueError, OSError, KeyError, TypeError) as error:
            if isinstance(error, RenderingInputError):
                issue = error.issue
            else:
                issue = {
                    "id": q.get("id"),
                    "source_document_id": q.get("source_document_id"),
                    "source_pdf": q.get("source_pdf"),
                    "question_number": q.get("question_number"),
                    "code": "rendering_failure",
                    "field": "content/assets",
                    "reason": str(error),
                    "responsible_stage": "pre-final asset references",
                }
            if issue not in findings:
                findings.append(issue)
    return {
        "domain": "mathematics",
        "stage": "mathematics_question_rendering_validation",
        "schema_version": "1",
        "input": "data/pre_final/mathematics/questions.json",
        "summary": {
            "pre_final_questions": len(data["questions"]),
            "renderable": len(data["questions"]) - len({x["id"] for x in findings}),
            "issues": len(findings),
            "ready_for_website_review": not findings,
            "content_blocks_by_type": dict(sorted(counts.items())),
            "questions_by_source": dict(sorted(per_source.items())),
        },
        "issues": findings,
    }


def render_artifacts(data, validation, preview_path):
    if validation["summary"]["pre_final_questions"] != len(
        data["questions"]
    ) or validation["summary"]["issues"] != len(validation["issues"]):
        raise ValueError("Rendering validation counts disagree with PRE-FINAL")
    back = [
        "# Mathematics QUESTION RENDERING backtesting",
        "",
        "Generated from canonical mathematics PRE-FINAL JSON and rendering validation; question content remains in PRE-FINAL.",
        "",
        f"PRE-FINAL questions: {validation['summary']['pre_final_questions']}",
        f"Renderable: {validation['summary']['renderable']}",
        f"Rendering issues: {validation['summary']['issues']}",
        f"Ready for website review: {str(validation['summary']['ready_for_website_review']).lower()}",
        "",
        "## Questions by source/test",
        "",
    ]
    back += [
        f"- {source}: {count}"
        for source, count in validation["summary"]["questions_by_source"].items()
    ]
    back += ["", "## Rendered content blocks", ""]
    back += [
        f"- {kind}: {count}"
        for kind, count in validation["summary"]["content_blocks_by_type"].items()
    ]
    back += [
        "",
        "## Reusable inspection",
        "",
        "The HTML inspection output contains one representative sample, not one file per question:",
        f"`{preview_path.as_posix()}`",
        "",
        "Select an individual question or test on demand:",
        "",
        "```powershell",
        "python -m processors.pre_final.mathematics_render inspect --id <stable-id> --output <preview.html>",
        "python -m processors.pre_final.mathematics_render inspect --source Test_3.pdf --question 12 --width 1350 --output <preview.html>",
        "python -m processors.pre_final.mathematics_render inspect --category M4 --sample 5 --output <preview.html>",
        "python -m processors.pre_final.mathematics_render inspect --issues --output <preview.html>",
        "```",
        "",
        "LaTeX becomes offline native MathML. Main Body and Main Question copy CLEAN-derived ordered blocks; the renderer does not infer boundaries. A null Main Question means no separate source task. Shared TSA/BMAT simulation, option-card, report-section and CSS components are reused. Explanation by AI and explanation are absent from the mathematics schema.",
    ]
    issue_md = [
        "# Mathematics QUESTION RENDERING issues",
        "",
        "Generated from the rendering validation derived from canonical PRE-FINAL JSON.",
        "",
        f"Total issues: {len(validation['issues'])}",
        f"Affected questions: {len({i['id'] for i in validation['issues']})}",
        "",
    ]
    if not validation["issues"]:
        issue_md.append(
            "No unresolved mathematics question-rendering issues currently exist."
        )
    for issue in validation["issues"]:
        issue_md += [
            f"## {issue['source_pdf']} — Q{issue['question_number']} — {issue['id']}",
            "",
            f"Type: `{issue['code']}`; field: `{issue['field']}`; responsible stage: `{issue['responsible_stage']}`.",
            f"Exact reason: {issue['reason']}",
            "",
        ]
    return "\n".join(back) + "\n", "\n".join(issue_md).rstrip() + "\n"


def write_inspection(data, output, *, width=1166, **filters):
    rows = select_many(data, **filters)
    html = build_report(rows, data["sources"], width=width)
    output = Path(output)
    resolved = output.resolve()
    if any(
        resolved.is_relative_to(ROOT / "data" / name)
        for name in ("input", "raw", "clean", "merged", "categorized", "pre_final")
    ):
        raise ValueError("Inspection output must be outside canonical data directories")
    if output.exists():
        raise FileExistsError("Choose a new disposable preview filename")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8", newline="\n")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser(
        "run",
        help="Audit all PRE-FINAL questions and generate one representative preview",
    )
    run.add_argument("--input", type=Path, default=INPUT)
    run.add_argument("--output", type=Path, default=OUTPUT)
    run.add_argument("--docs-dir", type=Path, default=DOCS)
    run.add_argument("--preview", type=Path, default=SAMPLE)
    run.add_argument("--width", type=int, choices=WIDTHS, default=1166)
    inspect = sub.add_parser(
        "inspect", help="Generate only a requested question preview"
    )
    inspect.add_argument("--input", type=Path, default=INPUT)
    inspect.add_argument("--validation", type=Path, default=OUTPUT)
    inspect.add_argument("--id", dest="identifier")
    inspect.add_argument("--source", help="Source PDF, test name or source document ID")
    inspect.add_argument("--question", type=int)
    inspect.add_argument("--category")
    inspect.add_argument("--issues", action="store_true")
    inspect.add_argument("--issue-code")
    inspect.add_argument("--sample", type=int)
    inspect.add_argument("--seed", type=int, default=0)
    inspect.add_argument("--width", type=int, choices=WIDTHS, default=1166)
    inspect.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    data = load(args.input)
    if args.command == "inspect":
        validation = (
            json.loads(args.validation.read_text(encoding="utf-8"))
            if args.validation.is_file()
            else {"issues": []}
        )
        return str(
            write_inspection(
                data,
                args.output,
                width=args.width,
                identifier=args.identifier,
                source=args.source,
                question=args.question,
                category=args.category,
                sample=args.sample,
                seed=args.seed,
                issues=args.issues,
                issue_code=args.issue_code,
                issue_rows=validation["issues"],
            )
        )
    validation = audit(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    renderable = {q["id"] for q in data["questions"]} - {
        issue["id"] for issue in validation["issues"]
    }
    preview_rows = [q for q in representative_sample(data) if q["id"] in renderable]
    if not preview_rows and renderable:
        preview_rows = [next(q for q in data["questions"] if q["id"] in renderable)]
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    if any(
        args.preview.resolve().is_relative_to(ROOT / "data" / name)
        for name in ("input", "raw", "clean", "merged", "categorized", "pre_final")
    ):
        raise ValueError(
            "Representative HTML must be outside canonical data directories"
        )
    args.preview.write_text(
        build_report(preview_rows, data["sources"], width=args.width),
        encoding="utf-8",
        newline="\n",
    )
    pair = render_artifacts(data, validation, args.preview.relative_to(ROOT))
    write_stage_pair(args.docs_dir, "QUESTION_RENDERING", pair)
    print(json.dumps(validation["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if not validation["issues"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
