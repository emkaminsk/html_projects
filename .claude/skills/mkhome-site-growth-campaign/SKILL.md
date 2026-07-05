---
name: mkhome-site-growth-campaign
description: >
  Executable campaign for GROWING the mkhome.byst.re site: load whenever asked to add a new
  page, a new tool (calculator/converter/generator), a new product or ebook to the store,
  a new section, or a new navigation/sidebar link — or to "publish", "launch", or "ship"
  anything new on the site. Covers the full path from empty file to verified production URL
  without breaking SEO, navigation, or the visual identity. Routes every merge through
  mkhome-change-control. This is the flagship growth skill; sibling skills hold the
  domain detail it delegates to.
---

# mkhome-site-growth-campaign

Adding things to this site is the owner's stated hardest live problem (2026-07-05):
"adding new pages/tools/products quickly without breaking SEO, navigation, or styling."
This skill is a decision-gated campaign. Every phase has an exact command, an expected
observation, and a branch for deviation. Success is measured by commands, never by eye.

**Run everything from repo root** (`/home/user/html_projects` or wherever the repo is checked out).
main IS production: push to main → GitHub Action → VPS git pull. There is no staging.

## When NOT to use this skill

- Fixing or debugging something that already exists → `mkhome-debugging-playbook`.
- Editing text/content on an existing page → `mkhome-change-control` directly (content edit class).
- Changing prices/descriptions of an EXISTING product → `mkhome-store-pipeline` (still rerun the build — see Fence F6).
- Deploy verification of an already-merged change → `mkhome-deploy-and-operate`.
- Restructuring nav, rebranding, adding frameworks/build tooling → STOP; that is an owner
  conversation per `mkhome-architecture-contract`, not a growth task.

## Track selection (first decision gate)

| You were asked to add… | Track |
|---|---|
| An ebook/product to the store | **A** |
| A page hosted on THIS site (tool page or content page) | **B** |
| A link to something hosted ELSEWHERE (own domain/subdomain) | **C** |

If unsure between B and C: does any new `*.html` file land in this repo? Yes → B. No → C.

## Common gate protocol (all tracks)

At each numbered gate: run the exact command, compare to the expected observation,
and on deviation take the named branch — never "probably fine, continue".

**Gate 0 — every track starts here:**
```
git status --porcelain        # expected: empty. Dirty → stash or resolve first.
git checkout -b growth/<slug> # never work directly on main (main IS production)
python3 --version             # expected: Python 3.x present
```
Load `mkhome-change-control` now and classify the change; keep its verification
requirements open beside this campaign. Every merge at the end goes THROUGH it.

---

## TRACK A — Add a product to the store

Mechanics (JSON field meanings, image conventions, KDP URLs) live in `mkhome-store-pipeline`.
This track owns the gate sequence only.

**A1. Edit `store/products.json`.** Append one object with ALL of:
`id, image, category, price, currency, kdpUrl` and `en`, `es`, `pl` blocks each containing
`title, subtitle, description, highlights[], cta`. Missing language block → build falls back
silently for some fields and crashes (KeyError) for others — do not omit any.

**A2. Validate JSON.**
```
python3 -m json.tool store/products.json > /dev/null && echo JSON_OK
```
Expected: `JSON_OK`. Anything else → fix the reported line before proceeding.

**A3. Run the build. This step is NOT optional.**
```
python3 scripts/build-store.py
```
Expected output: exactly two lines, `Updated .../store.html` and `Updated .../sitemap.xml`.

**A4. Verify diff shape.**
```
git diff --stat
```
Expected: exactly 3 files — `store/products.json`, `store.html`, `sitemap.xml`.
- `store.html` changes ONLY between `<!-- SEO:JSON-LD -->…<!-- /SEO:JSON-LD -->` and
  `<!-- SEO:NOSCRIPT -->…<!-- /SEO:NOSCRIPT -->` markers (check with `git diff store.html`).
  Changes outside the markers → you or the script touched hand-authored HTML → `git checkout store.html`, investigate.
