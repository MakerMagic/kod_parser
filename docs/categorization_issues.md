<!-- tsa_categorization_v1 -->
# Categorization issues

Counts are unique question records within each group. Accepted multi-label results are not errors. Upstream warnings remain traceable, not copied wholesale or declared fixed.

Active unresolved question records: **28**. A question may have several distinct issue types; group counts must not be added together.

## Run summary

```json
{
  "processed": 750,
  "statuses": {
    "classified": 706,
    "multi_label": 16,
    "needs_review": 25,
    "unclassified": 3
  },
  "categories_successful_only": {
    "Critical Thinking": 373,
    "Problem-Solving": 349
  },
  "subcategories_successful_only": {
    "Summarising the Main Conclusion": 77,
    "Finding Procedures": 226,
    "Detecting Reasoning Errors": 57,
    "Drawing a Conclusion": 51,
    "Identifying an Assumption": 59,
    "Identifying Similarity": 60,
    "Assessing the Impact of Additional Evidence": 58,
    "Relevant Selection": 79,
    "Matching Arguments": 37,
    "Applying Principles": 34
  },
  "selection_and_procedures": 14,
  "unresolved": 28
}
```

## Complete rulebook review pass

```json
{
  "all_needs_review": 262,
  "problem_solving_review": 260,
  "out_of_scope_review": 2,
  "reviewed": 260,
  "resolved": 235,
  "remaining_review": 25,
  "resolved_subcategory_counts_overlapping": {
    "Finding Procedures": 168,
    "Relevant Selection": 49,
    "Identifying Similarity": 31
  },
  "multi_label": 13,
  "remaining_reasons": {
    "below_semantic_threshold": 11,
    "explanation_question_conflict": 9,
    "taxonomy_boundary": 2,
    "incomplete_extraction": 2,
    "insufficient_semantic_evidence": 1
  }
}
```

Every in-scope record, including unresolved decisions, is linked from [categorization backtesting](CATEGORIZATION_BACKTEST.MD). Classifier-only uncertainty is replaced by the recorded diagnosis, not hidden.

Resolved questions are not issue rows. Their complete before/after history remains in [categorization backtesting](CATEGORIZATION_BACKTEST.MD).

## Rulebook Below Semantic Threshold (11 questions)

| Year | Question | Category / candidates | Reason | Matched record | Review |
|---|---|---|---|---|---|
| 2008 | 25 | Problem-Solving; Finding Procedures, Relevant Selection | Every filled square explicitly represents a man-day; counting their total and the tallest occupied day is direct. The source explanation confirms straightforward area/count operations, not a non-trivial scheduling construction. No substantial RS or equivalence is required. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/24 | required |
| 2008 | 30 | Problem-Solving; Finding Procedures, Relevant Selection | The diagram and all dimensions support the direct area ratio 550*400/(10*20), with reuse of offcuts explicitly allowed. FP's direct-calculation exclusion applies; no meaningful applicability filtering or equivalence recognition independently meets the rulebook threshold. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/29 | required |
| 2010 | 8 | Problem-Solving; Relevant Selection, Finding Procedures | The tenfold-per-unit rule is explicitly supplied and the answer follows by direct application to the named values. No excess-data applicability or equivalent-structure task exists, while the explicit-rule/simple-calculation exclusion prevents a defensible strong FP assignment. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/107 | required |
| 2010 | 36 | Problem-Solving; Finding Procedures, Relevant Selection | All three speed/consumption columns are explicitly required by the three named journey segments. Weighted fuel consumption then price multiplication is a directly prescribed calculation; no selective subset or equivalent representation is sought and FP's explicit-sequence exclusion remains material. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/135 | required |
| 2012 | 2 | Problem-Solving; Finding Procedures, Relevant Selection | The two named speeds and separation give a direct closing-rate calculation; no competing supplied information or equivalent representation exists. A non-trivial procedure beyond that routine model is not evidenced strongly enough under FP's exclusion. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/201 | required |
| 2012 | 6 | Problem-Solving; Finding Procedures, Relevant Selection | All three spending categories and explicit changes apply, so weighted percentage arithmetic alone does not establish FP and there is no excess-data selection or equivalence target. Keep review rather than infer a substantial procedure from several calculations. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/205 | required |
| 2012 | 24 | Problem-Solving; Finding Procedures, Relevant Selection | All purchases and sales are explicit; direct net cashflow 100+120-80-110 suffices. No non-trivial chain, applicable subset or equivalence judgment reaches the supplied rulebook threshold. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/223 | required |
| 2019 | 2 | Problem-Solving; Relevant Selection, Finding Procedures | Each row gives exactly its income/rate inputs for direct tax multiplication. Ignoring the region-name column is incidental; numeric equality is excluded from IS and no substantial method or applicability selection is evidenced. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2017-2019.matched.json/records/101 | required |
| 2019 | 14 | Problem-Solving; Finding Procedures, Relevant Selection | The task is direct ordinal comparison of age/price/size/speed across two plots. No substantial procedure or scenario-specific excess-data filtering is evidenced; comparison only by magnitude is explicitly excluded from IS, so do not force a subtype. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2017-2019.matched.json/records/113 | required |
| 2019 | 19 | Problem-Solving; Relevant Selection, Finding Procedures | The question explicitly identifies both year columns and requires direct percentage comparisons across all countries. Excluding year two alone is weak/incidental RS; repeated direct ratios are not non-trivial FP and numeric magnitude is not IS. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2017-2019.matched.json/records/118 | required |
| 2021 | 48 | Problem-Solving; Relevant Selection, Finding Procedures | All city construction/land rates are needed and the source explicitly supplies total floor/land areas and the cost-sum recipe. Direct repeated substitution/comparison is excluded from FP; no independently substantial applicability selection or structural equivalence. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2021.matched.json/records/47 | required |

