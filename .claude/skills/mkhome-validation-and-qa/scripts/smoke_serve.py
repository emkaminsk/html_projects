#!/usr/bin/env python3
"""smoke_serve.py — serve the repo over HTTP and smoke-test every page.

Starts python's stdlib http.server on a free port (fetch() breaks on file://,
so this mirrors how the site is actually consumed), requests each page + core
assets, and asserts HTTP 200 plus a per-page sentinel string that proves the
RIGHT content was served (not a 404 page or an empty shell). Shuts the server
down cleanly.

Exit code: 0 if all checks pass, 1 if any FAIL, 2 on usage error.
Usage: python3 smoke_serve.py [--root /path/to/repo] [--port N]
"""
import argparse
import functools
import http.server
import socketserver
import sys
import threading
import urllib.request
from pathlib import Path

# path -> list of sentinel substrings that must ALL be present in the body.
# Sentinels are verified ground truth as of 2026-07-05 — update them when a
# page's title/markup legitimately changes.
SENTINELS = {
    "/index.html": ['<nav class="sidebar" id="sidebar">',
                    "Marcin Kamiński | Senior Consultant"],
    "/store.html": ['<nav class="sidebar" id="sidebar">',
                    'class="products-grid"',          # noscript crawler fallback
                    "<!-- SEO:JSON-LD -->"],
    "/portfolio.html": ['<div class="sidebar">', "Portfolio | Marcin Kamiński"],
    "/projects.html": ['<div class="sidebar">', "Projects | Marcin Kamiński"],
    "/utilities.html": ['<div class="sidebar">', "Utilities | Marcin Kamiński"],
    "/json_prettifier.html": ["<h1>JSON Prettifier</h1>"],
    "/qr_code_generator.html": ["<title>QR Code Generator</title>"],
    "/morse_converter.html": ["<title>Bidirectional Morse Code Converter</title>"],
    "/sidebar.html": ['href="index.html"', 'href="store.html"'],
    "/styles.css": ["--accent-color: #667eea"],
    "/script.js": ["menuToggle"],
    "/store/products.json": ['"kdpUrl"'],
    "/sitemap.xml": ["<urlset"],
    "/robots.txt": [],  # 200 is enough
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # keep test output readable
        pass


def main():
    ap = argparse.ArgumentParser(description="HTTP smoke test: serve repo root, assert 200 + sentinel per page.")
    ap.add_argument("--root", default=None, help="Repo root (default: auto-detect from script location)")
    ap.add_argument("--port", type=int, default=0, help="Port (default 0 = pick a free one)")
    args = ap.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[4]
    if not (root / "index.html").exists():
        print(f"FAIL: {root} has no index.html — wrong --root")
        sys.exit(2)

    handler = functools.partial(QuietHandler, directory=str(root))
    with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), handler) as httpd:
        httpd.daemon_threads = True
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        print(f"Serving {root} on http://127.0.0.1:{port} (temporary)")

        passes = fails = 0
        for path, sentinels in SENTINELS.items():
            url = f"http://127.0.0.1:{port}{path}"
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    status = resp.status
                    body = resp.read().decode("utf-8", errors="replace")
            except Exception as e:
                print(f"FAIL: {path} — request error: {e}")
                fails += 1
                continue
            if status != 200:
                print(f"FAIL: {path} — HTTP {status} (expected 200)")
                fails += 1
                continue
            missing = [s for s in sentinels if s not in body]
            if missing:
                print(f"FAIL: {path} — HTTP 200 but sentinel(s) missing: {missing}")
                fails += 1
            else:
                extra = f" + {len(sentinels)} sentinel(s)" if sentinels else ""
                print(f"PASS: {path} — HTTP 200{extra}")
                passes += 1

        httpd.shutdown()
    t.join(timeout=5)
    print("Server shut down cleanly")
    print(f"\nSUMMARY: {passes} PASS, 0 WARN, {fails} FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