- `sitemap.xml` shows `<lastmod>` churn on ALL entries (today's date). This is normal
  generator behavior — commit it, do not revert it (as of 2026-07-05).
- NOTE: the build may also emit unrelated corrections — e.g. if a previous session edited
  products.json without rerunning the build, stale JSON-LD gets fixed now (this exact drift
  is live from commit 0860584: price 9.99→10.49 never rebuilt, as of 2026-07-05). Extra
  corrective lines in the generated blocks are expected; mention them in the PR.

**A5. Smoke + JS-off check.**
```
python3 -m http.server 8000 &   # file:// breaks fetch(); always serve
curl -s localhost:8000/store.html | grep -c '"@type": "Product"'
```
Expected: old product count + 1. Then confirm the new product's title appears inside the
`<noscript>` block (`grep -A2 'SEO:NOSCRIPT' -n store.html` region) — that is what crawlers
and JS-off users see. Missing → the build did not run against your JSON → back to A3.
If the sibling validation scripts exist, run all three (see Promotion protocol).

**A6. Change control.** Classify as store/products change in `mkhome-change-control`,
open PR, merge only when its gate passes. Post-merge: Promotion protocol below.

---

## TRACK B — Add a page

**B-Gate: standalone tool page or full site page?**

| Criterion | Standalone tool (like `morse_converter.html`) | Full site page (like `projects.html`) |
|---|---|---|
| Purpose | Self-contained utility, reached via a listing/submenu link | Destination content; part of site structure |
| Nav | NOT in main nav top level; linked from a submenu or listing page | Appears in sidebar |
| Styling | Own minimal inline styles; deliberately no `styles.css`/`sidebar`/`script.js` | Shared `styles.css` + sidebar |
| SEO weight | Low (still fix the head — donors currently lack charset/meta, a known gap as of 2026-07-05) | Full head contract mandatory |

When in doubt → full site page (cheaper to have nav than to retrofit it).

### Phase B1 — Create the HTML from a donor

**Standalone tool:** copy `morse_converter.html` as structural donor. Its head is minimal
(no charset/viewport/meta — known gap); ADD at minimum `<html lang="en">`,
`<meta charset="UTF-8">`, viewport, unique `<title>`, meta description, canonical.
Keep it self-contained: no sidebar, no styles.css, no script.js — that is deliberate.

**Full site page:** copy `projects.html` for body structure, **but replace its loader**:
projects/portfolio/utilities still use the legacy jQuery `$('.sidebar').load(...)` block —
do NOT copy it (Fence F2). Use the `index.html` pattern instead:
- body: `<nav class="sidebar" id="sidebar"></nav>` (nav + id, not a bare div)
- before GoatCounter: `<script src="script.js"></script>`
- delete the jQuery/Bootstrap-JS `<script>` tags and the inline `$(document).ready` block.

Head contract — change EVERY one of these (verify the full list against `index.html`, the
canonical donor head, as of 2026-07-05):

| Field | Rule |
|---|---|
| `<html lang>` | page language |
| `<title>` | unique, `Something | Marcin Kamiński` pattern |
| `meta description` | 150–160 chars, unique |
| `meta author` | `Marcin Kaminski` |
| `link canonical` | `https://mkhome.byst.re/<page>.html` — exact filename |
| `og:title` / `og:description` / `og:url` | match title/description/canonical |
| `og:type` | `website` |
| `og:image` + width 1200 + height 630 | keep `store/assets/og-image.png` unless a page-specific image exists |
| `twitter:card` | `summary_large_image` |
| Bootstrap 5.3.0 CSS CDN + `styles.css` | keep both links |
| GoatCounter snippet | before `</body>` |

Gate check:
```
grep -c '"og:image"' <page>.html          # expected: 1
grep -c 'rel="canonical"' <page>.html     # expected: 1
grep 'canonical' <page>.html              # URL must contain the NEW filename, not the donor's
```
Donor filename still present anywhere in the head → you missed a field; grep for the donor name.

### Phase B2 — Sidebar link (full site pages; standalone tools get a submenu/listing link)

Edit `sidebar.html`. Placement rules:
- Top-level page → new `<li><a href="<page>.html">Label</a></li>` in the flat list.
- Tool under Projects → new `<li>` inside the existing `ul.submenu` under the
  `projects.html` toggle (pattern: json_prettifier/qr/morse entries).
- Preserve the existing `<ul class="navbar-nav flex-column">` structure exactly — no new
  classes, no inline styles, no icons (visual identity gate; owner rule 2026-07-05).
Gate: `git diff sidebar.html` shows ONLY added `<li>` line(s). Structural churn → revert, redo.
Sidebar loads once via fetch on every page — one edit updates nav site-wide; never copy
nav markup into pages.

### Phase B3 — Sitemap pickup (generated — never by hand)

```
python3 scripts/build-store.py
git diff sitemap.xml
```
Expected (dry-run verified 2026-07-05): one new `<url>` block
`<loc>https://mkhome.byst.re/<page>.html</loc>` with `<priority>0.5</priority>`, plus
`<lastmod>` churn to today on every entry. The churn is normal — do not revert it.
The generator auto-includes ANY root `*.html` except `sidebar.html`; if your page is
missing, it is not in repo root. `store.html` may also show corrective churn in its
generated blocks (see A4 note) — expected, keep it.

### Phase B4 — Verify locally

```
python3 -m http.server 8000 &
curl -s localhost:8000/<page>.html | grep -c '"og:image"'     # expected: 1
curl -s localhost:8000/sitemap.xml | grep -c '<page>.html'    # expected: 1
python3 .claude/skills/mkhome-validation-and-qa/scripts/check_invariants.py
python3 .claude/skills/mkhome-validation-and-qa/scripts/check_store_sync.py
python3 .claude/skills/mkhome-validation-and-qa/scripts/smoke_serve.py
```
All three scripts must exit 0. Failures → each script names the violated invariant; fix,
rerun. Do not merge with a failing script (Fence F8).
Browser check at `http://localhost:8000/<page>.html`: sidebar populates (full pages),
hamburger appears at mobile width (script.js creates `#menuToggle` dynamically).
JS-off check: disable JS (or `curl` the raw HTML) — the page's primary content must be
present in the static HTML, not injected by script.

### Phase B5 — Change control → merge

`git diff --stat` expected: exactly `<page>.html` (new), `sidebar.html`, `sitemap.xml`
(+ possibly `store.html` corrective churn) — nothing else. Extra files → explain or revert.
Classify in `mkhome-change-control` (new-page class), open PR against main, merge only
through its gate.

### Phase B6 — Post-deploy

After the GitHub Action completes (verify via `mkhome-deploy-and-operate`):
```
curl -s https://mkhome.byst.re/<page>.html | grep -c '"og:image"'   # expected: 1
curl -s https://mkhome.byst.re/sitemap.xml | grep -c '<page>.html'  # expected: 1
```
Then run the new URL through an OG validator (e.g. opengraph.xyz or the social debuggers) —
title, description, and 1200×630 image must resolve. Remember nginx caches css/js 1h: a
page relying on a same-push `styles.css` change may look stale for up to an hour.

---

## TRACK C — Add an external project link only

Lightest track. Precedent entries: `game2048.byst.re`, `life.byst.re`, `searchexity.toadres.pl`
in the Utilities submenu of `sidebar.html`.

1. `sidebar.html`: add `<li><a href="https://<host>/">Label</a></li>` in the fitting
   submenu (Utilities for tools/games, Portfolio submenu for showcase projects).
2. Optionally add a card on `utilities.html` or `projects.html` (copy an existing
   `<div class="project-item section">` block — existing classes only).
3. NO build-store.py run needed (external URLs never enter sitemap.xml) unless you also
   touched a root `*.html`... which you did if you edited utilities/projects — then the
   diff should show no sitemap change from it (page already listed; lastmod churn only if
   you ran the script — skip running it for Track C).
4. Gate: `git diff --stat` shows 1–2 files, `curl -sI https://<host>/` returns HTTP 200/301.
5. Through `mkhome-change-control` (content-edit class, lowest risk) → merge → confirm the
   link renders on production.

---

## FENCED WRONG PATHS — do not do these

| # | Wrong path | Why (incident/debt) |
|---|---|---|
| F1 | Hand-editing `sitemap.xml` or anything between `<!-- SEO:JSON-LD -->` / `<!-- SEO:NOSCRIPT -->` markers | Generated by `scripts/build-store.py`; next run silently obliterates your edit |
| F2 | Copying the jQuery `$('.sidebar').load(...)` loader into a new page | jQuery removal is open debt (`.ai/transformation-checklist.md`); vanilla `script.js` is the direction of travel — new pages must not grow the debt |
| F3 | `position:fixed` elements inside `.sidebar` (or any CSS-transformed ancestor) | Incident PR #1 / commit 8b05870: transformed ancestor becomes the containing block; the hamburger became untappable on mobile. `script.js` appends `#menuToggle`/`#sidebarBackdrop` to `<body>` for exactly this reason |
| F4 | New brand colors, fonts, or gradients | Owner non-negotiable (2026-07-05): gradient `#667eea→#764ba2` (`--accent-color`/`--accent-color-2`), Lato, sidebar structure |
| F5 | Forking or duplicating `styles.css`, or per-page stylesheets that restate the theme | One source of truth; drift is invisible until it isn't. Use the Solution menu instead |
| F6 | Editing `store/products.json` without rerunning `scripts/build-store.py` | Commit 0860584: price changed in JSON, build skipped, committed JSON-LD still shows the old price as of 2026-07-05 — the canonical forgot-to-run-build failure |
| F7 | Adding npm, bundlers, frameworks, or a build step | Architecture contract: plain HTML/CSS/JS + one Python script is deliberate; owner conversation required |
| F8 | Merging to main with a failing validation script or skipping them | main IS production; there is no staging to catch it |
| F9 | Copying nav markup directly into a page instead of the sidebar fetch | Nav forks immediately; every future link addition breaks on that page |

## SOLUTION MENU — "the new page needs X the architecture lacks"

Ranked. Take the LOWEST number that works; each step up carries an obligation.

1. **Reuse existing `styles.css` classes** (`.section`, `.project-item`, `.content`, buttons…).
   Obligation: none. Always try first — grep styles.css before assuming a class is missing.
2. **Page-inline `<style>` extending theme variables.** Precedent: `store.html`'s inline
   block built on `var(--accent-color)` etc. Obligation: colors ONLY via `var()` of existing
   tokens; no literal hex that isn't already a token; no new fonts.
3. **New shared section appended to `styles.css`.** Obligation: additive only — zero changes
   to existing tokens/selectors; `check_invariants.py` visual-identity tripwire must still pass.
4. **New JSON data file + client-side fetch** (the store pattern). Obligation: if the content
   is SEO-relevant, a static/noscript fallback like `store.html`'s generated `<noscript>` —
   crawlers and JS-off users must see the content.
5. **Anything touching visual identity, nav structure, or architecture** (new fonts, layout
   system, framework, second stylesheet) → STOP. Owner conversation first, via
   `mkhome-architecture-contract` + `mkhome-change-control`. No exceptions.

## PROMOTION PROTOCOL — definition of done

A growth change is DONE only when every line below is checked, all through
`mkhome-change-control`:

- [ ] `python3 .claude/skills/mkhome-validation-and-qa/scripts/check_invariants.py` → exit 0
- [ ] `python3 .claude/skills/mkhome-validation-and-qa/scripts/check_store_sync.py` → exit 0
- [ ] `python3 .claude/skills/mkhome-validation-and-qa/scripts/smoke_serve.py` → exit 0
- [ ] JS-off: SEO-relevant content visible in raw HTML (`curl`, not browser-with-JS)
- [ ] Sitemap entry present (pages): `grep -c '<page>.html' sitemap.xml` → 1, produced by
      build-store.py, not by hand
- [ ] Post-deploy production sentinel: `curl -s https://mkhome.byst.re/<page or store>.html`
      returns the new content (route deploy verification via `mkhome-deploy-and-operate`)
- [ ] OG validator clean for any new page URL
- [ ] README structure tree updated if a file was added (route via `mkhome-docs-and-writing`)

Not judged by eye at any point. If a box cannot be checked with a command or validator
output, the change is not done.

## Provenance and maintenance

- Authored 2026-07-05 against repo state at commit 878a7f0. All commands and expected
  observations were dry-run against a scratch copy of the repo on that date: dummy-page
  sitemap pickup (`newpage.html` → one `<url>` at priority 0.5 + full lastmod churn),
  `json.tool` validation, `git diff --stat` shapes, `grep -c '"og:image"' → 1` and
  sitemap-count sentinels via `python3 -m http.server`.
- The 0860584 price drift (JSON-LD 9.99 vs products.json 10.49) was live and reproduced in
  scratch on 2026-07-05; once someone reruns the build and commits, A4's "corrective churn"
  note becomes historical.
- Validation scripts under `.claude/skills/mkhome-validation-and-qa/scripts/` were being
  authored in parallel on 2026-07-05; if a path 404s, check that skill's directory and
  update the three invocations here.
- Re-verify after: changes to `scripts/build-store.py` (sitemap priorities, markers),
  completion of the jQuery removal debt (B1 donor guidance simplifies), any new donor page,
  or a change to the head contract in `index.html`.
- Owner rules cited (visual identity, hardest-problem statement) were stated 2026-07-05;
  confirm with the owner before relaxing any fence.
