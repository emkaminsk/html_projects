---
name: mkhome-validation-and-qa
description: Routine pass/fail validation for the mkhome.byst.re repo. Load BEFORE merging ANY change to main, whenever you ask "how do I know this change is correct?", before claiming a PR is "verified", when checking store.html/products.json sync, when validating head metadata / sitemap / sidebar / visual identity invariants, or when adding a new automated check. Ships three runnable scripts (check_invariants.py, check_store_sync.py, smoke_serve.py) whose output IS the evidence mkhome-change-control demands.
---

# mkhome Validation and QA

This repo has NO test suite, NO linters, NO CI checks (the only workflow deploys to production on push to main). These three scripts ARE the test suite. Run them from repo root; paste their output into every PR.

## Evidence doctrine

- "Verified" means **command output or a DOM assertion** — never "it looks right". The owner's rule (2026-07-05): *success must be measurable, never judged by eye.*
- Every claim in a PR description must map to a **re-runnable command** someone else could execute and get the same PASS lines.
- A script exiting 0 is the merge gate; WARNs are allowed but must be listed as known (see Golden inventory below). A new WARN you did not introduce knowingly is a finding — investigate it.
- These scripts own **routine** pass/fail. For deep one-off measurement use `mkhome-analysis-toolkit`; for production verification after deploy use `mkhome-deploy-and-operate`.

## The three scripts

All are Python 3 stdlib-only, support `--help`, print `PASS:`/`WARN:`/`FAIL:` lines plus a `SUMMARY:` line, and exit 0 only when there is no FAIL. Run from repo root:

```bash
python3 .claude/skills/mkhome-validation-and-qa/scripts/check_invariants.py
python3 .claude/skills/mkhome-validation-and-qa/scripts/check_store_sync.py   # add --full-diff for the whole diff
python3 .claude/skills/mkhome-validation-and-qa/scripts/smoke_serve.py        # add --port N to pin a port
```

None of them writes to the repo. `check_store_sync.py` copies store.html + sitemap.xml + products.json + all root pages into a tempdir, runs the repo's own `scripts/build-store.py` **there**, and diffs — never run `build-store.py` directly against the repo just to "check".

### 1. check_invariants.py — static repo invariants

