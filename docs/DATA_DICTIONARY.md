# Data Dictionary

## Purpose

This document defines the main datasets, fields, identifiers, targets, audit outputs, and modelling conventions used by the Election Polling Aggregator.

The project contains multiple data layers:

- raw source data;
- cleaned polling data;
- cleaned election results;
- source-governance reference data;
- engineered polling features;
- modelling datasets;
- evaluation outputs.

## Core identifiers

The following fields are used repeatedly across the pipeline.

| Field | Type | Description |
|---|---|---|
| `country` | string | Normalised country identifier such as `australia`, `canada`, `uk`, or `us` |
| `election_year` | integer | Calendar year of the election |
| `party` | string | Canonical polling or election-result party label |
| `model_party` | string | Party label after mapping to the canonical modelling target |
| `source_table` | string | Identifier for the original source table |
| `dataset_split` | string | Either `development` or `holdout` |
| `poll_date` | date | Parsed date representing the polling observation |
| `election_date` | date | Verified election date used for leakage control |

## Canonical country values

| Value | Meaning |
|---|---|
| `australia` | Australian federal elections |
| `canada` | Canadian federal elections |
| `uk` | United Kingdom general elections |
| `us` | United States presidential elections |

## Party conventions

### Australia

The final modelling dataset uses only:

| Label | Meaning |
|---|---|
| `ALP (2PP)` | Australian Labor Party two-party-preferred result |
| `L/NP (2PP)` | Liberal/National Coalition two-party-preferred result |

Primary-vote polling labels may exist in cleaned polling data but are excluded from the final modelling scope.

### United Kingdom

| Polling label | Modelling label |
|---|---|
| `LD` | `LIB` |

This mapping aligns polling labels with the actual-results dataset.

### Canada and United States

Canonical polling labels generally match the actual-results labels directly after cleaning.

## Polling clean layer

Main location:

`data/polling_clean/`

The cleaned polling layer contains normalised poll-party observations.

Typical fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `source_table` | string | Original table identifier |
| `date_raw` | string | Original unparsed date text |
| `poll_date` | date | Parsed polling date |
| `pollster` | string | Polling organisation or source label |
| `party` | string | Canonical party label |
| `pct` | float | Reported polling percentage |
| `region` | string or null | Region value when explicitly present |
| `sample_size` | integer or null | Poll sample size when available |
| `notes` | string or null | Source notes or table metadata when available |

Not every source provides every optional field.

## Election-results clean layer

Main file:

`data/results_clean/national_actual_results.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `party` | string | Canonical party or candidate label |
| `actual_pct` | float | Official or authoritative national vote-share result |

The final modelling target is joined from this file after feature construction.

## Election-date reference

Main file:

`data/reference/election_dates.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `election_date` | date | Verified election date |

This file is used to remove post-election polling before feature engineering.

## Polling table scope audit

Main file:

`data/reference/polling_table_scope_audit.csv`

Purpose:

- determine whether a historical polling table represents national polling;
- compare election-result marker rows with verified national results;
- classify tables before feature engineering.

Typical fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `source_table` | string | Table identifier |
| `scope_status` | string | Automatic scope decision |
| `marker_found` | boolean | Whether a valid election-result marker was found |
| `overlap_parties` | integer | Number of comparable parties |
| `marker_mae` | float or null | Mean absolute difference between marker and verified result |
| `marker_max_error` | float or null | Maximum party-level difference |
| `reason` | string | Explanation for the automatic classification |

Expected automatic status values:

| Status | Meaning |
|---|---|
| `approved_marker_match` | Marker aligns closely enough with national results |
| `rejected_marker_mismatch` | Marker materially disagrees with national results |
| `review` | Evidence is incomplete or uncertain |

## Manual scope overrides

Main file:

`data/reference/polling_scope_overrides.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `source_table` | string | Table identifier |
| `override_status` | string | Manual decision |
| `reason` | string | Human-readable rationale |
| `evidence` | string | Supporting source or inspection evidence |

Allowed override values:

| Value | Meaning |
|---|---|
| `manual_approved` | Reviewed and approved as national polling |
| `manual_rejected` | Reviewed and rejected as non-national or incompatible |

Manual overrides take precedence over automatic audit status.

## Scope inclusion audit

Main file:

`data/features/polling_scope_included_tables.csv`

Purpose:

- record tables that entered feature engineering;
- preserve the reason for inclusion.

Typical fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `source_table` | string | Table identifier |
| `effective_scope_status` | string | Final inclusion status after overrides |
| `row_count` | integer | Number of included poll-party rows |

## Scope exclusion audit

Main file:

`data/features/polling_scope_excluded_tables.csv`

Purpose:

- record tables excluded before feature engineering;
- preserve the reason for exclusion.

Typical fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `source_table` | string | Table identifier |
| `effective_scope_status` | string | Final status after overrides |
| `row_count` | integer | Number of excluded poll-party rows |

## Post-election exclusion audit

Main file:

`data/features/post_election_rows_excluded.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `source_table` | string | Original source table |
| `date_raw` | string | Original date text |
| `pollster` | string | Pollster label |
| `party` | string | Party label |
| `pct` | float | Polling percentage |
| `poll_date` | date | Parsed polling date |
| `election_date` | date | Verified election date |

