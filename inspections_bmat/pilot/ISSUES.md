<!-- bmat-raw-report-v1 -->
# BMAT Section 1 RAW issues

Intentional skips and parser defects are independent. Tag counts overlap; unique question counts do not. A skipped record may also retain a genuine parser defect. No finding is not a correctness certification.

```json
{
  "questions": 142,
  "status_counts": {
    "retained": 85,
    "skipped": 56,
    "parser_review": 1
  },
  "unique_intentional_skips": 56,
  "unique_parsing_issue_questions": 16,
  "retained_without_parsing_issues": 85,
  "skip_tag_counts_overlapping": {
    "Shared Information Range": 39,
    "No Question": 5,
    "Necessary and Sufficient Conditions": 0,
    "Several correct answers": 1,
    "Complete the text": 1,
    "Source": 0,
    "Variable-related question": 1,
    "Explanation": 3,
    "too long": 11
  },
  "by_year": {
    "2003": {
      "retained": 18,
      "skipped": 21,
      "parser_review": 1
    },
    "2013": {
      "retained": 20,
      "skipped": 15
    },
    "2017": {
      "retained": 19,
      "skipped": 16
    },
    "2020": {
      "retained": 28,
      "skipped": 4
    }
  },
  "document_issues": []
}
```

## A. Intentional BMAT-specific skips

### Shared Information Range (39 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 7 | 6–6 | Question falls in declared shared-information interval 7--12. |
| 2003 | 8 | 6–6 | Question falls in declared shared-information interval 7--12. |
| 2003 | 9 | 6–6 | Question falls in declared shared-information interval 7--12. |
| 2003 | 10 | 7–7 | Question falls in declared shared-information interval 7--12. |
| 2003 | 11 | 7–7 | Question falls in declared shared-information interval 7--12. |
| 2003 | 12 | 7–7 | Question falls in declared shared-information interval 7--12. |
| 2003 | 24 | 13–13 | Question falls in declared shared-information interval 24--27. |
| 2003 | 25 | 13–13 | Question falls in declared shared-information interval 24--27. |
| 2003 | 26 | 13–13 | Question falls in declared shared-information interval 24--27. |
| 2003 | 27 | 14–14 | Question falls in declared shared-information interval 24--27. |
| 2003 | 36 | 18–18 | Question falls in declared shared-information interval 36--40. |
| 2003 | 37 | 18–18 | Question falls in declared shared-information interval 36--40. |
| 2003 | 38 | 18–18 | Question falls in declared shared-information interval 36--40. |
| 2003 | 39 | 19–19 | Question falls in declared shared-information interval 36--40. |
| 2003 | 40 | 19–19 | Question falls in declared shared-information interval 36--40. |
| 2013 | 8 | 6–6 | Question falls in declared shared-information interval 8--11. |
| 2013 | 9 | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2013 | 10 | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2013 | 11 | 7–7 | Question falls in declared shared-information interval 8--11. |
| 2013 | 19 | 13–13 | Question falls in declared shared-information interval 19--22. |
| 2013 | 20 | 13–13 | Question falls in declared shared-information interval 19--22. |
| 2013 | 21 | 14–14 | Question falls in declared shared-information interval 19--22. |
| 2013 | 22 | 14–14 | Question falls in declared shared-information interval 19--22. |
| 2013 | 32 | 22–22 | Question falls in declared shared-information interval 32--35. |
| 2013 | 33 | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2013 | 34 | 23–23 | Question falls in declared shared-information interval 32--35. |
| 2013 | 35 | 23–24 | Question falls in declared shared-information interval 32--35. |
| 2017 | 8 | 11–11 | Question falls in declared shared-information interval 8--11. |
| 2017 | 9 | 11–11 | Question falls in declared shared-information interval 8--11. |
| 2017 | 10 | 12–12 | Question falls in declared shared-information interval 8--11. |
| 2017 | 11 | 12–12 | Question falls in declared shared-information interval 8--11. |
| 2017 | 19 | 21–21 | Question falls in declared shared-information interval 19--22. |
| 2017 | 20 | 21–21 | Question falls in declared shared-information interval 19--22. |
| 2017 | 21 | 21–21 | Question falls in declared shared-information interval 19--22. |
| 2017 | 22 | 22–22 | Question falls in declared shared-information interval 19--22. |
| 2017 | 32 | 31–31 | Question falls in declared shared-information interval 32--35. |
| 2017 | 33 | 31–31 | Question falls in declared shared-information interval 32--35. |
| 2017 | 34 | 32–32 | Question falls in declared shared-information interval 32--35. |
| 2017 | 35 | 32–32 | Question falls in declared shared-information interval 32--35. |

### No Question (5 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 5 | 5–5 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | 8 | 6–6 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | 18 | 9–9 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | 21 | 10–10 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |
| 2003 | 39 | 19–19 | A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response. |

### Necessary and Sufficient Conditions (0 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|

### Several correct answers (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 31 | 15–15 | The request selects multiple separate choices, not one combination-valued answer. |

### Complete the text (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2017 | 13 | 14–14 | Select missing textual/argument content rather than solve a numeric blank. |

### Source (0 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|

### Variable-related question (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 16 | 9–9 | The requested mathematical result depends on an explicit symbolic relation/function. |

### Explanation (3 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2017 | 11 | 12–12 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2017 | 32 | 31–31 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |
| 2017 | 35 | 32–32 | The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility. |

