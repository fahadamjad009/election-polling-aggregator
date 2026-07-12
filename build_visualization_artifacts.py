from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent
MODEL_DIR = ROOT_DIR / "data" / "model"
BASELINE_DIR = MODEL_DIR / "baselines"
HOLDOUT_DIR = MODEL_DIR / "final_holdout"
PRESENTATION_DIR = ROOT_DIR / "data" / "presentation"

COUNTRY_METADATA = {
    "australia": {
        "country_label": "Australia",
        "iso_alpha": "AUS",
    },
    "canada": {
        "country_label": "Canada",
        "iso_alpha": "CAN",
    },
    "uk": {
        "country_label": "United Kingdom",
        "iso_alpha": "GBR",
    },
    "us": {
        "country_label": "United States",
        "iso_alpha": "USA",
    },
}


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required source artifact not found: {path}"
        )

    return pd.read_csv(path)


def add_country_metadata(dataframe):
    result = dataframe.copy()

    unknown_countries = sorted(
        set(result["country"].dropna().astype(str))
        - set(COUNTRY_METADATA)
    )

    if unknown_countries:
        raise ValueError(
            "Missing country metadata for: "
            + ", ".join(unknown_countries)
        )

    result["country_label"] = result["country"].map(
        lambda value: COUNTRY_METADATA[value]["country_label"]
    )

    result["iso_alpha"] = result["country"].map(
        lambda value: COUNTRY_METADATA[value]["iso_alpha"]
    )

    return result


def build_election_performance():
    development_elections = read_csv(
        BASELINE_DIR / "development_error_by_election.csv"
    )

    development = development_elections[
        [
            "country",
            "election_year",
            "winner_correct",
            "actual_winner",
            "polling_winner",
            "election_baseline_mae",
        ]
    ].copy()

    development = development.rename(
        columns={
            "polling_winner": "predicted_winner",
            "election_baseline_mae": "election_mae",
        }
    )

    development["split"] = "Development"

    holdout_predictions = read_csv(
        HOLDOUT_DIR / "final_holdout_predictions.csv"
    )

    holdout_elections = read_csv(
        HOLDOUT_DIR / "final_holdout_election_results.csv"
    )

    holdout_errors = (
        holdout_predictions.groupby(
            [
                "country",
                "election_year",
            ],
            as_index=False,
        )
        .agg(
            election_mae=("absolute_error", "mean"),
        )
    )

    holdout = holdout_errors.merge(
        holdout_elections[
            [
                "country",
                "election_year",
                "winner_correct",
                "actual_winner",
                "predicted_winner",
            ]
        ],
        on=[
            "country",
            "election_year",
        ],
        how="inner",
        validate="one_to_one",
    )

    holdout["split"] = "Holdout"

    elections = pd.concat(
        [
            development,
            holdout,
        ],
        ignore_index=True,
    )

    elections["election_year"] = pd.to_numeric(
        elections["election_year"],
        errors="raise",
    ).astype(int)

    elections["election_mae"] = pd.to_numeric(
        elections["election_mae"],
        errors="raise",
    )

    elections["winner_correct"] = pd.to_numeric(
        elections["winner_correct"],
        errors="raise",
    ).astype(int)

    elections = add_country_metadata(elections)

    elections["result_status"] = elections[
        "winner_correct"
    ].map(
        {
            1: "Correct winner",
            0: "Winner miss",
        }
    )

    elections["annotation"] = elections.apply(
        lambda row: (
            f"{row['election_mae']:.2f} "
            + (
                "OK"
                if row["winner_correct"] == 1
                else "MISS"
            )
        ),
        axis=1,
    )

    elections = elections[
        [
            "country",
            "country_label",
            "iso_alpha",
            "election_year",
            "split",
            "election_mae",
            "winner_correct",
            "result_status",
            "actual_winner",
            "predicted_winner",
            "annotation",
        ]
    ].sort_values(
        [
            "country_label",
            "election_year",
        ]
    )

    if len(elections) != 22:
        raise ValueError(
            f"Expected 22 elections, found {len(elections)}."
        )

    if elections[
        [
            "country",
            "election_year",
        ]
    ].duplicated().any():
        raise ValueError(
            "Duplicate country-election rows detected."
        )

    if int((elections["winner_correct"] == 0).sum()) != 2:
        raise ValueError(
            "Expected exactly two historical winner misses."
        )

    return elections.reset_index(drop=True)


