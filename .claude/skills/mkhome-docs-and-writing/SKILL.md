---
name: mkhome-docs-and-writing
description: >-
  Documentation and writing conventions for the mkhome.byst.re repo (Marcin Kaminski's
  static site). Load when creating or updating README.md, anything under doc/ or .ai/,
  writing commit messages or PR descriptions, deciding WHERE a new fact or doc belongs,
  judging whether an existing doc is current or stale, or maintaining the .claude/skills/
  skill library itself (adding a skill, fixing a drifted fact, writing a Provenance
  section, chronicling an incident). Contains the docs-of-record map, house style,
  update-trigger table, skill-library maintenance rules, and templates for archaeology
  entries, PR descriptions, and new skills.
---

# mkhome Docs and Writing (as of 2026-07-05)

How to write anything in this repo — docs, commits, PRs, and the skill library itself.
Audience: an AI session with zero prior context. Facts below verified against the
working tree and `git log` on 2026-07-05; re-verify with the commands in Provenance.

## When NOT to use this skill

- Deciding whether a code/content change is safe → `mkhome-change-control`.
- How to verify a change works → `mkhome-validation-and-qa` (evidence doctrine lives there).
- Recording or looking up a specific bug's history → `mkhome-failure-archaeology`
  (this skill only gives the entry TEMPLATE; the entries live there).
- SEO metadata rules, deploy mechanics, store pipeline → the respective sibling skill.

## 1. Docs-of-record map

| File / dir | Status | What belongs there | Update trigger |
|---|---|---|---|
| `README.md` | **Current — doc of record** | Purpose, structure tree, venv note, build-script usage, SEO maintenance rules, GoatCounter analytics snippet | Any new page, script, or top-level file; any workflow change |
| `doc/seo-implementation-plan.md` | Current | SEO strategy of record | SEO strategy changes |
| `doc/seo-validation.md` | Current | How to run external validators (Facebook/LinkedIn/Google) | Validator URLs/process change |
| `doc/sidebar.md` | **STALE** (verified 2026-07-05) | Sidebar behavior brief | Candidate for rewrite via normal change flow — see finding below |
| `.ai/deployment-security.md` | **Current — operationally live** | nginx hardening guide | Any nginx/deploy change (with `.deploy/mkhome`) |
| `.ai/tech-stack.md` | Historical, partly aspirational | 2025 stack analysis | Do not update; supersede in skills |
| `.ai/transformation-{plan,checklist,examples}.md` | Historical | 2025 redesign campaign. Unchecked checklist items = still-open debts (SRI, CSP meta, innerHTML, jQuery removal, noopener) | Tick items only when the debt is actually paid |
| `.ai/*.png` (`local.png`, `production.png`) | Historical | Redesign-era screenshots | Never |
| `.cursor/rules/javascript.mdc` | **DO NOT FOLLOW** | Nothing — stale React-Native/Expo rules with `alwaysApply: true`; this repo has no React Native. Ignore its guidance entirely | Candidate for deletion via normal change flow |
| `.claude/skills/mkhome-*/SKILL.md` | Current — the skill library | Operational knowledge for AI sessions | Section 4 rules |
| `LICENSE` | Current | Apache License 2.0 (verified in file header) | Never, absent owner decision |

**Verified findings — candidates for fixing via normal change flow (do NOT fix while merely consulting this skill; open a change per `mkhome-change-control`):**

- `doc/sidebar.md` claims the sidebar uses "the Bootstrap framework and the navbar
  component". Actual: `sidebar.html` is a plain `<ul class="navbar-nav flex-column">`
  fragment (Bootstrap class names only, no Bootstrap JS), and `script.js` hand-rolls
  the toggle — it `document.createElement`s `#menuToggle` and a `#sidebarBackdrop`
  directly on `<body>` (since commit `8b05870`).
- `README.md` says `source venv/bin/activate` but never documents creating the venv;
  `venv/` is gitignored and absent from a fresh clone. Bootstrap is
  `python3 -m venv venv && venv/bin/pip install Pillow` (Pillow is the only documented package).

**Rule: one home per fact.** Every fact lives in exactly one doc or skill; everything
else cross-references it. On conflict between docs, the repo's actual code/config wins,
then README, then `doc/`, then skills; `.ai/` is historical and never wins.

## 2. House style

