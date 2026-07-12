"""
Feature engineering, part 3 (final DSA component): cross-country similar-
election lookup.

DSA element: a KD-tree (k-dimensional tree, via scipy.spatial.KDTree) is a
spatial indexing structure that answers "which points are nearest to this
one" in O(log n) average time rather than the O(n) brute-force distance
comparison a naive search would require. Here, each election (regardless
of country) becomes a point in a small feature space (poll volatility,
final margin, campaign length, etc.), and querying the tree finds which
OTHER elections -- possibly in a completely different country -- looked
statistically similar, e.g. "this was a tight, volatile race" vs "this was
a landslide with a stable campaign."

Per-election feature vector (built only from data already verified real
in this project, no new sourcing):
  - final_leader_pct: the last chronological poll reading (from the
    rolling-average feature) for whichever party actually won
  - poll_volatility: standard deviation of that party's poll readings
    across the whole cycle -- a volatile campaign vs a stable one
  - actual_margin: winning margin in the real actual result (top party
    minus second party) -- landslide vs close race
  - n_polls: how many polls were conducted in that cycle -- a rough proxy
    for how closely-watched/competitive the race was
"""
import pandas as pd
import numpy as np
from scipy.spatial import KDTree
import os

def build_election_feature_vectors():
    features_path = "data/features/rolling_momentum_features.csv"
    actuals_path = "data/results_clean/national_actual_results.csv"

    if not os.path.exists(features_path) or not os.path.exists(actuals_path):
        print("  Required input files not found -- run build_features.py "
              "and build_national_results.py first")
        return pd.DataFrame()

    momentum = pd.read_csv(features_path)
    actuals = pd.read_csv(actuals_path)

    # Same class of bug already fixed in build_pollster_reliability.py:
    # election_year can end up as a different dtype (int64 vs object/str)
    # across dataframes built by different scripts. A plain "==" comparison
    # on mismatched types silently returns all-False rather than raising --
    # this was the actual root cause of zero feature vectors being built on
    # first production run (no crash, no error message, just silently
    # empty). Coerce explicitly before any comparison.
    momentum["election_year"] = pd.to_numeric(momentum["election_year"], errors="coerce").astype("Int64")
    actuals["election_year"] = pd.to_numeric(actuals["election_year"], errors="coerce").astype("Int64")
    momentum = momentum.dropna(subset=["election_year"])
    actuals = actuals.dropna(subset=["election_year"])

    rows = []
    for (country, year), group in actuals.groupby(["country", "election_year"]):
        group_sorted = group.sort_values("actual_pct", ascending=False)
        if len(group_sorted) < 2:
            continue
        leader_party = group_sorted.iloc[0]["party"]
        leader_pct = group_sorted.iloc[0]["actual_pct"]
        runner_up_pct = group_sorted.iloc[1]["actual_pct"]
        actual_margin = leader_pct - runner_up_pct

        cycle_polls = momentum[
            (momentum["country"] == country)
            & (momentum["election_year"] == year)
            & (momentum["party"] == leader_party)
        ]
        if len(cycle_polls) == 0:
            continue

        cycle_polls_sorted = cycle_polls.sort_values("poll_date")
        final_leader_pct = cycle_polls_sorted.iloc[-1]["rolling_avg"]
        poll_volatility = cycle_polls["pct"].std()
        n_polls = len(cycle_polls)

        if pd.isna(poll_volatility):
            poll_volatility = 0.0

        rows.append({
            "country": country, "election_year": year, "leader_party": leader_party,
            "final_leader_pct": final_leader_pct, "poll_volatility": poll_volatility,
            "actual_margin": actual_margin, "n_polls": n_polls,
        })

    return pd.DataFrame(rows)

def build_kdtree_similar_elections(feature_df, k=3):
    """Standardises features (z-score, so no single feature with a larger
    numeric range dominates the distance metric), builds a KD-tree, and
    finds the k nearest OTHER elections for each election -- explicitly
    allowing cross-country matches (a UK election can be "similar" to an
    Australian one)."""
    feature_cols = ["final_leader_pct", "poll_volatility", "actual_margin", "n_polls"]
    X = feature_df[feature_cols].values.astype(float)

    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds[stds == 0] = 1.0  # avoid divide-by-zero for a constant column
    X_standardised = (X - means) / stds

    tree = KDTree(X_standardised)

    # KDTree.query with k larger than the number of available points
    # returns sentinel entries (index == len(data), distance == inf) for
    # the "missing" neighbors rather than raising an error -- cap k to
    # what's actually available, and still guard against any stray
    # out-of-bounds index defensively.
    effective_k = min(k, len(feature_df) - 1)
    if effective_k < 1:
        print("  Not enough elections to find any similar pairs (need at least 2)")
        return pd.DataFrame()

    results = []
    for i, row in feature_df.iterrows():
        distances, indices = tree.query(X_standardised[i], k=effective_k + 1)
        for dist, idx in zip(np.atleast_1d(distances), np.atleast_1d(indices)):
            if idx == i or idx >= len(feature_df):
                continue
            neighbor = feature_df.iloc[idx]
            results.append({
                "country": row["country"], "election_year": row["election_year"],
                "similar_country": neighbor["country"], "similar_election_year": neighbor["election_year"],
                "distance": dist,
            })

    return pd.DataFrame(results)

def main():
    print("Building per-election feature vectors...")
    features = build_election_feature_vectors()
    if len(features) == 0:
        return
    print(f"  Built {len(features)} election feature vectors "
          f"across {features['country'].nunique()} countries")

    print("\nBuilding KD-tree and finding cross-country similar elections (k=3)...")
    similar = build_kdtree_similar_elections(features, k=3)

    os.makedirs("data/features", exist_ok=True)
    features.to_csv("data/features/election_feature_vectors.csv", index=False)
    similar.to_csv("data/features/similar_elections.csv", index=False)

    cross_country = similar[similar["country"] != similar["similar_country"]]
    print(f"\n{len(similar)} total similarity pairs found, "
          f"{len(cross_country)} of them cross-country")

    print("\nSample of cross-country similar-election pairs:")
    print(cross_country.head(10).to_string(index=False))

    print(f"\nSaved to data/features/election_feature_vectors.csv and "
          f"data/features/similar_elections.csv")

if __name__ == "__main__":
    main()
