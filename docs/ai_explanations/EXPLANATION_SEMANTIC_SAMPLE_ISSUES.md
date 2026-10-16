<!-- explanation-pilot-report -->
# Explanation pilot — manual review required

Only the explicitly selected pilot/calibration questions were processed. Availability and quality describe the complete snapshot. Structural validation is not semantic approval: candidates remain pending until documented reasoning review. Provider failures are not quality rejections.

Generation availability: 0/3 questions received model output.

Explanation quality among returned outputs with a completed quality decision: 0/0 accepted. Provider failures are excluded from this denominator.

Overall completed: 0/3 accepted explanations.

Semantic review pending: 0 questions. Pending candidates are not accepted and have no valid AI Final Explanation.

This run: 0/3 requested questions received model output; 27 transport attempts and 6 deferred cycles. Previously accepted results were not regenerated.

| Question | Model | First local validation | First rejection | Quality regeneration | Quality retry result | Deferred cycles (this run) | Final local validation | Semantic review | Final status | Characters | Backtest |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2017 Q9 | gemini-3.6-flash | not_run | none | False | not_attempted | 2 | not_run | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/semantic_sample/tsa_2017_q9.html>) |
| 2017 Q16 | gemini-3.6-flash | not_run | none | False | not_attempted | 2 | not_run | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/semantic_sample/tsa_2017_q16.html>) |
| 2017 Q17 | gemini-3.6-flash | not_run | none | False | not_attempted | 2 | not_run | not_run | provider_failure_exhausted | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/semantic_sample/tsa_2017_q17.html>) |

## Provider Failure Exhausted (3 questions)

- 2017 Q9: rate_limited
- 2017 Q16: rate_limited
- 2017 Q17: rate_limited

After backtesting and validating the text-only AI explanations, the next stage is AI explanation generation for questions requiring images/visuals. That stage has not been started.
