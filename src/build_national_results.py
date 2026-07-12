"""
Builds national actual-vote-share-by-party-by-election from each country's
raw results file, as the ground truth for measuring poll accuracy. Each
country's results file has a different native granularity (constituency/
riding/division-level for UK/Canada/Australia's first-preference data, or
candidate-level for US), so this does real vote-weighted national
aggregation rather than averaging pre-computed shares (averaging shares
across constituencies would incorrectly treat every constituency as equal
weight regardless of how many people actually voted there).

Known real anchor figures checked after aggregation (not fabricated targets
-- these are well-documented historical facts used only to sanity-check the
aggregation logic itself):
  UK 2019: Conservative ~43.6% of GB vote
  Australia 2022: ALP 52.13% TPP (already have this directly, no
    aggregation needed -- see build_australia_tpp.py from earlier)
  US 2016: Trump ~46.1%, Clinton ~48.2% of national popular vote
"""
import pandas as pd
import os

def read_csv_robust(path, **kwargs):
    """Tries UTF-8 first, falling back to cp1252 (the common encoding for
    UK government CSV exports from legacy Excel tooling) then latin-1 as a
    last resort that can decode any byte sequence. This isn't guessing --
    it's the standard, well-known encoding fallback order for exactly this
    situation (a UnicodeDecodeError on byte 0xf4, which is a valid
    accented-character byte in cp1252 but not valid UTF-8 continuation)."""
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding, **kwargs)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"Could not decode {path} with utf-8, cp1252, or latin-1")

def build_uk_national_results():
    path = "data/uk/election_results_1918_2019.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    df = read_csv_robust(path)
    df.columns = [c.strip() for c in df.columns]

    # Real data has blank/dash entries for parties that didn't contest a
    # given seat -- coerce to numeric explicitly (non-numeric -> NaN, which
    # .sum() correctly skips) rather than letting these columns stay as
    # object dtype, where .sum() silently does string concatenation instead
    # of arithmetic and the whole aggregation breaks downstream.
    vote_cols = ["con_votes", "lib_votes", "lab_votes", "total_votes"]
    for col in vote_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    party_vote_cols = {
        "CON": "con_votes", "LIB": "lib_votes", "LAB": "lab_votes",
    }
    rows = []
    for year, group in df.groupby("election"):
        total_votes = group["total_votes"].sum()
        if total_votes == 0 or pd.isna(total_votes):
            continue
        for party, col in party_vote_cols.items():
            if col not in group.columns:
                continue
            party_votes = group[col].sum()
            if pd.isna(party_votes):
                continue
            pct = party_votes / total_votes * 100
            rows.append({"country": "uk", "election_year": year, "party": party, "actual_pct": pct})
    return pd.DataFrame(rows)

def build_canada_national_results():
    import glob

    rows = []

    # Canadian source files use slightly different Conservative column
    # names across election years. In particular, 2004 uses "ConParty",
    # while later files use "Con". Both represent the federal Conservative
    # Party and therefore map to the same canonical polling label: CPC.
    party_column_map = {
        "Bloc": "BQ",
        "Con": "CPC",
        "ConParty": "CPC",
        "Grn": "GPC",
        "Lib": "LPC",
        "NDP": "NDP",
        "Other": "OTHER",
    }

    for csv_path in glob.glob("data/canada/by_riding_*.csv"):
        year = int(csv_path.split("_")[-1].replace(".csv", ""))
        df = read_csv_robust(csv_path)

        present_party_cols = [
            column
            for column in party_column_map
            if column in df.columns
        ]

        if not present_party_cols:
            continue

        canonical_labels = [
            party_column_map[column]
            for column in present_party_cols
        ]

        if len(canonical_labels) != len(set(canonical_labels)):
            raise ValueError(
                f"{csv_path} contains multiple columns mapping to the "
                f"same canonical party label: {canonical_labels}"
            )

        for column in present_party_cols:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        total_votes = df[present_party_cols].sum().sum()

        if total_votes == 0 or pd.isna(total_votes):
            continue

        for column in present_party_cols:
            party_votes = df[column].sum()
            actual_pct = party_votes / total_votes * 100

            rows.append({
                "country": "canada",
                "election_year": year,
                "party": party_column_map[column],
                "actual_pct": actual_pct,
            })

    return pd.DataFrame(rows)

