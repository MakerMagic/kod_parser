## Current milestone

Blackstone clean questions + TSA 2008–2016 explained answers → matched structured dataset.

## Current focus

2017–2019 supplied explanation imports and visual review: 97 text explanations matched by exact identity; 39 visual explanations accepted using the existing prompt/validator and inspected stored assets. Twelve visual cases remain unresolved (five structural, seven requiring stronger geometric proof); two text-sufficient illustrated cases are excluded from image-only generation. Match conflicts remain unchanged. Canonical HTML and no-explanation exports are rebuilt. Reapply via `processors.matching.explanation_imports`; see `docs/2017-2019_questions_images_with_explanation_ai_generated/README.md`. No Gemini API calls or raw/clean changes.

Gemini-only rate-limit classification/backoff/jitter and configurable successful-request cooldown added; prompt, validator, generic generator/scheduler/backtest hashes unchanged. Configured 3.5 Flash Q1–Q5 pilot: first API call returned 429 with provider retry delay 23,643 seconds; remaining calls correctly withheld, 0/5 outputs and five resumable provider failures, no quality rejections. Validation: 139 tests, Ruff and five read-only HTML/text/JSON inspections passed. No fallback/full batch. Report and backtests: `docs/ai_explanations/EXPLANATION_FLASH35_RUN.md`.

Semantic explanation safeguards added: explicit coexistence/assumption prompt rules and a documented, candidate-bound reasoning-review gate before acceptance. Q5 calibration, the same Q1–Q5 pilot and Q9/Q16/Q17 sample returned no output after rate-limited retries on the unchanged configured model. Q5's semantic error is NOT verified fixed. Interrupted sample preserved; connection-close transport handling regression added. Validation: 115 tests, Ruff, read-only HTML/text/JSON and PowerShell syntax checks passed. Canonical/source explanations unchanged; no full batch started. Actual outcomes and backtests: `docs/ai_explanations/EXPLANATION_SEMANTIC_REVIEW.md`.

Parse answers and explanations from `TSA-2008-2016-Explained-Answers.pdf`, then match them to existing clean Blackstone questions.

## Already completed

- BMAT continuation: 664 records, 326 clean-ready / 335 intentional skips / three upstream reviews; ten genuine RAW defects (seven independently skipped), zero cleaning-specific defects. `too long` uses >60% usable height to final option; Q18's verified bullet glyph clears its defect but 75.44% occupancy remains excluded. Compact shared declarations repair 2015 Q18/Q31; 667 question-only previews preserve all 524 source-page texts and 669 historical preview PNGs. Worked solutions: 594 parsed source records, 287 initial eligible matches. Task-supplied 98 text records add 14 matches; 48 existing explanations preserved, 27 skips, one upstream defer, eight source reviews; current verified matches 295. No imported images or generated explanations. Categorization remains 148 supported / 178 unattempted / three genuine reviews / 335 skips, with fresh matching context. Reports: `docs/BMAT_{RAW,CLEANING,MATCHING,CATEGORIZATION}_{ISSUES,BACKTEST}.md`; audit: `inspections_bmat/repair/validation.json`. Missing supplied 2011 Q15 header and source inconsistencies remain explicit.

- Representation/rulebook refinement: decoded option anchors, image-cell ownership, certified blank raster bands and detached chart legends repaired RAW body/answer separation; CLEAN recognises conditional sentence-completion prompts. RAW/CLEAN/matching propagated with all 750 raw question blocks and Final Explanations preserved. All ten new regressions pass: 12 prior reviews resolved, five accepted subtypes corrected, none withdrawn; current support 722/750, 25 PS reviews and three unclassified. All 265 affected/review HTMLs rebuilt; current evidence audit: `inspections_categorization/representation_refinement/validation.json`. No explanation generation.

