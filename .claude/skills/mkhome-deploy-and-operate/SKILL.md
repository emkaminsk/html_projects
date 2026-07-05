---
name: mkhome-deploy-and-operate
description: >
  Deploy and operations runbook for mkhome.byst.re (Marcin Kaminski's static site).
  Load when: deploying or releasing a change to main; verifying a release actually
  landed in production; production differs from what's in the repo (stale content,
  wrong version live); touching nginx config (.deploy/mkhome, nginx.conf.example),
  the GitHub Actions deploy workflow, or cache/Cache-Control behavior; checking
  analytics or site availability; investigating why a CSS/JS change isn't visible.
  Covers the commit→Action→SSH→git-pull deploy chain, curl verification commands,
  the cache policy table, nginx anatomy, and config-drift rules.
---

# mkhome: Deploy and Operate

Runbook for shipping changes to https://mkhome.byst.re and verifying they landed. Facts date-stamped (as of 2026-07-05); re-verify anything critical against the repo and live site.

**Jargon, once:** "VPS" = the owner's rented Linux server running nginx. "Action" = the GitHub Actions workflow `.github/workflows/deploy.yml`. "Docroot" = the directory nginx serves files from — here it is literally the git working tree of this repo on the VPS. "Drift" = live server state differing from what the repo says it should be.

## When NOT to use this skill

- Deciding *whether* a change may go to main → `mkhome-change-control`.
- Pre-merge validation/QA steps → `mkhome-validation-and-qa`.
- Debugging site bugs (JS errors, layout) → `mkhome-debugging-playbook` (it has the stale-cache triage summary; full cache detail lives here).
- Local dev server / environment setup → `mkhome-build-and-env`.
- Store/product generation → `mkhome-store-pipeline`. SEO files' *content* → `mkhome-seo-reference`.

## What you can and cannot do (AI session capabilities)

| Can do from a session | Cannot do — needs the owner |
|---|---|
| git operations, push to main (per change-control rules) | SSH to the VPS |
| Check Action runs (GitHub MCP tools or web UI) | Run `git pull` manually on the VPS |
| `curl` the public site to verify live state | Apply nginx config changes (`nginx -t`, `systemctl reload nginx`) |
| Read `.deploy/mkhome` (repo copy of nginx config) | Read the *live* nginx config or VPS logs |

Never claim to have run a VPS-side command. If a step needs the VPS, say so explicitly and hand the exact commands to the owner.

## 1. Deploy anatomy (as of 2026-07-05)

```
you commit ──► push to main ──► GitHub Action "Deploy to VPS" ──► SSH to VPS ──► git pull ──► nginx serves the working tree
   (1)            (2)                    (3)                        (4)             (5)              (6)
```

That is the ENTIRE deploy. No build step, no artifact upload: **the git working tree on the VPS is the nginx docroot**, so main IS production and committed files ARE the deployed artifacts (generated store.html blocks, sitemap.xml, og-image.png are committed, not built).

The workflow (`.github/workflows/deploy.yml`): single job, `appleboy/ssh-action@master`, secrets `VPS_HOST`/`VPS_USERNAME`/`VPS_SSH_KEY`, script is exactly `cd gitrepos/html_projects && git pull`.

| Hop | What can fail | Where to look |
|---|---|---|
| 1–2 Commit/push | Push rejected, wrong branch | `git log origin/main`, local git output |
| 3 Action triggers | Workflow disabled, YAML broken, only fires on push to `main` | Actions tab / `actions_list` MCP tool |
| 4 SSH | Secret rotated/expired, VPS down, host key change | Action run logs (red run) |
| 5 `git pull` | **Merge conflict or dirty working tree on the VPS → pull fails or partially applies while the Action may still look green** — see §7 | Sentinel curl check (§2, §7); Action step logs |
| 6 nginx serves | Stale browser/edge cache (1h css/js, 1w images), live nginx config drift | `curl -sI` headers (§2), owner for VPS side |

Caution: whether a failed `git pull` turns the Action run red depends on ssh-action propagating the script's exit code — this is not verifiable from the repo alone. **Treat a green Action as "SSH ran", not "deploy succeeded". Only a live curl proves the deploy.**

## 2. Release runbook

