# 2018 explanation backtesting

Read canonical records in `data/merged/blackstone/tsa_2017-2019.matched.json` by year 2018, question number, and issue status. Open referenced assets directly; no report is required to read an explanation.

For a user-requested inspection:

```powershell
python -m processors.matching.backtest inspect --matched-json data/merged/blackstone/tsa_2017-2019.matched.json --year 2018 --question 20 --format html --output inspections_matching/2018_selected_review.html
```

Use a new output filename. The view shows Final Explanation, AI provenance, source components, asset references and unresolved issues. A source review or unresolved option structure is not successful completion. See `ISSUES.md` for current workspace issues; authoritative status remains in canonical JSON.
