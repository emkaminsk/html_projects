---
name: mkhome-debugging-playbook
description: >
  Symptom-to-triage runbook for mkhome.byst.re (this repo). Load when something on the
  site is broken or misbehaving and the cause is unknown: sidebar missing or empty,
  hamburger/menu button gone or untappable on mobile, stale CSS/JS after deploy, store
  page blank, store in wrong language, broken social preview / OG image, mojibake or
  broken diacritics, page renders unstyled, 404 on a deployed page, hidden directory
  exposed. Gives the first command to run, expected output per hypothesis, and the
  branch to take.
---

# mkhome Debugging Playbook

Site: static HTML/CSS/JS, no framework, no bundler, live at https://mkhome.byst.re.
Deploy = push to `main` → GitHub Action SSHes to the VPS and runs `git pull`. Nothing is built server-side except what you commit. All commands below assume cwd = repo root.

**Three facts that explain most bugs here:**
1. **Split sidebar loader.** `index.html` and `store.html` have `<nav class="sidebar" id="sidebar">` filled by `script.js` (`fetch('sidebar.html')` → `getElementById('sidebar')`; script.js also *creates* `#menuToggle` and `#sidebarBackdrop` on `<body>` at runtime). `portfolio.html`, `projects.html`, `utilities.html` have `<div class="sidebar">` filled by inline jQuery `$('.sidebar').load('sidebar.html', ...)`. The three tool pages (`json_prettifier.html`, `qr_code_generator.html`, `morse_converter.html`) have **no sidebar, no styles.css, no script.js — by design**.
2. **nginx cache policy** (as of 2026-07-05, `.deploy/mkhome`): css/js 1h, images/fonts 1w, html no-cache. Stale styling after deploy is usually just this 1-hour window.
3. **The transform trap.** `.sidebar` has `transform: translateX(-100%)` on mobile. Per CSS spec, *any transformed element becomes the containing block for its `position: fixed` descendants* — a fixed-position child inside it is positioned relative to the sidebar, not the viewport, so it slides off-screen with it. This already cost a real incident (commit `8b05870`). Never put fixed-position UI inside `.sidebar`.

## When NOT to use this skill

| Situation | Use instead |
|---|---|
| You know the cause, want to know if the change is allowed | mkhome-change-control |
| Full incident history / post-mortems | mkhome-failure-archaeology |
| What invariants the site must keep | mkhome-architecture-contract |
| SEO tags/schema questions (not a live breakage) | mkhome-seo-reference |
| Editing products.json / rebuilding store | mkhome-store-pipeline |
| Setting up venv/Pillow/local server | mkhome-build-and-env |
| Deploy mechanics, nginx changes | mkhome-deploy-and-operate |
| Proving a fix works (evidence standards) | mkhome-validation-and-qa |
| Need DOM/geometry/screenshot/header PROOF of a behavior | mkhome-analysis-toolkit |

## Symptom → triage index

| # | Symptom | Most likely cause |
|---|---|---|
| 1 | Sidebar missing/empty | file:// CORS, wrong loader for that page, or missing `#sidebar` id |
| 2 | Hamburger missing/unreachable on mobile | transform trap, or script.js never ran |
| 3 | Production shows stale CSS/JS after deploy | 1h nginx cache vs browser cache vs deploy didn't run |
| 4 | Store page blank (no products) | products.json fetch failed or JSON syntax error |
| 5 | Store shows wrong language | Browser: stale localStorage `storeLang`. Crawler/curl: Spanish-by-design, or missing `es` object falling back to `en` |
| 6 | Social preview wrong/blurry | OG tags/dims, validator cache, low-res og-image.png |
| 7 | Mojibake / broken diacritics (Ã³, Å„, �) | non-UTF-8 write somewhere in the pipeline |
| 8 | Page renders unstyled | tool pages have no styles.css — probably NOT a bug |
| 9 | 404 on a deployed page | file not in repo root on VPS, or sitemap lists a page that doesn't exist |
| 10 | Hidden dir (.git, .ai, .deploy) publicly readable | nginx dotfile `deny all` block missing |

