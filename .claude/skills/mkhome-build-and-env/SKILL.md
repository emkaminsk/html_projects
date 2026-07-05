---
name: mkhome-build-and-env
description: >-
  Environment setup and local-preview runbook for the mkhome.byst.re static
  site (this repo). Load at SESSION START when the environment is fresh or the
  repo was just cloned; BEFORE running scripts/build-store.py or
  scripts/generate-og-image.py for the first time; BEFORE starting a local
  preview; or when a command fails with environment-looking errors:
  "No module named 'PIL'", "venv/bin/activate: No such file or directory",
  "Address already in use", "python: command not found", CORS errors on
  file:// URLs, blank sidebar, empty store page, or unstyled pages. Covers
  venv creation, the http.server preview, curl and headless-Chromium
  verification, and what tooling does NOT exist here.
---

# mkhome build & environment

Static site: plain HTML/CSS/JS. **There is NO build step for the site itself.**
The only tooling is two Python scripts in `scripts/`. Everything below was
executed and verified on 2026-07-05 (Python 3.11.15 in a Claude Code web
container; versions float).

## When NOT to use this skill

- Site is broken and cause unknown → `mkhome-debugging-playbook`.
- What/when to run the store scripts, products.json workflow → `mkhome-store-pipeline`.
- Deploying, VPS, nginx, GitHub Action, production caching → `mkhome-deploy-and-operate`.
- Whether a change is allowed at all → `mkhome-change-control` / `mkhome-architecture-contract`.
- Deep measurement (Lighthouse-style analysis, screenshots at scale) → `mkhome-analysis-toolkit`.

## 1. Zero-to-working checklist

Run from repo root (`/home/user/html_projects` in Claude containers; adjust if cloned elsewhere).

1. **Python present?** `python3 --version` → expect 3.x (3.11.15 here as of 2026-07-05). No other runtime is required to serve or edit the site.
2. **venv — only needed for `generate-og-image.py`.** Verified: `build-store.py` imports only stdlib (`json`, `re`, `html`, `pathlib`, `datetime`) and runs fine with system python3, no venv. `generate-og-image.py` imports `PIL` and fails without Pillow (`ModuleNotFoundError: No module named 'PIL'`). Fresh clone has NO venv (`venv/` is gitignored) — create it:

   ```bash
   python3 -m venv venv && source venv/bin/activate && pip install Pillow
   ```

3. **Do NOT run the scripts just to test the environment.** `build-store.py` rewrites `store.html` and `sitemap.xml` in place (fresh `<lastmod>` dates at minimum), dirtying the working tree. If you must smoke-test it, copy the repo to scratch space and run the copy. Committed files ARE the production artifacts here.
4. **Start local preview — MUST be an HTTP server, never file://:**

   ```bash
   python3 -m http.server 8000
   # then open http://localhost:8000/
   ```

5. **What "working" looks like** (needs internet — CSS/fonts/icons come from CDN):
   - `index.html`: sidebar nav visible on the left with links Home / Digital Store / Curriculum Vitae / Portfolio / Utilities; styled with the purple gradient; no console errors.
   - `store.html`: product cards render (2 products as of 2026-07-05, from `store/products.json`); language switcher works.
   - `portfolio.html` / `projects.html` / `utilities.html`: same sidebar (injected via jQuery `.load()`).

## 2. Traps

| Symptom | Why | Fix |
|---|---|---|
| Opened via `file://` — sidebar empty, store blank, console shows CORS/fetch errors | `script.js` does `fetch('sidebar.html')`, store.html fetches `store/products.json`, portfolio/projects/utilities use jQuery `.load('sidebar.html')` — all XHR, blocked on `file://` | Always serve over HTTP: `python3 -m http.server 8000`. (Exception: `json_prettifier.html`, `qr_code_generator.html`, `morse_converter.html` are standalone and work from `file://`.) |
| `source venv/bin/activate` → "No such file or directory" | README assumes an existing venv, but `venv/` is gitignored — a fresh clone has none | `python3 -m venv venv && source venv/bin/activate && pip install Pillow` first |
| `ModuleNotFoundError: No module named 'PIL'` | Running `generate-og-image.py` without the venv/Pillow | Activate the venv (above). `build-store.py` does NOT need this — stdlib only (verified 2026-07-05) |
| Pages load but look unstyled / no icons / default font | Offline or CDN unreachable: Bootstrap 5.3.0, Font Awesome 6.0.0, Google Fonts Lato, jQuery 3.6.0 (3 pages), QRCode.js (qr page) all load from CDN at runtime | Need internet for a faithful preview. DOM/content checks still work offline |
| Worried about running `build-store.py` from wrong cwd | Not a real trap: script resolves paths via `Path(__file__).resolve().parent.parent` — cwd-independent (verified: ran from a different cwd, it edited files next to the script) | Any cwd works. The real trap is that it MUTATES `store.html`/`sitemap.xml` wherever the script lives — see step 3 above |
| `http.server` → `OSError: [Errno 98] Address already in use` | Another server (possibly a leaked background one) holds the port | Use another port (`python3 -m http.server 8001`) or kill the holder: `kill $(lsof -ti:8000)` |
| `python: command not found` | Some hosts only ship `python3` (this container has both, pointing to the same 3.11) | Always type `python3` in commands and docs |

