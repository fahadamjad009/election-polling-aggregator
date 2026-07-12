"""
Audits whether each cleaned polling source table is national in scope.

For tables containing an election-result marker, the marker percentages are
compared with verified national actual results for the same country and
election year.

This script does not filter polling data. It creates a transparent audit for
review before build_features.py is changed.
"""

import glob
import os
import re

import pandas as pd


POLL_GLOB = "data/polling_clean/*_polls_clean.csv"
ACTUALS_PATH = "data/results_clean/national_actual_results.csv"

OUTPUT_DIR = "data/reference"
AUDIT_OUTPUT = f"{OUTPUT_DIR}/polling_table_scope_audit.csv"
CANDIDATE_OUTPUT = f"{OUTPUT_DIR}/polling_marker_candidates.csv"


# Election-result markers must look like actual result rows, not merely
# contain the word "election" somewhere in a client or organisation name.
DATE_MARKER_PATTERN = re.compile(
    r"^\s*(?:voting results?|election(?: results?)?)"
    r"(?:\s*\[[^\]]+\])?\s*$",
    flags=re.IGNORECASE,
)

POLLSTER_MARKER_PATTERN = re.compile(
    r"^\s*(?:(?:19|20)\d{2}\s+)?"
    r"(?:general\s+)?election"
    r"(?:\s*\[[^\]]+\])?\s*$",
    flags=re.IGNORECASE,
)


def normalise_year(df):
    df = df.copy()

    df["election_year"] = pd.to_numeric(
        df["election_year"],
        errors="coerce",
    ).astype("Int64")

    return df.dropna(
        subset=["election_year"]
    )


def comparison_party(country, party):
    """
    Maps polling labels to labels used by national_actual_results.csv.
    """
    if country == "uk" and party == "LD":
        return "LIB"

    return party


def marker_relevance(date_raw, election_year):
    """
    Scores whether a marker likely refers to the current election cycle.

    Explicit references to another election year are treated as historical.
    Generic labels such as 'Election' and 'Voting result' remain eligible.
    """
    text = str(date_raw)
    years = [
        int(value)
        for value in re.findall(
            r"\b(?:19|20)\d{2}\b",
            text,
        )
    ]

    if years and election_year not in years:
        return "historical_other_year"

    if election_year in years:
        return "explicit_current_year"

    return "generic_current_candidate"


def load_inputs():
    frames = []

    for path in glob.glob(POLL_GLOB):
        frames.append(
            normalise_year(
                pd.read_csv(path)
            )
        )

    if not frames:
        raise FileNotFoundError(
            "No cleaned polling files were found."
        )

    polls = pd.concat(
        frames,
        ignore_index=True,
    )

    actuals = normalise_year(
        pd.read_csv(ACTUALS_PATH)
    )

    polls["pct"] = pd.to_numeric(
        polls["pct"],
        errors="coerce",
    )

    actuals["actual_pct"] = pd.to_numeric(
        actuals["actual_pct"],
        errors="coerce",
    )

    polls = polls.dropna(
        subset=[
            "country",
            "election_year",
            "source_table",
            "party",
            "pct",
        ]
    )

    actuals = actuals.dropna(
        subset=[
            "country",
            "election_year",
            "party",
            "actual_pct",
        ]
    )

    polls["comparison_party"] = polls.apply(
        lambda row: comparison_party(
            row["country"],
            row["party"],
        ),
        axis=1,
    )

    return polls, actuals


