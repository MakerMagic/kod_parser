# BMAT Section 1 matching backtesting

Read-only views of canonical matches. Excluded/deferred sources are explicitly not accepted matches.

## Reproduce independently

```powershell
python -m acquisition.bmat_worked_solutions
python -m parsers.bmat_worked_solutions
python -m parsers.bmat_supplied_explanations data/input/bmat_supplied_explanations/2026-10-19.txt
python -m processors.matching.bmat run
python -m processors.matching.bmat report
```

Acquisition uses hash-verified local cache. Parser and matching need no network. An unavailable external mirror host is deferred after verified connection/TLS failures; use acquisition `--retry-failed-hosts` explicitly after connectivity returns. No answers are inferred from prose. Source-image answer headers are locally OCR-read, checked against the page identity, and retained with bbox/hash evidence; full explanation images are preserved. The 2014 Section 1 index links a separate specimen PDF, not individual solutions; that file is not substituted for these question records.

User-supplied material is a separate hash/line-bound local source. Imports never add images, overwrite an existing explanation, or bypass BMAT eligibility. Same-answer variants remain separate; explicit source cautions remain review issues. A missing question header is not inferred from neighboring prose.

## Select a user-requested inspection

```powershell
python -m processors.matching.bmat report --year 2021 --question 25
```

Only explicitly requested `report` commands render HTML. Omit `--question` to select a year; omit both selectors only when a complete export is actually requested. `run` persists matching and issues without HTML exports. Canonical data is `data/merged/bmat/questions.matched.json`; filter `records` by identity/status to read a question directly. Referenced assets can be opened directly. Correct Answer and Main/Final Explanation remain separate; reviews, conflicts, provenance and upstream exclusions remain visible. Counts and individual records belong to JSON and issue indexes, not this guide.
