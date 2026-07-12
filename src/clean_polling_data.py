"""
Cleans and normalises the raw poll tables scraped by scrape_polling_wikipedia.py.

Strategy: melt each table into LONG format (one row per poll per party) rather
than forcing identical wide columns across decades -- parties enter and exit
over time (e.g. Brexit Party existed only for the 2019 UK cycle), so a rigid
wide schema would either drop data or require constant manual updates.

Filtering logic (a table is kept as "genuine national polling data" only if):
  - It has a recognisable date-like first column
  - It has at least 2 columns that look like party vote-share percentages
  - Its Area/region column (if present) indicates national-level coverage
    (UK/GB/National/Nationwide) rather than a sub-national region
  - It has a reasonable number of rows (>= 3) -- excludes stray small tables

This is a first pass -- it intentionally keeps genuinely ambiguous tables
(logged, not silently dropped) so they can be manually reviewed rather than
silently lost.
"""
import pandas as pd
import glob
import re
import os
from date_parser import parse_poll_date

RAW_DIR = "data/polling_raw"
OUT_DIR = "data/polling_clean"

NATIONAL_AREA_VALUES = {"uk", "gb", "national", "nationwide", "great britain", "aus", "australia", "can", "canada"}

# Columns that are metadata, not party vote shares -- everything else in a
# kept table is treated as a candidate party column.
NON_PARTY_COLS = {
    "date(s) conducted", "date", "pollster/client(s)", "pollster", "area",
    "sample size", "lead", "others", "client", "fieldwork date",
    "polling firm", "firm", "region", "notes", "unnamed",
}

# Explicit known-party whitelist per country. Percentage-shaped values alone
# are NOT a reliable signal for "this column is a party" -- leader-approval
# tables (e.g. "David Cameron", "Jeremy Corbyn") and malformed merged headers
# (e.g. Australia's "2PP vote"/"2PP vote.1" from a flattened two-party-
# -preferred header) also produce percentage-shaped values and were wrongly
# accepted by an earlier version of this script. Only columns matching one
# of these known party labels (after stripping duplicate-suffixes like
# ".1"/"[a]") are treated as genuine party vote-share columns.
CANONICAL_PARTY = {
    "uk": {
        "con": "CON", "conservative": "CON",
        "lab": "LAB", "labour": "LAB",
        "ld": "LD", "lib dem": "LD", "libdem": "LD",
        "snp": "SNP", "pc": "PC", "plaid cymru": "PC",
        "ukip": "UKIP", "brx": "BRX", "brexit": "BRX",
        "grn": "GRN", "green": "GRN",
        "chg": "CHG", "change": "CHG",
        "bnp": "BNP", "bgpv": "BGPV", "dup": "DUP", "gpni": "GPNI",
        "reform": "REFORM", "sf": "SF", "sinn fein": "SF",
        "sdlp": "SDLP", "uup": "UUP", "alliance": "ALLIANCE",
    },
    "canada": {
        "cpc": "CPC", "con": "CPC", "conservative": "CPC",
        "lpc": "LPC", "lib": "LPC", "liberal": "LPC",
        "ndp": "NDP",
        "bq": "BQ", "bloc": "BQ",
        "gpc": "GPC", "grn": "GPC", "green": "GPC",
        "ppc": "PPC", "pc": "PC", "other": "OTHER",
    },
    "australia": {
        "alp": "ALP", "labor": "ALP", "labour": "ALP",
        "l/np": "L/NP", "coalition": "L/NP", "lnp": "L/NP", "lib/nat": "L/NP",
        "lib": "LIB", "liberal": "LIB",
        "nat": "NAT", "national": "NAT", "nationals": "NAT",
        "grn": "GRN", "greens": "GRN",
        "on": "ONP", "onp": "ONP", "one nation": "ONP",
        "uap": "UAP", "other": "OTHER", "oth": "OTHER",
    },
}
# Backwards-compatible view: the set of recognised variant keys per country,
# used to check "is this a known party column at all" before canonicalising.
KNOWN_PARTIES = {country: set(mapping.keys()) for country, mapping in CANONICAL_PARTY.items()}

