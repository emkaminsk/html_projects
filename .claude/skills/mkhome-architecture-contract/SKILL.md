---
name: mkhome-architecture-contract
description: >-
  The architecture contract for the mkhome.byst.re static site: load-bearing
  design decisions with their WHY, invariants that must hold after any change,
  and known weak points. Load this BEFORE any structural or design change,
  BEFORE adding a new page or nav entry, BEFORE touching store.html /
  sidebar.html / styles.css / script.js / scripts/ / .deploy/, or whenever you
  wonder "why is it built this way?" or "can I change X?". Also load when
  tempted to introduce a framework, bundler, npm, templating, or a build step.
---

# mkhome architecture contract

This repo is the plain-HTML/CSS/JS personal site of Marcin Kaminski, live at
https://mkhome.byst.re. There is no framework, no bundler, no npm, no test
suite. The `main` branch IS production: a push triggers a GitHub Action that
SSHes to the VPS and runs `git pull` in the nginx web root. Every committed
file is a deployed artifact.

Definitions used below:
- **Generated block**: HTML committed to the repo but written by a script, delimited by marker comments.
- **Marker comments**: paired HTML comments (e.g. `<!-- SEO:JSON-LD -->` / `<!-- /SEO:JSON-LD -->`) that a script uses to find and replace a generated block idempotently.
- **Containing block**: the CSS ancestor box that a `position: fixed` element is positioned against. Normally the viewport — but per CSS spec, any ancestor with a `transform` becomes the containing block instead.

## When NOT to use this skill

- Editing product data or running the store build → `mkhome-store-pipeline`.
- Diagnosing a live breakage → `mkhome-debugging-playbook` first.
- nginx/VPS/deploy mechanics beyond what is stated here → `mkhome-deploy-and-operate`.
- SEO/meta/sitemap details → `mkhome-seo-reference`.
- Pure copywriting in existing pages with no structural change → no need for this file (but `mkhome-change-control` still applies).

## 1. Decision register

Verified against the working tree as of 2026-07-05.

| Decision | Why | Consequence if violated |
|---|---|---|
| Static site, no build step, no npm/bundler | Simplicity, and the deploy is literally `git pull` on the VPS (`.github/workflows/deploy.yml`) — committed files ARE the served artifacts | Adding a build step breaks deploy: the VPS runs nothing after pull. Output would be missing or stale in production |
| `scripts/build-store.py` output is COMMITTED (JSON-LD, noscript cards in store.html; sitemap.xml) | Follows from the above — since served files must be in git, generated content must be committed, not built on the server | If you regenerate but don't commit, production diverges from source of truth; if you hand-edit generated blocks, the next script run silently overwrites your edits |
| `store/products.json` is the single source of truth for products | One JSON drives three consumers: client-side rendering in store.html (3 languages), JSON-LD, noscript cards | Editing product text in store.html directly = your change lives in a generated block and is destroyed by the next `build-store.py` run |
| Marker-comment injection (`<!-- SEO:JSON-LD -->`…`<!-- /SEO:JSON-LD -->`, `<!-- SEO:NOSCRIPT -->`…`<!-- /SEO:NOSCRIPT -->` in store.html) | Idempotency contract: the script regex-replaces everything between markers, so it can run any number of times safely | Delete, rename, or reorder a marker and the regex silently fails to match — the script "succeeds" but injects nothing, or mangles the page |
| Sidebar is a shared fragment (`sidebar.html`) loaded at runtime via fetch/jQuery `.load()` | One nav definition for all sidebar pages; no templating system exists to inline it | Hardcoding nav into a page forks the menu (edits miss that page). Also: runtime include means the site REQUIRES an HTTP server — `fetch()` fails on `file://`; always preview via a local http server |
| Hamburger button `#menuToggle` + `#sidebarBackdrop` are created by script.js and appended to `<body>`, NOT placed inside `.sidebar` | CSS rule, exactly: an ancestor with a `transform` becomes the containing block for `position: fixed` descendants. `.sidebar` has `transform: translateX(-100%)` (styles.css ~line 896), so a fixed button inside it would slide off-screen with the sidebar on mobile. Deliberate fix — PR #1 / commit 8b05870 "Fix mobile navigation: move hamburger button outside sidebar" | Moving the button (or any `position: fixed` element) inside `.sidebar` re-breaks mobile navigation: the open/close button disappears exactly when the menu is closed |
| Per-file-type nginx caching (`.deploy/mkhome`): css/js 1h, images/fonts 1w, html no-cache | A past staleness incident: long-cached assets served stale UI after deploys. HTML is never cached so page updates land instantly; css/js get only 1h | Renaming asset types or changing cache headers casually reintroduces stale-after-deploy bugs. Remember css/js changes can take up to 1h to reach repeat visitors |
| Repo doubles as deploy artifact AND server-config store: `.deploy/mkhome` is a tracked COPY of the live nginx config | Keeps server config reviewable in git; dotdirs (incl. `.deploy/`, `.git/`, `.github/`) are denied by nginx (`location ~ /\.`) so they're safe to serve from | Editing `.deploy/mkhome` does NOT change the live server — someone must apply it on the VPS. The two can drift; treat the repo copy as intent, verify reality per `mkhome-deploy-and-operate` |
| Tool pages (json_prettifier.html, qr_code_generator.html, morse_converter.html) are standalone: no sidebar, no styles.css, no script.js | Intentional — small self-contained utilities with inline styles | "Fixing" them to match the site shell is scope creep and changes their look; do not retrofit the sidebar without owner approval |
| Visual identity is frozen: gradient `--accent-color: #667eea` → `--accent-color-2: #764ba2`, Lato font, sidebar structure | Owner's explicit non-negotiable (2026-07-05): preserve visual identity; no changes without owner approval | Any hue/font/nav-structure drift is a change-control violation even if the site still "works" |

