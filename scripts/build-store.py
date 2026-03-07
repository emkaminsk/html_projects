#!/usr/bin/env python3
"""Build script that injects SEO content into store.html from products.json.

Generates:
1. JSON-LD Schema.org structured data for each product
2. <noscript> static product cards (Spanish default) for crawlers
3. Updated sitemap.xml with all HTML pages
"""

import json
import re
import html
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
STORE_HTML = ROOT / "store.html"
PRODUCTS_JSON = ROOT / "store" / "products.json"
SITEMAP_XML = ROOT / "sitemap.xml"
BASE_URL = "https://mkhome.byst.re"
DEFAULT_LANG = "es"


def load_products():
    with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_jsonld(products):
    blocks = []
    for product in products:
        p = product.get(DEFAULT_LANG, product.get("en"))
        schema = {
            "@context": "https://schema.org",
            "@type": "Book",
            "name": p["title"],
            "author": {"@type": "Person", "name": "Marcin Kaminski"},
            "description": p["description"],
            "url": product["kdpUrl"],
            "image": f"{BASE_URL}/{product['image']}",
            "inLanguage": DEFAULT_LANG,
            "bookFormat": "EBook",
            "offers": {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "url": product["kdpUrl"],
            },
        }
        block = json.dumps(schema, ensure_ascii=False, indent=2)
        blocks.append(f'<script type="application/ld+json">\n{block}\n</script>')
    return "\n".join(blocks)


def generate_noscript(products):
    cards = []
    for product in products:
        p = product.get(DEFAULT_LANG, product.get("en"))
        title = html.escape(p["title"])
        subtitle = html.escape(p["subtitle"])
        desc = html.escape(p["description"])
        img_alt = html.escape(p["title"])
        highlights_html = "\n".join(
            f"                        <li>{html.escape(h)}</li>" for h in p["highlights"]
        )
        cta = html.escape(p["cta"])
        kdp_url = html.escape(product["kdpUrl"])
        image = html.escape(product["image"])

        card = f"""                <article class="product-card">
                    <div class="product-image-wrapper">
                        <img src="{image}" alt="{img_alt}" loading="lazy">
                    </div>
                    <div class="product-body">
                        <h2>{title}</h2>
                        <p class="product-subtitle">{subtitle}</p>
                        <p class="product-description">{desc}</p>
                        <ul class="product-highlights">
{highlights_html}
                        </ul>
                        <a href="{kdp_url}" target="_blank" rel="noopener noreferrer" class="product-cta">
                            {cta}
                        </a>
                    </div>
                </article>"""
        cards.append(card)

    inner = "\n".join(cards)
    return f"""            <noscript>
            <div class="products-grid">
{inner}
            </div>
            </noscript>"""


def inject_between_markers(content, start_marker, end_marker, payload):
    pattern = re.compile(
        rf"([ \t]*{re.escape(start_marker)}\n).*?([ \t]*{re.escape(end_marker)})",
        re.DOTALL,
    )
    return pattern.sub(rf"\g<1>{payload}\n\g<2>", content)


def generate_sitemap():
    html_files = sorted(ROOT.glob("*.html"))
    priorities = {
        "store.html": "1.0",
        "index.html": "0.8",
        "portfolio.html": "0.6",
    }
    today = date.today().isoformat()

    urls = []
    for f in html_files:
        if f.name == "sidebar.html":
            continue
        priority = priorities.get(f.name, "0.5")
        urls.append(
            f"  <url>\n"
            f"    <loc>{BASE_URL}/{f.name}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def main():
    products = load_products()

    # Read store.html
    store_content = STORE_HTML.read_text(encoding="utf-8")

    # Generate and inject JSON-LD
    jsonld = generate_jsonld(products)
    store_content = inject_between_markers(
        store_content, "<!-- SEO:JSON-LD -->", "<!-- /SEO:JSON-LD -->", jsonld
    )

    # Generate and inject noscript
    noscript = generate_noscript(products)
    store_content = inject_between_markers(
        store_content, "<!-- SEO:NOSCRIPT -->", "<!-- /SEO:NOSCRIPT -->", noscript
    )

    # Write store.html
    STORE_HTML.write_text(store_content, encoding="utf-8")
    print(f"Updated {STORE_HTML}")

    # Generate sitemap
    sitemap = generate_sitemap()
    SITEMAP_XML.write_text(sitemap, encoding="utf-8")
    print(f"Updated {SITEMAP_XML}")


if __name__ == "__main__":
    main()
