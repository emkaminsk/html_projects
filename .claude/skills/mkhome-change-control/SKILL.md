---
name: mkhome-change-control
description: >
  Load BEFORE making ANY change to the mkhome.byst.re repo (static personal site of
  Marcin Kaminski). Classifies every change type (content edit, products.json/store,
  new page, CSS/styling, JS behavior, nginx/deploy, docs), states its risk level and
  required verification, lists the project's non-negotiables (visual identity, generated
  blocks, main-is-production, hidden-dir blocking, sidebar/hamburger contract, noscript
  store) with the incident behind each, and defines what an AI session may decide alone
  vs. what needs owner approval. Use when planning an edit, opening a PR, deciding
  whether to touch styles.css / store.html / sitemap.xml / nginx config, or judging
  whether a git diff is safe to merge to main.
---

# mkhome Change Control

Repo: static site (plain HTML/CSS/JS, no framework, no npm, no tests) live at
https://mkhome.byst.re. **Any push to `main` deploys to the production VPS within
minutes** via `.github/workflows/deploy.yml` (appleboy/ssh-action runs `git pull` on the
server). There is no staging environment. This skill tells you what class of change you
are making, which gates apply, and what you are never allowed to change silently.

Definitions used below:
- **build-store.py** = `scripts/build-store.py`; reads `store/products.json`, regenerates
  the JSON-LD and `<noscript>` blocks inside `store.html` (between marker comments) and
  rewrites `sitemap.xml` from all root `*.html` files (skips `sidebar.html`).
- **Generated block** = anything between `<!-- SEO:JSON-LD -->`/`<!-- /SEO:JSON-LD -->`
  or `<!-- SEO:NOSCRIPT -->`/`<!-- /SEO:NOSCRIPT -->` in `store.html`, plus all of
  `sitemap.xml`. Machine-written; hand edits are overwritten on the next build.
- **Visual identity** = brand gradient `#667eea → #764ba2` (`--accent-color` /
  `--accent-color-2` in `styles.css` lines 10–11), Lato typography, sidebar structure.

## When NOT to use this skill

- Diagnosing a live breakage → `mkhome-debugging-playbook`.
- How to run/edit the store build itself, products.json schema → `mkhome-store-pipeline`.
- Setting up venv/local server from scratch → `mkhome-build-and-env`.
- Deploy mechanics, nginx details, cache verification → `mkhome-deploy-and-operate`.
- Concrete verification commands/checklists per change → `mkhome-validation-and-qa`.
- SEO tag specifics (OG, hreflang, JSON-LD) → `mkhome-seo-reference`.
- Adding a whole new page/tool/product end-to-end → `mkhome-site-growth-campaign`.
- Why the architecture is the way it is → `mkhome-architecture-contract`.
- Past incidents in narrative detail → `mkhome-failure-archaeology`.

## 1. Change classification

Classify FIRST, then apply the row. If a change spans rows, apply the strictest row.

| Class | Examples | Risk | Required verification (details in mkhome-validation-and-qa) | Owner approval? |
|---|---|---|---|---|
| Docs-only | `doc/`, `.ai/`, `README.md` | Low | Read back; confirm no root `*.html` touched (else sitemap picks it up on next build) | No |
| Content-only edit | Text/typo/link inside an existing page, outside `<head>` and outside generated blocks | Low | Local preview (`python3 -m http.server 8000`), click the changed page, sidebar still loads | No |
| Store/product change | Any edit to `store/products.json` | Medium | **MUST run `python3 scripts/build-store.py` after editing** (README rule); `python3 -m json.tool store/products.json`; check diff of store.html generated blocks; verify diacritics survive (incident f2194d1) | No, unless price/product removal — confirm with owner |
| New page | New root `*.html` | Medium-High | Full head metadata (description, canonical, OG + `og:image:width/height`, Twitter), GoatCounter snippet, link added in `sidebar.html`, run build-store.py to regenerate sitemap, local preview on desktop AND narrow viewport | No for the page itself; Yes if it needs new global CSS |
| Styling change | Any edit to `styles.css` or inline styles | High | **Visual-identity gate (non-negotiable a)**; screenshot/compare before-after at mobile and desktop widths; verify sidebar transform behavior intact | YES if gradient, Lato, or sidebar structure is affected — otherwise no, but stay within existing CSS variables |
| JS behavior change | `script.js`, inline scripts, tool pages' JS | High | Local preview with browser console open; test the sidebar/hamburger on a narrow viewport (incident 8b05870); test store.html with JS disabled still shows noscript cards | No, unless it changes navigation UX |
| nginx / deploy config | `.deploy/mkhome`, `nginx.conf.example`, `.github/workflows/deploy.yml` | HIGHEST — touches the production server | `nginx -t` on the VPS before reload; after deploy, `curl -I` the hidden-dir URLs (must be 403) and cache headers (incidents d3b862c/0ac08b4 and the hidden-dir exposure) | YES, always |

