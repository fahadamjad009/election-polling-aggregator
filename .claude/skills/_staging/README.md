# Staged skill library — review before promoting

Six portfolio-wide skills authored 2026-07-17, encoding the Professional
Project Delivery Master Standard v2.0 and the confirmed findings of the
2026-07-16 source-verified portfolio audit. Factual claims about
`election-polling-aggregator` (file paths, line numbers, test names, the
7-line requirements.txt, the Vite base path, the missing release/screenshots/
PROJECT_STATUS.md) were verified against a fresh clone of that repo on
2026-07-17.

| Skill | Encodes | Grounded in |
|---|---|---|
| claim-verification-gate | Sections 1, 11 | churn-repo phantom features; bi-financial false "Complete" propagating to the portfolio site |
| test-suite-scaffolding | Section 10 | election-polling-aggregator `tests/test_data_invariants.py` (10-test template) |
| master-standard-review-gate | Sections 2, 3, 22 | the corrected election-polling-aggregator flagship review pattern |
| leakage-safe-validation | Sections 6, 8 | twice-confirmed dtype-mismatch bug; duplicated RESULT_MARKER logic |
| dual-app-deployment-checklist | Sections 13, 14, 19 | live Streamlit + React pair; Vite base rule; curated requirements |
| powershell-windows-gotchas | Sections 19, 20 | the six catalogued Windows failure modes |

## Promotion procedure

1. Read each SKILL.md against the audit findings; delete anything vague.
2. `mv .claude/skills/_staging/<name> .claude/skills/<name>` for approved ones.
3. Point future sessions at promoted skills from a short CLAUDE.md — do not
   paste the library into it.

Not yet promoted: nothing in this folder is active until moved out.

