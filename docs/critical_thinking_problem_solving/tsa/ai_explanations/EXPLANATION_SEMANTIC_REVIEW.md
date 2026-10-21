# Semantic calibration — provider blocked, not a verified reasoning fix

## Changes

The fixed provider-independent prompt now explicitly tests coexistence before
calling claims contradictory. Assumption guidance distinguishes necessary
premises from sufficient conditions, support, possibilities and alternatives.
Arithmetic, individual option analysis and the 2,000-character limit remain.

Local checks cannot reliably prove those relationships. Returned, structurally
valid candidates now remain `semantic_review_pending`, outside accepted Final
Explanation, until candidate-hash-bound, documented reasoning review. Review
must cover main reasoning and each incorrect choice; contradiction mentions also
require explicit coexistence evidence. Compatible claims cannot be approved as
contradictory. Keyword triage is not a semantic proof, and negated mentions are
not automatically rejected. No automatic semantic approval was installed.

## Actual runs

All live processes verified the unchanged configured `gemini-3.6-flash` model.
No credential values were printed. Source/manual explanations and canonical
matched inputs were not rewritten. Only explicit pilot/calibration identities
were sent, one question per request. No full batch was started.

| Run | Questions | Returned | Accepted | Quality decisions | Final result |
|---|---|---|---|---|---|
| Calibration | 2017 Q5 | 0/1 | 0 | 0 | Provider retry exhaustion: rate limited |
| Same five pilot | 2017 Q1–Q5 | 0/5 | 0 | 0 | All provider retry exhaustion: rate limited |
| Extra critical reasoning sample | 2017 Q9/Q16/Q17 | 0/3 | 0 | 0 | All provider retry exhaustion: rate limited |

The extra sample covers weakening, necessary assumption and strengthening;
each was confirmed eligible from existing parsed text-only matched records.
Its first execution was interrupted by an unwrapped connection-close exception.
That checkpoint remains under `data/merged/ai_pilot/semantic_sample/`. The provider
now handles connection closures within its existing three-attempt transport
mechanism, with no prompt changes or quality retry consumption. A separate bounded
recovery execution of the same three identities completed under
`data/merged/ai_pilot/semantic_sample_recovery/`. No candidate was lost or accepted.

Each completed execution used three immediate transport attempts and at most two
deferred cycles per question (nine attempts each); all final categories were
`rate_limited`. Provider failures are not explanation-quality rejections. With no
returned outputs, a new-model quality acceptance percentage is **undefined**,
not 0%. Overall completion is 0/5 for the five-question pilot.

## Comparison and unresolved result

The previous improved pilot had Q2/Q4 accepted, Q5 rejected for the false
contradiction, and no returned candidates for Q1/Q3. The new five-question run
returned no candidates. Therefore arithmetic quality, logical precision,
per-option reasoning and semantic improvement **cannot be compared empirically**.
The Q5 false-contradiction error is **not verified fixed**. Historical candidates
were not relabelled as newly generated or accepted.

Offline regressions verify that the Q5 bad candidate passes structural checks but
cannot enter accepted Final Explanation without review; a review explicitly
finding coexistence cannot approve its contradictory characterization. They also
cover negated contradiction mentions, other relationship terms, per-option review
coverage, candidate hash binding, pending-candidate HTML, pilot/calibration bounds,
and connection-close transport failures. These are safeguards, not evidence that
Gemini has produced correct new explanations.

Validation completed: 115 focused explanation/deferred/matching tests passed;
Ruff lint/format checks, Git whitespace checks and all five PowerShell command
blocks passed. Console/JSON inspection was verified read-only. All nine completed
calibration/pilot/sample HTML exports were checked, and all 550 existing
source/manual explanations retain AI provenance False.

## Backtesting and reports

- Calibration: `inspections/critical_thinking_problem_solving/tsa/matching/semantic_calibration/tsa_2017_q5.html`.
- Same pilot: `inspections/critical_thinking_problem_solving/tsa/matching/semantic/tsa_2017_q1.html` through `q5.html`.
- Extra sample: `inspections/critical_thinking_problem_solving/tsa/matching/semantic_sample/tsa_2017_q9.html`, `q16.html`, `q17.html`.
- Generated reports: `EXPLANATION_SEMANTIC_CALIBRATION_ISSUES.md`,
  `EXPLANATION_SEMANTIC_PILOT_ISSUES.md`, `EXPLANATION_SEMANTIC_SAMPLE_ISSUES.md`.
- Interrupted audit: `EXPLANATION_SEMANTIC_SAMPLE_INTERRUPTED_ISSUES.md`.
- Generated same-question comparison: `EXPLANATION_SEMANTIC_COMPARISON.md`.

HTML exports were checked for identity, answer, Final Explanation, AI False,
provider/model, retry/validation fields and explicit exhausted-provider status.
There is no new explanation content to inspect visually. A successful future
provider run and actual reasoning review are still required before acceptance.
See `EXPLANATION_PILOT.md` for scoped rerun commands; no retry is scheduled.