- Controlled Problem-Solving rulebook review: all 260 previously for-review PS records assessed; 225 resolved (12 multi-label), 35 retained with concrete reasons. The other 490 records, RAW/CLEAN/matching, answers and explanations are unchanged. Content-bound decisions: `categorization/ps_review_decisions.tsv` / `ps_review.json`; reproduce with `categorization review`. Current totals: 710 supported, 37 needs_review (35 PS + two excluded CT), three unclassified. Complete review trail: `docs/CATEGORIZATION_BACKTEST.MD`.

- Rulebook review completion verified after interruption: all 260 HTML inspections and 509 local links pass; persisted labels/multi-labels match bound decisions. Issues list contains only 40 unique unresolved records; resolved history stays in backtesting, not active issue rows. Focused review tests 41/41 and categorization regressions 111/111 pass; reports regenerate byte-identically. Saved checks: `inspections_categorization/rulebook/validation.json`.

- Semantic categorization refinement: v3 context-gated principle/impact/inference and procedural/tariff families, 64 reviewed examples. All 750 rows re-evaluated; 11 unclassified + five needs_review resolved, all 469 prior accepted labels retained. Current support 485/750 (373 CT, 112 PS), 265 unresolved. CLEAN-only 2009 Q17/Q14 prompt joins corrected with separately declared rules; RAW/answers/explanations preserved and legacy matching/handoff rebuilt. Before/after audit: `inspections_categorization/before_semantic_refinement.json`; current QA: `docs/CATEGORIZATION_BACKTEST.MD`.

- Categorization refinement: CLEAN recovers answer-completed colon prompts (2010 Q32, 2012 Q16); affected CLEAN/matching rebuilt and handoff refreshed, RAW/answers/explanations preserved. Catalogue v2 adds category modality/engine metadata and spatial equivalence patterns; decorative/preview references are not meaningful visuals. 59 reviewed examples; 17 prior unresolved assignments supported, eight prior selection labels corrected, three geometric-composition labels withdrawn for review. Current support: 469/750 (363 CT, 106 PS); 281 unresolved. Full before/after audit and HTML links: `docs/CATEGORIZATION_BACKTEST.MD`; reasons: `docs/categorization_issues.md`.

- Independent official 2020 profile verified: 50 full explanations / 50 matches, 26 explicit and 24 semantic answer inferences; all six supplied anchors pass. Complete text/evidence agrees with independent PDFium extraction; 50 HTML inspections are saved. Reparse is byte-identical and 36 pre-existing RAW/CLEAN/other-year matched JSONs remain unchanged. Q12's existing clean symbol-order review and Q25's raw caption review remain visible, not suppressed. Commands: `docs/MATCHING_2020_BACKTEST.md`.

- RAW structural grouping fixes 2019 Q36's detached dimension and 2016 Q37's fragmented mushroom arrays (3→2 / 48→2 assets). Isolated reparsing of all 800 questions changed only these two records' visual fields; text/identity/options and original PNGs remain preserved. Affected RAW/CLEAN and dependent matching snapshots/reports regenerated; existing issue counts and ambiguous cases remain unchanged. Full suite: 457 passed; focused lint/format checks passed; regenerated PNG crops visually checked.
- Matching derives ordered `final_explanation` blocks without modifying source components. With the approved manual supplements, 550 explanations are available and 150 answer-only records remain explicitly unavailable. HTML retains component debugging sections; original raw/clean inputs and assets stay immutable.
- Added pinned manual explanations for 2008 Q12 (supplied screenshot) and 2016 Q38 (confirmed notation, structured list, existing final takeaway retained). Original PDF candidates/warnings/previews remain archived and visible in a manual-supersession report table, not claimed parser fixes. Only these two of the 450 legacy merged records changed; 163 matching/explanation regressions pass.

