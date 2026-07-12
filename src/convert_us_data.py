"""
Converts US polling data (already downloaded from FiveThirtyEight earlier
in this project) into the same long-format schema used by the UK/Canada/
Australia pipeline: country, election_year, date_raw, pollster, sample_size,
party, pct, source_table -- so US flows into the same date-parsing and
feature-engineering steps as the other three countries.

The FiveThirtyEight file (pres_pollaverages_1968-2016.csv) reports
candidate_name, not party -- this maps each major-party presidential
candidate to their party (a matter of well-established historical record,
not something requiring the same kind of source-hunting the UK/Canada/
Australia party labels needed). Candidates not in the map (third-party/
minor candidates) are labeled OTHER rather than dropped, so they still
contribute to the dataset honestly without needing an exhaustive map of
every minor candidate across 12 election cycles.
"""
import pandas as pd
import os

# Major-party presidential candidates, 1968-2016. Source: well-established
# public historical record (every US presidential election's major-party
# nominees), not requiring the kind of sourcing investigation the other
# countries' minor-party labels needed.
CANDIDATE_PARTY = {
    "Richard Nixon": "REP", "Hubert Humphrey": "DEM",
    "George McGovern": "DEM",
    "Jimmy Carter": "DEM", "Gerald Ford": "REP",
    "Ronald Reagan": "REP",
    "Walter Mondale": "DEM",
    "George Bush": "REP", "Michael Dukakis": "DEM",
    "Bill Clinton": "DEM", "George H.W. Bush": "REP",
    "Bob Dole": "REP",
    "Al Gore": "DEM", "George W. Bush": "REP",
    "John Kerry": "DEM",
    "Barack Obama": "DEM", "John McCain": "REP",
    "Mitt Romney": "REP",
    "Hillary Clinton": "DEM", "Hillary Rodham Clinton": "DEM",
    "Donald Trump": "REP",
}

def map_party(candidate_name):
    if candidate_name in CANDIDATE_PARTY:
        return CANDIDATE_PARTY[candidate_name]
    # Handle minor variations in name formatting without silently losing
    # real major-party candidates due to a formatting mismatch
    for known_name, party in CANDIDATE_PARTY.items():
        if known_name.split()[-1] == str(candidate_name).split()[-1]:
            # last-name match as a fallback (e.g. "Trump" vs "Donald Trump")
            return party
    return "OTHER"

def convert_poll_averages():
    path = "data/us/pres_pollaverages_1968-2016.csv"
    if not os.path.exists(path):
        print(f"  {path} not found, skipping")
        return pd.DataFrame()

    df = pd.read_csv(path)
    df = df[df["state"] == "National"].copy()

    df["country"] = "us"
    df["election_year"] = df["cycle"]
    df["date_raw"] = df["modeldate"]
    df["pollster"] = None  # this file reports averages, not individual polls
    df["sample_size"] = None
    df["party"] = df["candidate_name"].apply(map_party)
    df["pct"] = df["pct_estimate"]
    df["source_table"] = "pres_pollaverages_1968-2016.csv"

    return df[["country", "election_year", "date_raw", "pollster",
               "sample_size", "party", "pct", "source_table"]]

def convert_pollster_files():
    """polls_2020.csv / polls_2024.csv report pollster metadata (name,
    rating, dates) but NOT per-poll vote-share percentages -- they're a
    different kind of file (pollster directory, not poll results) and
    genuinely can't be reshaped into the pct-per-party schema without
    fabricating numbers that aren't in the source. Documented here rather
    than silently skipped, so this limitation is visible."""
    frames = []
    for year, path in [(2020, "data/us/polls_2020.csv"), (2024, "data/us/polls_2024.csv")]:
        if os.path.exists(path):
            print(f"  {path} found but NOT converted: this file lists "
                  f"pollster metadata (ratings, dates active) not individual "
                  f"poll results with vote-share percentages -- there is no "
                  f"pct column to convert. {year} coverage in the unified "
                  f"dataset comes only from pres_pollaverages if it extends "
                  f"that far, otherwise {year} has a real, honest gap.")
    return frames

def main():
    print("Converting US polling data to unified schema...")
    poll_avg_df = convert_poll_averages()

    if len(poll_avg_df) > 0:
        years = sorted(poll_avg_df["election_year"].unique())
        parties = sorted(poll_avg_df["party"].unique())
        print(f"  Converted {len(poll_avg_df)} rows, years {years}")
        print(f"  Parties: {parties}")
        other_count = (poll_avg_df["party"] == "OTHER").sum()
        if other_count > 0:
            print(f"  NOTE: {other_count} rows mapped to OTHER (minor-party "
                  f"or unmapped candidates) -- not dropped, but not "
                  f"individually identified. Real third-party candidates "
                  f"(e.g. Ross Perot, Ralph Nader, Gary Johnson) are present "
                  f"in the source data under OTHER rather than fabricated "
                  f"specific party labels without verification.")

    convert_pollster_files()

    os.makedirs("data/polling_clean", exist_ok=True)
    out_path = "data/polling_clean/us_polls_clean.csv"
    poll_avg_df.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")
    print("\nSample:")
    print(poll_avg_df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
