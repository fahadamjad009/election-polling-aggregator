# Final Evaluation Summary

## Selected method

- Model: `final_polling_average`
- Prediction field: `final_rolling_avg`
- Prediction rule: use the final five-observation rolling polling average directly.
- Selection was completed using development elections only.
- No tuning or model reselection occurred after viewing the chronological holdout.

## Development validation

- Leave-one-election-out MAE: **1.3115 percentage points**
- Leave-one-election-out RMSE: **1.7230 percentage points**
- Election-winner accuracy: **92.9%**

## Chronological holdout

- Party-election rows: **25**
- Elections: **8**
- MAE: **1.2435 percentage points**
- RMSE: **1.6799 percentage points**
- Election-winner accuracy: **87.5%**

## Holdout election results

| Country | Election | Actual winner | Predicted winner | Correct |
|---|---:|---|---|---:|
| australia | 2019 | L/NP (2PP) | ALP (2PP) | No |
| australia | 2022 | ALP (2PP) | ALP (2PP) | Yes |
| canada | 2015 | LPC | LPC | Yes |
| canada | 2019 | CPC | CPC | Yes |
| uk | 2017 | CON | CON | Yes |
| uk | 2019 | CON | CON | Yes |
| us | 2012 | DEM | DEM | Yes |
| us | 2016 | DEM | DEM | Yes |

## Model-selection conclusion

The simple final polling average remained stronger than the tested Ridge and logistic-regression alternatives. Recent-window features improved the strongest Ridge challenger relative to the original broad feature set, but the challenger still produced materially worse vote-share error than the polling benchmark.

## Important limitations

- Australia is modelled using national two-party-preferred polling rather than full primary-vote party shares.
- The dataset contains only 22 elections across four countries.
- Historical polling source formats are inconsistent and required audited national-table filtering.
- The system predicts national vote share and the national polling leader, not seats, electoral-college outcomes, coalition formation, or government formation.
- Polling misses can remain systematic, as shown by Australia 2019 and the development result for the United States in 2000.

## Holdout governance

The chronological holdout was evaluated once and is protected by:

`data/model/final_holdout/HOLDOUT_EVALUATED.lock`