## 3. Copy-pasteable verification snippet

Serves the repo, checks HTTP 200 + content markers, then cleans up. Verified working 2026-07-05 (all 200s, all markers found).

```bash
cd /home/user/html_projects   # repo root
python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1 &
SRV=$!
sleep 1
for p in index.html sidebar.html store.html store/products.json styles.css script.js; do
  printf '%-25s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:8000/$p")"
done                                                             # expect 200 for every line
curl -s http://localhost:8000/script.js | grep -c "fetch('sidebar.html')"   # expect 1 (sidebar loader intact)
curl -s http://localhost:8000/index.html | grep -c goatcounter              # expect 1 (analytics snippet intact)
curl -s http://localhost:8000/store/products.json \
  | python3 -c "import json,sys; print('products:', len(json.load(sys.stdin)))"  # expect >= 1
kill $SRV
```

Note: curl checks prove files are served and markers exist — they do NOT prove JS executed (sidebar injection, store cards). For that, use section 4.

## 4. Real DOM checks (headless Chromium)

Claude Code web containers ship Playwright's Chromium (as of 2026-07-05) at
`/opt/pw-browsers`. Check availability first: `ls /opt/pw-browsers` — if
absent, fall back to the curl snippet above and reason about the JS manually.

Critical container gotcha (verified): `HTTPS_PROXY` is set, and Chromium
routes even `localhost` through the proxy, so fetches silently fail and the
sidebar stays empty. Pass `--no-proxy-server` for localhost checks.

```bash
cd /home/user/html_projects
python3 -m http.server 8123 --bind 127.0.0.1 >/dev/null 2>&1 &
SRV=$!
sleep 1
CHROME=$(ls -d /opt/pw-browsers/chromium-*/chrome-linux/chrome 2>/dev/null | head -1)
"$CHROME" --headless=new --no-sandbox --disable-gpu --no-proxy-server \
  --dump-dom --virtual-time-budget=8000 http://localhost:8123/index.html 2>/dev/null \
  | grep -c 'Digital Store'   # expect >= 1: sidebar WAS fetched and injected
kill $SRV
```

With `--no-proxy-server` the CDN assets won't load — fine for DOM-injection
checks (same-origin only), useless for visual/styling verification. For
screenshots, rendering audits, or performance measurement, load
`mkhome-analysis-toolkit` instead.

## 5. What does NOT exist here — stop looking (as of 2026-07-05)

- No `package.json`, no `node_modules`, no npm/yarn scripts (the container may have node installed; the repo never uses it).
- No Makefile, no task runner.
- No test suite, no linters, no formatters, no CI checks beyond the deploy Action.
- No Docker / docker-compose.
- No bundler, templating engine, or site generator — HTML files are hand-edited and committed as-is (see `mkhome-architecture-contract` before trying to add any of these).
- No `requirements.txt` — the only pip dependency is Pillow, documented in README prose.

## Provenance and maintenance

- All commands in this file were executed on 2026-07-05 in a Claude Code web container (Python 3.11.15, Chromium via /opt/pw-browsers); outputs shown are real.
- build-store.py stdlib-only claim: verified by running it in a fresh venv with no packages — exit 0.
- If Python major version, CDN dependency list, product count, or the Chromium path changes, re-run sections 3-4 and update the dates.
- If a build step, package.json, or test suite is ever added, section 5 is wrong — rewrite it and notify mkhome-architecture-contract.
