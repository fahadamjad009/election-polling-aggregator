"""
Runs the single final evaluation on the chronological holdout set.

The selected method was fixed using development-only leave-one-election-out
validation: final_rolling_avg is used directly as the vote-share prediction.

No model fitting, feature selection, threshold selection, or tuning occurs
here. A completion marker prevents casual repeated inspection of the
holdout results.
"""

from pathlib import Path
import json

import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)


INPUT_PATH = Path(
    "data/model/holdout_model_dataset.csv"
)

OUTPUT_DIR = Path(
    "data/model/final_holdout"
)

METRICS_OUTPUT = (
    OUTPUT_DIR / "final_holdout_metrics.csv"
)

PREDICTIONS_OUTPUT = (
    OUTPUT_DIR / "final_holdout_predictions.csv"
)

ELECTION_OUTPUT = (
    OUTPUT_DIR / "final_holdout_election_results.csv"
)

COUNTRY_OUTPUT = (
    OUTPUT_DIR / "final_holdout_country_errors.csv"
)

DECISION_OUTPUT = (
    OUTPUT_DIR / "model_selection_decision.json"
)

LOCK_PATH = (
    OUTPUT_DIR / "HOLDOUT_EVALUATED.lock"
)

ELECTION_KEYS = [
    "country",
    "election_year",
]


