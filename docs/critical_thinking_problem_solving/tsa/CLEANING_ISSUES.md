<!-- blackstone-cleaning-issues-report -->
# Blackstone cleaning issues

Clean-stage findings only. Raw parser warnings are preserved in each clean record and in RAW_PARSING_ISSUES.md; they are not copied into this report. Counts are unique records per category. No finding is not proof of fidelity.

## Body / Prompt Separation (5 records)

| Source | Year/session/paper | Question | Pages | Field | Reason | Asset | Review | Raw JSON / pointer | Clean JSON |
|---|---|---|---|---|---|---|---|---|---|
| C:\Users\user\Desktop\kod_parser\acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford specimen.pdf | unavailable/unavailable/unavailable | 13 | {'start_page': 9, 'end_page': 9} | main_question | ambiguous_body_question_split: No single complete explicit prompt; all supplied context retained in Main Body. | unavailable | yes | C:\Users\user\Desktop\kod_parser\data\raw\blackstone\TSA Oxford specimen-860a03b06ee0.raw.json /questions/12 | C:\Users\user\Desktop\kod_parser\data\clean\blackstone\TSA Oxford specimen-860a03b06ee0.clean.json |
| C:\Users\user\Desktop\kod_parser\acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford specimen.pdf | unavailable/unavailable/unavailable | 18 | {'start_page': 12, 'end_page': 12} | main_question | ambiguous_body_question_split: No single complete explicit prompt; all supplied context retained in Main Body. | unavailable | yes | C:\Users\user\Desktop\kod_parser\data\raw\blackstone\TSA Oxford specimen-860a03b06ee0.raw.json /questions/17 | C:\Users\user\Desktop\kod_parser\data\clean\blackstone\TSA Oxford specimen-860a03b06ee0.clean.json |
| C:\Users\user\Desktop\kod_parser\acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford specimen.pdf | unavailable/unavailable/unavailable | 2 | {'start_page': 3, 'end_page': 3} | main_question | ambiguous_body_question_split: No single complete explicit prompt; all supplied context retained in Main Body. | unavailable | yes | C:\Users\user\Desktop\kod_parser\data\raw\blackstone\TSA Oxford specimen-860a03b06ee0.raw.json /questions/1 | C:\Users\user\Desktop\kod_parser\data\clean\blackstone\TSA Oxford specimen-860a03b06ee0.clean.json |
| C:\Users\user\Desktop\kod_parser\acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford specimen.pdf | unavailable/unavailable/unavailable | 20 | {'start_page': 13, 'end_page': 13} | main_question | ambiguous_body_question_split: No single complete explicit prompt; all supplied context retained in Main Body. | unavailable | yes | C:\Users\user\Desktop\kod_parser\data\raw\blackstone\TSA Oxford specimen-860a03b06ee0.raw.json /questions/19 | C:\Users\user\Desktop\kod_parser\data\clean\blackstone\TSA Oxford specimen-860a03b06ee0.clean.json |
| C:\Users\user\Desktop\kod_parser\acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford specimen.pdf | unavailable/unavailable/unavailable | 7 | {'start_page': 7, 'end_page': 7} | main_question | ambiguous_body_question_split: No single complete explicit prompt; all supplied context retained in Main Body. | unavailable | yes | C:\Users\user\Desktop\kod_parser\data\raw\blackstone\TSA Oxford specimen-860a03b06ee0.raw.json /questions/6 | C:\Users\user\Desktop\kod_parser\data\clean\blackstone\TSA Oxford specimen-860a03b06ee0.clean.json |

## Text / Expression Ordering (1 records)

| Source | Year/session/paper | Question | Pages | Field | Reason | Asset | Review | Raw JSON / pointer | Clean JSON |
|---|---|---|---|---|---|---|---|---|---|
| C:\Users\user\Desktop\kod_parser\acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford 2020.pdf | 2020/unavailable/D512/11 | 12 | {'start_page': 9, 'end_page': 9} | question_text | isolated_symbol_ordering_unresolved: An isolated symbol may belong inside an expression; its original line retained, not repositioned. | unavailable | yes | C:\Users\user\Desktop\kod_parser\data\raw\blackstone\TSA Oxford 2020-ca4ee526afb0.raw.json /questions/11 | C:\Users\user\Desktop\kod_parser\data\clean\blackstone\TSA Oxford 2020-ca4ee526afb0.clean.json |

## Unresolved Encoding (1 records)

| Source | Year/session/paper | Question | Pages | Field | Reason | Asset | Review | Raw JSON / pointer | Clean JSON |
|---|---|---|---|---|---|---|---|---|---|
| C:\Users\user\Desktop\kod_parser\acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford 2021.pdf | 2021/unavailable/4502/11 | 7 | {'start_page': 6, 'end_page': 6} | question_text | encoding_artifact_unresolved: Encoding tokens/control glyphs have no verified replacement; content retained. | unavailable | yes | C:\Users\user\Desktop\kod_parser\data\raw\blackstone\TSA Oxford 2021-de4797cbdaeb.raw.json /questions/6 | C:\Users\user\Desktop\kod_parser\data\clean\blackstone\TSA Oxford 2021-de4797cbdaeb.clean.json |

## Visual Placement / Ordering (1 records)

| Source | Year/session/paper | Question | Pages | Field | Reason | Asset | Review | Raw JSON / pointer | Clean JSON |
|---|---|---|---|---|---|---|---|---|---|
| C:\Users\user\Desktop\kod_parser\acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford specimen.pdf | unavailable/unavailable/unavailable | 25 | {'start_page': 16, 'end_page': 16} | main_body | visual_placement_unresolved: Asset has no reliable displayed option/body placement; preserved without reassignment.; visual_text_ownership_unresolved: Stored visual-text ownership lacks safe body asset/page/bounds evidence; text retained for review. | assets/860a03b06ee073f9b68e/blackstone_unknown-year_q025_r025_p016_view_01_07281ce2f9.png | yes | C:\Users\user\Desktop\kod_parser\data\raw\blackstone\TSA Oxford specimen-860a03b06ee0.raw.json /questions/24 | C:\Users\user\Desktop\kod_parser\data\clean\blackstone\TSA Oxford specimen-860a03b06ee0.clean.json |

