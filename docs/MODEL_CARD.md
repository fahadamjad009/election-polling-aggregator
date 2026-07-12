# Model Card

## Model name

Election Polling Aggregator — Final Five-Observation Polling Average

## Model version

Final documented model selected after development-only validation and evaluated once on the locked chronological holdout.

## Model overview

The Election Polling Aggregator estimates national party vote share and identifies the national polling leader for historical elections in:

- Australia;
- Canada;
- the United Kingdom;
- the United States.

The final selected method is not a fitted machine-learning model.

It uses the final available five-observation rolling polling average for each party before election day:

`final_rolling_avg`

Within each election, the party with the highest final rolling average is treated as the predicted polling winner.

The method was selected because it outperformed the evaluated Ridge-regression challengers on development vote-share error while matching the strongest challenger on winner accuracy.

## Intended tasks

The model supports two related tasks.

### Vote-share estimation

Estimate each included party's national vote share using its final five-observation polling average.

### Polling-leader identification

Identify the party with the highest estimated national vote share within each election.

This is reported as polling-winner accuracy against the actual national popular-vote winner represented in the modelling dataset.

## Out-of-scope uses

The model does not predict:

- constituency or district results;
- parliamentary seats;
- electoral-college votes;
- coalition formation;
- government formation;
- prime-minister or president selection rules;
- turnout;
- demographic subgroup voting;
- local, state, provincial or regional outcomes;
- causal effects of campaigns or political events;
- real-time election probabilities;
- uncertainty intervals;
- future elections outside the declared data and evaluation design.

The predicted polling leader must not be interpreted as a guaranteed election winner.

## Geographic and electoral scope

The final dataset covers national elections from four countries.

### Australia

Australia is represented through national two-party-preferred polling and results.

The canonical modelled labels are:

- `ALP (2PP)`;
- `L/NP (2PP)`.

The Australian component is therefore not a full primary-vote model.

### Canada

Canadian federal national polling and national popular-vote results are used for included parties.

### United Kingdom

United Kingdom general-election national polling and national popular-vote results are used.

Polling label `LD` is mapped to the canonical actual-result label `LIB`.

### United States

United States presidential national popular-vote polling and national popular-vote results are used.

The project does not model the Electoral College.

## Data inputs

The model consumes one final modelling row per party and election.

The selected prediction field is:

`final_rolling_avg`

This value is created from polling observations that:

- belong to an approved national source table;
- have a valid country, election year and party;
- occur on or before the verified election date;
- have passed cleaning and canonical party mapping;
- remain after documented scope exclusions;
- are grouped by country, election and party;
- are ordered chronologically.

The rolling feature uses up to the latest five valid observations available for the party.

## Final dataset size

| Dataset | Party-election rows | Elections |
|---|---:|---:|
| Full modelling dataset | 68 | 22 |
| Development dataset | 43 | 14 |
| Chronological holdout | 25 | 8 |

All rows belonging to the same election remain in the same split.

## Development-validation design

Model selection was performed using development elections only.

The project used leave-one-election-out cross-validation.

For each fold:

1. one complete election was withheld;
2. all remaining development elections formed the training set for fitted challengers;
3. predictions were produced for every party in the withheld election;
4. vote-share and election-winner metrics were recorded;
5. the process was repeated until every development election had served as the validation election.

This election-level design prevents rows from the same election appearing in both training and validation data.

## Evaluated methods

### Selected benchmark

Final five-observation polling average:

`final_rolling_avg`

This method directly uses the final rolling polling estimate and requires no fitted coefficients.

### Ridge-regression challengers

Ridge regression was evaluated using several feature groups, including:

- broad campaign features;
- recent-window features;
- final-polling plus recent-window features.

The strongest Ridge challenger used final plus recent-window features.

### Logistic-regression challenger

Logistic regression was evaluated for winner classification using development-only election-level validation.

It provided a ranked winner probability but did not improve the final model-selection criteria sufficiently to replace the benchmark.

## Development results

The selected final polling-average benchmark achieved:

| Metric | Result |
|---|---:|
| Mean absolute error | 1.3115 percentage points |
| Root mean squared error | 1.7230 percentage points |
| Election-winner accuracy | 92.9% |
| Correct election winners | 13 of 14 |

The strongest Ridge challenger achieved:

| Metric | Result |
|---|---:|
| Mean absolute error | 2.2684 percentage points |
| Root mean squared error | 2.8831 percentage points |
| Election-winner accuracy | 92.9% |

The benchmark therefore produced substantially lower vote-share error while matching the Ridge challenger on election-winner accuracy.

The broader legacy Ridge feature set performed materially worse:

| Metric | Result |
|---|---:|
| Mean absolute error | 3.7050 percentage points |
| Root mean squared error | 4.6891 percentage points |

## Model-selection decision

The final polling average was selected before the holdout was evaluated.

The decision was based on development-only evidence:

