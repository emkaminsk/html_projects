#!/usr/bin/env python3
"""check_store_sync.py — detect drift between store/products.json and the
committed generated blocks in store.html (JSON-LD + noscript) and sitemap.xml.

How it works (NEVER touches repo files):
  1. Copies store.html, sitemap.xml, store/products.json and scripts/build-store.py
     into a temp directory, preserving relative layout.
  2. Runs the repo's OWN build-store.py inside the temp copy.
  3. Diffs the regenerated store.html against the committed one. ANY difference
     means products.json changed without re-running the generator -> FAIL.
  4. Diffs sitemap.xml ignoring <lastmod> lines (they churn to today's date on
     every run — that alone is not drift). Structural URL/priority drift -> FAIL.

Exit code: 0 if in sync, 1 if drift (FAIL), 2 on usage/environment error.
Usage: python3 check_store_sync.py [--root /path/to/repo] [--full-diff]
"""
import argparse
import difflib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_DIFF_LINES = 40


def strip_lastmod(text):
    return re.sub(r"^\s*<lastmod>[^<]*</lastmod>\n", "", text, flags=re.M)


def main():
    ap = argparse.ArgumentParser(
        description="Rebuild store.html generated blocks in a temp copy and diff against the committed file.")
    ap.add_argument("--root", default=None, help="Repo root (default: auto-detect from script location)")
    ap.add_argument("--full-diff", action="store_true",
                    help=f"Print the whole diff instead of the first {MAX_DIFF_LINES} lines")
    args = ap.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[4]

    needed = ["store.html", "sitemap.xml", "store/products.json", "scripts/build-store.py"]
    for rel in needed:
        if not (root / rel).exists():
            print(f"FAIL: {root / rel} not found — wrong --root or repo layout changed")
            sys.exit(2)

    fails = 0
    with tempfile.TemporaryDirectory(prefix="mkhome-store-sync-") as td:
        tmp = Path(td)
        (tmp / "store").mkdir()
        (tmp / "scripts").mkdir()
        for rel in needed:
            shutil.copy2(root / rel, tmp / rel)
        # build-store.py regenerates the sitemap from ROOT.glob("*.html"),
        # so the temp copy needs every root page (sidebar.html included —
        # the generator itself excludes it).
        for page in root.glob("*.html"):
            if not (tmp / page.name).exists():
                shutil.copy2(page, tmp / page.name)

        proc = subprocess.run(
            [sys.executable, str(tmp / "scripts" / "build-store.py")],
            capture_output=True, text=True)
        if proc.returncode != 0:
            print("FAIL: build-store.py crashed in the temp copy — fix the generator/products.json first")
            print(proc.stderr.strip())
            sys.exit(1)

        committed = (root / "store.html").read_text(encoding="utf-8")
        regenerated = (tmp / "store.html").read_text(encoding="utf-8")
        if committed == regenerated:
            print("PASS: store.html generated blocks (JSON-LD + noscript) match store/products.json")
        else:
            fails += 1
            print("FAIL: store.html is OUT OF SYNC with store/products.json — "
                  "products.json changed without re-running build-store.py — "
                  "run: python3 scripts/build-store.py (then commit store.html + sitemap.xml together)")
            diff = list(difflib.unified_diff(
                committed.splitlines(), regenerated.splitlines(),
                fromfile="store.html (committed)", tofile="store.html (regenerated from products.json)",
                lineterm=""))
            shown = diff if args.full_diff else diff[:MAX_DIFF_LINES]
            for line in shown:
                print("  " + line)
            if len(diff) > len(shown):
                print(f"  ... {len(diff) - len(shown)} more diff lines (use --full-diff)")

        committed_sm = strip_lastmod((root / "sitemap.xml").read_text(encoding="utf-8"))
        regenerated_sm = strip_lastmod((tmp / "sitemap.xml").read_text(encoding="utf-8"))
        if committed_sm == regenerated_sm:
            print("PASS: sitemap.xml matches regenerated output (ignoring <lastmod>, which churns by design)")
        else:
            fails += 1
            print("FAIL: sitemap.xml structurally differs from what build-store.py would generate "
                  "(URL set/priorities, NOT lastmod) — run: python3 scripts/build-store.py")
            for line in list(difflib.unified_diff(
                    committed_sm.splitlines(), regenerated_sm.splitlines(),
                    fromfile="sitemap.xml (committed, lastmod stripped)",
                    tofile="sitemap.xml (regenerated, lastmod stripped)", lineterm=""))[:MAX_DIFF_LINES]:
                print("  " + line)

    print(f"\nSUMMARY: {2 - fails} PASS, 0 WARN, {fails} FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
