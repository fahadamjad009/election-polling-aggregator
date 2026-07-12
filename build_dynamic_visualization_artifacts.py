from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
FEATURE_DIR = DATA_DIR / "features"
MODEL_DIR = DATA_DIR / "model"
BASELINE_DIR = MODEL_DIR / "baselines"
HOLDOUT_DIR = MODEL_DIR / "final_holdout"
PRESENTATION_DIR = DATA_DIR / "presentation"

COUNTRY_LABELS = {
    "australia": "Australia",
    "canada": "Canada",
    "uk": "United Kingdom",
    "us": "United States",
}


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required artifact not found: {path}"
        )

    return pd.read_csv(path)


def add_country_labels(dataframe):
    result = dataframe.copy()

    unknown = sorted(
        set(
            result["country"]
            .dropna()
            .astype(str)
        )
        - set(COUNTRY_LABELS)
    )

    if unknown:
        raise ValueError(
            "Missing display labels for countries: "
            + ", ".join(unknown)
        )

    result["country_label"] = (
        result["country"]
        .map(COUNTRY_LABELS)
    )

    result["election_label"] = (
        result["country_label"]
        + " "
        + result["election_year"]
        .astype(int)
        .astype(str)
    )

    return result


def build_polling_trajectory():
    rolling = read_csv(
        FEATURE_DIR
        / "rolling_momentum_features.csv"
    )

    model_dataset = read_csv(
        MODEL_DIR / "model_dataset.csv"
    )

    model_audit = read_csv(
        MODEL_DIR / "model_dataset_audit.csv"
    )

    required_rolling_columns = {
        "country",
        "election_year",
        "party",
        "poll_date",
        "pct",
        "rolling_avg",
        "momentum_1st_diff",
        "momentum_2nd_diff",
    }

    missing_rolling_columns = (
        required_rolling_columns
        - set(rolling.columns)
    )

    if missing_rolling_columns:
        raise ValueError(
            "Rolling feature columns missing: "
            + ", ".join(
                sorted(missing_rolling_columns)
            )
        )

    rolling["poll_date"] = pd.to_datetime(
        rolling["poll_date"],
        errors="raise",
    )

    election_splits = (
        model_audit[
            [
                "country",
                "election_year",
                "dataset_split",
            ]
        ]
        .drop_duplicates()
    )

    if election_splits[
        [
            "country",
            "election_year",
        ]
    ].duplicated().any():
        raise ValueError(
            "Election split mapping is not unique."
        )

    model_targets = model_dataset[
        [
            "country",
            "election_year",
            "party",
            "actual_pct",
            "is_winner",
            "n_poll_observations",
            "poll_std",
        ]
    ].copy()

    if model_targets[
        [
            "country",
            "election_year",
            "party",
        ]
    ].duplicated().any():
        raise ValueError(
            "Model targets contain duplicate party-election rows."
        )

    trajectory = rolling.merge(
        election_splits,
        on=[
            "country",
            "election_year",
        ],
        how="left",
        validate="many_to_one",
    )

    trajectory = trajectory.merge(
        model_targets,
        on=[
            "country",
            "election_year",
            "party",
        ],
        how="left",
        validate="many_to_one",
    )

    if trajectory["dataset_split"].isna().any():
        raise ValueError(
            "Some polling trajectories could not be mapped "
            "to a development or holdout election."
        )

    trajectory["model_included"] = (
        trajectory["actual_pct"].notna()
    )

    trajectory["is_winner"] = (
        trajectory["is_winner"]
        .fillna(0)
        .astype(int)
    )

    numeric_columns = [
        "pct",
        "rolling_avg",
        "momentum_1st_diff",
        "momentum_2nd_diff",
    ]

    for column in numeric_columns:
        trajectory[column] = pd.to_numeric(
            trajectory[column],
            errors="raise",
        )

    trajectory = add_country_labels(
        trajectory
    )

    trajectory["poll_date"] = (
        trajectory["poll_date"]
        .dt.strftime("%Y-%m-%d")
    )

    trajectory = trajectory[
        [
            "country",
            "country_label",
            "election_year",
            "election_label",
            "dataset_split",
            "party",
            "poll_date",
            "pct",
            "rolling_avg",
            "momentum_1st_diff",
            "momentum_2nd_diff",
            "model_included",
            "actual_pct",
            "is_winner",
            "n_poll_observations",
            "poll_std",
        ]
    ].sort_values(
        [
            "country_label",
            "election_year",
            "party",
            "poll_date",
        ]
    )

    if len(trajectory) != 16125:
        raise ValueError(
            "Expected 16,125 rolling trajectory rows; "
            f"found {len(trajectory):,}."
        )

    election_count = trajectory[
        [
            "country",
            "election_year",
        ]
    ].drop_duplicates().shape[0]

    if election_count != 22:
        raise ValueError(
            "Expected trajectories for 22 elections; "
            f"found {election_count}."
        )

    if trajectory["country"].nunique() != 4:
        raise ValueError(
            "Expected four countries in polling trajectories."
        )

    return trajectory.reset_index(drop=True)


