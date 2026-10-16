<!-- explanation-pilot-report -->
# Explanation pilot — manual review required

Only the explicitly selected pilot questions were processed. Local acceptance checks structure and obvious failures; factual correctness requires manual review.

| Question | Model | First local validation | First rejection | Regenerated | Retry result | Final local validation | Final status | Characters | Backtest |
|---|---|---|---|---|---|---|---|---|---|
| 2017 Q1 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | accepted | 1293 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/baseline/gemini_pilot_2017_q1.html>) |
| 2017 Q2 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | accepted | 1479 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/baseline/gemini_pilot_2017_q2.html>) |
| 2017 Q3 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | accepted | 1747 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/baseline/gemini_pilot_2017_q3.html>) |
| 2017 Q4 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | accepted | 1109 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/baseline/gemini_pilot_2017_q4.html>) |
| 2017 Q5 | gemini-3.6-flash | accepted | none | False | not_attempted | accepted | rejected | 1370 | [HTML](<C:/Users/user/Desktop/kod_parser/inspections_matching/baseline/gemini_pilot_2017_q5.html>) |

## Accepted (4 questions)

- 2017 Q1: Local validation passed; manual reasoning review pending.
- 2017 Q2: Local validation passed; manual reasoning review pending.
- 2017 Q3: Local validation passed; manual reasoning review pending.
- 2017 Q4: Local validation passed; manual reasoning review pending.

## Rejected (1 questions)

- 2017 Q5: Option A again misuses contradiction: talent often running in families is compatible with a particular son being unlikely to be the best candidate. The option is not a required assumption.

After backtesting and validating the text-only AI explanations, the next stage is AI explanation generation for questions requiring images/visuals. That stage has not been started.
