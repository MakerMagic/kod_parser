# 2017 explanation backtesting

Read canonical records in `data/merged/blackstone/tsa_2017-2019.matched.json` by year 2017, question number, and issue status. Open referenced assets directly; no report is required to read an explanation.

For a user-requested inspection:

```powershell
python -m processors.matching.backtest inspect --matched-json data/merged/blackstone/tsa_2017-2019.matched.json --year 2017 --question 20 --format html --output inspections/critical_thinking_problem_solving/tsa/matching/2017_selected_review.html
```

Use a new output filename. The view shows Final Explanation, AI provenance, source components, asset references and unresolved issues. A source review or unresolved option structure is not successful completion. See `ISSUES.md` for current workspace issues; authoritative status remains in canonical JSON.
