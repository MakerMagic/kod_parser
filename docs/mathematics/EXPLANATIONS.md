# Mathematics explanations

This stage reads `data/pre_final/mathematics/questions.json` as read-only input
and stores directly authored explanations separately in
`data/explanations/mathematics/explanations.json`. It does not change question,
answer, category, asset, pre-final, or rendering data.

Explanation text is authored by the active assistant from canonical question
content and the stored correct answer. No Gemini, OpenAI, Claude, external LLM,
batch provider, or other explanation-generation service may be called or used.
User-supplied AI explanations may also be imported after content review. Import
uses only the canonical stable ID; review decisions bind both the question's
content hash and the exact explanation text hash. Unknown/duplicate IDs, existing
valid explanations, null entries and content/answer conflicts are explicit in
data/explanations/mathematics/import_audit.json. Supplied text is not rewritten.
The AI provenance field `final_explanation.explanation_by_ai` is `true` for
these assistant-authored explanations, consistent with the TSA/BMAT schema.

The current command only validates and publishes explanation records already
authored in the output JSON; it never generates text. Run it with:

```powershell
.venv\Scripts\python.exe -m processors.explanations.mathematics --require-complete
```

Records are bound to stable PRE-FINAL IDs, content hashes, and stored correct
answers. Use inline `\( ... \)` and display `\[ ... \]` LaTeX; explanations
must be no longer than 2000 characters and have no artificial minimum. If
canonical content is ambiguous, a required visual cannot be read reliably, or
the derived result does not match the stored answer, retain an exact
EXPLANATION issue instead of guessing. The command deterministically regenerates
`EXPLANATION_BACKTESTING.md` and `EXPLANATION_ISSUES.md` from the structured
explanation output, including when the issue count is zero.

Explanation LaTeX uses its own syntax validator, supporting standard single-token
arguments, binomial coefficients, integrals and solution formatting without
changing RAW's restricted grammar. This validates syntax, not mathematical truth:
content, derivations, diagrams and stored-answer correspondence require direct
review. Image questions are eligible when their canonical assets suffice.

The explanation directory's direct_authored.json retains directly authored task
records; content_review.json retains supplied-text decisions. Canonical
explanations.json is the published projection. A completed pass must account for
every rendered question exactly once as a valid explanation or a specific
blocking issue. A missing-authoring placeholder is not a solving blocker and
must not count as completed coverage.
