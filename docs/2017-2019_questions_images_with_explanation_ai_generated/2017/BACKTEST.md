# 2017 explanation backtesting

37 imported text explanations and 9 accepted visual explanations. Q14/Q38/Q44/Q50
remain unresolved; inspect their issue status rather than treating them as complete.

- [All questions](../../../inspections_matching/explanation_imports/index.html)
- [Imported Q1](../../../inspections_matching/explanation_imports/2017_q01.html)
- [Table and visual answers Q20](../../../inspections_matching/explanation_imports/2017_q20.html)
- [Unresolved option structure Q38](../../../inspections_matching/explanation_imports/2017_q38.html)
- [Issues](ISSUES.md)

After setting `$matchingPython` as in the [workspace README](../README.md):

```powershell
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --year 2017 --question 20 --format html --output 'inspections_matching\2017_q20_import_review.html'
```

Use a new output filename on each run. Final Explanation, AI provenance, input
references and hashes, source components, visuals and unresolved issues are shown.
