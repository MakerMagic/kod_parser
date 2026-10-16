<!-- explanation-pilot-report -->
# Explanation pilot — manual review required

Only the explicitly selected pilot/calibration questions were processed. Availability and quality describe the complete snapshot. Structural validation is not semantic approval: candidates remain pending until documented reasoning review. Provider failures are not quality rejections.

Generation availability: 0/5 questions received model output.

Explanation quality among returned outputs with a completed quality decision: 0/0 accepted. Provider failures are excluded from this denominator.

Overall completed: 0/5 accepted explanations.

Semantic review pending: 0 questions. Pending candidates are not accepted and have no valid AI Final Explanation.

This run: 0/5 requested questions received model output; 1 transport attempts and 10 deferred cycles. Previously accepted results were not regenerated.

| Question | Model | First local validation | First rejection | Quality regeneration | Quality retry result | Deferred cycles (this run) | Final local validation | Semantic review | Final status | Characters | Backtest |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.5-flash | not_run | none | False | not_attempted | 2 | not_run | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/flash35/tsa_2017_q1.html>) |
| 2017 Q2 | gemini-3.5-flash | not_run | none | False | not_attempted | 2 | not_run | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/flash35/tsa_2017_q2.html>) |
| 2017 Q3 | gemini-3.5-flash | not_run | none | False | not_attempted | 2 | not_run | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/flash35/tsa_2017_q3.html>) |
| 2017 Q4 | gemini-3.5-flash | not_run | none | False | not_attempted | 2 | not_run | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/flash35/tsa_2017_q4.html>) |
| 2017 Q5 | gemini-3.5-flash | not_run | none | False | not_attempted | 2 | not_run | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/flash35/tsa_2017_q5.html>) |

## Provider Failure Exhausted (5 questions)

- 2017 Q1: rate_limited
- 2017 Q2: rate_limited
- 2017 Q3: rate_limited
- 2017 Q4: rate_limited
- 2017 Q5: rate_limited

After backtesting and validating the text-only AI explanations, the next stage is AI explanation generation for questions requiring images/visuals. That stage has not been started.
