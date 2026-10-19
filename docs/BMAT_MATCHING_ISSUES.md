# BMAT Section 1 matching issues

Counts are unique question records. Intentional skips are policy exclusions, not parser errors.

```json
{
  "questions": 664,
  "eligible": 326,
  "parsed_explanations": 594,
  "unique_parsed_question_identities": 592,
  "unresolved_sources": 72,
  "unique_unresolved_source_identities": 71,
  "duplicate_source_question_identities": 37,
  "statuses": {
    "deferred_upstream_issue": 3,
    "matched": 295,
    "intentionally_skipped": 335,
    "source_unresolved": 5,
    "duplicate_source": 1,
    "supplied_review_required": 2,
    "source_missing": 17,
    "explanation_review_required": 6
  },
  "supplied_imports": {
    "records": 98,
    "by_year": {
      "2011": 34,
      "2021": 32,
      "2020": 32
    },
    "statuses": {
      "intentionally_skipped": 27,
      "matched_supplied": 14,
      "supplied_review_required": 8,
      "existing_preserved": 48,
      "deferred_upstream_issue": 1
    },
    "target_missing": 0,
    "missing_numbers_in_supplied_years": {
      "2011": [
        15
      ],
      "2020": [],
      "2021": []
    }
  }
}
```

## Source acquisition/parser issues

```json
{
  "acquisition_issues": [
    {
      "code": "year_or_section_unavailable",
      "year": 2014,
      "reason": "No question links found"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 1,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-1.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 2,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-2.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 3,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-3.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 4,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-4.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 5,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-5.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 6,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-6.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 7,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-7.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 8,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-8.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 9,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-9.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 10,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-10.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 11,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-11.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 12,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-12.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 13,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-13.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 14,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-14.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 15,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-15.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 16,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-16.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 17,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-17.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 18,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-18.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 19,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-19.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 20,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-20.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 21,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-21.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 22,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-22.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 23,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-23.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 24,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-24.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 25,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-25.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 26,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-26.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 27,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-27.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 28,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-28.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 29,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-29.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 30,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-30.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 31,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-31.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 32,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-32.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 33,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-33.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 34,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-34.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    },
    {
      "code": "question_download_failed",
      "source_family": "bmat",
      "year": 2011,
      "section": "section_1",
      "question_number": 35,
      "source_url": "https://bmatsolutions.blogspot.com/p/2011-section-1-question-35.html",
      "status": "failed",
      "error": "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored"
    }
  ],
  "unresolved_source_reasons": {
    "malformed_answer_header": 33,
    "ValueError: Source host deferred after repeated verified transport/TLS failures; rerun with --retry-failed-hosts after connectivity is restored": 35,
    "source_title_identity_mismatch": 1,
    "explanation_asset_missing_or_changed": 2,
    "answer_header_image_only_or_missing": 1
  },
  "unique_questions_by_source_reason": {
    "malformed_answer_header": 33,
    "download_failed": 35,
    "source_title_identity_mismatch": 1,
    "explanation_asset_missing_or_changed": 2,
    "answer_header_image_only_or_missing": 1
  }
}
```

## Active matching / deferred records

### deferred_upstream_issue (3 unique questions)

| Year | Question | Status | Correct answer |
|---|---|---|---|
| 2003 | [1](../inspections_bmat_matching/2003_q001.html) | deferred_upstream_issue | — |
| 2004 | [14](../inspections_bmat_matching/2004_q014.html) | deferred_upstream_issue | — |
| 2021 | [8](../inspections_bmat_matching/2021_q008.html) | deferred_upstream_issue | — |

### duplicate_source (1 unique questions)

| Year | Question | Status | Correct answer |
|---|---|---|---|
| 2008 | [12](../inspections_bmat_matching/2008_q012.html) | duplicate_source | — |

### explanation_review_required (6 unique questions)

| Year | Question | Status | Correct answer |
|---|---|---|---|
| 2020 | [18](../inspections_bmat_matching/2020_q018.html) | explanation_review_required | D |
| 2020 | [23](../inspections_bmat_matching/2020_q023.html) | explanation_review_required | B |
| 2020 | [24](../inspections_bmat_matching/2020_q024.html) | explanation_review_required | B |
| 2020 | [25](../inspections_bmat_matching/2020_q025.html) | explanation_review_required | D |
| 2020 | [30](../inspections_bmat_matching/2020_q030.html) | explanation_review_required | C |
| 2021 | [24](../inspections_bmat_matching/2021_q024.html) | explanation_review_required | A |

### source_missing (17 unique questions)

| Year | Question | Status | Correct answer |
|---|---|---|---|
| 2014 | [1](../inspections_bmat_matching/2014_q001.html) | source_missing | — |
| 2014 | [2](../inspections_bmat_matching/2014_q002.html) | source_missing | — |
| 2014 | [3](../inspections_bmat_matching/2014_q003.html) | source_missing | — |
| 2014 | [4](../inspections_bmat_matching/2014_q004.html) | source_missing | — |
| 2014 | [6](../inspections_bmat_matching/2014_q006.html) | source_missing | — |
| 2014 | [7](../inspections_bmat_matching/2014_q007.html) | source_missing | — |
| 2014 | [12](../inspections_bmat_matching/2014_q012.html) | source_missing | — |
| 2014 | [13](../inspections_bmat_matching/2014_q013.html) | source_missing | — |
| 2014 | [15](../inspections_bmat_matching/2014_q015.html) | source_missing | — |
| 2014 | [16](../inspections_bmat_matching/2014_q016.html) | source_missing | — |
| 2014 | [17](../inspections_bmat_matching/2014_q017.html) | source_missing | — |
| 2014 | [18](../inspections_bmat_matching/2014_q018.html) | source_missing | — |
| 2014 | [22](../inspections_bmat_matching/2014_q022.html) | source_missing | — |
| 2014 | [24](../inspections_bmat_matching/2014_q024.html) | source_missing | — |
| 2014 | [25](../inspections_bmat_matching/2014_q025.html) | source_missing | — |
| 2014 | [26](../inspections_bmat_matching/2014_q026.html) | source_missing | — |
| 2014 | [30](../inspections_bmat_matching/2014_q030.html) | source_missing | — |

### source_unresolved (5 unique questions)

| Year | Question | Status | Correct answer |
|---|---|---|---|
| 2004 | [12](../inspections_bmat_matching/2004_q012.html) | source_unresolved | — |
| 2005 | [24](../inspections_bmat_matching/2005_q024.html) | source_unresolved | — |
| 2016 | [16](../inspections_bmat_matching/2016_q016.html) | source_unresolved | — |
| 2016 | [29](../inspections_bmat_matching/2016_q029.html) | source_unresolved | — |
| 2019 | [1](../inspections_bmat_matching/2019_q001.html) | source_unresolved | — |

### supplied_review_required (2 unique questions)

| Year | Question | Status | Correct answer |
|---|---|---|---|
| 2011 | [4](../inspections_bmat_matching/2011_q004.html) | supplied_review_required | — |
| 2011 | [16](../inspections_bmat_matching/2011_q016.html) | supplied_review_required | — |

## Intentional exclusions

335 targets remain skipped. Full per-question reasons/source candidates are available in the [backtest](BMAT_MATCHING_BACKTEST.md).
