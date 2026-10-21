# Question-rendering backtesting

Active stage: completed `data/pre_final/questions.json` → selector → single-question
website simulation → detailed report → disposable HTML/browser preview. Earlier
stages (raw, clean, matching, categorization and assembly) are complete dependencies
and are NOT rerun, repaired or reviewed here. No content/answer/category/explanation
quality reassessment. Database import follows rendering review; difficulty is later.

## Previous-stage commands (not part of rendering)

```powershell
python -m processors.pre_final build
python -m processors.pre_final validate
```

Inputs: `data/categorized/blackstone/tsa.categorized.json` and
`data/categorized/bmat/questions.categorized.json`. Existing hashed matching
references provide missing BMAT answer/explanation context and validate snapshots;
they do not run matching. JSON and referenced assets remain authoritative.

Outputs: `data/pre_final/questions.json` and compact `validation.json` with unique
excluded inputs, reason codes and counts. Exclusion counts by reason may overlap;
the unique excluded count must not be obtained by adding overlapping groups.
BMAT-specific skips and TSA multi-primary results are excluded, not reclassified.
Absent explanations are allowed only when upstream explicitly reports them
unavailable without an unresolved issue; correct answers are required.
Document-level source-profile notices remain provenance, not question defects;
question-specific unresolved warnings and review states block assembly.

## Explicit user inspection

```powershell
python -m processors.pre_final inspect --source BMAT --year 2021 --question 25 --width 1166 --output inspections_pre_final/selected.html
python -m processors.pre_final inspect --id "blackstone_2021_4502/11_section_1_q1" --width 1350 --output inspections_pre_final/selected-wide.html
python -m processors.pre_final inspect --sample 10 --width 1350 --output inspections_pre_final/sample.html
python -m processors.pre_final inspect --category ps_similarity --sample 5 --output inspections_pre_final/category-sample.html
```

Use `--id` for an exact identity, source/year/question for one question, or filters
with an explicit positive `--sample` count. Category accepts the canonical ID or
exact catalogue name. Sampling is deterministic (default seed 0, optional `--seed`)
and bounded by matching records. Without `--sample`, selection must be unique;
no default whole-dataset export. A sample produces ONE HTML, not one file per row.
`--input` defaults to pre-final JSON; no upstream JSON or reports are read.
`--open` optionally opens the generated file in the browser. Output files are
disposable and must be outside canonical data directories; use a new filename.

For a browser that does not support `file://`, serve only the preview directory
through the standard loopback-only HTTP preview workflow:

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory inspections_pre_final
```

Open the requested filename at `http://127.0.0.1:8765/`; stop the server with
Ctrl+C when finished. Do not serve the whole repository or bind a public interface.
Browser/site access still requires the normal permission controls.

One template supports width presets 1166px and 1350px (the canonical wide value).
The preview frame shows that target desktop width; smaller browser windows may
scroll the frame horizontally so a narrow window does not silently change the
chosen preset. The two-column simulation follows the supplied screenshot: passage
left, prompt/options right, neutral answer selection only (no scoring/timers).
Both columns have bounded height and independent vertical scrolling. Images use
max-width:100%, width:auto, height:auto and object-fit:contain; no stretching/crop.
Long options grow vertically. Explanations appear only in the lower detailed report.

The lower report starts Source → Explanation by AI → Category, then body, prompt,
answers, correct answer, explanation, screenshot and concise existing provenance.
Both simulation and report use the SAME pre-final record. Missing rendering fields
or assets fail clearly; content is not repaired/reinterpreted to fit the preview.

```powershell
python -m pytest -q tests/test_question_rendering.py
```
python -m processors.pre_final inspect --source BMAT --year 2015 --question 13 --width 1166 --output inspections_pre_final/2015_13.html --open