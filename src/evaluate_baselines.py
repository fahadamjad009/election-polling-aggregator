"""
Evaluates simple election-prediction baselines using only the development set.

Validation uses leave-one-election-out cross-validation. Every fold removes
all party rows belonging to one election, trains on the remaining elections,
and predicts the excluded election.

The chronological holdout dataset is deliberately not loaded here.
"""

import os
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


INPUT_PATH = "data/model/development_model_dataset.csv"
OUTPUT_DIR = "data/model/baselines"

PREDICTIONS_OUTPUT = (
    f"{OUTPUT_DIR}/development_oof_predictions.csv"
)
METRICS_OUTPUT = (
    f"{OUTPUT_DIR}/development_baseline_metrics.csv"
)
ELECTION_OUTPUT = (
    f"{OUTPUT_DIR}/development_election_predictions.csv"
)


NUMERIC_FEATURES = [
    "final_rolling_avg",
    "poll_std",
    "days_before_election",
    "n_poll_observations",
]

CATEGORICAL_FEATURES = [
    "country",
]

ELECTION_KEYS = [
    "country",
    "election_year",
]


def load_development_data():
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(
            f"Missing development dataset: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required = (
        ELECTION_KEYS
        + [
            "party",
            "actual_pct",
            "is_winner",
        ]
        + NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df["election_year"] = pd.to_numeric(
        df["election_year"],
        errors="raise",
    ).astype(int)

    for column in (
        NUMERIC_FEATURES
        + ["actual_pct", "is_winner"]
    ):
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    if not (
        df["dataset_split"] == "development"
    ).all():
        raise ValueError(
            "Non-development rows were found in the input."
        )

    return df


def make_preprocessor():
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                NUMERIC_FEATURES,
            ),
            (
                "country",
                OneHotEncoder(
                    handle_unknown="ignore",
                ),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )


def make_regression_model():
    return Pipeline(
        steps=[
            (
                "preprocess",
                make_preprocessor(),
            ),
            (
                "model",
                Ridge(alpha=10.0),
            ),
        ]
    )