## Triage details

### 1. Sidebar missing or empty
First: `python3 -m http.server 8000` then open http://localhost:8000/ — **if the sidebar appears locally over HTTP but not when you opened the file directly, it's file:// CORS** (browsers block `fetch()`/`$.load()` of local files); not a real bug, always preview over HTTP.
If it fails over HTTP too, discriminate by page:
- index/store: `grep -n 'id="sidebar"' index.html store.html` → expect one `<nav class="sidebar" id="sidebar">` each. Missing id → `script.js` line 6 (`getElementById('sidebar')`) silently targets nothing. Also confirm `grep -n 'script.js' index.html store.html` hits.
- portfolio/projects/utilities: `grep -n "load('sidebar.html'" portfolio.html projects.html utilities.html` → expect the jQuery `.load` call in each; also check the jQuery `<script src=` tag loads (CDN outage → `$ is not defined` in console).
- If someone "unified" the loaders, that's the bug: a page with only `class="sidebar"` (no id) breaks under script.js, and vice versa. Check console for `Error loading sidebar:` (script.js) — jQuery `.load` fails silently.

### 2. Hamburger button missing or unreachable on mobile
First: `grep -n 'menuToggle' index.html store.html sidebar.html` → **expected: zero matches**. The button must NOT exist in any HTML; script.js creates it on `<body>` (script.js lines 25–37, comment explains why).
- If a match appears inside `sidebar.html` or inside the `<nav class="sidebar">` markup → that's the regression: the transform trap (fact 3 above). Move it back to dynamic creation on body.
- If zero matches but the button still doesn't show: check `script.js` loaded (Network tab / `curl -sI https://mkhome.byst.re/script.js`), and that the page is index or store — the jQuery pages get no hamburger from script.js at all; their mobile nav is separate. Also check CSS: `#menuToggle` is `display: none` above 768px by design (`styles.css` `@media (min-width: 769px)`).
- Button visible but taps do nothing: check console for a JS error thrown earlier in `DOMContentLoaded` (it would abort before listeners attach).

### 3. Production shows stale CSS/JS after deploy
Three suspects, in order:
1. **Did the deploy run?** `gh run list --limit 5` if the `gh` CLI exists; otherwise use the GitHub MCP `actions_list` tool or the repo's Actions tab (see mkhome-deploy-and-operate §2). Workflow "Deploy to VPS", triggers on push to main. Failed/absent run → redeploy; nothing below matters.
2. **nginx/edge cache?** `curl -sI https://mkhome.byst.re/styles.css` → expect `Cache-Control: public, max-age=3600` and `expires` ~1h ahead. Then `curl -s "https://mkhome.byst.re/styles.css?v=$(date +%s)" | grep -n "<the new rule>"` — a query string busts caches. **New content with `?v=` but old without → it's cache; wait ≤1h or accept it.**
3. **Browser cache?** Hard-reload (Ctrl+Shift+R) or compare `curl` output vs what DevTools shows. curl fresh + browser stale → browser.
If even `?v=`-busted curl shows old content, the file on the VPS is old: deploy ran but `git pull` failed (dirty tree on VPS) — see mkhome-deploy-and-operate.

### 4. Store page blank (no product cards)
First: `python3 -m json.tool store/products.json > /dev/null && echo OK` → **`OK` means JSON is valid**; any other output pinpoints the syntax error (trailing comma, unescaped quote — typical after a hand edit).
- JSON valid → check the fetch: store.html fetches `store/products.json` (relative path). Console shows `Failed to load products:` on failure. Over file:// this always fails (see #1). In production: `curl -sI https://mkhome.byst.re/store/products.json` → expect `200`.
- Products load but cards look wrong → a product object is missing a key (`en`/`es`/`pl` object, `title`, `highlights[]`...) — schema in mkhome-store-pipeline.
- Note: the `<noscript>` Spanish cards between `<!-- SEO:NOSCRIPT -->` markers are static build output — them being fine while the page is blank confirms a client-side JS/fetch failure.

