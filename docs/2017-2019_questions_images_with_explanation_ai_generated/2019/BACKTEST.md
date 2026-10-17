# 2019 explanation backtesting

28 imported text explanations and 17 accepted visual explanations. Q20/Q32/Q44/Q50
remain unresolved. Q6 is text-sufficient and excluded from image generation.
Q32's answer key C does not repair its conflicted match.

- [All questions](../../../inspections_matching/explanation_imports/index.html)
- [Imported Q1](../../../inspections_matching/explanation_imports/2019_q01.html)
- [Pie chart and table Q38](../../../inspections_matching/explanation_imports/2019_q38.html)
- [Conflicted Q32](../../../inspections_matching/explanation_imports/2019_q32.html)
- [Issues](ISSUES.md)

After setting `$matchingPython` as in the [workspace README](../README.md):

```powershell
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --year 2019 --question 38 --format html --output 'inspections_matching\2019_q38_import_review.html'
```

Use a new output filename on each run. Correct answer, Final Explanation,
option-specific reasons, visual evidence and unresolved statuses remain visible.
