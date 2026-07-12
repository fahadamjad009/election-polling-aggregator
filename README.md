# Election Polling Aggregator

A reproducible multi-country polling analytics pipeline covering Australia, Canada, the United Kingdom, and the United States.

## Final results

| Evaluation | MAE | RMSE | Winner accuracy |
|---|---:|---:|---:|
| Development leave-one-election-out validation | 1.3115 pp | 1.7230 pp | 92.9% |
| Final chronological holdout | 1.2435 pp | 1.6799 pp | 87.5% |

The selected method is the **final five-observation rolling polling average**.

## Project scope

- 22 national elections
- 14 development elections
- 8 chronological holdout elections
- 4 countries
- 68 party-election rows
- 43 development rows
- 25 holdout rows

The system predicts national vote share and the national polling leader.

It does not predict seats, constituencies, electoral-college outcomes, coalition formation, or government formation.

## Countries

| Country | Polling scope | Modelling target |
|---|---|---|
| Australia | National polling | Two-party-preferred vote |
| Canada | National party polling | National party vote share |
| United Kingdom | National party polling | National party vote share |
| United States | National presidential polling averages | National popular-vote share |

Australia uses `ALP (2PP)` and `L/NP (2PP)` because consistent historical national primary-vote actuals were unavailable across the selected elections.

## Pipeline

Raw polling and election data  
? Polling-table extraction  
? Country-specific cleaning and party normalisation  
? National-scope table audit  
? Automatic decisions and documented manual overrides  
? Election-date cutoff  
? Rolling averages and polling features  
? Party-election modelling dataset  
? Development-only validation and feature ablation  
? Locked chronological holdout evaluation

## National polling-scope controls

Historical polling pages may include regional, state, constituency, by-election, approval-rating, and historical comparison tables.

Only automatically approved or manually approved national tables enter feature engineering.

Current scope-filter result:

- 16,489 poll-party rows retained
- 47,727 rows excluded
- 15 automatically approved tables
- 9 manually approved tables
- 6 manually rejected tables

Key evidence:

- `data/reference/polling_table_scope_audit.csv`
- `data/reference/polling_scope_overrides.csv`
- `data/features/polling_scope_included_tables.csv`
- `data/features/polling_scope_excluded_tables.csv`

## Leakage prevention

- Post-election observations are removed before feature engineering.
- Election-result marker rows are not treated as polls.
- Development and holdout elections are separated chronologically.
- Model selection uses development elections only.
- The final holdout was evaluated once.
- The holdout is protected by `data/model/final_holdout/HOLDOUT_EVALUATED.lock`.

## Model selection

Development evaluation used leave-one-election-out cross-validation.

| Method | MAE | RMSE | Winner accuracy |
|---|---:|---:|---:|
| Final polling average | **1.3115** | **1.7230** | **92.9%** |
| Ridge: final plus recent | 2.2684 | 2.8831 | 92.9% |
| Ridge: broad features | 3.7050 | 4.6891 | 92.9% |
| Ridge: recent features | 3.7242 | 4.9366 | 78.6% |

The polling-average benchmark was selected because no challenger improved vote-share error while preserving overall performance.

## Final chronological holdout

- MAE: **1.2435 percentage points**
- RMSE: **1.6799 percentage points**
- Winner accuracy: **7 of 8 elections**
- Missed winner: **Australia 2019**

## Documentation

- `METHODOLOGY.md`
- `PROJECT_STATUS.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_DICTIONARY.md`
- `docs/MODEL_CARD.md`
- `docs/RUNBOOK.md`

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r .\requirements.txt
```

## Run

```powershell
.\run_development_pipeline.ps1
```

## Test

```powershell
python -m unittest discover -s .\tests -p "test_*.py" -v
```

The development runner does not evaluate the final holdout.

The holdout remains protected by `data/model/final_holdout/HOLDOUT_EVALUATED.lock`.

## Current status

Completed:

- data pipeline;
- scope and leakage controls;
- feature engineering;
- development validation;
- locked final holdout evaluation;
- documentation;
- dependency packaging;
- automated tests;
- clean-environment smoke test;
- required-output validation.

Remaining:

- Streamlit presentation layer;
- final detailed project explanation document.
