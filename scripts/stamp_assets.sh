#!/bin/sh
# Cache-bust local JS/CSS references in deployed HTML: x.css -> x.css?v=<version>.
# Usage: stamp_assets.sh <version> <file.html>...
# nginx serves the repo checkout directly, so this edits tracked files on the VPS.
# The deploy workflow runs `git checkout -- '*.html'` before `git pull` to undo the
# previous stamp; never run this on your local working copy.
set -eu
ver="$1"; shift
case "$ver" in *[!0-9a-zA-Z]*|'') echo "bad version: $ver" >&2; exit 1;; esac
# Only relative refs in src= / href= (first char not '/', so //cdn and /abs are skipped;
# no ':' so https: URLs are skipped); already-stamped refs (with '?') are skipped.
sed -E -i "s#((src|href)=\"[^\"/:?][^\":?]*\.(js|css))\"#\1?v=${ver}\"#g" "$@"
