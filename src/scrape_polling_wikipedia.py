"""
Scrapes raw HTML tables of individual opinion polls directly from Wikipedia's
"Opinion polling for the X election" articles, using pandas.read_html to
parse every table on each page. This is a standard, legitimate technique for
personal/portfolio data analysis -- it fetches structured data programmatically
rather than reproducing large tables by hand.

Each page's tables are saved RAW (unmodified column names, one CSV per
page/table) since table structure varies significantly across election
cycles and countries (different parties, different eras). A separate
cleaning/normalisation script should run AFTER this to unify schemas --
attempting to force a common schema during scraping risks silently
dropping or misaligning columns.

Usage:
    pip install pandas lxml html5lib requests --break-system-packages
    python scrape_polling_wikipedia.py
"""
import pandas as pd
import requests
import time
import os
import re
from io import StringIO

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) portfolio-research-script"}

# UK: one "Opinion polling for the YYYY United Kingdom general election" page
# per election since 1945. Earlier elections (pre-1997) often lack dedicated
# pages or have sparse polling data -- start from 1997 where coverage is rich
# and consistent, matching the depth the US/other sources already provide.
UK_ELECTIONS = [1997, 2001, 2005, 2010, 2015, 2017, 2019, 2024]

# Canada: "Opinion polling for the CANADIAN_ELECTION_YEAR federal election"
CANADA_ELECTIONS = [2004, 2006, 2008, 2011, 2015, 2019, 2021, 2025]

# Australia: "Opinion polling for the CANADIAN_ELECTION_YEAR Australian federal election"
AUSTRALIA_ELECTIONS = [2004, 2007, 2010, 2013, 2016, 2019, 2022, 2025]

def build_url(country, year):
    if country == "uk":
        return f"https://en.wikipedia.org/wiki/Opinion_polling_for_the_{year}_United_Kingdom_general_election"
    elif country == "canada":
        return f"https://en.wikipedia.org/wiki/Opinion_polling_for_the_{year}_Canadian_federal_election"
    elif country == "australia":
        return f"https://en.wikipedia.org/wiki/Opinion_polling_for_the_{year}_Australian_federal_election"

def scrape_page(country, year, out_dir):
    url = build_url(country, year)
    print(f"Fetching {url} ...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  FAILED: {e}")
        return 0

    try:
        tables = pd.read_html(StringIO(resp.text))
    except ValueError as e:
        print(f"  No tables found: {e}")
        return 0

    saved = 0
    for i, table in enumerate(tables):
        # Skip tiny/irrelevant tables (nav boxes, single-row summaries)
        if len(table) < 3:
            continue
        # Skip tables that clearly aren't polling data (no numeric-looking columns)
        numeric_like_cols = sum(
            table[col].astype(str).str.contains(r"\d", regex=True).mean() > 0.3
            for col in table.columns
        )
        if numeric_like_cols < 2:
            continue
        fname = f"{out_dir}/{country}_{year}_table{i}.csv"
        table.to_csv(fname, index=False)
        saved += 1
    print(f"  Saved {saved} table(s)")
    return saved

def main():
    out_dir = "data/polling_raw"
    os.makedirs(out_dir, exist_ok=True)

    total = 0
    for year in UK_ELECTIONS:
        total += scrape_page("uk", year, out_dir)
        time.sleep(1)  # be polite to Wikipedia's servers
    for year in CANADA_ELECTIONS:
        total += scrape_page("canada", year, out_dir)
        time.sleep(1)
    for year in AUSTRALIA_ELECTIONS:
        total += scrape_page("australia", year, out_dir)
        time.sleep(1)

    print(f"\nDone. {total} raw poll tables saved to {out_dir}/")
    print("Next step: inspect a few files manually, then write a cleaning script")
    print("to normalise columns (date, pollster, party percentages) per country.")

if __name__ == "__main__":
    main()
