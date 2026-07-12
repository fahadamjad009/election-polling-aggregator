"""
Exploratory Data Analysis (EDA) across all 4 countries' polling and results
data. Produces summary statistics and figures answering:

  1. Polling volatility by country -- how much do polls swing during a
     campaign, and does this differ meaningfully between countries?
  2. House effects by pollster -- does a given pollster systematically lean
     toward one party relative to other pollsters (a real, well-documented
     phenomenon in polling analysis, not implying dishonesty -- house
     effects come from real methodological differences like sampling frame
     or weighting choices)
  3. Poll-error distribution vs actual results -- how are prediction errors
     shaped (normal-ish, skewed, fat-tailed)?
  4. Cross-party correlation -- when one party's polling rises, does a
     specific rival's fall (zero-sum dynamic) or is it more diffuse?
"""
import pandas as pd
import numpy as np
import glob
import os
import re

# Reused directly from date_parser.py / build_pollster_reliability.py's
# same pattern -- election-result rows have a marker string like "2010
# general election" sitting in the pollster field (a source-table
# placeholder for the row showing the actual outcome), not a real
# pollster name. Missing this exclusion here (already fixed once in
# build_pollster_reliability.py) let those rows corrupt the house-effects
# ranking the same way they once corrupted the reliability ranking.
RESULT_MARKER_PATTERN = re.compile(r"election|voting result|by-election", re.I)

def exclude_result_marker_rows(df):
    is_marker = (
        df["pollster"].astype(str).str.contains(RESULT_MARKER_PATTERN)
        | df["date_raw"].astype(str).str.contains(RESULT_MARKER_PATTERN)
    )
    excluded = is_marker.sum()
    if excluded > 0:
        print(f"  Excluding {excluded} election-result-marker rows "
              f"(not real pollsters) from house-effects analysis")
    return df[~is_marker]

def load_all_polls():
    frames = [pd.read_csv(p) for p in glob.glob("data/polling_clean/*_polls_clean.csv")]
    return pd.concat(frames, ignore_index=True)

def polling_volatility_by_country(polls):
    """Standard deviation of poll readings per (country, election_year,
    party), averaged up to country level -- a rough proxy for "how much did
    opinion swing during this campaign.\""""
    per_cycle = polls.groupby(["country", "election_year", "party"])["pct"].std()
    per_cycle = per_cycle.dropna()
    by_country = per_cycle.groupby("country").agg(["mean", "median", "std", "count"])
    return by_country.round(2)

def house_effects(polls, actuals, min_polls=10):
    """For each pollster, computes their mean SIGNED error (not absolute)
    per party -- a positive signed error means that pollster systematically
    over-estimated that party relative to the real result, a negative
    error means systematic under-estimation. This is the actual definition
    of a "house effect" in polling analysis."""
    polls = polls.copy()
    polls = exclude_result_marker_rows(polls)
    actuals = actuals.copy()
    polls["election_year"] = pd.to_numeric(polls["election_year"], errors="coerce").astype("Int64")
    actuals["election_year"] = pd.to_numeric(actuals["election_year"], errors="coerce").astype("Int64")

    merged = polls.merge(actuals, on=["country", "election_year", "party"], how="inner")
    merged["signed_error"] = merged["pct"] - merged["actual_pct"]

    grouped = merged.groupby(["country", "pollster", "party"])["signed_error"].agg(["mean", "count"])
    grouped = grouped[grouped["count"] >= min_polls]
    return grouped.sort_values("mean", ascending=False)

def error_distribution_stats(polls, actuals):
    """Shape statistics (skewness, kurtosis) of the poll-error distribution
    -- tells us whether errors are roughly symmetric (normal-ish) or biased/
    fat-tailed, which matters for how confident any model's uncertainty
    estimates can be."""
    from scipy.stats import skew, kurtosis

    polls = polls.copy()
    polls = exclude_result_marker_rows(polls)
    actuals = actuals.copy()
    polls["election_year"] = pd.to_numeric(polls["election_year"], errors="coerce").astype("Int64")
    actuals["election_year"] = pd.to_numeric(actuals["election_year"], errors="coerce").astype("Int64")

    merged = polls.merge(actuals, on=["country", "election_year", "party"], how="inner")
    merged["error"] = merged["pct"] - merged["actual_pct"]

    stats = {
        "n": len(merged),
        "mean_error": merged["error"].mean(),
        "std_error": merged["error"].std(),
        "skewness": skew(merged["error"].dropna()),
        "kurtosis": kurtosis(merged["error"].dropna()),
    }
    return stats, merged

def cross_party_correlation(polls, country, election_year):
    """For a single election cycle, pivots polls into one row per poll date
    with one column per party, then computes the correlation matrix -- a
    real zero-sum dynamic between two parties shows up as a strong negative
    correlation between their columns."""
    cycle = polls[(polls["country"] == country) & (polls["election_year"] == election_year)]
    pivot = cycle.pivot_table(index="date_raw", columns="party", values="pct", aggfunc="mean")
    return pivot.corr()

def main():
    print("Loading all polling and results data...\n")
    polls = load_all_polls()
    actuals_path = "data/results_clean/national_actual_results.csv"
    actuals = pd.read_csv(actuals_path) if os.path.exists(actuals_path) else pd.DataFrame()

    print(f"Loaded {len(polls)} poll-party rows, {len(actuals)} actual result rows\n")

    print("=" * 60)
    print("1. POLLING VOLATILITY BY COUNTRY")
    print("=" * 60)
    volatility = polling_volatility_by_country(polls)
    print(volatility.to_string())

    print("\n" + "=" * 60)
    print("2. HOUSE EFFECTS (top 10 most positive, top 10 most negative)")
    print("=" * 60)
    if len(actuals) > 0:
        effects = house_effects(polls, actuals)
        print("\nMost OVER-estimating (positive house effect):")
        print(effects.head(10).to_string())
        print("\nMost UNDER-estimating (negative house effect):")
        print(effects.tail(10).to_string())
    else:
        print("  No actuals file found -- run build_national_results.py first")

    print("\n" + "=" * 60)
    print("3. POLL ERROR DISTRIBUTION SHAPE")
    print("=" * 60)
    if len(actuals) > 0:
        stats, error_df = error_distribution_stats(polls, actuals)
        for k, v in stats.items():
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
        print("\n  Interpretation: skewness near 0 = symmetric errors (neither")
        print("  systematically over- nor under-estimating overall); positive")
        print("  kurtosis = more extreme outlier errors than a normal")
        print("  distribution would predict (fat tails).")

    os.makedirs("data/eda", exist_ok=True)
    volatility.to_csv("data/eda/polling_volatility_by_country.csv")
    if len(actuals) > 0:
        effects.to_csv("data/eda/house_effects.csv")
        error_df.to_csv("data/eda/poll_errors_full.csv", index=False)

    print(f"\nSaved EDA outputs to data/eda/")

if __name__ == "__main__":
    main()
