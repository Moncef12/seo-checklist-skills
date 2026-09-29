---
name: seo-audit
description: Runs a full SEO audit of a website against a 40-point checklist (technical, on-page, content, quick wins, links) and turns it into a prioritized action plan. Use whenever someone wants their site's SEO checked or improved as a whole - "audit my SEO", "SEO health check", "why am I not ranking", "what should I fix for Google", "get this site SEO-ready before launch", "run the SEO checklist on example.com" - even if they don't say "audit". For one area only, the sibling skills seo-technical, seo-on-page, seo-content, seo-quick-wins and seo-links go deeper.
---

# SEO audit

Audit a site against the checklist in `references/checklist.md` and deliver a short, prioritized plan the owner can act on this week. The value is not a wall of findings; it is knowing which five things to do first and exactly how.

## 1. Gather inputs (ask once, don't block)

Ask for anything missing in a single message, then start with whatever you have:

- **Site URL** (required) and the 2-5 pages that matter most (pricing, main product, top blog post).
- **Google Search Console export** (optional, unlocks quick wins): Performance > Search results > last 3 months > Export > Download CSV. The `.zip` works as-is.
- **Target keywords / competitors** (optional). If a keyword-data MCP is connected (DataForSEO, Ahrefs, Semrush...), use it instead of asking.
- **Local business?** (decides whether Google Business Profile applies).
- **Codebase access?** If the site's repo is open in this session, you can fix issues directly instead of just reporting them.

## 2. Collect evidence

Run the bundled checkers (Python 3.9+, standard library only). Paths are relative to this skill's directory.

```bash
python3 scripts/seo_check.py site https://example.com --sample 20 --crawl 60
python3 scripts/seo_check.py page https://example.com/ https://example.com/pricing --psi
python3 scripts/gsc_analyze.py quick-wins ~/Downloads/example.com-Performance.zip   # if provided
```

- `site` covers hosts/HTTPS, robots.txt, sitemaps, indexability of a URL sample, soft 404s, broken links, internal redirects and orphan candidates.
- `page --psi` covers titles, meta, headings, intro, images, schema, canonical, viewport, JS-rendering risk and Core Web Vitals.
- If a fetch fails with a certificate error, rerun with `--insecure`. If the site blocks the script, fall back to WebFetch and your own reading of the HTML.
- For local files (a static export or build output), pass the `.html` paths to `page`. There's no `site` mode for files, so check links between pages, orphans, noindex and duplicates yourself by reading them.
- **If the scripts can't run at all** (no shell, sandbox, no network), keep going. Read the HTML with Read or WebFetch and apply the same checks by hand: title and meta lengths, H1 count and heading order, canonical, robots meta, viewport, alt attributes, JSON-LD, internal links. Scripts make the audit faster and more precise, but they aren't a prerequisite.
- For the search-intent and competitor items, look at the live SERP. Use a SERP tool if connected (e.g. `serp_organic_live_advanced`), otherwise web search.

## 3. Grade every checklist item

Go through all 40 items in `references/checklist.md` and give each one a status:

| Status | Meaning |
|---|---|
| ✅ Pass | Verified with evidence |
| ⚠️ Needs work | Partly done or minor issues |
| ❌ Fail | Verified problem |
| ❓ Unknown | Can't be verified from here. Say what data would settle it |

Be strict about ❓. Things like GSC setup, Bing submission, backlink profile or GBP status often can't be seen from outside. Guessing "pass" hides real problems, and guessing "fail" sends the owner chasing ghosts. Say what you need instead, for example "share a GSC export" or "tell me whether GA4 is installed".

## 4. Prioritize

Score each non-passing item by **impact** (how much traffic or indexing it affects) against **effort**, then order it roughly like this:

1. **Blockers.** Anything stopping pages from being crawled or indexed: robots/noindex mistakes, 5xx or 4xx errors on key pages, a missing sitemap, duplicate hosts, client-side-only content.
2. **Quick wins.** Low effort with measurable upside: low-CTR titles, page-2 pages, decliners.
3. **On-page fixes** on the pages that already get impressions.
4. **Content gaps and consolidation.**
5. **Links and authority.**

A site with 3 pages and no traffic needs different priorities from a 5,000-page site losing traffic. Adjust the order to what you actually find.

## 5. Report

Use `references/report-template.md`. Keep the executive summary to five bullets. Give every recommendation a concrete "do this", such as the rewritten title with its character count or the exact redirect rule, not "optimize titles".

## 6. Fix (when you have the codebase)

Offer to implement the top fixes. Detect the stack first (Next.js metadata API, Nuxt `useSeoMeta`, Astro, WordPress, plain HTML), then follow the stack-specific patterns in the seo-technical skill's `references/fixes.md`. Change titles and meta through the framework's own mechanism instead of hard-coding tags into templates.

## Going deeper

Each area has its own skill with detailed how-tos. Load the one you need when a section needs more than a line of advice:

- **seo-technical**: GSC/GA4 setup, sitemaps, indexing, canonicals, CWV, rendering, schema.
- **seo-on-page**: intent, titles, meta, headings, intros, images, internal links.
- **seo-content**: competitor keywords, low-KD targets, cannibalization, clusters, comparison and listicle pages, E-E-A-T.
- **seo-quick-wins**: GSC-driven CTR, page-2, PAA and decliner fixes.
- **seo-links**: brand mentions, backlink gap, "best X" lists, Reddit, Google Business Profile.

If a sibling skill isn't installed, `references/checklist.md` has enough on each item to proceed.
