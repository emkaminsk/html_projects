---
name: mkhome-seo-reference
description: >
  SEO domain-knowledge pack for the mkhome.byst.re static site. Load when touching
  <head> metadata (title, meta description, canonical), Open Graph / Twitter Card /
  social-preview tags, JSON-LD structured data, hreflang alternates, sitemap.xml or
  robots.txt, the <noscript> crawler fallback in store.html, or when diagnosing why a
  page looks wrong in Google results, Facebook/LinkedIn/Twitter link previews, or
  Google Rich Results. Also load before adding a new page or product so the SEO
  contract is not broken.
---

# mkhome SEO Reference

Domain knowledge for search-engine and social-preview visibility of this site, **as applied
here** — not a general SEO textbook. Site: static HTML/CSS/JS personal website of Marcin
Kaminski, live at `https://mkhome.byst.re`. SEO priority page: `store.html` (multilingual
ebook store; primary market: Spanish-speaking seniors).

**Division of labor with sibling skills:** this skill explains the SEO *why*. The mechanical
*how* of running `scripts/build-store.py` and editing `store/products.json` lives in
`mkhome-store-pipeline`. Incident narratives live in `mkhome-failure-archaeology`.

## When NOT to use this skill

- Editing product data or running the build script step-by-step → `mkhome-store-pipeline`.
- Pure styling/JS/layout changes that do not touch `<head>`, `<noscript>`, JSON-LD, sitemap, or robots.
- Deployment, hosting, or nginx questions → `mkhome-deploy-and-operate`.
- Writing prose/copy → `mkhome-docs-and-writing` (come back here only to check keyword/meta implications).

## Glossary (terms used below, defined once)

| Term | Meaning |
|---|---|
| **canonical** | `<link rel="canonical" href="...">` — declares the single authoritative URL for a page so search engines consolidate ranking signals there instead of splitting them across URL variants (`/` vs `/index.html`, http vs https). |
| **OG (Open Graph)** | `<meta property="og:*">` tags read by Facebook, LinkedIn, Slack, WhatsApp etc. to build the link-preview card (title, description, image). |
| **Twitter Card** | `<meta name="twitter:card">` — same idea for X/Twitter; `summary_large_image` requests the big-image card layout. |
| **JSON-LD** | JSON-Linked-Data: a `<script type="application/ld+json">` block containing Schema.org structured data. Google reads it to generate **rich results** (search listings enhanced with price, stars, images). |
| **hreflang** | `<link rel="alternate" hreflang="xx" href="...">` — tells search engines which URL serves which language; `x-default` is the fallback for unmatched languages. |
| **noscript fallback** | Content inside `<noscript>` that only renders when JavaScript is off. Used here so crawlers that don't execute JS still see product content in the raw HTML source. |
| **crawl budget** | The limited number of pages/frequency a search engine will fetch from a site. Tiny site → not a real constraint here, but sitemap `lastmod` churn (below) still wastes recrawls. |

## 1. Head-metadata contract (every main page)

Applies to the five main pages: `index.html`, `store.html`, `portfolio.html`,
`projects.html`, `utilities.html`. (Known gap as of 2026-07-05: the tool pages
`json_prettifier.html`, `qr_code_generator.html`, `morse_converter.html` are in the sitemap
but have **no** SEO metadata — `morse_converter.html` even lacks `lang` on `<html>`. If asked
to improve SEO, these are the low-hanging fruit; follow this contract.)

| Tag | Why it exists here | Real example (from the live files) |
|---|---|---|
| `<html lang="...">` | Crawlers don't run JS. `store.html` switches language client-side (`document.documentElement.lang = lang` at runtime), but Google only sees the **source** value, so the static `lang="en"` on line 2 is what counts. | `<html lang="en">` (store.html:2) |
| `<title>` | Search-result headline. Store title is Spanish-first (target market). | `<title>Tienda Digital \| Marcin Kaminski — Ebooks de Tecnología e Informática</title>` |
| `meta description` | The search-result snippet Google usually shows. Page-specific, ~150–160 chars. | `<meta name="description" content="Guías prácticas y ebooks sobre tecnología, informática e inteligencia artificial. ...">` |
| `meta author` | Attribution; low SEO weight but part of the contract on all main pages. | `<meta name="author" content="Marcin Kaminski">` |
| `link canonical` | `mkhome.byst.re` is a subdomain on shared free hosting — the owner does not control host-level redirects, and the same page is reachable at multiple URLs (`/` vs `/index.html`, protocol variants). Canonical picks the winner so signals aren't split. Always the full `https://mkhome.byst.re/<page>.html` form. | `<link rel="canonical" href="https://mkhome.byst.re/store.html">` |
| OG set: `og:title`, `og:description`, `og:url`, `og:type`, `og:image` | Link-preview card on social platforms. All pages share one image: `https://mkhome.byst.re/store/assets/og-image.png` (1200x630). | see index.html:10–14 |
| `og:image:width` + `og:image:height` | **Required by hard-won experience.** Without explicit dimensions, LinkedIn rendered a blurry/wrong-size preview (fixed in commit `0fc1ba1`, which also regenerated the image at 2x resolution with LANCZOS downscaling for sharp text). Never add an `og:image` without these two tags. | `<meta property="og:image:width" content="1200">` `<meta property="og:image:height" content="630">` |
| `article:published_time` | LinkedIn Post Inspector flagged a missing date; added in `0fc1ba1`. Present on store.html only. | `<meta property="article:published_time" content="2026-03-07">` |
| `twitter:card` | Requests large-image card on X/Twitter. | `<meta name="twitter:card" content="summary_large_image">` |
| `meta keywords` | store.html only; Spanish target keywords. Google ignores it; kept for minor engines and as the keyword strategy of record. | `<meta name="keywords" content="informática para mayores, tecnología para personas mayores, ...">` |

