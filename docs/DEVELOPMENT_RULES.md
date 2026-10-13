# Development Rules

## 1. Current Development Milestone

Current milestone:

```text
Blackstone raw structured JSON → Blackstone clean structured JSON

Raw parsing is now the upstream input for the current stage.
Do not redesign the parser while implementing cleaning unless a confirmed raw-data defect makes a parser fix necessary.
Do not implement answer matching, categorization, final export, or additional sources unless explicitly requested.
2. Inspect Before Editing
Before changing existing code, inspect only the files directly relevant to the task.
For cleaning work, inspect:
- representative Blackstone raw records;
- current normalization/cleaning code, if any;
- relevant schema expectations;
- related tests;
- parser output only when a raw-data defect is suspected.
Do not scan or refactor the whole repository for a small cleaning task.
3. Cleaning Must Operate on Raw Structured Data
Cleaning starts from already parsed structured data.
Expected flow:
data/raw/blackstone/
↓
cleaning / normalization
↓
data/clean/blackstone/

Cleaning should not reopen or reparse PDFs during normal operation.
If a problem originates from incorrect raw extraction, treat it as a parser issue rather than hiding it during cleaning.
4. Preserve Raw Data
Raw data is immutable input for the cleaning stage.
Do not:
- overwrite raw files;
- replace raw text with cleaned text;
- delete uncertain raw content;
- silently repair semantic parser errors.
Clean output must be written separately.
Every clean record should remain traceable to its corresponding raw record.
5. What Cleaning May Do
Cleaning may normalize representation when meaning is preserved.
Allowed transformations include:
- whitespace normalization;
- unnecessary line-break cleanup;
- leading/trailing whitespace removal;
- known PDF extraction artifact removal;
- consistent Unicode/encoding normalization;
- option-label normalization;
- multiline option normalization;
- subpoint representation normalization;
- metadata formatting;
- consistent null/empty-value representation;
- image-reference normalization.
Cleaning may remove an artifact only when it is reliably identified as non-content.
6. What Cleaning Must Not Do
Cleaning must not:
- paraphrase question wording;
- change semantic meaning;
- invent missing text or metadata;
- guess ambiguous option associations;
- hide unresolved parser warnings;
- determine correct answers;
- match questions with answer files;
- categorize questions;
- depend on acquisition method, URL, or website structure.
Cleaning fixes representation, not meaning.
7. Preserve Uncertainty
If raw data contains genuine uncertainty, cleaning should preserve it.
Cleaning may resolve uncertainty only when the issue is purely representational and the correction is deterministic.
When uncertain:
- keep the original information;
- preserve or add a warning;
- do not guess.
8. Generalized Cleaning Rules Only
Before adding a cleaning rule:
1. inspect representative affected raw records;
2. compare multiple similar examples;
3. confirm the pattern is systematic;
4. distinguish formatting noise from parser errors;
5. implement a generalized rule;
6. verify that valid content is not changed incorrectly.
Do not hard-code:
- question numbers;
- years;
- page numbers;
- filenames;
- asset IDs;
- one-off strings
unless they represent a genuinely source-specific rule.
9. No Silent Failures
If cleaning cannot safely normalize a record, preserve the data and make the issue visible.
Where relevant, report:
- source;
- raw record/question ID;
- year;
- question number;
- field affected;
- failure or uncertainty reason.
Do not silently skip problematic records.
10. Testing Rules
Cleaning tests should operate on fixed raw records or fixtures.
Tests should verify that cleaning:
- produces expected normalized text;
- preserves question identity;
- preserves meaningful question content;
- preserves option labels and option content;
- preserves numbered subpoints;
- preserves image associations;
- preserves legitimate warnings;
- does not modify raw files;
- does not remove meaningful text;
- produces deterministic output.
For every important cleaning rule, include:
- at least one case that should be normalized;
- at least one case that should remain unchanged when the rule does not apply.
If a parser bug is discovered during cleaning work, add or update parser regression tests separately.
11. Preserve Existing Parser Stability
The completed raw parsing stage should be treated as stable upstream infrastructure.
Do not modify parser logic merely because cleaning output is inconvenient.
Modify parsing only when:
- raw extraction is objectively incorrect;
- the defect can be demonstrated with representative examples;
- the fix is generalized;
- parser regression tests confirm that existing correct behavior remains intact.
12. Stage-by-Stage Development
Develop in this order:
1. Input PDF → Blackstone raw JSON — completed/current upstream
2. Blackstone raw → Blackstone clean — current stage
3. Answer/explanation input → answers raw
4. Answers raw → answers clean
5. Question + answer datasets → merged
6. Merged → categorized/final
7. Additional sources
Do not implement multiple future stages simultaneously.
13. Adding a New Source
When adding a source later:
1. define how files can enter the system;
2. define document identification;
3. implement source parser;
4. produce raw data;
5. define source-specific normalization where necessary;
6. produce clean structured data;
7. validate output;
8. integrate matching and categorization only when needed.
Adding one source must not require rewriting unrelated source parsers or cleaners.
14. Completion Criteria for Cleaning
The Blackstone cleaning stage is complete only when:
- raw input contract is clear;
- clean output schema is clear;
- cleaning works independently of PDF acquisition and parsing;
- raw data remains unchanged;
- transformations are deterministic;
- representative real records have been tested;
- meaningful text and structure are preserved;
- legitimate uncertainty remains visible;
- failures are not silent;
- regression tests cover important cleaning rules;
- downstream stages can consume the clean output reliably.
15. Core Principle
Design cleaning around:
How can this raw structured data be represented consistently
without changing its meaning or hiding uncertainty?

Cleaning should improve consistency, not compensate for incorrect parsing.
Raw data is the preserved source of truth for extraction. Clean data is its normalized downstream representation.
