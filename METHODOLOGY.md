# Methodology — Election Polling Aggregator

This document explains **what was built and why**, in plain language, so you
can walk through the whole project and defend every decision in an
interview without needing to read code. Treat this as your study guide.

---

## 1. Why this project exists, and the framing decision

The original portfolio catalog item was a simple **Bayesian polling
average** — smooth out noisy polls into a trend line. You deliberately
reframed it into something richer: a **dual-target supervised ML problem**
across four countries, specifically so you could demonstrate classification
metrics (AUC/ROC) and dimensionality reduction (PCA), which a pure
Bayesian-average project wouldn't naturally need.

**The two targets:**
- **Classification** — which party/candidate wins (binary/multiclass)
- **Regression** — what vote share % each party gets

**Why both, not just one:** a model could get the *winner* right while being
badly wrong on *margin* (predicting a landslide that was actually close), or
vice versa. Having both targets is a more complete, more defensible
evaluation than either alone — and it's exactly the kind of "why did you
choose this" question that shows real methodological thinking in an
interview.

**Why national-level only, not district/state-level:** district-level data
multiplies the scope by hundreds of constituencies per country per election.
National-level keeps the project scoped to something genuinely completable
while still being real, multi-country, and methodologically rich.

---

## 2. Data sourcing strategy — why these sources, and the honesty principle