def make_classification_model():
    return Pipeline(
        steps=[
            (
                "preprocess",
                make_preprocessor(),
            ),
            (
                "model",
                LogisticRegression(
                    C=0.5,
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )


def add_election_winner_predictions(df):
    df = df.copy()

    winner_score_columns = {
        "polling_baseline": "baseline_vote_prediction",
        "ridge_regression": "ridge_vote_prediction",
        "logistic_regression": "logistic_win_probability",
    }

    for model_name, score_column in winner_score_columns.items():
        prediction_column = (
            f"{model_name}_predicted_winner"
        )

        df[prediction_column] = 0

        winner_indices = (
            df.groupby(ELECTION_KEYS)[score_column]
            .idxmax()
        )

        df.loc[
            winner_indices,
            prediction_column,
        ] = 1

    return df


def build_election_summary(predictions):
    rows = []

    for keys, group in predictions.groupby(
        ELECTION_KEYS
    ):
        country, election_year = keys

        actual_winner = group.loc[
            group["is_winner"] == 1,
            "party",
        ].iloc[0]

        baseline_winner = group.loc[
            group[
                "polling_baseline_predicted_winner"
            ] == 1,
            "party",
        ].iloc[0]

        ridge_winner = group.loc[
            group[
                "ridge_regression_predicted_winner"
            ] == 1,
            "party",
        ].iloc[0]

        logistic_winner = group.loc[
            group[
                "logistic_regression_predicted_winner"
            ] == 1,
            "party",
        ].iloc[0]

        rows.append({
            "country": country,
            "election_year": election_year,
            "actual_winner": actual_winner,
            "polling_baseline_winner": (
                baseline_winner
            ),
            "polling_baseline_correct": int(
                baseline_winner == actual_winner
            ),
            "ridge_winner": ridge_winner,
            "ridge_correct": int(
                ridge_winner == actual_winner
            ),
            "logistic_winner": logistic_winner,
            "logistic_correct": int(
                logistic_winner == actual_winner
            ),
        })

    return pd.DataFrame(rows).sort_values(
        ELECTION_KEYS
    )


def regression_metrics(
    actual,
    predicted,
    model_name,
):
    return [
        {
            "task": "vote_share_regression",
            "model": model_name,
            "metric": "MAE",
            "value": mean_absolute_error(
                actual,
                predicted,
            ),
        },
        {
            "task": "vote_share_regression",
            "model": model_name,
            "metric": "RMSE",
            "value": mean_squared_error(
                actual,
                predicted,
            ) ** 0.5,
        },
    ]


def main():
    print(
        "Loading development dataset only..."
    )

    df = load_development_data()

    elections = (
        df[ELECTION_KEYS]
        .drop_duplicates()
        .sort_values(ELECTION_KEYS)
    )

    print(
        f"  {len(df)} party-election rows"
    )
    print(
        f"  {len(elections)} development elections"
    )
    print(
        "  Holdout dataset was not loaded"
    )

    prediction_parts = []

    for fold_number, election in enumerate(
        elections.itertuples(index=False),
        start=1,
    ):
        test_mask = (
            (df["country"] == election.country)
            & (
                df["election_year"]
                == election.election_year
            )
        )

        train = df.loc[~test_mask].copy()
        test = df.loc[test_mask].copy()

        regression_model = (
            make_regression_model()
        )
        classification_model = (
            make_classification_model()
        )

        regression_model.fit(
            train[
                NUMERIC_FEATURES
                + CATEGORICAL_FEATURES
            ],
            train["actual_pct"],
        )

        classification_model.fit(
            train[
                NUMERIC_FEATURES
                + CATEGORICAL_FEATURES
            ],
            train["is_winner"],
        )

        fold_predictions = test[
            [
                "country",
                "election_year",
                "party",
                "actual_pct",
                "is_winner",
                "final_rolling_avg",
            ]
        ].copy()

        fold_predictions["fold_number"] = (
            fold_number
        )

        # Honest polling baseline: use the final
        # rolling polling average directly as the
        # predicted vote share.
        fold_predictions[
            "baseline_vote_prediction"
        ] = test["final_rolling_avg"].to_numpy()

        fold_predictions[
            "ridge_vote_prediction"
        ] = regression_model.predict(
            test[
                NUMERIC_FEATURES
                + CATEGORICAL_FEATURES
            ]
        )

        fold_predictions[
            "logistic_win_probability"
        ] = classification_model.predict_proba(
            test[
                NUMERIC_FEATURES
                + CATEGORICAL_FEATURES
            ]
        )[:, 1]

        prediction_parts.append(
            fold_predictions
        )

        print(
            f"  Fold {fold_number:02d}: "
            f"held out {election.country} "
            f"{election.election_year} "
            f"({len(test)} parties)"
        )

    predictions = pd.concat(
        prediction_parts,
        ignore_index=True,
    )

    predictions = add_election_winner_predictions(
        predictions
    )

    election_summary = build_election_summary(
        predictions
    )

    metric_rows = []

    metric_rows.extend(
        regression_metrics(
            predictions["actual_pct"],
            predictions[
                "baseline_vote_prediction"
            ],
            "final_polling_average",
        )
    )

    metric_rows.extend(
        regression_metrics(
            predictions["actual_pct"],
            predictions[
                "ridge_vote_prediction"
            ],
            "ridge_regression",
        )
    )

    metric_rows.extend([
        {
            "task": "winner_classification",
            "model": "final_polling_average",
            "metric": (
                "election_winner_accuracy"
            ),
            "value": election_summary[
                "polling_baseline_correct"
            ].mean(),
        },
        {
            "task": "winner_classification",
            "model": "ridge_regression",
            "metric": (
                "election_winner_accuracy"
            ),
            "value": election_summary[
                "ridge_correct"
            ].mean(),
        },
        {
            "task": "winner_classification",
            "model": "logistic_regression",
            "metric": (
                "election_winner_accuracy"
            ),
            "value": election_summary[
                "logistic_correct"
            ].mean(),
        },
        {
            "task": "winner_classification",
            "model": "logistic_regression",
            "metric": "OOF_ROC_AUC",
            "value": roc_auc_score(
                predictions["is_winner"],
                predictions[
                    "logistic_win_probability"
                ],
            ),
        },
        {
            "task": "winner_classification",
            "model": "logistic_regression",
            "metric": (
                "row_accuracy_at_0.5"
            ),
            "value": accuracy_score(
                predictions["is_winner"],
                (
                    predictions[
                        "logistic_win_probability"
                    ] >= 0.5
                ).astype(int),
            ),
        },
    ])

    metrics = pd.DataFrame(metric_rows)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    predictions.to_csv(
        PREDICTIONS_OUTPUT,
        index=False,
    )

    metrics.to_csv(
        METRICS_OUTPUT,
        index=False,
    )

    election_summary.to_csv(
        ELECTION_OUTPUT,
        index=False,
    )

    print(
        "\n=== DEVELOPMENT OOF METRICS ==="
    )

    display_metrics = metrics.copy()
    display_metrics["value"] = (
        display_metrics["value"].round(4)
    )

    print(
        display_metrics.to_string(index=False)
    )

    print(
        "\n=== DEVELOPMENT ELECTION WINNERS ==="
    )

    print(
        election_summary.to_string(index=False)
    )

    print(
        "\nImportant: these are development "
        "cross-validation results, not final "
        "holdout performance."
    )

    print("\nSaved:")
    print(f"  {PREDICTIONS_OUTPUT}")
    print(f"  {METRICS_OUTPUT}")
    print(f"  {ELECTION_OUTPUT}")


if __name__ == "__main__":
    main()
