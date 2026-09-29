---
name: seo-technical
description: Checks and fixes technical SEO - GSC/GA4 and Bing setup, XML sitemaps, indexing problems, robots.txt and noindex, canonical tags, Core Web Vitals, mobile-friendliness, JavaScript rendering/crawlability, broken links and redirect chains, URL structure, breadcrumbs, orphan pages and schema markup. Use when a site isn't being indexed, pages vanished from Google, someone asks about sitemaps, robots.txt, canonicals, redirects, CWV/PageSpeed, structured data or rich results, or wants a technical SEO review of a site or codebase (Next.js, Nuxt, Astro, WordPress, etc.).
---

# Technical SEO

Technical SEO decides whether Google can crawl, render and index the site at all. Nothing else on the checklist matters for a page that isn't indexed, so work in the order below: access first, then quality.

## Workflow

1. **Run the site check.** Paths are relative to this skill's directory. Python 3.9+, standard library only.
   ```bash
   python3 scripts/seo_check.py site https://example.com --sample 25 --crawl 80
   ```
   Raise `--crawl` (e.g. 500) when you need reliable orphan detection, because a partial crawl only produces orphan *candidates*. Add `--json` if you want to post-process the results. Use `--insecure` if TLS verification fails on this machine.
2. **Run page checks on each template** (home, category, article, product, landing) with Core Web Vitals:
   ```bash
   python3 scripts/seo_check.py page https://example.com/ https://example.com/blog/post --psi
   ```
   PSI works without a key but is rate-limited. Setting `PSI_API_KEY` raises the quota.
3. **Grade the 13 items below.** Use ✅ ⚠️ ❌ ❓. Mark ❓ when something is only visible inside GSC, GA4 or Bing, and ask for access or a screenshot instead of guessing.
4. **Fix.** If the codebase is available, implement the fixes using the framework patterns in `references/fixes.md`. Otherwise give exact instructions: the rule, the file, and the setting.

## The 13 technical items

| # | Item | What to check | Typical fix |
|---|---|---|---|
| T1 | GSC + GA4 | A Domain property verified by DNS TXT. GA4 tag present. The two are linked. | `references/fixes.md#search-console-ga4-bing` |
| T2 | Sitemap to GSC + Bing | Sitemap exists, is valid, lists only canonical 200 URLs, and appears in robots.txt | Generate it from the router or CMS. Submit it in GSC and Bing (Bing can import from GSC). |
| T3 | Indexing issues | The GSC Page indexing report. The `site` sample flags non-200, noindex or robots-blocked URLs in the sitemap. | Triage by reason, see the table below |
| T4 | robots.txt / noindex | No `Disallow: /`. JS/CSS aren't blocked. No leftover staging `noindex`. | Remove the rule. Remember that robots.txt blocks crawling, not indexing: use `noindex` to de-index. |
| T5 | Canonicals | One absolute self-canonical per indexable page. Parameter and duplicate variants point to the primary. | Framework metadata, `references/fixes.md#canonicals` |
| T6 | Core Web Vitals | p75 mobile: LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 | `references/fixes.md#core-web-vitals` |
| T7 | Mobile friendly | Viewport meta, responsive layout, 16 px+ text, tap targets | Add `<meta name="viewport" content="width=device-width, initial-scale=1">`. Fix overflow. |
| T8 | JS crawlability | The `js-rendering` warning. Content and `<a href>` links are present in the raw HTML. | SSR/SSG/prerender. Use real `<a href>` elements, not `onClick` navigation. |
| T9 | Broken links / redirects | No 4xx/5xx internal links. Single-hop 301/308s. Internal links point at final URLs. | Update the links at their source. Collapse chains. Use 301 for permanent moves. |
| T10 | Clean URLs | Lowercase, hyphens, short, descriptive. No session IDs or needless params. | Change only with 301s from the old URLs, since URL changes cost equity temporarily. |
| T11 | Breadcrumbs | Visible trail on inner pages plus `BreadcrumbList` JSON-LD | `references/fixes.md#breadcrumbs` |
| T12 | Orphan pages | Sitemap URLs that no crawled page links to | Link them from hubs, categories or related-post modules, or drop them from the sitemap if they're worthless. |
| T13 | Schema + Rich Results | Valid JSON-LD matching the visible content. Passes the Rich Results Test. | `references/fixes.md#structured-data` |

## Triage: common GSC "Page indexing" reasons

| Reason | Usually means | Action |
|---|---|---|
| Discovered - currently not indexed | Google knows the URL but hasn't crawled it: low priority, weak internal links, or crawl budget | Add internal links from strong pages and improve uniqueness. Don't just click "Request indexing". |
| Crawled - currently not indexed | Crawled and judged not worth indexing: thin, duplicate or low value | Improve or merge the content (see seo-content), or noindex it. |
| Duplicate without user-selected canonical / Google chose different canonical | Near-duplicates, or conflicting canonical signals | Align the canonical, internal links, sitemap and hreflang on one URL. |
| Excluded by 'noindex' tag | Intentional, or a leftover from staging | Check it's intentional. Remove it from the sitemap if it is. |
| Blocked by robots.txt | Disallowed path | Allow it if it should rank. If it must be de-indexed, allow the crawl and use noindex. |
| Soft 404 | Thin or empty page returning 200 | Return a real 404/410, or add real content. |
| Page with redirect / Not found (404) | Normally fine | Only act if important URLs are affected, or if the sitemap lists them. |

## Judgment notes

- **Don't let robots.txt fight noindex.** Google can't see a `noindex` on a page that robots.txt blocks, so the URL can stay indexed with no snippet.
- **Canonicals are hints, not directives.** When internal links, the sitemap and the canonical disagree, Google picks its own. Make every signal agree.
- **Cookie bounces.** If `site` reports a `cookie-redirect`, the page only renders after setting a cookie. Googlebot doesn't persist cookies, so check the page in URL Inspection.
- **Rich results change often.** Google restricted FAQ rich results to authoritative government and health sites and dropped HowTo results in 2023. Check the current Search Gallery before promising a specific rich result. Schema still helps Google (and AI answer engines) understand the page even without a visual enhancement.
- **Lab vs field CWV.** Lighthouse scores are lab data. Google ranks on CrUX field data (p75 real users). With no field data, optimize anyway, but don't present the lab score as a ranking factor.