- **Language:** English everywhere (docs, commits, PRs) — even though site content is EN/ES/PL.
- **Markdown:** concise; headings + tables + fenced blocks over prose. No emojis.
- **Commands:** always in fenced ` ```bash ` blocks, copy-pasteable from repo root
  (e.g. `python3 scripts/build-store.py`, not `cd scripts && ...`).
- **Date-stamp volatile facts:** "(as of YYYY-MM-DD)" on anything that can drift
  (versions, URLs, line numbers, external services).

**Commit messages** (observed style, verified in `git log` 2026-07-05): the history
mixes conventional prefixes with plain sentences — **prefer conventional prefixes**
(`feat:` / `fix:` / `chore:`), imperative summary ≤ ~70 chars, body as `-` bullets
explaining what and why. Real examples from this repo:

- `0fc1ba1` — `fix: address SEO validation feedback from Facebook, LinkedIn, Google` (body: 5 bullets, one per change)
- `1285d55` — `feat: add comprehensive SEO infrastructure across all pages`
- `8b05870` — `Fix mobile navigation: move hamburger button outside sidebar` (plain-sentence form; body explains the CSS-transform root cause — good body, prefer a `fix:` prefix)

Claude-assisted commits carry a `Co-Authored-By:` trailer (e.g. `0fc1ba1` has
`Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`). Keep doing this.

**PR descriptions** must state what was verified and HOW — a claim without its
evidence command is not verification (doctrine: `mkhome-validation-and-qa`).
Use the template in section 5b.

## 3. Update triggers — when X changes, update Y

| You changed... | You MUST also update (same PR) |
|---|---|
| Added/removed a page (`*.html` in root) | README structure tree; per-page meta tags (see `mkhome-seo-reference`); re-run `python3 scripts/build-store.py` (regenerates `sitemap.xml`) |
| `store/products.json` | Re-run `python3 scripts/build-store.py`; commit regenerated `store.html` + `sitemap.xml` |
| Deploy/nginx behavior | `.ai/deployment-security.md` AND the `.deploy/mkhome` copy (keep both in sync; see `mkhome-deploy-and-operate`) |
| Resolved an incident / hit a dead end | New entry in `mkhome-failure-archaeology` SKILL.md (template in 5a) |
| Anything a skill states as fact | Fix that SKILL.md and its Provenance line in the SAME PR (section 4) |
| Build scripts / venv packages | README "Python Virtual Environment" + "Build Scripts" sections |
| Sidebar/nav structure | `sidebar.html` is the single source; check `doc/sidebar.md` for compounding staleness |

## 4. Skill-library maintenance rules

The library is `.claude/skills/mkhome-*` — 13 skills (as of 2026-07-05):
change-control, debugging-playbook, failure-archaeology, architecture-contract,
seo-reference, store-pipeline, build-and-env, deploy-and-operate, validation-and-qa,
docs-and-writing (this one), site-growth-campaign, analysis-toolkit, frontier-and-method.

1. **Ground truth only.** Before a skill states a command, path, or behavior, run it
   or read the source. Never copy a claim from another doc unverified (that is how
   `doc/sidebar.md` went stale).
2. **Provenance section mandatory.** Every SKILL.md ends with
   `## Provenance and maintenance`: one line per volatile fact with the exact
   re-verification command.
3. **Date-stamp volatile facts** "(as of YYYY-MM-DD)".
4. **One home per fact.** A fact lives in exactly one skill; siblings cross-reference
   by skill name. Never duplicate — duplicates drift independently.
5. **Repo wins over skill.** If a skill contradicts the code/config, the repo is
   right; fix the skill (and say so in the commit).
6. **Drift fixes ride the change.** A PR that invalidates a skill fact updates that
   SKILL.md + its Provenance line in the same PR (section 3).
7. **Incidents go to `mkhome-failure-archaeology`**, never scattered across skills.
8. **New skills** use the skeleton in 5c: trigger-rich `description:` (when to load,
   concrete symptoms/filenames), a "When NOT to use this skill" section, imperative
   voice, tables over prose. Audience is a Sonnet-class AI with zero context.

## 5. Templates

### 5a. Failure-archaeology entry (append to `mkhome-failure-archaeology/SKILL.md`)

```markdown
## <Short incident name> (<YYYY-MM>)

- **Symptom:** <what was observably wrong, from the user/crawler perspective>
- **Root cause:** <the actual mechanism, not the first hypothesis>
- **Evidence:** <commit hashes, `git show` output, curl output, validator screenshots>
- **Resolution:** <what fixed it, with commit hash; or "abandoned because ...">
- **Status:** RESOLVED | OPEN DEBT | WONTFIX (<date>)
```

### 5b. PR description

```markdown
## What
<1-3 sentences: the change and why.>

## Where
<Files touched and any docs/skills updated per the section-3 trigger table.>

## Verification
<One line per claim: the exact command run and its relevant output. E.g.:>
- `python3 scripts/build-store.py` → exit 0, sitemap.xml regenerated (diff reviewed)
- `git diff --stat` matches intended scope, no generated-block drift
- <Visual check per mkhome-validation-and-qa if CSS/layout touched>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### 5c. New-skill skeleton

```markdown
---
name: mkhome-<topic>
description: >-
  <What this skill contains>. Load when <concrete triggers: filenames, symptoms,
  task types — write for retrieval, not for elegance>.
---

# mkhome <Topic> (as of <YYYY-MM-DD>)

<One-paragraph scope statement. Facts verified against <source> on <date>.>

## When NOT to use this skill
- <Adjacent task> → `mkhome-<sibling>`.

## <Body: imperative sections, tables, fenced copy-pasteable commands>

## Provenance and maintenance
- <Fact>: re-verify with `<exact command>` (as of <date>).
```

## Provenance and maintenance

- Docs inventory (`README.md`, `doc/`, `.ai/`, `.cursor/rules/`): re-verify with `ls doc .ai .cursor/rules && wc -l README.md doc/*.md` (as of 2026-07-05).
- `doc/sidebar.md` staleness: re-verify with `cat doc/sidebar.md sidebar.html && grep -n "menuToggle\|createElement" script.js` — stale while it still claims Bootstrap navbar mechanics (as of 2026-07-05).
- README venv gap: re-verify with `grep -n venv README.md .gitignore && ls venv` — gap exists while README lacks a `python3 -m venv` line and `venv/` is absent (as of 2026-07-05).
- License type: re-verify with `head -3 LICENSE` (Apache 2.0 as of 2026-07-05).
- Commit-style examples (`0fc1ba1`, `1285d55`, `8b05870`): re-verify with `git log --format='%h %s' -20` and `git show -s --format=%B 0fc1ba1` (as of 2026-07-05).
- Skill inventory (13 mkhome-* skills): re-verify with `ls .claude/skills/` (as of 2026-07-05; some siblings may still be in-flight PRs).
- Build/venv commands quoted from README: re-verify with `sed -n '30,66p' README.md` (as of 2026-07-05).