## Rulebook Explanation Question Conflict (9 questions)

| Year | Question | Category / candidates | Reason | Matched record | Review |
|---|---|---|---|---|---|
| 2010 | 14 | Problem-Solving; Identifying Similarity, Applying Principles | Constrained tiling suggests FP rather than RS/IS, but the stored explanation first says B overlaps and then says B fills the window, concluding A. This contradictory candidate attribution remains visible; do not silently repair the explanation to approve the review. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/113 | required |
| 2016 | 48 | Problem-Solving; Finding Procedures, Relevant Selection | Orbital recurrence needs FP, not RS/IS, but source explanation incorrectly uses 37/45 for Hamlet at 72 days (actual remainder 27/45). All three phases equal 0.6 at 72 days, conflicting with its claim that only E/216 works. Retain review; do not change stored answer/explanation here. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/447 | required |
| 2021 | 44 | Problem-Solving; Finding Procedures, Relevant Selection | The question asks for monthly distances from cumulative records, requiring differences (FP), but the stored explanation sums cumulative totals to 1856 and treats July's cumulative 478 as a monthly share. Question and explanation use incompatible quantities; RS/IS cannot remove the conflict. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2021.matched.json/records/43 | required |
| 2022 | 19 | Problem-Solving; Finding Procedures, Relevant Selection | The actual source and structured record say Fay wants to swap, but Main Question asks about Eve. These have different consecutive-duty constraints (Pat is feasible for Fay but not Eve). FP scheduling is plausible; RS/FP/IS cannot be finalised by silently choosing a name interpretation. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2022.matched.json/records/18 | required |
| 2022 | 20 | Problem-Solving; Finding Procedures, Relevant Selection | Table-to-scatter correspondence suggests IS, not RS/FP, but stored correct answer B names Gary while Final Explanation says Ffion. Preserve review rather than approve conflicting question/explanation attribution. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2022.matched.json/records/19 | required |
| 2022 | 30 | Problem-Solving; Finding Procedures, Relevant Selection | Question requires systematic factor/permutation cases (FP), but source explanation lists only 124 and 118 while claiming ten arrangements; those yield nine and omit valid 222. Preserve inconsistent supporting evidence; no RS/IS resolution by guessing the omitted case. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2022.matched.json/records/29 | required |
| 2022 | 42 | Problem-Solving; Finding Procedures, Relevant Selection | Coin-state reconstruction suggests FP, not RS/IS, but explanation calls 20p+10p 40p, buys a 55p bar with it and repeats 10p despite six-distinct-coins. This directly violates source constraints; preserve review without replacing source text. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2022.matched.json/records/41 | required |
| 2022 | 43 | Problem-Solving; Finding Procedures, Relevant Selection | Local-score optimisation is FP, not RS/IS, but explanation places the winning token on a bottom-left square containing two. That square's score does not reach fourteen; the fourteen-point position is the upper zero square. Stored visual and explanation conflict. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2022.matched.json/records/42 | required |
| 2022 | 44 | Problem-Solving; Relevant Selection, Finding Procedures | Game-history propagation is FP, not RS/IS. Cards 3/8 are mice and successful 8/10 therefore makes 10 a cat; the source explanation instead calls 10 a mouse before concluding 12 is a cat. Keep the inconsistent inference unresolved, preserving the pinned body image and source text. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2022.matched.json/records/43 | required |

