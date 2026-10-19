<!-- bmat-categorization-report-v1 -->
# BMAT categorization issues

Only current unresolved decisions are active issues. Intentional skips and unattempted normal attribution are counted separately; neither is a successfully matched dataset.
Independent upstream defects on skipped records remain in BMAT_RAW_ISSUES.md and BMAT_CLEANING_ISSUES.md; exclusion does not repair them.

```json
{
  "records": 664,
  "unique_review_questions": 3,
  "statuses": {
    "needs_review": 3,
    "supported": 148,
    "not_evaluated": 178,
    "intentional_skip": 335
  },
  "skipped_with_upstream_defects": 7
}
```

## upstream_defect (3 unique questions)

| Year | Question | Reason |
|---|---|---|
| 2003 | [1](../inspections_bmat_categorization/2003_q001.html) | Upstream defects remain: visual_neighbor_boundary_uncertain |
| 2004 | [14](../inspections_bmat_categorization/2004_q014.html) | Upstream defects remain: visual_component_association_uncertain |
| 2021 | [8](../inspections_bmat_categorization/2021_q008.html) | Upstream defects remain: incomplete_or_ambiguous_options, visual_caption_boundary_uncertain, visual_caption_may_be_incomplete, visual_component_association_uncertain, visual_option_labels_ambiguous |
