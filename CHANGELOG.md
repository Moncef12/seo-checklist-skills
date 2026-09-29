# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

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
  tests and the sample reports, plus `examples/sample-audit-report.md`, a full audit produced end-to-end by the skill.
- Offline unit and integration tests, a `claude plugin eval` suite (7 cases with and without the
  plugin, including a negative trigger case), CI on Python 3.9 to 3.13, and a release workflow
  that attaches one Claude.ai-ready zip per skill.
