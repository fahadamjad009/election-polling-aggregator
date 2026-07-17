---
name: powershell-windows-gotchas
description: Use when working on or debugging anything developed on the Windows/PowerShell machine — mysterious TOML/JSON parse errors, Linux deploy failures from a Windows-built repo, git showing a venv or thousands of unexpected files, PowerShell here-string sessions hanging at ">>", files that won't delete, or config files that "look identical but don't parse". Trigger condition: the symptom involves Windows-origin files or a PowerShell workflow.
---

# PowerShell / Windows Gotchas

Direct encoding of Master Standard Section 20's catalogued list (plus the
Section 19 deploy overlaps). One entry per gotcha: symptom → cause → fix.
These are recurring, environment-specific failures on this portfolio's dev
machine — check this list BEFORE inventing a novel explanation for a weird
Windows-origin failure.

## When NOT to use

- Failures that reproduce identically on Linux/CI from a fresh clone — those
  are real code bugs; debug them normally.
- macOS/Linux-only workflows with no Windows-origin files involved.

## The catalogue

### 1. Blind `pip freeze` breaks the Linux deploy
- **Symptom:** Streamlit Cloud / Linux CI build fails resolving packages that
  have no Linux wheel (pywin32, pypiwin32, wincertstore), or installs 100+
  packages for a 5-import project.
- **Cause:** `pip freeze > requirements.txt` from the Windows venv captures
  the entire environment, including Windows-only and transitive packages.
- **Fix:** Curate by hand: list only direct imports, pinned. Reference:
  election-polling-aggregator's 7-line requirements.txt. Verify:
  `python -m venv /tmp/clean && /tmp/clean/bin/pip install -r requirements.txt`
  on Linux (CI counts).

### 2. venv committed to git
- **Symptom:** `git status` shows thousands of files; repo balloons; clones
  are slow; diffs are unreadable.
- **Cause:** `python -m venv venv` created inside the repo with no
  `.gitignore` entry before the first `git add .`.
- **Fix:** Add `venv/` (and `.venv/`) to `.gitignore`;
  `git rm -r --cached venv` and commit. If it reached the remote, the history
  is polluted — flag it; do NOT rewrite published history without explicit
  approval.

### 3. UTF-8 BOM breaks TOML/JSON
- **Symptom:** A config file that looks byte-for-byte correct fails to parse
  (`Expecting value: line 1 column 1` for JSON; TOML parse error at 1:1).
- **Cause:** PowerShell 5.1's `Out-File`/`>` and Notepad write UTF-8 with a
  BOM (bytes `EF BB BF`). Strict TOML/JSON parsers reject it. JS tolerates it
  — the template repo's own `web/vite.config.js` ships a BOM harmlessly,
  which is why the habit goes unnoticed until it hits a .toml/.json file
  (e.g. `.streamlit/config.toml`).
- **Fix:** Detect: `head -c 3 file | od -c` → `357 273 277` = BOM. Strip:
  `sed -i '1s/^\xEF\xBB\xBF//' file`. Prevent: in PowerShell use
  `Set-Content -Encoding utf8NoBOM` (PS 7+) or write files via Python
  (`open(..., "w", encoding="utf-8")`).

### 4. Large here-strings hit the continuation prompt
- **Symptom:** Pasting a multi-line here-string (`@" ... "@`) into the
  PowerShell console leaves the session stuck at `>>`, or silently truncates
  and executes garbage.
- **Cause:** Console line-length/paste handling; the closing `"@` must also
  start at column 1 — indented terminators are not recognized.
- **Fix:** Don't paste large content as here-strings. Write it to a `.ps1` or
  have Python/git generate the file. If stuck at `>>`, Ctrl+C, then verify
  what (if anything) executed before retrying — assume partial state.

### 5. Notepad appends `.txt`
- **Symptom:** Tooling can't find `requirements.txt` or `config.toml` that
  "definitely exists" — because the file is actually `requirements.txt.txt`
  or `config.toml.txt` (extension hidden by Explorer).
- **Fix:** Detect: `Get-ChildItem -Name *.txt.txt, *.toml.txt, *.md.txt` (or
  `ls -la` in git bash). Rename with `git mv`. Prevent: create files from the
  terminal or editor Save-As with quoted filename ("requirements.txt").

### 6. Locked folders holding a dev-server handle
- **Symptom:** `rm`/delete of `node_modules`, `dist`, or a build folder fails
  with "in use by another process"; rebuilds behave stale; git checkout
  fails on a directory.
- **Cause:** A still-running dev server (Vite/Streamlit) or Explorer window
  holds a handle on the folder.
- **Fix:** Stop the dev server first (find it: `Get-Process node, streamlit`;
  stop it: `Stop-Process -Id <pid>`), close Explorer windows on the folder,
  then delete. Never reach for force-unlock utilities as step one, and never
  conclude the repo is corrupted.

## Cross-cutting procedure

1. Match the symptom against the catalogue BEFORE deep debugging — these six
   have burned this portfolio before; base rates favor them.
2. Apply the entry's fix, then its verify step.
3. If a fix changes committed files (BOM strip, venv removal, rename), commit
   that as its own small, labeled change — don't fold it into feature work.
4. If the symptom matches nothing here but is Windows-origin, reproduce on
   Linux/CI from a fresh clone to separate environment issues from code bugs
   — and report a candidate new catalogue entry.

## Quality bar

The fix addresses the catalogued CAUSE, is verified by re-running the failing
operation, and prevention (gitignore entry, encoding flag, curated file) is
put in place so the same gotcha doesn't recur next session.

## Verification checklist

- [ ] Symptom matched to a catalogue entry (or explicitly ruled out on all six).
- [ ] Fix applied and the originally-failing command re-run successfully.
- [ ] Prevention step applied, not just the one-time fix.
- [ ] Any repo file changes committed separately with a clear message.
- [ ] BOM checks run on any .toml/.json touched from Windows this session.

## Common mistakes

- Debugging a TOML parse error semantically for an hour when `od -c` would
  show the BOM in 5 seconds.
- "Fixing" requirements.txt by deleting only pywin32 from a frozen list —
  still a freeze, still fragile; curate instead.
- Rewriting git history to purge a committed venv without asking first.
- Renaming `x.txt.txt` in Explorer (invisible extensions caused this) instead
  of `git mv` in the terminal.
- Force-deleting a locked folder while the dev server still runs, corrupting
  the next build.

## What to report back

- Which catalogue entry matched, the evidence (exact bytes/filenames/pids),
  the fix, and the re-run proof.
- The prevention now in place.
- If nothing matched: the fresh-clone Linux repro result and the proposed new
  entry.

