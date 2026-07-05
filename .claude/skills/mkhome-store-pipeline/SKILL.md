---
name: mkhome-store-pipeline
description: >
  Runbook for product-level changes to the mkhome.byst.re digital store. Load when
  adding, editing, or removing a product; changing a price; touching store/products.json,
  store.html, store/assets/ images, scripts/build-store.py, or scripts/generate-og-image.py;
  regenerating the OG image; or investigating why store.html's JSON-LD / noscript content
  disagrees with products.json. Covers the products.json field catalog, the build-store.py
  generation contract (markers, idempotency, DEFAULT_LANG), and known failure modes.
---

# mkhome store pipeline

The store (store.html) sells ebooks via Amazon KDP links. `store/products.json` is the
**single source of truth**. It feeds TWO consumers:

1. **Client UI** — inline JS in store.html fetches `store/products.json` at runtime and
   renders product cards. Language switcher (`.lang-btn`, `data-lang`), persisted in
   localStorage key `storeLang`, default `'en'`.
2. **Generated crawler content** — `scripts/build-store.py` bakes JSON-LD structured data
   and `<noscript>` cards INTO store.html between marker comments, and regenerates
   sitemap.xml. This content is **committed to git** and goes stale the moment
   products.json changes without a rebuild.

**The iron rule: after ANY edit to store/products.json, run `python3 scripts/build-store.py`
and commit the resulting store.html + sitemap.xml changes together with products.json.**
(README says the same.)

## When NOT to use this skill

- Adding a whole new PAGE to the site → `mkhome-site-growth-campaign` (this skill owns
  product-level changes only).
- SEO strategy / why JSON-LD looks the way it does → `mkhome-seo-reference` (this skill
  owns the mechanical HOW).
- venv / environment setup details → `mkhome-build-and-env`.
- Deploying the change → `mkhome-deploy-and-operate`.
- Store page broken with unknown cause → `mkhome-debugging-playbook` first.

## products.json field catalog

Top level: a JSON **array** of product objects. Per product:

| Field | Type | Required | Used by | Example | Gotchas |
|---|---|---|---|---|---|
| `id` | string | yes | nothing programmatic (verified as of 2026-07-05) | `"it-for-seniors"` | Keep unique anyway; kebab-case; used as the human key in commits/discussion |
| `image` | string | yes | JSON-LD, noscript, client UI | `"store/assets/it-for-seniors.png"` | **Repo-relative path**, no leading slash. Build prefixes `https://mkhome.byst.re/` for JSON-LD; client and noscript use it as-is |
| `category` | string | yes | client UI only (badge: `ebook` → "eBook" badge, else "Guide") | `"ebook"` | Not in JSON-LD or noscript |
| `price` | string | no (defaults `"9.99"`) | JSON-LD only | `"10.49"` | **A string, not a number.** Must match the REAL Amazon price (external — cannot be verified from the repo). Omitting it silently emits 9.99 |
| `currency` | string | no (defaults `"USD"`) | JSON-LD only | `"USD"` | |
| `kdpUrl` | string | yes | JSON-LD (`offers.url`), noscript CTA, client CTA | full `https://www.amazon.com/...` URL | Full Amazon URL incl. tracking params; opens in new tab |
| `en` / `es` / `pl` | object | `en` and `es` effectively required; provide all three | see below | | Missing `es` → crawler content silently falls back to `en` (verified). Missing both `es` AND `en` → build crashes with `TypeError: 'NoneType' object is not subscriptable`. Missing `pl` → client falls back to `en` (`product[lang] || product.en`) |

Each language object:

| Field | Type | Used by | Gotchas |
|---|---|---|---|
| `title` | string | JSON-LD `name`, noscript `<h2>` + img alt, client | Use REAL diacritics (see mojibake lesson below) |
| `subtitle` | string | noscript, client | |
| `description` | string | JSON-LD `description`, noscript, client | |
| `highlights` | array of strings | noscript + client, each rendered as an `<li>` | Must be an array even for one item; build calls `p["highlights"]` — missing key crashes |
| `cta` | string | noscript + client (button text) | |

JSON-LD extras generated per product (not stored in JSON): `@type: Product`,
`brand: {Person, "Marcin Kaminski"}`, `availability: InStock`. Product (not Book) is
deliberate — Google Rich Results feedback, commit 0fc1ba1. Don't change the @type here;
that decision lives in `mkhome-seo-reference`.

## Runbook: ADD a product

Route through `mkhome-change-control` first (store changes are classified there). Then:

1. **Image**: place a PNG in `store/assets/`. Existing product images (as of 2026-07-05):
   `it-for-seniors.png` 1728x2464, `ai-product-management.png` 1024x1024 — portrait or
   square book-cover shapes; match that shape, RGBA PNG. Check current inventory with
   `ls -la store/assets/` before choosing a name.
2. **JSON entry**: append a new object to `store/products.json` with ALL fields above and
   ALL THREE language objects (`en`, `es`, `pl`). Write Spanish/Polish text with **real
   diacritics** (á, ñ, ó, ł, ż...), NOT ASCII-flattened. Lesson: initial store content was
   authored ASCII-flattened (560677f) and had to be fixed in f2194d1. The pipeline is fully
   UTF-8 (`ensure_ascii=False`, `encoding="utf-8"` everywhere) — flattening is never needed.
3. **Validate JSON**: `python3 -m json.tool store/products.json > /dev/null` (catches
   trailing commas etc. with the same error the build would give).
4. **Build**: `python3 scripts/build-store.py` (from repo root; no venv needed — stdlib only,
   verified: imports are json, re, html, pathlib, datetime).
5. **Inspect `git diff`**. Expected, and ONLY expected:
   - one new `<script type="application/ld+json">` block in store.html,
   - one new `<article class="product-card">` inside the `<noscript>` block,
   - sitemap.xml `<lastmod>` churn on every URL (lastmod = today on every run — normal,
     commit it).
   Anything else in the diff is a red flag — stop and investigate.
6. **Preview both render paths**: `python3 -m http.server 8000` from repo root, open
   `http://localhost:8000/store.html` with JS **on** (client cards, all three languages via
   the EN/ES/PL buttons) AND JS **off** (noscript Spanish cards must show).
7. Run the checks in `mkhome-validation-and-qa` (its `check_store_sync.py` proves
   products.json ↔ store.html sync) before merging per `mkhome-change-control`.

## Runbook: EDIT a product (price, text, highlights)

1. Edit the field in `store/products.json` only. **Never edit the generated blocks in
   store.html by hand** — the next build overwrites them.
2. For prices: the JSON-LD price should match the product's real price on Amazon KDP.
   That is external state you cannot verify from the repo — confirm with the owner or the
   live Amazon page.
3. `python3 -m json.tool store/products.json > /dev/null`
4. `python3 scripts/build-store.py` — **this step is the one that gets forgotten.**
   Cautionary example, live in the repo as of 2026-07-05: commit 0860584 ("Price update")
   raised it-for-seniors to 10.49 in products.json but did NOT re-run the build, so the
   committed JSON-LD in store.html still advertises 9.99 to crawlers. Known out-of-sync
   state; the next store change should fix it simply by running the script (route the fix
   through `mkhome-change-control` — do not fold it silently into unrelated work).
5. `git diff` → expect the corresponding JSON-LD/noscript change + sitemap lastmod churn.
6. Preview with JS on and off as above.

## Runbook: REMOVE a product

1. Delete the product's object from the `store/products.json` array (mind the commas —
   re-validate with `python3 -m json.tool`).
2. `python3 scripts/build-store.py` — removes its JSON-LD block and noscript card.
3. Optionally remove its PNG from `store/assets/` (check nothing else references it:
   `grep -rn "the-image-name.png" --include="*.html" --include="*.json" .`).
4. `git diff` → expect one JSON-LD block gone, one noscript card gone, sitemap churn.
5. Preview JS on/off; the client grid re-renders purely from JSON so no other edit needed.
6. Ask the owner whether the Amazon listing itself is retired; the repo only controls the
   storefront, not KDP.

## build-store.py anatomy (as of 2026-07-05)

Constants: `BASE_URL = "https://mkhome.byst.re"`, `DEFAULT_LANG = "es"`.

| Function | One line |
|---|---|
| `load_products()` | json.load of store/products.json (UTF-8) |
| `generate_jsonld(products)` | One schema.org Product `<script>` per product; text from `product.get("es", product.get("en"))`; image prefixed with BASE_URL; price/currency with defaults 9.99/USD; url = kdpUrl |
| `generate_noscript(products)` | Spanish (fallback en) HTML-escaped product cards, highlights as `<li>`, wrapped in one `<noscript><div class="products-grid">` |
| `inject_between_markers(content, start, end, payload)` | Regex-replaces everything between the marker comments (DOTALL, non-greedy), preserving the markers |
| `generate_sitemap()` | All root `*.html` except sidebar.html; priorities store 1.0 / index 0.8 / portfolio 0.6 / else 0.5; lastmod = today (hence churn every run) |
| `main()` | load → inject JSON-LD between `<!-- SEO:JSON-LD -->`…`<!-- /SEO:JSON-LD -->` → inject noscript between `<!-- SEO:NOSCRIPT -->`…`<!-- /SEO:NOSCRIPT -->` → write store.html → write sitemap.xml |