### 5. Store shows wrong language
First, split the symptom — wrong language **in a browser** vs **in search results / curl output** are different mechanisms:
- **In a browser:** in DevTools console on store.html run `localStorage.getItem('storeLang')`. The switcher persists to that key; default is `'en'` only when the key is absent. **A stale `'pl'`/`'es'` value fully explains "always opens in Polish".** `localStorage.removeItem('storeLang')` and reload to confirm. Not a bug unless the value changes without a user click.
- **In search results / curl (crawler view):** crawlers see only the generated noscript/JSON-LD blocks, which are Spanish **by design** (`DEFAULT_LANG = "es"` in `scripts/build-store.py`) — but a product missing its `es` object **silently falls back to `en`**. Check: `curl -s https://mkhome.byst.re/store.html | sed -n '/SEO:NOSCRIPT/,/\/SEO:NOSCRIPT/p'` and read the language. English where Spanish is expected → missing `es` object → mkhome-store-pipeline (failure modes). Why es-for-crawlers/en-for-clients is intentional → mkhome-seo-reference §7.

### 6. Social preview wrong or blurry
First: `curl -s https://mkhome.byst.re/store.html | grep -o '<meta property="og:[^>]*>'` → expect `og:image` = `https://mkhome.byst.re/store/assets/og-image.png` (absolute URL) plus `og:image:width` 1200 / `og:image:height` 630.
- Tags correct but preview stale → validator-side cache; re-scrape with the validators listed in `doc/seo-validation.md` (Facebook Sharing Debugger, LinkedIn Post Inspector, etc.).
- Image blurry → regenerate: `scripts/generate-og-image.py` renders at 2x + LANCZOS (needs Pillow in a venv — mkhome-build-and-env); a manually saved 1x image is the usual culprit (this was part of the `0fc1ba1` fix).
- Remember images are nginx-cached 1 week — cache-bust the URL when checking a regenerated image.

### 7. Mojibake / broken diacritics
First: `grep -n 'Ã\|Å\|â€' store/products.json store.html sidebar.html *.html | head` → **any hit = UTF-8 bytes decoded as Latin-1 somewhere**. Also `file store/products.json` should say UTF-8/Unicode.
- This exact failure happened in `products.json` (commit `f2194d1` — see mkhome-failure-archaeology). Fix at the source file with explicit UTF-8; `scripts/build-store.py` reads/writes `encoding="utf-8"` throughout, so the build is not the corruptor — an editor or copy-paste step is.
- Charset audit: `grep -Li 'charset' *.html` → as of 2026-07-05 the three tool pages and sidebar.html have **no** `<meta charset>` at all (the five main pages declare UTF-8). If mojibake appears on a tool page, that missing declaration is the first suspect — the browser is guessing the encoding.

### 8. Page renders unstyled
First: `grep -L 'styles.css' *.html` → as of 2026-07-05 this prints exactly `json_prettifier.html`, `morse_converter.html`, `qr_code_generator.html` (plus `sidebar.html`, a fragment). **The tool pages intentionally carry their own inline styling — self-contained, no sidebar, no shared CSS. Not a bug; do not "fix" by adding styles.css.**
- If a main page (index, store, portfolio, projects, utilities) is unstyled: `curl -sI https://mkhome.byst.re/styles.css` (expect 200), then check for a CSS syntax error near recent edits, then #3 (stale cache).

### 9. 404 on a deployed page
First: `curl -sI https://mkhome.byst.re/<page>.html | head -1`, then `ls <page>.html` in the repo.
- In repo but 404 live → deploy problem: `gh run list --limit 5`, then #3 step 1.
- Not in repo but Google/sitemap links it → sitemap drift: `grep '<loc>' sitemap.xml` and compare to `ls *.html`. sitemap.xml is generated by `scripts/build-store.py` from root `*.html` (skips sidebar.html) — a page deleted without rerunning the build leaves a dangling sitemap entry. Rerun the build (mkhome-store-pipeline).
- nginx serves with `try_files $uri $uri/ =404` — no rewrites, no extensionless URLs: `/store` 404s, `/store.html` works. That's config, not breakage.

