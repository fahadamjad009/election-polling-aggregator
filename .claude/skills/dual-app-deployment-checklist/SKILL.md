---
name: dual-app-deployment-checklist
description: Use when deploying, fixing, or reviewing the Streamlit + React delivery pair for a fahadamjad009 project — publishing to Streamlit Community Cloud, building a React app for GitHub Pages, editing vite.config.js, writing requirements.txt for deploy, or before any "deployed"/"live" claim. Trigger condition: work touches app deployment, gh-pages, Vite config, or deploy-facing requirements files.
---

# Dual-App Deployment Checklist (Streamlit + React)

Encodes Master Standard Sections 13–14 (delivery pattern) and the deploy
halves of Sections 19–20 (Windows-origin deploy breakers).

Reference implementation: `election-polling-aggregator` — `app.py` (Streamlit),
`web/` (React source, committed on `main`), `web/vite.config.js`
(`base: '/election-polling-aggregator/'`), `.github/workflows/deploy-react.yml`,
and a 7-line pinned `requirements.txt`.

## The roles are distinct — keep them distinct

- **Streamlit = evidence exploration.** The analyst-facing app over the real
  pipeline artifacts. It carries the numbers.
- **React = polished communication layer.** The recruiter/stakeholder-facing
  presentation on GitHub Pages. It carries the story and links back to the
  evidence.

Do not collapse them into one, and do not let the React layer state claims
the Streamlit/evidence layer can't back (route any new numbers through
`claim-verification-gate`).

## When NOT to use

- Repos with no web delivery (library/pipeline-only projects).
- Local-only development runs with no deploy or "live" claim in play.
- Non-Vite/non-Pages hosting (rules 1–2 below are Vite/Pages-specific;
  the requirements and verification rules still apply).

## Procedure

1. **Vite base path = `/<repository-name>/`, exactly.** For this pattern the
   value in `vite.config.js` must match the GitHub repo name with leading and
   trailing slashes (real example: `base: '/election-polling-aggregator/'`).
   A wrong or missing base is the classic all-assets-404 blank Pages site
   (Section 20 catalogued gotcha). If the repo is ever renamed, this line
   changes with it.
2. **React SOURCE lives on `main`.** `web/` (or the app folder) with its
   `src/`, `package.json`, and config is committed to `main`; `gh-pages`
   (or the Pages artifact) holds only built output, produced by the deploy
   workflow. Source existing ONLY on gh-pages is a named failure mode
   (Sections 13–14, 20): it makes the build irreproducible and the repo look
   empty. Check with `git ls-tree origin/main --name-only`.
3. **requirements.txt is curated, never `pip freeze`.** List only direct
   imports, pinned (the template's whole file is 7 lines: numpy, pandas,
   requests, scipy, scikit-learn, plotly, streamlit). A blind freeze from a
   Windows venv drags in Windows-only packages (e.g. pywin32) that break the
   Linux build on Streamlit Cloud (Sections 10, 19). Verify install in a
   clean environment before deploying.
4. **Cross-link both apps from the README.** The README front door links the
   live Streamlit URL and the live Pages URL, and each app should point to
   the other/the repo. Two live apps nobody can find from the front door
   fail Section 11.
5. **"Deployed" means you fetched it.** Before writing "live", "deployed",
   or adding a Live badge: request both URLs and confirm HTTP 200 and real
   content (Streamlit apps can 200 on a sleeping shell — check the body or
   wake it in a browser). A deploy claim without this check is Section 1's
   "implied deployment" violation.
6. **Config file encoding.** If you touched config files on Windows, verify
   no UTF-8 BOM on TOML/JSON (`head -c 3 file | od -c`; BOM = `357 273 277`).
   JS tolerates a BOM (the template repo's `vite.config.js` ships one,
   harmlessly), but TOML/JSON parsers reject it — see
   `powershell-windows-gotchas` for the fix.

## Commands

```bash
grep -n "base:" web/vite.config.js                      # must equal '/<repo-name>/'
git ls-tree origin/main --name-only | grep "^web"       # source on main
wc -l requirements.txt                                  # tens of lines = probably a freeze
grep -in "pywin32\|pypiwin32\|wincertstore" requirements.txt   # Windows leakage
python -m venv /tmp/clean && /tmp/clean/bin/pip install -q -r requirements.txt && echo CLEAN-INSTALL-OK
cd web && npm ci && npm run build                       # build must succeed from main
curl -sS -o /dev/null -w "%{http_code}\n" https://<app>.streamlit.app https://fahadamjad009.github.io/<repo>/
grep -n "streamlit.app\|github.io" README.md            # cross-links present
```

## Quality bar

Both apps reachable and showing real content; React rebuildable from a fresh
clone of `main` alone; requirements install clean on Linux; base path exact;
README links both. Only then may any surface say "deployed".

## Verification checklist

- [ ] `base` in vite.config.js equals `/<repo-name>/` character-for-character.
- [ ] `npm ci && npm run build` succeeds from `main` in a fresh clone.
- [ ] gh-pages/Pages artifact contains built output only, produced by the
      workflow, not hand-pushed.
- [ ] requirements.txt: every line is a direct import, pinned; clean-venv
      install passes; no Windows-only packages.
- [ ] Both live URLs fetched this session with real content confirmed.
- [ ] README links both apps; apps cross-reference the evidence.
- [ ] Any numbers added to the React layer passed claim-verification-gate.

## Common mistakes

- `base: '/'` (works locally with `npm run dev`, 404s every asset on Pages).
- Committing only `dist/` output — to gh-pages or anywhere — and losing the
  source; or the inverse, hand-editing files on the gh-pages branch.
- Shipping a 200-line frozen requirements from the Windows dev venv and
  discovering pywin32 at deploy time on Streamlit Cloud.
- Claiming "deployed" because the workflow went green — the workflow can pass
  while the page 404s on a bad base path. Fetch the URL.
- Letting the React copy drift ahead of the evidence ("interactive ML
  platform" over a static JSON export).

## What to report back

- Both URLs with the status codes and a one-line content confirmation.
- The base path value and repo name, shown matching.
- requirements.txt line count and the clean-install result.
- Where React source lives (proof from `git ls-tree`).
- Anything still not live or not verified, stated plainly instead of implied.