1. **Pre-merge:** run the checks in `mkhome-validation-and-qa`; confirm the change is allowed per `mkhome-change-control`. Preserve visual identity — non-negotiable.
2. **Merge/push to main.** Note the commit SHA and pick a **sentinel string**: some text your change added that is greppable in a served file (e.g. a new heading, a CSS rule name).
3. **Verify the Action ran** (either way — do not assume `gh` CLI exists):
   - *GitHub MCP tools:* `actions_list` (workflow runs for the repo, workflow "Deploy to VPS") → newest run should reference your SHA and conclude `success`; `get_job_logs` if it failed.
   - *Web UI (relay to owner if you lack tools):* https://github.com/emkaminsk/html_projects → Actions tab → "Deploy to VPS" → newest run.
4. **Verify production with curl** (the only real proof):

```bash
# Site up + security headers present
curl -sI https://mkhome.byst.re/

# Your change is actually live (replace with your sentinel + the file you changed)
curl -s https://mkhome.byst.re/index.html | grep -F "YOUR_SENTINEL_STRING"

# Cache headers on assets — READ the Cache-Control value
curl -sI https://mkhome.byst.re/styles.css | grep -i cache-control
```

5. **Interpret cache behavior:** css/js are cached 1 hour (`max-age=3600`). Your CSS/JS change can take **up to 1 hour** to reach returning visitors even after a perfect deploy. To bypass the cache when *testing*, request `https://mkhome.byst.re/styles.css?v=$(date +%s)` — a fresh query string is a cache miss. HTML is `no-cache, no-store`, so HTML changes appear immediately once the pull lands. Images/fonts: up to 1 week.
6. **If the sentinel is missing but the Action is green** → suspected stale VPS working tree; go to §7.

## 3. Cache policy table (from `.deploy/mkhome`, as of 2026-07-05)

| File type | TTL | Header sent | Operational consequence | Why it exists |
|---|---|---|---|---|
| `.css`, `.js` | 1h | `Cache-Control: public, max-age=3600` + `Vary: Accept-Encoding` | Style/script changes lag up to 1h for returning visitors; test with `?v=` query string | Nov 2025 cache-staleness incident: commits `d3b862c` "chore: attempt to fix caching problem" + `0ac08b4` "fix: nginx config" introduced per-type policy |
| images/fonts (`jpg jpeg png gif ico svg woff woff2 ttf eot`) | 1w | `Cache-Control: public, max-age=604800` | Replacing an image under the same filename lags up to a week — prefer a new filename | Same incident; heavy assets rarely change |
| `.html` | none | `Cache-Control: no-cache, no-store, must-revalidate` + `Pragma: no-cache` | HTML changes visible immediately after pull | Same incident; content freshness prioritized |

Open candidate (NOT implemented): a comment in the nginx file suggests versioned query strings (`styles.css?v=timestamp` in the HTML references) plus longer cache. If ever implemented, that changes this whole table — update it.

## 4. nginx config anatomy (`.deploy/mkhome`, repo copy, as of 2026-07-05)

Line-by-line intent (repo-derived; live config UNVERIFIABLE from the repo):

- `listen 80` / `listen [::]:80` — HTTP only in the repo copy; the live site serves HTTPS, so TLS termination (443 block/certs) exists on the VPS but is NOT in the repo. This is known, expected drift — the repo copy is partial.
- `root <user home path on VPS>` — the git clone directory; do not treat the literal path as load-bearing, it can differ on the VPS.
- `server_name mkhome mkhome.byst.re www.mkhome.byst.re` — the three served hostnames.
- `error_page 404 /error404.html` — **live discrepancy (verified in repo 2026-07-05): no `error404.html` exists anywhere in the repo.** nginx will internally redirect 404s to a missing file and fall back to its default 404 page. Fix: either commit an `error404.html` at repo root (styled per visual identity) or have the owner remove the directive.
- `location ~ /\. { deny all; ... }` — blocks ALL dotfiles/dot-dirs. Incident behind it: `.ai/`, `.cursor/`, `.github/` were once publicly servable (internal docs exposed); documented in `.ai/deployment-security.md`. Never remove this rule; `.git/` would be exposed too.
- Security headers: `X-Frame-Options SAMEORIGIN` (anti-clickjacking), `CSP object-src 'none'; frame-ancestors 'none'; base-uri 'self'` (blocks plugin embeds, framing, base-tag hijacks), `Strict-Transport-Security` (forces HTTPS for a year, preload), `X-Content-Type-Options nosniff` (no MIME sniffing), `Referrer-Policy no-referrer-when-downgrade`, `Permissions-Policy` (denies mic/camera/etc.; replaced the deprecated `Feature-Policy` in commit `0ac08b4`).
- Three `location ~* \.(…)$` blocks — the cache policy of §3, each with `try_files $uri =404`.
- `location / { try_files $uri $uri/ =404; }` — plain static file serving, no rewrites.

