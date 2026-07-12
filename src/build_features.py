"""
Feature engineering, part 1: rolling poll averages and momentum.

DSA element: a fixed-size deque (double-ended queue) maintains the sliding
window explicitly -- O(1) append/evict per new poll, rather than recomputing
a window slice from scratch each time (which is what pandas.rolling() does
internally on a per-call basis without exposing the underlying structure).
This is the same technique real polling aggregators (538, RealClearPolitics)
use conceptually: a bounded buffer of the most recent N polls per party.

Momentum features use finite differences (first-order: rate of change
between consecutive averaged points; second-order: rate of change of the
rate of change, i.e. acceleration) -- a standard numerical-methods technique
for detecting trend direction and trend curvature from a discrete sequence.
"""
import pandas as pd
import glob
import os
from collections import deque
from date_parser import add_parsed_dates, MONTH_MAP


SCOPE_AUDIT_PATH = (
    "data/reference/polling_table_scope_audit.csv"
)

SCOPE_OVERRIDES_PATH = (
    "data/reference/polling_scope_overrides.csv"
)

INCLUDED_SCOPE_OUTPUT = (
    "data/features/polling_scope_included_tables.csv"
)

EXCLUDED_SCOPE_OUTPUT = (
    "data/features/polling_scope_excluded_tables.csv"
)

APPROVED_SCOPE_STATUSES = {
    "approved_marker_match",
    "manual_approved",
}

ELECTION_DATES_PATH = (
    "data/reference/election_dates.csv"
)

POST_ELECTION_AUDIT_OUTPUT = (
    "data/features/post_election_rows_excluded.csv"
)

# Approximate election month per (country, year) -- used by date_parser's
# year-rollback logic for month-only date ranges. Built from the actual
# election results data already collected (not guessed): each country's
# results file has real election dates.
def load_election_months():
    """Returns {(country, year): month_int} built from the real election
    date data already collected in this project."""
    months = {}

    # Australia: tpp_national_1949_2022.csv has real election_date column
    path = "data/australia/tpp_national_1949_2022.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            d = pd.to_datetime(row["election_date"])
            months[("australia", row["year"])] = d.month

    # UK and Canada: election months are well-known historical facts already
    # implicit in this project's own election_results files (which are
    # constituency-level with no single "election date" column to extract
    # cleanly) -- rather than guess, these are filled in only where the
    # (country, year) key is actually needed, from the election_year values
    # that already appear in the polling data itself: the poll_date closest
    # to the "is_election_result" row IS the real election date, so this
    # gets backfilled after an initial pass parses what it can without a
    # month hint (see backfill_election_months below).
    return months

def backfill_election_months(df, months):
    """After an initial date-parse pass (without month hints for
    (country,year) pairs not covered by load_election_months), use each
    election's own is_election_result rows -- which by definition state the
    real election date in full (day+month+year) -- to fill in the missing
    (country, year) -> month mapping, then re-parse so month-only ranges in
    that same cycle roll back to the correct year."""
    election_rows = df[df["is_election_result"] & df["poll_date"].notna()]
    for (country, year), group in election_rows.groupby(["country", "election_year"]):
        if (country, year) not in months:
            months[(country, year)] = group["poll_date"].iloc[0].month
    return months

def sliding_window_average(dates_and_values, window_size=5):
    """DSA: deque-based fixed-size sliding window. Given a list of
    (date, value) pairs already sorted by date, yields (date, window_avg)
    for each point, where window_avg is the mean of the current point and
    up to (window_size - 1) preceding points."""
    window = deque(maxlen=window_size)
    results = []
    for date, value in dates_and_values:
        window.append(value)
        avg = sum(window) / len(window)
        results.append((date, avg))
    return results

def finite_difference_momentum(dates_and_values):
    """First and second finite differences of a value sequence, indexed by
    date. First difference = rate of change (momentum); second difference
    = rate of change of the rate of change (acceleration -- is momentum
    itself speeding up or slowing down)."""
    values = [v for _, v in dates_and_values]
    dates = [d for d, _ in dates_and_values]
    first_diff = [None] + [values[i] - values[i - 1] for i in range(1, len(values))]
    second_diff = [None, None] + [
        first_diff[i] - first_diff[i - 1] for i in range(2, len(values))
    ]
    return list(zip(dates, first_diff, second_diff))