## Rulebook Incomplete Extraction (1 questions)

| Year | Question | Category / candidates | Reason | Matched record | Review |
|---|---|---|---|---|---|
| 2020 | 12 | Problem-Solving; Finding Procedures, Relevant Selection | An isolated colon in the target mixture ratio remains a declared ordering ambiguity. A mixture-reconstruction FP path is plausible, but RS/FP/IS cannot be finalised by silently repositioning uncertain source text; preserve upstream review. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2020.matched.json/records/11 | required |

## Rulebook Insufficient Semantic Evidence (1 questions)

| Year | Question | Category / candidates | Reason | Matched record | Review |
|---|---|---|---|---|---|
| 2022 | 36 | Problem-Solving; Relevant Selection, Finding Procedures | The wording states only that more reading gets greater total book cost, while the expected allocation relies on exact proportionality to hours. Rank-only and proportional allocations differ. FP allocation is plausible but cannot be approved by assuming the missing proportional rule; RS/IS do not resolve it. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2022.matched.json/records/35 | required |

## Rulebook Taxonomy Boundary (2 questions)

| Year | Question | Category / candidates | Reason | Matched record | Review |
|---|---|---|---|---|---|
| 2010 | 15 | Problem-Solving; Drawing a Conclusion, Relevant Selection | The actual task evaluates which inferential claim follows from aggregate attitude data; rejecting causal/population generalisations is not a material scenario-applicability task. No non-trivial FP or structural IS is established; a visual cannot by itself justify a PS subtype. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/114 | required |
| 2015 | 14 | Problem-Solving; Relevant Selection, Finding Procedures | Task infers limits of causal/school-background conclusions from two aggregate tables; it does not materially select scenario-applicable inputs, construct a non-trivial procedure or recognise equivalent structures. Visual CT eligibility cannot be bypassed by inventing a PS subtype. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/363 | required |

## Top Level Pattern Uncovered (3 questions)

| Year | Question | Category / candidates | Reason | Matched record | Review |
|---|---|---|---|---|---|
| 2009 | 14 | unclassified; Relevant Selection, Assessing the Impact of Additional Evidence | No corroborated cognitive-task profile; candidate similarities alone do not justify a label. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/63 | required |
| 2009 | 48 | unclassified; Relevant Selection, Finding Procedures | No corroborated cognitive-task profile; candidate similarities alone do not justify a label. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/97 | required |
| 2011 | 46 | unclassified; Finding Procedures, Relevant Selection | No corroborated cognitive-task profile; candidate similarities alone do not justify a label. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2008-2016.matched.json/records/195 | required |

## Upstream Structure Unresolved (1 questions)

| Year | Question | Category / candidates | Reason | Matched record | Review |
|---|---|---|---|---|---|
| 2021 | 7 | unclassified; Relevant Selection, Finding Procedures | Concrete cleaning ambiguity affects the evidence needed for categorization. | C:\Users\user\Desktop\kod_parser\data\merged\blackstone\tsa_2021.matched.json/records/6 | required |

