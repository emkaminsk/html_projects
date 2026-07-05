---
name: mkhome-frontier-and-method
description: >
  The improvement frontier and the method for advancing it on mkhome.byst.re
  (Marcin Kaminski's static site). Load when proposing ANY improvement to the
  site, prioritizing tech-debt work, deciding what to work on next, evaluating
  "should we fix X or Y first?", or turning a hunch/idea into an accepted
  change. Lists the ranked open problems (sidebar/jQuery unification, SRI+CSP,
  CI-gated validation, head-metadata generation, multilingual crawlability,
  cache-busting, sitemap lastmod) with concrete first steps and falsifiable
  milestones, plus the claim→experiment→refutation→adoption discipline every
  change must follow. Everything here is a CANDIDATE, not a decision.
---

# mkhome Frontier and Method

**Owner's definition of state-of-the-art for THIS project (2026-07-05, definitive):**
"Fully AI-maintainable site — any Sonnet-class session can ship a verified change
end-to-end with zero human review; the skill library IS the product."
Every frontier item below is ranked by how much it advances *that* goal, not by
generic web best practice.

**Status discipline — read this first.** Every item below is labeled `OPEN`
(verified still undone as of 2026-07-05) or `CANDIDATE` (a proposed direction,
not yet designed). **Nothing in this file is decided or pre-approved.** Adoption
of any item requires owner approval routed through `mkhome-change-control`.
Before acting on any item, re-verify it with the grep commands in
"Provenance and maintenance" — a sibling session may have shipped it since.

## When NOT to use this skill

- You are executing an already-approved change → use `mkhome-change-control` + the domain skill.
- Something is broken right now → `mkhome-debugging-playbook`.
- You need the current invariants → `mkhome-architecture-contract` (this file only *references* them).
- You are writing content/docs → `mkhome-docs-and-writing`.
- You want to know whether an idea was already tried and killed → `mkhome-failure-archaeology` FIRST.

---

# HALF 1 — THE FRONTIER

Seven open problems. Format per item: why current state falls short → this
project's specific asset → first three steps in this repo → falsifiable
milestone → invariants and skills touched.

## F1. Unify sidebar loading and remove jQuery — `OPEN`

- **Falls short (as of 2026-07-05):** TWO loader mechanisms coexist. `index.html` and `store.html` use `<nav class="sidebar" id="sidebar">` filled by a vanilla `fetch('sidebar.html')` in `script.js` (lines 1–10). `portfolio.html`, `projects.html`, `utilities.html` use `<div class="sidebar">` filled by inline `$('.sidebar').load('sidebar.html', ...)` with jQuery 3.6.0 from CDN. Any sidebar change must be tested against both paths; jQuery exists ONLY for this and submenu toggles. `.ai/transformation-checklist.md` line 13 already demands jQuery removal (unchecked).
- **Asset:** the correct mechanism already ships and works on 2 of 5 pages — this is a port, not an invention.
- **First three steps:** (1) diff the inline jQuery callback in `portfolio.html` (~line 104) against `script.js`'s `initializeSidebar()` to enumerate every behavior the jQuery path provides (submenu toggle, active states); (2) convert `portfolio.html` alone: swap `<div class="sidebar">` → `<nav class="sidebar" id="sidebar">`, add `<script src="script.js">`, delete the jQuery `<script>` tags; (3) verify with the `mkhome-validation-and-qa` DOM/smoke checks + manual mobile-viewport check, then repeat for `projects.html`, `utilities.html`.
- **Milestone:** all 5 sidebar pages use one mechanism; `grep -rn "jquery" *.html` returns nothing; smoke + DOM checks pass; hamburger works on mobile viewport on every page.
- **Touches:** sidebar/hamburger contract and no-framework invariant (`mkhome-architecture-contract`); JS-behavior change class (`mkhome-change-control`); the hamburger incident history (`mkhome-failure-archaeology` — PR #1/8b05870 is the costliest failure on record; treat any sidebar DOM change as high risk).

## F2. Supply-chain hardening: SRI + CSP meta — `OPEN`

- **Falls short (as of 2026-07-05):** `grep -c integrity *.html` = 0 on all 9 pages. CDN dependencies: Bootstrap 5.3.0 CSS+JS (jsdelivr), Font Awesome 6.0.0 (cdnjs), Google Fonts, jQuery 3.6.0 (3 pages), GoatCounter. A compromised CDN executes arbitrary JS on the site. `.ai/transformation-checklist.md` lines 9 and 234 demand SRI; line 301 demands CSP — all unchecked.
- **Asset:** the checklist already specifies the work; pinned versions in the URLs make hashes stable; site has zero inline-event-handler debt to fight CSP over (verify before claiming in a PR).
- **First three steps:** (1) generate hashes: `curl -s <cdn-url> | openssl dgst -sha384 -binary | openssl base64 -A`; (2) add `integrity="sha384-..." crossorigin="anonymous"` to every CDN `<link>`/`<script>` on ONE page, verify headless render identical; (3) draft CSP `<meta http-equiv="Content-Security-Policy">` in report-friendly strictness (allow the exact CDN hosts + GoatCounter + `'unsafe-inline'` only if inline scripts genuinely require it — the tool pages have inline `<script>` blocks, so plan for that), test on one page before rollout. NOTE: check `mkhome-failure-archaeology` for prior CSP/SRI attempts before starting.
- **Milestone:** every CDN tag carries `integrity`+`crossorigin`; CSP meta present on all pages; all pages render identically (headless screenshot or DOM-diff before/after); Google Fonts caveat handled (fonts CSS is UA-varying — either self-host Lato or exclude that link from SRI with the reason documented).
- **Touches:** visual-identity invariant (a wrong hash silently kills Bootstrap/Lato → unstyled page); security posture; `mkhome-validation-and-qa` for the render-identical proof.

## F3. CI-gated validation on PRs — `OPEN` — **highest leverage**

- **Falls short (as of 2026-07-05):** the only workflow, `.github/workflows/deploy.yml`, does `git pull` on the VPS on push to main. No check ever blocks a bad merge. Validation scripts (sibling skill `mkhome-validation-and-qa`, `.claude/skills/mkhome-validation-and-qa/scripts/`) run only when a session remembers to run them. Zero-human-review shipping is impossible while merging is unguarded.
- **Asset:** the validation scripts exist as of today — CI is wiring, not authorship. (Verify the scripts directory exists before writing the workflow; the sibling skill may still be landing.)
- **First three steps:** (1) list the scripts and confirm each exits non-zero on failure (a CI gate needs exit codes, not prose); (2) write `.github/workflows/validate.yml` triggered on `pull_request`, running each script; (3) prove the gate: open a PR that deliberately breaks an invariant (e.g. delete `id="sidebar"` from `index.html`) and confirm a red check, then close it unmerged.
- **Milestone:** a PR with a deliberately broken invariant gets a red check; a clean PR gets green. The red-check PR is the proof artifact — link it in the adoption record.
- **Touches:** main-is-production invariant (`mkhome-change-control` — this ADDS a guard, changes no site file); `mkhome-deploy-and-operate` (workflow anatomy); `mkhome-validation-and-qa` (the scripts themselves).

## F4. Head-metadata generation without a framework — `CANDIDATE`

- **Falls short (as of 2026-07-05):** every page hand-copies ~20 lines of `<head>` metadata. Verified drift: `og:image` on index/portfolio/projects/utilities/store ALL point at `https://mkhome.byst.re/store/assets/og-image.png` — the store's image fronts every page. Verified gap: `json_prettifier.html`, `morse_converter.html`, `qr_code_generator.html`, and `sidebar.html` have NO `<meta charset>` (latent mojibake; `sidebar.html` is a fragment so charset there is N/A — the three tool pages are the real defect). No mechanism propagates a head fix to all pages.
- **Asset:** the repo already accepts generated HTML — `scripts/build-store.py` writes generated blocks and sitemap. Extending the generate-into-static-files pattern violates nothing.
- **First three steps:** (1) inventory actual head divergence: `grep -n "og:image\|charset\|description" *.html`; (2) design the smallest mechanism honoring the static-output invariant — e.g. a `scripts/build-heads.py` that rewrites a marked block (`<!-- head:begin -->…<!-- head:end -->`) in each page from one manifest, mirroring build-store.py's generated-block convention; committed output stays plain HTML; (3) pilot on the three tool pages (fixes the charset defect as the first propagated edit).
- **Milestone:** one edit to the manifest propagates to all pages, proven by `git diff` showing identical changes in every page; per-page fields (title, description, og:image) stay per-page. **Obligation:** static-output invariant holds — no runtime templating, no npm, no framework.
- **Touches:** no-framework/no-build-step invariant (`mkhome-architecture-contract` — a repo-side generator in the build-store.py mold is the only acceptable shape, and even that needs owner sign-off since it changes the editing workflow); `mkhome-seo-reference` (head contract); `mkhome-store-pipeline` (generated-block convention).

## F5. Real multilingual crawlability for the store — `CANDIDATE`

- **Falls short (as of 2026-07-05):** `store.html` lines 11–14 declare hreflang en/es/pl/x-default ALL pointing at the same URL; language switching is client-side JS. Crawlers see only the Spanish `<noscript>` content (verified: noscript block at lines 419–460 is Spanish-only). EN/PL product content is invisible to search engines — in the site's primary market strategy (Spanish-speaking seniors, `doc/seo-implementation-plan.md`) the secondary languages currently contribute zero SEO.
- **Asset:** `store/products.json` already holds all three languages; `build-store.py` already generates static output — generating `store.en.html` / `store.pl.html` (or `/en/store.html`) is an extension of the existing pipeline, not new machinery.
- **First three steps:** (1) read `mkhome-seo-reference` for the hreflang contract — per-language URLs must cross-reference each other + x-default; (2) extend `build-store.py` to emit per-language static pages from `products.json`, each with correct `lang` attr, hreflang cluster, canonical, and localized noscript/JSON-LD; (3) validate with Google Rich Results test + an hreflang validator before proposing adoption.
- **Milestone:** `curl -s https://mkhome.byst.re/store.en.html | grep -c "<h2>"` (JS off) shows English product content; hreflang cluster validates; existing Spanish rich results still pass. **Obligation:** theory per `mkhome-seo-reference` + external validator proof, not vibes.
- **Touches:** noscript-store and generated-blocks invariants (`mkhome-change-control` non-negotiables); sitemap (new URLs); `mkhome-store-pipeline`; `mkhome-seo-reference`.

## F6. Cache-busting versioned assets — `OPEN`

- **Falls short (as of 2026-07-05):** `.deploy/mkhome` caches css/js 1h (`expires 1h`, line 28) and images 1w; line 26 is a comment saying "consider using versioning (styles.css?v=timestamp)" — never implemented. Every CSS/JS deploy has up to a 1-hour window where users (and verifying AI sessions) see stale assets; this has repeatedly wasted debugging time (see `mkhome-failure-archaeology`, stale-CSS entries).
- **Asset:** the fix is named in the repo's own nginx config comment; if F4's head generator exists, stamping `?v=<content-hash>` on asset links is one function in the same script.
- **First three steps:** (1) decide scheme: query-string `styles.css?v=<8-char sha>` needs zero nginx changes (nginx serves same file; the URL change busts browser/CDN cache); (2) add hash-stamping to the generation step (or a tiny `scripts/stamp-assets.py`) rewriting `href="styles.css?v=…"` in all pages; (3) after one real deploy, prove propagation.
- **Milestone:** deploy a visible CSS change, then within the old 1h TTL window `curl -s https://mkhome.byst.re/index.html | grep 'styles.css?v='` shows the new hash and fetching that URL returns the new CSS — immediate propagation, no cache flush.
- **Touches:** deploy chain (`mkhome-deploy-and-operate` cache policy table); pairs naturally with F4; nginx changes, if any, are owner-approval class per `mkhome-change-control`.

## F7. Meaningful sitemap lastmod — `OPEN`

- **Falls short (as of 2026-07-05):** `scripts/build-store.py` lines 109–119 write `date.today()` as `<lastmod>` for every URL on every run — after any rebuild, all 8 lastmod entries churn to today (currently all read 2026-03-07, i.e. the last build date). Crawlers learn to ignore a lastmod that always changes; the signal is dead weight.
- **Asset:** the repo is git-native — `git log -1 --format=%cs -- <file>` gives an honest per-page modification date with zero new infrastructure.
- **First three steps:** (1) in `build-store.py`, replace `today` with per-URL `git log -1 --format=%cs -- <page>` (fallback to today only for files with no history); (2) rebuild twice with no content change and diff `sitemap.xml`; (3) touch one page, rebuild, confirm only that URL's lastmod moved.
- **Milestone:** two consecutive `build-store.py` runs with unchanged content produce a byte-identical `sitemap.xml`; editing exactly one page changes exactly one `<lastmod>`.
- **Touches:** store pipeline generated output (`mkhome-store-pipeline`); low risk, but sitemap is SEO surface → `mkhome-seo-reference` sanity check.

## Recommended order (leverage toward AI-maintainability)

| Rank | Item | One-line justification |
|---|---|---|
| 1 | F3 CI-gated validation | The force multiplier: converts every other skill's checks into an automatic gate — the literal precondition for "zero human review". |
| 2 | F1 Sidebar/jQuery unification | Halves the test surface of the site's most incident-prone component and retires a whole dependency; do it AFTER F3 so the gate protects the riskiest port. |
| 3 | F7 Sitemap lastmod | Smallest diff on the list; makes builds deterministic, which makes F3's checks sharper (byte-identical rebuild becomes assertable). |
| 4 | F4 Head generation | Turns 9 hand-synced heads into 1 verified source; unblocks F6 and fixes the charset + og:image drift in one mechanism. |
| 5 | F6 Cache-busting | Removes the 1h stale window that corrupts every post-deploy verification an AI session performs. |
| 6 | F2 SRI + CSP | Real security value but low AI-maintainability leverage; visually risky, so wants F3's gate + F1's simplified script surface first. |
| 7 | F5 Multilingual crawlability | Biggest scope, needs external validators and owner SEO-strategy input; build on a stabilized pipeline (F4/F7 done). |

---

# HALF 2 — THE METHOD

The discipline that turns a hunch into an accepted change in this repo. Five
steps, in order, no skipping.

## Step 1 — Write the claim BEFORE touching anything

State (a) the mechanism you believe is at work, and (b) the **predicted
measurable observation**: exact numbers or strings a command will print if you
are right — and what it prints if you are wrong. "It should work better" is not
a claim. `curl -s URL | grep -c '<h2>' prints 3, currently prints 0` is a claim.
Write it down in the PR description or scratch notes before the first edit.

## Step 2 — Build the discriminating experiment

Use `mkhome-analysis-toolkit` for measurement methods. A discriminating
experiment is one whose outcome differs depending on which hypothesis is true —
if every hypothesis predicts the same output, the experiment is decoration.
Prefer: curl against production/local, headless DOM queries, `git diff` of
generated output, validator APIs.

## Step 3 — One mechanism must explain ALL observations

Including the negatives: why it did NOT fail elsewhere, why it only fails on
mobile, why the second run differs from the first. If your explanation covers
the failure but not the places that work, you have a correlation, not a
mechanism. (The hamburger case below is the canonical example: "button missing
on mobile only" was explained only by a mechanism — transform → containing
block — that also predicted it working on desktop, where no transform applies.)

## Step 4 — Adversarial pass: try to refute your own fix

Standard refutation moves for THIS repo — run every one that applies:

| Move | How | Catches |
|---|---|---|
| JS off | curl the raw HTML / disable JS; check noscript content | Fixes that only exist client-side; crawler-invisible content (F5-class bugs) |
| Mobile viewport | headless at 375px width; tap targets, `transform` side effects | The hamburger trap class of bug — desktop-only verification is how PR #1's bug shipped |
| Cold cache | fresh curl with no cache headers honored; check against the 1h css/js TTL | "Works on my session" staleness; anything F6 exists to kill |
| Crawler view | fetch as a bot: no JS, check `<head>`, JSON-LD, hreflang, noscript | SEO regressions invisible in a browser |
| Second build-store run | run `scripts/build-store.py` twice; diff generated blocks + sitemap | Non-determinism, lastmod churn (F7), generated-block clobbering |

A fix that survives all applicable moves is a candidate. One that you didn't
try to refute is a guess.

## Step 5 — Idea lifecycle (where each stage lives)

```
hunch
  → scratch experiment            (scratchpad; nothing committed)
  → branch + validation scripts   (mkhome-validation-and-qa evidence bar)
  → owner-gated adoption          (mkhome-change-control — NOTHING merges without this)
  → README/docs update            (mkhome-docs-and-writing)
  → if rejected or abandoned      (record the dead end in mkhome-failure-archaeology
                                   with evidence, so no future session re-fights it)
```

The last arrow is mandatory, not optional: an unrecorded dead end costs the
next session everything it cost you.

## Worked example — the hamburger fix (settled case, PR #1 / commit 8b05870)

**Label: this is a reconstruction** from the commit message and diff of
8b05870 ("Fix mobile navigation: move hamburger button outside sidebar",
2026-06-06, merged as PR #1 in 01136cc) — the method is being retro-fitted onto
real evidence to show what each step looks like; the original session did not
necessarily write these artifacts in this order.

1. **Claim + predicted observation:** *Mechanism:* `#menuToggle` sits inside
   `.sidebar`, which has `transform: translateX(-100%)` on mobile; a transformed
   ancestor becomes the containing block for `position: fixed` descendants, so
   the "fixed" button is dragged off-screen with the sidebar. *Prediction:* at
   mobile width, `getBoundingClientRect()` of `#menuToggle` has `x < 0`; at
   desktop width (no transform) it is on-screen. If the mechanism were instead
   z-index or display, the rect would be on-screen but occluded/absent — the
   prediction discriminates.
2. **Experiment:** inspect the button's rect at 375px vs desktop. Off-screen
   coordinates at mobile only → containing-block mechanism confirmed; it also
   explains the key negative (desktop unaffected — no transform applies there).
3. **Fix consistent with the mechanism:** don't fight the transform — move the
   button out of the transformed subtree. 8b05870 has `script.js` create
   `#menuToggle` and a `#sidebarBackdrop` directly on `<body>`
   (`document.body.appendChild(menuToggle)`, script.js lines 27–37), removing
   them from `sidebar.html` (diff: 63 lines changed there).
4. **Refutation pass (reconstructed):** mobile viewport — button visible and
   tappable at 375px, sidebar slides over backdrop, backdrop tap closes
   (standard drawer pattern per the commit message); desktop — unchanged
   layout; JS off — sidebar pages already require JS for nav injection, so no
   regression class added; cold cache — new script.js subject to the 1h TTL,
   verify post-deploy with a fresh fetch.
5. **Adoption:** shipped via branch → PR #1 → merge to main (01136cc) →
   auto-deploy. The residue is codified as the sidebar/hamburger contract in
   `mkhome-architecture-contract` and the incident record in
   `mkhome-failure-archaeology` — which is why every F1 step above treats
   sidebar DOM changes as high-risk.

Cost note: this bug is on record as the project's costliest failure. It shipped
because verification was desktop-only — one missing refutation move. That is
the argument for Step 4 being non-negotiable.

---

## Provenance and maintenance

All claims verified against the working tree and git history on 2026-07-05.
Before acting on any frontier item, re-check it is still open:

- **F1 (jQuery/sidebar):** `grep -rn "jquery" /home/user/html_projects/*.html` — empty ⇒ done. Two mechanisms: `grep -n 'class="sidebar"' *.html` (mixed `<div>`/`<nav id="sidebar">` ⇒ still split).
- **F2 (SRI/CSP):** `grep -c integrity *.html` (all 0 ⇒ open) and `grep -rn "Content-Security-Policy" *.html` (empty ⇒ open).
- **F3 (CI gate):** `ls .github/workflows/` — only `deploy.yml` ⇒ open. Also confirm scripts exist: `ls .claude/skills/mkhome-validation-and-qa/scripts/` (dir was still landing on 2026-07-05 — verify before citing).
- **F4 (heads):** `grep -L "charset" json_prettifier.html morse_converter.html qr_code_generator.html` (any output ⇒ charset gap remains); `grep -n "og:image" *.html | grep -v store/assets` (empty ⇒ og:image drift remains — all pages still point at the store image).
- **F5 (multilingual):** `grep -n hreflang store.html` — all four alternates same URL ⇒ open; `ls store.en.html 2>/dev/null` or equivalent per-language pages ⇒ done.
- **F6 (cache-busting):** `grep -n "?v=" *.html` (empty ⇒ open); nginx comment at `.deploy/mkhome` line ~26.
- **F7 (lastmod):** `grep -n "date.today\|today =" scripts/build-store.py` (present and used for lastmod ⇒ open).
- **error404 side-finding (as of 2026-07-05):** `.deploy/mkhome` line 10 sets `error_page 404 /error404.html` but `error404.html` does NOT exist in the repo — live 404-of-the-404 candidate; verify with `ls error404.html` and report via `mkhome-debugging-playbook`/`mkhome-change-control` if still absent.
- **Hamburger case facts:** `git show 8b05870 --stat` and `git log --oneline | grep 01136cc`.
- **This file:** update status labels only with evidence (command output or merged PR link); when an item ships, flip it to `DONE (PR #N, date)` — do not delete it, later sessions need the trail.
