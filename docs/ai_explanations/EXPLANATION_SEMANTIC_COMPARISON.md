<!-- explanation-pilot-comparison -->
# Same-question explanation pilot comparison

Local validation checks structure and obvious defects; reasoning review can reject a locally valid response. No full batch was run. Credentials are not included.

## Previous improved pilot

Generation availability: 3/5 received output. Local validation: 3 accepted / 0 not accepted among completed quality decisions.

Explanation quality among returned outputs with completed decisions: 2/3 accepted; provider failures excluded. Overall completed: 2/5.

Prompt SHA-256: `7e37255c77b0cd076f890239ea26a49c9bea020a594606d658ffadc47abbfb6a`.

| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |
|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1075 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | 1249 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | accepted | none | False | not_attempted | reasoning_review_rejected | 1456 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q5.html>) |

- Q5 reasoning-review finding: Option A still misuses contradiction despite the strengthened prompt: talent running in families is compatible with the son not being the best candidate. A is not required by the argument.
- Q2 arithmetic verified: 40*2 + 35*1 + 8*1 + 14*0.5 = 130 revenue; subtract 30 cost = 100 profit (A). No contradictory calculation remains.
- Q2 options B/C/D exceed the demonstrated profit by 2.50/15/20 respectively; E is revenue before subtracting costs. Reasons are distinct and all incorrect options are covered.
- Q4 reasoning and option-specific exclusions checked; contradiction is justified for E because the passage explicitly rejects disavowing role-model status.
- Q1/Q3 returned no candidate after three bounded transport attempts each; no quality-regeneration request was made for provider failures.
- Q5 structural validation passed, but reasoning review rejected the unsupported contradiction claim. The prompt change did not solve this semantic failure.

## Semantic safeguards pilot

Generation availability: 0/5 received output. Local validation: 0 accepted / 0 not accepted among completed quality decisions.

Explanation quality among returned outputs with completed decisions: 0/0 accepted; provider failures excluded. Overall completed: 0/5.

Prompt SHA-256: `3161f496bc34705efa86436bf88c2f5f133bb61329025d98f5d0baf8802381c8`.

| Question | Model | First validation | First rejection | Regenerated | Retry result | Final status | Length | Backtest |
|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/semantic/tsa_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/semantic/tsa_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/semantic/tsa_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/semantic/tsa_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | not_run | none | False | not_attempted | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/semantic/tsa_2017_q5.html>) |


Manual user review is required before any broader generation.
