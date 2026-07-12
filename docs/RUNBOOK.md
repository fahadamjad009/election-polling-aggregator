# Reproducibility Runbook

## Purpose

This document records the verified execution order for the Election Polling Aggregator.

Development outputs may be rebuilt. The chronological holdout has already been evaluated and must remain frozen.

## Environment

- Python 3.11.9
- Virtual environment: `venv`
- Project root: `D:\projects\election-polling-aggregator`

Activate the environment:

```powershell
Set-Location "D:\projects\election-polling-aggregator"
.\venv\Scripts\Activate.ps1
python --version
```

Run all scripts from the project root because they use project-relative paths.

## Governance rules

1. Preserve `data/reference/election_dates.csv`.
2. Preserve `data/reference/polling_scope_overrides.csv`.
3. Only approved national polling tables may enter feature engineering.
4. Remove post-election observations before calculating features.
5. Keep complete elections together in development or holdout.
6. Use development elections only for model selection.
7. Do not delete or bypass the holdout lock.
8. Do not retune against the frozen holdout.

## Safe development pipeline

Run the following commands in order:

```powershell
python .\src\convert_us_data.py
python .\src\clean_polling_data.py
python .\src\build_national_results.py
python .\src\build_national_polling_scope.py
python .\src\build_features.py
python .\src\build_pollster_reliability.py
python .\src\build_similar_elections.py
python .\src\build_train_test_split.py
python .\src\build_model_dataset.py
python .\src\evaluate_baselines.py
python .\src\analyse_development_errors.py
python .\src\evaluate_feature_ablation.py
```

The Wikipedia scraper is excluded from the normal rebuild because it reads live webpages:

```powershell
python .\src\scrape_polling_wikipedia.py
```

Use it only when deliberately refreshing raw acquisition data.

## Main outputs

- National results: `data/results_clean/national_actual_results.csv`
- Scope audit: `data/reference/polling_table_scope_audit.csv`
- Scope overrides: `data/reference/polling_scope_overrides.csv`
- Election dates: `data/reference/election_dates.csv`
- Rolling features: `data/features/rolling_momentum_features.csv`
- Included tables: `data/features/polling_scope_included_tables.csv`
- Excluded tables: `data/features/polling_scope_excluded_tables.csv`
- Post-election audit: `data/features/post_election_rows_excluded.csv`
- Development split: `data/splits/development_elections.csv`
- Holdout split: `data/splits/holdout_elections.csv`
- Development metrics: `data/model/baselines/development_baseline_metrics.csv`
- Ablation metrics: `data/model/ablation/development_feature_ablation_metrics.csv`

## Expected dataset counts

| Dataset | Rows | Elections |
|---|---:|---:|
| Full modelling dataset | 68 | 22 |
| Development dataset | 43 | 14 |
| Chronological holdout | 25 | 8 |

## Selected method

The selected prediction field is `final_rolling_avg`.

Development results:

- MAE: 1.3115 percentage points
- RMSE: 1.7230 percentage points
- Winner accuracy: 92.9%

The fitted challengers did not improve development vote-share error.

## Frozen holdout

The holdout lock is:

`data/model/final_holdout/HOLDOUT_EVALUATED.lock`

Do not run:

```powershell
python .\src\evaluate_final_holdout.py
```

The script correctly refuses to run when the lock exists.

Frozen holdout results:

- MAE: 1.2435 percentage points
- RMSE: 1.6799 percentage points
- Winner accuracy: 87.5%
- Correct winners: 7 of 8
- Incorrect winner: Australia 2019

These results may be reported but must not be used for further model selection.

## Final operating rule

Rebuild and validate development artefacts only.

Preserve the declared split and the frozen chronological holdout.
