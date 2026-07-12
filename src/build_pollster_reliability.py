"""
Feature engineering, part 2: pollster-reliability ranking.

DSA element: a min-heap priority queue (heapq) ranks pollsters by their
historical mean absolute error against actual results -- this is the
canonical priority-queue application (always efficiently retrieve the
best/worst element without a full sort), used here to answer "which
pollsters are most reliable" in O(log n) per insertion rather than
resorting the whole list every time a new pollster's score is added.

Note: US contributes no pollster-level data here -- pres_pollaverages
reports model-averaged estimates, not individual named polls, so the
pollster column is empty for all US rows. Reliability ranking only covers
UK/Canada/Australia, where individual pollster names were scraped.
"""
import pandas as pd
import heapq
import glob
import os
import re

# Reused directly from date_parser.py's RESULT_MARKER_PATTERN rather than
# re-defining a second, possibly-divergent copy
RESULT_MARKER_PATTERN = re.compile(r"election|voting result|by-election", re.I)

def load_polls_with_pollster():
    frames = []
    for path in glob.glob("data/polling_clean/*_polls_clean.csv"):
        df = pd.read_csv(path)
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined = combined[combined["pollster"].notna()]

    # The is_election_result column is only ever added by date_parser.py's
    # add_parsed_dates() -- these raw *_polls_clean.csv files never had it
    # in the first place, so checking for that column here was a no-op bug
    # (silently excluded nothing). Real actual-result rows show up with an
    # election-marker string sitting in EITHER the pollster field (e.g.
    # Canada's "2019 election" placeholder) or the date_raw field (e.g. UK's
    # "1997 general election"/"2008 by-election") depending on the source
    # table's column layout -- check both directly against the same pattern
    # date_parser.py itself uses, rather than relying on a column that was
    # never populated here.
    is_marker = (
        combined["pollster"].astype(str).str.contains(RESULT_MARKER_PATTERN)
        | combined["date_raw"].astype(str).str.contains(RESULT_MARKER_PATTERN)
    )
    excluded_count = is_marker.sum()
    if excluded_count > 0:
        print(f"  Excluding {excluded_count} rows where pollster/date_raw "
              f"is an election-result marker, not a real named pollster")
    combined = combined[~is_marker]

    return combined

def compute_poll_errors(polls_df, actuals_df):
    """Joins each poll to its matching actual result (same country,
    election_year, party) and computes absolute error. Polls with no
    matching actual (e.g. Australia's Primary-vote polls, which have no
    national Primary-vote actuals collected) are excluded from scoring
    rather than assigned a fabricated error."""
    # election_year can end up as int64 in one dataframe and object/str in
    # the other after concatenating multiple source CSVs with slightly
    # different original dtypes -- coerce both sides explicitly before
    # merging, or pandas refuses to join on mismatched key types.
    polls_df = polls_df.copy()
    actuals_df = actuals_df.copy()
    polls_df["election_year"] = pd.to_numeric(polls_df["election_year"], errors="coerce").astype("Int64")
    actuals_df["election_year"] = pd.to_numeric(actuals_df["election_year"], errors="coerce").astype("Int64")
    polls_df = polls_df.dropna(subset=["election_year"])
    actuals_df = actuals_df.dropna(subset=["election_year"])

    merged = polls_df.merge(
        actuals_df, on=["country", "election_year", "party"], how="inner"
    )
    merged["abs_error"] = (merged["pct"] - merged["actual_pct"]).abs()
    return merged

def rank_pollsters_by_reliability(poll_errors_df, min_polls=5):
    """DSA: builds a min-heap of (mean_abs_error, pollster, n_polls) and
    pops in order to produce a reliability ranking -- lowest error (most
    reliable) first. Pollsters with fewer than min_polls scored polls are
    excluded, since a single lucky/unlucky poll shouldn't rank a pollster
    at the extreme end of the list."""
    grouped = poll_errors_df.groupby(["country", "pollster"])["abs_error"].agg(["mean", "count"])
    grouped = grouped[grouped["count"] >= min_polls]

    heap = []
    for (country, pollster), row in grouped.iterrows():
        heapq.heappush(heap, (row["mean"], country, pollster, int(row["count"])))

    ranked = []
    while heap:
        mean_error, country, pollster, n_polls = heapq.heappop(heap)
        ranked.append({
            "rank": len(ranked) + 1, "country": country, "pollster": pollster,
            "mean_abs_error": mean_error, "n_polls_scored": n_polls,
        })
    return pd.DataFrame(ranked)

def main():
    print("Loading polls and actual results...")
    polls = load_polls_with_pollster()
    print(f"  {len(polls)} poll-party rows with a real pollster name")

    actuals_path = "data/results_clean/national_actual_results.csv"
    if not os.path.exists(actuals_path):
        print(f"  {actuals_path} not found -- run build_national_results.py first")
        return
    actuals = pd.read_csv(actuals_path)
    print(f"  {len(actuals)} actual national results rows")

    errors = compute_poll_errors(polls, actuals)
    print(f"\nMatched {len(errors)} polls to a real actual result "
          f"({len(errors)/len(polls)*100:.1f}% of pollster-attributed polls)")

    unmatched_parties = set(polls["party"]) - set(errors["party"])
    if unmatched_parties:
        print(f"  Parties with NO matching actual result (excluded from "
              f"scoring, not fabricated): {sorted(unmatched_parties)}")

    ranking = rank_pollsters_by_reliability(errors, min_polls=5)
    os.makedirs("data/features", exist_ok=True)
    ranking.to_csv("data/features/pollster_reliability_ranking.csv", index=False)

    print(f"\nRanked {len(ranking)} pollsters (min 5 scored polls each)")
    print("\nTop 10 most reliable pollsters:")
    print(ranking.head(10).to_string(index=False))
    print("\nBottom 10 least reliable pollsters:")
    print(ranking.tail(10).to_string(index=False))
    print(f"\nSaved to data/features/pollster_reliability_ranking.csv")

if __name__ == "__main__":
    main()