def build_marker_candidates(polls, actuals):
    # Canada commonly stores result labels in date_raw, while UK tables
    # commonly store labels such as "2010 general election" in pollster.
    # Match whole result-label fields rather than any text containing the
    # word "election".
    date_text = (
        polls["date_raw"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    pollster_text = (
        polls["pollster"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    date_marker = date_text.str.match(
        DATE_MARKER_PATTERN,
        na=False,
    )

    pollster_marker = pollster_text.str.match(
        POLLSTER_MARKER_PATTERN,
        na=False,
    )

    marker_rows = polls[
        date_marker | pollster_marker
    ].copy()

    marker_rows["marker_text"] = (
        marker_rows["date_raw"].fillna("").astype(str)
        + " | "
        + marker_rows["pollster"].fillna("").astype(str)
    )

    marker_rows["marker_relevance"] = (
        marker_rows.apply(
            lambda row: marker_relevance(
                row["marker_text"],
                int(row["election_year"]),
            ),
            axis=1,
        )
    )

    candidate_rows = []

    group_columns = [
        "country",
        "election_year",
        "source_table",
        "date_raw",
        "marker_relevance",
    ]

    for keys, group in marker_rows.groupby(
        group_columns,
        dropna=False,
    ):
        (
            country,
            election_year,
            source_table,
            date_raw,
            relevance,
        ) = keys

        marker_vector = (
            group[
                [
                    "comparison_party",
                    "pct",
                ]
            ]
            .groupby(
                "comparison_party",
                as_index=False,
            )["pct"]
            .mean()
        )

        election_actuals = actuals[
            (actuals["country"] == country)
            & (
                actuals["election_year"]
                == election_year
            )
        ][
            [
                "party",
                "actual_pct",
            ]
        ].copy()

        comparison = marker_vector.merge(
            election_actuals,
            left_on="comparison_party",
            right_on="party",
            how="inner",
        )

        comparison["abs_error"] = (
            comparison["pct"]
            - comparison["actual_pct"]
        ).abs()

        overlap = len(comparison)

        candidate_rows.append({
            "country": country,
            "election_year": int(election_year),
            "source_table": source_table,
            "date_raw": date_raw,
            "marker_text": (
                " | ".join(
                    sorted(
                        group["marker_text"]
                        .dropna()
                        .astype(str)
                        .unique()
                    )
                )
            ),
            "marker_relevance": relevance,
            "marker_party_rows": int(
                group["comparison_party"].nunique()
            ),
            "national_overlap_parties": overlap,
            "marker_mae": (
                comparison["abs_error"].mean()
                if overlap
                else None
            ),
            "marker_max_abs_error": (
                comparison["abs_error"].max()
                if overlap
                else None
            ),
            "matched_parties": (
                "|".join(
                    sorted(
                        comparison[
                            "comparison_party"
                        ].unique()
                    )
                )
                if overlap
                else ""
            ),
        })

    return pd.DataFrame(candidate_rows)


def choose_best_current_marker(candidates):
    eligible = candidates[
        candidates["marker_relevance"]
        != "historical_other_year"
    ].copy()

    if eligible.empty:
        return None

    eligible["marker_mae_sort"] = (
        eligible["marker_mae"]
        .fillna(float("inf"))
    )

    eligible = eligible.sort_values(
        [
            "national_overlap_parties",
            "marker_mae_sort",
        ],
        ascending=[
            False,
            True,
        ],
    )

    return eligible.iloc[0]


def classify_table(best_marker):
    if best_marker is None:
        return (
            "review",
            "no usable current-cycle election marker",
        )

    overlap = int(
        best_marker["national_overlap_parties"]
    )

    marker_mae = best_marker["marker_mae"]
    max_error = best_marker[
        "marker_max_abs_error"
    ]

    if overlap < 2 or pd.isna(marker_mae):
        return (
            "review",
            "fewer than 2 marker parties matched national actuals",
        )

    if marker_mae <= 1.5 and max_error <= 3.0:
        return (
            "approved_marker_match",
            "election marker closely matches national actual results",
        )

    if marker_mae >= 3.0 or max_error >= 6.0:
        return (
            "rejected_marker_mismatch",
            "election marker materially differs from national actual results",
        )

    return (
        "review",
        "marker comparison is inconclusive",
    )


def build_table_audit(polls, candidates):
    table_rows = []

    grouped = polls.groupby(
        [
            "country",
            "election_year",
            "source_table",
        ]
    )

    for keys, group in grouped:
        country, election_year, source_table = keys

        table_candidates = candidates[
            (candidates["country"] == country)
            & (
                candidates["election_year"]
                == election_year
            )
            & (
                candidates["source_table"]
                == source_table
            )
        ]

        best_marker = choose_best_current_marker(
            table_candidates
        )

        status, reason = classify_table(
            best_marker
        )

        table_rows.append({
            "country": country,
            "election_year": int(election_year),
            "source_table": source_table,
            "poll_party_rows": len(group),
            "party_count": int(
                group["party"].nunique()
            ),
            "party_signature": "|".join(
                sorted(
                    group["party"].unique()
                )
            ),
            "marker_candidate_count": len(
                table_candidates
            ),
            "best_marker_date_raw": (
                best_marker["date_raw"]
                if best_marker is not None
                else ""
            ),
            "best_marker_relevance": (
                best_marker["marker_relevance"]
                if best_marker is not None
                else ""
            ),
            "national_overlap_parties": (
                int(
                    best_marker[
                        "national_overlap_parties"
                    ]
                )
                if best_marker is not None
                else 0
            ),
            "marker_mae": (
                best_marker["marker_mae"]
                if best_marker is not None
                else None
            ),
            "marker_max_abs_error": (
                best_marker[
                    "marker_max_abs_error"
                ]
                if best_marker is not None
                else None
            ),
            "scope_status": status,
            "scope_reason": reason,
        })

    return pd.DataFrame(table_rows).sort_values(
        [
            "country",
            "election_year",
            "scope_status",
            "source_table",
        ]
    )


def main():
    print(
        "Loading cleaned polling tables and national actual results..."
    )

    polls, actuals = load_inputs()

    print(
        f"  {len(polls)} cleaned poll-party rows"
    )

    print(
        f"  {polls['source_table'].nunique()} source tables"
    )

    candidates = build_marker_candidates(
        polls,
        actuals,
    )

    audit = build_table_audit(
        polls,
        candidates,
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    candidates.to_csv(
        CANDIDATE_OUTPUT,
        index=False,
    )

    audit.to_csv(
        AUDIT_OUTPUT,
        index=False,
    )

    print("\n=== TABLE SCOPE STATUS COUNTS ===")

    print(
        audit["scope_status"]
        .value_counts()
        .to_string()
    )

    print("\n=== STATUS COUNTS BY COUNTRY ===")

    print(
        audit.groupby(
            [
                "country",
                "scope_status",
            ]
        )
        .size()
        .rename("tables")
        .to_string()
    )

    print(
        "\n=== FOCUS ELECTION TABLE AUDIT ==="
    )

    focus = audit[
        (
            (audit["country"] == "canada")
            & (
                audit["election_year"]
                == 2004
            )
        )
        |
        (
            (audit["country"] == "uk")
            & audit["election_year"].isin(
                [
                    1997,
                    2001,
                    2005,
                    2010,
                    2015,
                ]
            )
        )
    ]

    print(
        focus[
            [
                "country",
                "election_year",
                "source_table",
                "party_signature",
                "best_marker_date_raw",
                "national_overlap_parties",
                "marker_mae",
                "marker_max_abs_error",
                "scope_status",
            ]
        ]
        .round(3)
        .to_string(index=False)
    )

    print("\nSaved:")
    print(f"  {AUDIT_OUTPUT}")
    print(f"  {CANDIDATE_OUTPUT}")

    print(
        "\nNo polling rows were filtered by this audit."
    )


if __name__ == "__main__":
    main()
