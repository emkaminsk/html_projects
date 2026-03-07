# Purpose

This repository is my home page, contains my updated CV, portfolio. Also it is a collection of my personal projects and experiments.

This is a static website built with HTML, CSS and JavaScript.

## Project Structure

```
├── index.html              # Homepage
├── store.html              # Digital store (multilingual: EN/ES/PL)
├── portfolio.html           # Professional portfolio
├── projects.html            # Side projects (JSON Prettifier, QR Code, Morse)
├── utilities.html           # External tools (Searchexity, VIM, games)
├── sidebar.html             # Shared navigation sidebar
├── styles.css               # Shared styles
├── script.js                # Shared JS (sidebar, scroll, etc.)
├── robots.txt               # Search engine crawling rules
├── sitemap.xml              # Auto-generated sitemap
├── store/
│   ├── products.json        # Product data (single source of truth for store)
│   └── assets/              # Product images and OG image
├── scripts/
│   ├── build-store.py       # Injects SEO content into store.html
│   └── generate-og-image.py # Generates Open Graph image (1200x630px)
└── doc/
    └── seo-implementation-plan.md  # Full SEO strategy document
```

## Python Virtual Environment

Activate before running any scripts:

```bash
source venv/bin/activate
```

Installed packages: `Pillow` (image generation).

## Build Scripts

### `scripts/build-store.py`

Reads `store/products.json` and injects into `store.html`:

1. **JSON-LD Schema.org** structured data (Book type) for each product
2. **`<noscript>` static product cards** (Spanish default) so crawlers see content
3. **Regenerates `sitemap.xml`** from all `.html` files in root

Run after any `products.json` update:

```bash
source venv/bin/activate
python3 scripts/build-store.py
```

The script is idempotent — it replaces content between marker comments (`<!-- SEO:NOSCRIPT -->` / `<!-- SEO:JSON-LD -->`).

### `scripts/generate-og-image.py`

Generates the Open Graph preview image at `store/assets/og-image.png` (1200x630px) using the site's brand gradient colors.

```bash
source venv/bin/activate
python3 scripts/generate-og-image.py
```

## SEO Maintenance

All pages include: `<meta name="description">`, `<meta name="author">`, `<link rel="canonical">`, Open Graph tags, and Twitter Card tags.

The store page additionally has:
- Spanish meta description and keywords (primary target market)
- `hreflang` tags for EN/ES/PL
- Schema.org JSON-LD structured data (auto-generated)
- `<noscript>` fallback product cards (auto-generated)

**When adding a new page**: add meta tags to `<head>`, and re-run `build-store.py` to update the sitemap.

**When adding/editing products**: edit `store/products.json`, then run `build-store.py`.

## Analytics

See statistics at https://emkaminsk.goatcounter.com/

The code to add:
```javascript
<script data-goatcounter="https://emkaminsk.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
```
