"""
Transcribes official AEC House of Representatives Two-Party-Preferred (TPP)
national results, 1949-2022, from the AEC's own published page. Manually
transcribed from the AUST column of the AEC's official tables -- no
estimation. State-level columns exist on the source page too but are
excluded here since this project scope is national-level only.

Source: https://www.aec.gov.au/elections/federal_elections/tpp-results.htm
(AEC page updated 20 July 2022; sourced from Federal Election Results
1949-1996, Dept of the Parliamentary Library, for 1949-1980, and AEC
Election Statistics for 1983 onwards)

NOTE: Elections before 1984 did not have a full distribution of preferences
for statistical purposes (the 1983 election's ballots were processed
retrospectively) -- the AEC's own caveat, carried forward here.
"""
import pandas as pd

def build_australia_tpp():
    # election_date, alp_tpp_pct, coalition_tpp_pct, winner
    rows = [
        ("1949-12-10", 49.0, 51.0, "Coalition"),
        ("1951-04-28", 49.3, 50.7, "Coalition"),
        ("1954-05-29", 50.7, 49.3, "Coalition"),
        ("1955-12-10", 45.8, 54.2, "Coalition"),
        ("1958-11-22", 45.9, 54.1, "Coalition"),
        ("1961-12-09", 50.5, 49.5, "Coalition"),
        ("1963-11-30", 47.4, 52.6, "Coalition"),
        ("1966-11-26", 43.1, 56.9, "Coalition"),
        ("1969-10-25", 50.2, 49.8, "Coalition"),
        ("1972-12-02", 52.7, 47.3, "ALP"),
        ("1974-05-18", 51.7, 48.3, "ALP"),
        ("1975-12-13", 44.3, 55.7, "Coalition"),
        ("1977-12-10", 45.4, 54.6, "Coalition"),
        ("1980-10-18", 49.6, 50.4, "Coalition"),
        ("1983-03-05", 53.23, 46.77, "ALP"),
        ("1984-12-01", 51.77, 48.23, "ALP"),
        ("1987-07-11", 50.83, 49.17, "ALP"),
        ("1990-03-24", 49.90, 50.10, "ALP"),
        ("1993-03-13", 51.44, 48.56, "ALP"),
        ("1996-03-02", 46.37, 53.63, "Coalition"),
        ("1998-10-03", 50.98, 49.02, "Coalition"),
        ("2001-11-10", 49.05, 50.95, "Coalition"),
        ("2004-10-09", 47.26, 52.74, "Coalition"),
        ("2007-11-24", 52.70, 47.30, "ALP"),
        ("2010-08-21", 50.12, 49.88, "ALP"),
        ("2013-09-07", 46.51, 53.49, "Coalition"),
        ("2016-07-02", 49.64, 50.36, "Coalition"),
        ("2019-05-18", 48.47, 51.53, "Coalition"),
        ("2022-05-21", 52.13, 47.87, "ALP"),
    ]
    df = pd.DataFrame(rows, columns=[
        "election_date", "alp_tpp_pct", "coalition_tpp_pct", "winner"
    ])
    df["year"] = pd.to_datetime(df["election_date"]).dt.year
    df.to_csv("data/australia/tpp_national_1949_2022.csv", index=False)
    return df

def main():
    df = build_australia_tpp()
    print(f"Australia national TPP results built: {len(df)} elections, 1949-2022")
    print(df.to_string(index=False))
    print(f"\nWinner counts: {df['winner'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()
