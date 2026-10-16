# TSA 2017 Q1–Q5: configured Gemini 3.5 Flash pilot

## Scope and invariants

The actual generation process verified `GEMINI_MODEL=gemini-3.5-flash` before
generation. No user-environment setting was changed and no credentials were
printed or saved. No model/provider fallback or full batch was attempted.
Only Gemini provider pacing/classification and focused tests changed. File hashes
confirmed that the generator (including prompt and quality-regeneration logic),
validator (including Q5 coexistence safeguards), deferred scheduler and matching
backtest code stayed unchanged. Canonical question/source explanation content
was preserved; the pilot has its own matched snapshot.

## Provider behavior

`providers/gemini.py` classifies HTTP 429 and structured `RESOURCE_EXHAUSTED`,
`too_many_requests`, `rate_limit_exceeded` and `quota_exceeded` as resumable
rate-limit errors, distinct from authentication, availability and other failures.
This follows Google's [error guidance](https://ai.google.dev/gemini-api/docs/troubleshooting).
Only bounded error bodies are inspected; bodies, keys and sensitive metadata are
discarded. Saved diagnostics contain hashes, sanitized categories, counts and waits.

Three total immediate transport attempts remain the maximum. Rate-limit waits
grow approximately 5, 15 and 35 seconds, with small positive jitter (up to 1, 3
and 5 seconds respectively). With three total attempts there are only two immediate
retries. The third/backoff-capped interval is carried across subsequent calls to
the same provider instance, including deferred retries; a successful response
resets the rate-limit streak. Non-rate-limit transport retries are unchanged.

The longer of default backoff, `Retry-After` (seconds/HTTP-date) and structured
`google.rpc.RetryInfo.retryDelay` is respected. An authoritative wait over 60
seconds is not shortened or slept inline: the existing scheduler receives a
resumable rate-limit failure, and the provider withholds further network requests
until its in-process not-before deadline. This keeps the run bounded without
retrying prematurely. A fresh future process must consult its new provider
response; this change is not a persistent quota-reset scheduler.

`GEMINI_REQUEST_DELAY_SECONDS` controls pacing after successful responses;
default **8 seconds**, valid range 0–60. Invalid/non-finite values fail with a
sanitized configuration error. Timing is confined to Gemini, not generic
generation or other providers. The live pilot used the default 8; because no
response succeeded, successful-request cooldown was tested offline, not live.

## Verified actual outcome

The first API request received HTTP **429**, with an authoritative retry delay
of **23,643 seconds** (about 6 h 34 min). No early API retry was sent. The existing
loop visited all five selected questions and its ten bounded deferred cycles;
all subsequent provider calls were withheld by the shared not-before deadline.

| Question | Actual API attempts | 429 responses | Model output | Final status |
|---|---:|---:|---|---|
| 2017 Q1 | 1 | 1 | None | provider_failure_exhausted |
| 2017 Q2 | 0 | 0 | None | provider_failure_exhausted |
| 2017 Q3 | 0 | 0 | None | provider_failure_exhausted |
| 2017 Q4 | 0 | 0 | None | provider_failure_exhausted |
| 2017 Q5 | 0 | 0 | None | provider_failure_exhausted |

Availability **0/5**; returned explanations **0**; accepted **0**; semantic/reasoning
rejections **0**; validation rejections **0**; provider/rate-limit-blocked questions
**5**. Quality acceptance is undefined (no returned explanations), not a 0% model
quality score. All five remain eligible for an explicit provider-only resume.

Q5 was withheld, not solved or semantically rejected. Its prompt/regression
coexistence rule remains unchanged, but new-model reasoning correctness cannot
be verified without output. Historical Q5 rejections remain preserved.

## Comparison (do not confound prompts with models)

| Archived run | Returned | Accepted after review | Reasoning rejections | Provider failures |
|---|---:|---:|---:|---:|
| Flash-Lite historical pilot | 5/5 | 3 | 2 | 0 |
| 3.6 Flash historical baseline | 5/5 | 4 | 1 | 0 |
| 3.6 Flash, current prompt | 0/5 | 0 | 0 | 5 |
| 3.5 Flash, current prompt | 0/5 | 0 | 0 | 5 |

The Flash-Lite Q2 candidate also failed structural length checks; its final status
was reasoning-review rejected, not an additional question. Both historical
successful runs rejected Q5's false contradiction. Their prompts differed from
the current prompt, so they are historical context, not a controlled quality
comparison. With the same current prompt neither 3.6 nor 3.5 returned output;
no arithmetic/logical-quality advantage can be concluded.

## Inspection and rerun

Snapshot: `data/merged/ai_pilot/flash35/tsa_2017.flash35.matched.json`.
Generated report: `EXPLANATION_FLASH35_PILOT_ISSUES.md`.
Generated comparison: `EXPLANATION_FLASH35_COMPARISON.md`.
HTML: `inspections_matching/flash35/tsa_2017_q1.html` through `q5.html`.
Existing HTML metadata shows `provider_pacing`: response availability, actual
rate-limit count, configured delay and sanitized events. Validation/semantic and
quality-regeneration statuses remain distinct from provider exhaustion.
All five HTML/text/JSON inspections were checked; inspection remains read-only.
The project testing skill guided focused provider regressions: **139 tests passed**
across rate-limit, pilot, deferred, semantic, explanation and matching tests;
Ruff lint/format and Git whitespace checks passed.

Once the provider's quota delay has expired, use the PowerShell environment setup
in `EXPLANATION_PILOT.md`, then explicitly resume only this pilot:

```powershell
& $pilotPython -m processors.explanations --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --resume-from 'data\merged\ai_pilot\flash35\tsa_2017.flash35.matched.json' --question 2017:1 --question 2017:2 --question 2017:3 --question 2017:4 --question 2017:5 --output 'data\merged\ai_pilot\flash35_resume\tsa_2017.flash35.matched.json' --report 'docs\ai_explanations\EXPLANATION_FLASH35_RESUME_ISSUES.md'
```

This is a manual command, not a scheduled retry. The generic CLI preserves its
existing sanitized attempt/status history; this run additionally checkpointed
Gemini pacing diagnostics without changing generic orchestration or rendering.
No broader generation is authorized or scheduled.
