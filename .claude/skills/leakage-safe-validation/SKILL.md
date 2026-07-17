---
name: leakage-safe-validation
description: Use whenever building or modifying a train/test split, holdout set, evaluation, feature pipeline, or any pandas merge/filter/join on key columns in a fahadamjad009 ML repo. Trigger condition: code touches dataset splitting, holdout evaluation, feature construction from raw data, or equality-based joins between dataframes from different sources.
---

# Leakage-Safe Validation

Encodes Master Standard Section 6 (leakage checklist) and Section 8 (split
strategy), plus one bug class that hit this portfolio TWICE and is therefore
promoted to a mandatory pre-join check.

Reference implementation: `election-polling-aggregator` —
`src/build_train_test_split.py`, `data/splits/{development,holdout}_elections.csv`,
`data/model/final_holdout/HOLDOUT_EVALUATED.lock`, and
`tests/test_data_invariants.py` (the executable form of these rules).

## The two confirmed portfolio bug classes

**1. Silent dtype mismatch on join/filter keys.** `election_year` arrived as
int64 in one dataframe and object/str in another; plain `==` comparison and
merge silently returned ZERO matches instead of erroring. No exception, no
warning, empty output downstream. Found and independently fixed in BOTH
`src/build_pollster_reliability.py` (lines 62–71) and
`src/build_similar_elections.py` (lines 44–53). The fix pattern, verbatim
from the repo:

```python
polls_df["election_year"] = pd.to_numeric(polls_df["election_year"], errors="coerce").astype("Int64")
actuals_df["election_year"] = pd.to_numeric(actuals_df["election_year"], errors="coerce").astype("Int64")
polls_df = polls_df.dropna(subset=["election_year"])
actuals_df = actuals_df.dropna(subset=["election_year"])
```

**2. Result-marker rows treated as real data** (Section 6). Scraped tables
embed election-result rows among polls; if not excluded they leak the answer
into features. The exclusion regex
(`re.compile(r"election|voting result|by-election", re.I)`) was COPY-PASTED
into both `src/build_pollster_reliability.py:24` and `src/run_eda.py:30` and
bug-fixed separately in each — duplicated logic, duplicated drift risk. The
copy in `build_pollster_reliability.py` even carries a comment claiming it is
"Reused directly from date_parser.py's RESULT_MARKER_PATTERN rather than
re-defining a second, possibly-divergent copy" — immediately above a line that
re-defines exactly such a copy. Rule: exclusion logic for a marker class lives
in ONE shared module and is IMPORTED (`from date_parser import
RESULT_MARKER_PATTERN`); a comment promising reuse is not reuse.

## When NOT to use

- Non-ML repos with no train/eval distinction.
- Single-dataframe transformations with no join, no filter on a key shared
  across sources, and no split (though the dtype check still applies to any
  cross-source equality).
- Visualization-only code consuming an already-validated model dataset.

## Procedure

1. **Split on natural units and time boundaries** (Section 8). The unit is
   the thing that must not straddle splits — an election (country, year), a
   customer, a day — never the row. Chronological holdout: everything after
   the boundary date is holdout, no cherry-picking. Persist the assignment as
   committed artifacts (the `data/splits/*.csv` pattern), don't recompute it
   per run with a seed.
2. **Freeze the holdout with a lock file.** After the ONE final evaluation,
   write a lock file next to the holdout artifacts stating what was evaluated
   and "Do not retune or repeatedly inspect this set" (verbatim pattern:
   `data/model/final_holdout/HOLDOUT_EVALUATED.lock`). A test must assert the
   lock exists and retains its warning text
   (`test_holdout_lock_exists` in the template suite).
3. **No repeated holdout inspection** (Section 6). If the lock exists, the
   holdout is spent: do not re-run evaluation on it after changing features
   or models, do not look at per-row holdout errors to guide development.
   All iteration happens on the development split (leave-one-unit-out or
   similar). If someone asks you to re-evaluate a locked holdout, stop and
   surface the lock instead of complying.
4. **No target-derived features.** For each feature, ask: could this column
   be computed before the outcome existed? Dates help enforce this
   mechanically — assert feature-source dates precede the outcome date
   (`test_last_poll_is_not_after_election` pattern: `last_poll_date <=
   election_date` for every row).
5. **Exclude result-marker rows once, in one place.** Import the shared
   exclusion function; if the repo doesn't have one yet, create it in the
   shared module and refactor any existing copies to import it.
6. **Dtype-check before EVERY equality-based join or filter.** Before
   `merge`, `==` filtering, `isin`, or `groupby` on keys from different
   sources: print/compare `df.dtypes[key_cols]` on both sides; coerce with
   the `pd.to_numeric(...).astype("Int64")` pattern above (or explicit `str`
   normalization for string keys); then **assert the result is non-empty**:

   ```python
   merged = polls_df.merge(actuals_df, on=["country", "election_year", "party"], how="inner")
   assert len(merged) > 0, "join produced zero rows - check key dtypes and values"
   ```

   The zero-match failure is silent by construction; the assert makes it loud.
7. **Pin the invariants in tests.** Split disjointness (`isdisjoint` on
   natural-unit tuples), split labels, exact counts, temporal boundary, lock
   existence — see `test-suite-scaffolding` for the full pattern.

## Commands

```bash
python -m unittest discover tests -v          # invariant suite must stay green
ls data/splits/ data/model/final_holdout/     # split artifacts + lock present
grep -rn "RESULT_MARKER\|result_marker" src/ | cut -d: -f1 | sort -u   # must be 1 defining module
python - <<'EOF'
import pandas as pd
a = pd.read_csv("data/model/development_model_dataset.csv")
b = pd.read_csv("data/model/holdout_model_dataset.csv")
print(a.dtypes[["country","election_year"]], b.dtypes[["country","election_year"]], sep="\n")
EOF
```

## Quality bar

Splits are committed artifacts on natural units; holdout is locked after one
evaluation; every cross-source join has a dtype coercion and a non-empty
assert; marker exclusion is defined exactly once; all of it is pinned by
tests that would fail if violated.

## Verification checklist

- [ ] Split unit is a natural unit, stated explicitly.
- [ ] Split assignment committed as an artifact, not recomputed per run.
- [ ] Lock file present after final eval, with do-not-retune text, and tested.
- [ ] No code path re-evaluates a locked holdout.
- [ ] Every merge/filter on shared keys: dtypes checked, coerced, result
      asserted non-empty.
- [ ] Marker-exclusion logic defined in exactly one module (grep proves it).
- [ ] Temporal boundary assert exists for every time-ordered target.

## Common mistakes

- Trusting pandas to error on mismatched key dtypes — it doesn't; it returns
  empty results. This is the twice-confirmed portfolio bug. Assert non-empty.
- Fixing a shared-logic bug in one copy and not knowing a second copy exists
  (grep for the pattern before fixing; refactor to one module while there).
- "Just one more look" at the holdout after changing a feature — that
  converts the holdout into a second development set (Section 6).
- Random row-level splits on data with natural units, letting one election's
  parties land in both splits.
- Writing the lock file but no test for it, so a later script quietly
  regenerates the holdout.

## What to report back

- Split design: unit, boundary, artifact paths.
- Holdout state: locked or not; if you evaluated it, say so — that was the
  one shot.
- Joins touched: keys, coercion applied, non-empty assert added.
- Result of the single-definition grep for marker/exclusion logic.
- Any leakage risk you saw and did NOT fix, named explicitly.

