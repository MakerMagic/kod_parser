<!-- explanation-pilot-report -->
# Explanation pilot — manual review required

Only the explicitly selected pilot questions were processed. Local acceptance checks structure and obvious failures; factual correctness requires manual review.

| Question | Model | First local validation | First rejection | Regenerated | Retry result | Final local validation | Final status | Characters | Backtest |
|---|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | not_run | none | False | not_attempted | not_run | provider_failed | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | accepted | 1075 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | not_run | none | False | not_attempted | not_run | provider_failed | unavailable | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | accepted | 1249 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | rejected | 1456 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/improved/gemini_pilot_2017_q5.html>) |

## Accepted (2 questions)

- 2017 Q2: Local validation passed; manual reasoning review pending.
- 2017 Q4: Local validation passed; manual reasoning review pending.

## Rejected (1 questions)

- 2017 Q5: Option A still misuses contradiction despite the strengthened prompt: talent running in families is compatible with the son not being the best candidate. A is not required by the argument.

## Provider Failed (2 questions)

- 2017 Q1: transient_http_failure
- 2017 Q3: transient_http_failure

After backtesting and validating the text-only AI explanations, the next stage is AI explanation generation for questions requiring images/visuals. That stage has not been started.