Checks (all from `mkhome-architecture-contract`): head-metadata contract on the 5 main pages (title, meta description, meta author, canonical, og:image:width/height 1200/630, twitter:card, GoatCounter, html lang); GoatCounter on every root page; the 4 SEO markers exactly once each in store.html; sitemap.xml == root `*.html` minus sidebar.html; sidebar.html internal links resolve; products.json schema (6 top-level fields + title/subtitle/description/highlights/cta in en/es/pl, images exist); visual-identity tripwire (`--accent-color: #667eea`, `--accent-color-2: #764ba2`, Lato in styles.css, Lato webfont link on index/store); no static `id="menuToggle"` in any HTML (script.js must create it on `<body>` — transform containing-block trap, PR #1/8b05870, see `mkhome-failure-archaeology`); charset on main pages (missing charset on tool pages/sidebar = WARN, pre-existing).

Expected output TODAY (2026-07-05) — 26 PASS elided, WARN/summary shown verbatim:

```
PASS: head-contract: index.html has full head-metadata contract
... (25 more PASS lines) ...
WARN: visual-identity: portfolio.html never loads the Lato webfont (pre-existing gap as of 2026-07-05; styles.css asks for Lato but the page falls back to sans-serif — fix opportunistically)
WARN: visual-identity: projects.html never loads the Lato webfont (pre-existing gap as of 2026-07-05; styles.css asks for Lato but the page falls back to sans-serif — fix opportunistically)
WARN: visual-identity: utilities.html never loads the Lato webfont (pre-existing gap as of 2026-07-05; styles.css asks for Lato but the page falls back to sans-serif — fix opportunistically)
WARN: charset: json_prettifier.html lacks <meta charset> (pre-existing gap; standalone tool page with minimal head by design; served UTF-8 by nginx — fix opportunistically, not blocking)
WARN: charset: qr_code_generator.html lacks <meta charset> (pre-existing gap; standalone tool page with minimal head by design; served UTF-8 by nginx — fix opportunistically, not blocking)
WARN: charset: morse_converter.html lacks <meta charset> (pre-existing gap; standalone tool page with minimal head by design; served UTF-8 by nginx — fix opportunistically, not blocking)
WARN: charset: sidebar.html lacks <meta charset> (pre-existing gap; include fragment, head never used; served UTF-8 by nginx — fix opportunistically, not blocking)

SUMMARY: 26 PASS, 7 WARN, 0 FAIL
```
Exit code today: **0**.

### 2. check_store_sync.py — generated-block drift detector

Expected output TODAY (2026-07-05) — this FAIL is real and pre-existing (products.json commit 0860584 raised it-for-seniors to 10.49; build-store.py was never re-run, so committed JSON-LD still advertises 9.99 to Google):

```
FAIL: store.html is OUT OF SYNC with store/products.json — products.json changed without re-running build-store.py — run: python3 scripts/build-store.py (then commit store.html + sitemap.xml together)
  --- store.html (committed)
  +++ store.html (regenerated from products.json)
  @@ -474,7 +474,7 @@
     },
     "offers": {
       "@type": "Offer",
  -    "price": "9.99",
  +    "price": "10.49",
       "priceCurrency": "USD",
  ...
PASS: sitemap.xml matches regenerated output (ignoring <lastmod>, which churns by design)

SUMMARY: 1 PASS, 0 WARN, 1 FAIL
```
Exit code today: **1**. Do NOT tune the check to hide this; the fix is a deliberate store change (run `python3 scripts/build-store.py`, commit store.html + sitemap.xml) gated by `mkhome-change-control` + `mkhome-store-pipeline`. Note: `<lastmod>` churning to today is ignored by design — only URL-set/priority drift in sitemap.xml fails.

### 3. smoke_serve.py — HTTP smoke test

Serves repo root on a free port with stdlib http.server (fetch() breaks on file://), asserts HTTP 200 + content sentinels per page, shuts down cleanly.

Expected output TODAY (2026-07-05):

```
Serving /home/user/html_projects on http://127.0.0.1:<port> (temporary)
PASS: /index.html — HTTP 200 + 2 sentinel(s)
PASS: /store.html — HTTP 200 + 3 sentinel(s)
PASS: /portfolio.html — HTTP 200 + 2 sentinel(s)
PASS: /projects.html — HTTP 200 + 2 sentinel(s)
PASS: /utilities.html — HTTP 200 + 2 sentinel(s)
PASS: /json_prettifier.html — HTTP 200 + 1 sentinel(s)
PASS: /qr_code_generator.html — HTTP 200 + 1 sentinel(s)
PASS: /morse_converter.html — HTTP 200 + 1 sentinel(s)
PASS: /sidebar.html — HTTP 200 + 2 sentinel(s)
PASS: /styles.css — HTTP 200 + 1 sentinel(s)
PASS: /script.js — HTTP 200 + 1 sentinel(s)
PASS: /store/products.json — HTTP 200 + 1 sentinel(s)
PASS: /sitemap.xml — HTTP 200 + 1 sentinel(s)
PASS: /robots.txt — HTTP 200
Server shut down cleanly

SUMMARY: 14 PASS, 0 WARN, 0 FAIL
```
Exit code today: **0**.

## What a failure means, and where to go next

| Failing check | Meaning | Open next |
|---|---|---|
| head-contract / charset FAIL | A main page lost required `<head>` metadata | `mkhome-seo-reference` |
| goatcounter FAIL | Analytics blind spot on a page | `mkhome-seo-reference`, `mkhome-deploy-and-operate` (analytics) |
| seo-markers FAIL | Someone edited/duplicated the injection anchors; next build-store.py run corrupts store.html | `mkhome-store-pipeline` |
| sitemap FAIL (either script) | Page added/removed without regenerating, or hand-edited sitemap | `mkhome-store-pipeline` (build-store.py owns sitemap) |
| sidebar-links FAIL | Nav points at a missing file — every page shares this nav | `mkhome-architecture-contract` |
| products-json FAIL | Store will break at render time in ≥1 language | `mkhome-store-pipeline` |
| visual-identity FAIL | Non-negotiable brand tokens touched | `mkhome-change-control` (owner-approval territory) |
| menu-toggle FAIL | Hamburger re-inserted into sidebar markup — regression of PR #1/8b05870 | `mkhome-failure-archaeology` |
| store-sync FAIL | products.json vs committed JSON-LD/noscript drift | `mkhome-store-pipeline` |
| smoke FAIL | Page 404s or serves the wrong content | `mkhome-debugging-playbook` |

## Per-change-type checklist (mirrors mkhome-change-control classes)

Run everything listed BEFORE opening the PR; paste outputs into the PR.

| Change class | check_invariants | check_store_sync | smoke_serve | Manual checks |
|---|---|---|---|---|
| Content edit (text/images on a page) | yes | no | yes | — |
| products.json / store change | yes | **yes — must PASS after you re-run build-store.py** | yes | JS-off store check (below) |
| New page / nav entry | yes | yes (sitemap side) | yes — **add a sentinel for the new page first** | JS-off if page fetches content |
| CSS / styling | yes (visual-identity tripwire) | no | yes | Mobile hamburger check (below) |
| JS behavior (script.js, tool pages) | yes (menu-toggle) | no | yes | Mobile hamburger check (below) |
| nginx / deploy config | yes | no | no | `mkhome-deploy-and-operate` curl verification |
| Docs / skills only | no | no | no | — |

### Manual check: JS-off store (noscript crawler fallback)

```bash
python3 -m http.server 8123 --bind 127.0.0.1 &   # from repo root
curl -s http://127.0.0.1:8123/store.html | grep -c 'class="product-card"'   # expect >= product count (2 as of 2026-07-05)
curl -s http://127.0.0.1:8123/store.html | grep -c '<noscript>'             # expect >= 1
kill %1
```

### Manual check: mobile hamburger

Headless Chromium EXISTS at `/opt/pw-browsers` in this environment (verified 2026-07-05). This asserts script.js created the menuToggle on a mobile-sized viewport:

```bash
python3 -m http.server 8123 --bind 127.0.0.1 &   # from repo root
# Binary path floats across container versions — locate it, don't hardcode it:
CHROME=$(find /opt/pw-browsers -type f \( -name headless_shell -o -name chrome \) | head -1)
"$CHROME" \
  --no-sandbox --disable-gpu --no-proxy-server --window-size=375,667 --virtual-time-budget=4000 \
  --dump-dom http://127.0.0.1:8123/index.html | grep -c 'id="menuToggle"'   # expect 1
kill %1
```
Verified output today: `1`. If `/opt/pw-browsers` is absent (different environment), documented fallback: state in the PR that the DOM assertion could not be run, and ask the owner to tap the hamburger on a phone at 375px width — it must sit OUTSIDE `.sidebar` in the DOM (`grep -n 'menuToggle' script.js` proves creation on `document.body`).

## Golden inventory — baseline as of 2026-07-05

Summary lines (the golden numbers a clean checkout must reproduce):

```
check_invariants.py : SUMMARY: 26 PASS, 7 WARN, 0 FAIL   (exit 0)
check_store_sync.py : SUMMARY: 1 PASS, 0 WARN, 1 FAIL    (exit 1)
smoke_serve.py      : SUMMARY: 14 PASS, 0 WARN, 0 FAIL   (exit 0)
```

Known pre-existing findings (report, don't silently fix, don't hide):

1. **FAIL — store price drift**: products.json says it-for-seniors = 10.49 (commit 0860584); committed store.html JSON-LD still says 9.99. Fix = re-run build-store.py as a deliberate store change.
2. **WARN — tool-page heads**: json_prettifier.html, qr_code_generator.html, morse_converter.html lack `<meta charset>` and the full head contract; json_prettifier.html additionally has **no `<title>` at all** and qr_code_generator.html/morse_converter.html have **no `lang` attr on `<html>`** (found 2026-07-05, honest extras beyond the charset gap).
3. **WARN — sidebar.html** lacks charset (include fragment; its head is never used).
4. **WARN — Lato webfont never loaded on portfolio/projects/utilities**: styles.css declares `font-family: 'Lato'` but only index.html and store.html carry the Google Fonts `<link>`; the other three render the sans-serif fallback. Newly surfaced by this skill on 2026-07-05.

If your diff turns any WARN into a PASS, also update the baseline numbers here and the dated comments in the script.

## How to ADD a check

1. Pick the script: static file fact → `check_invariants.py` (add a `check_*` function calling `emit()`, register it in `main()`); generated-content drift → `check_store_sync.py`; served-behavior fact → `smoke_serve.py` (add path + sentinel strings to `SENTINELS`).
2. Ground-truth the expectation first with grep/curl against the CURRENT repo — never write a check from memory.
3. Decide FAIL vs WARN: FAIL = would be a regression if a merge introduced it; WARN = pre-existing gap, dated in the message (`as of YYYY-MM-DD`) with the reason it is tolerated.
4. Run the script, confirm the new line appears and the exit code is right, then update the Golden inventory numbers above and paste fresh output.
5. If the check enforces a new invariant, add it to `mkhome-architecture-contract` too — this skill checks invariants, that skill owns their WHY.

## When NOT to use this skill

- Verifying **production** after a deploy (cache headers, live curl, GoatCounter liveness) → `mkhome-deploy-and-operate`.
- Diagnosing WHY something is broken → `mkhome-debugging-playbook`, then `mkhome-failure-archaeology`.
- Deep one-off measurement (Lighthouse-style analysis, content audits) → `mkhome-analysis-toolkit`.
- Deciding whether a change is ALLOWED at all → `mkhome-change-control` (this skill only produces the evidence that gate demands).
- Editing generated store blocks by hand — never; `mkhome-store-pipeline`.

## Provenance and maintenance

- Authored 2026-07-05 against commit 878a7f0. Every command, output block, sentinel string, and baseline number above was executed/verified on that date in this repo — nothing is aspirational.
- All three scripts are Python 3 stdlib-only (verified on Python 3.11.15); no venv needed.
- Maintenance triggers: adding/renaming a root page (update `SENTINELS`, rerun everything); changing a page `<title>` (update its sentinel); changing products.json schema (update `PRODUCT_*` constants in check_invariants.py and `mkhome-store-pipeline`); fixing any Golden-inventory finding (update baseline numbers + dated WARN branches in check_invariants.py); build-store.py changes (check_store_sync.py runs it verbatim, so it self-updates, but re-verify the lastmod-stripping assumption).
- If expected output here disagrees with a fresh run, the REPO changed: trust the fresh run, investigate the delta, then update this file with new dated output.
