# Project Status — Election Polling Aggregator

Last updated: 12 July 2026

## Project objective

Build a reproducible multi-country election-polling analytics system that:

- collects and normalises historical polling data;
- separates national polling from regional, constituency and other incompatible tables;
- prevents post-election leakage;
- engineers polling trend and recent-window features;
- compares simple statistical and machine-learning approaches;
- selects a model using development elections only;
- performs one locked evaluation on a chronological holdout;
- presents results, limitations and engineering evidence clearly.

## Current milestone

The analytical and modelling pipeline is complete.

The project is now in the documentation, quality-assurance and presentation phase.

## Completed milestones

### M1 — Project framing

Completed.

- Defined national-level vote-share regression.
- Defined national polling-leader prediction.
- Limited scope to Australia, Canada, the United Kingdom and the United States.
- Documented that the system does not predict seats, coalitions, electoral-college outcomes or government formation.

### M2 — Data acquisition

Completed.

- Collected historical Wikipedia polling tables for Australia, Canada and the United Kingdom.
- Converted FiveThirtyEight US presidential polling averages into the common schema.
- Collected and normalised national election results.
- Preserved raw and cleaned data separately.

### M3 — Cleaning and standardisation

Completed.

- Normalised country-specific polling-table structures.
- Canonicalised party names and aliases.
- Recovered Australian primary and two-party-preferred labels.
- Parsed inconsistent date ranges.
- Corrected duplicated and malformed party columns.
- Created reusable cleaned polling outputs.

### M4 — National polling-scope governance

Completed.

- Audited 206 source tables.
- Compared election-result marker rows with verified national results.
- Created automatic approved, rejected and review classifications.
- Created a documented manual override register.
- Retained 16,489 approved poll-party rows.
- Excluded 47,727 regional, mismatched or unresolved rows.
- Applied fail-closed behaviour to unresolved tables.

Key evidence:

- data/reference/polling_table_scope_audit.csv
- data/reference/polling_scope_overrides.csv
- data/features/polling_scope_included_tables.csv
- data/features/polling_scope_excluded_tables.csv

### M5 — Leakage controls and feature engineering

Completed.

- Stored verified election dates separately.
- Removed post-election observations before rolling features were calculated.
- Confirmed zero post-election rows remained.
- Created five-observation rolling averages.
- Created first- and second-difference momentum indicators.
- Created campaign-wide summary features.
- Created final-30-day mean, volatility, observation-count and trend features.

### M6 — Modelling dataset and split

Completed.

- Built one modelling row per party and election.
- Created 68 party-election rows across 22 elections.
- Development set: 43 rows across 14 elections.
- Chronological holdout: 25 rows across 8 elections.
- Confirmed exactly one actual winner per election.
- Documented intentionally excluded and unmatched parties.

### M7 — Development validation and model selection

Completed.

- Used leave-one-election-out development validation.
- Evaluated the final polling-average benchmark.
- Evaluated Ridge-regression feature sets.
- Evaluated logistic-regression winner classifiers.
- Added recent-window feature ablation.
- Rejected challengers that did not improve the benchmark.

Selected method:

- final five-observation rolling polling average.

Development results:

- MAE: 1.3115 percentage points
- RMSE: 1.7230 percentage points
- winner accuracy: 92.9%

### M8 — Locked chronological holdout

Completed and frozen.

Final holdout results:

- 25 party-election rows
- 8 elections
- MAE: 1.2435 percentage points
- RMSE: 1.6799 percentage points
- winner accuracy: 87.5%
- correct winners: 7 of 8
- missed election: Australia 2019

The holdout must not be used for additional tuning or model selection.

Lock evidence:

- data/model/final_holdout/HOLDOUT_EVALUATED.lock

## Remaining milestones

### M9 — Repository documentation

Complete.

Required work:

- create the professional README;
- replace outdated sections of METHODOLOGY.md;
- preserve the useful cleaning and debugging history;
- document the national-scope audit and overrides;
- document leakage controls;
- document development-only model selection;
- document the locked holdout;
- add an architecture and data-flow diagram;
- add a data dictionary;
- add a model card;
- add a reproducibility runbook;
- add a limitations and responsible-use section.

### M10 — Quality assurance and reproducibility

In progress.

Required work:

- [x] create requirements.txt with verified versions;
- [x] create a single development-pipeline runner;
- [x] add schema and invariant tests;
- [ ] add a clean-environment smoke test;
- [ ] verify all referenced outputs exist;
- [ ] verify README commands from a fresh shell;
- [x] verify scripts do not silently overwrite the holdout lock;
- [ ] produce a final validation report.

### M11 — Presentation layer

Not started.

Recommended work:

- create a compact Streamlit application;
- show country/election polling trends;
- show polling estimate versus actual result;
- show development and holdout metrics separately;
- show national-table audit evidence;
- show the Australia 2019 miss honestly;
- show limitations prominently;
- include downloadable, non-sensitive result summaries.

This presentation layer must use existing frozen outputs and must not retrain or retune models.

### M12 — Final project explanation document

Not started.

The final document will explain:

- project framing;
- data-source decisions;
- all major cleaning problems and fixes;
- national-table contamination discovery;
- scope-audit methodology;
- leakage prevention;
- feature engineering;
- split design;
- baseline and challenger models;
- ablation findings;
- model-selection decision;
- holdout governance;
- final results;
- limitations;
- lessons learned;
- interview-ready explanations;
- how this project compares with the user's other portfolio repositories.

The final document will be produced only after the repository documentation, tests, runbook and presentation layer are complete.

## Professional enhancement principles

The remaining work must follow these rules:

1. Do not add complexity without evidence that it improves the project.
2. Preserve the final polling average as the selected model.
3. Do not tune against the locked holdout.
4. Keep raw, intermediate and final outputs traceable.
5. Record manual data decisions explicitly.
6. Report both successes and failures.
7. Separate analytical evidence from predictive features.
8. Use quantified validation rather than unsupported claims.
9. Make every major result reproducible from scripts.
10. Ensure repository documentation matches the implemented code.

## Current completion estimate

- Core data pipeline: complete
- Scope and leakage controls: complete
- Feature engineering: complete
- Development validation: complete
- Final holdout evaluation: complete
- Repository documentation: complete
- Tests and reproducibility packaging: in progress
- Presentation application: remaining
- Final detailed explanation document: remaining

Overall project completion: approximately 85%.

