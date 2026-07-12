"""
Train/test split strategy for election modeling.

WHY THIS MATTERS: election data is temporal. Randomly shuffling all
elections and doing an 80/20 split would let the model train on a 2019
election while being tested on a 2013 election it happened AFTER -- a real
form of data leakage (the model implicitly has "future" information
relative to what it's being evaluated on). This is exactly the kind of
subtle mistake that separates a genuinely rigorous project from a
superficially plausible one.

Nested validation approach used here (combining chronological holdout +
leave-one-election-out cross-validation, per explicit user decision):

  1. CHRONOLOGICAL HOLDOUT: the most recent N elections per country are set
     aside and NEVER touched during model development or tuning. These
     exist purely to produce one final, honest, unbiased performance number
     at the very end.

  2. LEAVE-ONE-ELECTION-OUT CV: within the remaining (older) elections,
     each election takes a turn being the "test" case while the model
     trains on every other remaining election. This is the standard way to
     get a robust performance estimate from a small number of elections
     (we have ~22-28 per country, not thousands of rows -- individual
     elections are the natural unit of a train/test split here, NOT
     individual polls, since polls from the same election are correlated
     with each other and splitting at the poll level would leak
     information about that specific election's outcome).
"""
import pandas as pd
import os

def get_election_list(actuals_path="data/results_clean/national_actual_results.csv",
                       features_path="data/features/election_feature_vectors.csv"):
    """Returns a DataFrame of unique (country, election_year) pairs, sorted
    chronologically within each country.

    IMPORTANT: restricted to the INTERSECTION of elections that have both
    real actual results AND real polling-based features. The raw results
    files go back much further than the scraped polling data does (e.g.
    Canada's results file covers all 43 federal elections since 1867, but
    Wikipedia polling data was only scraped for the 8 most recent cycles).
    An election with real results but zero polling data has nothing for a
    polling-based model to learn from -- including it in the split would
    silently create rows with all-empty features. Since this project's
    entire premise is predicting FROM polling data, only elections where
    genuine polling-derived features exist belong in the modeling
    population at all."""
    actuals = pd.read_csv(actuals_path)
    actuals["election_year"] = pd.to_numeric(actuals["election_year"], errors="coerce")
    actuals = actuals.dropna(subset=["election_year"])
    elections_with_results = actuals[["country", "election_year"]].drop_duplicates()

    if not os.path.exists(features_path):
        print(f"  WARNING: {features_path} not found -- run build_similar_elections.py "
              f"first to establish which elections have real polling features. "
              f"Falling back to results-only list (NOT RECOMMENDED for modeling).")
        elections = elections_with_results
    else:
        features = pd.read_csv(features_path)
        features["election_year"] = pd.to_numeric(features["election_year"], errors="coerce")
        elections_with_features = features[["country", "election_year"]].drop_duplicates()

        elections = elections_with_results.merge(
            elections_with_features, on=["country", "election_year"], how="inner"
        )
        dropped = len(elections_with_results) - len(elections)
        print(f"  {len(elections_with_results)} elections have real actual results; "
              f"restricting to the {len(elections)} that ALSO have real polling "
              f"features ({dropped} elections excluded -- results exist but no "
              f"polling data was ever scraped for them, so there's nothing for a "
              f"polling-based model to learn from)")

    elections = elections.sort_values(["country", "election_year"]).reset_index(drop=True)
    return elections

def chronological_holdout_split(elections, n_holdout_per_country=2):
    """Splits into a development set (everything except the most recent N
    elections per country) and a holdout set (the most recent N per
    country). The holdout set must not be touched until final evaluation."""
    holdout_rows = []
    dev_rows = []
    for country, group in elections.groupby("country"):
        group_sorted = group.sort_values("election_year")
        n = min(n_holdout_per_country, len(group_sorted) - 1)  # always leave >=1 for dev
        if n < 1:
            # too few elections in this country to hold anything out safely
            dev_rows.append(group_sorted)
            continue
        holdout_rows.append(group_sorted.tail(n))
        dev_rows.append(group_sorted.iloc[:-n])

    holdout = pd.concat(holdout_rows, ignore_index=True) if holdout_rows else pd.DataFrame(columns=elections.columns)
    dev = pd.concat(dev_rows, ignore_index=True)
    return dev, holdout

def leave_one_election_out_folds(dev_elections):
    """Generator yielding (train_elections, test_election) for each
    election in the development set -- one fold per election, training on
    every other development-set election."""
    for i in range(len(dev_elections)):
        test_election = dev_elections.iloc[[i]]
        train_elections = dev_elections.drop(dev_elections.index[i])
        yield train_elections, test_election

def main():
    elections = get_election_list()
    print(f"Total elections across all countries: {len(elections)}")
    print(elections.groupby("country").size().to_string())

    dev, holdout = chronological_holdout_split(elections, n_holdout_per_country=2)
    print(f"\nDevelopment set: {len(dev)} elections (used for CV/tuning)")
    print(f"Chronological holdout: {len(holdout)} elections (untouched until final evaluation)")
    print("\nHoldout elections (most recent per country, never used until the very end):")
    print(holdout.sort_values(["country", "election_year"]).to_string(index=False))

    print(f"\nLeave-one-election-out CV folds within development set: {len(dev)} folds")
    fold_sizes = []
    for train, test in leave_one_election_out_folds(dev):
        fold_sizes.append((len(train), len(test)))
    print(f"  Each fold trains on {fold_sizes[0][0]} elections, tests on 1")

    os.makedirs("data/splits", exist_ok=True)
    dev.to_csv("data/splits/development_elections.csv", index=False)
    holdout.to_csv("data/splits/holdout_elections.csv", index=False)
    print(f"\nSaved to data/splits/development_elections.csv and holdout_elections.csv")

if __name__ == "__main__":
    main()
