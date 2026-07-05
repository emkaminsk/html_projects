---
name: mkhome-analysis-toolkit
description: "Ad-hoc measurement recipes for PROVING behavior on the mkhome.byst.re site instead of assuming it: DOM state after JavaScript runs (headless Chromium at mobile viewport), computed geometry / getBoundingClientRect probes, CSS containing-block experiments, HTTP header inspection (Cache-Control), crawler's-eye JSON-LD and noscript extraction, byte-level UTF-8/mojibake audits, build-script idempotency proofs, and screenshot diffing with PIL. Load when a question is 'is the button actually visible on mobile?', 'what does a crawler actually see?', 'is this really cached for 1h?', 'did the build really change nothing?' — anything where eyeballing or static grep can lie. Routine PASS/FAIL checks live in mkhome-validation-and-qa; this skill is for novel first-principles measurement."
---

# mkhome Analysis Toolkit

First-principles measurement recipes for this repo. Every command below was run
in this container on 2026-07-05 and the outputs shown are real. Motto: **prove
it, don't eyeball it.** The costliest bug in this repo's history (the mobile
hamburger trap, fixed in commit 8b05870) was invisible to desktop testing and to
static grep — only computed-position measurement at a mobile viewport could
catch it. These recipes are that measurement.

## Prerequisites (as of 2026-07-05, Claude web container)

- **Headless Chromium** is preinstalled under `/opt/pw-browsers`. The binary
  path FLOATS across container versions — always locate it first:
  ```bash
  CHROME=$(find /opt/pw-browsers -type f -name chrome -path "*chrome-linux*" | head -1)
  ```
  Today that resolves to `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`.
- **Local server** (required — `file://` breaks fetch of sidebar.html/products.json):
  ```bash
  cd /home/user/html_projects && python3 -m http.server 8000 &
  ```
- **PIL** is NOT preinstalled but `pip install pillow` worked in this container
  (installed 12.3.0). Only needed for Recipe 7.
- No npm/Playwright driver here. CDP over `--remote-debugging-port` needs a
  websocket client, which is not in the Python stdlib — so all recipes below use
  plain Chromium CLI flags (`--dump-dom`, `--screenshot`, `--virtual-time-budget`)
  plus grep/python on the artifacts. These are verified working; do not burn time
  trying to script CDP without a websocket library.
- Chromium flags that matter: `--headless=new --no-sandbox --disable-gpu`
  (all three required here), `--window-size=W,H` (sets viewport),
  `--virtual-time-budget=MS` (lets JS/fetch finish before dump/screenshot),
  `--hide-scrollbars` (for screenshots).

## Recipe 1 (FLAGSHIP): Assert DOM state after JS at mobile viewport

**Goal.** Prove that `#menuToggle` (the hamburger button) exists and is visible
in-viewport at 375px width. Static grep CANNOT do this: `script.js` creates
`#menuToggle` and the backdrop on `document.body` at runtime, so
`grep -c menuToggle index.html` returns **0** (verified). DOM-level checks are
mandatory for any nav assertion.

**Step A — existence (read-only, runs against the real repo):**
```bash
$CHROME --headless=new --no-sandbox --disable-gpu --window-size=375,812 \
  --virtual-time-budget=8000 --dump-dom http://localhost:8000/index.html \
  > /tmp/dom-mobile.html 2>/dev/null
grep -c 'id="menuToggle"' /tmp/dom-mobile.html   # PASS: 1
```
Real output: `1`, and the element carries
`aria-label="Toggle navigation" aria-expanded="false"`.