**Marker contract**: each marker pair must exist in store.html **exactly once**. Never
hand-edit content between markers; never delete or duplicate the markers. Verified behavior
on a scratch copy (2026-07-05): markers missing → **silent no-op**, exit 0, stale content
stays (no error, no warning); marker pair duplicated → payload injected into **every** pair
(duplicate JSON-LD blocks served to crawlers), also silent. Re-running on a healthy file is
byte-for-byte idempotent for store.html (verified).

**Language asymmetry (deliberate, don't "fix" without owner sign-off)**: crawler-facing
content (JSON-LD + noscript) is Spanish (`DEFAULT_LANG='es'`) — the books target the
Spanish-language market; the client UI defaults to `'en'`. So what a crawler sees differs
from what a first-time JS visitor sees. This is expected.

**Runs without venv**: stdlib only (json, re, html, pathlib, datetime) — verified by running
with system python3 and no venv present.

## generate-og-image.py

- Regenerates `store/assets/og-image.png` (1200x630, rendered at 2x + LANCZOS downscale):
  site-wide social-preview image with name/tagline on the brand gradient.
- **When to rerun**: only when the owner's name/tagline/site branding on the image changes,
  or brand colors change. NOT needed for product add/edit/remove — it is not per-product.
- **Needs Pillow**, so needs the venv (absent by default, gitignored):
  `python3 -m venv venv && source venv/bin/activate && pip install Pillow` — full env
  details in `mkhome-build-and-env`. Then `python3 scripts/generate-og-image.py`.
- Brand colors are **hard-coded duplicates** of styles.css: `(102,126,234)` = `#667eea`,
  `(118,75,162)` = `#764ba2`. Visual identity (this gradient, Lato, sidebar) is an owner
  non-negotiable — if styles.css colors ever change (owner approval required), this script
  must be updated in the same change or the OG image drifts off-brand.
- Fonts: picks first available system bold font (DejaVu/Liberation/FreeSans); output varies
  slightly across machines — a re-rendered PNG diffing against the committed one is normal.

## Failure modes

All "verified" rows reproduced on a scratch copy 2026-07-05; never test against the real repo files.

| Failure | Build behavior (verified) | Client behavior | Fix |
|---|---|---|---|
| Broken JSON (e.g. trailing comma) | Crash: `json.decoder.JSONDecodeError`, exit 1, store.html NOT touched | `r.json()` rejects → console "Failed to load products:", grid stays **blank** (from code; noscript hidden because JS is on) | Fix JSON; `python3 -m json.tool` pinpoints line/col |
| Missing `es` object | **Silent** fallback to `en` — crawler content becomes English, exit 0 | Client unaffected if `en` present | Add the `es` object; Spanish is the crawler-facing language |
| Missing `es` AND `en` | Crash: `TypeError: 'NoneType' object is not subscriptable`, exit 1 | Client card crashes render for that product | Always author all three languages |
| ASCII-flattened / mojibake text | Builds "fine" — garbage in, garbage out | Wrong characters visible in UI and search results | Author real diacritics; history: 560677f flattened, f2194d1 fixed |
| Markers deleted from store.html | **Silent no-op** — exit 0, stale generated content remains; the danger case | n/a | Restore exact marker comments from git history, rebuild |
| Marker pair duplicated | **Silent double-injection** — payload written into every pair; duplicate JSON-LD for crawlers | n/a | Remove the extra pair, rebuild |
| Edited products.json, forgot to run build | No error anywhere; store.html JSON-LD lies to crawlers | Client shows NEW data (reads JSON live) while crawlers see OLD — the split-brain is invisible in a browser | Run the build. Live example: 0860584 (10.49 vs 9.99, still unfixed as of 2026-07-05). `mkhome-validation-and-qa`'s `check_store_sync.py` detects this |
| Hand-edited between markers | Next build silently overwrites your edit | n/a | Only ever edit products.json or the templates inside build-store.py |

## Provenance and maintenance

- Facts verified 2026-07-05 against build-store.py, generate-og-image.py, store.html,
  products.json, store/assets/, and commits 560677f, f2194d1, 0fc1ba1, 0860584.
- Marker no-op/double-injection, idempotency, JSONDecodeError, es→en fallback, and
  NoneType crash reproduced by dry-run on a scratch copy (never the real repo).
- Re-verify after any edit to scripts/build-store.py (markers, DEFAULT_LANG, defaults) or
  to the store.html client JS; update the drift example once 0860584's 9.99 is rebuilt away.
- Amazon prices are external state — this file cannot vouch for them.