- Python environment created.
- GitHub repository connected.
- Basic project documentation added.
- Codex skills added.
- `AGENTS.md` added.
- Initial folder structure prepared.
- First Blackstone raw parser and CLI implemented in `parsers/blackstone/`.
- Full page text, question spans, source metadata, options, graphics references, and warnings preserved in raw JSON.
- Parser regression tests and local PDF validation added; no new dependencies.
- All 16 local PDFs parsed into 800 numbered raw records; 18 tests pass. Unresolved extraction details remain flagged.
- Raw question inspection and separate parsing-issues reports added, including automatic reporting after parser CLI runs.
- Current issues snapshot stored in `docs/RAW_PARSING_ISSUES.md`; raw JSON remains unchanged by backtesting.
- Raster/vector crops and question-page layout PNGs saved with ordered raw JSON references; universal self-contained HTML inspection added alongside text/JSON inspection.
- All 16 local PDFs reparsed with visual assets; original page/question/option text and identity fields verified unchanged. Visual extraction/missing-file issues are included in the refreshed report.
- Focused crops now exclude external prose while retaining diagram/table labels. Ordered raw-span-backed layout blocks and option image associations are shown in HTML; duplicate/shared choice geometry remains unresolved.
- Previous validation: 61 tests and lint/format checks passed. Attached 2010 questions 7/12, image-choice questions 14/20, and previously good 2022 question 50 have regression checks; original text/options/subparts remained preserved across all 800 records.
- All 16 PDFs regenerated with the refined geometry/association rules; saved-asset references and read-only text/JSON/HTML inspection validated.
- Fixed 2022 Q8/Q20 crop regressions with wrapped-paragraph barriers, nearest-graphic text ownership, and baseline-aware rotated labels. Repeated image choices now recover A–E without treating internal chart/table text as answer text; initial text candidates remain raw.
- Current validation: 67 tests plus lint/format checks pass. All 16 PDFs regenerated; all 800 raw page/question/options blocks, spans, identities, question text, and subparts verified unchanged. Structured option corrections are limited to 2022 Q8 and 2021 Q32; the visual issues report and HTML previews were refreshed.
- Graph-specific grouping now joins detached chart guides, respects one-letter/one-image option cells, and reconstructs rotated axis labels from PDF glyph order. 2021 Q26/Q37/Q38 were reparsed; Q32 option PNGs and 2017 Q13's rotated-text visual remain bit-identical, 2022 Q8/Q20/Q50 controls pass, and 2020 Q25 is an additional axis-label control. Current validation: 73 tests plus lint/format checks pass; the issues report was refreshed.
- Image-choice crops now exclude neighboring structural option letters; a crop that cannot be separated remains saved but unassigned and appears in QA. 2011 Q50 A no longer contains B. The issues report is grouped by nonempty categories with deterministic row order. All 16 local PDFs were reparsed and the report refreshed; vertical/grid/graph controls remain associated. Current validation: 76 tests, lint, and format checks pass.
- Image-answer association now accepts only a left-side option anchor. Invisible white vector masks and text-enclosure page frames no longer become visual assets; 2011 Q7 and text-only 2012 Q3 were regenerated and the aggregate issues report refreshed. Current validation: 78 tests plus lint/format checks pass.
- Verified the shifted CID font encoding in the 2012–2014 Oxford papers and decoded structured question/option text while preserving original CID page/question spans. Reparsed those three papers; the CID question-and-all-options issue count fell from 148 to 0. The generated issues report now shows per-category counts and a CID subcategory; 52 parser/backtest/visual tests pass.
- Page-margin white vector frames no longer become question visuals or merge into tables. Closed table borders now define focused crops, and a single enclosing option contour can resolve false per-edge ownership. All 16 PDFs were reparsed; the 2015 question-level issue count fell from 50 to 0, while the genuinely merged 2016 Q32 remains flagged. All 800 question numbers, page references, raw blocks, text, options, and subpoints matched the pre-change baseline; 80 focused tests pass.

- PDF drawing color spaces now preserve black spot-color grids, including the complete 2017 Q20 table. Category counts include unique document/page/question records; Source Metadata correctly shows 16 records without hiding provenance warnings. PowerShell parsing/inspection/report/test commands were verified. All 16 papers were reparsed; all 800 raw/text/numbering/page/option records matched the baseline, and representative existing crop pixels/associations stayed unchanged. 86 tests plus lint/format checks pass.