**Step B — geometry (the write-results-into-DOM-then-dump trick).** You cannot
mutate the repo, so copy it to scratch, append a probe script before `</body>`
of index.html, serve the copy, dump, grep the probe div:
```bash
S=/tmp/scratch; cp -r /home/user/html_projects $S/repo-probe
# append before </body> of $S/repo-probe/index.html:
#   <script>window.addEventListener('load',()=>setTimeout(()=>{
#     const el=document.getElementById('menuToggle');
#     const d=document.createElement('div'); d.id='__probe';
#     const r=el.getBoundingClientRect(), cs=getComputedStyle(el);
#     d.textContent=JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height,
#       display:cs.display,position:cs.position,
#       inViewport:r.x>=0&&r.y>=0&&r.right<=innerWidth&&r.bottom<=innerHeight&&r.width>0});
#     document.body.appendChild(d);},300));</script>
(cd $S/repo-probe && python3 -m http.server 8001 &)
$CHROME --headless=new --no-sandbox --disable-gpu --window-size=375,812 \
  --virtual-time-budget=8000 --dump-dom http://localhost:8001/index.html 2>/dev/null \
  | grep -oP '(?<=id="__probe">)[^<]*'
```
**How to read it.** PASS criterion: `position:"fixed"`, `display:"block"`,
`x>=0`, `inViewport:true`. Real output today (healthy layout):
```json
{"x":16,"y":16,"w":24,"h":16,"display":"block","position":"fixed","inViewport":true}
```
(16px = the CSS `top:1rem; left:1rem`. w/h are small because the Font Awesome
icon loads from a CDN that may be proxy-blocked in this container — geometry is
still trustworthy. Grep the `__probe` div specifically, not the word "PROBE":
`--dump-dom` also emits your script's own source text.)

**Why this catches the historic bug.** Pre-8b05870, `#menuToggle` sat inside
`.sidebar`, which has `transform: translateX(-100%)` at ≤768px. Per the CSS
spec, a transformed ancestor becomes the containing block for `position:fixed`
descendants — so "fixed" resolved against the off-screen sidebar. I reproduced
that layout in a second scratch copy (reparented the button into `.sidebar`)
and the same probe printed:
```json
{"x":-234,"y":16,"inViewport":false}
```
x = 16 − 250 (sidebar width): the button was 234px off the left edge. Desktop
viewports never show this; only this measurement does.

## Recipe 2: Prove the containing-block rule by experiment

**Goal.** Settle "does transform really hijack position:fixed?" (or any layout
argument) with a minimal controlled experiment, not spec-lawyering.

**Command.** Write a self-contained HTML file in scratch — self-contained pages
work over `file://`, no server needed — with a fixed child inside a transformed
parent and an identical control, plus an inline script writing both
`getBoundingClientRect`s into a `<pre id="result">`:
```bash
$CHROME --headless=new --no-sandbox --disable-gpu --window-size=375,812 \
  --virtual-time-budget=2000 --dump-dom file://$S/cb-repro.html 2>/dev/null \
  | grep -o 'RESULT \[.*\]'
```
Both children have `position:fixed; top:10px; left:10px`; parent B has
`transform: translateX(-100%)`. Real output:
```
RESULT [{"id":"a","x":10,"y":10},{"id":"b","x":-162,"y":150}]
```
**How to read it.** Control `a` lands at the viewport's (10,10). Child `b`
lands relative to its transformed parent — off-screen. Identical CSS, one
variable changed: experiment settled.

## Recipe 3: HTTP header measurement (cache policy)

**Goal.** Read the actual `Cache-Control` a client receives — the incident
class here was stale CSS/JS confusion (commits d3b862c/0ac08b4), settled by
per-type nginx caching.

**Commands.**
```bash
curl -sI http://localhost:8000/styles.css       # local dev server
curl -sI https://mkhome.byst.re/styles.css      # production
```
**How to read it.** `Cache-Control: public, max-age=3600` = cached 1h; `no-cache,
no-store, must-revalidate` = always fresh; python's `http.server` sends NO
Cache-Control at all (verified: only `Server: SimpleHTTP/... Last-Modified: ...`)
— so local testing can never reproduce a caching bug; you must reason from the
nginx config or measure production.

**Caveat (as of 2026-07-05, Claude web container):** production curl returned
`HTTP/1.1 403 Forbidden` — the container's egress proxy blocks the live site.
The following is therefore **repo-derived** from `.deploy/mkhome`, not measured
live: css/js → `expires 1h; Cache-Control "public, max-age=3600"`; images/fonts
→ 1w (`max-age=604800`); html → `expires -1; "no-cache, no-store,
must-revalidate"`. If your container CAN reach production, prefer measuring.
So a CSS change is visible at worst 1h after deploy; if it's older than that
and still stale, the problem is not this cache layer.

## Recipe 4: Crawler's-eye view (no-JS HTML + JSON-LD validation)

**Goal.** See what a non-JS crawler sees, and validate the generated JSON-LD.
The store page renders products with JS; crawlers rely on the committed
`<noscript>` cards and JSON-LD blocks that `scripts/build-store.py` injects.

**Commands.**
```bash
curl -s http://localhost:8000/store.html > /tmp/store-nojs.html
python3 - <<'EOF'
import re, json
html = open("/tmp/store-nojs.html", encoding="utf-8").read()
for i, b in enumerate(re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)):
    d = json.loads(b)   # raises on invalid JSON -> that IS the finding
    o = d.get("offers", {})
    print(i, d.get("@type"), d.get("name"), "| price:", o.get("price"), o.get("priceCurrency"))
print(len(re.findall(r'<noscript>(.*?)</noscript>', html, re.S)), "noscript block(s)")
EOF
```
**How to read it.** Each block must parse (use `json.loads`, or pipe an
extracted block through `python3 -m json.tool`); then cross-check prices and
names against `store/products.json`.

**Worked example — a real finding, today.** Output:
```
0 Product Tecnología para Seniors: Una Guía Práctica | price: 9.99 USD
1 Product Gestión de Productos con IA | price: 9.99 USD
1 noscript block(s)
```
But `store/products.json` says `it-for-seniors` costs **10.49**. The committed
JSON-LD is stale (price changed after the last build-store.py run). Spanish
names are NOT a bug — `build-store.py` sets `DEFAULT_LANG = "es"` deliberately.
This drift is exactly why this check exists; fix path is in mkhome-store-pipeline.

## Recipe 5: Byte-level encoding audit

**Goal.** Find invalid UTF-8 or mojibake (double-encoded diacritics) — the
f2194d1 incident class, where initial content shipped ASCII-flattened.

**Command** (run from repo root):
```bash
python3 - <<'EOF'
import pathlib, re
sig = re.compile(r'Ã[©¡³­ºÂ±"]|Å[›ºÄ‚„]|â€|Â[»«°]')
for p in sorted(pathlib.Path('.').rglob('*')):
    if p.suffix not in {'.html','.css','.js','.json','.xml','.txt','.md','.py'} \
       or '.git' in p.parts or not p.is_file(): continue
    raw = p.read_bytes()
    try: text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        print(f"INVALID UTF-8: {p} byte {e.start}: {raw[e.start:e.start+8]!r}"); continue
    for i, line in enumerate(text.splitlines(), 1):
        if sig.search(line): print(f"MOJIBAKE? {p}:{i}: {line[:80]}")
EOF
```
**How to read it.** `INVALID UTF-8` is always a real problem. `MOJIBAKE?` needs
a human eye: real output today flagged only two lines in
`mkhome-debugging-playbook/SKILL.md` — lines that *document* mojibake
signatures. Known false-positive class; site content itself was clean, with
proper single-encoded diacritics (`Tecnología` in products.json is genuine UTF-8).

## Recipe 6: Build idempotency proof

**Goal.** Prove `scripts/build-store.py` is deterministic (run twice → identical
output) and see exactly what a rebuild would change vs. the committed files —
WITHOUT touching the repo. The script derives all paths from its own location,
so a scratch copy is fully self-contained.

**Commands.**
```bash
S=/tmp/scratch; cp -r /home/user/html_projects $S/build1 && rm -rf $S/build1/.git
python3 $S/build1/scripts/build-store.py
cp $S/build1/store.html $S/run1-store.html; cp $S/build1/sitemap.xml $S/run1-sitemap.xml
python3 $S/build1/scripts/build-store.py
diff $S/run1-store.html $S/build1/store.html && echo IDEMPOTENT
diff /home/user/html_projects/store.html $S/build1/store.html   # drift vs committed
diff /home/user/html_projects/sitemap.xml $S/build1/sitemap.xml
```
**Real results, 2026-07-05.** run1 vs run2: **byte-identical** for both files
(idempotency holds). Scratch build vs committed: exactly two diff classes —
```
<     "price": "9.99"        # committed store.html (stale)
>     "price": "10.49"       # what a rebuild produces (matches products.json)
```
and every sitemap `<lastmod>2026-03-07</lastmod>` → `2026-07-05` (the script
stamps today's date — an *expected* rebuild diff, not drift; don't flag it).

## Recipe 7: Screenshot-diff layout regression (maturity: proven once, coarse)

**Goal.** Detect visual layout change between two versions at a fixed viewport.
Honest label: this worked end-to-end today, but it is a coarse tool — it tells
you *that* and *where* pixels changed, not *what*. Prefer Recipe 1's geometry
probe for anything you can express as coordinates.

**Commands** (needs `pip install pillow` first):
```bash
$CHROME --headless=new --no-sandbox --disable-gpu --window-size=375,812 \
  --hide-scrollbars --virtual-time-budget=8000 \
  --screenshot=$S/after.png http://localhost:8000/index.html 2>/dev/null
# ...same for the other version on another port -> before.png, then:
python3 - <<'EOF'
from PIL import Image, ImageChops
a = Image.open("before.png").convert("RGB"); b = Image.open("after.png").convert("RGB")
d = ImageChops.difference(a, b)
print("bbox:", d.getbbox())     # None = pixel-identical
EOF
```
**Worked example.** Healthy layout vs the reproduced pre-8b05870 bug at
375x812: `diff bbox: (10, 14, 46, 42)`, 860 changed pixels (0.28%) — precisely
the hamburger-button region going missing. A crop of the button area
(`img.crop((8,8,68,58)).getcolors(...)`) showed 152 distinct colors in the
healthy shot vs 31 in the buggy one (flat background). Caveats: renders can
differ by a few anti-aliased pixels across runs; treat tiny diffs as noise, and
remember external fonts/CDN assets may not load in this container, so compare
container-shot against container-shot only, never against a real-browser shot.

## When NOT to use this skill

- **Routine regression gating** — `check_invariants.py`, `check_store_sync.py`,
  `smoke_serve.py` in `.claude/skills/mkhome-validation-and-qa/scripts/` already
  encode the known invariants as PASS/FAIL. Run those first; come here when they
  can't answer the question.
- **Symptom triage** ("the sidebar is blank") — start with
  mkhome-debugging-playbook, which routes to these methods when needed.
- **Static questions** grep can answer (does file X contain string Y, is a link
  present in committed HTML). Don't spin up Chromium for those.
- **Deciding whether a change is allowed** — that's mkhome-change-control.
- **Fixing what you measured** — store drift fixes go through
  mkhome-store-pipeline; deploy/cache changes through mkhome-deploy-and-operate.

## Provenance and maintenance

- Written 2026-07-05 by a Claude session; every command was executed in that
  session's Claude web container and all quoted outputs are pasted from real
  runs (trimmed only for length).
- Environment-dependent facts, all stamped 2026-07-05: Chromium at
  `/opt/pw-browsers/chromium-1194/...` (path floats — always `find` it);
  python3 3.11.15; PIL absent until `pip install pillow` (got 12.3.0);
  production `mkhome.byst.re` unreachable through the egress proxy (403).
  Re-verify each of these at the start of any session that relies on them.
- The Recipe 4/6 price-drift finding (JSON-LD 9.99 vs products.json 10.49 for
  `it-for-seniors`) was true on 2026-07-05. Once someone reruns build-store.py
  and commits, that worked example becomes historical — update it to "expect
  no diff" or to whatever the then-current drift is, rather than deleting it.
- If a recipe stops working (Chromium flags change, `--headless=new` retired,
  proxy rules shift), fix the recipe by re-running it to green, then update the
  pasted output and the date stamp. Never leave an unverified command in this
  file — per mkhome-docs-and-writing, this skill's contract is ground truth only.