- lower vote-share MAE than fitted Ridge challengers;
- lower RMSE than fitted Ridge challengers;
- winner accuracy equal to the strongest Ridge challenger;
- simpler and more interpretable behaviour;
- no evidence that additional fitted complexity improved out-of-election validation;
- lower operational and methodological complexity;
- direct traceability from source polling observations to the prediction.

The project therefore rejected unnecessary model complexity rather than selecting a more complex method for presentation value.

The recorded selection decision is stored in:

`data/model/final_holdout/model_selection_decision.json`

## Chronological holdout

The final holdout contains the later declared elections:

- Australia: 2019 and 2022;
- Canada: 2015 and 2019;
- United Kingdom: 2017 and 2019;
- United States: 2012 and 2016.

The holdout contains:

- 25 party-election rows;
- 8 elections.

The selected method was evaluated once on this set.

## Final holdout results

| Metric | Result |
|---|---:|
| Mean absolute error | 1.2435 percentage points |
| Root mean squared error | 1.6799 percentage points |
| Election-winner accuracy | 87.5% |
| Correct election winners | 7 of 8 |

The holdout error was slightly lower than the development cross-validation error, but this must not be interpreted as proof of broad universal performance because the holdout contains only eight elections.

## Holdout country-level error

| Country | Rows | Elections | MAE | RMSE | Mean error |
|---|---:|---:|---:|---:|---:|
| Australia | 4 | 2 | 1.7650 | 2.1154 | -0.3000 |
| Canada | 10 | 2 | 1.0526 | 1.2584 | -0.1167 |
| United Kingdom | 6 | 2 | 0.3800 | 0.4439 | 0.0756 |
| United States | 5 | 2 | 2.2442 | 2.6697 | -2.0395 |

The United States subset had the largest holdout MAE and a negative mean error, indicating underestimation across the included US party rows.

These country-level summaries contain very small numbers of elections and must not be treated as stable country rankings.

## Known incorrect holdout prediction

The only incorrect holdout polling winner was Australia 2019.

The model predicted:

`ALP (2PP)`

The actual two-party-preferred winner was:

`L/NP (2PP)`

For that election:

- predicted ALP two-party-preferred polling estimate: 51.4%;
- actual ALP two-party-preferred result: 48.47%;
- predicted polling margin: 2.8 percentage points toward ALP;
- actual result margin: 3.06 percentage points toward L/NP.

Both included party rows had an absolute vote-share error of approximately 2.93 percentage points.

This failure is retained as an important example of systematic polling error that averaging alone cannot remove.

## Leakage controls

The project applies the following leakage protections.

### Election-date filtering

Verified election dates are stored separately.

All polling observations after the relevant election date are removed before rolling averages or momentum features are calculated.

The final validation confirmed that zero post-election feature rows remained.

### Election-level splitting

Development and holdout separation occurs at complete-election level.

Rows from the same election cannot appear in both splits.

### Development-only model selection

The baseline, Ridge challengers, logistic challenger and feature ablations were evaluated using development elections only.

The holdout was not loaded for model selection.

### Holdout lock

After the one-time final evaluation, the following file was created:

`data/model/final_holdout/HOLDOUT_EVALUATED.lock`

Its instruction is:

> Final chronological holdout evaluated.  
> Do not retune or repeatedly inspect this set.

Future model changes must not be selected using the existing holdout results.

## Source-scope governance

Historical polling pages can contain national tables, regional tables, demographic subsets, hypothetical contests and other non-comparable content.

The project therefore audited polling source tables before feature engineering.

The governance process included:

- automated source-table profiling;
- comparison of election-result marker rows with verified national results;
- approved, rejected and review classifications;
- documented manual overrides;
- separate inclusion and exclusion audit outputs;
- exclusion of non-national or structurally unsuitable tables.

Only approved national polling tables enter the final predictive pipeline.

## Data quality invariants

The final modelling pipeline requires:

1. every row has a valid country, election year and party;
2. each party appears at most once per election in the modelling dataset;
3. every modelled election contains exactly one actual winner;
4. no final feature row uses polling after election day;
5. development and holdout elections do not overlap;
6. only approved national tables enter feature engineering;
7. Australian final modelling uses two-party-preferred labels;
8. UK Liberal Democrat polling and result labels are mapped consistently;
9. holdout outputs are not used for later model selection;
10. retrospective similarity features do not enter the predictive dataset.

## Performance interpretation

The model should be understood as a historical national polling benchmark.

It demonstrates that:

- carefully governed national polling tables can produce useful vote-share estimates;
- strict leakage prevention matters;
- election-level validation gives a more credible test than random row splitting;
- a simple polling average can outperform more complex fitted models on a small heterogeneous dataset;
- systematic polling misses remain possible;
- correct winner classification does not guarantee an accurate vote margin;
- low average error does not eliminate election-specific failures.

