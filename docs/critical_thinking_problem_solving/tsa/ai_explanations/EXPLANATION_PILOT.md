# Text-only explanation pilot

Current Gemini-only rate-limit backoff/cooldown and the actual configured-model
pilot outcome: [EXPLANATION_FLASH35_RUN.md](EXPLANATION_FLASH35_RUN.md).
`GEMINI_REQUEST_DELAY_SECONDS` defaults to 8 seconds; provider-provided retry
delays take priority. No prompt, validator or deferred/quality retry changes were
made for that model run.

## Semantic-review gate (current behavior)

Structural validation no longer accepts explanations on its own. Valid returned
candidates enter `semantic_review_pending`, remain in the pilot audit, and are
displayed separately in backtesting as **not accepted**. Their AI provenance is
False until approval; source/manual explanations are unchanged. Pending reviews
are excluded from completed quality decisions, just like unfinished decisions
interrupted by provider failures, but remain visible in status counts.

The fixed provider-independent `generator.PROMPT` now requires a coexistence test
before using contradiction, and distinguishes necessary assumptions from
sufficient conditions, strengthening evidence and background possibilities.
`validator.semantic_review` identifies relationship mentions for inspection; it
does **not** infer semantic truth from keywords (including negated mentions).
Even unflagged explanations need reasoning review. No local NLI/arithmetic proof
is claimed and no automatic approval reviewer is installed.

`generator.approve_after_quality_review` accepts an explicitly identified reviewer,
the SHA-256 of the exact sorted-key candidate JSON, substantive checks for the
main reasoning and every incorrect option, and coexistence evidence for every
part mentioning contradiction/incompatibility. Evidence must identify whether a
contradiction is asserted and whether the claims can coexist, with a justification.
Compatible claims cannot be approved as a contradiction. These checks validate
review completeness and consistency, not the truth of the reviewer's judgement.
`reject_after_quality_review` retains the complete candidate and reasons outside
Final Explanation. Save the returned snapshot and regenerate its report with
the existing `save_snapshot` / `write_report` functions after either decision.

Normal fresh pilots still require 5–10 explicit questions. The explicit
`--calibration` flag permits only 1–4 questions for narrowly scoped regression
checks; it is not a full-batch mode. With the environment setup below:

```powershell
& $pilotPython -m processors.explanations --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --calibration --question 2017:5 --output 'data\merged\ai_pilot\semantic_calibration_next\tsa_2017.calibration.matched.json' --report 'docs\critical_thinking_problem_solving\tsa\ai_explanations\EXPLANATION_SEMANTIC_CALIBRATION_NEXT_ISSUES.md'
& $pilotPython -m processors.explanations --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --question 2017:1 --question 2017:2 --question 2017:3 --question 2017:4 --question 2017:5 --output 'data\merged\ai_pilot\semantic_next\tsa_2017.semantic.matched.json' --report 'docs\critical_thinking_problem_solving\tsa\ai_explanations\EXPLANATION_SEMANTIC_NEXT_ISSUES.md'
& $pilotPython -m pytest -q tests/test_explanation_semantics.py tests/test_explanation_pilot.py tests/test_explanation_deferred.py
```

Use a new output/report path for a fresh run. Resume rejects a changed prompt or
validator rather than silently applying old reviews to changed logic. Candidate
review and provider recovery remain separate operations; transport failure never
triggers a prompt rewrite or semantic acceptance.

The generation subsystem is `processors/explanations/`. `generator.PROMPT` is
the single provider-independent instruction template. Each request includes only
that template, one question's text/options, and its known correct answer.
`validator.py` checks the complete displayed character count (including option
labels/separators), exact incorrect-option coverage, answer consistency, basic
substance, repeated reasons, unknown labels, and obvious meta-commentary. These
checks cannot prove factual or logical correctness; manual pilot review is required.

