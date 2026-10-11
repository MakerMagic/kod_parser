# Inspecting Blackstone raw output

Run commands from the repository root. These utilities read existing raw JSON; inspection does not reopen the PDF or rerun extraction.

## Parse and report

```powershell
python -m parsers.blackstone acquisition/local --overwrite --issues-report docs/PARSING_ISSUES.md
```

The parser's extraction behavior and raw schema are unchanged. The only new parser CLI behavior is generating a separate Markdown issues report after raw output is saved. Without `--issues-report`, the report is `PARSING_ISSUES.md` inside the selected raw output directory. It covers all `*.raw.json` files in that directory, including previous outputs. Use a separate output directory to isolate a run.

## Inspect a stored question

```powershell
python -m parsers.blackstone.backtest inspect --raw-json "data/raw/blackstone/TSA Oxford 2020-ca4ee526afb0.raw.json" --source "TSA Oxford 2020.pdf" --year 2020 --question 12
```

`--raw-json` accepts explicit JSON files or a directory of `*.raw.json` files. `--source` accepts the stored PDF filename, path, input URL/reference, or recorded acquisition origin. URLs are compared as stored strings and are never fetched. A supplied path must match the recorded path; it does not fall back to the filename.

Optional selectors are `--year`, `--session`, `--paper`, `--variant`, `--section`, and `--question-id`. Session matching requires an existing session field; no session is inferred. Ambiguous matches produce an error instead of selecting the first record.

The default text view includes document metadata, every stored question field, and the verbatim raw question block. Add `--include-pages` for the complete stored pages in the recorded page range. Missing and null components are listed separately, without modifying the question. Empty optional lists are kept as stored; absent answers or explanations are expected for question-only parsing.

For an exact JSON representation of the question plus its document context:

```powershell
python -m parsers.blackstone.backtest inspect --raw-json data/raw/blackstone --source "TSA Oxford 2020.pdf" --year 2020 --question 12 --format json --output question-12-inspection.json
```

Exports require a new file. Existing files, including raw JSON, are never overwritten by inspection.

## Refresh the issues report without reparsing

```powershell
python -m parsers.blackstone.backtest report --raw-json data/raw/blackstone --output docs/PARSING_ISSUES.md
```

Reports list source file, available year/session/paper/variant/section, question number, pages, affected components, reasons, manual-review status, and raw JSON location. Document-level issues use an explicit document row rather than inventing a question number. Shared source/year issues are reported once per document.

Review rows come from actual parser warnings, explicit unresolved/low-confidence flags, empty essential text, duplicate/invalid numbers, or inconsistent page references/spans. General graphics-presence notices, blank-page notices, empty subpoint lists, and absent answers/explanations alone are not treated as faults. Numeric confidence values are preserved by inspection but no new confidence threshold is invented. A report with no issues is not proof of correctness.

Compare flagged records against the original PDF: wording and context, numbering, option labels and continuation lines, subparts, diagrams and their associations, page spans, and exam metadata. Font artifacts and grouped diagram options remain extraction limitations; the utility does not repair them or track manual review decisions. Reports are reproducible snapshots and refresh only files bearing their generated-report marker; unrelated Markdown files are protected.

## Tests

```powershell
python -m pytest -q tests/test_blackstone_backtest.py tests/test_blackstone_raw.py
```

If the existing virtual environment cannot launch, use the bundled-runtime setup in `parsers/blackstone/README.md` and replace `python` in these commands with `& $parserPython`.