Rows in this file were removed because `poll_date` was later than `election_date`.

## Rolling and momentum feature layer

Main file:

`data/features/rolling_momentum_features.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `party` | string | Canonical polling label |
| `poll_date` | date | Polling date |
| `pct` | float | Raw polling percentage |
| `rolling_avg` | float | Five-observation rolling average |
| `momentum_1st_diff` | float or null | First difference in polling percentage |
| `momentum_2nd_diff` | float or null | Second difference in polling percentage |

The rolling window is based on observation order, not calendar days.

## Election split files

Main files:

- `data/splits/development_elections.csv`
- `data/splits/holdout_elections.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |

All parties from one election must remain in the same split.

## Final modelling dataset

Main file:

`data/model/model_dataset.csv`

One row represents one party in one election.

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `party` | string | Canonical modelling party |
| `dataset_split` | string | `development` or `holdout` |
| `election_date` | date | Verified election date |
| `last_poll_date` | date | Latest available pre-election polling date |
| `days_before_election` | integer | Days between final polling observation and election date |
| `final_poll_pct` | float | Final raw poll percentage |
| `final_rolling_avg` | float | Final five-observation rolling average |
| `final_momentum_1st` | float | Final first-difference value |
| `final_momentum_2nd` | float | Final second-difference value |
| `recent_30d_mean` | float | Mean polling percentage in final 30 days |
| `recent_30d_std` | float | Polling standard deviation in final 30 days |
| `recent_30d_observations` | integer | Number of observations in final 30 days |
| `recent_30d_trend_per_day` | float | Linear trend in percentage points per day |
| `final_vs_recent_30d_mean` | float | Final rolling average minus 30-day mean |
| `mean_poll_pct` | float | Full-campaign polling mean |
| `poll_std` | float | Full-campaign polling standard deviation |
| `min_poll_pct` | float | Minimum polling percentage |
| `max_poll_pct` | float | Maximum polling percentage |
| `mean_rolling_avg` | float | Mean of rolling averages |
| `mean_momentum_1st` | float | Mean first-difference value |
| `mean_momentum_2nd` | float | Mean second-difference value |
| `n_poll_observations` | integer | Number of poll-party observations |
| `campaign_span_days` | integer | Days between first and final polling observations |
| `actual_pct` | float | Actual national vote share |
| `is_winner` | integer | `1` for actual election winner, otherwise `0` |

## Development modelling dataset

Main file:

`data/model/development_model_dataset.csv`

This file contains only rows where:

`dataset_split == "development"`

It is used by:

- `evaluate_baselines.py`
- `evaluate_feature_ablation.py`
- `analyse_development_errors.py`

## Holdout modelling dataset

Main file:

`data/model/holdout_model_dataset.csv`

This file contains only rows where:

`dataset_split == "holdout"`

It is used only by the final holdout evaluation script.

It must not be used for further tuning or feature selection.

## Modelling exclusions audit

Main file:

`data/model/excluded_polling_parties.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `party` | string | Original polling label |
| `model_party` | string or null | Mapped modelling label |
| `status` | string | Reason for exclusion |

Common status values:

| Status | Meaning |
|---|---|
| `excluded by documented modelling scope` | Intentionally excluded from the final target definition |
| `no matching actual-result target` | No canonical actual result was available |

## Development baseline predictions

Main file:

`data/model/baselines/development_oof_predictions.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `party` | string | Party label |
| `actual_pct` | float | Actual vote share |
| `is_winner` | integer | Actual winner flag |
| `final_rolling_avg` | float | Final polling average |
| `fold_number` | integer | Leave-one-election-out fold |
| `baseline_vote_prediction` | float | Final polling-average prediction |
| `ridge_vote_prediction` | float | Ridge-regression prediction |
| `logistic_win_probability` | float | Logistic-regression winner probability |
| `polling_baseline_predicted_winner` | integer | Baseline winner flag |
| `ridge_regression_predicted_winner` | integer | Ridge winner flag |
| `logistic_regression_predicted_winner` | integer | Logistic winner flag |

## Development metrics

Main file:

`data/model/baselines/development_baseline_metrics.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `task` | string | Regression or winner-classification task |
| `model` | string | Evaluated model |
| `metric` | string | Metric name |
| `value` | float | Metric value |

Metric definitions:

| Metric | Meaning |
|---|---|
| `MAE` | Mean absolute vote-share error |
| `RMSE` | Root mean squared vote-share error |
| `election_winner_accuracy` | Fraction of elections with correct predicted winner |
| `OOF_ROC_AUC` | Out-of-fold ROC AUC for winner classification |
| `row_accuracy_at_0.5` | Row-level classification accuracy at threshold 0.5 |

## Feature ablation metrics

Main file:

`data/model/ablation/development_feature_ablation_metrics.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `task` | string | Evaluation task |
| `feature_set` | string | Feature configuration |
| `model` | string | Evaluated model |
| `metric` | string | Metric name |
| `value` | float | Metric value |

Feature-set values:

| Value | Meaning |
|---|---|
| `benchmark` | Final polling-average benchmark |
| `legacy_broad` | Broad campaign feature set |
| `recent_compact` | Compact final-30-day feature set |
| `final_plus_recent` | Final polling average plus recent-window features |

## Final holdout predictions

Main file:

`data/model/final_holdout/final_holdout_predictions.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `party` | string | Party label |
| `actual_pct` | float | Actual vote share |
| `is_winner` | integer | Actual winner flag |
| `final_rolling_avg` | float | Selected polling estimate |
| `selected_vote_prediction` | float | Final selected prediction |
| `vote_share_error` | float | Prediction minus actual vote share |
| `absolute_error` | float | Absolute vote-share error |
| `selected_model_predicted_winner` | integer | Selected-model winner flag |

## Final holdout metrics

Main file:

`data/model/final_holdout/final_holdout_metrics.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `evaluation_set` | string | `chronological_holdout` |
| `task` | string | Regression or winner classification |
| `model` | string | Final selected model |
| `metric` | string | Metric name |
| `value` | float | Metric value |
| `rows` | integer | Number of party-election rows |
| `elections` | integer | Number of elections |

## Final election-level results

Main file:

`data/model/final_holdout/final_holdout_election_results.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `election_year` | integer | Election year |
| `actual_winner` | string | Actual winning party |
| `predicted_winner` | string | Polling-model predicted winner |
| `winner_correct` | integer | `1` when correct, otherwise `0` |
| `predicted_winner_polling_pct` | float | Polling estimate for predicted winner |
| `predicted_winner_actual_pct` | float | Actual vote share for predicted winner |
| `predicted_margin` | float | Polling lead over second place |
| `actual_margin` | float | Actual lead over second place |

## Final country-level error summary

Main file:

`data/model/final_holdout/final_holdout_country_errors.csv`

Fields:

| Field | Type | Description |
|---|---|---|
| `country` | string | Country identifier |
| `rows` | integer | Number of party-election rows |
| `elections` | integer | Number of holdout elections |
| `MAE` | float | Mean absolute error |
| `mean_error` | float | Mean signed prediction error |
| `RMSE` | float | Root mean squared error |

## Model selection decision

Main file:

`data/model/final_holdout/model_selection_decision.json`

Important fields:

| Field | Description |
|---|---|
| `selected_model` | Name of the selected final model |
| `prediction_column` | Dataset field used as prediction |
| `selection_basis` | Development-only selection rationale |
| `development_mae` | Development MAE |
| `development_rmse` | Development RMSE |
| `development_winner_accuracy` | Development winner accuracy |
| `challenger_decision` | Reason challengers were rejected |
| `holdout_usage` | Holdout governance statement |

## Holdout lock

Main file:

`data/model/final_holdout/HOLDOUT_EVALUATED.lock`

Purpose:

- record that the final chronological holdout has already been evaluated;
- prevent casual repeated evaluation;
- reinforce that no further tuning should use the holdout.

## Data quality invariants

The following conditions must remain true:

1. Every modelling row has a valid `country`, `election_year`, and `party`.
2. Each party appears at most once per election in the modelling dataset.
3. Every modelled election contains exactly one actual winner.
4. No final model row uses polling after the election date.
5. Development and holdout elections do not overlap.
6. Only approved national source tables enter feature engineering.
7. Australia final modelling uses only 2PP labels.
8. UK `LD` polling maps to `LIB` actual results.
9. Final holdout outputs are not used for later model selection.
10. Retrospective similarity features do not enter the predictive dataset.

## Current final dataset counts

| Dataset | Rows | Elections |
|---|---:|---:|
| Full modelling dataset | 68 | 22 |
| Development dataset | 43 | 14 |
| Chronological holdout | 25 | 8 |

## Final selected method

The final selected prediction field is:

`final_rolling_avg`

This is the last available five-observation rolling polling average for each party before election day.

The party with the highest value within each election is treated as the predicted polling winner.