## 2. Invariants checklist — must hold after ANY change

Run down this list before committing. All verified true as of 2026-07-05 except where noted.

- [ ] Every served HTML page carries the GoatCounter snippet (`data-goatcounter="https://emkaminsk.goatcounter.com/count"`). Currently on all 8 pages; sidebar.html is a fragment and must NOT have it.
- [ ] The five main pages (index, store, portfolio, projects, utilities) have full head metadata: `<meta charset="UTF-8">`, viewport, title, description, canonical, OG tags. (Known gap as of 2026-07-05: the three tool pages have minimal heads and NO charset meta — do not worsen this, and add full heads if you touch them anyway, with owner approval for anything visual.)
- [ ] Every link in sidebar.html resolves: internal hrefs (index.html, store.html, portfolio.html, utilities.html, projects.html, the three tool pages) exist in the repo root; external links are absolute URLs.
- [ ] store.html works with JavaScript disabled: the `<noscript>` block between `<!-- SEO:NOSCRIPT -->` markers exists and reflects the CURRENT store/products.json (re-run `scripts/build-store.py` after any product change).
- [ ] All four markers are present in store.html, in pairs, in order: `SEO:NOSCRIPT` open/close, `SEO:JSON-LD` open/close.
- [ ] sitemap.xml lists exactly the root-level `*.html` files minus sidebar.html (currently 8 URLs), and is only ever regenerated by `scripts/build-store.py` — never hand-edited.
- [ ] Visual identity tokens unchanged in styles.css: `--accent-color: #667eea`, `--accent-color-2: #764ba2`, and the Google Fonts Lato import in page heads.
- [ ] No `position: fixed` element lives inside `.sidebar` markup or gets appended into it by script (see containing-block rule above). `#menuToggle` and `#sidebarBackdrop` stay direct children of `<body>`.
- [ ] UTF-8 everywhere: files saved as UTF-8; charset meta present on full pages; `build-store.py` reads/writes `encoding="utf-8"` — keep it that way (product text is Spanish/Polish and breaks visibly otherwise).
- [ ] If you changed products.json or added/removed a root page: `build-store.py` was re-run AND its output (store.html, sitemap.xml) committed together with the source change.
- [ ] index.html and store.html still use `<nav class="sidebar" id="sidebar">` + script.js; portfolio/projects/utilities still have their inline jQuery loader intact (don't half-migrate one page).

## 3. Known weak points (as of 2026-07-05) — stated plainly

1. **TWO sidebar loader mechanisms.** index/store use vanilla `fetch` in script.js (with hamburger creation); portfolio/projects/utilities use inline jQuery `$('.sidebar').load(...)` with per-page active-link and submenu code. They can diverge (and mobile behavior already differs). New pages must use the script.js mechanism (`<nav class="sidebar" id="sidebar">` + script.js include). Unification is an open improvement candidate — see `mkhome-frontier-and-method`; do not unify ad hoc.
2. **Head metadata duplicated per page.** No templating: every new page copies ~20 lines of meta/link tags by hand. Drift risk is real (tool pages already drifted to minimal heads). Copy from index.html when creating a page.
3. **CDN dependencies unpinned by SRI.** Bootstrap 5.3.0, Font Awesome 6.0.0, Google Fonts Lato, jQuery 3.6.0, QRCode.js — version-pinned URLs but no `integrity` hashes and no CSP meta in HTML (nginx sends a partial CSP header). Open debt per `.ai/transformation-checklist.md`.
4. **No automated tests.** Nothing catches a broken page except manual checking — hence the invariants checklist above and `mkhome-validation-and-qa`.
5. **sitemap.xml lastmod churns.** `build-store.py` stamps every URL with today's date on every run, regardless of real changes. A build-only commit rewrites all 8 lastmod values; this is known noise, not a bug to "fix" in passing.
6. **Brand colors duplicated in Python.** `scripts/generate-og-image.py` hard-codes #667eea/#764ba2 to match styles.css. If (with owner approval) the palette ever changes, change it in BOTH places.
7. **hreflang tags on store.html all point at the same URL** (store.html lines 11–14: en, es, pl, x-default → all `https://mkhome.byst.re/store.html`). All languages share one page via a client-side switcher (localStorage key `storeLang`, default `en`), so the hreflang set is of debatable SEO value. Leave as-is unless doing deliberate SEO work.
8. **`.cursor/rules/javascript.mdc` is stale React-Native/Expo content** left over from another project. It claims `alwaysApply: true`. Ignore it entirely — this repo has no React.

## 4. Routing table — about to change X? Read Y first

| If you're about to… | Read first |
|---|---|
| Change ANYTHING visual (colors, fonts, layout, sidebar look) | `mkhome-change-control` (owner approval gate), then this file's decision register |
| Add a new page | This file (invariants + weak points 1–2), then `mkhome-seo-reference` for head/sitemap, then `mkhome-change-control` |
| Edit products, prices, translations, store copy | `mkhome-store-pipeline` (runbook lives there) — never edit generated blocks in store.html |
| Touch sidebar.html, script.js, or the jQuery loaders | This file (decision register rows 5–6, weak point 1) |
| Run or modify build-store.py / generate-og-image.py | `mkhome-build-and-env` (venv/Pillow setup), `mkhome-store-pipeline` |
| Touch .deploy/, deploy.yml, caching, headers | `mkhome-deploy-and-operate` |
| Fix a live bug | `mkhome-debugging-playbook`, and `mkhome-failure-archaeology` for prior incidents |
| Add features / grow the site | `mkhome-site-growth-campaign`, improvement candidates in `mkhome-frontier-and-method` |
| Verify your change before pushing | `mkhome-validation-and-qa` + section 2 checklist here |

## Provenance and maintenance

- Every claim verified 2026-07-05 by reading the working tree: script.js, sidebar.html, styles.css (lines 10–11, 887–955), store.html, scripts/build-store.py, sitemap.xml, .deploy/mkhome, .github/workflows/deploy.yml, .cursor/rules/javascript.mdc, page heads, and `git log` (commit 8b05870).
- Re-verify section 2 counts (8 pages, 8 sitemap URLs, 2 products) and all "(as of 2026-07-05)" facts before relying on them.
- Update this file when: a weak point is fixed (esp. sidebar-loader unification), a page is added/removed, markers or build scripts change, or the owner revises the visual-identity mandate.