- Initial conservative Blackstone cleaning added under `processors/normalization/blackstone/`: separate clean JSON, complete raw snapshots/hashes/pointers, preserved warnings/assets, ordered body/prompt/options, and offline HTML comparison. All 800 clean records generated and audited; raw JSON and the renamed raw issues report remain byte-identical. Raw QA exports moved to `inspections_raw/`; clean QA uses `inspections_clean/`. Full suite: 117 passed; final cleaning/backtest safeguards: 51 passed; lint/format pass.

- Raw graph-cell top-guide handling now recognizes 2017 Q20's five A–E images without weakening foreign-letter boundaries; only that paper was reparsed. Cleaning saves separate geometry-verified answer crops and uses them in HTML: 246 derivatives audited (83 glyph removals, 163 unchanged copies), with every other answer pixel preserved. All 4,055 raw PNGs remain byte-identical; all 800 raw core text/identity/page/option records are preserved. Full suite: 138 passed; final clean/unsafe-crop checks: 49 passed; lint/format pass. Shared/unassigned raw visuals remain unresolved.

- Sentence-aware cleaning resolves 65 of 75 missing prompts, retains attached notes (including 2011 Q43), and separates introduced structured blocks in 59 records (including 2011 Q37). All 800 records were audited: 723 existing prompts unchanged, two detached-note corrections, unchanged options/assets/raw snapshots, complete fragment accounting and stable repeat formatting. All 4,071 raw files remain byte-identical. Full suite: 170 passed; lint/format pass. Ten incomplete/implicit/corrupt prompt cases remain reported.

- Traced 2020 Q25/Q36 to body graphics, not failed image answers. Raw body projection now excludes verified interleaved page administration while preserving original text; clean alignment recognizes exact initial number-only anchors. Reparsed 2017–2021 and regenerated all 800 clean records: eight layout alignments recovered, six additional clean issue-free records (739→745). All 4,055 raw PNGs, raw page/question/option blocks and image associations remain unchanged; Q25's caption review and genuinely shared/unassigned visuals remain flagged. Full suite: 185 passed; lint/format pass. Regression coverage: `tests/test_blackstone_body_alignment.py`.

- Verified CID spatial interpretation and identical-glyph deduplication now resolve the 2012 Q8 answer group/crop and analogous 2012–2014 choices; specimen Q36 also recovers C–E images. All 800 records were regenerated, with original raw text/identity fields and all 1,520 previously referenced PNGs unchanged. Reports: 19 raw question reviews, 54 unique clean reviews; 36 separate CID/body alignments and genuine shared visuals remain unresolved. Full suite: 201 passed; lint/format checks pass.

- Clean layout now verifies CID blocks by exact raw spans and the upstream verified map, not line counts. This fixes 2012 Q19 table duplication and Q38 placement plus all 36 analogous alignments (18 visual-text duplication cases); no raw parser/asset changes were needed. All 800 clean records regenerated: unique reviews 54→18, unchanged prompts/options/derivatives and previously-correct body content/order. Raw files/report remain byte-identical; unknown/shared visuals retain warnings. Full suite: 223 passed; lint/format checks pass.

- Readiness verified for 450 unique 2008–2016 clean questions. Independent local answer-source parsing and exact-key matching added: 450 SECTION 1 answers, 449 matches, one preserved 2014 Q50 option conflict. Paragraphs, lists, cross-page content, source PNGs, raw/clean snapshots/hashes/pointers, grouped matching issues, and offline HTML/text/JSON inspection are retained. No question raw/clean code or outputs changed.
- Six matching/source QA questions remain: 2014 Q50; image-only 2008 Q12 explanation; unmapped 2016 Q9/Q21/Q33 elimination items; encoded 2016 Q38 list markers. All 223 existing regressions passed; final 24 source/matching tests pass on rebuilt, frozen inputs. PowerShell commands and unchanged raw/clean content hashes verified.

