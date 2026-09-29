# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-09-29

### Added
- `/seo` command router (Claude Code). Running `/seo` shows the menu, `/seo <url>` runs a full audit,
  and 15 modes (`audit`, `technical`, `page`, `rewrite`, `gsc`, `decliners`, `content`, `cannibal`,
  `compare`, `links`, `local`, `schema`, `cwv`, `fix`, `ci`) dispatch to the six skills. It's
  explicit-only (`disable-model-invocation`), so plain-language requests still auto-load the right skill.
- `tests/test_router.py` keeps the menu, routing table, `argument-hint` and skill names consistent.

### Changed
- The README Usage section now starts with the `/seo` command reference.
- Claude.ai zips exclude the router, since slash commands are a Claude Code feature.

## [1.0.1] - 2026-09-29

### Changed
- The README now leads with how you actually use the skills: plain-language requests to Claude, the
  skill that loads, and what comes back. The script reference moved into a collapsed developer section.
- Added `examples/conversations/`, six unedited transcripts of real sessions (full audit, on-page
  rewrite, Search Console quick wins, cannibalization, de-indexing, link building).
- Raw checker outputs moved to `examples/under-the-hood/`.

## [1.0.0] - 2026-09-29

### Added
- Six skills covering the 40-point SEO checklist: `seo-audit`, `seo-technical`, `seo-on-page`,
  `seo-content`, `seo-quick-wins`, `seo-links`, packaged as a Claude Code plugin marketplace.
- `seo_check.py` (standard library only):
  - `site` checks host/HTTPS consolidation, robots.txt, sitemap indexes (including gzip), indexability
    sampling, soft 404s, broken links, redirect chains, cookie-bounce redirects and orphan pages.
  - `page` checks titles, meta descriptions, headings, the intro after the H1, images, links, JSON-LD,
    canonical tags, the viewport tag, JS-rendering risk, and Core Web Vitals via PageSpeed Insights.
  - The crawler obeys robots.txt. `--delay` throttles requests, and `--fail-on FAIL|WARN` sets the
    exit code for CI gating.
- `gsc_analyze.py` finds low-CTR queries and pages, page-2 rankings, question queries, decliners
  (from compare exports) and keyword cannibalization. It reads GSC zip exports directly and parses
  localized exports (EN/FR/DE/ES/PT/IT/NL number formats and column names).
- `lengths.py` gives exact character counts and pixel-width estimates for rewrites. Models miscount; the skills verify with it.
- Fallback instructions so every skill still works when scripts can't run (Claude.ai without code
  execution, sandboxed paths, pasted data).
- `examples/demo_site.py`, a fictional site with 10 planted SEO issues, used by the integration
  tests and the sample reports.
- Offline unit and integration tests, a `claude plugin eval` suite (7 cases with and without the
  plugin, including a negative trigger case), CI on Python 3.9 to 3.13, and a release workflow
  that attaches one Claude.ai-ready zip per skill.
