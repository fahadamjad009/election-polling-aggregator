"""
Analyses development-set out-of-fold baseline errors.

This script uses only previously generated development OOF predictions.
It does not load or inspect the chronological holdout dataset.
"""

import os
import pandas as pd


PREDICTIONS_PATH = (
    "data/model/baselines/development_oof_predictions.csv"
)

OUTPUT_DIR = "data/model/baselines"
COUNTRY_OUTPUT = (
    f"{OUTPUT_DIR}/development_error_by_country.csv"
)
ELECTION_OUTPUT = (
    f"{OUTPUT_DIR}/development_error_by_election.csv"
)
PARTY_OUTPUT = (
    f"{OUTPUT_DIR}/development_party_error_detail.csv"
)
UPSET_OUTPUT = (
    f"{OUTPUT_DIR}/development_wrong_winner_analysis.csv"
)


def load_predictions():
    if not os.path.exists(PREDICTIONS_PATH):
        raise FileNotFoundError(
            f"Missing predictions file: {PREDICTIONS_PATH}"
        )

    df = pd.read_csv(PREDICTIONS_PATH)

    numeric_columns = [
        "election_year",
        "actual_pct",
        "is_winner",
        "final_rolling_avg",
        "baseline_vote_prediction",
        "ridge_vote_prediction",
        "logistic_win_probability",
        "polling_baseline_predicted_winner",
        "ridge_regression_predicted_winner",
        "logistic_regression_predicted_winner",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    return df


def add_error_columns(df):
    df = df.copy()

    df["baseline_error"] = (
        df["baseline_vote_prediction"]
        - df["actual_pct"]
    )

    df["baseline_abs_error"] = (
        df["baseline_error"].abs()
    )

    df["ridge_error"] = (
        df["ridge_vote_prediction"]
        - df["actual_pct"]
    )

    df["ridge_abs_error"] = (
        df["ridge_error"].abs()
    )

    return df


def build_country_summary(df):
    return (
        df.groupby("country")
        .agg(
            rows=("party", "size"),
            elections=("election_year", "nunique"),
            baseline_mae=("baseline_abs_error", "mean"),
            baseline_mean_error=("baseline_error", "mean"),
            ridge_mae=("ridge_abs_error", "mean"),
            ridge_mean_error=("ridge_error", "mean"),
        )
        .reset_index()
        .sort_values("baseline_mae")
    )


def build_election_summary(df):
    rows = []

    for keys, group in df.groupby(
        ["country", "election_year"]
    ):
        country, election_year = keys

        actual_winner_row = group.loc[
            group["is_winner"] == 1
        ].iloc[0]

        baseline_winner_row = group.loc[
            group[
                "polling_baseline_predicted_winner"
            ] == 1
        ].iloc[0]

        actual_sorted = group.sort_values(
            "actual_pct",
            ascending=False,
        )

        polling_sorted = group.sort_values(
            "baseline_vote_prediction",
            ascending=False,
        )

        actual_margin = (
            actual_sorted.iloc[0]["actual_pct"]
            - actual_sorted.iloc[1]["actual_pct"]
        )

        polling_margin = (
            polling_sorted.iloc[0][
                "baseline_vote_prediction"
            ]
            - polling_sorted.iloc[1][
                "baseline_vote_prediction"
            ]
        )

        rows.append({
            "country": country,
            "election_year": int(election_year),
            "party_rows": len(group),
            "actual_winner": actual_winner_row["party"],
            "polling_winner": baseline_winner_row["party"],
            "winner_correct": int(
                actual_winner_row["party"]
                == baseline_winner_row["party"]
            ),
            "actual_winner_pct": (
                actual_winner_row["actual_pct"]
            ),
            "actual_winner_polling_average": (
                actual_winner_row[
                    "baseline_vote_prediction"
                ]
            ),
            "actual_winner_poll_error": (
                actual_winner_row["baseline_error"]
            ),
            "actual_margin": actual_margin,
            "polling_margin": polling_margin,
            "election_baseline_mae": (
                group["baseline_abs_error"].mean()
            ),
            "election_ridge_mae": (
                group["ridge_abs_error"].mean()
            ),
        })

    return pd.DataFrame(rows).sort_values(
        ["winner_correct", "election_baseline_mae"],
        ascending=[True, False],
    )


def build_wrong_winner_analysis(df):
    rows = []

    for keys, group in df.groupby(
        ["country", "election_year"]
    ):
        actual_winner = group.loc[
            group["is_winner"] == 1
        ].iloc[0]

        polling_winner = group.loc[
            group[
                "polling_baseline_predicted_winner"
            ] == 1
        ].iloc[0]

        if actual_winner["party"] == polling_winner["party"]:
            continue

        rows.append({
            "country": keys[0],
            "election_year": int(keys[1]),
            "actual_winner": actual_winner["party"],
            "actual_winner_actual_pct": (
                actual_winner["actual_pct"]
            ),
            "actual_winner_polling_pct": (
                actual_winner[
                    "baseline_vote_prediction"
                ]
            ),
            "actual_winner_poll_error": (
                actual_winner["baseline_error"]
            ),
            "polling_winner": polling_winner["party"],
            "polling_winner_actual_pct": (
                polling_winner["actual_pct"]
            ),
            "polling_winner_polling_pct": (
                polling_winner[
                    "baseline_vote_prediction"
                ]
            ),
            "polling_winner_poll_error": (
                polling_winner["baseline_error"]
            ),
            "polling_lead_over_actual_winner": (
                polling_winner[
                    "baseline_vote_prediction"
                ]
                - actual_winner[
                    "baseline_vote_prediction"
                ]
            ),
            "actual_lead_over_polling_winner": (
                actual_winner["actual_pct"]
                - polling_winner["actual_pct"]
            ),
        })

    return pd.DataFrame(rows).sort_values(
        ["country", "election_year"]
    )


def main():
    print(
        "Loading development OOF predictions only..."
    )

    predictions = add_error_columns(
        load_predictions()
    )

    country_summary = build_country_summary(
        predictions
    )

    election_summary = build_election_summary(
        predictions
    )

    party_detail = predictions[
        [
            "country",
            "election_year",
            "party",
            "actual_pct",
            "is_winner",
            "baseline_vote_prediction",
            "baseline_error",
            "baseline_abs_error",
            "ridge_vote_prediction",
            "ridge_error",
            "ridge_abs_error",
            "logistic_win_probability",
        ]
    ].sort_values(
        "baseline_abs_error",
        ascending=False,
    )

    wrong_winners = build_wrong_winner_analysis(
        predictions
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    country_summary.to_csv(
        COUNTRY_OUTPUT,
        index=False,
    )

    election_summary.to_csv(
        ELECTION_OUTPUT,
        index=False,
    )

    party_detail.to_csv(
        PARTY_OUTPUT,
        index=False,
    )

    wrong_winners.to_csv(
        UPSET_OUTPUT,
        index=False,
    )

    print("\n=== BASELINE ERROR BY COUNTRY ===")
    print(
        country_summary.round(4).to_string(
            index=False
        )
    )

    print("\n=== ELECTION ERROR SUMMARY ===")
    print(
        election_summary.round(4).to_string(
            index=False
        )
    )

    print("\n=== WRONG WINNER CASES ===")
    print(
        wrong_winners.round(4).to_string(
            index=False
        )
        if len(wrong_winners)
        else "None"
    )

    print(
        "\n=== 12 LARGEST PARTY-LEVEL "
        "BASELINE ERRORS ==="
    )

    print(
        party_detail.head(12)
        .round(4)
        .to_string(index=False)
    )

    print(
        "\nHoldout data was not loaded or analysed."
    )

    print("\nSaved:")
    print(f"  {COUNTRY_OUTPUT}")
    print(f"  {ELECTION_OUTPUT}")
    print(f"  {PARTY_OUTPUT}")
    print(f"  {UPSET_OUTPUT}")


if __name__ == "__main__":
    main()