- Explanation classifier v2 restores Q38 post-list prose and complete Q9/Q21/Q33 incorrect-answer sections; 18 additional diamond-labelled sections and Q43's standalone marker are recovered. All 450 raw excerpts/identities/answer letters/previews and correct control projections are preserved; 37 projections improve. Canonical answer/matching outputs and issues were regenerated, with 449 matches and the existing 2014 Q50 conflict unchanged. All 66 source/matching regressions pass; numbered-option mapping and encoded score text remain flagged.

- Verified 2016 Q9/Q21/Q33 against source previews: intact numbered elimination lists do not supply individual option letters and are no longer falsely reported as parsing failures (profile v3); no letters inferred. Answer/matched outputs and issues regenerated: three genuine QA cases remain (2016 Q38 encoded score text, 2008 Q12, 2014 Q50). All 450 explanation contents/page extractions and question raw/clean files are unchanged; 72 source/matching regressions pass.

- Added independent Blackstone 2021/2022 explanation parsing with anchored boundaries, excluded page headers, cross-page paragraphs/lists, ordered visual crops and year-scoped matching/HTML QA. Real Q48 2021 table verified; 50/50 matches in 2021, 48/50 in 2022. Missing Q46 source header/answer and Q45 boundary remain reported. All 99 answer declarations agree with independent PDFium extraction; 87 focused regressions pass (final matching/visual rerun: 32). Legacy parser/outputs and question raw/clean hashes remain unchanged.

- Verified 2022 Q45's complete expected prose/list/prose against the PDF and final HTML; numbering gaps no longer falsely invalidate the previous explanation, while orphan declarations remain flagged. Confirmed list lead-ins are separated in Q45/Q37 without losing text. User corrected Q46's year to 2022 and supplied an exact manual explanation/C answer: versioned single-question source, separate manual intermediate, target-key/hash checks and visible provenance; 50/50 2022 matches. The real PDF header omission stays reported. All 96 focused tests pass; all 99 existing answer raw/identity/asset records and protected legacy/question raw/clean files remain unchanged.

- Independent 2017–2019 answer-key parsing verified all 150 answers against PDFium: 148 matches, two preserved upstream option conflicts (2018 Q20, 2019 Q32). Grouped issues and offline row/question HTML QA added. Explicit Q44 2022 clean-body pin retains the supplied composite across a complete raw→clean→matching rerun; raw assets, other 49 clean questions and legacy matching results remain unchanged. Validation: 214 focused tests, 18 final source/pin checks, lint and PowerShell syntax checks pass.

- Cleaning-only capitalized-wrap fix regenerated all 800 clean questions: 77 prose records improved (71 bodies, six prompts), including 2019 Q33 and analogous existing issue records. Exact raw layout/relative geometry supplies evidence, not proper-name dictionaries. All content, paragraph gaps, identities/options/warnings/assets remain preserved; 5,303 raw/reference hashes unchanged. Dependent matching snapshots refreshed without changing statuses/issues. Validation: 179 focused regressions and stored clean/matched HTML checks pass; unrelated incomplete prompts/visuals remain unresolved.
- Text-only AI-explanation work now starts from the restored answer-key-only 2017–2019 snapshot. A separate strict eligibility/validation overlay and QA report exist; no discarded generated explanation was retained or restored. Eligible records remain pending a quality-validated generation source rather than receiving generic text.

## Code navigation

- Semantic triage/review evidence: `processors/explanations/validator.py`; candidate-bound approval: `generator.approve_after_quality_review`; regressions: `tests/test_explanation_semantics.py`. Structural pass alone stays pending, not accepted.

- Deferred-provider queue: `processors/explanations/scheduler.py`; orchestration/resume/metrics: `generator.py`; regressions: `tests/test_explanation_deferred.py`.