`providers/gemini.py` owns the default model, environment override, HTTP request,
JSON extraction, timeout and bounded retry policy. It uses the documented REST
API and Python's standard library; no SDK installation is required. Provider
results are plain content plus provider/model/attempt count. Keys and full HTTP
responses are never stored. The implementation follows Google's
[generateContent reference](https://ai.google.dev/api/generate-content),
[API-key guide](https://ai.google.dev/gemini-api/docs/api-key), and
[troubleshooting guide](https://ai.google.dev/gemini-api/docs/troubleshooting).
The requested AI Studio getting-started URL was inaccessible in the browsing tool.

## Configuration and execution (PowerShell, repository root)

Configure `GEMINI_API_KEY` locally. `GOOGLE_API_KEY` is supported as a fallback;
`GEMINI_API_KEY` takes precedence. An optional `GEMINI_MODEL` overrides the
provider's single default constant. No model fallback is attempted on a model
availability error. Do not place credentials in the repository or command history.
If configured in the Windows user environment, import only these settings into
the current PowerShell session:

```powershell
foreach ($pilotName in @('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GEMINI_MODEL')) {
    $pilotValue = [Environment]::GetEnvironmentVariable($pilotName, 'User')
    if ($pilotValue) { [Environment]::SetEnvironmentVariable($pilotName, $pilotValue, 'Process') }
}
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
if (-not $env:GEMINI_MODEL) { throw 'Configured GEMINI_MODEL is not visible; stop and diagnose environment propagation.' }
$pilotPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $pilotPython -m processors.explanations --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --question 2017:1 --question 2017:2 --question 2017:3 --question 2017:4 --question 2017:5 --quality-regenerations 1 --output 'data\merged\ai_pilot\improved\tsa_2017.improved.matched.json' --report 'docs\critical_thinking_problem_solving\tsa\ai_explanations\EXPLANATION_PILOT_IMPROVED_ISSUES.md' --overwrite
```

The fixed pilot covers conclusion, calculation, flaw, inference and assumption.
The CLI requires 5–10 distinct explicitly selected identities and verifies the
entire selection before contacting a provider. There is no full-batch command.
Use `--overwrite` only to deliberately retry the same pilot output. The original
matched snapshot remains unchanged; accepted answers are immediately attached to
the pilot snapshot's `final_explanation`. Source/manual fields and question/asset
references stay intact. Rejected candidate content and failure reasons remain in
`explanation_pilot.audit`; they never become valid Final Explanation blocks.
Unselected questions are unchanged. Checkpointing preserves completed requests.

## Backtest and manual review

```powershell
& $pilotPython -m processors.matching.backtest inspect --matched-json 'data\merged\ai_pilot\improved\tsa_2017.improved.matched.json' --year 2017 --question 2
$pilotHtml = 'inspections/critical_thinking_problem_solving/tsa/matching\pilot_2017_q2_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $pilotPython -m processors.matching.backtest inspect --matched-json 'data\merged\ai_pilot\improved\tsa_2017.improved.matched.json' --year 2017 --question 2 --format html --output $pilotHtml
Invoke-Item -LiteralPath $pilotHtml
& $pilotPython -m pytest -q tests/test_explanation_pilot.py tests/test_ai_explanations.py tests/test_final_explanation.py tests/test_matching.py
```

Repeat inspection for Q2–Q5. Verify the calculations/premises, complete logical
chain, every option-specific rejection, and source fidelity. Accepted explanations
show `Explanation by AI: True` and validation/provider metadata; source/manual
explanations show `False`. Rejections show failure details in the provenance
section; no AI explanation is inserted. Text/JSON/HTML inspection remains read-only.

Stop after this pilot for manual review. After backtesting and validating the
text-only AI explanations, the next stage is AI explanation generation for
questions requiring images/visuals. That stage is not implemented here.

## Original pilot (preserved; manual review pending)

Five real requests used the configured provider/model, one API attempt each.
Q1/Q3/Q4 passed local validation and reasoning review (1,544/1,652/1,550 displayed
characters). Q2 was rejected for excessive length and contradictory draft
calculations. Q5 initially passed structural checks but reasoning review rejected
its option-A analysis: family talent does not imply being the best available
candidate, so calling it a contradiction overstates the evidence. Both complete
rejected candidates remain in the pilot audit, outside Final Explanation.

Saved HTML: `inspections/critical_thinking_problem_solving/tsa/matching/gemini_pilot_2017_q1.html` through `q5.html`.
The original matching snapshot and all unselected records are unchanged. The
rerun command above deliberately replaces only the pilot snapshot and generates
new candidates; its results require fresh reasoning review. It does not replay
or automatically clear previous quality-review rejections.

## Model comparison and bounded regeneration

The configured Windows user model was verified in the generation process before
both live runs; only its name was logged. Neither the user setting nor the
provider's fallback constant was changed. The previous pilot remains untouched.

The new baseline used the original prompt and unchanged validator, with no quality
regeneration. It is saved at
`data/merged/ai_pilot/baseline/tsa_2017.baseline.matched.json` with the exact original
prompt/hash. Five candidates passed local checks; Q5 was then rejected on reasoning
review for incorrectly calling inherited talent a contradiction. Q2's calculation
was correct and 1,479 characters, compared with the previous 2,457-character draft.

The current fixed prompt adds internal arithmetic checks, a concise consistent
calculation chain, and explicit distinctions between contradiction and other
logical failure modes. `run_pilot(..., quality_regenerations=1)` now permits exactly
one extra generation **only after local validation rejection**. It receives the
same minimal question context and rejection codes, never the prior full response.
`--quality-regenerations 0` disables it; values above one are forbidden. Transport
retries remain exclusively in the provider, with separate attempt counts.

The improved run used the same five identities and unchanged validator. Q2/Q4
are accepted; Q5 remains rejected after reasoning review; Q1/Q3 have no candidates
after three provider transport attempts each (`transient_http_failure`). None of
the returned candidates failed local structural validation, so no live quality
regeneration was triggered. Unit tests exercise successful repair, repeated
rejection, a failed provider call during regeneration, and the one-retry limit.
The prompt change has **not** solved Q5's semantic problem.

Each audit stores first/retry content, validation outcomes, displayed lengths,
provider call counts and final review status. Backtesting adds a visible Generation
Validation section and expandable history. Provider failures and reasoning-review
rejections stay unexplained; accepted content alone has AI provenance True.

Comparison: [EXPLANATION_PILOT_COMPARISON.md](EXPLANATION_PILOT_COMPARISON.md).
Baseline/improved reports: `EXPLANATION_PILOT_BASELINE_ISSUES.md` and
`EXPLANATION_PILOT_IMPROVED_ISSUES.md`; HTML folders:
`inspections/critical_thinking_problem_solving/tsa/matching/baseline/` and `inspections/critical_thinking_problem_solving/tsa/matching/improved/`.
No full batch or visual-question generation was started.

## Deferred provider recovery and resume

The prompt, model configuration and validator are unchanged. Temporary provider
errors are classified by the provider's `retryable` flag, independently of local
validation. Gemini still performs at most three immediate transport attempts with
the same request. After exhaustion the scheduler checkpoints
`provider_failure_deferred`, processes a later question, then retries earlier
deferred work. Each question has at most **two additional deferred cycles per
run**, shared across its initial generation and any quality regeneration. Remaining
work is drained in bounded end-of-run sweeps when no later questions exist; this
also permits safely retrying one isolated failed question. There is no infinite
queue or extra quality-regeneration budget.

Final statuses distinguish `accepted`, `validation_rejected`,
`reasoning_review_rejected`, `provider_failure_deferred` and
`provider_failure_exhausted`. Non-temporary authentication/configuration errors
are exhausted without deferred cycles. Exhausted provider errors remain rerunnable
later. Each failed call retains only a sanitized category, retryability, attempt
counts and request hash; credentials and HTTP response bodies are never archived.

`--resume-from` preserves accepted and reviewed results, verifies unchanged source
content, prompt, validator and configured provider/model, and retries only selected
provider-failed or pending entries. Fresh pilots still require 5–10 identities;
resuming permits a subset from the original pilot, including just one question.
The original five-question scope remains in the saved snapshot and report.

Using the PowerShell environment setup above, the completed scoped resume was:

```powershell
& $pilotPython -m processors.explanations --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --resume-from 'data\merged\ai_pilot\improved\tsa_2017.improved.matched.json' --question 2017:1 --question 2017:2 --question 2017:3 --question 2017:4 --question 2017:5 --output 'data\merged\ai_pilot\deferred\tsa_2017.deferred.matched.json' --report 'docs\critical_thinking_problem_solving\tsa\ai_explanations\EXPLANATION_PILOT_DEFERRED_ISSUES.md'
```

Q2/Q4 were preserved without generation; Q5's valid reasoning-review rejection
was preserved. Q1/Q3 each exhausted nine transport attempts in this run, with
identical request hashes across deferred cycles. The final provider category is
`rate_limited`; Q3's first window was `transient_http_failure`. This behavior
does not claim the provider service or Q5's reasoning defect has been fixed.

Pilot snapshot metrics: availability **3/5**, accepted quality among returned
outputs **2/3**, overall completed **2/5**. This run alone received **0/2** requested
outputs, using 18 transport attempts and four deferred cycles. Provider failures
are excluded from the explanation-quality denominator. If a provider interrupts
a quality regeneration after an earlier invalid output, the unfinished quality
decision is separately reported rather than lowering model-quality acceptance.

After provider availability recovers, an explicit subset resume can use:

```powershell
& $pilotPython -m processors.explanations --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --resume-from 'data\merged\ai_pilot\deferred\tsa_2017.deferred.matched.json' --question 2017:1 --question 2017:3 --output 'data\merged\ai_pilot\future_retry\tsa_2017.retry.matched.json' --report 'docs\critical_thinking_problem_solving\tsa\ai_explanations\EXPLANATION_PILOT_RETRY_ISSUES.md'
& $pilotPython -m processors.matching.backtest inspect --matched-json 'data\merged\ai_pilot\deferred\tsa_2017.deferred.matched.json' --year 2017 --question 1
```

These are manual commands, not a scheduled retry. HTML previews are saved under
`inspections/critical_thinking_problem_solving/tsa/matching/deferred/`; the report includes all five links. Backtesting
shows the separate metrics, final status, failure category, deferred cycles and
full sanitized attempt/event history. The pilot is stopped; no full batch began.
