---
name: seo-content
description: Plans and fixes SEO content strategy - competitor keyword gaps, high-volume/low-difficulty keywords, keyword cannibalization, merging thin or overlapping pages, topic clusters and pillar pages, feature and use-case pages, comparison ("X vs Y") and alternatives pages, "best X" listicles, author bios and E-E-A-T, and dateModified on refreshes. Use when someone asks what content to write, wants keyword research or a content calendar, asks why two pages compete for the same keyword, wants to prune or consolidate a blog, or needs a comparison, alternatives, listicle, feature or use-case page planned or written.
---

# SEO content strategy

Content work answers two questions: **which pages should exist** (gaps), and **which pages shouldn't** (cannibalization and thin overlap). Most sites need both, and consolidation is often the faster win.

## Data sources, best first

1. **Keyword MCP, if connected.** DataForSEO tools such as `dataforseo_labs_google_ranked_keywords` (a competitor's keywords), `dataforseo_labs_google_domain_intersection` (shared keywords and gaps), `dataforseo_labs_google_keyword_ideas`/`related_keywords`, `dataforseo_labs_bulk_keyword_difficulty` and `dataforseo_labs_search_intent`. The equivalents in Ahrefs or Semrush MCPs work too.
2. **User exports.** Ahrefs/Semrush Content Gap or Organic Keywords CSVs, and GSC exports.
3. **GSC query+page data** for cannibalization (see below).
4. **No tools.** Use web search: SERP inspection, autocomplete, PAA and related searches. Be explicit that volumes are unknown and prioritize by intent and business fit.

Never invent search volumes or KD numbers. Label estimates as estimates.

## The 10 content items

**C1. Competitors' keywords.** Find 3-5 *search* competitors (the sites ranking for your keywords, which may differ from business competitors). Pull their ranking keywords and filter to the ones you don't rank for (a domain intersection or content gap). Group the results by topic, not keyword by keyword.

**C2. High-volume, low-KD keywords.** Prioritize with `priority ≈ volume × business value × winnability`. Winnability comes from KD relative to your site's authority: a new site should target KD < 20-30, a mid-authority site can go to 40+. Long-tail, specific queries convert better and rank sooner.

**C3. Keyword cannibalization.** This is when several of your URLs compete for one query, so neither ranks well. Detect it with:
```bash
python3 scripts/gsc_analyze.py cannibalization query_page.csv
```
This needs query+page rows from the GSC API, Search Analytics for Sheets, or Looker Studio, because the plain GSC UI export doesn't pair them. Without that data, search `site:domain.com "keyword"` for each money keyword. Fix it by choosing one owner URL per intent, then either merge (C4), differentiate the intent, or re-point internal links and anchors to the owner. Two pages that serve different intents for similar words (e.g. "CRM pricing" vs "best CRM") are not cannibalization.

**C4. Merge thin or overlapping pages.** Candidates are pages under ~300 words with no unique value, several posts on the same subtopic, and pages with impressions but near-zero clicks for months. The process:
1. Pick the strongest URL (most traffic or backlinks).
2. Fold the unique content in.
3. 301 the others to it.
4. Update internal links.
5. Drop the old URLs from the sitemap.

Deliver a table with these columns: `Old URL → Target URL | Reason | Content to keep`.

**C5. Topic clusters around pillars.** Each core topic gets a pillar page (the broad guide) with 5-20 cluster pages (specific subtopics). Every cluster page links to the pillar with a descriptive anchor, and the pillar links to every cluster page. Deliver it as a map: pillar → cluster pages (existing ✓ / to write ✗), each with its target keyword.

**C6. Pages for each feature and use case.** Create one indexable landing page per feature ("invoice reminders"), per use case or job ("invoicing for photographers"), and per audience or industry, but only where there's real search demand or sales value. Don't spin up near-duplicate city or industry pages: that's thin, doorway-style content.

**C7. Comparison and alternatives pages.** "[You] vs [Competitor]" and "[Competitor] alternatives" pages capture buyers who are ready to switch. They must be accurate and fair: current pricing, the competitor's genuine strengths, and who should pick them instead. Inaccurate claims about competitors create legal risk and destroy trust. Date the pricing ("as of Sep 2026") and cite sources.

**C8. The best listicles in your category.** Publish "Best [category] tools for [audience] (Year)" pages. Include yourself honestly, not always at #1 without justification, along with real alternatives, a clear methodology ("we tested X for 2 weeks"), and a comparison table. Getting into *other* sites' lists is covered by seo-links.

**C9. Author bio and E-E-A-T.**
- **Experience:** show first-hand use (screenshots, original data, "we tried").
- **Expertise:** add a named author with a bio, credentials and a link to their profile.
- **Authoritativeness:** show citations, mentions and an about page.
- **Trust:** include contact info, sources, editorial policy and accurate dates.

Mark up authors with `Person` (name, url, sameAs) inside `Article.author`. E-E-A-T matters most for YMYL topics (money, health, legal).

**C10. Update dateModified on refresh.** When content changes substantively (new data, sections or corrections), update both the visible "Updated <date>" and `dateModified` in the schema and the sitemap `<lastmod>`. Don't bump dates without real changes: Google treats fake freshness as a manipulation signal, and it erodes trust.

## Deliverables

Pick what the request needs:
- **Content plan / calendar** (`references/templates.md#content-plan`): a table of keyword, volume, KD, intent, page type, new or existing URL, cluster, and priority.
- **Consolidation plan:** a redirect table and merge notes.
- **Cluster map:** pillar → spokes, with link requirements.
- **Page briefs or full drafts** for comparison, alternatives, listicle, feature or use-case pages, using the outlines in `references/templates.md`.

When writing drafts, apply the seo-on-page rules too: intent match, a 50-60 character title, the answer in the first two lines, and a clean heading outline.
