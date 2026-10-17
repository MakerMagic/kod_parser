# 2018 explanation backtesting

32 imported text explanations and 13 accepted visual explanations. Q20/Q32/Q44/Q50
remain unresolved. Q14 is text-sufficient and excluded from image generation.
Q20's answer key B does not repair its conflicted match.

- [All questions](../../../inspections_matching/explanation_imports/index.html)
- [Imported Q1](../../../inspections_matching/explanation_imports/2018_q01.html)
- [View/height reasoning Q26](../../../inspections_matching/explanation_imports/2018_q26.html)
- [Conflicted Q20](../../../inspections_matching/explanation_imports/2018_q20.html)
- [Issues](ISSUES.md)

After setting `$matchingPython` as in the [workspace README](../README.md):

```powershell
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --year 2018 --question 26 --format html --output 'inspections_matching\2018_q26_import_review.html'
```

Use a new output filename on each run. Backtesting retains all question images
and separately shows explanation availability, AI provenance and match approval.
