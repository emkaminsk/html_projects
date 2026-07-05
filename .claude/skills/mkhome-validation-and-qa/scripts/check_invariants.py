#!/usr/bin/env python3
"""check_invariants.py — static invariant checks for the mkhome.byst.re repo.

Read-only. Checks head-metadata contract, GoatCounter coverage, SEO markers,
sitemap consistency, sidebar links, products.json schema, visual-identity
tokens, menuToggle placement, and charset declarations.

Exit code: 0 if no FAIL (WARNs allowed), 1 if any FAIL, 2 on usage error.
Usage: python3 check_invariants.py [--root /path/to/repo]
"""
import argparse
import json
import re
import sys
from pathlib import Path

MAIN_PAGES = ["index.html", "store.html", "portfolio.html", "projects.html", "utilities.html"]
TOOL_PAGES = ["json_prettifier.html", "qr_code_generator.html", "morse_converter.html"]
SEO_MARKERS = ["<!-- SEO:JSON-LD -->", "<!-- /SEO:JSON-LD -->",
               "<!-- SEO:NOSCRIPT -->", "<!-- /SEO:NOSCRIPT -->"]
PRODUCT_TOP_FIELDS = ["id", "image", "category", "price", "currency", "kdpUrl"]
PRODUCT_LANGS = ["en", "es", "pl"]
PRODUCT_LANG_FIELDS = ["title", "subtitle", "description", "highlights", "cta"]

results = []


def emit(level, msg):
    results.append((level, msg))
    print(f"{level}: {msg}")


def read(path):
    return path.read_text(encoding="utf-8")


def check_head_contract(root):
    """Five main pages must carry the full head-metadata contract."""
    checks = [
        ("title", re.compile(r"<title>[^<]+</title>")),
        ("meta description", re.compile(r'<meta\s+name="description"')),
        ("meta author", re.compile(r'<meta\s+name="author"')),
        ("canonical", re.compile(r'<link\s+rel="canonical"')),
        ("og:image:width 1200", re.compile(r'property="og:image:width"\s+content="1200"')),
        ("og:image:height 630", re.compile(r'property="og:image:height"\s+content="630"')),
        ("twitter:card", re.compile(r'name="twitter:card"')),
        ("GoatCounter snippet", re.compile(r"goatcounter", re.I)),
        ("html lang attr", re.compile(r'<html\s+lang="[a-zA-Z-]+"')),
    ]
    for page in MAIN_PAGES:
        p = root / page
        if not p.exists():
            emit("FAIL", f"head-contract: {page} is missing from repo root")
            continue
        content = read(p)
        missing = [name for name, rx in checks if not rx.search(content)]
        if missing:
            emit("FAIL", f"head-contract: {page} missing: {', '.join(missing)}")
        else:
            emit("PASS", f"head-contract: {page} has full head-metadata contract")


def check_goatcounter(root):
    """Every root *.html except sidebar.html (include fragment) needs GoatCounter."""
    for p in sorted(root.glob("*.html")):
        if p.name == "sidebar.html":
            continue
        if "goatcounter" in read(p).lower():
            emit("PASS", f"goatcounter: {p.name} has the GoatCounter snippet")
        else:
            emit("FAIL", f"goatcounter: {p.name} lacks the GoatCounter snippet — analytics blind spot")


def check_seo_markers(root):
    """store.html must contain each SEO marker exactly once (build-store.py anchors)."""
    content = read(root / "store.html")
    ok = True
    for marker in SEO_MARKERS:
        n = content.count(marker)
        if n != 1:
            emit("FAIL", f"seo-markers: '{marker}' appears {n}x in store.html (must be exactly 1) — build-store.py injection will corrupt the page")
            ok = False
    if ok:
        emit("PASS", "seo-markers: all 4 SEO markers appear exactly once in store.html")


def check_sitemap(root):
    """sitemap.xml must list exactly the root *.html files minus sidebar.html."""
    sitemap = read(root / "sitemap.xml")
    listed = set(re.findall(r"<loc>https://mkhome\.byst\.re/([^<]+)</loc>", sitemap))
    expected = {p.name for p in root.glob("*.html")} - {"sidebar.html"}
    missing = expected - listed
    extra = listed - expected
    if missing:
        emit("FAIL", f"sitemap: root pages not in sitemap.xml: {sorted(missing)} — run: python3 scripts/build-store.py")
    if extra:
        emit("FAIL", f"sitemap: sitemap.xml lists non-existent/excluded pages: {sorted(extra)}")
    if not missing and not extra:
        emit("PASS", f"sitemap: sitemap.xml lists exactly the {len(expected)} root pages (sidebar.html correctly excluded)")


def check_sidebar_links(root):
    """Every relative href in sidebar.html must resolve to a real file."""
    content = read(root / "sidebar.html")
    hrefs = re.findall(r'href="([^"]+)"', content)
    broken = []
    internal = 0
    for h in hrefs:
        if h.startswith(("http://", "https://", "mailto:", "#")):
            continue
        internal += 1
        if not (root / h.split("#")[0]).exists():
            broken.append(h)
    if broken:
        emit("FAIL", f"sidebar-links: broken internal links in sidebar.html: {broken}")
    else:
        emit("PASS", f"sidebar-links: all {internal} internal links in sidebar.html resolve to files")


