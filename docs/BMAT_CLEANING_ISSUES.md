<!-- bmat-clean-report-v1 -->
# BMAT cleaning issues

Intentional skips remain stored and are not cleaning defects. Upstream defects are propagated, never repaired or concealed by cleaning.

```json
{
  "records": 664,
  "status_counts": {
    "upstream_review": 3,
    "clean_ready": 326,
    "intentional_skip": 335
  },
  "unique_upstream_issue_questions": 10,
  "unique_cleaning_specific_issue_questions": 0,
  "unique_issue_questions": 10
}
```

## A. Propagated RAW defects (10 unique questions)

### font_encoding_artifacts (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2017 | [28](../inspections_bmat_clean/2017_q028.html) | intentional_skip | font_encoding_artifacts:unverified_glyphs_preserved |

### foreign_option_letter_in_crop (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2003 | [40](../inspections_bmat_clean/2003_q040.html) | intentional_skip | foreign_option_letter_in_crop:C->D [assets/b50f7fbc103ff2982062/bmat_2003_q040_p019_geometry_a0e29dbbf8.png] |

### incomplete_or_ambiguous_options (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2021 | [8](../inspections_bmat_clean/2021_q008.html) | upstream_review | incomplete_or_ambiguous_options:noncontiguous_label_candidates |

### option_content_unresolved (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2011 | [34](../inspections_bmat_clean/2011_q034.html) | intentional_skip | option_content_unresolved:D |

### options_not_detected (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2005 | [8](../inspections_bmat_clean/2005_q008.html) | intentional_skip | options_not_detected:requires_source_inspection |

### visual_caption_boundary_uncertain (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2021 | [8](../inspections_bmat_clean/2021_q008.html) | upstream_review | visual_caption_boundary_uncertain:external_caption_preserved [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_13_c5059495a7.png] |

### visual_caption_may_be_incomplete (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2021 | [8](../inspections_bmat_clean/2021_q008.html) | upstream_review | visual_caption_may_be_incomplete:local_text_preserved_in_layout [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_12_bbcfcb7e76.png] |

### visual_component_association_uncertain (3 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2004 | [14](../inspections_bmat_clean/2004_q014.html) | upstream_review | visual_component_association_uncertain [assets/bf878c35d9f91132da01/bmat_2004_q014_r014_p009_asset_01_20f43d92d0.png] |
| 2011 | [34](../inspections_bmat_clean/2011_q034.html) | intentional_skip | visual_component_association_uncertain [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |
| 2021 | [8](../inspections_bmat_clean/2021_q008.html) | upstream_review | visual_component_association_uncertain [assets/79ddc2445760dcf85ae6/bmat_2021_q008_r008_p008_asset_13_c5059495a7.png] |

### visual_image_option_mapping_inconsistent (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2011 | [31](../inspections_bmat_clean/2011_q031.html) | intentional_skip | visual_image_option_mapping_inconsistent:F [assets/a8ffa678ede8f746feb3/bmat_2011_q031_r031_p025_asset_14_2154ae6569.png] |

### visual_multiple_option_images_merged (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2011 | [34](../inspections_bmat_clean/2011_q034.html) | intentional_skip | visual_multiple_option_images_merged:shared_geometry_requires_review [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |

### visual_neighbor_boundary_uncertain (2 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2003 | [1](../inspections_bmat_clean/2003_q001.html) | upstream_review | visual_neighbor_boundary_uncertain:touching_native_envelopes [assets/b50f7fbc103ff2982062/bmat_2003_q001_p003_option_E_fe47fa0ab3.png] |
| 2011 | [5](../inspections_bmat_clean/2011_q005.html) | intentional_skip | visual_neighbor_boundary_uncertain:content_bounds_overlap [assets/a8ffa678ede8f746feb3/bmat_2011_q005_r005_p006_asset_01_e33c7fbd76.png] |

### visual_option_anchor_boundary_uncertain (2 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2009 | [25](../inspections_bmat_clean/2009_q025.html) | intentional_skip | visual_option_anchor_boundary_uncertain:manual_review [assets/f2b39a709c6add90186d/bmat_2009_q025_r025_p019_asset_03_1c8a7e94bf.png] |
| 2011 | [34](../inspections_bmat_clean/2011_q034.html) | intentional_skip | visual_option_anchor_boundary_uncertain:manual_review [assets/a8ffa678ede8f746feb3/bmat_2011_q034_r034_p027_asset_02_7a3b3d92d8.png] |

### visual_option_labels_ambiguous (1 unique questions)

| Year | Question | Status | Reason |
|---|---|---|---|
| 2021 | [8](../inspections_bmat_clean/2021_q008.html) | upstream_review | visual_option_labels_ambiguous:duplicate_structural_labels |

## B. Cleaning-specific defects (0 unique questions)

None detected.