def build_country_summary(elections):
    development_errors = read_csv(
        BASELINE_DIR / "development_party_error_detail.csv"
    )[
        [
            "country",
            "election_year",
            "party",
            "baseline_abs_error",
        ]
    ].rename(
        columns={
            "baseline_abs_error": "absolute_error",
        }
    )

    development_errors["split"] = "Development"

    holdout_errors = read_csv(
        HOLDOUT_DIR / "final_holdout_predictions.csv"
    )[
        [
            "country",
            "election_year",
            "party",
            "absolute_error",
        ]
    ].copy()

    holdout_errors["split"] = "Holdout"

    party_errors = pd.concat(
        [
            development_errors,
            holdout_errors,
        ],
        ignore_index=True,
    )

    party_errors["absolute_error"] = pd.to_numeric(
        party_errors["absolute_error"],
        errors="raise",
    )

    error_summary = (
        party_errors.groupby(
            "country",
            as_index=False,
        )
        .agg(
            evaluated_party_rows=("party", "size"),
            mean_absolute_error=("absolute_error", "mean"),
            median_absolute_error=("absolute_error", "median"),
            maximum_absolute_error=("absolute_error", "max"),
        )
    )

    model_dataset = read_csv(
        MODEL_DIR / "model_dataset.csv"
    )

    poll_volume = (
        model_dataset.groupby(
            "country",
            as_index=False,
        )
        .agg(
            poll_observations=("n_poll_observations", "sum"),
            campaign_party_rows=("party", "size"),
        )
    )

    election_summary = (
        elections.groupby(
            "country",
            as_index=False,
        )
        .agg(
            elections=("election_year", "size"),
            correct_winners=("winner_correct", "sum"),
        )
    )

    election_summary["wrong_winners"] = (
        election_summary["elections"]
        - election_summary["correct_winners"]
    )

    election_summary["winner_accuracy"] = (
        election_summary["correct_winners"]
        / election_summary["elections"]
    )

    worst_indices = elections.groupby(
        "country"
    )["election_mae"].idxmax()

    worst_elections = elections.loc[
        worst_indices,
        [
            "country",
            "country_label",
            "election_year",
            "election_mae",
            "result_status",
        ],
    ].copy()

    worst_elections["worst_election"] = (
        worst_elections["country_label"]
        + " "
        + worst_elections["election_year"].astype(str)
    )

    worst_elections = worst_elections.rename(
        columns={
            "election_mae": "worst_election_mae",
            "result_status": "worst_election_result_status",
        }
    )[
        [
            "country",
            "worst_election",
            "worst_election_mae",
            "worst_election_result_status",
        ]
    ]

    summary = (
        error_summary.merge(
            poll_volume,
            on="country",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            election_summary,
            on="country",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            worst_elections,
            on="country",
            how="inner",
            validate="one_to_one",
        )
    )

    summary = add_country_metadata(summary)

    summary["winner_accuracy_pct"] = (
        summary["winner_accuracy"] * 100.0
    )

    summary = summary[
        [
            "country",
            "country_label",
            "iso_alpha",
            "poll_observations",
            "campaign_party_rows",
            "evaluated_party_rows",
            "elections",
            "correct_winners",
            "wrong_winners",
            "winner_accuracy",
            "winner_accuracy_pct",
            "mean_absolute_error",
            "median_absolute_error",
            "maximum_absolute_error",
            "worst_election",
            "worst_election_mae",
            "worst_election_result_status",
        ]
    ].sort_values(
        "country_label"
    )

    if len(summary) != 4:
        raise ValueError(
            f"Expected four country rows, found {len(summary)}."
        )

    if int(summary["elections"].sum()) != 22:
        raise ValueError(
            "Country election totals do not sum to 22."
        )

    if int(summary["wrong_winners"].sum()) != 2:
        raise ValueError(
            "Country winner misses do not sum to two."
        )

    if (summary["poll_observations"] <= 0).any():
        raise ValueError(
            "All mapped countries must have polling observations."
        )

    return summary.reset_index(drop=True)


def main():
    PRESENTATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    elections = build_election_performance()
    countries = build_country_summary(elections)

    election_output = (
        PRESENTATION_DIR
        / "election_error_heatmap.csv"
    )

    country_output = (
        PRESENTATION_DIR
        / "country_geographic_performance.csv"
    )

    elections.to_csv(
        election_output,
        index=False,
        float_format="%.6f",
    )

    countries.to_csv(
        country_output,
        index=False,
        float_format="%.6f",
    )

    print("Presentation artifacts built successfully.")
    print(f"Country map rows: {len(countries)}")
    print(f"Election heatmap rows: {len(elections)}")
    print(
        "Historical winner misses: "
        f"{int((elections['winner_correct'] == 0).sum())}"
    )
    print(f"Created: {country_output}")
    print(f"Created: {election_output}")


if __name__ == "__main__":
    main()