def clean_party_label(raw_label):
    """Strip pandas duplicate-column suffixes, citation markers, and any
    metric-type tag (e.g. "(2PP)"/"(Primary)") so a column can be matched
    against the known-party whitelist."""
    s = str(raw_label).strip().lower()
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)  # trailing "(2PP)", "(Primary)" metric tags
    s = re.sub(r"\.\d+$", "", s)        # trailing ".1", ".2" from pandas dedup
    s = re.sub(r"\[[a-z0-9]+\]$", "", s)  # trailing "[a]", "[aa]" citation markers
    return s.strip()

def is_known_party_column(col_name, country):
    cleaned = clean_party_label(col_name)
    return cleaned in KNOWN_PARTIES.get(country, set())

def base_col_name(c):
    """Strip pandas' auto-dedup ".1"/".2" suffix to recover the original
    (possibly duplicated) top-level column name before disambiguation."""
    return re.sub(r"\.\d+$", "", str(c)).strip()

def metric_tag_for(base_name):
    """Maps a flattened top-level header (e.g. "TPP vote", "Primary vote")
    to a short tag used to disambiguate harvested party names that would
    otherwise collide (e.g. Australia's "ALP" appears under BOTH the Primary
    vote group and the TPP vote group in the same table -- these are
    different metrics and must not be merged under one party label)."""
    b = base_name.lower()
    if "2pp" in b or "tpp" in b or "two party" in b or "two-party" in b:
        return "2PP"
    if "primary" in b or "first pref" in b or "political parties" in b:
        return "Primary"
    return None

def harvest_subheader_labels(df):
    """Wikipedia often encodes a genuinely two-level header (e.g. a top row
    "Primary vote" spanning 5 sub-columns "L/NP, ALP, GRN, ONP, OTH") that
    pandas.read_html flattens into a single header row, demoting the real
    sub-labels into what looks like a garbage first data row (mixed with
    "Unnamed: N_level_1" placeholders for columns that only had one level).
    Rather than discarding that row as junk (which loses the real party
    names entirely), harvest its real-looking values as the true column
    names -- tagging them with the top-level group name where that group is
    duplicated across the table (e.g. "ALP (Primary)" vs "ALP (2PP)"), since
    those are genuinely different metrics that must not collide."""
    if len(df) == 0:
        return df
    row0 = df.iloc[0]
    base_names = [base_col_name(c) for c in df.columns]
    base_counts = {}
    for b in base_names:
        base_counts[b] = base_counts.get(b, 0) + 1

    new_cols = list(df.columns)
    harvested_any = False
    for i, col in enumerate(df.columns):
        val = str(row0.iloc[i]).strip()
        val_lower = val.lower()
        is_unnamed = val_lower.startswith("unnamed:") or val_lower in ("nan", "")
        is_duplicated_group = base_counts[base_names[i]] > 1
        if not is_unnamed and is_duplicated_group and 0 < len(val) <= 25:
            tag = metric_tag_for(base_names[i])
            new_cols[i] = f"{val} ({tag})" if tag else val
            harvested_any = True

    if harvested_any:
        df = df.iloc[1:].reset_index(drop=True)
        # Guarantee uniqueness: two harvested labels can collide (e.g. two
        # duplicated groups that happen to share a sub-label), and pandas
        # silently allows duplicate column names -- df[some_dupe_name] then
        # returns a DataFrame instead of a Series and breaks every .str
        # accessor downstream. Dedup exactly like pandas' own CSV reader
        # does (append ".1", ".2", ...) so this can never happen.
        seen = {}
        deduped_cols = []
        for c in new_cols:
            if c not in seen:
                seen[c] = 0
                deduped_cols.append(c)
            else:
                seen[c] += 1
                deduped_cols.append(f"{c}.{seen[c]}")
        df.columns = deduped_cols
    return df

def looks_like_date_column(series, election_year):
    """Uses the actual, already-tested date parser as ground truth rather
    than a separate loose heuristic -- a prior looser regex (matching any
    string containing a 1-2 digit number OR a month-name substring) wrongly
    accepted organisation names with citation markers like "Election
    Forecast[5]" as looking like dates, since "[5]" contains a digit. If a
    column's values don't actually parse as real dates, it isn't one."""
    sample = series.dropna().astype(str).head(15)
    if len(sample) == 0:
        return False
    parsed = sample.apply(lambda v: parse_poll_date(v, election_year) is not None)
    return parsed.mean() > 0.5

