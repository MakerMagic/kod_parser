<!-- bmat-categorization-report-v1 -->
# BMAT categorization issues

Only current unresolved decisions are active issues. Each supported/intentional-skip result has one canonical category. Categorization is not a claim of successful matching or upstream repair.
Independent upstream defects on skipped records remain in BMAT_RAW_ISSUES.md and BMAT_CLEANING_ISSUES.md; exclusion does not repair them.

```json
{
  "records": 664,
  "unique_review_questions": 5,
  "statuses": {
    "needs_review": 5,
    "supported": 316,
    "intentional_skip": 343
  },
  "skipped_with_upstream_defects": 7
}
```

## input_representation_review (2 unique questions)

| Year | Question | Reason |
|---|---|---|
| 2011 | 13 | Evaluate new evidence strengthening the HAR1-language hypothesis, not explain the phenomenon itself. The source preview confirms displaced option boundaries in CLEAN; defer acceptance pending that upstream repair. |
| 2015 | 29 | Compute wall areas net of openings, coats and whole-tin optimization. The source preview shows A-H in two columns but CLEAN merges E-H into A-D; defer acceptance until upstream options are repaired. |

## upstream_defect (3 unique questions)

| Year | Question | Reason |
|---|---|---|
| 2003 | 1 | Upstream defects remain: visual_neighbor_boundary_uncertain |
| 2004 | 14 | Upstream defects remain: visual_component_association_uncertain |
| 2021 | 8 | Upstream defects remain: incomplete_or_ambiguous_options, visual_caption_boundary_uncertain, visual_caption_may_be_incomplete, visual_component_association_uncertain, visual_option_labels_ambiguous |