def build_party_error_distribution():
    development = read_csv(
        BASELINE_DIR
        / "development_party_error_detail.csv"
    )[
        [
            "country",
            "election_year",
            "party",
            "actual_pct",
            "baseline_vote_prediction",
            "baseline_error",
            "baseline_abs_error",
        ]
    ].copy()

    development = development.rename(
        columns={
            "baseline_vote_prediction": "predicted_pct",
            "baseline_error": "signed_error",
            "baseline_abs_error": "absolute_error",
        }
    )

    development["evaluation_split"] = "Development"

    holdout = read_csv(
        HOLDOUT_DIR
        / "final_holdout_predictions.csv"
    )[
        [
            "country",
            "election_year",
            "party",
            "actual_pct",
            "selected_vote_prediction",
            "vote_share_error",
            "absolute_error",
        ]
    ].copy()

    holdout = holdout.rename(
        columns={
            "selected_vote_prediction": "predicted_pct",
            "vote_share_error": "signed_error",
        }
    )

    holdout["evaluation_split"] = "Holdout"

    errors = pd.concat(
        [
            development,
            holdout,
        ],
        ignore_index=True,
    )

    model_dataset = read_csv(
        MODEL_DIR / "model_dataset.csv"
    )[
        [
            "country",
            "election_year",
            "party",
            "dataset_split",
            "is_winner",
            "n_poll_observations",
            "poll_std",
            "campaign_span_days",
            "recent_30d_observations",
        ]
    ].copy()

    errors = errors.merge(
        model_dataset,
        on=[
            "country",
            "election_year",
            "party",
        ],
        how="inner",
        validate="one_to_one",
    )

    numeric_columns = [
        "actual_pct",
        "predicted_pct",
        "signed_error",
        "absolute_error",
        "n_poll_observations",
        "poll_std",
        "campaign_span_days",
        "recent_30d_observations",
    ]

    for column in numeric_columns:
        errors[column] = pd.to_numeric(
            errors[column],
            errors="raise",
        )

    errors["is_winner"] = (
        errors["is_winner"]
        .astype(int)
    )

    errors["party_role"] = (
        errors["is_winner"]
        .map(
            {
                1: "Election winner",
                0: "Other modelled party",
            }
        )
    )

    errors["bubble_size"] = (
        errors["poll_std"]
        .fillna(0)
        .clip(lower=0)
        + 0.25
    )

    errors = add_country_labels(
        errors
    )

    errors = errors[
        [
            "country",
            "country_label",
            "election_year",
            "election_label",
            "party",
            "party_role",
            "evaluation_split",
            "dataset_split",
            "actual_pct",
            "predicted_pct",
            "signed_error",
            "absolute_error",
            "n_poll_observations",
            "poll_std",
            "bubble_size",
            "campaign_span_days",
            "recent_30d_observations",
        ]
    ].sort_values(
        [
            "country_label",
            "election_year",
            "party",
        ]
    )

    if len(errors) != 68:
        raise ValueError(
            "Expected 68 party-election error rows; "
            f"found {len(errors)}."
        )

    if errors[
        [
            "country",
            "election_year",
            "party",
        ]
    ].duplicated().any():
        raise ValueError(
            "Duplicate party-election error rows detected."
        )

    split_counts = (
        errors["evaluation_split"]
        .value_counts()
        .to_dict()
    )

    if split_counts != {
        "Development": 43,
        "Holdout": 25,
    }:
        raise ValueError(
            "Unexpected development/holdout error counts: "
            f"{split_counts}"
        )

    error_difference = (
        errors["signed_error"].abs()
        - errors["absolute_error"]
    ).abs().max()

    if float(error_difference) > 1e-8:
        raise ValueError(
            "Signed and absolute error fields are inconsistent."
        )

    return errors.reset_index(drop=True)


def main():
    PRESENTATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    trajectory = build_polling_trajectory()
    errors = build_party_error_distribution()

    trajectory_path = (
        PRESENTATION_DIR
        / "polling_trajectory.csv"
    )

    error_path = (
        PRESENTATION_DIR
        / "party_error_distribution.csv"
    )

    trajectory.to_csv(
        trajectory_path,
        index=False,
        float_format="%.6f",
    )

    errors.to_csv(
        error_path,
        index=False,
        float_format="%.6f",
    )

    included_trajectory_rows = int(
        trajectory["model_included"].sum()
    )

    print("Dynamic visualisation artifacts: PASS")
    print(
        "Polling trajectory rows: "
        f"{len(trajectory):,}"
    )
    print(
        "Trajectory election coverage: "
        f"{trajectory[['country', 'election_year']].drop_duplicates().shape[0]}"
    )
    print(
        "Model-included trajectory rows: "
        f"{included_trajectory_rows:,}"
    )
    print(
        "Party error rows: "
        f"{len(errors)}"
    )
    print(
        "Development error rows: "
        f"{int((errors['evaluation_split'] == 'Development').sum())}"
    )
    print(
        "Holdout error rows: "
        f"{int((errors['evaluation_split'] == 'Holdout').sum())}"
    )
    print(f"Created: {trajectory_path}")
    print(f"Created: {error_path}")


if __name__ == "__main__":
    main()