<!-- explanation-pilot-comparison -->
# Same-question explanation pilot comparison

Local validation checks structure and obvious defects; reasoning review can reject a locally valid response. No full batch was run. Credentials are not included.

## Flash-Lite historical pilot

Generation availability: 5/5 received output. Local validation: 4 accepted / 1 not accepted among completed quality decisions.

Explanation quality among returned outputs with completed decisions: 3/5 accepted; provider failures excluded. Overall completed: 3/5.

Prompt SHA-256: `8f598bbbe6192a579358da08e8d0f1083cad35432443a740daba8bb6188cbfef`.

| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |
|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.5-flash-lite | accepted | none | False | not_attempted | accepted | 1544 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/gemini_pilot_2017_q1.html>) |
| 2017 Q2 | gemini-3.5-flash-lite | rejected | explanation_too_long | False | not_attempted | reasoning_review_rejected | 2457 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/gemini_pilot_2017_q2.html>) |
| 2017 Q3 | gemini-3.5-flash-lite | accepted | none | False | not_attempted | accepted | 1652 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/gemini_pilot_2017_q3.html>) |
| 2017 Q4 | gemini-3.5-flash-lite | accepted | none | False | not_attempted | accepted | 1550 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/gemini_pilot_2017_q4.html>) |
| 2017 Q5 | gemini-3.5-flash-lite | accepted | none | False | not_attempted | reasoning_review_rejected | 1387 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/gemini_pilot_2017_q5.html>) |

- Q2 reasoning-review finding: Exceeds 2000 characters and preserves contradictory draft arithmetic before correcting itself; incorrect-option reasons speculate about unverified calculation errors.
- Q5 reasoning-review finding: Option A analysis incorrectly claims a contradiction: talent running in families does not imply the son is the best available candidate. The relevant reason is that A is unnecessary to the argument.

## 3.6 Flash historical baseline

Generation availability: 5/5 received output. Local validation: 5 accepted / 0 not accepted among completed quality decisions.

Explanation quality among returned outputs with completed decisions: 4/5 accepted; provider failures excluded. Overall completed: 4/5.

Prompt SHA-256: `8f598bbbe6192a579358da08e8d0f1083cad35432443a740daba8bb6188cbfef`.

| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |
|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1293 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/baseline/gemini_pilot_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1479 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/baseline/gemini_pilot_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1747 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/baseline/gemini_pilot_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1109 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/baseline/gemini_pilot_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | accepted | none | False | not_attempted | reasoning_review_rejected | 1370 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/baseline/gemini_pilot_2017_q5.html>) |

- Q5 reasoning-review finding: Option A again misuses contradiction: talent often running in families is compatible with a particular son being unlikely to be the best candidate. The option is not a required assumption.
- Q2 calculation verified: morning revenue 80+35, afternoon revenue 8+7, total revenue 130 less cost 30 gives profit 100 (A). No contradictory arithmetic remains. Wrong options B/C/D/E correspond to 102.50/115/120/130, with distinct exclusions.
- Q1/Q3/Q4 explanations cover every incorrect option with distinct reasons; no duplicate-reason or length validation failures were detected.
- Q5 repeats the same unsupported contradiction claim about inherited business talent seen in the earlier pilot; structural validation does not establish semantic correctness.

## 3.6 Flash same current prompt

Generation availability: 0/5 received output. Local validation: 0 accepted / 0 not accepted among completed quality decisions.

Explanation quality among returned outputs with completed decisions: 0/0 accepted; provider failures excluded. Overall completed: 0/5.

Prompt SHA-256: `3161f496bc34705efa86436bf88c2f5f133bb61329025d98f5d0baf8802381c8`.

| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |
|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/semantic/tsa_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/semantic/tsa_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/semantic/tsa_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/semantic/tsa_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/semantic/tsa_2017_q5.html>) |


## 3.5 Flash current pilot

Generation availability: 0/5 received output. Local validation: 0 accepted / 0 not accepted among completed quality decisions.

Explanation quality among returned outputs with completed decisions: 0/0 accepted; provider failures excluded. Overall completed: 0/5.

Prompt SHA-256: `3161f496bc34705efa86436bf88c2f5f133bb61329025d98f5d0baf8802381c8`.

| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |
|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.5-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/flash35/tsa_2017_q1.html>) |
| 2017 Q2 | gemini-3.5-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/flash35/tsa_2017_q2.html>) |
| 2017 Q3 | gemini-3.5-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/flash35/tsa_2017_q3.html>) |
| 2017 Q4 | gemini-3.5-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/flash35/tsa_2017_q4.html>) |
| 2017 Q5 | gemini-3.5-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/flash35/tsa_2017_q5.html>) |

- Provider returned HTTP 429 with RetryInfo delay 23643 seconds. One actual API attempt; remaining calls withheld to respect the provider not-before time. No new explanation-quality comparison or Q5 semantic verification is possible.

Manual user review is required before any broader generation.
