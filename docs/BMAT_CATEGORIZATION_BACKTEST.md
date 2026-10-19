# BMAT categorization backtesting

Reads persisted CLEAN-based task attribution with hash-verified matching context where available. Correct Answer, Main/Final Explanation and source screenshots are shown together; attribution does not infer categories from explanation wording. BMAT exclusions have precedence. All records remain inspectable.

Reproduce: `python -m categorization.bmat run` (or `python -m processors.bmat categorize run`). Refresh exclusion evidence independently with `python -m parsers.bmat.skip_rules data/raw/bmat --overwrite`, then regenerate CLEAN before categorization. No PDF or answer matching runs in categorization.

- [Inspection index](../inspections_bmat_categorization/index.html)
- [Current issues](BMAT_CATEGORIZATION_ISSUES.md)

| Year | Question | Status | Result / evidence |
|---|---|---|---|
| 2003 | [1](../inspections_bmat_categorization/2003_q001.html) | needs_review | Upstream defects remain: visual_neighbor_boundary_uncertain |
| 2003 | [2](../inspections_bmat_categorization/2003_q002.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2003 | [3](../inspections_bmat_categorization/2003_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2003 | [4](../inspections_bmat_categorization/2003_q004.html) | intentional_skip | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2003 | [5](../inspections_bmat_categorization/2003_q005.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | [6](../inspections_bmat_categorization/2003_q006.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2003 | [7](../inspections_bmat_categorization/2003_q007.html) | intentional_skip | Question falls in declared shared-information interval 7--12. |
| 2003 | [8](../inspections_bmat_categorization/2003_q008.html) | intentional_skip | Question falls in declared shared-information interval 7--12. |
| 2003 | [9](../inspections_bmat_categorization/2003_q009.html) | intentional_skip | Question falls in declared shared-information interval 7--12. |
| 2003 | [10](../inspections_bmat_categorization/2003_q010.html) | intentional_skip | Question falls in declared shared-information interval 7--12. |
| 2003 | [11](../inspections_bmat_categorization/2003_q011.html) | intentional_skip | Question falls in declared shared-information interval 7--12. |
| 2003 | [12](../inspections_bmat_categorization/2003_q012.html) | intentional_skip | Question falls in declared shared-information interval 7--12. |
| 2003 | [13](../inspections_bmat_categorization/2003_q013.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2003 | [14](../inspections_bmat_categorization/2003_q014.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2003 | [15](../inspections_bmat_categorization/2003_q015.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2003 | [16](../inspections_bmat_categorization/2003_q016.html) | intentional_skip | The requested mathematical result depends on an explicit symbolic relation/function. |
| 2003 | [17](../inspections_bmat_categorization/2003_q017.html) | intentional_skip | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2003 | [18](../inspections_bmat_categorization/2003_q018.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | [19](../inspections_bmat_categorization/2003_q019.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2003 | [20](../inspections_bmat_categorization/2003_q020.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2003 | [21](../inspections_bmat_categorization/2003_q021.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | [22](../inspections_bmat_categorization/2003_q022.html) | intentional_skip | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2003 | [23](../inspections_bmat_categorization/2003_q023.html) | supported | Critical Thinking / Identifying an Assumption |
| 2003 | [24](../inspections_bmat_categorization/2003_q024.html) | intentional_skip | Question falls in declared shared-information interval 24--27. |
| 2003 | [25](../inspections_bmat_categorization/2003_q025.html) | intentional_skip | Question falls in declared shared-information interval 24--27. |
| 2003 | [26](../inspections_bmat_categorization/2003_q026.html) | intentional_skip | Question falls in declared shared-information interval 24--27. |
| 2003 | [27](../inspections_bmat_categorization/2003_q027.html) | intentional_skip | Question falls in declared shared-information interval 24--27. |
| 2003 | [28](../inspections_bmat_categorization/2003_q028.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2003 | [29](../inspections_bmat_categorization/2003_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2003 | [30](../inspections_bmat_categorization/2003_q030.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2003 | [31](../inspections_bmat_categorization/2003_q031.html) | intentional_skip | The request selects multiple separate choices, not one combination-valued answer. |
| 2003 | [32](../inspections_bmat_categorization/2003_q032.html) | supported | Critical Thinking / Identifying an Assumption |
| 2003 | [33](../inspections_bmat_categorization/2003_q033.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2003 | [34](../inspections_bmat_categorization/2003_q034.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2003 | [35](../inspections_bmat_categorization/2003_q035.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2003 | [36](../inspections_bmat_categorization/2003_q036.html) | intentional_skip | Question falls in declared shared-information interval 36--40. |
| 2003 | [37](../inspections_bmat_categorization/2003_q037.html) | intentional_skip | Question falls in declared shared-information interval 36--40. |
| 2003 | [38](../inspections_bmat_categorization/2003_q038.html) | intentional_skip | Question falls in declared shared-information interval 36--40. |
| 2003 | [39](../inspections_bmat_categorization/2003_q039.html) | intentional_skip | Question falls in declared shared-information interval 36--40. |
| 2003 | [40](../inspections_bmat_categorization/2003_q040.html) | intentional_skip | Question falls in declared shared-information interval 36--40. |
| 2004 | [1](../inspections_bmat_categorization/2004_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [2](../inspections_bmat_categorization/2004_q002.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2004 | [3](../inspections_bmat_categorization/2004_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [4](../inspections_bmat_categorization/2004_q004.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2004 | [5](../inspections_bmat_categorization/2004_q005.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [6](../inspections_bmat_categorization/2004_q006.html) | supported | Critical Thinking / Identifying an Assumption |
| 2004 | [7](../inspections_bmat_categorization/2004_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [8](../inspections_bmat_categorization/2004_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2004 | [9](../inspections_bmat_categorization/2004_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2004 | [10](../inspections_bmat_categorization/2004_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2004 | [11](../inspections_bmat_categorization/2004_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2004 | [12](../inspections_bmat_categorization/2004_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [13](../inspections_bmat_categorization/2004_q013.html) | intentional_skip | Answer alternatives compare necessity and sufficiency of the same condition. |
| 2004 | [14](../inspections_bmat_categorization/2004_q014.html) | needs_review | Upstream defects remain: visual_component_association_uncertain |
| 2004 | [15](../inspections_bmat_categorization/2004_q015.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2004 | [16](../inspections_bmat_categorization/2004_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [17](../inspections_bmat_categorization/2004_q017.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2004 | [18](../inspections_bmat_categorization/2004_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [19](../inspections_bmat_categorization/2004_q019.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2004 | [20](../inspections_bmat_categorization/2004_q020.html) | intentional_skip | Question falls in declared shared-information interval 20--23. |
| 2004 | [21](../inspections_bmat_categorization/2004_q021.html) | intentional_skip | Question falls in declared shared-information interval 20--23. |
| 2004 | [22](../inspections_bmat_categorization/2004_q022.html) | intentional_skip | Question falls in declared shared-information interval 20--23. |
| 2004 | [23](../inspections_bmat_categorization/2004_q023.html) | intentional_skip | Question falls in declared shared-information interval 20--23. |
| 2004 | [24](../inspections_bmat_categorization/2004_q024.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2004 | [25](../inspections_bmat_categorization/2004_q025.html) | supported | Critical Thinking / Identifying an Assumption |
| 2004 | [26](../inspections_bmat_categorization/2004_q026.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [27](../inspections_bmat_categorization/2004_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [28](../inspections_bmat_categorization/2004_q028.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [29](../inspections_bmat_categorization/2004_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2004 | [30](../inspections_bmat_categorization/2004_q030.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2004 | [31](../inspections_bmat_categorization/2004_q031.html) | intentional_skip | The request selects multiple separate choices, not one combination-valued answer. |
| 2004 | [32](../inspections_bmat_categorization/2004_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2004 | [33](../inspections_bmat_categorization/2004_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2004 | [34](../inspections_bmat_categorization/2004_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2004 | [35](../inspections_bmat_categorization/2004_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2005 | [1](../inspections_bmat_categorization/2005_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2005 | [2](../inspections_bmat_categorization/2005_q002.html) | supported | Critical Thinking / Identifying an Assumption |
| 2005 | [3](../inspections_bmat_categorization/2005_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2005 | [4](../inspections_bmat_categorization/2005_q004.html) | intentional_skip | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2005 | [5](../inspections_bmat_categorization/2005_q005.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2005 | [6](../inspections_bmat_categorization/2005_q006.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2005 | [7](../inspections_bmat_categorization/2005_q007.html) | intentional_skip | Question falls in declared shared-information interval 7--10. |
| 2005 | [8](../inspections_bmat_categorization/2005_q008.html) | intentional_skip | Question falls in declared shared-information interval 7--10. |
| 2005 | [9](../inspections_bmat_categorization/2005_q009.html) | intentional_skip | Question falls in declared shared-information interval 7--10. |
| 2005 | [10](../inspections_bmat_categorization/2005_q010.html) | intentional_skip | Question falls in declared shared-information interval 7--10. |
| 2005 | [11](../inspections_bmat_categorization/2005_q011.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2005 | [12](../inspections_bmat_categorization/2005_q012.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2005 | [13](../inspections_bmat_categorization/2005_q013.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2005 | [14](../inspections_bmat_categorization/2005_q014.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2005 | [15](../inspections_bmat_categorization/2005_q015.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2005 | [16](../inspections_bmat_categorization/2005_q016.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2005 | [17](../inspections_bmat_categorization/2005_q017.html) | intentional_skip | Select missing textual/argument content rather than solve a numeric blank. |
| 2005 | [18](../inspections_bmat_categorization/2005_q018.html) | supported | Critical Thinking / Identifying an Assumption |
| 2005 | [19](../inspections_bmat_categorization/2005_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--23. |
| 2005 | [20](../inspections_bmat_categorization/2005_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--23. |
| 2005 | [21](../inspections_bmat_categorization/2005_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--23. |
| 2005 | [22](../inspections_bmat_categorization/2005_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--23. |
| 2005 | [23](../inspections_bmat_categorization/2005_q023.html) | intentional_skip | Question falls in declared shared-information interval 19--23. |
| 2005 | [24](../inspections_bmat_categorization/2005_q024.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2005 | [25](../inspections_bmat_categorization/2005_q025.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2005 | [26](../inspections_bmat_categorization/2005_q026.html) | intentional_skip | Answer alternatives compare necessity and sufficiency of the same condition. |
| 2005 | [27](../inspections_bmat_categorization/2005_q027.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2005 | [28](../inspections_bmat_categorization/2005_q028.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2005 | [29](../inspections_bmat_categorization/2005_q029.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2005 | [30](../inspections_bmat_categorization/2005_q030.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2005 | [31](../inspections_bmat_categorization/2005_q031.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2005 | [32](../inspections_bmat_categorization/2005_q032.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2005 | [33](../inspections_bmat_categorization/2005_q033.html) | intentional_skip | Question falls in declared shared-information interval 33--35. |
| 2005 | [34](../inspections_bmat_categorization/2005_q034.html) | intentional_skip | Question falls in declared shared-information interval 33--35. |
| 2005 | [35](../inspections_bmat_categorization/2005_q035.html) | intentional_skip | Question falls in declared shared-information interval 33--35. |
| 2006 | [1](../inspections_bmat_categorization/2006_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2006 | [2](../inspections_bmat_categorization/2006_q002.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2006 | [3](../inspections_bmat_categorization/2006_q003.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2006 | [4](../inspections_bmat_categorization/2006_q004.html) | supported | Critical Thinking / Identifying an Assumption |
| 2006 | [5](../inspections_bmat_categorization/2006_q005.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [6](../inspections_bmat_categorization/2006_q006.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2006 | [7](../inspections_bmat_categorization/2006_q007.html) | intentional_skip | Question falls in declared shared-information interval 7--10. |
| 2006 | [8](../inspections_bmat_categorization/2006_q008.html) | intentional_skip | Question falls in declared shared-information interval 7--10. |
| 2006 | [9](../inspections_bmat_categorization/2006_q009.html) | intentional_skip | Question falls in declared shared-information interval 7--10. |
| 2006 | [10](../inspections_bmat_categorization/2006_q010.html) | intentional_skip | Question falls in declared shared-information interval 7--10. |
| 2006 | [11](../inspections_bmat_categorization/2006_q011.html) | intentional_skip | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2006 | [12](../inspections_bmat_categorization/2006_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2006 | [13](../inspections_bmat_categorization/2006_q013.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [14](../inspections_bmat_categorization/2006_q014.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2006 | [15](../inspections_bmat_categorization/2006_q015.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [16](../inspections_bmat_categorization/2006_q016.html) | supported | Critical Thinking / Identifying an Assumption |
| 2006 | [17](../inspections_bmat_categorization/2006_q017.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2006 | [18](../inspections_bmat_categorization/2006_q018.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2006 | [19](../inspections_bmat_categorization/2006_q019.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2006 | [20](../inspections_bmat_categorization/2006_q020.html) | intentional_skip | Question falls in declared shared-information interval 20--22. |
| 2006 | [21](../inspections_bmat_categorization/2006_q021.html) | intentional_skip | Question falls in declared shared-information interval 20--22. |
| 2006 | [22](../inspections_bmat_categorization/2006_q022.html) | intentional_skip | Question falls in declared shared-information interval 20--22. |
| 2006 | [23](../inspections_bmat_categorization/2006_q023.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2006 | [24](../inspections_bmat_categorization/2006_q024.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2006 | [25](../inspections_bmat_categorization/2006_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2006 | [26](../inspections_bmat_categorization/2006_q026.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2006 | [27](../inspections_bmat_categorization/2006_q027.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2006 | [28](../inspections_bmat_categorization/2006_q028.html) | intentional_skip | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2006 | [29](../inspections_bmat_categorization/2006_q029.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2006 | [30](../inspections_bmat_categorization/2006_q030.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2006 | [31](../inspections_bmat_categorization/2006_q031.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2006 | [32](../inspections_bmat_categorization/2006_q032.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2006 | [33](../inspections_bmat_categorization/2006_q033.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2006 | [34](../inspections_bmat_categorization/2006_q034.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2006 | [35](../inspections_bmat_categorization/2006_q035.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2007 | [1](../inspections_bmat_categorization/2007_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2007 | [2](../inspections_bmat_categorization/2007_q002.html) | intentional_skip | Select missing textual/argument content rather than solve a numeric blank. |
| 2007 | [3](../inspections_bmat_categorization/2007_q003.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [4](../inspections_bmat_categorization/2007_q004.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2007 | [5](../inspections_bmat_categorization/2007_q005.html) | intentional_skip | 
Source: Department |
| 2007 | [6](../inspections_bmat_categorization/2007_q006.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2007 | [7](../inspections_bmat_categorization/2007_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2007 | [8](../inspections_bmat_categorization/2007_q008.html) | intentional_skip | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2007 | [9](../inspections_bmat_categorization/2007_q009.html) | intentional_skip | Question falls in declared shared-information interval 9--12. |
| 2007 | [10](../inspections_bmat_categorization/2007_q010.html) | intentional_skip | Question falls in declared shared-information interval 9--12. |
| 2007 | [11](../inspections_bmat_categorization/2007_q011.html) | intentional_skip | Question falls in declared shared-information interval 9--12. |
| 2007 | [12](../inspections_bmat_categorization/2007_q012.html) | intentional_skip | Question falls in declared shared-information interval 9--12. |
| 2007 | [13](../inspections_bmat_categorization/2007_q013.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [14](../inspections_bmat_categorization/2007_q014.html) | intentional_skip | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2007 | [15](../inspections_bmat_categorization/2007_q015.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2007 | [16](../inspections_bmat_categorization/2007_q016.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2007 | [17](../inspections_bmat_categorization/2007_q017.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2007 | [18](../inspections_bmat_categorization/2007_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2007 | [19](../inspections_bmat_categorization/2007_q019.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2007 | [20](../inspections_bmat_categorization/2007_q020.html) | intentional_skip | Question falls in declared shared-information interval 20--23. |
| 2007 | [21](../inspections_bmat_categorization/2007_q021.html) | intentional_skip | Question falls in declared shared-information interval 20--23. |
| 2007 | [22](../inspections_bmat_categorization/2007_q022.html) | intentional_skip | Question falls in declared shared-information interval 20--23. |
| 2007 | [23](../inspections_bmat_categorization/2007_q023.html) | intentional_skip | Question falls in declared shared-information interval 20--23. |
| 2007 | [24](../inspections_bmat_categorization/2007_q024.html) | intentional_skip | Answer alternatives compare necessity and sufficiency of the same condition. |
| 2007 | [25](../inspections_bmat_categorization/2007_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2007 | [26](../inspections_bmat_categorization/2007_q026.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2007 | [27](../inspections_bmat_categorization/2007_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2007 | [28](../inspections_bmat_categorization/2007_q028.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2007 | [29](../inspections_bmat_categorization/2007_q029.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2007 | [30](../inspections_bmat_categorization/2007_q030.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [31](../inspections_bmat_categorization/2007_q031.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2007 | [32](../inspections_bmat_categorization/2007_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2007 | [33](../inspections_bmat_categorization/2007_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2007 | [34](../inspections_bmat_categorization/2007_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2007 | [35](../inspections_bmat_categorization/2007_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2008 | [1](../inspections_bmat_categorization/2008_q001.html) | intentional_skip | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2008 | [2](../inspections_bmat_categorization/2008_q002.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2008 | [3](../inspections_bmat_categorization/2008_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [4](../inspections_bmat_categorization/2008_q004.html) | intentional_skip | Select missing textual/argument content rather than solve a numeric blank. |
| 2008 | [5](../inspections_bmat_categorization/2008_q005.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [6](../inspections_bmat_categorization/2008_q006.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [7](../inspections_bmat_categorization/2008_q007.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2008 | [8](../inspections_bmat_categorization/2008_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2008 | [9](../inspections_bmat_categorization/2008_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2008 | [10](../inspections_bmat_categorization/2008_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2008 | [11](../inspections_bmat_categorization/2008_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2008 | [12](../inspections_bmat_categorization/2008_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [13](../inspections_bmat_categorization/2008_q013.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [14](../inspections_bmat_categorization/2008_q014.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [15](../inspections_bmat_categorization/2008_q015.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2008 | [16](../inspections_bmat_categorization/2008_q016.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2008 | [17](../inspections_bmat_categorization/2008_q017.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [18](../inspections_bmat_categorization/2008_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [19](../inspections_bmat_categorization/2008_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2008 | [20](../inspections_bmat_categorization/2008_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2008 | [21](../inspections_bmat_categorization/2008_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2008 | [22](../inspections_bmat_categorization/2008_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2008 | [23](../inspections_bmat_categorization/2008_q023.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [24](../inspections_bmat_categorization/2008_q024.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2008 | [25](../inspections_bmat_categorization/2008_q025.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2008 | [26](../inspections_bmat_categorization/2008_q026.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2008 | [27](../inspections_bmat_categorization/2008_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [28](../inspections_bmat_categorization/2008_q028.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2008 | [29](../inspections_bmat_categorization/2008_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [30](../inspections_bmat_categorization/2008_q030.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2008 | [31](../inspections_bmat_categorization/2008_q031.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2008 | [32](../inspections_bmat_categorization/2008_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2008 | [33](../inspections_bmat_categorization/2008_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2008 | [34](../inspections_bmat_categorization/2008_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2008 | [35](../inspections_bmat_categorization/2008_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2009 | [1](../inspections_bmat_categorization/2009_q001.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [2](../inspections_bmat_categorization/2009_q002.html) | intentional_skip | The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw. |
| 2009 | [3](../inspections_bmat_categorization/2009_q003.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [4](../inspections_bmat_categorization/2009_q004.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2009 | [5](../inspections_bmat_categorization/2009_q005.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2009 | [6](../inspections_bmat_categorization/2009_q006.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2009 | [7](../inspections_bmat_categorization/2009_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2009 | [8](../inspections_bmat_categorization/2009_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--10. |
| 2009 | [9](../inspections_bmat_categorization/2009_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--10. |
| 2009 | [10](../inspections_bmat_categorization/2009_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--10. |
| 2009 | [11](../inspections_bmat_categorization/2009_q011.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2009 | [12](../inspections_bmat_categorization/2009_q012.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2009 | [13](../inspections_bmat_categorization/2009_q013.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2009 | [14](../inspections_bmat_categorization/2009_q014.html) | supported | Critical Thinking / Identifying an Assumption |
| 2009 | [15](../inspections_bmat_categorization/2009_q015.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [16](../inspections_bmat_categorization/2009_q016.html) | intentional_skip | Question falls in declared shared-information interval 16--20. |
| 2009 | [17](../inspections_bmat_categorization/2009_q017.html) | intentional_skip | Question falls in declared shared-information interval 16--20. |
| 2009 | [18](../inspections_bmat_categorization/2009_q018.html) | intentional_skip | Question falls in declared shared-information interval 16--20. |
| 2009 | [19](../inspections_bmat_categorization/2009_q019.html) | intentional_skip | Question falls in declared shared-information interval 16--20. |
| 2009 | [20](../inspections_bmat_categorization/2009_q020.html) | intentional_skip | Question falls in declared shared-information interval 16--20. |
| 2009 | [21](../inspections_bmat_categorization/2009_q021.html) | intentional_skip | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2009 | [22](../inspections_bmat_categorization/2009_q022.html) | supported | Critical Thinking / Identifying an Assumption |
| 2009 | [23](../inspections_bmat_categorization/2009_q023.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2009 | [24](../inspections_bmat_categorization/2009_q024.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2009 | [25](../inspections_bmat_categorization/2009_q025.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [26](../inspections_bmat_categorization/2009_q026.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2009 | [27](../inspections_bmat_categorization/2009_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2009 | [28](../inspections_bmat_categorization/2009_q028.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2009 | [29](../inspections_bmat_categorization/2009_q029.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2009 | [30](../inspections_bmat_categorization/2009_q030.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2009 | [31](../inspections_bmat_categorization/2009_q031.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2009 | [32](../inspections_bmat_categorization/2009_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2009 | [33](../inspections_bmat_categorization/2009_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2009 | [34](../inspections_bmat_categorization/2009_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2009 | [35](../inspections_bmat_categorization/2009_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2010 | [1](../inspections_bmat_categorization/2010_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [2](../inspections_bmat_categorization/2010_q002.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2010 | [3](../inspections_bmat_categorization/2010_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [4](../inspections_bmat_categorization/2010_q004.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2010 | [5](../inspections_bmat_categorization/2010_q005.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [6](../inspections_bmat_categorization/2010_q006.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2010 | [7](../inspections_bmat_categorization/2010_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [8](../inspections_bmat_categorization/2010_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2010 | [9](../inspections_bmat_categorization/2010_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2010 | [10](../inspections_bmat_categorization/2010_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2010 | [11](../inspections_bmat_categorization/2010_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2010 | [12](../inspections_bmat_categorization/2010_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [13](../inspections_bmat_categorization/2010_q013.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2010 | [14](../inspections_bmat_categorization/2010_q014.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [15](../inspections_bmat_categorization/2010_q015.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2010 | [16](../inspections_bmat_categorization/2010_q016.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2010 | [17](../inspections_bmat_categorization/2010_q017.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2010 | [18](../inspections_bmat_categorization/2010_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [19](../inspections_bmat_categorization/2010_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2010 | [20](../inspections_bmat_categorization/2010_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2010 | [21](../inspections_bmat_categorization/2010_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2010 | [22](../inspections_bmat_categorization/2010_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2010 | [23](../inspections_bmat_categorization/2010_q023.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [24](../inspections_bmat_categorization/2010_q024.html) | supported | Critical Thinking / Identifying an Assumption |
| 2010 | [25](../inspections_bmat_categorization/2010_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [26](../inspections_bmat_categorization/2010_q026.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2010 | [27](../inspections_bmat_categorization/2010_q027.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2010 | [28](../inspections_bmat_categorization/2010_q028.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2010 | [29](../inspections_bmat_categorization/2010_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2010 | [30](../inspections_bmat_categorization/2010_q030.html) | supported | Critical Thinking / Identifying an Assumption |
| 2010 | [31](../inspections_bmat_categorization/2010_q031.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2010 | [32](../inspections_bmat_categorization/2010_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2010 | [33](../inspections_bmat_categorization/2010_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2010 | [34](../inspections_bmat_categorization/2010_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2010 | [35](../inspections_bmat_categorization/2010_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2011 | [1](../inspections_bmat_categorization/2011_q001.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2011 | [2](../inspections_bmat_categorization/2011_q002.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2011 | [3](../inspections_bmat_categorization/2011_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [4](../inspections_bmat_categorization/2011_q004.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2011 | [5](../inspections_bmat_categorization/2011_q005.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2011 | [6](../inspections_bmat_categorization/2011_q006.html) | supported | Critical Thinking / Identifying an Assumption |
| 2011 | [7](../inspections_bmat_categorization/2011_q007.html) | intentional_skip | The source supplies named rows of one data table, not a separate multiple-choice answer set. |
| 2011 | [8](../inspections_bmat_categorization/2011_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2011 | [9](../inspections_bmat_categorization/2011_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2011 | [10](../inspections_bmat_categorization/2011_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2011 | [11](../inspections_bmat_categorization/2011_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2011 | [12](../inspections_bmat_categorization/2011_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [13](../inspections_bmat_categorization/2011_q013.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [14](../inspections_bmat_categorization/2011_q014.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [15](../inspections_bmat_categorization/2011_q015.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2011 | [16](../inspections_bmat_categorization/2011_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [17](../inspections_bmat_categorization/2011_q017.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2011 | [18](../inspections_bmat_categorization/2011_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [19](../inspections_bmat_categorization/2011_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2011 | [20](../inspections_bmat_categorization/2011_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2011 | [21](../inspections_bmat_categorization/2011_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2011 | [22](../inspections_bmat_categorization/2011_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2011 | [23](../inspections_bmat_categorization/2011_q023.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2011 | [24](../inspections_bmat_categorization/2011_q024.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [25](../inspections_bmat_categorization/2011_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [26](../inspections_bmat_categorization/2011_q026.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2011 | [27](../inspections_bmat_categorization/2011_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [28](../inspections_bmat_categorization/2011_q028.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2011 | [29](../inspections_bmat_categorization/2011_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2011 | [30](../inspections_bmat_categorization/2011_q030.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2011 | [31](../inspections_bmat_categorization/2011_q031.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2011 | [32](../inspections_bmat_categorization/2011_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2011 | [33](../inspections_bmat_categorization/2011_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2011 | [34](../inspections_bmat_categorization/2011_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2011 | [35](../inspections_bmat_categorization/2011_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2012 | [1](../inspections_bmat_categorization/2012_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [2](../inspections_bmat_categorization/2012_q002.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2012 | [3](../inspections_bmat_categorization/2012_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [4](../inspections_bmat_categorization/2012_q004.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2012 | [5](../inspections_bmat_categorization/2012_q005.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2012 | [6](../inspections_bmat_categorization/2012_q006.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2012 | [7](../inspections_bmat_categorization/2012_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [8](../inspections_bmat_categorization/2012_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2012 | [9](../inspections_bmat_categorization/2012_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2012 | [10](../inspections_bmat_categorization/2012_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2012 | [11](../inspections_bmat_categorization/2012_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2012 | [12](../inspections_bmat_categorization/2012_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [13](../inspections_bmat_categorization/2012_q013.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2012 | [14](../inspections_bmat_categorization/2012_q014.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2012 | [15](../inspections_bmat_categorization/2012_q015.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2012 | [16](../inspections_bmat_categorization/2012_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [17](../inspections_bmat_categorization/2012_q017.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2012 | [18](../inspections_bmat_categorization/2012_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [19](../inspections_bmat_categorization/2012_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2012 | [20](../inspections_bmat_categorization/2012_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2012 | [21](../inspections_bmat_categorization/2012_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2012 | [22](../inspections_bmat_categorization/2012_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2012 | [23](../inspections_bmat_categorization/2012_q023.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2012 | [24](../inspections_bmat_categorization/2012_q024.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2012 | [25](../inspections_bmat_categorization/2012_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [26](../inspections_bmat_categorization/2012_q026.html) | supported | Critical Thinking / Matching Arguments |
| 2012 | [27](../inspections_bmat_categorization/2012_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [28](../inspections_bmat_categorization/2012_q028.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2012 | [29](../inspections_bmat_categorization/2012_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [30](../inspections_bmat_categorization/2012_q030.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2012 | [31](../inspections_bmat_categorization/2012_q031.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2012 | [32](../inspections_bmat_categorization/2012_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2012 | [33](../inspections_bmat_categorization/2012_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2012 | [34](../inspections_bmat_categorization/2012_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2012 | [35](../inspections_bmat_categorization/2012_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2013 | [1](../inspections_bmat_categorization/2013_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [2](../inspections_bmat_categorization/2013_q002.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2013 | [3](../inspections_bmat_categorization/2013_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [4](../inspections_bmat_categorization/2013_q004.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2013 | [5](../inspections_bmat_categorization/2013_q005.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [6](../inspections_bmat_categorization/2013_q006.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [7](../inspections_bmat_categorization/2013_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [8](../inspections_bmat_categorization/2013_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2013 | [9](../inspections_bmat_categorization/2013_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2013 | [10](../inspections_bmat_categorization/2013_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2013 | [11](../inspections_bmat_categorization/2013_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2013 | [12](../inspections_bmat_categorization/2013_q012.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2013 | [13](../inspections_bmat_categorization/2013_q013.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2013 | [14](../inspections_bmat_categorization/2013_q014.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [15](../inspections_bmat_categorization/2013_q015.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2013 | [16](../inspections_bmat_categorization/2013_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [17](../inspections_bmat_categorization/2013_q017.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2013 | [18](../inspections_bmat_categorization/2013_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [19](../inspections_bmat_categorization/2013_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2013 | [20](../inspections_bmat_categorization/2013_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2013 | [21](../inspections_bmat_categorization/2013_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2013 | [22](../inspections_bmat_categorization/2013_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2013 | [23](../inspections_bmat_categorization/2013_q023.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2013 | [24](../inspections_bmat_categorization/2013_q024.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2013 | [25](../inspections_bmat_categorization/2013_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [26](../inspections_bmat_categorization/2013_q026.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [27](../inspections_bmat_categorization/2013_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [28](../inspections_bmat_categorization/2013_q028.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2013 | [29](../inspections_bmat_categorization/2013_q029.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2013 | [30](../inspections_bmat_categorization/2013_q030.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2013 | [31](../inspections_bmat_categorization/2013_q031.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2013 | [32](../inspections_bmat_categorization/2013_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2013 | [33](../inspections_bmat_categorization/2013_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2013 | [34](../inspections_bmat_categorization/2013_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2013 | [35](../inspections_bmat_categorization/2013_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2014 | [1](../inspections_bmat_categorization/2014_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [2](../inspections_bmat_categorization/2014_q002.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2014 | [3](../inspections_bmat_categorization/2014_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [4](../inspections_bmat_categorization/2014_q004.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2014 | [5](../inspections_bmat_categorization/2014_q005.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2014 | [6](../inspections_bmat_categorization/2014_q006.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2014 | [7](../inspections_bmat_categorization/2014_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [8](../inspections_bmat_categorization/2014_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2014 | [9](../inspections_bmat_categorization/2014_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2014 | [10](../inspections_bmat_categorization/2014_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2014 | [11](../inspections_bmat_categorization/2014_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2014 | [12](../inspections_bmat_categorization/2014_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [13](../inspections_bmat_categorization/2014_q013.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2014 | [14](../inspections_bmat_categorization/2014_q014.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2014 | [15](../inspections_bmat_categorization/2014_q015.html) | supported | Critical Thinking / Identifying an Assumption |
| 2014 | [16](../inspections_bmat_categorization/2014_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [17](../inspections_bmat_categorization/2014_q017.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2014 | [18](../inspections_bmat_categorization/2014_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [19](../inspections_bmat_categorization/2014_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--21. |
| 2014 | [20](../inspections_bmat_categorization/2014_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--21. |
| 2014 | [21](../inspections_bmat_categorization/2014_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--21. |
| 2014 | [22](../inspections_bmat_categorization/2014_q022.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [23](../inspections_bmat_categorization/2014_q023.html) | intentional_skip | Select missing textual/argument content rather than solve a numeric blank. |
| 2014 | [24](../inspections_bmat_categorization/2014_q024.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [25](../inspections_bmat_categorization/2014_q025.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2014 | [26](../inspections_bmat_categorization/2014_q026.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [27](../inspections_bmat_categorization/2014_q027.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2014 | [28](../inspections_bmat_categorization/2014_q028.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2014 | [29](../inspections_bmat_categorization/2014_q029.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2014 | [30](../inspections_bmat_categorization/2014_q030.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2014 | [31](../inspections_bmat_categorization/2014_q031.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2014 | [32](../inspections_bmat_categorization/2014_q032.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2014 | [33](../inspections_bmat_categorization/2014_q033.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2014 | [34](../inspections_bmat_categorization/2014_q034.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2014 | [35](../inspections_bmat_categorization/2014_q035.html) | intentional_skip | Question falls in declared shared-information interval 31--35. |
| 2015 | [1](../inspections_bmat_categorization/2015_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [2](../inspections_bmat_categorization/2015_q002.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2015 | [3](../inspections_bmat_categorization/2015_q003.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2015 | [4](../inspections_bmat_categorization/2015_q004.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2015 | [5](../inspections_bmat_categorization/2015_q005.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2015 | [6](../inspections_bmat_categorization/2015_q006.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2015 | [7](../inspections_bmat_categorization/2015_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [8](../inspections_bmat_categorization/2015_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2015 | [9](../inspections_bmat_categorization/2015_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2015 | [10](../inspections_bmat_categorization/2015_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2015 | [11](../inspections_bmat_categorization/2015_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2015 | [12](../inspections_bmat_categorization/2015_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [13](../inspections_bmat_categorization/2015_q013.html) | supported | Critical Thinking / Identifying an Assumption |
| 2015 | [14](../inspections_bmat_categorization/2015_q014.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [15](../inspections_bmat_categorization/2015_q015.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2015 | [16](../inspections_bmat_categorization/2015_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [17](../inspections_bmat_categorization/2015_q017.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2015 | [18](../inspections_bmat_categorization/2015_q018.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2015 | [19](../inspections_bmat_categorization/2015_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2015 | [20](../inspections_bmat_categorization/2015_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2015 | [21](../inspections_bmat_categorization/2015_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2015 | [22](../inspections_bmat_categorization/2015_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2015 | [23](../inspections_bmat_categorization/2015_q023.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2015 | [24](../inspections_bmat_categorization/2015_q024.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [25](../inspections_bmat_categorization/2015_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [26](../inspections_bmat_categorization/2015_q026.html) | supported | Critical Thinking / Identifying an Assumption |
| 2015 | [27](../inspections_bmat_categorization/2015_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [28](../inspections_bmat_categorization/2015_q028.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2015 | [29](../inspections_bmat_categorization/2015_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [30](../inspections_bmat_categorization/2015_q030.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2015 | [31](../inspections_bmat_categorization/2015_q031.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2015 | [32](../inspections_bmat_categorization/2015_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2015 | [33](../inspections_bmat_categorization/2015_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2015 | [34](../inspections_bmat_categorization/2015_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2015 | [35](../inspections_bmat_categorization/2015_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2016 | [1](../inspections_bmat_categorization/2016_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [2](../inspections_bmat_categorization/2016_q002.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2016 | [3](../inspections_bmat_categorization/2016_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [4](../inspections_bmat_categorization/2016_q004.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2016 | [5](../inspections_bmat_categorization/2016_q005.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2016 | [6](../inspections_bmat_categorization/2016_q006.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2016 | [7](../inspections_bmat_categorization/2016_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [8](../inspections_bmat_categorization/2016_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2016 | [9](../inspections_bmat_categorization/2016_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2016 | [10](../inspections_bmat_categorization/2016_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2016 | [11](../inspections_bmat_categorization/2016_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2016 | [12](../inspections_bmat_categorization/2016_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [13](../inspections_bmat_categorization/2016_q013.html) | supported | Critical Thinking / Identifying an Assumption |
| 2016 | [14](../inspections_bmat_categorization/2016_q014.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [15](../inspections_bmat_categorization/2016_q015.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2016 | [16](../inspections_bmat_categorization/2016_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [17](../inspections_bmat_categorization/2016_q017.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2016 | [18](../inspections_bmat_categorization/2016_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [19](../inspections_bmat_categorization/2016_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2016 | [20](../inspections_bmat_categorization/2016_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2016 | [21](../inspections_bmat_categorization/2016_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2016 | [22](../inspections_bmat_categorization/2016_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2016 | [23](../inspections_bmat_categorization/2016_q023.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [24](../inspections_bmat_categorization/2016_q024.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2016 | [25](../inspections_bmat_categorization/2016_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [26](../inspections_bmat_categorization/2016_q026.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2016 | [27](../inspections_bmat_categorization/2016_q027.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2016 | [28](../inspections_bmat_categorization/2016_q028.html) | supported | Critical Thinking / Identifying an Assumption |
| 2016 | [29](../inspections_bmat_categorization/2016_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [30](../inspections_bmat_categorization/2016_q030.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2016 | [31](../inspections_bmat_categorization/2016_q031.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2016 | [32](../inspections_bmat_categorization/2016_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2016 | [33](../inspections_bmat_categorization/2016_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2016 | [34](../inspections_bmat_categorization/2016_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2016 | [35](../inspections_bmat_categorization/2016_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2017 | [1](../inspections_bmat_categorization/2017_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2017 | [2](../inspections_bmat_categorization/2017_q002.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2017 | [3](../inspections_bmat_categorization/2017_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2017 | [4](../inspections_bmat_categorization/2017_q004.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2017 | [5](../inspections_bmat_categorization/2017_q005.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [6](../inspections_bmat_categorization/2017_q006.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2017 | [7](../inspections_bmat_categorization/2017_q007.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [8](../inspections_bmat_categorization/2017_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2017 | [9](../inspections_bmat_categorization/2017_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2017 | [10](../inspections_bmat_categorization/2017_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2017 | [11](../inspections_bmat_categorization/2017_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2017 | [12](../inspections_bmat_categorization/2017_q012.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [13](../inspections_bmat_categorization/2017_q013.html) | intentional_skip | Select missing textual/argument content rather than solve a numeric blank. |
| 2017 | [14](../inspections_bmat_categorization/2017_q014.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2017 | [15](../inspections_bmat_categorization/2017_q015.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2017 | [16](../inspections_bmat_categorization/2017_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2017 | [17](../inspections_bmat_categorization/2017_q017.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2017 | [18](../inspections_bmat_categorization/2017_q018.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [19](../inspections_bmat_categorization/2017_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2017 | [20](../inspections_bmat_categorization/2017_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2017 | [21](../inspections_bmat_categorization/2017_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2017 | [22](../inspections_bmat_categorization/2017_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2017 | [23](../inspections_bmat_categorization/2017_q023.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [24](../inspections_bmat_categorization/2017_q024.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2017 | [25](../inspections_bmat_categorization/2017_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2017 | [26](../inspections_bmat_categorization/2017_q026.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2017 | [27](../inspections_bmat_categorization/2017_q027.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2017 | [28](../inspections_bmat_categorization/2017_q028.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2017 | [29](../inspections_bmat_categorization/2017_q029.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2017 | [30](../inspections_bmat_categorization/2017_q030.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2017 | [31](../inspections_bmat_categorization/2017_q031.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2017 | [32](../inspections_bmat_categorization/2017_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2017 | [33](../inspections_bmat_categorization/2017_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2017 | [34](../inspections_bmat_categorization/2017_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2017 | [35](../inspections_bmat_categorization/2017_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2018 | [1](../inspections_bmat_categorization/2018_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [2](../inspections_bmat_categorization/2018_q002.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2018 | [3](../inspections_bmat_categorization/2018_q003.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [4](../inspections_bmat_categorization/2018_q004.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2018 | [5](../inspections_bmat_categorization/2018_q005.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2018 | [6](../inspections_bmat_categorization/2018_q006.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2018 | [7](../inspections_bmat_categorization/2018_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [8](../inspections_bmat_categorization/2018_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2018 | [9](../inspections_bmat_categorization/2018_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2018 | [10](../inspections_bmat_categorization/2018_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2018 | [11](../inspections_bmat_categorization/2018_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2018 | [12](../inspections_bmat_categorization/2018_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [13](../inspections_bmat_categorization/2018_q013.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2018 | [14](../inspections_bmat_categorization/2018_q014.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [15](../inspections_bmat_categorization/2018_q015.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2018 | [16](../inspections_bmat_categorization/2018_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [17](../inspections_bmat_categorization/2018_q017.html) | supported | Critical Thinking / Matching Arguments |
| 2018 | [18](../inspections_bmat_categorization/2018_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [19](../inspections_bmat_categorization/2018_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2018 | [20](../inspections_bmat_categorization/2018_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2018 | [21](../inspections_bmat_categorization/2018_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2018 | [22](../inspections_bmat_categorization/2018_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2018 | [23](../inspections_bmat_categorization/2018_q023.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [24](../inspections_bmat_categorization/2018_q024.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2018 | [25](../inspections_bmat_categorization/2018_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [26](../inspections_bmat_categorization/2018_q026.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2018 | [27](../inspections_bmat_categorization/2018_q027.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2018 | [28](../inspections_bmat_categorization/2018_q028.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2018 | [29](../inspections_bmat_categorization/2018_q029.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2018 | [30](../inspections_bmat_categorization/2018_q030.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2018 | [31](../inspections_bmat_categorization/2018_q031.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2018 | [32](../inspections_bmat_categorization/2018_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2018 | [33](../inspections_bmat_categorization/2018_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2018 | [34](../inspections_bmat_categorization/2018_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2018 | [35](../inspections_bmat_categorization/2018_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2019 | [1](../inspections_bmat_categorization/2019_q001.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2019 | [2](../inspections_bmat_categorization/2019_q002.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2019 | [3](../inspections_bmat_categorization/2019_q003.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [4](../inspections_bmat_categorization/2019_q004.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2019 | [5](../inspections_bmat_categorization/2019_q005.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [6](../inspections_bmat_categorization/2019_q006.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2019 | [7](../inspections_bmat_categorization/2019_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2019 | [8](../inspections_bmat_categorization/2019_q008.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2019 | [9](../inspections_bmat_categorization/2019_q009.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2019 | [10](../inspections_bmat_categorization/2019_q010.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2019 | [11](../inspections_bmat_categorization/2019_q011.html) | intentional_skip | Question falls in declared shared-information interval 8--11. |
| 2019 | [12](../inspections_bmat_categorization/2019_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2019 | [13](../inspections_bmat_categorization/2019_q013.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2019 | [14](../inspections_bmat_categorization/2019_q014.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [15](../inspections_bmat_categorization/2019_q015.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2019 | [16](../inspections_bmat_categorization/2019_q016.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2019 | [17](../inspections_bmat_categorization/2019_q017.html) | supported | Critical Thinking / Identifying an Assumption |
| 2019 | [18](../inspections_bmat_categorization/2019_q018.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [19](../inspections_bmat_categorization/2019_q019.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2019 | [20](../inspections_bmat_categorization/2019_q020.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2019 | [21](../inspections_bmat_categorization/2019_q021.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2019 | [22](../inspections_bmat_categorization/2019_q022.html) | intentional_skip | Question falls in declared shared-information interval 19--22. |
| 2019 | [23](../inspections_bmat_categorization/2019_q023.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [24](../inspections_bmat_categorization/2019_q024.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2019 | [25](../inspections_bmat_categorization/2019_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2019 | [26](../inspections_bmat_categorization/2019_q026.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2019 | [27](../inspections_bmat_categorization/2019_q027.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [28](../inspections_bmat_categorization/2019_q028.html) | intentional_skip | Exactly three full propositions are evaluated through single combination-valued answers. |
| 2019 | [29](../inspections_bmat_categorization/2019_q029.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2019 | [30](../inspections_bmat_categorization/2019_q030.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2019 | [31](../inspections_bmat_categorization/2019_q031.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2019 | [32](../inspections_bmat_categorization/2019_q032.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2019 | [33](../inspections_bmat_categorization/2019_q033.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2019 | [34](../inspections_bmat_categorization/2019_q034.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2019 | [35](../inspections_bmat_categorization/2019_q035.html) | intentional_skip | Question falls in declared shared-information interval 32--35. |
| 2020 | [1](../inspections_bmat_categorization/2020_q001.html) | supported | Critical Thinking / Matching Arguments |
| 2020 | [2](../inspections_bmat_categorization/2020_q002.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [3](../inspections_bmat_categorization/2020_q003.html) | supported | Critical Thinking / Identifying an Assumption |
| 2020 | [4](../inspections_bmat_categorization/2020_q004.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2020 | [5](../inspections_bmat_categorization/2020_q005.html) | supported | Critical Thinking / Applying Principles |
| 2020 | [6](../inspections_bmat_categorization/2020_q006.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [7](../inspections_bmat_categorization/2020_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [8](../inspections_bmat_categorization/2020_q008.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [9](../inspections_bmat_categorization/2020_q009.html) | supported | Critical Thinking / Matching Arguments |
| 2020 | [10](../inspections_bmat_categorization/2020_q010.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2020 | [11](../inspections_bmat_categorization/2020_q011.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2020 | [12](../inspections_bmat_categorization/2020_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [13](../inspections_bmat_categorization/2020_q013.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [14](../inspections_bmat_categorization/2020_q014.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [15](../inspections_bmat_categorization/2020_q015.html) | supported | Critical Thinking / Identifying an Assumption |
| 2020 | [16](../inspections_bmat_categorization/2020_q016.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2020 | [17](../inspections_bmat_categorization/2020_q017.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2020 | [18](../inspections_bmat_categorization/2020_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [19](../inspections_bmat_categorization/2020_q019.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [20](../inspections_bmat_categorization/2020_q020.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2020 | [21](../inspections_bmat_categorization/2020_q021.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2020 | [22](../inspections_bmat_categorization/2020_q022.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2020 | [23](../inspections_bmat_categorization/2020_q023.html) | supported | Critical Thinking / Matching Arguments |
| 2020 | [24](../inspections_bmat_categorization/2020_q024.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [25](../inspections_bmat_categorization/2020_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [26](../inspections_bmat_categorization/2020_q026.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [27](../inspections_bmat_categorization/2020_q027.html) | supported | Critical Thinking / Applying Principles |
| 2020 | [28](../inspections_bmat_categorization/2020_q028.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [29](../inspections_bmat_categorization/2020_q029.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2020 | [30](../inspections_bmat_categorization/2020_q030.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2020 | [31](../inspections_bmat_categorization/2020_q031.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2020 | [32](../inspections_bmat_categorization/2020_q032.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2021 | [1](../inspections_bmat_categorization/2021_q001.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2021 | [2](../inspections_bmat_categorization/2021_q002.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [3](../inspections_bmat_categorization/2021_q003.html) | supported | Critical Thinking / Matching Arguments |
| 2021 | [4](../inspections_bmat_categorization/2021_q004.html) | supported | Critical Thinking / Applying Principles |
| 2021 | [5](../inspections_bmat_categorization/2021_q005.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2021 | [6](../inspections_bmat_categorization/2021_q006.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2021 | [7](../inspections_bmat_categorization/2021_q007.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [8](../inspections_bmat_categorization/2021_q008.html) | needs_review | Upstream defects remain: incomplete_or_ambiguous_options, visual_caption_boundary_uncertain, visual_caption_may_be_incomplete, visual_component_association_uncertain, visual_option_labels_ambiguous |
| 2021 | [9](../inspections_bmat_categorization/2021_q009.html) | supported | Critical Thinking / Identifying an Assumption |
| 2021 | [10](../inspections_bmat_categorization/2021_q010.html) | supported | Critical Thinking / Drawing a Conclusion |
| 2021 | [11](../inspections_bmat_categorization/2021_q011.html) | supported | Critical Thinking / Applying Principles |
| 2021 | [12](../inspections_bmat_categorization/2021_q012.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [13](../inspections_bmat_categorization/2021_q013.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [14](../inspections_bmat_categorization/2021_q014.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2021 | [15](../inspections_bmat_categorization/2021_q015.html) | supported | Critical Thinking / Matching Arguments |
| 2021 | [16](../inspections_bmat_categorization/2021_q016.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2021 | [17](../inspections_bmat_categorization/2021_q017.html) | supported | Critical Thinking / Identifying an Assumption |
| 2021 | [18](../inspections_bmat_categorization/2021_q018.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [19](../inspections_bmat_categorization/2021_q019.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [20](../inspections_bmat_categorization/2021_q020.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
| 2021 | [21](../inspections_bmat_categorization/2021_q021.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2021 | [22](../inspections_bmat_categorization/2021_q022.html) | supported | Critical Thinking / Applying Principles |
| 2021 | [23](../inspections_bmat_categorization/2021_q023.html) | supported | Critical Thinking / Assessing the Impact of Additional Evidence |
| 2021 | [24](../inspections_bmat_categorization/2021_q024.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [25](../inspections_bmat_categorization/2021_q025.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [26](../inspections_bmat_categorization/2021_q026.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [27](../inspections_bmat_categorization/2021_q027.html) | supported | Critical Thinking / Detecting Reasoning Errors |
| 2021 | [28](../inspections_bmat_categorization/2021_q028.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [29](../inspections_bmat_categorization/2021_q029.html) | supported | Critical Thinking / Summarising the Main Conclusion |
| 2021 | [30](../inspections_bmat_categorization/2021_q030.html) | not_evaluated | Normal task attribution outside this targeted Critical Thinking pass remains pending; surviving exclusion filters is not a Problem-Solving label. |
| 2021 | [31](../inspections_bmat_categorization/2021_q031.html) | supported | Critical Thinking / Matching Arguments |
| 2021 | [32](../inspections_bmat_categorization/2021_q032.html) | intentional_skip | One complete question occupies more than 60% of the usable content height, ending at the bottom of its final answer option. |
