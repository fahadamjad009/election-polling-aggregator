"""
Compares compact feature sets using development data only.

Validation is leave-one-election-out. The chronological holdout dataset is
not loaded or evaluated. The final polling average remains the benchmark.
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
OUTPUT_DIR = "data/model/ablation"

METRICS_OUTPUT = (
    f"{OUTPUT_DIR}/development_feature_ablation_metrics.csv"
)

PREDICTIONS_OUTPUT = (
    f"{OUTPUT_DIR}/development_feature_ablation_predictions.csv"
)

ELECTION_OUTPUT = (
    f"{OUTPUT_DIR}/development_feature_ablation_winners.csv"
)


ELECTION_KEYS = [
    "country",
    "election_year",
]

CATEGORICAL_FEATURES = [
    "country",
]

FEATURE_SETS = {
    "legacy_broad": [
        "final_rolling_avg",
        "poll_std",
        "days_before_election",
        "n_poll_observations",
    ],
    "recent_compact": [
        "recent_30d_mean",
        "recent_30d_std",
        "recent_30d_observations",
        "recent_30d_trend_per_day",
        "days_before_election",
    ],
    "final_plus_recent": [
        "final_rolling_avg",
        "recent_30d_mean",
        "recent_30d_std",
        "recent_30d_observations",
        "recent_30d_trend_per_day",
        "final_vs_recent_30d_mean",
        "days_before_election",
    ],
}


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
            "dataset_split",
            "actual_pct",
            "is_winner",
            "final_rolling_avg",
        ]
        + CATEGORICAL_FEATURES
        + sorted(
            {
                feature
                for features in FEATURE_SETS.values()
                for feature in features
            }
        )
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

    if not (
        df["dataset_split"] == "development"
    ).all():
        raise ValueError(
            "Non-development rows were found."
        )

    df["election_year"] = pd.to_numeric(
        df["election_year"],
        errors="raise",
    ).astype(int)

    numeric_columns = sorted(
        {
            "actual_pct",
            "is_winner",
            "final_rolling_avg",
            *[
                feature
                for features in FEATURE_SETS.values()
                for feature in features
            ],
        }
    )

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    if df[numeric_columns].isna().any().any():
        raise ValueError(
            "Missing numeric values were found."
        )

    if np.isinf(
        df[numeric_columns].to_numpy()
    ).any():
        raise ValueError(
            "Infinite numeric values were found."
        )

    return df


def make_preprocessor(numeric_features):
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                numeric_features,
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


def make_ridge(numeric_features):
    return Pipeline(
        steps=[
            (
                "preprocess",
                make_preprocessor(
                    numeric_features
                ),
            ),
            (
                "model",
                Ridge(alpha=10.0),
            ),
        ]
    )


def make_logistic(numeric_features):
    return Pipeline(
        steps=[
            (
                "preprocess",
                make_preprocessor(
                    numeric_features
                ),
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


def add_predicted_winner(df, score_column):
    result = df.copy()

    result["predicted_winner"] = 0

    winner_indices = (
        result.groupby(ELECTION_KEYS)[
            score_column
        ]
        .idxmax()
    )

    result.loc[
        winner_indices,
        "predicted_winner",
    ] = 1

    return result


def winner_accuracy(df):
    election_rows = []

    for keys, group in df.groupby(
        ELECTION_KEYS
    ):
        actual_winner = group.loc[
            group["is_winner"] == 1,
            "party",
        ].iloc[0]

        predicted_winner = group.loc[
            group["predicted_winner"] == 1,
            "party",
        ].iloc[0]

        election_rows.append({
            "country": keys[0],
            "election_year": keys[1],
            "actual_winner": actual_winner,
            "predicted_winner": predicted_winner,
            "correct": int(
                actual_winner
                == predicted_winner
            ),
        })

    summary = pd.DataFrame(election_rows)

    return (
        float(summary["correct"].mean()),
        summary,
    )


def regression_rows(
    actual,
    predicted,
    feature_set,
    model,
):
    return [
        {
            "task": "vote_share_regression",
            "feature_set": feature_set,
            "model": model,
            "metric": "MAE",
            "value": mean_absolute_error(
                actual,
                predicted,
            ),
        },
        {
            "task": "vote_share_regression",
            "feature_set": feature_set,
            "model": model,
            "metric": "RMSE",
            "value": (
                mean_squared_error(
                    actual,
                    predicted,
                )
                ** 0.5
            ),
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

    for feature_set, numeric_features in (
        FEATURE_SETS.items()
    ):
        print(
            f"\nEvaluating: {feature_set}"
        )

        for fold_number, election in enumerate(
            elections.itertuples(index=False),
            start=1,
        ):
            test_mask = (
                (
                    df["country"]
                    == election.country
                )
                & (
                    df["election_year"]
                    == election.election_year
                )
            )

            train = df.loc[
                ~test_mask
            ].copy()

            test = df.loc[
                test_mask
            ].copy()

            ridge = make_ridge(
                numeric_features
            )

            logistic = make_logistic(
                numeric_features
            )

            model_columns = (
                numeric_features
                + CATEGORICAL_FEATURES
            )

            ridge.fit(
                train[model_columns],
                train["actual_pct"],
            )

            logistic.fit(
                train[model_columns],
                train["is_winner"],
            )

            fold = test[
                [
                    "country",
                    "election_year",
                    "party",
                    "actual_pct",
                    "is_winner",
                    "final_rolling_avg",
                ]
            ].copy()

            fold["feature_set"] = (
                feature_set
            )

            fold["fold_number"] = (
                fold_number
            )

            fold[
                "baseline_vote_prediction"
            ] = test[
                "final_rolling_avg"
            ].to_numpy()

            fold[
                "ridge_vote_prediction"
            ] = ridge.predict(
                test[model_columns]
            )

            fold[
                "logistic_win_probability"
            ] = logistic.predict_proba(
                test[model_columns]
            )[:, 1]

            prediction_parts.append(
                fold
            )

    predictions = pd.concat(
        prediction_parts,
        ignore_index=True,
    )

    metrics = []
    winner_parts = []

    baseline_source = predictions[
        predictions["feature_set"]
        == "legacy_broad"
    ].copy()

    baseline_winners = add_predicted_winner(
        baseline_source,
        "baseline_vote_prediction",
    )

    (
        baseline_winner_accuracy,
        baseline_elections,
    ) = winner_accuracy(
        baseline_winners
    )

    metrics.extend(
        regression_rows(
            baseline_source["actual_pct"],
            baseline_source[
                "baseline_vote_prediction"
            ],
            "benchmark",
            "final_polling_average",
        )
    )

    metrics.append({
        "task": "winner_classification",
        "feature_set": "benchmark",
        "model": "final_polling_average",
        "metric": "election_winner_accuracy",
        "value": baseline_winner_accuracy,
    })

    baseline_elections[
        "feature_set"
    ] = "benchmark"

    baseline_elections[
        "model"
    ] = "final_polling_average"

    winner_parts.append(
        baseline_elections
    )

    for feature_set in FEATURE_SETS:
        current = predictions[
            predictions["feature_set"]
            == feature_set
        ].copy()

        metrics.extend(
            regression_rows(
                current["actual_pct"],
                current[
                    "ridge_vote_prediction"
                ],
                feature_set,
                "ridge_regression",
            )
        )

        ridge_winners = add_predicted_winner(
            current,
            "ridge_vote_prediction",
        )

        (
            ridge_accuracy,
            ridge_elections,
        ) = winner_accuracy(
            ridge_winners
        )

        metrics.append({
            "task": "winner_classification",
            "feature_set": feature_set,
            "model": "ridge_regression",
            "metric": "election_winner_accuracy",
            "value": ridge_accuracy,
        })

        ridge_elections[
            "feature_set"
        ] = feature_set

        ridge_elections[
            "model"
        ] = "ridge_regression"

        winner_parts.append(
            ridge_elections
        )

        logistic_winners = add_predicted_winner(
            current,
            "logistic_win_probability",
        )

        (
            logistic_accuracy,
            logistic_elections,
        ) = winner_accuracy(
            logistic_winners
        )

        metrics.extend([
            {
                "task": "winner_classification",
                "feature_set": feature_set,
                "model": "logistic_regression",
                "metric": (
                    "election_winner_accuracy"
                ),
                "value": logistic_accuracy,
            },
            {
                "task": "winner_classification",
                "feature_set": feature_set,
                "model": "logistic_regression",
                "metric": "OOF_ROC_AUC",
                "value": roc_auc_score(
                    current["is_winner"],
                    current[
                        "logistic_win_probability"
                    ],
                ),
            },
            {
                "task": "winner_classification",
                "feature_set": feature_set,
                "model": "logistic_regression",
                "metric": "row_accuracy_at_0.5",
                "value": accuracy_score(
                    current["is_winner"],
                    (
                        current[
                            "logistic_win_probability"
                        ]
                        >= 0.5
                    ).astype(int),
                ),
            },
        ])

        logistic_elections[
            "feature_set"
        ] = feature_set

        logistic_elections[
            "model"
        ] = "logistic_regression"

        winner_parts.append(
            logistic_elections
        )

    metrics = pd.DataFrame(metrics)

    winner_summary = pd.concat(
        winner_parts,
        ignore_index=True,
    ).sort_values(
        [
            "feature_set",
            "model",
            "country",
            "election_year",
        ]
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    metrics.to_csv(
        METRICS_OUTPUT,
        index=False,
    )

    predictions.to_csv(
        PREDICTIONS_OUTPUT,
        index=False,
    )

    winner_summary.to_csv(
        ELECTION_OUTPUT,
        index=False,
    )

    print(
        "\n=== DEVELOPMENT FEATURE ABLATION ==="
    )

    display = metrics.copy()

    display["value"] = (
        display["value"]
        .round(4)
    )

    print(
        display.sort_values(
            [
                "task",
                "metric",
                "value",
            ]
        ).to_string(index=False)
    )

    print(
        "\nBenchmark to beat:"
    )

    benchmark = metrics[
        metrics["feature_set"]
        == "benchmark"
    ]

    print(
        benchmark.to_string(
            index=False
        )
    )

    print(
        "\nImportant: all results are development "
        "leave-one-election-out estimates."
    )

    print(
        "The chronological holdout remains untouched."
    )

    print("\nSaved:")
    print(f"  {METRICS_OUTPUT}")
    print(f"  {PREDICTIONS_OUTPUT}")
    print(f"  {ELECTION_OUTPUT}")


if __name__ == "__main__":
    main()
