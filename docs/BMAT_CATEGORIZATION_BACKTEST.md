# BMAT categorization backtesting

Categorization is now a read-only upstream dependency of pre-final assembly.
Unified question rendering follows pre-final JSON; no command below is rerun as
part of assembly. Existing stage-specific tools remain opt-in user inspections.

Reads persisted CLEAN-based dominant-task attribution with hash-verified matching context, TSA model and content-bound rulebook review. Correct Answer, Main/Final Explanation, body/option assets and source screenshots remain visible. All records, including excluded and unresolved questions, remain inspectable. Existing BMAT-specific taxonomy and exclusion precedence are preserved; TSA multi-label behavior is not changed.

Reproduce: `python -m categorization.bmat run` (or `python -m processors.bmat categorize run`). Review source: `categorization/bmat/decisions.tsv`; rebind verified decisions with `python -m categorization.bmat bind-review`. A changed question or asset needs fresh review; unseen weak-evidence cases abstain. No parsing, cleaning, answer matching or explanation generation runs in categorization.

## User-requested inspection

`python -m categorization.bmat report --year 2021 --question 25` exports only the selected question. Omit `--question` for a requested year export; omit both selectors only for an explicitly requested full export. `run` writes canonical categories and current issue indexes without rendering question HTML.

Canonical input is `data/categorized/bmat/questions.categorized.json`. Read `records` by identity or categorization issue code directly; open the referenced assets when needed. Internal candidates are not accepted primary categories. BMAT-specific types remain separate from normal TSA categories. Blocked upstream records and source reviews are not repaired by categorization.