The results do not establish that the model will perform equally well on future elections, other countries or different polling environments.

## Limitations

### Small number of elections

The full dataset contains 22 elections, with only 14 development elections and 8 holdout elections.

This limits statistical certainty and makes subgroup results unstable.

### Cross-country heterogeneity

The four countries differ in:

- electoral systems;
- party systems;
- polling practices;
- historical periods;
- available data structure;
- number of modelled parties.

A single aggregated metric can conceal these differences.

### No probabilistic uncertainty

The model produces point estimates only.

It does not produce:

- confidence intervals;
- prediction intervals;
- calibrated win probabilities;
- polling-house uncertainty;
- sampling-error propagation;
- scenario ranges.

### Simplified poll aggregation

The final method uses a five-observation rolling average.

It does not currently weight polls by:

- sample size;
- pollster quality;
- fieldwork recency beyond ordering;
- survey mode;
- historical pollster bias;
- likely-voter methodology;
- population coverage.

### National vote only

The project estimates national vote share.

It cannot infer seat outcomes reliably in district-based, constituency-based or Electoral College systems.

### Australian representation

Australia is represented by two-party-preferred values rather than full primary-vote modelling.

This excludes richer multiparty primary-vote interpretation.

### Source dependence

The historical data depends on public source tables and previously published polling averages.

Source corrections, omissions or formatting changes can affect the pipeline.

### Manual governance decisions

Some source-table classifications required documented manual review.

Although these decisions are auditable, they remain human judgements.

### Systematic polling error

A rolling average reduces noise but cannot correct an industry-wide shared polling bias.

Australia 2019 demonstrates this limitation directly.

### Historical performance is not a guarantee

Political systems, polling methods and voter behaviour change over time.

Historical performance must not be presented as guaranteed future accuracy.

## Ethical and responsible use

Election forecasts can influence public expectations and political narratives.

Users should:

- report uncertainty and limitations prominently;
- avoid presenting the predicted leader as a certain winner;
- avoid using the output to discourage voting or participation;
- distinguish national popular vote from seat or government outcomes;
- disclose the small historical sample;
- disclose country-specific modelling conventions;
- retain incorrect predictions and negative evidence;
- avoid tuning against the locked holdout;
- verify new source data before publication;
- use newly declared external elections for future evaluation.

The model should be used for education, portfolio demonstration, reproducible research and historical analysis rather than high-stakes operational election calls.

## Reproducibility artefacts

### Development metrics

`data/model/baselines/development_baseline_metrics.csv`

### Development predictions

`data/model/baselines/development_oof_predictions.csv`

### Election-level development results

`data/model/baselines/development_election_predictions.csv`

### Development error analysis

`data/model/baselines/development_error_by_country.csv`

`data/model/baselines/development_error_by_election.csv`

`data/model/baselines/development_party_error_detail.csv`

`data/model/baselines/development_wrong_winner_analysis.csv`

### Feature-ablation results

`data/model/ablation/development_feature_ablation_metrics.csv`

`data/model/ablation/development_feature_ablation_predictions.csv`

`data/model/ablation/development_feature_ablation_winners.csv`

### Final holdout results

`data/model/final_holdout/final_holdout_metrics.csv`

`data/model/final_holdout/final_holdout_predictions.csv`

`data/model/final_holdout/final_holdout_election_results.csv`

`data/model/final_holdout/final_holdout_country_errors.csv`

`data/model/final_holdout/final_evaluation_summary.md`

### Governance artefacts

`data/model/final_holdout/model_selection_decision.json`

`data/model/final_holdout/HOLDOUT_EVALUATED.lock`

## Relevant implementation scripts

- `src/build_features.py`
- `src/build_model_dataset.py`
- `src/build_train_test_split.py`
- `src/evaluate_baselines.py`
- `src/evaluate_feature_ablation.py`
- `src/evaluate_final_holdout.py`

## Monitoring and future evaluation

The current historical model is static.

Any future extension should monitor:

- missing or malformed polling dates;
- new party-label mismatches;
- unapproved source tables entering the feature layer;
- post-election observations;
- duplicate party-election rows;
- elections without exactly one actual winner;
- changes in country-level error;
- systematic underprediction or overprediction;
- incorrect polling-winner calls;
- changes in polling methodology;
- deviations from the declared split and holdout policy.

Future evaluation must use a newly declared external test set or newly completed elections.

The existing chronological holdout must remain frozen.

## Final model statement

The final selected method is the last available five-observation rolling polling average for each party before election day.

It was selected because development-only validation showed that it produced lower vote-share error than the fitted challengers while retaining equal or better practical interpretability.

Its final chronological holdout performance was:

- MAE: 1.2435 percentage points;
- RMSE: 1.6799 percentage points;
- election-winner accuracy: 87.5%;
- correct winners: 7 of 8.

The model is a transparent historical national polling benchmark, not a universal election forecasting system.