def build_rolling_features(df, window_size=5):
    """Applies sliding-window averaging and momentum per (country,
    election_year, party) group, sorted chronologically within each group."""
    df = df[df["poll_date"].notna() & ~df["is_election_result"]].copy()
    df = df.sort_values(["country", "election_year", "party", "poll_date"])

    all_rows = []
    for (country, year, party), group in df.groupby(["country", "election_year", "party"]):
        group = group.sort_values("poll_date")
        pairs = list(zip(group["poll_date"], group["pct"]))
        if len(pairs) == 0:
            continue

        rolling = sliding_window_average(pairs, window_size)
        momentum = finite_difference_momentum(pairs)

        for i, (date, val) in enumerate(pairs):
            all_rows.append({
                "country": country, "election_year": year, "party": party,
                "poll_date": date, "pct": val,
                "rolling_avg": rolling[i][1],
                "momentum_1st_diff": momentum[i][1],
                "momentum_2nd_diff": momentum[i][2],
            })

    return pd.DataFrame(all_rows)

def apply_national_scope_filter(df):
    """
    Retains only source tables confirmed as national polling.

    Automatic marker classifications come from
    polling_table_scope_audit.csv. Explicit reviewed decisions from
    polling_scope_overrides.csv take precedence over automatic status.

    Tables that remain unresolved, rejected, or absent from the audit are
    excluded rather than silently entering model features.
    """
    if not os.path.exists(SCOPE_AUDIT_PATH):
        raise FileNotFoundError(
            f"Missing scope audit: {SCOPE_AUDIT_PATH}. "
            "Run build_national_polling_scope.py first."
        )

    if not os.path.exists(SCOPE_OVERRIDES_PATH):
        raise FileNotFoundError(
            f"Missing scope overrides: {SCOPE_OVERRIDES_PATH}"
        )

    polls = df.copy()

    polls["election_year"] = pd.to_numeric(
        polls["election_year"],
        errors="coerce",
    ).astype("Int64")

    audit = pd.read_csv(SCOPE_AUDIT_PATH)

    audit["election_year"] = pd.to_numeric(
        audit["election_year"],
        errors="raise",
    ).astype("Int64")

    overrides = pd.read_csv(
        SCOPE_OVERRIDES_PATH
    )

    overrides["election_year"] = pd.to_numeric(
        overrides["election_year"],
        errors="raise",
    ).astype("Int64")

    key_columns = [
        "country",
        "election_year",
        "source_table",
    ]

    if audit.duplicated(key_columns).any():
        raise ValueError(
            "Duplicate source-table keys found in scope audit."
        )

    if overrides.duplicated(key_columns).any():
        raise ValueError(
            "Duplicate source-table keys found in scope overrides."
        )

    polls = polls.merge(
        audit[
            key_columns
            + [
                "scope_status",
                "scope_reason",
            ]
        ],
        on=key_columns,
        how="left",
        validate="many_to_one",
    )

    polls = polls.merge(
        overrides[
            key_columns
            + [
                "override_status",
                "reason",
                "evidence",
            ]
        ],
        on=key_columns,
        how="left",
        validate="many_to_one",
    )

    polls["effective_scope_status"] = (
        polls["override_status"]
        .fillna(polls["scope_status"])
        .fillna("unclassified")
    )

    polls["effective_scope_reason"] = (
        polls["reason"]
        .fillna(polls["scope_reason"])
        .fillna(
            "source table was absent from the scope audit"
        )
    )

    approved_mask = (
        polls["effective_scope_status"]
        .isin(APPROVED_SCOPE_STATUSES)
    )

    approved = polls.loc[
        approved_mask
    ].copy()

    excluded = polls.loc[
        ~approved_mask
    ].copy()

    os.makedirs(
        "data/features",
        exist_ok=True,
    )

    summary_columns = (
        key_columns
        + [
            "scope_status",
            "override_status",
            "effective_scope_status",
            "effective_scope_reason",
            "evidence",
        ]
    )

    included_summary = (
        approved.groupby(
            summary_columns,
            dropna=False,
        )
        .size()
        .rename("poll_party_rows")
        .reset_index()
        .sort_values(key_columns)
    )

    excluded_summary = (
        excluded.groupby(
            summary_columns,
            dropna=False,
        )
        .size()
        .rename("poll_party_rows")
        .reset_index()
        .sort_values(key_columns)
    )

    included_summary.to_csv(
        INCLUDED_SCOPE_OUTPUT,
        index=False,
    )

    excluded_summary.to_csv(
        EXCLUDED_SCOPE_OUTPUT,
        index=False,
    )

    print("\n=== NATIONAL POLLING SCOPE FILTER ===")

    print(
        f"Included {len(approved):,} poll-party rows "
        f"from {approved[key_columns].drop_duplicates().shape[0]} "
        "country-election-source tables"
    )

    print(
        f"Excluded {len(excluded):,} poll-party rows "
        f"from {excluded[key_columns].drop_duplicates().shape[0]} "
        "country-election-source tables"
    )

    print("\nIncluded effective statuses:")

    print(
        approved["effective_scope_status"]
        .value_counts()
        .to_string()
    )

    print("\nExcluded effective statuses:")

    print(
        excluded["effective_scope_status"]
        .value_counts()
        .to_string()
    )

    print("\nSaved scope audits:")
    print(f"  {INCLUDED_SCOPE_OUTPUT}")
    print(f"  {EXCLUDED_SCOPE_OUTPUT}")

    columns_to_drop = [
        "scope_status",
        "scope_reason",
        "override_status",
        "reason",
        "evidence",
        "effective_scope_status",
        "effective_scope_reason",
    ]

    return approved.drop(
        columns=columns_to_drop,
        errors="ignore",
    )