def looks_like_pct_column(series):
    if not isinstance(series, pd.Series):
        # Defensive: a duplicate column name would make df[c] return a
        # DataFrame instead of a Series here. Treat as "not a party column"
        # rather than crashing -- the underlying cause should already be
        # prevented by the dedup step in harvest_subheader_labels, but this
        # guards against any other path producing the same situation.
        return False
    sample = series.dropna().astype(str).head(15)
    pct_pattern = re.compile(r"^\s*\d{1,2}(\.\d+)?\s*%?\s*$")
    return sample.str.match(pct_pattern).mean() > 0.5

def clean_pct(val):
    if pd.isna(val):
        return None
    s = str(val).strip().replace("%", "")
    s = s.replace("\u2013", "").replace("\u2014", "")  # stray dashes used for "no data"
    try:
        return float(s)
    except ValueError:
        return None

def fix_encoding_artifacts(text):
    if not isinstance(text, str):
        return text
    # Common mis-decoded en-dash / em-dash sequences seen in the raw scrape
    return text.replace("â€“", "\u2013").replace("â€”", "\u2014").replace("â€™", "'")

def process_file(filepath, country, year):
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return None, f"read error: {e}"

    if len(df) < 3 or len(df.columns) < 4:
        return None, "too small"

    # Seat-count/projection tables (e.g. MRP seat tallies: "94 seats") use
    # bare 1-2 digit numbers that are structurally indistinguishable from
    # percentages by looks_like_pct_column() alone (that check doesn't
    # require a literal "%" sign, since plenty of genuine percentage columns
    # in these tables also omit it). Seat counts are NOT vote-share data --
    # exclude any table whose header mentions "seat" before it ever reaches
    # party-column detection, rather than risk silently treating a seat
    # count as a vote percentage.
    if any("seat" in str(c).lower() for c in df.columns):
        return None, "seat-count/projection table, not vote-share data"

    # First, recover any real party names hiding in a flattened sub-header
    # row (e.g. Australia's Primary/TPP vote tables) before anything else
    # gets a chance to discard that row as junk.
    df = harvest_subheader_labels(df)
    if len(df) < 3:
        return None, "too small after subheader harvest"

    # pandas.read_html sometimes flattens a genuinely multi-level header
    # into a single header row PLUS a leftover junk row that just repeats
    # the column names as if they were data. Drop any leading rows that
    # match this pattern, or the date-column check below will reject an
    # otherwise perfectly good table.
    col_names_lower = set(str(c).lower().strip() for c in df.columns)
    while len(df) > 0:
        first_row_vals = set(str(v).lower().strip() for v in df.iloc[0].tolist())
        overlap = len(first_row_vals & col_names_lower)
        has_unnamed = df.iloc[0].astype(str).str.contains("unnamed:", case=False).any()
        if overlap >= 2 or has_unnamed:
            df = df.iloc[1:].reset_index(drop=True)
        else:
            break

    if len(df) < 3:
        return None, "too small after junk-row removal"

    cols_lower = [str(c).lower().strip() for c in df.columns]

    # Find the date column BY NAME rather than assuming it's always column 0
    # -- some tables (e.g. Canadian polling tables) put the pollster/firm
    # name first and the date second.
    date_col = next((c for c, cl in zip(df.columns, cols_lower) if "date" in cl), df.columns[0])
    if not looks_like_date_column(df[date_col], year):
        return None, "no column looks like dates"

    # Identify area column if present, filter to national-level rows only
    area_col = None
    for c, cl in zip(df.columns, cols_lower):
        if cl == "area" or cl == "region":
            area_col = c
            break
    if area_col is not None:
        df = df[df[area_col].astype(str).str.lower().str.strip().isin(NATIONAL_AREA_VALUES)]
        if len(df) == 0:
            return None, "no national-level rows after area filter"

    # Identify party columns using the known-party whitelist, not just
    # "values look like percentages" (which also matches candidate-approval
    # ratings and malformed merged headers -- see module docstring).
    party_cols = []
    for c, cl in zip(df.columns, cols_lower):
        if any(non_party in cl for non_party in NON_PARTY_COLS):
            continue
        if not looks_like_pct_column(df[c]):
            continue
        if is_known_party_column(c, country):
            party_cols.append(c)

    if len(party_cols) < 2:
        return None, f"fewer than 2 recognised party columns found (got {len(party_cols)})"

    pollster_col = next((c for c, cl in zip(df.columns, cols_lower) if "pollster" in cl or "client" in cl or "firm" in cl), None)
    sample_col = next((c for c, cl in zip(df.columns, cols_lower) if "sample" in cl), None)

    id_vars = [date_col]
    if pollster_col:
        id_vars.append(pollster_col)
    if sample_col:
        id_vars.append(sample_col)

    long_df = df.melt(id_vars=id_vars, value_vars=party_cols, var_name="party", value_name="pct_raw")
    # Collapse duplicate-suffixed variants of the same party (e.g. "LD" and
    # "LD.1" both appearing in one table) down to one canonical label --
    # otherwise pandas' auto-dedup suffixes fragment a single party into
    # multiple distinct "party" values in the output. The synthetic
    # "ALP (2PP)"/"Coalition (2PP)" labels assigned above for Australia are
    # already canonical and left untouched.
    def to_canonical(base):
        cleaned = clean_party_label(base)
        return CANONICAL_PARTY.get(country, {}).get(cleaned, cleaned.upper())

    def canonicalise(p):
        p_str = str(p)
        m = re.match(r"^(.*?)\s*(\([^)]*\))\s*$", p_str)
        if m:
            # has a metric tag like "(2PP)" or "(Primary)" -- canonicalise
            # just the party portion and re-attach the tag
            base, tag = m.group(1), m.group(2)
            return f"{to_canonical(base)} {tag}"
        return to_canonical(p_str)
    long_df["party"] = long_df["party"].apply(canonicalise)
    long_df["pct"] = long_df["pct_raw"].apply(clean_pct)
    long_df = long_df.dropna(subset=["pct"])
    long_df = long_df.rename(columns={date_col: "date_raw"})
    if pollster_col:
        long_df = long_df.rename(columns={pollster_col: "pollster"})
    else:
        long_df["pollster"] = None
    if sample_col:
        long_df = long_df.rename(columns={sample_col: "sample_size"})
    else:
        long_df["sample_size"] = None

    for col in ["date_raw", "pollster", "party"]:
        long_df[col] = long_df[col].apply(fix_encoding_artifacts)

    long_df["country"] = country
    long_df["election_year"] = year
    long_df["source_table"] = os.path.basename(filepath)

    return long_df[["country", "election_year", "date_raw", "pollster", "sample_size", "party", "pct", "source_table"]], "ok"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = glob.glob(f"{RAW_DIR}/*.csv")
    print(f"Found {len(files)} raw table files")

    results = {"uk": [], "canada": [], "australia": []}
    kept, skipped = 0, 0
    skip_reasons = {}

    for filepath in files:
        fname = os.path.basename(filepath)
        m = re.match(r"(uk|canada|australia)_(\d{4})_table\d+\.csv", fname)
        if not m:
            continue
        country, year = m.group(1), int(m.group(2))

        long_df, status = process_file(filepath, country, year)
        if long_df is not None and len(long_df) > 0:
            results[country].append(long_df)
            kept += 1
        else:
            skipped += 1
            skip_reasons[status] = skip_reasons.get(status, 0) + 1

    print(f"\nKept {kept} tables as genuine national polling data, skipped {skipped}")
    print("Skip reasons:", skip_reasons)

    for country, dfs in results.items():
        if not dfs:
            print(f"\n{country}: no usable tables found")
            continue
        combined = pd.concat(dfs, ignore_index=True)
        combined = combined.drop_duplicates()
        out_path = f"{OUT_DIR}/{country}_polls_clean.csv"
        combined.to_csv(out_path, index=False)
        print(f"\n{country}: {len(combined)} poll-party rows across {combined['election_year'].nunique()} election cycles")
        print(f"  Saved to {out_path}")
        print(f"  Parties found: {sorted(combined['party'].unique())[:15]}")

if __name__ == "__main__":
    main()