Notes:
- The three tool pages (`json_prettifier.html`, `qr_code_generator.html`,
  `morse_converter.html`) have NO sidebar, NO `styles.css`, NO `script.js` (verified).
  Do not "fix" that uninvited — it is a standing design choice; adding the sidebar to
  them is a styling + JS change requiring the rows above and owner sign-off.
- Sidebar loading is split: `index.html`/`store.html` use `script.js`
  (`fetch('sidebar.html')` into `#sidebar`; `#menuToggle` and `#sidebarBackdrop` are
  created dynamically on `<body>`), while `portfolio.html`/`projects.html`/
  `utilities.html` use jQuery `$('.sidebar').load('sidebar.html', ...)` inline. A change
  to `sidebar.html` affects BOTH mechanisms — test at least one page of each kind.

## 2. Non-negotiables (rule → rationale → incident)

Never advise or attempt routing around these. Each exists because it already went wrong
once, or because the owner said so explicitly.

**(a) PRESERVE VISUAL IDENTITY.** Brand gradient `#667eea → #764ba2`
(`--accent-color`/`--accent-color-2`, `styles.css` lines 10–11), Lato font-family,
sidebar structure. Owner-stated rule (2026-07-05): never change any of these without
explicit owner approval. Rationale: this is the owner's personal brand across every
page; an AI session has no authority over brand. There is no incident — the rule is
preventive and absolute.

**(b) Never hand-edit generated blocks.** Do not edit `store.html` between the
`SEO:JSON-LD` or `SEO:NOSCRIPT` markers, and never hand-edit `sitemap.xml`. Always edit
`store/products.json` and run `python3 scripts/build-store.py`. Rationale: the script is
idempotent — it replaces everything between the markers (README documents this;
`inject_between_markers()` in the script confirms it), so hand edits are silently
destroyed on the next run. Evidence: README "Build Scripts" section; commit f2194d1
shows content fixes correctly went through products.json.