For every one of the four countries, the rule was: **use official or
clearly-reputable sources, transcribe/download real numbers, never
estimate or fabricate a gap.** This shows up repeatedly in the project —
several times, data was found to be *unavailable* for something (e.g.
Australia's national Primary-vote actuals), and the honest choice was to
document the gap rather than quietly fill it with a guess.

| Country | Election results source | Polling source |
|---|---|---|
| US | FiveThirtyEight's own GitHub data repo | Same (FiveThirtyEight) |
| UK | UK Parliament's House of Commons Library (official) | Wikipedia's "Opinion polling for the X election" articles |
| Canada | Elections Canada data, via a maintained open-data GitHub repo | Wikipedia |
| Australia | Australian Electoral Commission (AEC), official government page | Wikipedia |

**Why Wikipedia for polling data specifically:** individual historical
polls (hundreds per election cycle, going back decades) aren't published
anywhere as a single clean downloadable file for UK/Canada/Australia the
way FiveThirtyEight does it for the US. Wikipedia's election-cycle articles
turned out to be the only source with genuinely comprehensive historical
poll-by-poll tables. This was a real trade-off you were consulted on and
approved: less "official" than a government source, but Wikipedia's
election polling tables are themselves sourced from real published polls
and are the de facto standard reference for this kind of historical data.

---

## 3. Getting the polling data out of Wikipedia — the scraper

**The problem:** copying hundreds of polls per election cycle by hand,
across dozens of election cycles, isn't practical or reliable.

**The solution:** `pandas.read_html()` — a tool that automatically finds
and parses every HTML table on a web page into a structured table, without
needing to manually describe the page's layout. This is a standard,
legitimate technique (not "scraping" in the sense of doing anything
underhanded) — it's the same as opening the page and copying each table,
just automated and accurate.

**Why this matters for you to be able to explain:** an interviewer might
ask "how did you get this data" — the honest answer is "I wrote a script
that programmatically extracts every table from each Wikipedia article
covering an election's opinion polling, across 8 election cycles per
country, saving 275 raw tables total." That's a real, demonstrable data
engineering skill, not just "I downloaded a CSV."

---

## 4. Cleaning the scraped data — six rounds of real, verifiable bugs

This is the part most worth understanding deeply for an interview, because
it's the part that demonstrates actual data engineering judgment rather
than just running a tool. Real messy data needs real decisions. Here's what
happened, and why each fix was the right call:

### Round 1 — Percentage-shaped values aren't the same as "this is a party"
**Problem:** the first version of the cleaning logic accepted any column
whose values "looked like a percentage" (a number between 0-99, maybe with
a % sign) as a real party. This wrongly accepted UK "leader approval"
tables (e.g. a column literally named "David Cameron" holding his approval
rating, which is also a number that looks like a percentage) as if it were
a party's vote share.
**Fix:** built an explicit **known-party whitelist** per country — a list
of real, verified party names/abbreviations. A column is only treated as a
party if its name actually matches a real party, not just because its
values are numeric.
**Why this is the right lesson:** *"does this look like the right shape of
data" is not the same question as "is this actually the right data"* — a
genuinely important data-quality principle.

### Round 2 — The same party can appear under different labels in one table
**Problem:** a table might have two columns both meaning "Liberal
Democrats" — one just labeled "LD", the other duplicated by the scraping
tool as "LD.1" (a standard behavior when a spreadsheet-style tool
encounters two identically-named columns). Left unfixed, this would count
the same party as two different parties.
**Fix:** canonicalize every matched party name to one standard label before
using it, so "LD" and "LD.1" collapse into one real "LD".

### Round 3 — Column position isn't a reliable way to find "the date"
**Problem:** most tables put the date first, but some (particularly
Canadian tables) put the pollster's name first and the date second. Code
that just assumed "column 0 is always the date" silently grabbed the wrong
column for those tables.
**Fix:** search for the date column **by name** ("does this column's header
contain the word 'date'"), only falling back to position 0 if nothing
matches.

Separately in this same round: some Australian tables report **two
different metrics** (first-preference "Primary vote" and "Two-Party-
Preferred" i.e. "2PP" vote) under one merged header that gets
auto-flattened, burying the real party names in what looks like a
throwaway row. Fixed by explicitly **recovering** those real labels from
that row instead of discarding it, and tagging each recovered party with
which metric it belongs to (e.g. "ALP (Primary)" vs "ALP (2PP)") so the
two metrics never get accidentally averaged together.

### Round 4 — A production crash from a duplicate column name
**Problem:** two of those recovered party labels happened to collide (two
different table sections producing the same name), and pandas allows
duplicate column names — which means asking for "that column" returns
*multiple* columns instead of one, and the whole script crashed.
**Fix:** guarantee every recovered column name is unique (appending ".1",
".2" etc. exactly the way spreadsheet tools do it automatically), plus a
defensive check elsewhere so the script degrades gracefully instead of
crashing if this ever happens again via some other path.

### Round 5 — Validating a party name isn't the same as normalizing it
**Problem:** the whitelist correctly recognized that "Green" and "Grn" were
both real, valid party references — but kept them as two *different*
output labels, so the same party still ended up double-counted under two
names.
**Fix:** converted the whitelist into a proper **mapping** (every known
variant → one single canonical output), not just a validity check.

### Round 6 — Two more real, distinct issues found by directly investigating
When some Australian rows remained unmatched to any known category, rather
than just discarding them, you asked for further investigation. That
surfaced two genuinely different problems:
1. Some genuine primary-vote tables used the phrase "Political parties"
   instead of "Primary vote" as their group heading — a labeling variant
   the code didn't yet recognize. Fixed by adding it.
2. Several tables turned out to be **seat-count projections** (e.g. "this
   forecaster predicts party X wins 94 seats"), not vote-share polls at
   all — a completely different kind of data that had been wrongly let
   through because a bare number like "94" is structurally
   indistinguishable from a percentage without more context. Fixed by
   detecting and excluding any table whose header mentions "seat".

**The interview-ready story here:** each of these was a real defect found
by testing against genuine real data (not synthetic assumptions), root-
caused to understand *why* it happened, fixed precisely, and re-verified
against the exact failure case before being called done. That's the actual
practice of production data engineering.

---

## 5. Parsing dates — normalizing chaos into one consistent format

Real-world scraped date text is extremely inconsistent: `"12 Dec 2019"`,
`"10–11 Dec"` (a date *range*, no year), `"October 21, 2019"` (US-style),
`"7–8 Aug 2010"`, `"3/3/2016"` (US numeric format), and even non-dates like
`"Voting result"` mixed into the same column.

**Approach:** rather than one giant catch-all pattern, each real format
discovered gets its own specific rule, tried in sequence. Ranges use the
**later** date (closest to when opinion was actually measured). When a date
has no year of its own (like `"10–11 Dec"`), the surrounding election's
actual year is used, with a "rollback" rule: if the month mentioned is
*later in the calendar* than the election month, it must mean the
*previous* year (since campaign polling naturally runs backward from
election day).

**Testing philosophy — this matters for interviews:** every fix was tested
two ways: (1) synthetic test cases covering every known format, run
automatically every time the script runs, and (2) a **diagnostic mode**
that runs against the *actual real data* and reports the true success rate
plus concrete examples of anything still unparsed — which is how several
further real formats (cross-year ranges, month-only dates, citation-marker
noise) were discovered that the synthetic tests alone would have missed.
This two-layer testing (synthetic + real-data diagnostic) is a genuinely
strong practice to describe in an interview.

Final real-world parse rates: **UK 99.9%, Canada 99.7%, Australia ~99%,
US 100%.**

---

## 6. The four "DSA" (Data Structures & Algorithms) components

You specifically asked for real computer-science fundamentals to be visible
in this project, not just calling library functions. Here's what each one
is, and — critically — **why it's the right tool for the job**, which is
the actual thing an interviewer wants to hear (not just "I used a deque").

### 6a. Deque-based sliding-window poll averaging
**What it is:** a *deque* (double-ended queue) is a data structure that
lets you add/remove items from either end in constant time (O(1)),
regardless of how many items are already in it.

**Why it's the right fit here:** to compute a "rolling average of the last
5 polls," you need a fixed-size window that slides forward as new polls
arrive — old polls drop off the back as new ones join the front. A deque
with a fixed maximum size does exactly this natively: when it's full and
you add a new item, the oldest one is automatically evicted. This is
literally how real polling aggregators (538, RealClearPolitics) describe
their rolling-average methodology conceptually.

**The alternative, and why it's worse:** you *could* just take a slice of
the last 5 rows of a sorted list every time — but that means re-scanning
and re-slicing on every single new poll, which gets slower as the dataset
grows. The deque approach is the same idea done properly.

### 6b. Finite-difference momentum
**What it is:** the *first difference* between consecutive averaged values
is just "how much did it change" — the same concept as a derivative/rate of
change in calculus, but computed directly from discrete data points rather
than a continuous formula. The *second difference* (the difference of the
differences) tells you whether that rate of change is itself speeding up or
slowing down — i.e., acceleration.

**Why it's useful:** "Party X is polling at 45%" is a snapshot. "Party X's
support has been climbing by about 1 point per week, and that climb is
accelerating" is a genuinely different, more predictive signal — this is
what "momentum" means in a campaign, made precise and computable.

### 6c. Priority queue (heapq) for pollster reliability
**What it is:** a *min-heap* is a data structure that always lets you
efficiently retrieve the smallest (or, with the right ordering, best/worst)
element without needing to fully sort everything else first.

**Why it's the right fit here:** ranking hundreds of pollsters by their
historical accuracy is exactly the "always be able to get the best/worst
efficiently" problem a priority queue is built for. Every pollster's mean
error (real poll values compared against real historical election results)
gets pushed onto the heap, and popping them off in order produces the
reliability ranking.

**A genuinely good interview story lives here:** the first production run
of this component put entries like `"1997 general election"` and `"2008
by-election"` at both the *top* and *bottom* of the ranking — because those
weren't real pollsters at all, they were the placeholder text some source
tables used for the row showing the actual result (which trivially has ~0
error against itself, since it *is* the result). This was root-caused
(the exclusion filter was checking for a data column that had never
actually been created) and fixed by directly checking the text itself for
election-marker language. This is a great example to describe in an
interview: a bug that produced *plausible-looking, silently wrong* output
rather than an obvious crash — the harder and more important kind of bug
to catch.

### 6d. KD-tree for cross-country similar-election lookup
**What it is:** a KD-tree (k-dimensional tree) is a spatial indexing
structure — think of it as a smart, pre-organized filing system for points
in space that lets you ask "what are the nearest points to this one?"
efficiently, without comparing your query point against every single other
point one by one.

**Why it's the right fit here:** each election was turned into a small
numeric "fingerprint" — final poll standing, how volatile the polling was,
the actual winning margin, how many polls were conducted — and the KD-tree
finds elections (from *any* country) whose fingerprints are close together.
This produced genuine findings like "Australia's 2019 election looked
statistically similar to several recent US elections" purely from the
shape of the polling and result data, not from any hand-coded rule saying
those elections should be related.

**The brute-force alternative, and why the tree is better:** without a
KD-tree, finding the nearest elections means comparing your target election
against literally every other election's fingerprint one at a time. With
22 elections that's not a big deal — but the same technique scales to
thousands of points without becoming slow, which is the actual point of
using a real spatial data structure instead of a loop.

---

## 7. What "verification" actually meant throughout this project

A pattern worth being able to describe explicitly: **almost nothing was
handed to you without first being tested against a synthetic case built
from the exact real data structure**, before you ever ran it yourself. When
something still failed in real production (which happened several times —
data is messier than any synthetic test fully anticipates), the failure was
root-caused using the *real* failing example you pasted back, a fix was
built and re-verified against that exact case, and only then handed back.
This loop — build, verify against known cases, ship, catch real failures,
root-cause with real evidence, re-verify, re-ship — is the actual practice
of software/data engineering, and it's the thing to describe if asked "walk
me through your development process" in an interview.

---

## 8. Still to come (this document will be extended as the project continues)

- Exploratory data analysis (EDA)
- Dual-target modeling: classification (AUC/ROC) + regression, with PCA
- Streamlit app
- React companion webapp

---

# Current Implemented Methodology and Final Evaluation

This section records the final implemented pipeline and supersedes any
earlier statements in this document that describe modelling, validation,
scope filtering, or evaluation as future work.

## 1. Final project framing

The completed project is a reproducible multi-country national election
polling analytics system covering:

- Australia
- Canada
- the United Kingdom
- the United States

The project evaluates two related tasks:

1. national vote-share estimation;
2. identification of the party or candidate leading the national polling
   estimate.

The system does not predict:

- parliamentary seats;
- electoral-college votes;
- constituency outcomes;
- coalition formation;
- government formation.

Australia is modelled using national two-party-preferred polling because
consistent historical national primary-vote actuals were not available
across the selected election set.

## 2. Final dataset scope

The final modelling dataset contains:

- 22 elections;
- 14 development elections;
- 8 chronological holdout elections;
- 68 party-election rows;
- 43 development rows;
- 25 holdout rows.

The development and holdout split is applied at election level so that all
party rows from the same election remain together.

## 3. National polling-table governance

A major data-quality risk was the presence of non-national tables inside
historical polling pages.

Examples included:

- state and provincial polling;
- Scotland and Wales tables;
- constituency polling;
- by-election polling;
- regional subsamples;
- approval-rating tables;
- historical comparison tables.

To prevent these tables entering national features, the project created a
table-level scope audit.

The audit compares election-result marker rows in each source table against
verified national election results.

Automatic classifications include:

- `approved_marker_match`;
- `rejected_marker_mismatch`;
- `review`.

Reviewed exceptions are recorded explicitly in:

`data/reference/polling_scope_overrides.csv`

Manual decisions include:

- `manual_approved`;
- `manual_rejected`.

Only automatically approved and manually approved tables enter feature
engineering.

Final scope-filter results:

- 16,489 poll-party rows retained;
- 47,727 poll-party rows excluded;
- 15 automatically approved tables;
- 9 manually approved tables;
- 6 manually rejected tables.

Tables that remain unresolved are excluded by default.

This is a fail-closed design: uncertain sources do not silently enter the
model.

## 4. Leakage prevention

The final pipeline applies several leakage controls.

### Election-date control

Verified election dates are stored in:

`data/reference/election_dates.csv`

Polling observations after the election date are removed before rolling
averages or momentum features are calculated.

The final validation confirmed:

- zero post-election feature rows remained;
- eight post-election Australia 2022 poll-party rows were removed.

The exclusion audit is stored in:

`data/features/post_election_rows_excluded.csv`

### Election-result marker control

Election-result rows used for table validation are not treated as ordinary
polling observations in the predictive feature set.

### Development and holdout separation

Model selection uses development elections only.

The chronological holdout is not loaded by the development baseline or
feature-ablation scripts.

### Holdout governance

The selected model was fixed before the final holdout was evaluated.

The holdout was evaluated once and then protected by:

`data/model/final_holdout/HOLDOUT_EVALUATED.lock`

No later model tuning or reselection should use the holdout results.

## 5. Feature engineering

The project creates five-observation rolling polling averages and momentum
features for each country, election, and party.

Core party-election features include:

- final polling percentage;
- final five-observation rolling average;
- first finite difference;
- second finite difference;
- full-campaign polling mean;
- full-campaign polling standard deviation;
- minimum and maximum polling percentage;
- mean rolling average;
- observation count;
- campaign duration;
- days between the final polling observation and election day.

Final-30-day diagnostic features include:

- `recent_30d_mean`;
- `recent_30d_std`;
- `recent_30d_observations`;
- `recent_30d_trend_per_day`;
- `final_vs_recent_30d_mean`.

The 30-day trend is estimated as percentage-point change per elapsed day.

These features were evaluated through ablation but were not selected as the
final forecasting method.

## 6. Party-label and modelling conventions

Polling labels are mapped to the canonical labels used in actual election
results.

Important rules include:

- Australia retains only `ALP (2PP)` and `L/NP (2PP)`;
- UK polling label `LD` maps to actual-results label `LIB`;
- unmatched or intentionally excluded parties are documented in
  `data/model/excluded_polling_parties.csv`.

Each final modelling row represents one party in one election.

Each election must contain exactly one actual winner.

## 7. Development validation

Development evaluation uses leave-one-election-out cross-validation.

For each fold:

1. one complete election is removed;
2. all remaining development elections are used for training;
3. every party in the excluded election is predicted;
4. the process repeats for all 14 development elections.

This prevents party rows from the same election being split across training
and validation data.

## 8. Compared methods

The project evaluated:

- the final five-observation polling average;
- Ridge regression using broad campaign features;
- Ridge regression using recent-window features;
- Ridge regression using final plus recent-window features;
- logistic regression for winner classification.

The final polling average acts as an honest benchmark because it uses the
polling estimate directly without fitting a more complex model.

## 9. Development results

The selected final polling average achieved:

- MAE: 1.3115 percentage points;
- RMSE: 1.7230 percentage points;
- election-winner accuracy: 92.9%.

The strongest Ridge challenger used final plus recent-window features and
achieved:

- MAE: 2.2684;
- RMSE: 2.8831;
- election-winner accuracy: 92.9%.

Other Ridge configurations performed worse.

Logistic regression achieved useful ranking performance but did not improve
the final model-selection criteria.

The simpler polling benchmark was therefore selected.

This is an important methodological result: additional model complexity was
rejected because it did not improve out-of-election performance.

## 10. Final chronological holdout

The holdout elections are:

- Australia: 2019 and 2022;
- Canada: 2015 and 2019;
- United Kingdom: 2017 and 2019;
- United States: 2012 and 2016.

Final holdout performance:

- MAE: 1.2435 percentage points;
- RMSE: 1.6799 percentage points;
- winner accuracy: 87.5%;
- correct winners: 7 of 8.

The only incorrect holdout winner was Australia 2019.

That miss is retained and reported rather than hidden.

## 11. Interpretation of the final result

The holdout error is slightly lower than the development cross-validation
error, but the holdout contains only eight elections.

The result should therefore be interpreted as evidence that the pipeline
generalised reasonably across the selected historical elections, not as a
universal election-forecasting guarantee.

The project demonstrates that careful data-scope control and leakage
prevention contributed more value than adding unnecessary model complexity.

## 12. Retrospective analysis versus predictive features

The similar-election analysis is retrospective.

Its vectors use actual election outcomes and therefore must not enter the
forecasting model.

Pollster-reliability outputs are also analytical evidence unless they are
rebuilt inside each training fold using only historically available
information.

This separation prevents analytical outputs from being incorrectly
presented as leakage-safe predictive inputs.

## 13. Main limitations

- The final dataset contains only 22 elections.
- Historical polling formats differ by country and election.
- Some source-table decisions required documented manual review.
- Australia is represented through two-party-preferred polling.
- The selected approach estimates national vote share, not seats or
  government formation.
- Systematic polling errors can remain.
- The project does not currently produce probabilistic uncertainty
  intervals.
- The final holdout contains only eight elections.
- Historical performance should not be treated as guaranteed future
  performance.

## 14. Final methodological conclusion

The completed project is best described as an evaluation-first historical
polling analytics system.

Its strongest professional features are:

- traceable raw and processed data;
- country-specific cleaning logic;
- explicit party-label mapping;
- table-level national-scope auditing;
- documented manual overrides;
- fail-closed source inclusion;
- pre-feature election-date filtering;
- election-level cross-validation;
- feature ablation;
- evidence-based rejection of unnecessary complexity;
- one-time chronological holdout evaluation;
- honest reporting of the Australia 2019 failure;
- reproducible output files and audit trails.

The selected final method remains the five-observation rolling polling
average.

Future work must use newly declared external elections or a new evaluation
set rather than retuning against the locked holdout.

