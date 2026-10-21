<!-- explanation-pilot-comparison -->
# Same-question explanation pilot comparison

Local validation checks structure and obvious defects; reasoning review can reject a locally valid response. No full batch was run. Credentials are not included.

## Previous Flash-Lite pilot

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

## Configured-model baseline

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

## Improved prompt and bounded quality regeneration

Generation availability: 3/5 received output. Local validation: 3 accepted / 0 not accepted among completed quality decisions.

Explanation quality among returned outputs with completed decisions: 2/3 accepted; provider failures excluded. Overall completed: 2/5.

Prompt SHA-256: `7e37255c77b0cd076f890239ea26a49c9bea020a594606d658ffadc47abbfb6a`.

| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |
|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/improved/gemini_pilot_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1075 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/improved/gemini_pilot_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/improved/gemini_pilot_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1249 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/improved/gemini_pilot_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | accepted | none | False | not_attempted | reasoning_review_rejected | 1456 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/improved/gemini_pilot_2017_q5.html>) |

- Q5 reasoning-review finding: Option A still misuses contradiction despite the strengthened prompt: talent running in families is compatible with the son not being the best candidate. A is not required by the argument.
- Q2 arithmetic verified: 40*2 + 35*1 + 8*1 + 14*0.5 = 130 revenue; subtract 30 cost = 100 profit (A). No contradictory calculation remains.
- Q2 options B/C/D exceed the demonstrated profit by 2.50/15/20 respectively; E is revenue before subtracting costs. Reasons are distinct and all incorrect options are covered.
- Q4 reasoning and option-specific exclusions checked; contradiction is justified for E because the passage explicitly rejects disavowing role-model status.
- Q1/Q3 returned no candidate after three bounded transport attempts each; no quality-regeneration request was made for provider failures.
- Q5 structural validation passed, but reasoning review rejected the unsupported contradiction claim. The prompt change did not solve this semantic failure.

## Deferred transport recovery

Generation availability: 3/5 received output. Local validation: 3 accepted / 0 not accepted among completed quality decisions.

Explanation quality among returned outputs with completed decisions: 2/3 accepted; provider failures excluded. Overall completed: 2/5.

Prompt SHA-256: `7e37255c77b0cd076f890239ea26a49c9bea020a594606d658ffadc47abbfb6a`.

| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |
|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/deferred/gemini_pilot_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1075 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/deferred/gemini_pilot_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/deferred/gemini_pilot_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1249 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/deferred/gemini_pilot_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | accepted | none | False | not_attempted | reasoning_review_rejected | 1456 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections/critical_thinking_problem_solving/tsa/matching/deferred/gemini_pilot_2017_q5.html>) |

- Q5 reasoning-review finding: Option A still misuses contradiction despite the strengthened prompt: talent running in families is compatible with the son not being the best candidate. A is not required by the argument.
- Q2 arithmetic verified: 40*2 + 35*1 + 8*1 + 14*0.5 = 130 revenue; subtract 30 cost = 100 profit (A). No contradictory calculation remains.
- Q2 options B/C/D exceed the demonstrated profit by 2.50/15/20 respectively; E is revenue before subtracting costs. Reasons are distinct and all incorrect options are covered.
- Q4 reasoning and option-specific exclusions checked; contradiction is justified for E because the passage explicitly rejects disavowing role-model status.
- Q1/Q3 returned no candidate after three bounded transport attempts each; no quality-regeneration request was made for provider failures.
- Q5 structural validation passed, but reasoning review rejected the unsupported contradiction claim. The prompt change did not solve this semantic failure.

Manual user review is required before any broader generation.
