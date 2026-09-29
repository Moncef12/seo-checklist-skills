# The 40-point SEO checklist

Each item gives what "done" looks like, how to verify it, and which skill goes deeper.
`site` = `scripts/seo_check.py site`, `page` = `scripts/seo_check.py page`, `gsc` = `scripts/gsc_analyze.py`.

## Contents
- [Technical (13)](#technical)
- [Quick wins (5)](#quick-wins)
- [On-page (7)](#on-page)
- [Content (10)](#content)
- [Links (5)](#links)

---

## Technical
Deep dive: **seo-technical**

| # | Item | Done when | Verify |
|---|---|---|---|
| T1 | Set up GSC and GA4 | A GSC Domain property is verified by DNS. GA4 is collecting data. The two are linked. | Ask the owner or check for a `gtag`/GTM snippet in the HTML. GSC can't be seen from outside, so mark ❓ unless confirmed. |
| T2 | Submit sitemap to GSC and Bing | An XML sitemap exists, is listed in robots.txt, and has been submitted in both GSC and Bing Webmaster Tools. | `site` checks existence and the robots line. Submission is ❓ unless confirmed. |
| T3 | Fix indexing issues | Important pages are indexed. The GSC "Page indexing" report has no unexpected exclusions. | GSC export or screenshot. `site` flags non-200, noindex and blocked URLs in the sitemap. `site:domain.com` gives a rough count. |
| T4 | Check robots.txt and noindex tags | robots.txt doesn't block important paths or JS/CSS. No accidental `noindex` or `X-Robots-Tag`. | `site` (robots section and sample), `page` (noindex finding) |
| T5 | Add canonical tags | Every indexable page has exactly one absolute, self-referencing canonical. Duplicates point to the primary. | `page`, `site` sample |
| T6 | Fix Core Web Vitals | LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at p75 on mobile. | `page --psi` on each key template, or the GSC Core Web Vitals report |
| T7 | Make the site mobile friendly | Meta viewport is present, the layout is responsive, tap targets are usable and there is no horizontal scroll. | `page` (viewport). Look at the page at a 375 px width if a browser is available. |
| T8 | Check JS content is crawlable | Primary content and links are in the server HTML, via SSR/SSG, not only after hydration. | `page` `js-rendering` warning. Compare the raw HTML word count to the rendered page. Use GSC URL Inspection > View crawled page. |
| T9 | Fix broken links, 404s, redirect chains | No internal links go to 4xx/5xx. Redirects are single-hop 301/308. Internal links point at final URLs. | `site` (links section, hosts section) |
| T10 | Use clean, descriptive URLs | URLs are lowercase, hyphenated and readable. There are no session or tracking params and no opaque IDs. | `page`/`site` `url` findings |
| T11 | Add breadcrumbs | Inner pages show a visible breadcrumb trail backed by `BreadcrumbList` schema. | `page` `breadcrumbs` finding |
| T12 | Fix orphan pages | Every indexable page gets at least one internal link from a crawlable page. | `site --crawl 500` or higher for full coverage. Compare the sitemap against the crawl. |
| T13 | Add schema, test in Rich Results | Relevant JSON-LD (Organization, Article, Product, BreadcrumbList...) is valid in the Rich Results Test. | `page` (schema types, invalid JSON). Then run https://search.google.com/test/rich-results |

## Quick wins
Deep dive: **seo-quick-wins**. These mostly need GSC data.

| # | Item | Done when | Verify |
|---|---|---|---|
| Q1 | High impressions, low CTR in GSC | Rows with CTR well below the norm for their position have a rewritten title and meta description. | `gsc quick-wins` > "High impressions, low CTR" |
| Q2 | Search `site:yourdomain.com` on Google | The titles shown in results aren't cut off or rewritten by Google, and they contain the target keyword. | Run the search (web search tool or the owner) and compare it with the `page` title lengths. |
| Q3 | Old pages ranking on page 2 | Pages at positions 11-20 have been refreshed and strengthened first. | `gsc quick-wins` > "Page 2" |
| Q4 | "People also ask" on your keywords | PAA questions for your main keywords are answered in quick FAQ sections or pages. | SERP tool PAA items, plus the "Question queries" list from `gsc quick-wins` |
| Q5 | Pages losing traffic or rankings | Decliners are refreshed before they drop further. | `gsc decliners` on a compare-mode export |

## On-page
Deep dive: **seo-on-page**

| # | Item | Done when | Verify |
|---|---|---|---|
| O1 | Match every page to search intent | The page format (guide, list, tool, product, comparison) matches what ranks for its keyword. | Look at the top 10 on the SERP for the page's main keyword. |
| O2 | Titles 50-60 characters | The title is unique, puts the keyword first, reads naturally, and is 50-60 characters (about 600 px). | `page` `title` finding, plus duplicates in the `site` sample |
| O3 | Unique meta descriptions | Each page has its own description of about 120-160 characters with the keyword and a reason to click. | `page`, `site` duplicates |
| O4 | Fix heading structure | There is one H1 matching the topic, and H2/H3 follow a logical outline with no skipped levels. | `page` h1, heading-order and outline |
| O5 | Answer the query in the first 2 lines | The text right after the H1 directly answers the main query. | `page` "Intro after H1". Judge it against the keyword. |
| O6 | Optimize images, add alt text | Images are compressed WebP/AVIF, have width and height set, lazy-load below the fold, and have descriptive alt text. | `page` img-* findings |
| O7 | Internal links to important pages | Money pages and pillars get contextual links with descriptive anchors from relevant, strong pages. | `page` internal-link count and anchors. Use GSC Links > Top linked pages. |

## Content
Deep dive: **seo-content**

| # | Item | Done when | Verify |
|---|---|---|---|
| C1 | Find your competitors' keywords | There is a list of keywords that competitors rank for and you don't. | Keyword MCP (ranked keywords / domain intersection) or an Ahrefs/Semrush export |
| C2 | Find high-volume, low-KD keywords | The content plan targets winnable keywords, not just the biggest ones. | Keyword MCP (volume + KD) or a tool export |
| C3 | Fix keyword cannibalization | Each query has one clear owner URL. | `gsc cannibalization` on query+page data, or `site:domain.com keyword` |
| C4 | Merge thin or overlapping pages | Thin or duplicate pages are merged, and the old URLs 301 to the survivor. | `page` word counts, cannibalization output, GSC pages with impressions but no clicks |
| C5 | Topic clusters around pillar pages | Each core topic has a pillar page, and its supporting pages link to it and to each other. | Map the URLs by topic and check the internal links. |
| C6 | Pages for each feature and use case | Every feature and every use case or audience has its own landing page. | Compare the product's features with the sitemap. |
| C7 | Comparison and alternatives pages | Fair "X vs Y" and "X alternatives" pages exist for the main competitors. | Sitemap/URL search, SERP for "[competitor] alternatives" |
| C8 | The best listicles in your category | You publish "best [category]" roundups (and appear in other people's, see L3). | SERP for "best [category]" |
| C9 | Author bio and E-E-A-T signals | Articles show a real author with credentials, an about page, sources, and Person/Organization schema. | Read a blog post. `page` schema types. |
| C10 | Update dateModified on refresh | Substantive updates change both the visible "Updated" date and `dateModified` in schema. | `page` "dateModified: yes/no" |

## Links
Deep dive: **seo-links**

| # | Item | Done when | Verify |
|---|---|---|---|
| L1 | Turn brand mentions into backlinks | Unlinked mentions have been found and their authors asked to add a link. | Web search `"Brand" -site:brand.com`, alerts, or a mentions tool |
| L2 | Backlink gap | There is a list of domains linking to 2+ competitors but not to you, with an outreach plan. | Backlink tool (Ahrefs Link Intersect, Semrush Backlink Gap, Moz, DataForSEO Backlinks). Otherwise ❓. |
| L3 | Get into other sites' "best X" lists | Listicles ranking for "best [category]" have been pitched. | SERP for "best [category]" and "top [category] tools" |
| L4 | Show up in Reddit threads that rank | Reddit threads ranking on Google for your keywords are identified, and you take part genuinely and with disclosure. | SERP for `site:reddit.com [keyword]`, or Reddit results in the main SERP |
| L5 | Google Business Profile (local businesses) | The profile is claimed and verified with the right categories, consistent NAP, photos, reviews and replies. | Local businesses only, otherwise N/A. Search the brand on Maps. |
