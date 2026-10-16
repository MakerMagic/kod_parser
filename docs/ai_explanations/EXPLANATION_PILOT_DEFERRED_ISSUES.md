<!-- explanation-pilot-report -->
# Explanation pilot — manual review required

Only the explicitly selected pilot questions were processed. Availability and quality describe the complete resumed pilot snapshot, including preserved results. Local acceptance checks structure and obvious failures; factual correctness requires manual review.

Generation availability: 3/5 questions received model output.

Explanation quality among returned outputs with a completed quality decision: 2/3 accepted. Provider failures are excluded from this denominator.

Overall completed: 2/5 accepted explanations.

This run: 0/2 requested questions received model output; 18 transport attempts and 4 deferred cycles. Previously accepted results were not regenerated.

| Question | Model | First local validation | First rejection | Quality regeneration | Quality retry result | Deferred cycles (this run) | Final local validation | Final status | Characters | Backtest |
|---|---|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | not_run | none | False | not_attempted | 2 | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/deferred/gemini_pilot_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | accepted | none | False | not_attempted | 0 | accepted | accepted | 1075 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/deferred/gemini_pilot_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | not_run | none | False | not_attempted | 2 | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/deferred/gemini_pilot_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | accepted | none | False | not_attempted | 0 | accepted | accepted | 1249 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/deferred/gemini_pilot_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | accepted | none | False | not_attempted | 0 | accepted | reasoning_review_rejected | 1456 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/deferred/gemini_pilot_2017_q5.html>) |

## Accepted (2 questions)

- 2017 Q2: Local validation passed; manual reasoning review pending.
- 2017 Q4: Local validation passed; manual reasoning review pending.

## Reasoning Review Rejected (1 questions)

- 2017 Q5: Option A still misuses contradiction despite the strengthened prompt: talent running in families is compatible with the son not being the best candidate. A is not required by the argument.

## Provider Failure Exhausted (2 questions)

- 2017 Q1: rate_limited
- 2017 Q3: rate_limited

After backtesting and validating the text-only AI explanations, the next stage is AI explanation generation for questions requiring images/visuals. That stage has not been started.