def check_products_json(root):
    """products.json must parse and every product must be complete in en/es/pl."""
    path = root / "store" / "products.json"
    try:
        products = json.loads(read(path))
    except (json.JSONDecodeError, OSError) as e:
        emit("FAIL", f"products-json: store/products.json unreadable/invalid: {e}")
        return
    if not isinstance(products, list) or not products:
        emit("FAIL", "products-json: store/products.json must be a non-empty array")
        return
    problems = []
    for i, prod in enumerate(products):
        pid = prod.get("id", f"#index-{i}")
        for f in PRODUCT_TOP_FIELDS:
            if f not in prod:
                problems.append(f"{pid}: missing top-level '{f}'")
        img = prod.get("image")
        if img and not (root / img).exists():
            problems.append(f"{pid}: image file '{img}' does not exist")
        for lang in PRODUCT_LANGS:
            if lang not in prod:
                problems.append(f"{pid}: missing language block '{lang}'")
                continue
            for f in PRODUCT_LANG_FIELDS:
                if f not in prod[lang]:
                    problems.append(f"{pid}.{lang}: missing '{f}'")
            hl = prod.get(lang, {}).get("highlights")
            if hl is not None and (not isinstance(hl, list) or not hl):
                problems.append(f"{pid}.{lang}: 'highlights' must be a non-empty list")
    if problems:
        for pr in problems:
            emit("FAIL", f"products-json: {pr}")
    else:
        emit("PASS", f"products-json: {len(products)} products valid, all fields present x {len(PRODUCT_LANGS)} languages, images exist")


def check_visual_identity(root):
    """Tripwire: accent colors and Lato must survive any CSS change."""
    css = read(root / "styles.css")
    tokens = {
        "--accent-color: #667eea": "--accent-color: #667eea" in css,
        "--accent-color-2: #764ba2": "--accent-color-2: #764ba2" in css,
        "Lato font-family reference": "Lato" in css,
    }
    bad = [t for t, ok in tokens.items() if not ok]
    if bad:
        emit("FAIL", f"visual-identity: styles.css lost non-negotiable token(s): {bad} — restore before merging (see mkhome-change-control)")
    else:
        emit("PASS", "visual-identity: styles.css has --accent-color #667eea, --accent-color-2 #764ba2, Lato")
    # The Lato webfont <link> lives in page heads, not styles.css. As of
    # 2026-07-05 only index.html and store.html actually load it;
    # portfolio/projects/utilities declare 'Lato' via styles.css but never
    # fetch the font (pre-existing gap -> WARN). Losing the link on
    # index/store would be a NEW regression -> FAIL.
    for page in ("index.html", "store.html"):
        if "fonts.googleapis.com/css2?family=Lato" in read(root / page):
            emit("PASS", f"visual-identity: {page} loads the Lato webfont")
        else:
            emit("FAIL", f"visual-identity: {page} lost its Lato Google-Fonts link — restore it (visual identity is non-negotiable)")
    for page in ("portfolio.html", "projects.html", "utilities.html"):
        if "fonts.googleapis.com/css2?family=Lato" in read(root / page):
            emit("PASS", f"visual-identity: {page} loads the Lato webfont (gap fixed — update this check's baseline)")
        else:
            emit("WARN", f"visual-identity: {page} never loads the Lato webfont (pre-existing gap as of 2026-07-05; styles.css asks for Lato but the page falls back to sans-serif — fix opportunistically)")


def check_menu_toggle(root):
    """menuToggle must ONLY be created by script.js (PR #1/8b05870: a fixed-position
    button inside .sidebar is trapped by the transform containing block)."""
    offenders = []
    for p in sorted(root.glob("*.html")):
        if re.search(r'id="menuToggle"', read(p)):
            offenders.append(p.name)
    if offenders:
        emit("FAIL", f"menu-toggle: static id=\"menuToggle\" found in {offenders} — it must be created dynamically by script.js on <body>, never in sidebar markup")
    else:
        emit("PASS", "menu-toggle: no static menuToggle in any HTML file (script.js creates it on <body>)")


def check_charset(root):
    """Main pages MUST declare charset. Tool pages + sidebar.html currently don't
    (verified pre-existing gap as of 2026-07-05) — WARN, not FAIL."""
    rx = re.compile(r'<meta\s+charset=', re.I)
    for page in MAIN_PAGES:
        if rx.search(read(root / page)):
            emit("PASS", f"charset: {page} declares <meta charset>")
        else:
            emit("FAIL", f"charset: {page} lacks <meta charset> — main pages must declare it (mojibake risk)")
    for page in TOOL_PAGES + ["sidebar.html"]:
        p = root / page
        if not p.exists():
            continue
        if rx.search(read(p)):
            emit("PASS", f"charset: {page} declares <meta charset>")
        else:
            reason = ("include fragment, head never used" if page == "sidebar.html"
                      else "standalone tool page with minimal head by design")
            emit("WARN", f"charset: {page} lacks <meta charset> (pre-existing gap; {reason}; served UTF-8 by nginx — fix opportunistically, not blocking)")


def main():
    ap = argparse.ArgumentParser(description="Static invariant checks for the mkhome.byst.re repo (read-only).")
    ap.add_argument("--root", default=None, help="Repo root (default: auto-detect from script location)")
    args = ap.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[4]
    if not (root / "styles.css").exists() or not (root / "index.html").exists():
        print(f"FAIL: {root} does not look like the mkhome repo root (no styles.css/index.html). Use --root.")
        sys.exit(2)

    check_head_contract(root)
    check_goatcounter(root)
    check_seo_markers(root)
    check_sitemap(root)
    check_sidebar_links(root)
    check_products_json(root)
    check_visual_identity(root)
    check_menu_toggle(root)
    check_charset(root)

    fails = sum(1 for lv, _ in results if lv == "FAIL")
    warns = sum(1 for lv, _ in results if lv == "WARN")
    passes = sum(1 for lv, _ in results if lv == "PASS")
    print(f"\nSUMMARY: {passes} PASS, {warns} WARN, {fails} FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