**Rule for a new page:** copy the whole `<head>` metadata block from `index.html`, change
title/description/canonical/og:title/og:description/og:url to page-specific values, keep the
shared og:image trio and twitter:card as-is, then re-run `python3 scripts/build-store.py` so
the sitemap picks up the new file (any root `*.html` except `sidebar.html` is auto-included).

## 2. JSON-LD on store.html: `@type: Product`, never `Book`

The original plan (doc/seo-implementation-plan.md §2.2) drafted `@type: Book`. Commit
`0fc1ba1` ("fix: address SEO validation feedback from Facebook, LinkedIn, Google") switched
to `@type: Product` **because Google Rich Results requires an `offers` block with
price/priceCurrency to render product rich results, and validated Book markup wasn't
producing them**. Do not "correct" it back to Book — Product-with-offers is the deliberate,
validator-tested choice.

The blocks live in `store.html` between `<!-- SEO:JSON-LD -->` and `<!-- /SEO:JSON-LD -->`
(lines ~463–504) and are **generated** by `scripts/build-store.py` from
`store/products.json` using the Spanish (`DEFAULT_LANG = "es"`) fields. Actual generated
shape (first product, abridged URL):

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Tecnología para Seniors: Una Guía Práctica",
  "description": "Una guía completa de 16 capítulos ...",
  "image": "https://mkhome.byst.re/store/assets/it-for-seniors.png",
  "brand": { "@type": "Person", "name": "Marcin Kaminski" },
  "offers": {
    "@type": "Offer",
    "price": "9.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "url": "https://www.amazon.com/Tecnolog%C3%ADa-para-Seniors-...ebook/dp/B0GPQFWPB3/..."
  }
}
</script>
```

**Iron rule: never hand-edit anything between the `SEO:JSON-LD` or `SEO:NOSCRIPT` markers.**
Edit `store/products.json`, then regenerate (`python3 scripts/build-store.py`). Hand edits
are silently overwritten by the next build, and skipping the build causes drift.

**Live drift example (as of 2026-07-05):** commit `0860584` ("Price update") changed the
it-for-seniors price to `"10.49"` in products.json, but build-store.py was not re-run, so
store.html's generated JSON-LD still advertises `"price": "9.99"`. Google may flag or ignore
structured data whose price disagrees with reality. If you touch the store, run the build
and commit the regenerated store.html + sitemap.xml alongside products.json.

## 3. hreflang: single-URL for all languages (known compromise)

store.html declares (lines 11–14):

```html
<link rel="alternate" hreflang="en" href="https://mkhome.byst.re/store.html">
<link rel="alternate" hreflang="es" href="https://mkhome.byst.re/store.html">
<link rel="alternate" hreflang="pl" href="https://mkhome.byst.re/store.html">
<link rel="alternate" hreflang="x-default" href="https://mkhome.byst.re/store.html">
```

All four point at the **same URL**. That is unusual — hreflang normally maps each language
to a *distinct* URL so Google can serve the right variant per user. Here language switching
is client-side JS (EN/ES/PL buttons, choice persisted in `localStorage.storeLang`), so there
is only one URL to point at.

What this setup **does** achieve: signals that the page is relevant to en/es/pl audiences,
and is harmless (self-referencing hreflang is valid). What it **doesn't**: Google cannot
index or rank three language variants separately — crawlers see only the source HTML, which
is one fixed-language document. This is the documented "Option B" from
doc/seo-implementation-plan.md §2.4 (Option A — per-language URLs like `store-es.html` —
was deferred). **Status: as-designed but debatable.** Don't "fix" it unilaterally; if asked
to improve multilingual SEO, the real upgrade is per-language URLs with cross-pointing
hreflang, which is a change-control decision (see `mkhome-change-control`).

## 4. noscript strategy: crawlers must see Spanish product content without JS

The visible product grid (`<div class="products-grid" id="products-grid">`) is empty in the
HTML source and populated by JS from `store/products.json`. Since crawler JS execution is
unreliable, `build-store.py` injects full static Spanish product cards inside `<noscript>`
between `<!-- SEO:NOSCRIPT -->` markers (store.html lines ~418–461): real `<article>` cards
with `<h2>` product titles, descriptions, highlight lists, and Amazon links.

Verify the crawler-visible content without a browser:

```bash
# Local source check — should print the Spanish product <h2> titles:
grep -A2 'SEO:NOSCRIPT' store.html | head; grep '<h2>' store.html