### too long (11 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 35 | 17–17 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2013 | 12 | 8–8 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2013 | 23 | 15–15 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2013 | 29 | 19–19 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2017 | 12 | 13–13 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2017 | 23 | 23–23 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2017 | 29 | 27–27 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2020 | 8 | 7–7 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2020 | 14 | 11–11 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2020 | 20 | 15–15 | One complete question is the sole question on the page and spans at least 65% of its usable height. |
| 2020 | 32 | 23–23 | One complete question is the sole question on the page and spans at least 65% of its usable height. |

## B. Genuine parsing issues

### incomplete_or_ambiguous_options (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 12 | 7–7 | incomplete_or_ambiguous_options:A,B,C,D |

### multi_column_options (3 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 12 | 7–7 | multi_column_options:text_and_image_association_unresolved |
| 2003 | 16 | 9–9 | multi_column_options:text_and_image_association_unresolved |
| 2003 | 35 | 17–17 | multi_column_options:text_and_image_association_unresolved |

### raw_prompt_boundary_unresolved (9 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 30 | 15–15 | raw_prompt_boundary_unresolved |
| 2003 | 36 | 18–18 | raw_prompt_boundary_unresolved |
| 2013 | 8 | 6–6 | raw_prompt_boundary_unresolved |
| 2013 | 10 | 7–7 | raw_prompt_boundary_unresolved |
| 2013 | 21 | 14–14 | raw_prompt_boundary_unresolved |
| 2013 | 32 | 22–22 | raw_prompt_boundary_unresolved |
| 2013 | 33 | 23–23 | raw_prompt_boundary_unresolved |
| 2013 | 34 | 23–23 | raw_prompt_boundary_unresolved |
| 2013 | 35 | 23–24 | raw_prompt_boundary_unresolved |

### visual_caption_boundary_uncertain (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2020 | 8 | 7–7 | visual_caption_boundary_uncertain:external_caption_preserved [assets/88d436a5b3b9aecef601/bmat_2020_q008_r008_p007_asset_01_c374504778.png] |

### visual_caption_may_be_incomplete (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2020 | 8 | 7–7 | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/88d436a5b3b9aecef601/bmat_2020_q008_r008_p007_asset_01_c374504778.png] |

### visual_component_association_uncertain (8 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 12 | 7–7 | visual_component_association_uncertain [assets/b50f7fbc103ff2982062/bmat_2003_q012_r012_p007_asset_04_b2113ffc13.png] |
| 2003 | 16 | 9–9 | visual_component_association_uncertain [assets/b50f7fbc103ff2982062/bmat_2003_q016_r016_p009_asset_05_baeab4b53c.png] |
| 2003 | 35 | 17–17 | visual_component_association_uncertain [assets/b50f7fbc103ff2982062/bmat_2003_q035_r035_p017_asset_08_4d8b64d8f7.png] |
| 2003 | 40 | 19–19 | visual_component_association_uncertain [assets/b50f7fbc103ff2982062/bmat_2003_q040_r040_p019_asset_04_681a922eec.png] |
| 2013 | 11 | 7–7 | visual_component_association_uncertain [assets/6e2a62a372670b103588/bmat_2013_q011_r011_p007_asset_01_8c3cef0043.png] |
| 2013 | 22 | 14–14 | visual_component_association_uncertain [assets/6e2a62a372670b103588/bmat_2013_q022_r022_p014_asset_02_f3f737d6bd.png] |
| 2013 | 35 | 23–24 | visual_component_association_uncertain [assets/6e2a62a372670b103588/bmat_2013_q035_r035_p023_asset_01_33f8ea9615.png] |
| 2020 | 8 | 7–7 | visual_component_association_uncertain [assets/88d436a5b3b9aecef601/bmat_2020_q008_r008_p007_asset_01_c374504778.png] |

### visual_crop_contains_unrelated_text (1 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2020 | 8 | 7–7 | visual_crop_contains_unrelated_text:boundary_overlap [assets/88d436a5b3b9aecef601/bmat_2020_q008_r008_p007_asset_01_c374504778.png] |

### visual_multiple_option_images_merged (2 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 35 | 17–17 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/b50f7fbc103ff2982062/bmat_2003_q035_r035_p017_asset_08_4d8b64d8f7.png] |
| 2003 | 40 | 19–19 | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/b50f7fbc103ff2982062/bmat_2003_q040_r040_p019_asset_04_681a922eec.png] |

### visual_option_anchor_boundary_uncertain (4 unique questions)

| Year | Question | Pages | Evidence / issue |
|---|---|---|---|
| 2003 | 12 | 7–7 | visual_option_anchor_boundary_uncertain:manual_review [assets/b50f7fbc103ff2982062/bmat_2003_q012_r012_p007_asset_04_b2113ffc13.png] |
| 2003 | 16 | 9–9 | visual_option_anchor_boundary_uncertain:manual_review [assets/b50f7fbc103ff2982062/bmat_2003_q016_r016_p009_asset_05_baeab4b53c.png] |
| 2003 | 35 | 17–17 | visual_option_anchor_boundary_uncertain:manual_review [assets/b50f7fbc103ff2982062/bmat_2003_q035_r035_p017_asset_08_4d8b64d8f7.png] |
| 2003 | 40 | 19–19 | visual_option_anchor_boundary_uncertain:manual_review [assets/b50f7fbc103ff2982062/bmat_2003_q040_r040_p019_asset_04_681a922eec.png] |

## Document / range issues

None detected.