- Answer-only profile: `parsers/blackstone_answer_keys/`; tests: `tests/test_blackstone_answer_keys.py`; commands/report: `MATCHING_2017-2019_BACKTEST.md` / `MATCHING_2017-2019_ISSUES.md`.
- Explicit clean-body pins: clean module `body_assets.py` / `pinned_sources/`; tests: `tests/test_blackstone_pinned_body.py`.

- Independent 2021/2022 Blackstone explanation profile: `parsers/blackstone_explained_answers/`; regression tests: `tests/test_blackstone_explained_answers.py`. Year-scoped matching/HTML commands: `docs/MATCHING_2021_BACKTEST.md` and `docs/MATCHING_2022_BACKTEST.md`.
- Explicit manual source import: `parsers/manual_explanations.py`; approved Q46 source: `processors/matching/manual_sources/tsa_2022_q046.json`; continuation/manual regressions: `tests/test_blackstone_explanation_continuation.py`.

- Explained-answer source parser/CLI: `parsers/explained_answers/`; tests: `tests/test_explained_answers.py`.
- Generic matching/readiness/report/inspection: `processors/matching/`; tests: `tests/test_matching.py`; commands: `docs/MATCHING_2008-2016_BACKTEST.md`.

- Clean transformation/CLI: `processors/normalization/blackstone/`; tests: `tests/test_blackstone_cleaning.py`.
- Derived answer PNGs: `option_assets.py` / `png_pixels.py` in the clean module; regression tests: `tests/test_blackstone_option_asset_crops.py`.
- Body/prompt and introduced-block rules: `structure.py` / `text.py`; regressions: `tests/test_blackstone_clean_structure.py`.
- Capitalized prose-wrap geometry/alignment: `text.py` / `structure.question_line_context`; regressions: `tests/test_blackstone_prose_wraps.py`.
- Clean output: `data/clean/blackstone/*.clean.json`; commands: `docs/CLEANING_BACKTEST.md`.
- Reports: `docs/RAW_PARSING_ISSUES.md` and `docs/CLEANING_ISSUES.md`; raw inspection commands remain unchanged.
- CID spatial word/paragraph regressions: `tests/test_blackstone_cid_visual_layout.py`.
- Clean visual ownership/CID span alignment: `tests/test_blackstone_clean_visual_body.py`.

## Do not work on yet

- final dataset generation;
- additional sources.

## Next task

- Review the 11 remaining BMAT RAW defects (three non-skipped, eight also skipped). Shared/overlapping visual envelopes, outlined labels and unknown fonts remain unresolved. Do not infer matching completion or normal PS categories from the targeted CT pass; matching, normal PS attribution and explanation generation require a separate task.

- Manually backtest the current refinement trail and investigate the remaining 25 PS reviews: 11 below semantic thresholds, nine source/explanation conflicts, two incomplete extractions, two taxonomy boundaries and one insufficiently specified task. Three unclassified records remain. Assistant assessments are not human approval; do not generate explanations or repair unrelated upstream issues implicitly.

- Review the imported/visual 2017–2019 explanations through the new HTML index and twelve unresolved cases in the year-specific workspace reports. Historical Gemini pilot commands remain inactive.

- Independent CLEAN limitation: 2016 Q37 retains the declarative "When I looked..." sentence in Main Question, despite correct RAW ordering between the two now-complete diagrams. Grouping does not resolve this body/prompt classification; review separately without a question-specific exception.
- The 2018 Q20 and 2019 Q32 option-label conflicts are now repaired in RAW and match source answers B/C. Keep the 2022 Q44 manual composite scoped to the approved source/key.

- Keep the supplied PDF's Q46 header omission traceable; replace the approved 2022 manual supplement only with verified source evidence. Do not turn it into an automatic missing-explanation fallback.
- The 2014 Q50 option conflict is repaired and source answer B is matched. Keep 2008 Q12 / 2016 Q38's original source failures traceable alongside their approved manual explanations.
- Expand manual explanation/screenshot fidelity checks before any downstream stage.