# Live check — what a non-JS crawler actually receives:
curl -s https://mkhome.byst.re/store.html | grep -o '<h2>[^<]*</h2>'
# Expect: <h2>Tecnología para Seniors: Una Guía Práctica</h2> etc.
```

Authoritative check: Google Search Console → URL Inspection ("view crawled page") confirms
the noscript content is in Google's rendered/indexed copy.

## 5. sitemap.xml and robots.txt

- `robots.txt` (hand-maintained, root) is intentionally minimal — allow everything, point at the sitemap:
  ```
  User-agent: *
  Allow: /

  Sitemap: https://mkhome.byst.re/sitemap.xml
  ```
- `sitemap.xml` is **generated** by `scripts/build-store.py`: every root `*.html` except
  `sidebar.html` (a shared fragment, not a page), with priorities `store.html` 1.0,
  `index.html` 0.8, `portfolio.html` 0.6, everything else 0.5, and `lastmod` = **the date
  the build script ran** (`date.today()`), applied to *all* URLs uniformly.
- **lastmod-churn caveat:** because lastmod is the build date, every build stamps *every*
  page as "modified today" even if nothing changed. Search engines learn to distrust
  inaccurate lastmod and may ignore it; it also invites pointless recrawls. Don't run the
  build gratuitously, and don't treat sitemap lastmod as a real change record — git history
  is the change record. (Known limitation, accepted for simplicity.)
- Submission/validation: Google Search Console → Sitemaps → submit
  `https://mkhome.byst.re/sitemap.xml`; quick manual check is just opening
  `https://mkhome.byst.re/robots.txt` and `.../sitemap.xml` in a browser
  (per doc/seo-validation.md).

## 6. Validation workflow (run after any SEO-touching change)

Source of record: `doc/seo-validation.md`. Each validator mapped to the historical failure
it would have caught (all from commit `0fc1ba1`'s fix list):

| Validator | URL | Catches | Caught here historically |
|---|---|---|---|
| Facebook Sharing Debugger | https://developers.facebook.com/tools/debug/ | OG tags as Facebook parses them; forces preview-cache refresh | OG validation feedback that fed `0fc1ba1` |
| Twitter Card Validator | https://cards-dev.twitter.com/validator | twitter:card rendering | — (preventive) |
| LinkedIn Post Inspector | https://www.linkedin.com/post-inspector/ | LinkedIn preview quality and metadata | Blurry preview (missing og:image:width/height) and missing date (missing article:published_time) |
| Google Rich Results Test | https://search.google.com/test/rich-results | JSON-LD eligibility for rich results | Book schema without offers/price not producing product rich results → switched to Product |
| Schema.org Validator | https://validator.schema.org/ | Detailed schema correctness beyond Google's subset | — (preventive) |
| Google Search Console | https://search.google.com/search-console | Sitemap acceptance; URL Inspection shows the crawled page (proves noscript content is seen) | — |
| Lighthouse (Chrome DevTools) / PageSpeed Insights | https://pagespeed.web.google.com/ | Automated SEO audit per page (meta presence, crawlability basics) | — |

Minimum loop after a change: Rich Results Test on `mkhome.byst.re/store.html` + one social
debugger (LinkedIn is the strictest here) + the curl noscript check from §4. Note the
social debuggers also *re-scrape*, which is how you bust a stale preview cache after fixing
OG tags.

## 7. Target-market asymmetry: Spanish for crawlers, English for humans

Per doc/seo-implementation-plan.md, the primary SEO audience is **Spanish-speaking
seniors** searching for the IT-for-seniors ebook (keywords like "informática para mayores").
Consequences baked into the code — do not "harmonize" them away:

- `build-store.py` has `DEFAULT_LANG = "es"`: all crawler-facing generated content
  (JSON-LD, noscript cards) is Spanish. store.html's title/description/keywords/OG text are
  Spanish too.
- But the **client-side** default is English: `let currentLang = localStorage.getItem('storeLang') || 'en';`
  (store.html:598), the EN button starts `active`, and `<html lang="en">`.

So a first-time human visitor sees English while Google indexes Spanish. This asymmetry is
**intentional** (crawlers = target market, direct visitors = mixed/professional audience),
but it is genuinely inconsistent — notably `lang="en"` on a page whose indexed content is
Spanish. If a task involves changing default language anywhere, surface this trade-off to
the owner instead of silently picking a side.

## Provenance and maintenance

- Verified 2026-07-05 against: `store.html`, `index.html`, `scripts/build-store.py`, `store/products.json`, `sitemap.xml`, `robots.txt`, `doc/seo-validation.md`, `doc/seo-implementation-plan.md`, `git show 0fc1ba1` / `0860584`.
- Line numbers, the 9.99-vs-10.49 price drift, and the tool-pages metadata gap are point-in-time (2026-07-05); re-check before relying on them.
- Validator URLs come from doc/seo-validation.md; if one 404s, update that doc first, then this skill.
- If build-store.py's DEFAULT_LANG, markers, or sitemap rules change, update §§2, 4, 5, 7 here and the runbook in `mkhome-store-pipeline` together.
