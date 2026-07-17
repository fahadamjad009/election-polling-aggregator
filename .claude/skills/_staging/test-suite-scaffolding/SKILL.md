---
name: test-suite-scaffolding
description: Use when adding a first test suite to a fahadamjad009 repo that has none, or when a repo's tests are decorative (exist but assert nothing meaningful). Priority targets from the 2026-07-16 audit — grid-demand-forecaster, fintech-fraud-detection-platform, nyc-taxi-azure-platform, customer-churn-ml-benchmark. Trigger condition: a data/ML repo with working pipeline code but no tests/ directory, or a request to "add tests" / "harden" a repo.
---

# Test Suite Scaffolding (data-invariant pattern)

Encodes Master Standard Section 10 (testing stack; decorative testing is a
named anti-pattern) using the real, working template:
`election-polling-aggregator/tests/test_data_invariants.py` — a 10-test
`unittest` suite over the pipeline's committed output artifacts.

The template's four test families, with the real examples:

1. **Required-output tests** — the pipeline's key artifacts exist and are
   complete: `test_required_prediction_fields_are_complete` asserts no NaN in
   the 8 columns downstream code needs; `test_expected_row_counts` pins exact
   sizes (68 full / 43 dev / 25 holdout) so silent data loss fails loudly.
2. **Split-integrity tests** — `test_development_holdout_do_not_overlap`
   builds tuple-sets of (country, election_year) per split and asserts
   `isdisjoint`; `test_split_labels_are_correct` asserts each file contains
   only its own label; `test_holdout_lock_exists` asserts the lock file exists
   AND still contains its warning text ("Do not retune").
3. **Scope-control tests** — the data means what the docs say it means:
   `test_australia_uses_tpp_labels` asserts the Australia rows are exactly
   the two 2PP labels; `test_one_actual_winner_per_election` asserts the
   is_winner sum is exactly 1 per election group.
4. **Leakage-boundary tests** — `test_last_poll_is_not_after_election`
   asserts no feature-source date exceeds the outcome date.

## When NOT to use

- Repos that already have a real suite — extend it in its own style instead.
- Class A exploratory notebooks (Section 2): controls scale with class; a
  throwaway EDA notebook does not need a suite. Anything PUBLIC is Class B
  minimum and does.
- As a substitute for fixing broken pipeline code. Scaffold tests against a
  pipeline that currently runs; if it doesn't run, fix that first and say so.

## Procedure

1. **Identify the committed output artifacts** (CSVs/parquet the pipeline
   writes) and the 5–10 columns downstream code or the README depends on.
   Test the artifacts, not mocks — this is what makes the suite non-decorative.
2. **Write 10–15 tests** across the four families above. Every test must be
   able to fail: pin exact counts where the data is frozen, exact label sets
   where scope is governed, `isdisjoint` where splits must not leak.
3. **Mirror the template's mechanics**: `unittest.TestCase`, artifacts loaded
   once in `setUpClass`, paths built from
   `ROOT = Path(__file__).resolve().parents[1]` so the suite runs from any cwd.
4. **Prove each test can fail** for at least the load-bearing ones: perturb a
   copy of the artifact (drop a row, blank a cell, move a date past the
   boundary) and confirm the test catches it. A test never seen red is
   decorative until proven otherwise.
5. **Run the suite in a clean state** and paste the real output.
6. **Wire into CI** if the repo has a workflow; if it has none, add a minimal
   one that installs the curated requirements and runs the suite (see
   election-polling-aggregator/.github/workflows/ci.yml as reference). A CI
   badge must point at a workflow that actually runs (Section 22).
7. **Update the README's testing section** — through `claim-verification-gate`:
   state the real test count and the real command.

## Commands

```bash
mkdir -p tests
python -m unittest discover tests -v      # template repo uses unittest
python -m unittest discover tests -v 2>&1 | tail -5   # paste this in report
grep -c "def test_" tests/*.py
```

## Quality bar

10–15 tests, all four families represented, every count/label assertion pinned
to a value you read from the actual artifact (state where you read it), suite
green in a clean run, and at least the split-integrity and leakage-boundary
tests demonstrated to fail on perturbed data.

## Verification checklist

- [ ] Tests load the repo's real committed artifacts, not fixtures invented
      for the test.
- [ ] Exact-count assertions match the current artifacts (run, don't infer).
- [ ] Split disjointness tested on natural-unit keys, not row indices.
- [ ] Temporal boundary test present if the repo has any time-ordered target.
- [ ] Full suite output pasted, showing N tests, OK.
- [ ] Failure demonstration performed for ≥2 tests and reverted cleanly.
- [ ] README/CI updated to reflect the real suite (no aspirational counts).

## Common mistakes

- Decorative tests: `assertTrue(True)`, testing that pandas can read a CSV,
  or asserting `len(df) > 0` when the real invariant is `len(df) == 68`.
- Testing functions with hand-made toy inputs while the committed artifacts —
  the thing that actually feeds the app and README numbers — go unchecked.
- Copying election-polling-aggregator's specific numbers (68/43/25) into
  another repo's tests instead of deriving that repo's own invariants.
- Adding pytest as a dependency when unittest suffices, then blind-freezing
  it into requirements.txt (Section 10: curate imports, never `pip freeze`).
- Writing the CI badge before the workflow exists or passes.

## What to report back

- Test inventory: name → family → invariant it pins.
- The clean-run output (real paste).
- Which tests were failure-demonstrated and how.
- Invariants you wanted to pin but couldn't verify (unknown expected value) —
  listed as open items, not silently skipped.