### 10. Hidden directory publicly accessible
First: `curl -sI https://mkhome.byst.re/.ai/deployment-security.md | head -1` → **expect `HTTP/... 403`** (nginx `location ~ /\. { deny all; }`). Also test `/.git/HEAD` and `/.deploy/mkhome`.
- Any `200` → the dotfile deny block is missing from the live nginx config. This is a real past incident (`.ai/deployment-security.md`, see mkhome-failure-archaeology). Treat as security-urgent; restore the block from `.deploy/mkhome` via mkhome-deploy-and-operate.

## Discriminating experiments

**Local vs production.** Serve the repo exactly as nginx would: `python3 -m http.server 8000`, open `http://localhost:8000/<page>`. Reproduces locally → code bug in the repo, debug here. Only in production → deploy, nginx, or cache (#3, #9, #10). Never test via `file://` — the sidebar/products fetches fail there by design of browser CORS, producing fake bugs.

**Deploy vs cache.** `curl -sI https://mkhome.byst.re/styles.css` and read `Cache-Control`/`expires`. Then fetch the same URL with `?v=$(date +%s)`: differs from the bare URL → cache; identical and old → the deployed file itself is old → `gh run list --limit 5` to see whether the "Deploy to VPS" action ran, succeeded, and *when* relative to your push.

**What a crawler sees.** Crawlers largely get the no-JS view: `curl -s https://mkhome.byst.re/store.html` and inspect (a) the `<noscript>` block between `<!-- SEO:NOSCRIPT -->` markers — Spanish product cards must be present and current, (b) the JSON-LD between `<!-- SEO:JSON-LD -->` markers — `@type: Product` entries. Both are injected by `scripts/build-store.py`; if they lag products.json, the build wasn't rerun after the last edit. The dynamically rendered product grid will be absent in curl output — that's expected.

## Traps that cost real time

Full stories in **mkhome-failure-archaeology**; one-liners here for recognition:
- **Transform containing-block trap** (`8b05870`, merged via PR #1): hamburger placed inside `.sidebar` → `translateX(-100%)` dragged the "fixed" button off-screen on mobile; fix = create it on `<body>` from script.js.
- **Cache staleness in prod** (`d3b862c`, `0ac08b4`): CSS/JS changes invisible after deploy until per-type nginx cache headers (css/js 1h) were set; still expect up to 1h of staleness today.
- **Diacritics mojibake** (`f2194d1`): Spanish/Polish text in products.json committed with mangled encoding; grep for `Ã`/`Å` before trusting any multilingual edit.
- **SEO validator rejections** (`0fc1ba1`): JSON-LD `Book` without offer → `Product` with price; missing og:image dims; blurry 1x OG image → 2x + LANCZOS render.
- **Hidden dirs served publicly** (`.ai/deployment-security.md`): dotfile directories were once reachable over HTTP until the nginx deny-all block was added.
- **file:// preview** (recurring self-inflicted): opening pages without an HTTP server "breaks" the sidebar and store — always `python3 -m http.server 8000` first.

## Provenance and maintenance

All claims verified against this repo on 2026-07-05. Re-verify before trusting:
- Split loader: `grep -n 'id="sidebar"\|load('"'"'sidebar.html'"'"'' *.html` and `head -40 script.js`
- Transform trap CSS: `grep -n 'translateX(-100%)' styles.css`; incident: `git show 8b05870 --stat`
- Cache policy + dotfile deny: `grep -n 'max-age\|deny all' .deploy/mkhome`
- Deploy flow: `cat .github/workflows/deploy.yml`
- Store keys/markers: `grep -n 'storeLang\|SEO:' store.html`; `python3 -m json.tool store/products.json > /dev/null && echo OK`
- Unstyled-by-design pages: `grep -L 'styles.css' *.html`
- Incident commits: `git log --oneline | grep -E '8b05870|d3b862c|0ac08b4|f2194d1|0fc1ba1'`
