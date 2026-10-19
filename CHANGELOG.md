# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-10-19

### Added
- **Search engine setup (T1, T2).** `site` reads the analytics and verification footprints: GA4 and Tag
  Manager tags (also inside the site's own JavaScript bundles, where Next.js and similar apps load them),
  legacy Universal Analytics, Google consent mode, a Search Console Domain property verified by DNS (TXT
  record over DNS-over-HTTPS, `--no-dns` to skip), the verification meta tags and Bing's BingSiteAuth.xml.
- **Duplicate content (C4).** `site` compares the main text of every crawled page (nav and footer ignored):
  near-duplicate groups scored by the share of words that match in order, which also catches templated
  doorway pages where only a city name changes; paragraphs pasted on several pages, warned only when they're
  a large part of those pages; thin pages by their own word count. Pages already consolidated with
  rel=canonical are left out. `page` runs the same comparison across several files (static builds).
- **Title check (Q2).** `gsc_analyze.py titles` pairs each page with its top Search Console query, reads the
  live title (or a static build with `--html-dir`) and flags titles that miss the query, only partly contain
  it, push it past the ~600 px cut-off, or get cut off themselves.
- **Schema rules (T13).** Required and recommended properties per type (Product, Offer, AggregateRating,
  BreadcrumbList items, FAQPage, LocalBusiness and its subtypes, Event, VideoObject, Recipe, JobPosting,
  SoftwareApplication, Article family), ISO 8601 dates, relative URLs, missing @context, and the retired
  HowTo, FAQ and sitelinks search box features.
- **Image weight (O6).** `page` measures each image's file size (HEAD or a 1-byte range request, or the file
  size in a local build) and flags images over 200 KB and a lazy-loaded first image.
- **Progress tracker.** `checklist.py` and the `/seo checklist` mode keep a living `SEO-CHECKLIST.md` in the
  project: the 40 items by section, progress, what improved or regressed since the last run, and boxes ticked
  by hand are kept.
- **HTML report.** `--html report.html` writes a styled, self-contained report (dark and light themes, all
  site content escaped). `--color` gives colored badges in a terminal, `--counts` writes finding counts.
- **GitHub Action.** `uses: Moncef12/seo-checklist-skills@v1.2.0` runs the check in CI, writes the job
  summary, uploads the reports and fails the job at the level you choose.
- New `/seo` modes: `titles`, `dupes`, `report`, `checklist`.
- 5 behavioral eval cases built so plain Claude is likely to miss what the scripts catch: titles cut off by
  pixel width at 56 characters, a city-swap doorway pair among 22 pages, an existing canonical to respect,
  schema that is valid JSON but not eligible, setup footprints, and the tracker update.

### Fixed
- The crawler could leave the site when an internal URL redirected to another domain, then crawl that
  domain's links. It now stays on the site and reports the off-site redirect.
- Connection errors are reported in plain words ("no HTTPS on this host", "DNS name doesn't resolve").

### Changed
- Every skill that runs scripts now gets all shared modules (`make sync`), and `check-sync` also catches
  stale copies.

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
