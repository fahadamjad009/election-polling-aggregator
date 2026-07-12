"""
Normalises the inconsistent raw date strings found across all scraped
polling sources into real datetime objects. Real formats observed in the
data so far (not hypothetical -- each pattern below was seen in an actual
downloaded file this session):

  "12 Dec 2019"           -- UK, single-day poll
  "10-11 Dec"             -- UK, date range within a year implied by context,
                              en-dash separated (year must come from the
                              election_year column since it's not in the string)
  "October 21, 2019"      -- Canada, US-style long format
  "7-8 Aug 2010"          -- Australia, date range with year
  "18 May 2019 election"  -- Australia, the actual election result row
                              (trailing "election" marker, not a poll)

Strategy: for a range like "10-11 Dec", we take the LATER date (end of
fieldwork) since that's the more meaningful "as-of" date for a poll -- it's
the closest point to when opinion was actually measured.
"""
import pandas as pd
import re
from datetime import datetime

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

import calendar

def safe_date(year, month, day):
    """Constructs a date, clamping the day to the last valid day of the
    month if it's out of range (e.g. "29 Feb" in a non-leap year, or a
    31st in a 30-day month) rather than discarding the row entirely --
    a small precision loss that preserves far more real data than a hard
    failure would."""
    last_day = calendar.monthrange(year, month)[1]
    day = min(day, last_day)
    return datetime(year, month, day).date()

RESULT_MARKER_PATTERN = re.compile(r"election|voting result", re.I)

def strip_noise(s):
    """Strips citation markers like "[3]"/"[a]" and leading qualifier words
    like "Early"/"Late"/"Mid"/"Pre-" that don't affect the actual date."""
    s = re.sub(r"\[[a-z0-9]+\]", "", s, flags=re.I)
    s = re.sub(r"^(early|late|mid)\s+", "", s, flags=re.I)
    s = re.sub(r"^pre-?\s*", "", s, flags=re.I)
    return s.strip()