def apply_election_date_cutoff(df):
    """
    Removes polling observations after the verified election date before
    rolling averages or momentum are calculated.

    Election-result marker rows are retained temporarily because
    build_rolling_features() already excludes them. This function removes
    only dated observations occurring after the election.
    """
    if not os.path.exists(ELECTION_DATES_PATH):
        raise FileNotFoundError(
            f"Missing election dates: {ELECTION_DATES_PATH}"
        )

    polls = df.copy()

    dates = pd.read_csv(
        ELECTION_DATES_PATH
    )

    polls["election_year"] = pd.to_numeric(
        polls["election_year"],
        errors="coerce",
    ).astype("Int64")

    dates["election_year"] = pd.to_numeric(
        dates["election_year"],
        errors="raise",
    ).astype("Int64")

    dates["election_date"] = pd.to_datetime(
        dates["election_date"],
        errors="raise",
    )

    polls = polls.merge(
        dates[
            [
                "country",
                "election_year",
                "election_date",
            ]
        ],
        on=[
            "country",
            "election_year",
        ],
        how="left",
        validate="many_to_one",
    )

    missing_dates = polls[
        polls["election_date"].isna()
    ][
        [
            "country",
            "election_year",
        ]
    ].drop_duplicates()

    if len(missing_dates):
        print(
            "\nWarning: election dates are unavailable for "
            f"{len(missing_dates)} country-election pairs."
        )

    post_election_mask = (
        polls["poll_date"].notna()
        & polls["election_date"].notna()
        & (
            polls["poll_date"]
            > polls["election_date"]
        )
    )

    excluded = polls.loc[
        post_election_mask
    ].copy()

    retained = polls.loc[
        ~post_election_mask
    ].copy()

    audit_columns = [
        "country",
        "election_year",
        "source_table",
        "date_raw",
        "pollster",
        "party",
        "pct",
        "poll_date",
        "election_date",
    ]

    excluded[
        audit_columns
    ].sort_values(
        [
            "country",
            "election_year",
            "poll_date",
            "source_table",
            "party",
        ]
    ).to_csv(
        POST_ELECTION_AUDIT_OUTPUT,
        index=False,
    )

    print("\n=== ELECTION-DATE CUTOFF ===")

    print(
        f"Removed {len(excluded):,} post-election "
        "poll-party rows before feature engineering"
    )

    if len(excluded):
        print(
            excluded.groupby(
                [
                    "country",
                    "election_year",
                ]
            )
            .size()
            .rename("removed_rows")
            .to_string()
        )

    print(
        f"Saved audit to {POST_ELECTION_AUDIT_OUTPUT}"
    )

    return retained.drop(
        columns=["election_date"],
        errors="ignore",
    )


def main():
    all_dfs = []
    for path in glob.glob("data/polling_clean/*_polls_clean.csv"):
        df = pd.read_csv(path)
        all_dfs.append(df)

    if not all_dfs:
        print("No cleaned polling data found in data/polling_clean/ -- run "
              "clean_polling_data.py first.")
        return

    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"Loaded {len(combined)} poll-party rows across "
          f"{combined['country'].nunique()} countries")

    combined = apply_national_scope_filter(
        combined
    )

    if combined.empty:
        raise ValueError(
            "National scope filtering removed every polling row."
        )

    print(
        f"Continuing with {len(combined):,} approved "
        "national poll-party rows"
    )

    # Two-pass date parsing: first pass without month hints, then backfill
    # real election months from is_election_result rows, then re-parse so
    # month-only date ranges roll back to the correct year.
    combined = add_parsed_dates(combined)
    months = backfill_election_months(combined, {})
    combined = add_parsed_dates(combined, election_month_by_country_year=months)

    parsed = combined["poll_date"].notna().sum()
    print(f"Parsed {parsed}/{len(combined)} dates ({parsed/len(combined)*100:.1f}%) "
          f"after election-month backfill")

    combined = apply_election_date_cutoff(
        combined
    )

    features = build_rolling_features(
        combined,
        window_size=5,
    )
    os.makedirs("data/features", exist_ok=True)
    features.to_csv("data/features/rolling_momentum_features.csv", index=False)
    print(f"\nBuilt {len(features)} rows of rolling-average + momentum features")
    print(f"Saved to data/features/rolling_momentum_features.csv")
    print("\nSample:")
    print(features.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
