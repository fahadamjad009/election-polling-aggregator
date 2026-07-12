"""
Builds the party-level modelling dataset.

Each output row represents one party in one election. Features are derived
only from polling observations dated on or before the verified election
date. Actual vote share and winner status are joined afterward as targets.

The chronological development/holdout split is preserved at election level.
No model fitting or holdout evaluation occurs in this script.
"""

import os
import numpy as np
import pandas as pd


FEATURES_PATH = "data/features/rolling_momentum_features.csv"
ACTUALS_PATH = "data/results_clean/national_actual_results.csv"
DATES_PATH = "data/reference/election_dates.csv"
DEV_PATH = "data/splits/development_elections.csv"
HOLDOUT_PATH = "data/splits/holdout_elections.csv"

OUTPUT_DIR = "data/model"
FULL_OUTPUT = f"{OUTPUT_DIR}/model_dataset.csv"
DEV_OUTPUT = f"{OUTPUT_DIR}/development_model_dataset.csv"
HOLDOUT_OUTPUT = f"{OUTPUT_DIR}/holdout_model_dataset.csv"
AUDIT_OUTPUT = f"{OUTPUT_DIR}/model_dataset_audit.csv"
EXCLUSIONS_OUTPUT = f"{OUTPUT_DIR}/excluded_polling_parties.csv"


def normalise_year(df):
    df = df.copy()
    df["election_year"] = pd.to_numeric(
        df["election_year"],
        errors="coerce",
    ).astype("Int64")

    return df.dropna(subset=["election_year"])


def load_inputs():
    required_paths = [
        FEATURES_PATH,
        ACTUALS_PATH,
        DATES_PATH,
        DEV_PATH,
        HOLDOUT_PATH,
    ]

    missing = [
        path
        for path in required_paths
        if not os.path.exists(path)
    ]

    if missing:
        raise FileNotFoundError(
            "Required files are missing:\n"
            + "\n".join(missing)
        )

    features = normalise_year(
        pd.read_csv(FEATURES_PATH)
    )
    actuals = normalise_year(
        pd.read_csv(ACTUALS_PATH)
    )
    dates = normalise_year(
        pd.read_csv(DATES_PATH)
    )
    development = normalise_year(
        pd.read_csv(DEV_PATH)
    )
    holdout = normalise_year(
        pd.read_csv(HOLDOUT_PATH)
    )

    features["poll_date"] = pd.to_datetime(
        features["poll_date"],
        errors="coerce",
    )

    dates["election_date"] = pd.to_datetime(
        dates["election_date"],
        errors="coerce",
    )

    return features, actuals, dates, development, holdout


def build_split_table(development, holdout):
    development = development.copy()
    holdout = holdout.copy()

    development["dataset_split"] = "development"
    holdout["dataset_split"] = "holdout"

    splits = pd.concat(
        [development, holdout],
        ignore_index=True,
    )

    duplicated = splits.duplicated(
        ["country", "election_year"],
        keep=False,
    )

    if duplicated.any():
        duplicate_rows = splits.loc[
            duplicated,
            ["country", "election_year", "dataset_split"],
        ]

        raise ValueError(
            "An election appears in more than one split:\n"
            + duplicate_rows.to_string(index=False)
        )

    return splits


def map_polling_party(country, party):
    """
    Maps polling labels to the canonical labels in the actual-results file.

    Australia uses only two-party-preferred series because national primary
    vote targets have not been collected in this project.

    UK polling uses LD while the historical actual-results file uses LIB.
    All other supported labels already match exactly.
    """
    if country == "australia":
        if party in {"ALP (2PP)", "L/NP (2PP)"}:
            return party
        return None

    if country == "uk" and party == "LD":
        return "LIB"

    return party


