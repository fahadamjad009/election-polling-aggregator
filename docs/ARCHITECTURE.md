# Architecture

## System purpose

The Election Polling Aggregator is a reproducible historical analytics pipeline for national election polling across Australia, Canada, the United Kingdom, and the United States.

The system separates:

- raw source acquisition;
- country-specific cleaning;
- source-scope governance;
- leakage-safe feature engineering;
- development-only model selection;
- locked chronological holdout evaluation;
- analytical and presentation outputs.

## High-level architecture

```text
External polling and result sources
                |
                v
        Raw source layer
        data/polling_raw/
        data/results_raw/
                |
                v
    Country-specific transformation
        clean_polling_data.py
        convert_us_data.py
        build_national_results.py
                |
                v
       Canonical clean layer
        data/polling_clean/
        data/results_clean/
                |
                v
       Source-scope governance
 build_national_polling_scope.py
                |
       +--------+---------+
       |                  |
       v                  v
automatic audit     manual overrides
scope audit CSV     override register
       |                  |
       +--------+---------+
                |
                v
       Approved national tables
                |
                v
      Election-date filtering
          build_features.py
                |
                v
       Feature engineering layer
           data/features/
                |
                v
       Party-election dataset
       build_model_dataset.py
                |
        +-------+--------+
        |                |
        v                v
 development set    chronological holdout
        |                |
        v                |
baseline evaluation     |
feature ablation        |
error analysis          |
        |                |
        v                |
model selection locked  |
        +-------+--------+
                |
                v
single final holdout evaluation
 evaluate_final_holdout.py
                |
                v
 data/model/final_holdout/
```

## Architectural principles

### 1. Raw data is preserved

Raw files are not overwritten by cleaned outputs.

This supports:

- traceability;
- debugging;
- reproducibility;
- comparison between source and transformed data.

### 2. Country-specific complexity is handled before modelling

Polling sources differ substantially between countries.

Country-specific logic handles:

- column layouts;
- party aliases;
- Australian primary and 2PP fields;
- date formats;
- duplicated labels;
- election-result marker rows.

The modelling layer receives a shared canonical schema rather than handling raw-source differences directly.

### 3. Source scope is governed explicitly

Historical polling pages may contain national and non-national tables together.

The scope layer classifies source tables before feature engineering.

Automatic evidence is stored in:

- `data/reference/polling_table_scope_audit.csv`
- `data/reference/polling_marker_candidates.csv`

Manual decisions are stored in:

- `data/reference/polling_scope_overrides.csv`

Only approved national tables proceed downstream.

### 4. Uncertain sources fail closed

Tables classified as unresolved or review-only are excluded unless a documented manual approval exists.

This prevents ambiguous regional or constituency tables from silently entering national features.

### 5. Election dates are a formal control boundary

Election dates are stored separately in:

- `data/reference/election_dates.csv`

Post-election rows are removed before rolling averages, momentum, or recent-window features are calculated.

This prevents future information from affecting predictive inputs.

### 6. Splits occur at election level

All parties from one election remain in the same split.

This prevents rows from the same political event appearing in both training and validation data.

### 7. Development and holdout responsibilities are separated

Development scripts use only:

- `data/model/development_model_dataset.csv`

The final evaluation script uses only:

- `data/model/holdout_model_dataset.csv`

The development evaluators do not load the holdout file.

### 8. Model selection precedes holdout evaluation

The final five-observation rolling polling average was selected using development-only evidence.

The holdout was evaluated once after selection.

The lock file is:

- `data/model/final_holdout/HOLDOUT_EVALUATED.lock`

### 9. Analytical outputs are separated from predictive inputs

The following are analytical outputs unless rebuilt under fold-safe rules:

- pollster reliability;
- similar-election analysis;
- exploratory analysis;
- post-hoc error diagnostics.

The similar-election vectors include actual outcomes and must not enter forecasting models.

## Data layers

### Raw layer

Purpose:

- retain downloaded or scraped source data unchanged.

Main locations:

- `data/polling_raw/`
- `data/results_raw/`

### Clean layer

Purpose:

- standardise country, election year, party, polling date, pollster, and percentage fields.

Main locations:

- `data/polling_clean/`
- `data/results_clean/`

### Reference and governance layer

Purpose:

- hold verified election dates;
- store table-scope audit evidence;
- record manual inclusion and exclusion decisions.

Main location:

- `data/reference/`

### Feature layer

Purpose:

- retain approved pre-election polling;
- create rolling averages and momentum;
- create recent-window diagnostics;
- save inclusion, exclusion, and cutoff audits.

Main location:

- `data/features/`

### Modelling layer

Purpose:

- create one row per party-election;
- attach actual vote share and winner target;
- maintain development and chronological holdout splits.

Main location:

- `data/model/`

### Evaluation layer

Purpose:

- store development predictions;
- store ablation results;
- store error diagnostics;
- store final locked holdout outputs.

Main locations:

- `data/model/baselines/`
- `data/model/ablation/`
- `data/model/final_holdout/`

## Core components

| Component | Responsibility |
|---|---|
| `scrape_polling_wikipedia.py` | Extract historical polling tables |
| `clean_polling_data.py` | Clean and canonicalise country polling data |
| `convert_us_data.py` | Convert US polling averages to the common schema |
| `date_parser.py` | Parse inconsistent historical dates |
| `build_national_results.py` | Create canonical actual election results |
| `build_national_polling_scope.py` | Classify table-level national scope |
| `build_features.py` | Apply scope and election-date controls, then engineer features |
| `build_train_test_split.py` | Create development and holdout election splits |
| `build_model_dataset.py` | Create party-election modelling rows |
| `evaluate_baselines.py` | Evaluate development baselines |
| `evaluate_feature_ablation.py` | Compare feature configurations |
| `analyse_development_errors.py` | Analyse development failures |
| `evaluate_final_holdout.py` | Run the single final evaluation |

## Final selected prediction path

```text
approved national polling rows
        |
        v
pre-election observations only
        |
        v
sort by country, election, party and date
        |
        v
five-observation rolling average
        |
        v
take final available rolling value
        |
        v
predict national vote share
        |
        v
party with highest prediction is polling winner
```

## Final evaluation boundary

Development evidence:

- 14 elections;
- leave-one-election-out validation;
- MAE 1.3115;
- RMSE 1.7230;
- winner accuracy 92.9%.

Final holdout evidence:

- 8 later elections;
- MAE 1.2435;
- RMSE 1.6799;
- winner accuracy 87.5%.

The holdout is now frozen and must not be used for further selection.

## Future presentation architecture

The future Streamlit layer should:

- read frozen outputs only;
- avoid retraining models;
- show development and holdout results separately;
- expose country and election filters;
- display polling trends against actual results;
- present source-scope audit evidence;
- show limitations and the Australia 2019 miss clearly.

The presentation layer should remain downstream of the validated analytical pipeline.