def build_australia_national_results():
    """Australia's TPP national results are already directly available
    (no aggregation needed) from the earlier AEC transcription. Primary
    vote national actuals are NOT collected anywhere in this project --
    this is a real, honest gap: pollster-reliability scoring for
    Australia's (Primary)-tagged poll data cannot be computed without
    separately sourcing national first-preference results, which hasn't
    been done. Only (2PP)-tagged Australia polls can be validated here."""
    path = "data/australia/tpp_national_1949_2022.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    df = read_csv_robust(path)
    rows = []
    for _, row in df.iterrows():
        rows.append({"country": "australia", "election_year": row["year"], "party": "ALP (2PP)", "actual_pct": row["alp_tpp_pct"]})
        rows.append({"country": "australia", "election_year": row["year"], "party": "L/NP (2PP)", "actual_pct": row["coalition_tpp_pct"]})
    return pd.DataFrame(rows)

def build_us_national_results():
    path = "data/us/election_results_presidential.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    df = read_csv_robust(path)
    df = df[df["stage"] == "general"].copy()
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce")

    # candidate_name -> party mapping reused from convert_us_data.py's
    # historical-record approach
    from convert_us_data import map_party

    rows = []
    for year, group in df.groupby("cycle"):
        total_votes = group["votes"].sum()
        if total_votes == 0 or pd.isna(total_votes):
            continue
        group = group.copy()
        group["party_mapped"] = group["candidate_name"].apply(map_party)
        for party, subgroup in group.groupby("party_mapped"):
            party_votes = subgroup["votes"].sum()
            pct = party_votes / total_votes * 100
            rows.append({"country": "us", "election_year": year, "party": party, "actual_pct": pct})
    return pd.DataFrame(rows)

def main():
    print("Building national actual-vote-share results per country...\n")

    uk = build_uk_national_results()
    canada = build_canada_national_results()
    australia = build_australia_national_results()
    us = build_us_national_results()

    combined = pd.concat([uk, canada, australia, us], ignore_index=True)
    os.makedirs("data/results_clean", exist_ok=True)
    combined.to_csv("data/results_clean/national_actual_results.csv", index=False)

    print(f"UK: {len(uk)} rows, {uk['election_year'].nunique() if len(uk) else 0} elections")
    print(f"Canada: {len(canada)} rows, {canada['election_year'].nunique() if len(canada) else 0} elections")
    print(f"Australia: {len(australia)} rows, {australia['election_year'].nunique() if len(australia) else 0} elections "
          f"(TPP only -- Primary vote national actuals not collected, real gap)")
    print(f"US: {len(us)} rows, {us['election_year'].nunique() if len(us) else 0} elections")

    print("\n--- Sanity checks against known real historical figures ---")
    if len(uk) > 0:
        uk_2019 = uk[(uk["election_year"] == 2019) & (uk["party"] == "CON")]
        if len(uk_2019) > 0:
            print(f"UK 2019 Conservative national %: {uk_2019['actual_pct'].iloc[0]:.1f}% "
                  f"(known real figure: ~43.6%)")
    if len(us) > 0:
        us_2016 = us[(us["election_year"] == 2016)]
        for _, row in us_2016.iterrows():
            if row["party"] in ("REP", "DEM"):
                print(f"US 2016 {row['party']} national %: {row['actual_pct']:.1f}% "
                      f"(known real figures: Trump ~46.1%, Clinton ~48.2%)")

    print(f"\nSaved to data/results_clean/national_actual_results.csv")

if __name__ == "__main__":
    main()