def apply_election_cutoff(features, dates, splits):
    dated = features.merge(
        dates[
            [
                "country",
                "election_year",
                "election_date",
            ]
        ],
        on=["country", "election_year"],
        how="inner",
        validate="many_to_one",
    )

    dated = dated.merge(
        splits[
            [
                "country",
                "election_year",
                "dataset_split",
            ]
        ],
        on=["country", "election_year"],
        how="inner",
        validate="many_to_one",
    )

    missing_dates = dated[
        dated["poll_date"].isna()
        | dated["election_date"].isna()
    ]

    if len(missing_dates) > 0:
        raise ValueError(
            f"{len(missing_dates)} rows have a missing poll or election date."
        )

    dated["is_post_election"] = (
        dated["poll_date"] > dated["election_date"]
    )

    pre_election = dated[
        ~dated["is_post_election"]
    ].copy()

    pre_election["model_party"] = pre_election.apply(
        lambda row: map_polling_party(
            row["country"],
            row["party"],
        ),
        axis=1,
    )

    return dated, pre_election


def build_party_features(pre_election):
    usable = pre_election[
        pre_election["model_party"].notna()
    ].copy()

    usable = usable.sort_values(
        [
            "country",
            "election_year",
            "model_party",
            "poll_date",
        ]
    )

    group_cols = [
        "country",
        "election_year",
        "model_party",
        "election_date",
        "dataset_split",
    ]

    rows = []

    for keys, group in usable.groupby(
        group_cols,
        dropna=False,
    ):
        (
            country,
            election_year,
            model_party,
            election_date,
            dataset_split,
        ) = keys

        group = group.sort_values("poll_date")
        final_row = group.iloc[-1]

        momentum_1 = pd.to_numeric(
            group["momentum_1st_diff"],
            errors="coerce",
        )

        momentum_2 = pd.to_numeric(
            group["momentum_2nd_diff"],
            errors="coerce",
        )

        pct = pd.to_numeric(
            group["pct"],
            errors="coerce",
        )

        rolling_avg = pd.to_numeric(
            group["rolling_avg"],
            errors="coerce",
        )

        window_start = (
            election_date
            - pd.Timedelta(days=30)
        )

        recent_30d = group[
            group["poll_date"].between(
                window_start,
                election_date,
            )
        ].copy()

        recent_30d["pct_numeric"] = pd.to_numeric(
            recent_30d["pct"],
            errors="coerce",
        )

        recent_30d = recent_30d.dropna(
            subset=[
                "poll_date",
                "pct_numeric",
            ]
        )

        if recent_30d.empty:
            raise ValueError(
                "No observations exist in the final 30 days for "
                f"{country} {election_year} {model_party}."
            )

        recent_30d_mean = float(
            recent_30d["pct_numeric"].mean()
        )

        recent_30d_std = float(
            recent_30d["pct_numeric"].std(
                ddof=0
            )
        )

        recent_30d_observations = int(
            len(recent_30d)
        )

        if (
            recent_30d["poll_date"].nunique() >= 2
            and recent_30d_observations >= 2
        ):
            elapsed_days = (
                recent_30d["poll_date"]
                - recent_30d["poll_date"].min()
            ).dt.days.astype(float)

            recent_30d_trend_per_day = float(
                np.polyfit(
                    elapsed_days,
                    recent_30d["pct_numeric"],
                    1,
                )[0]
            )
        else:
            recent_30d_trend_per_day = 0.0

        rows.append({
            "country": country,
            "election_year": int(election_year),
            "party": model_party,
            "dataset_split": dataset_split,
            "election_date": election_date,
            "last_poll_date": final_row["poll_date"],
            "days_before_election": (
                election_date - final_row["poll_date"]
            ).days,
            "final_poll_pct": float(final_row["pct"]),
            "final_rolling_avg": float(
                final_row["rolling_avg"]
            ),
            "final_momentum_1st": (
                float(final_row["momentum_1st_diff"])
                if pd.notna(
                    final_row["momentum_1st_diff"]
                )
                else 0.0
            ),
            "final_momentum_2nd": (
                float(final_row["momentum_2nd_diff"])
                if pd.notna(
                    final_row["momentum_2nd_diff"]
                )
                else 0.0
            ),
            "recent_30d_mean": recent_30d_mean,
            "recent_30d_std": recent_30d_std,
            "recent_30d_observations": (
                recent_30d_observations
            ),
            "recent_30d_trend_per_day": (
                recent_30d_trend_per_day
            ),
            "final_vs_recent_30d_mean": float(
                final_row["rolling_avg"]
                - recent_30d_mean
            ),
            "mean_poll_pct": float(pct.mean()),
            "poll_std": float(pct.std(ddof=0)),
            "min_poll_pct": float(pct.min()),
            "max_poll_pct": float(pct.max()),
            "mean_rolling_avg": float(
                rolling_avg.mean()
            ),
            "mean_momentum_1st": float(
                momentum_1.mean()
            ) if momentum_1.notna().any() else 0.0,
            "mean_momentum_2nd": float(
                momentum_2.mean()
            ) if momentum_2.notna().any() else 0.0,
            "n_poll_observations": int(len(group)),
            "campaign_span_days": int(
                (
                    group["poll_date"].max()
                    - group["poll_date"].min()
                ).days
            ),
        })

    return pd.DataFrame(rows)