`nginx.conf.example` at repo root is a *generic documented example*, not the live config. `.deploy/mkhome` is the closer-to-live copy. Neither is authoritative for what the VPS actually runs.

## 5. Config-drift warning (critical)

**Editing `.deploy/mkhome` or `nginx.conf.example` changes NOTHING in production.** The deploy chain only runs `git pull`; nginx never re-reads config from the docroot. Applying a config change requires the owner, on the VPS (per `.ai/deployment-security.md`):

```bash
# OWNER ONLY — run on the VPS
sudo cp <repo>/.deploy/mkhome /etc/nginx/sites-available/<site>   # or hand-merge
sudo nginx -t
sudo systemctl reload nginx
```

Consequences for an AI session:
- Drift between the repo copy and the live server is possible and **undetectable from the repo alone**. Live headers (`curl -sI`) are the only observable truth.
- If you change a repo nginx file, your job is to (a) make the change, (b) tell the owner exactly what to run, (c) give a curl that proves it applied. Never report the config as "deployed".

## 6. Routine operations checks

```bash
# Hidden dirs blocked (expect 403 or 404 — NOT 200; a 200 is a security incident)
curl -s -o /dev/null -w "%{http_code}\n" https://mkhome.byst.re/.ai/tech-stack.md
curl -s -o /dev/null -w "%{http_code}\n" https://mkhome.byst.re/.git/config
curl -s -o /dev/null -w "%{http_code}\n" https://mkhome.byst.re/.cursor/

# SEO surface reachable (expect 200)
curl -s -o /dev/null -w "%{http_code}\n" https://mkhome.byst.re/robots.txt
curl -s -o /dev/null -w "%{http_code}\n" https://mkhome.byst.re/sitemap.xml

# Security headers still present
curl -sI https://mkhome.byst.re/ | grep -iE "x-frame|content-security|strict-transport|x-content-type"
```

Analytics/monitoring (as of 2026-07-05): **GoatCounter is the only monitoring** — dashboard https://emkaminsk.goatcounter.com/ (owner login; the count script `emkaminsk.goatcounter.com/count` is embedded in the HTML pages). There are **no uptime checks and no error tracking**. A traffic drop on GoatCounter can be the first sign of an outage.

## 7. Silent failure mode: stale production behind a green Action

Scenario: someone (or a stray process) edited files directly on the VPS → the working tree is dirty → `git pull` fails with a conflict → the Action may still show green (exit-code propagation through ssh-action is unverified) → **production silently serves the old version forever** while every future deploy also no-ops.

**Detect** (no VPS access needed):

```bash
# Pick a string that exists in repo main but predates your change window
git show origin/main:index.html | grep -F "SENTINEL"
# Compare against live:
curl -s https://mkhome.byst.re/index.html | grep -F "SENTINEL"
```

Use an HTML file for the comparison (no-cache, so no cache ambiguity). Repo-has-it / live-doesn't = stale VPS tree.

**Fix (owner only, on the VPS):** inspect `git status` in the clone; typically `git stash` or `git checkout -- <file>` then `git pull`. Never instruct `git reset --hard` without the owner confirming the local changes are disposable. Your role: detect, report the exact evidence (the two grep outputs), hand over commands.

## Provenance and maintenance

- Deploy chain: read from `.github/workflows/deploy.yml` (verified 2026-07-05).
- Cache/security/nginx facts: read from `.deploy/mkhome` and commits `d3b862c`, `0ac08b4` (verified 2026-07-05).
- Missing `error404.html`: verified absent from repo 2026-07-05; re-check before repeating the claim.
- Live-site claims (headers, dotfile blocking, 404 behavior): **repo-derived, live state UNVERIFIED** — authoring-session network blocked mkhome.byst.re (proxy CONNECT 403, 2026-07-05). Run the §6 curls yourself before asserting live behavior.
- If the deploy workflow, `.deploy/mkhome`, or the monitoring story changes, update §§1, 3, 4, 6 and re-date the stamps.