def load_holdout():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing holdout dataset: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required = [
        "country",
        "election_year",
        "party",
        "dataset_split",
        "actual_pct",
        "is_winner",
        "final_rolling_avg",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing holdout columns: {missing}"
        )

    if not (
        df["dataset_split"] == "holdout"
    ).all():
        raise ValueError(
            "Non-holdout rows were found."
        )

    df["election_year"] = pd.to_numeric(
        df["election_year"],
        errors="raise",
    ).astype(int)

    numeric_columns = [
        "actual_pct",
        "is_winner",
        "final_rolling_avg",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    if df[numeric_columns].isna().any().any():
        raise ValueError(
            "Missing numeric values were found."
        )

    duplicated = df.duplicated(
        [
            "country",
            "election_year",
            "party",
        ],
        keep=False,
    )

    if duplicated.any():
        raise ValueError(
            "Duplicate party-election rows found:\n"
            + df.loc[
                duplicated,
                [
                    "country",
                    "election_year",
                    "party",
                ],
            ].to_string(index=False)
        )

    winner_counts = (
        df.groupby(ELECTION_KEYS)[
            "is_winner"
        ]
        .sum()
    )

    invalid = winner_counts[
        winner_counts != 1
    ]

    if len(invalid):
        raise ValueError(
            "Expected exactly one winner per holdout election:\n"
            + invalid.to_string()
        )

    return df


def build_election_results(predictions):
    rows = []

    for keys, group in predictions.groupby(
        ELECTION_KEYS
    ):
        country, election_year = keys

        actual_winner_row = group.loc[
            group["is_winner"] == 1
        ].iloc[0]

        predicted_winner_row = group.loc[
            group[
                "selected_model_predicted_winner"
            ] == 1
        ].iloc[0]

        ordered = group.sort_values(
            "selected_vote_prediction",
            ascending=False,
        )

        predicted_margin = (
            ordered.iloc[0][
                "selected_vote_prediction"
            ]
            - ordered.iloc[1][
                "selected_vote_prediction"
            ]
            if len(ordered) >= 2
            else float("nan")
        )

        actual_ordered = group.sort_values(
            "actual_pct",
            ascending=False,
        )

        actual_margin = (
            actual_ordered.iloc[0]["actual_pct"]
            - actual_ordered.iloc[1]["actual_pct"]
            if len(actual_ordered) >= 2
            else float("nan")
        )

        rows.append({
            "country": country,
            "election_year": election_year,
            "actual_winner": (
                actual_winner_row["party"]
            ),
            "predicted_winner": (
                predicted_winner_row["party"]
            ),
            "winner_correct": int(
                actual_winner_row["party"]
                == predicted_winner_row["party"]
            ),
            "predicted_winner_polling_pct": (
                predicted_winner_row[
                    "selected_vote_prediction"
                ]
            ),
            "predicted_winner_actual_pct": (
                predicted_winner_row["actual_pct"]
            ),
            "predicted_margin": predicted_margin,
            "actual_margin": actual_margin,
        })

    return pd.DataFrame(rows).sort_values(
        ELECTION_KEYS
    )


def main():
    if LOCK_PATH.exists():
        raise RuntimeError(
            "The final holdout has already been evaluated.\n"
            f"Lock file: {LOCK_PATH}\n"
            "Do not rerun or retune against the holdout."
        )

    print(
        "Loading untouched chronological holdout..."
    )

    df = load_holdout()

    elections = (
        df[ELECTION_KEYS]
        .drop_duplicates()
        .sort_values(ELECTION_KEYS)
    )

    print(
        f"  {len(df)} party-election rows"
    )

    print(
        f"  {len(elections)} holdout elections"
    )

    print(
        "  Selected method: final polling average"
    )

    predictions = df[
        [
            "country",
            "election_year",
            "party",
            "actual_pct",
            "is_winner",
            "final_rolling_avg",
        ]
    ].copy()

    predictions[
        "selected_vote_prediction"
    ] = predictions[
        "final_rolling_avg"
    ]

    predictions[
        "vote_share_error"
    ] = (
        predictions[
            "selected_vote_prediction"
        ]
        - predictions["actual_pct"]
    )

    predictions[
        "absolute_error"
    ] = predictions[
        "vote_share_error"
    ].abs()

    predictions[
        "selected_model_predicted_winner"
    ] = 0

    winner_indices = (
        predictions.groupby(ELECTION_KEYS)[
            "selected_vote_prediction"
        ]
        .idxmax()
    )

    predictions.loc[
        winner_indices,
        "selected_model_predicted_winner",
    ] = 1

    election_results = build_election_results(
        predictions
    )

    mae = mean_absolute_error(
        predictions["actual_pct"],
        predictions[
            "selected_vote_prediction"
        ],
    )

    rmse = mean_squared_error(
        predictions["actual_pct"],
        predictions[
            "selected_vote_prediction"
        ],
    ) ** 0.5

    winner_accuracy = float(
        election_results[
            "winner_correct"
        ].mean()
    )

    metrics = pd.DataFrame([
        {
            "evaluation_set": (
                "chronological_holdout"
            ),
            "task": "vote_share_regression",
            "model": "final_polling_average",
            "metric": "MAE",
            "value": mae,
            "rows": len(predictions),
            "elections": len(elections),
        },
        {
            "evaluation_set": (
                "chronological_holdout"
            ),
            "task": "vote_share_regression",
            "model": "final_polling_average",
            "metric": "RMSE",
            "value": rmse,
            "rows": len(predictions),
            "elections": len(elections),
        },
        {
            "evaluation_set": (
                "chronological_holdout"
            ),
            "task": "winner_classification",
            "model": "final_polling_average",
            "metric": (
                "election_winner_accuracy"
            ),
            "value": winner_accuracy,
            "rows": len(predictions),
            "elections": len(elections),
        },
    ])

    country_errors = (
        predictions.groupby("country")
        .agg(
            rows=("party", "size"),
            elections=(
                "election_year",
                "nunique",
            ),
            MAE=(
                "absolute_error",
                "mean",
            ),
            mean_error=(
                "vote_share_error",
                "mean",
            ),
            RMSE=(
                "vote_share_error",
                lambda values: (
                    (values ** 2).mean()
                    ** 0.5
                ),
            ),
        )
        .reset_index()
    )

    decision = {
        "selected_model": (
            "final_polling_average"
        ),
        "prediction_column": (
            "final_rolling_avg"
        ),
        "selection_basis": (
            "Lowest development leave-one-election-out "
            "MAE and RMSE while retaining the highest "
            "development election-winner accuracy."
        ),
        "development_mae": (
            1.3115491966662662
        ),
        "development_rmse": (
            1.7230338400942018
        ),
        "development_winner_accuracy": (
            0.9285714285714286
        ),
        "challenger_decision": (
            "Rejected. No Ridge or logistic feature "
            "configuration improved the regression "
            "benchmark without reducing performance."
        ),
        "holdout_usage": (
            "Single final evaluation only; no tuning "
            "or reselection after inspection."
        ),
    }

    OUTPUT_DIR.mkdir(
        parents=True,
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

    election_results.to_csv(
        ELECTION_OUTPUT,
        index=False,
    )

    country_errors.to_csv(
        COUNTRY_OUTPUT,
        index=False,
    )

    DECISION_OUTPUT.write_text(
        json.dumps(
            decision,
            indent=2,
        ),
        encoding="utf-8",
    )

    LOCK_PATH.write_text(
        "Final chronological holdout evaluated.\n"
        "Do not retune or repeatedly inspect this set.\n",
        encoding="utf-8",
    )

    print(
        "\n=== FINAL CHRONOLOGICAL HOLDOUT ==="
    )

    display_metrics = metrics.copy()

    display_metrics["value"] = (
        display_metrics["value"]
        .round(4)
    )

    print(
        display_metrics.to_string(
            index=False
        )
    )

    print(
        "\n=== HOLDOUT ELECTION RESULTS ==="
    )

    print(
        election_results.to_string(
            index=False
        )
    )

    print(
        "\n=== HOLDOUT COUNTRY ERRORS ==="
    )

    print(
        country_errors.round(4).to_string(
            index=False
        )
    )

    print(
        "\nFinal holdout evaluation completed "
        "and locked."
    )

    print("\nSaved:")
    print(f"  {METRICS_OUTPUT}")
    print(f"  {PREDICTIONS_OUTPUT}")
    print(f"  {ELECTION_OUTPUT}")
    print(f"  {COUNTRY_OUTPUT}")
    print(f"  {DECISION_OUTPUT}")
    print(f"  {LOCK_PATH}")


if __name__ == "__main__":
    main()
