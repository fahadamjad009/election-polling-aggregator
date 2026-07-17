---
name: master-standard-review-gate
description: Use to audit any fahadamjad009 repo against the Master Standard Section 22 Definition of Done — before declaring a project "done", before pinning it to the profile, before listing it as Complete on the portfolio site, at the start of work on a blueprint project, or when asked to "review", "audit", or "check status of" a repo. Trigger condition: any completion/tier judgment is about to be made about a repository.
---

# Master Standard Review Gate (Section 22 DoD)

Encodes Section 22's Definition of Done as a runnable checklist, plus
Section 3's gate rule: a milestone is complete only when its exit evidence
EXISTS and HAS BEEN INSPECTED — "code written" is not "verified complete".

There are two bars. Do not apply the wrong one (Section 2: controls scale
with project class):

- **Core DoD** (any public Class B repo): README front door, METHODOLOGY.md,
  real test suite, curated requirements, honest status.
- **Flagship DoD** (Class B/C flagships): core DoD **plus** verified CI,
  deployed Streamlit + React apps, screenshots in README, a tagged release,
  PROJECT_STATUS.md, and a monitoring/ownership note.

Reference output pattern — the corrected election-polling-aggregator review
(verified against the repo 2026-07-17): docs present (METHODOLOGY.md +
docs/{ARCHITECTURE,DATA_DICTIONARY,MODEL_CARD,RUNBOOK}.md), CI real
(ci.yml + deploy-react.yml), holdout lock present
(data/model/final_holdout/HOLDOUT_EVALUATED.lock) — but tagged release
MISSING (`git ls-remote --tags` empty), screenshots MISSING (none in README),
PROJECT_STATUS.md MISSING. Small, named gaps. Replicate that shape:
findings must be specific and falsifiable, never "docs could be better".

## When NOT to use

- Mid-implementation feature work with no completion claim in play.
- Class A exploratory work not published or claimed anywhere.
- As a writing task: this gate never edits the repo. It only produces a
  findings table. Fixes go through the other skills
  (`test-suite-scaffolding`, `claim-verification-gate`,
  `dual-app-deployment-checklist`).

## Procedure

1. **Determine the class and the bar.** Is this repo pinned, on the portfolio
   site, or described as a flagship anywhere? If yes → flagship bar. Public
   but unpinned → core bar. State which bar you are using and why.
2. **Run every check below and record PRESENT / MISSING / DECORATIVE with the
   evidence pointer.** "Decorative" means the artifact exists but doesn't do
   what it claims (badge with no passing workflow, empty METHODOLOGY.md,
   tests that assert nothing — Section 10's named anti-pattern).
3. **Checks — core bar:**
   - README exists, states what the project does AND does not claim, and its
     factual claims pass `claim-verification-gate` spot checks.
   - METHODOLOGY.md exists and is non-trivial (not a heading skeleton).
   - docs/{ARCHITECTURE,DATA_DICTIONARY,MODEL_CARD,RUNBOOK}.md present where
     the project type calls for them (a model card only if there's a model).
   - tests/ exists, has real assertions, and passes now (run it).
   - requirements.txt is curated (a handful of pinned direct imports — see
     election-polling-aggregator's 7-line file), not a 100-line pip freeze.
4. **Checks — flagship bar adds:**
   - CI badge in README links to a workflow that exists AND whose latest run
     passed. Badge without run = DECORATIVE, not PRESENT.
   - Streamlit app URL loads (curl it); React/gh-pages URL loads; React
     SOURCE is on `main`, not only built output on gh-pages (Section 13-14).
   - Screenshots actually embedded in README (grep for image links).
   - Tagged release exists: `git ls-remote --tags origin` non-empty.
   - PROJECT_STATUS.md exists and matches reality.
   - Locked-holdout evidence where the project evaluates a model (lock file
     with its do-not-retune text, per the template repo).
   - Monitoring/ownership note present.
5. **Produce the findings table** (check → status → evidence → smallest fix),
   then an overall verdict: which bar, met or not, and the exact remaining
   gaps by name.
6. **Cross-check external labels.** If the repo is labeled "Complete"/"Strong"
   on the portfolio site or profile and the verdict says otherwise, flag the
   propagated false claim explicitly (this is exactly how
   bi-financial-kpi-command-centre's 2-commit scaffold ended up marked
   "Complete" on the live site).

## Commands

```bash
ls METHODOLOGY.md PROJECT_STATUS.md docs/ tests/ .github/workflows/ 2>&1
git ls-remote --tags origin
git log --oneline | wc -l
wc -l requirements.txt && cat requirements.txt
grep -n "!\[.*\](.*\.\(png\|jpg\|gif\|webp\)" README.md   # screenshots
grep -n "badge.svg" README.md                              # CI badge → verify the workflow
python -m unittest discover tests -v 2>&1 | tail -3        # or pytest -q
curl -sS -o /dev/null -w "%{http_code}\n" <streamlit-url> <pages-url>
git ls-tree origin/main --name-only | grep -i "src\|web"   # React source on main?
```

## Quality bar

Every row of the findings table has an evidence pointer a stranger could
re-run. No row says "looks fine". MISSING items are named individually — the
election-polling-aggregator pattern (release missing, screenshots missing,
PROJECT_STATUS.md missing) is the reference for specificity.

## Verification checklist

- [ ] Bar (core vs flagship) stated with the reason.
- [ ] Every check has PRESENT / MISSING / DECORATIVE + evidence.
- [ ] Tests were actually run, not just found.
- [ ] Live URLs were actually fetched, not assumed.
- [ ] Tag check used `ls-remote` (local tags can be absent in shallow clones).
- [ ] External labels (site, pins) cross-checked against the verdict.
- [ ] No fixes were applied inside this gate — findings only.

## Common mistakes

- Applying the flagship bar to a Class A notebook (over-rigor is also a
  Section 2 violation) or the core bar to a pinned repo.
- Counting a CI badge as CI (the badge is a claim; the workflow run is the
  evidence).
- Marking docs PRESENT because the file exists, without opening it.
- Reviewing the README's description of the tests instead of running them.
- Producing vague findings ("improve documentation") instead of named gaps.

## What to report back

- The findings table (check / status / evidence / smallest fix).
- Verdict: bar used, met or not, remaining gaps by name.
- Any DECORATIVE findings called out separately — these are worse than
  MISSING (Section 1: concealed failure).
- Any external label contradicted by the verdict, with both locations.