def parse_poll_date(date_raw, election_year, election_month=None):
    """Returns a datetime.date, or None if unparseable. election_year is
    used as a fallback when the raw string has no year of its own (the
    common case for mid-cycle date ranges like "10-11 Dec")."""
    if pd.isna(date_raw):
        return None
    s = str(date_raw).strip()
    if RESULT_MARKER_PATTERN.search(s):
        s = RESULT_MARKER_PATTERN.sub("", s).strip()
        if s == "" or re.match(r"^\d{4}$", s):
            return None  # e.g. "Election", "2007 election" with nothing else useful

    s = strip_noise(s)
    if s == "":
        return None

    # Pattern: "3/3/2016" or "10/1/2012" (numeric M/D/YYYY, US convention --
    # FiveThirtyEight's modeldate column uses this format specifically).
    # Checked BEFORE the "/"-range-splitting logic below, since a complete
    # numeric date must not be treated as a multi-window range poll.
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        month, day, year = m.groups()
        month = int(month)
        if 1 <= month <= 12:
            try:
                return safe_date(int(year), month, int(day))
            except ValueError:
                return None

    # Pattern: "16-17/23-24 Feb 2013" or "24-25 Nov/1-2 Dec 2012" -- a poll
    # spanning two separate fieldwork windows, joined by "/". Take the
    # LATER of the two windows (consistent with the existing convention of
    # using the end/most-recent date for any range), then parse that
    # window with the normal patterns below by discarding everything
    # before the "/".
    if "/" in s:
        s = s.split("/")[-1].strip()
        # the trailing part after "/" may be missing its own year/month if
        # the full date only appeared once at the very end of the original
        # string (e.g. "24-25 Nov/1-2 Dec 2012" -> "1-2 Dec 2012", which
        # already has everything it needs) -- no special-casing needed,
        # it just falls through to the patterns below

    # Normalise all dash variants (en-dash, em-dash, hyphen) to " - " with
    # consistent spacing, so range patterns below don't need to handle every
    # possible spacing/dash-character combination separately.
    s = re.sub(r"\s*[\u2013\u2014-]\s*", "-", s)

    # Pattern: "October 21, 2019" (long month name, US-style)
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$", s)
    if m:
        month_name, day, year = m.groups()
        month = MONTH_MAP.get(month_name.lower()[:3])
        if month:
            try:
                return safe_date(int(year), month, int(day))
            except ValueError:
                return None

    # Pattern: "12 Dec 2019" (day month year)
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        day, month_name, year = m.groups()
        month = MONTH_MAP.get(month_name.lower()[:3])
        if month:
            try:
                return safe_date(int(year), month, int(day))
            except ValueError:
                return None

    # Pattern: "30 Dec 1998-3 Jan 1999" (cross-year, cross-month day range --
    # two different years explicitly given, take the later date)
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})-(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        _, _, _, day2, month2_name, year2 = m.groups()
        month = MONTH_MAP.get(month2_name.lower()[:3])
        if month:
            try:
                return safe_date(int(year2), month, int(day2))
            except ValueError:
                return None

    # Pattern: "30 Jul-1 Aug 2010" (cross-month day range WITH year -- two
    # different month names, take the later date)
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)-(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        _, _, day2, month2_name, year = m.groups()
        month = MONTH_MAP.get(month2_name.lower()[:3])
        if month:
            try:
                return safe_date(int(year), month, int(day2))
            except ValueError:
                return None

    # Pattern: "7-8 Aug 2010" (same-month day range WITH year)
    m = re.match(r"^(\d{1,2})-(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        _, day2, month_name, year = m.groups()
        month = MONTH_MAP.get(month_name.lower()[:3])
        if month:
            try:
                return safe_date(int(year), month, int(day2))
            except ValueError:
                return None

    # Pattern: "31 May-2 Jun" (cross-month day range, NO year -- use
    # election_year with rollback if the END month is later than the
    # election month, since this is almost always pre-election polling)
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)-(\d{1,2})\s+([A-Za-z]+)$", s)
    if m:
        _, _, day2, month2_name = m.groups()
        month = MONTH_MAP.get(month2_name.lower()[:3])
        if month and election_year:
            year = election_year
            if election_month and month > election_month:
                year -= 1
            try:
                return safe_date(int(year), month, int(day2))
            except ValueError:
                return None

    # Pattern: "10-11 Dec" (same-month day range, NO year)
    m = re.match(r"^(\d{1,2})-(\d{1,2})\s+([A-Za-z]+)$", s)
    if m:
        _, day2, month_name = m.groups()
        month = MONTH_MAP.get(month_name.lower()[:3])
        if month and election_year:
            year = election_year
            if election_month and month > election_month:
                year -= 1
            try:
                return safe_date(int(year), month, int(day2))
            except ValueError:
                return None

    # Pattern: "12 Dec" (single day, month, NO year)
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)$", s)
    if m:
        day, month_name = m.groups()
        month = MONTH_MAP.get(month_name.lower()[:3])
        if month and election_year:
            year = election_year
            if election_month and month > election_month:
                year -= 1
            try:
                return safe_date(int(year), month, int(day))
            except ValueError:
                return None

    # Pattern: "April 2002" (month + year, no day -- use day 1 as a
    # documented approximation; precision loss is real but the alternative
    # is discarding the row entirely, which loses more information)
    m = re.match(r"^([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        month_name, year = m.groups()
        month = MONTH_MAP.get(month_name.lower()[:3])
        if month:
            try:
                return safe_date(int(year), month, 1)
            except ValueError:
                return None

    # Pattern: "May-Jun 2004" (month range + year, no days -- take the
    # later month, day 1 as approximation)
    m = re.match(r"^([A-Za-z]+)-([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        _, month2_name, year = m.groups()
        month = MONTH_MAP.get(month2_name.lower()[:3])
        if month:
            try:
                return safe_date(int(year), month, 1)
            except ValueError:
                return None

    # Pattern: "May" (month only, no day, no year -- use election_year with
    # rollback, day 1 as approximation)
    m = re.match(r"^([A-Za-z]+)$", s)
    if m:
        month_name = m.group(1)
        month = MONTH_MAP.get(month_name.lower()[:3])
        if month and election_year:
            year = election_year
            if election_month and month > election_month:
                year -= 1
            try:
                return safe_date(int(year), month, 1)
            except ValueError:
                return None

    return None

def add_parsed_dates(df, election_month_by_country_year=None):
    """Adds a 'poll_date' column (real date objects) and 'is_election_result'
    flag to a cleaned polling dataframe. election_month_by_country_year is an
    optional dict {(country, year): month_int} used to correctly roll back
    the year for month-only date ranges that span a year boundary -- if not
    provided, no rollback is attempted (safe default, may misdate a few
    December-polls-for-a-following-May-election cases)."""
    df = df.copy()
    df["is_election_result"] = df["date_raw"].astype(str).str.contains(RESULT_MARKER_PATTERN)

    def _parse_row(row):
        month = None
        if election_month_by_country_year:
            month = election_month_by_country_year.get((row["country"], row["election_year"]))
        return parse_poll_date(row["date_raw"], row["election_year"], month)

    df["poll_date"] = df.apply(_parse_row, axis=1)
    return df

def diagnose_real_data():
    """Run against the actual cleaned polling CSVs and report the real
    parse success rate, plus examples of anything that failed to parse --
    so any date format not covered above gets caught and fixed before the
    rest of the pipeline is built on top of this."""
    import glob
    for path in glob.glob("data/polling_clean/*_polls_clean.csv"):
        df = pd.read_csv(path)
        df = add_parsed_dates(df)
        total = len(df)
        parsed = df["poll_date"].notna().sum()
        failed = df[df["poll_date"].isna()]
        print(f"\n{path}: {parsed}/{total} parsed ({parsed/total*100:.1f}%)")
        if len(failed) > 0:
            print(f"  {len(failed)} unparsed. Sample of unique unparsed date_raw values:")
            for val in failed["date_raw"].drop_duplicates().head(10):
                print(f"    {val!r}")

if __name__ == "__main__":
    # Self-test against the exact real date formats seen this session
    test_cases = [
        ("12 Dec 2019", 2019, None, datetime(2019, 12, 12).date()),
        ("10-11 Dec", 2019, 12, datetime(2019, 12, 11).date()),
        ("October 21, 2019", 2019, None, datetime(2019, 10, 21).date()),
        ("7-8 Aug 2010", 2010, None, datetime(2010, 8, 8).date()),
        ("18 May 2019 election", 2019, None, datetime(2019, 5, 18).date()),
        # newly discovered real formats from the actual production run
        ("30 Jul \u2013 1 Aug 2010", 2010, None, datetime(2010, 8, 1).date()),
        ("30 Apr-2 May 2010", 2010, None, datetime(2010, 5, 2).date()),
        ("2 \u2013 4 Oct 2009[3]", 2009, None, datetime(2009, 10, 4).date()),
        ("Election", 2019, None, None),
        ("2007 election", 2007, None, None),
        ("Election 2000", 2000, None, None),
        ("Voting result", 2019, None, None),
        ("Voting result[4]", 2019, None, None),
        ("April 2002", 2002, None, datetime(2002, 4, 1).date()),
        ("Early Apr 1993[a]", 1993, None, datetime(1993, 4, 1).date()),
        ("31 May \u2013 2 Jun", 2019, 6, datetime(2019, 6, 2).date()),
        ("17 Feb \u2013 13 Mar", 2019, 3, datetime(2019, 3, 13).date()),
        ("30 Dec 1998 \u2013 3 Jan 1999", 1999, None, datetime(1999, 1, 3).date()),
        ("May\u2013Jun 2004", 2004, None, datetime(2004, 6, 1).date()),
        ("Early May", 2019, 6, datetime(2019, 5, 1).date()),
        ("Pre-23 Apr", 2019, 4, datetime(2019, 4, 23).date()),
        ("28\u201329 Feb", 2019, 5, datetime(2019, 2, 28).date()),  # 2019 not a leap year -> clamped to 28
    ]
    print("Running self-test against real observed date formats...")
    all_passed = True
    for raw, year, month, expected in test_cases:
        result = parse_poll_date(raw, year, month)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"  [{status}] parse_poll_date({raw!r}, {year}, {month}) = {result} (expected {expected})")
    print("\nAll tests passed!" if all_passed else "\nSOME TESTS FAILED -- do not use until fixed.")

    import os
    if os.path.isdir("data/polling_clean"):
        print("\n" + "=" * 60)
        print("Checking real parse rate against actual cleaned data...")
        diagnose_real_data()
