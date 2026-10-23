# Mathematics QUESTION RENDERING backtesting

Generated from canonical mathematics PRE-FINAL JSON and rendering validation; question content remains in PRE-FINAL.

PRE-FINAL questions: 519
Renderable: 519
Rendering issues: 0
Ready for website review: true

## Questions by source/test

- Test_1.pdf: 22
- Test_2.pdf: 25
- Test_3.pdf: 27
- Test_4.pdf: 27
- Test_5.pdf: 27
- Test_6.pdf: 24
- Test_7.pdf: 24
- Test_8.pdf: 4
- math_1.pdf: 28
- math_10.pdf: 30
- math_11.pdf: 28
- math_12.pdf: 29
- math_2.pdf: 26
- math_3.pdf: 26
- math_4.pdf: 29
- math_5.pdf: 29
- math_6.pdf: 27
- math_7.pdf: 29
- math_8.pdf: 30
- math_9.pdf: 28

## Rendered content blocks

- list: 2
- math: 3612
- text: 3426
- visual: 185

## Reusable inspection

The HTML inspection output contains one representative sample, not one file per question:
`inspections/mathematics/question_rendering/representative.html`

Select an individual question or test on demand:

```powershell
python -m processors.pre_final.mathematics_render inspect --id <stable-id> --output <preview.html>
python -m processors.pre_final.mathematics_render inspect --source Test_3.pdf --question 12 --width 1350 --output <preview.html>
python -m processors.pre_final.mathematics_render inspect --category M4 --sample 5 --output <preview.html>
python -m processors.pre_final.mathematics_render inspect --issues --output <preview.html>
```

LaTeX becomes offline native MathML. Main Body and Main Question copy CLEAN-derived ordered blocks; the renderer does not infer boundaries. A null Main Question means no separate source task. Shared TSA/BMAT simulation, option-card, report-section and CSS components are reused. Explanation by AI and explanation are absent from the mathematics schema.
