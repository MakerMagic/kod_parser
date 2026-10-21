# Matching → categorization handoff

Canonical matching remains `data/merged/blackstone/*.matched.json` (top-level
files only; archived AI pilots are not inputs). The current persisted scope is
750 records, all matched. Final Explanation is available on 736
records (600 source/manual, 136 accepted AI); 14 remain unavailable. A successful
identity/answer match does not certify the reasoning of an existing explanation.

`data/categorized/blackstone/matching_handoff.json` pins each canonical file,
record pointer/content digest, referenced inputs, original/source/derived assets
and manual/AI explanation sources. No competing matching format or rewritten
question dataset is created. Categorization checks this manifest before use;
changing a dependency produces an explicit failure, not stale silent reuse.
Keep the canonical files, their referenced dependencies and this manifest together
when preserving the working dataset. This is a hash lock, **not an archival backup**.

During categorization refinement, the CLEAN-only colon-prompt rule intentionally
updated 2010 Q32 and 2012 Q16. The two clean documents and dependent 2008–2016
matching artifact were rebuilt through their supported commands before explicitly
refreshing this handoff. All 750 correct answers/Final Explanations, other-year
canonical matching artifacts, RAW JSON and original assets remained unchanged.
The saved categorization QA baseline pins the previous hashes for audit; it is not
an alternate matching input. A premature handoff refresh was correctly blocked
while upstream hashes were stale; no mismatch was bypassed.

The subsequent semantic refinement refreshes only the 2009 clean document and
dependent legacy matching after verified prompt-word boundary repairs (Q17/Q14).
RAW JSON/PNGs and all stored correct answers/Final Explanations remain unchanged.
The corresponding previous hashes/statuses are retained in
`inspections/critical_thinking_problem_solving/tsa/categorization/before_semantic_refinement.json`.

The current representation refinement intentionally rebuilds affected RAW/CLEAN
and canonical matching after recovering decoded option boundaries, certifying
body/option image cells and separating blank raster padding. CLEAN also recognises
conditional sentence-completion prompts. The previously blocked 2014 Q50,
2018 Q20 and 2019 Q32 now have complete options and source answers B/B/C;
their previous null conflicted answers are replaced only after structural repair.
All existing Final Explanation objects, original page/question raw text and old
asset files remain unchanged. Input snapshots and hashes are retained in
`inspections/critical_thinking_problem_solving/tsa/categorization/representation_refinement/archive.json`; verification
is in [the current audit](../../../inspections/critical_thinking_problem_solving/tsa/categorization/representation_refinement/validation.json).

## Nuances that downstream processing must retain

- The three earlier option/key conflicts are resolved by upstream recovery, not
  a categorization override. Other concrete raw/clean issues remain visible.
- 2008 Q12 and 2016 Q38 use approved manual explanation replacements. Original
  PDF candidates/warnings/previews remain archived, not falsely labelled fixed.
- 2022 Q46 uses the approved manual supplement; its source header omission remains
  traceable. Q45's recovered full source explanation remains intact.
- 2022 Q44 uses the explicit persistent clean-body composite; original raw assets
  remain preserved. Do not infer a general visual-collapse rule from this pin.
- 2017–2019 accepted imported/visual explanations retain `explanation_by_ai=true`,
  source file/hash/record identity and review metadata. Unaccepted drafts/pilot
  candidates are not successful explanations and are not restored or generated.
- 2020 has 50 official full explanations with explicit/semantic answer-inference
  evidence. It is not split using the older source-component assumptions.
- Source/manual explanations stay non-AI. Correct answers, final blocks, original
  component fields and provenance are immutable inputs to categorization.
- Concrete RAW/CLEAN issues remain in matching snapshots/inspection. The broad
  `upstream_review_required` flag also catches the informational
  `graphics_present:option_association_not_resolved`; it is not an issue count or
  a categorization veto by itself. No warning is removed by categorization.

## Reproducibility

All current results already exist on disk; categorization does not rebuild them.
Source-specific reproduction commands and exceptions remain in:

- [2008–2016 matching](MATCHING_2008-2016_BACKTEST.md)
- [2017–2019 matching and explanation overlays](MATCHING_2017-2019_BACKTEST.md)
- [2020 official explanations](MATCHING_2020_BACKTEST.md)
- [2021 matching](MATCHING_2021_BACKTEST.md)
- [2022 matching/manual supplement](MATCHING_2022_BACKTEST.md)

Use [categorization commands](CATEGORIZATION_BACKTEST.MD) only after confirming the
handoff matches the intended canonical state. No acquisition, provider calls or
matching rerun is implicit in the new stage.