**(c) main IS production.** `.github/workflows/deploy.yml` triggers on every push to
`main` and pulls on the VPS — there is no review step, no staging, no rollback tooling.
Nothing lands on `main` unverified. Work on a branch, verify locally, then PR/merge.
Incident: caching problems (d3b862c "attempt to fix caching problem", 0ac08b4 "fix:
nginx config") were debugged live in production because main deploys immediately.

**(d) Never expose hidden directories.** `.ai/`, `.cursor/`, `.github/`, `.git/` must
stay blocked by the nginx `location ~ /\.` deny rule (present in `.deploy/mkhome` lines
11–16). Incident: these dirs were publicly reachable until the deny rules were added
(documented in `.ai/deployment-security.md`, which includes the `curl -I` 403
verification). Corollary: never weaken that location block, and never move secrets or
internal notes into a served path.

**(e) Don't break the sidebar/hamburger contract.** `#menuToggle` and `#sidebarBackdrop`
MUST be created on `<body>` by `script.js` — never placed inside `.sidebar`. Rationale:
`.sidebar` gets `transform: translateX(-100%)` on mobile, and a transformed parent
becomes the containing block for `position: fixed` children, so any fixed button inside
it is dragged off-screen and unreachable. Incident: commit 8b05870 / merged PR #1 ("Fix
mobile navigation: move hamburger button outside sidebar") — the owner's stated
costliest past failure. Any change to sidebar CSS transforms, `script.js` DOM creation,
or sidebar.html structure must re-test mobile nav on a narrow viewport.

**(f) store.html must work without JavaScript.** Crawlers and no-JS visitors must see
the `<noscript>` Spanish product cards (store.html lines ~418–461) and the JSON-LD.
Rationale: the SEO plan (`doc/seo-implementation-plan.md`) targets crawlers that don't
execute JS; the noscript block is the only crawlable product content. Any store change
must leave a valid noscript block in place — which follows automatically from rule (b):
edit products.json, run build-store.py.

## 3. Gate procedure (branch → verify → merge = deploy)

1. **Branch.** Never commit on `main`. Observed convention: `claude/<topic>-<suffix>`
   (e.g. `claude/project-overview-KJDjF`, `claude/skill-library-handoff-2ytie3`).
   ```bash
   git checkout -b claude/short-topic-xxxxx
   ```
2. **Make the change** per its classification row above.
3. **Run build-store.py when applicable** — required after ANY products.json edit, and
   after adding/removing/renaming any root `*.html` (sitemap regeneration):
   ```bash
   python3 -m venv venv && source venv/bin/activate && pip install Pillow  # only if venv absent (it is gitignored)
   python3 scripts/build-store.py
   ```
   (build-store.py itself uses only stdlib; Pillow is needed only for
   `scripts/generate-og-image.py`.)
4. **Verify locally.** The sidebar fetch fails on `file://`, so always use a server:
   ```bash
   python3 -m http.server 8000   # then open http://localhost:8000/
   ```
   Apply the verification column for your change class; deeper checklists live in
   `mkhome-validation-and-qa`.
5. **Judge generated churn in the diff.** `generate_sitemap()` stamps `<lastmod>` with
   today's date on EVERY url on EVERY run — so a build-store run always dirties
   `sitemap.xml` even when nothing meaningful changed. Rules of thumb:
   - sitemap diff = only `<lastmod>` lines changed → expected noise; commit it with the
     change that legitimately triggered the build.
   - sitemap diff = a `<loc>` added/removed → must exactly match the page you
     added/removed; anything else means a stray root `*.html` exists — investigate.
   - store.html diff outside the SEO marker pairs when you only edited products.json →
     wrong; the script must not touch anything outside the markers. Stop and inspect.
   - Do NOT run build-store.py gratuitously "to be safe" in an unrelated change — it
     creates pure-lastmod churn that buries real diffs.
6. **PR and merge to main = deploy.** Merging is the deploy action (rule c). After
   merge, verify production per `mkhome-deploy-and-operate` (HTML is served no-cache;
   CSS/JS are cached 1h, so style/JS changes can lag up to an hour — that is the cache
   policy from incidents d3b862c/0ac08b4, not a broken deploy).

## 4. Ask the owner vs. decide alone

**MUST ask the owner first:**
- Anything touching visual identity: gradient colors, Lato, sidebar structure/layout (rule a).
- nginx or deploy workflow changes (highest-risk class).
- Removing a product, changing a price, or changing `kdpUrl` targets.
- Adding the sidebar/styles to the three standalone tool pages, or unifying the two
  sidebar-loading mechanisms (architecture change).
- Deleting or renaming any live page/URL (breaks inbound links and sitemap history).
- Anything involving analytics account, domain, or third-party services.

**An AI session may decide alone (still branch + verify):**
- Typos, copy edits, link fixes within existing pages.
- products.json content fixes (descriptions, highlights, diacritics) + build-store run.
- Adding a new page that follows the existing template patterns (head metadata,
  GoatCounter, sidebar entry) without new global CSS.
- Bug fixes that restore documented behavior (e.g. re-fixing mobile nav), with the
  relevant incident's verification repeated.
- Docs under `doc/` and `.ai/` (they are nginx-blocked, not public).

Ignore `.cursor/rules/javascript.mdc` — it is a stale React-Native rules file and does
not apply to this repo. Do not follow it.

## Provenance and maintenance

All facts verified 2026-07-05 against the working tree. Re-verify before relying on them:

- Deploy-on-push-to-main: `cat .github/workflows/deploy.yml` (server script is `cd gitrepos/html_projects && git pull`).
- Brand variables/gradient: `grep -n "accent-color\|Lato" styles.css | head -5` (lines 10–11, 35 as of 2026-07-05).
- SEO markers in store.html: `grep -n "SEO:" store.html`.
- build-store behavior (markers, idempotence, sitemap lastmod=today): `sed -n '94,129p' scripts/build-store.py` and README section "Build Scripts".
- Hidden-dir deny rule: `grep -n -A4 'location ~ /\\\.' .deploy/mkhome`; incident doc: `cat .ai/deployment-security.md`.
- Hamburger incident: `git show 8b05870 -s --format='%B'`; merged as PR #1: `git show 01136cc -s --format='%B'`.
- Cache incidents: `git show d3b862c -s --format='%s'; git show 0ac08b4 -s --format='%s'`; policy: `grep -n -A3 'expires' .deploy/mkhome`.
- Diacritics incident: `git show f2194d1 -s --format='%s'`.
- Branch naming: `git log --all --oneline | grep claude/`.
- Split sidebar mechanisms: `grep -n "fetch('sidebar" script.js; grep -n "load('sidebar" portfolio.html projects.html utilities.html`.
- Tool pages have no sidebar/styles/script: `grep -c "sidebar" json_prettifier.html qr_code_generator.html morse_converter.html` (expect 0 0 0).
- GoatCounter on every page: `grep -ln goatcounter *.html` (all root pages except sidebar.html).
- Owner rules (visual identity, approval requirements): owner statements dated 2026-07-05 — not in-repo; re-confirm with owner if stale.