def prepare_actual_targets(actuals, splits):
    actuals = actuals.merge(
        splits[
            [
                "country",
                "election_year",
                "dataset_split",
            ]
        ],
        on=["country", "election_year"],
        how="inner",
        validate="many_to_one",
    )

    actuals["actual_pct"] = pd.to_numeric(
        actuals["actual_pct"],
        errors="coerce",
    )

    actuals = actuals.dropna(
        subset=["actual_pct"]
    )

    winner_values = (
        actuals.groupby(
            ["country", "election_year"]
        )["actual_pct"]
        .transform("max")
    )

    actuals["is_winner"] = (
        actuals["actual_pct"] == winner_values
    ).astype(int)

    winner_counts = (
        actuals.groupby(
            ["country", "election_year"]
        )["is_winner"]
        .sum()
    )

    invalid_winners = winner_counts[
        winner_counts != 1
    ]

    if len(invalid_winners) > 0:
        raise ValueError(
            "Expected exactly one winner per election:\n"
            + invalid_winners.to_string()
        )

    return actuals[
        [
            "country",
            "election_year",
            "party",
            "actual_pct",
            "is_winner",
        ]
    ]


def build_exclusion_audit(pre_election, actual_targets):
    available_targets = set(
        zip(
            actual_targets["country"],
            actual_targets["election_year"],
            actual_targets["party"],
        )
    )

    exclusions = (
        pre_election[
            [
                "country",
                "election_year",
                "party",
                "model_party",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    def exclusion_reason(row):
        if pd.isna(row["model_party"]):
            return (
                "excluded by documented modelling scope"
            )

        key = (
            row["country"],
            row["election_year"],
            row["model_party"],
        )

        if key not in available_targets:
            return "no matching actual-result target"

        return "included"

    exclusions["status"] = exclusions.apply(
        exclusion_reason,
        axis=1,
    )

    return exclusions[
        exclusions["status"] != "included"
    ].sort_values(
        ["country", "election_year", "party"]
    )


def validate_dataset(dataset, splits):
    if dataset.empty:
        raise ValueError(
            "The modelling dataset is empty."
        )

    duplicated = dataset.duplicated(
        ["country", "election_year", "party"],
        keep=False,
    )

    if duplicated.any():
        raise ValueError(
            "Duplicate party-election rows were created:\n"
            + dataset.loc[
                duplicated,
                ["country", "election_year", "party"],
            ].to_string(index=False)
        )

    if (
        dataset["last_poll_date"]
        > dataset["election_date"]
    ).any():
        raise ValueError(
            "Post-election observations remain in the modelling dataset."
        )

    covered_elections = dataset[
        ["country", "election_year"]
    ].drop_duplicates()

    expected_elections = splits[
        ["country", "election_year"]
    ].drop_duplicates()

    missing_elections = expected_elections.merge(
        covered_elections,
        on=["country", "election_year"],
        how="left",
        indicator=True,
    )

    missing_elections = missing_elections[
        missing_elections["_merge"] == "left_only"
    ]

    if len(missing_elections) > 0:
        raise ValueError(
            "No model rows were created for these elections:\n"
            + missing_elections[
                ["country", "election_year"]
            ].to_string(index=False)
        )

    winner_counts = (
        dataset.groupby(
            ["country", "election_year"]
        )["is_winner"]
        .sum()
    )

    invalid_winners = winner_counts[
        winner_counts != 1
    ]

    if len(invalid_winners) > 0:
        raise ValueError(
            "The joined dataset does not contain exactly one winner "
            "for each election:\n"
            + invalid_winners.to_string()
        )


def build_audit(dated, dataset):
    post_counts = (
        dated.groupby(
            ["country", "election_year"]
        )
        .agg(
            source_feature_rows=("party", "size"),
            post_election_rows=(
                "is_post_election",
                "sum",
            ),
        )
        .reset_index()
    )

    dataset_counts = (
        dataset.groupby(
            [
                "country",
                "election_year",
                "dataset_split",
            ]
        )
        .agg(
            model_party_rows=("party", "size"),
            winner_rows=("is_winner", "sum"),
            earliest_model_poll=(
                "last_poll_date",
                "min",
            ),
            latest_model_poll=(
                "last_poll_date",
                "max",
            ),
        )
        .reset_index()
    )

    return post_counts.merge(
        dataset_counts,
        on=["country", "election_year"],
        how="left",
    )


def main():
    print("Loading feature, result, date, and split files...")

    (
        features,
        actuals,
        dates,
        development,
        holdout,
    ) = load_inputs()

    splits = build_split_table(
        development,
        holdout,
    )

    print(
        f"  {len(splits)} model elections: "
        f"{len(development)} development, "
        f"{len(holdout)} holdout"
    )

    dated, pre_election = apply_election_cutoff(
        features,
        dates,
        splits,
    )

    removed_post_election = int(
        dated["is_post_election"].sum()
    )

    print(
        f"  Removed {removed_post_election} "
        f"post-election feature rows"
    )

    party_features = build_party_features(
        pre_election
    )

    actual_targets = prepare_actual_targets(
        actuals,
        splits,
    )

    exclusions = build_exclusion_audit(
        pre_election,
        actual_targets,
    )

    dataset = party_features.merge(
        actual_targets,
        on=["country", "election_year", "party"],
        how="inner",
        validate="one_to_one",
    )

    dataset = dataset.sort_values(
        ["country", "election_year", "actual_pct"],
        ascending=[True, True, False],
    ).reset_index(drop=True)

    validate_dataset(
        dataset,
        splits,
    )

    audit = build_audit(
        dated,
        dataset,
    )

    development_dataset = dataset[
        dataset["dataset_split"] == "development"
    ].copy()

    holdout_dataset = dataset[
        dataset["dataset_split"] == "holdout"
    ].copy()

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    dataset.to_csv(
        FULL_OUTPUT,
        index=False,
    )

    development_dataset.to_csv(
        DEV_OUTPUT,
        index=False,
    )

    holdout_dataset.to_csv(
        HOLDOUT_OUTPUT,
        index=False,
    )

    audit.to_csv(
        AUDIT_OUTPUT,
        index=False,
    )

    exclusions.to_csv(
        EXCLUSIONS_OUTPUT,
        index=False,
    )

    print(
        f"\nBuilt {len(dataset)} party-election rows "
        f"across {dataset[['country', 'election_year']].drop_duplicates().shape[0]} elections"
    )

    print(
        f"  Development rows: {len(development_dataset)}"
    )

    print(
        f"  Holdout rows: {len(holdout_dataset)}"
    )

    print(
        f"  Intentional/unmatched exclusions documented: "
        f"{len(exclusions)}"
    )

    print("\nRows by country and split:")
    print(
        dataset.groupby(
            ["country", "dataset_split"]
        )
        .size()
        .rename("rows")
        .to_string()
    )

    print("\nDevelopment target summary only:")
    print(
        development_dataset[
            [
                "actual_pct",
                "is_winner",
                "final_rolling_avg",
                "poll_std",
                "n_poll_observations",
            ]
        ]
        .describe()
        .round(3)
        .to_string()
    )

    print(
        "\nHoldout targets were saved but not summarised "
        "or evaluated in this script."
    )

    print("\nSaved:")
    print(f"  {FULL_OUTPUT}")
    print(f"  {DEV_OUTPUT}")
    print(f"  {HOLDOUT_OUTPUT}")
    print(f"  {AUDIT_OUTPUT}")
    print(f"  {EXCLUSIONS_OUTPUT}")


if __name__ == "__main__":
    main()
