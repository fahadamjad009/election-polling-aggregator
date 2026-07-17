---
name: claim-verification-gate
description: Use BEFORE writing or editing any README, PROJECT_STATUS.md, portfolio-site project table entry, CV/LinkedIn bullet, or any external text that states a feature, metric, test count, row count, deployment, or completion status for any fahadamjad009 repo. Also use when asked to "update the status", "describe the project", or "summarize what this repo does". Trigger condition: the output will contain a checkable factual claim about a repository.
---

# Claim Verification Gate

Encodes Master Standard Section 1 (core rule: no fake completion, no claim that
cannot be traced to evidence; every claim = evidence + context + limitation +
implication) and Section 11 (claims that cannot be traced to an artifact must be
removed or qualified).

Built from two confirmed portfolio failures (2026-07-16 audit):

- **customer-churn-ml-benchmark**: README/prior descriptions cited SHAP,
  CLV-weighted metrics, decile-lift, and an ROI simulator. None exist in the
  code. No `tests/` directory exists either.
- **bi-financial-kpi-command-centre**: a 2-commit scaffold described elsewhere
  as "Strong tier" with fabricated row counts and test counts — and the false
  "Complete" label propagated to the live portfolio site
  (fahadamjad009.github.io), the first thing a recruiter sees.

## When NOT to use

- Pure code changes with no accompanying prose claims.
- Claims already in the repo that you are not touching and were not asked to
  review (use `master-standard-review-gate` for a full-repo sweep instead).
- Internal scratch notes that will never be published.

## Procedure

For EVERY factual claim in the text you are about to write or approve:

1. **Classify the claim.** Feature ("uses SHAP"), metric ("87.9% accuracy",
   "MAE 1.24pp"), count ("15 tests", "68 rows"), status ("Complete",
   "Deployed"), or artifact ("CI green", "tagged release").
2. **Locate the evidence in the repo — not in prior descriptions.**
   - Feature claim → grep the source for the named library/function. It must
     appear in executed code, not just requirements.txt or a comment.
   - Metric claim → find the script or artifact that produces the number, and
     the committed output (results CSV, evaluation log, README table generated
     from it). A number with no producing artifact is unverifiable.
   - Test-count claim → count actual test functions and confirm they pass.
   - Status claim → check against the repo's own checklist/milestones. A repo
     whose own docs say "Phase 1 scaffold" is not "Complete", ever.
   - Deployment claim → fetch the live URL and confirm it loads.
3. **Check propagation.** If a status/metric appears in one place, search for
   it everywhere it may have been copied: repo README, portfolio site project
   table (fahadamjad009.github.io repo), pinned-repo description,
   PROJECT_STATUS.md. A correction applied in one place and not the other
   recreates the bi-financial-kpi-command-centre failure. Fix ALL locations or
   none, in the same change.
4. **Rewrite unverifiable claims.** Options, in order of preference:
   a. Delete the claim.
   b. Qualify it honestly ("planned", "scaffold only", "unverified figure
      pending re-run").
   c. Build the missing evidence first, then claim it.
   Never leave the claim as-is with a TODO.
5. **Attach the four-part structure** for significant claims: evidence,
   context, limitation, implication (Section 1). "Winner accuracy 87.5% on the
   locked 8-election holdout; single miss was Australia 2019" is the model —
   number, scope, and the failure named in the same breath.

## Commands

```bash
# Feature claim: does the named thing exist in executed code?
grep -rn "shap\|SHAP" src/ *.py --include="*.py"
grep -rn "def <claimed_function>" src/

# Test claims: real count, and do they pass?
grep -rn "def test_" tests/ | wc -l
python -m pytest tests/ -q   # or: python -m unittest discover tests -v

# Status propagation check (run in the portfolio-site repo too)
grep -rn "<repo-name>" . --include="*.md" --include="*.html" --include="*.js" --include="*.json"

# Deployment claim
curl -sS -o /dev/null -w "%{http_code}" <live-url>

# Emptiness check for a repo claimed as substantive
git log --oneline | wc -l   # 2 commits ≠ "Strong tier"
find . -name "*.py" -o -name "*.pbix" -o -name "*.ipynb" | head
```

## Quality bar

Every claim in the final text is traceable to a specific file, command output,
or live URL that you personally checked in this session. "It was claimed
before" is not evidence — the audit exists because prior claims were wrong.

## Verification checklist

- [ ] Every named library/feature was grepped and found in executed code.
- [ ] Every metric has a producing script AND a committed output artifact.
- [ ] Every test count came from counting `def test_` and running the suite.
- [ ] Every "Complete/Deployed" label checked against the repo's own state.
- [ ] Propagation search run; all copies of a corrected claim fixed together.
- [ ] No claim survived on the strength of a previous description.

## Common mistakes

- Trusting the existing README as evidence for the new README.
- Verifying a library is in `requirements.txt` and calling that a feature
  (installed ≠ used — the churn repo failure exactly).
- Fixing the repo README but leaving the portfolio site table stale.
- Softening a false claim ("mostly complete") instead of correcting it.
- Inventing plausible specifics (row counts, test counts) to make a
  description feel concrete. This is the named anti-pattern.

## What to report back

- List of claims checked, each with its evidence pointer (file:line, command
  output, or URL + status code).
- Claims deleted or qualified, with the reason.
- Propagation locations found and whether each was fixed.
- Any claim you could not verify either way — flagged, not silently kept.

