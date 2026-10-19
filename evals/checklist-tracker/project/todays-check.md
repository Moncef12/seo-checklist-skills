# Technical SEO check: https://getpayly.example (2026-10-19)

**Summary:** ❌ 2 FAIL | ⚠️ 5 WARN | ℹ️ 7 INFO | ✅ 9 PASS

## Search engine setup
- ✅ **PASS** `analytics` GA4 tag found: G-8XK2PL4QZ1
- ✅ **PASS** `gsc-verification` Search Console Domain property verified by DNS (google-site-verification TXT record)
- ℹ️ **INFO** `bing-verification` No Bing Webmaster Tools verification visible

## Sample of 20 URLs
- ✅ **PASS** `canonical` Self-referencing canonical on all 20 sampled pages
- ⚠️ **WARN** `title` 1/20 sampled pages: /pricing title is 79 chars (target 50-60)
- ✅ **PASS** `meta-description` Every sampled page has its own description (120-158 chars)
- ⚠️ **WARN** `schema` /features/invoicing: BreadcrumbList is missing required itemListElement

## 404 handling
- ❌ **FAIL** `soft-404` Non-existent URLs return 200 (soft 404) - return a real 404 status

## Links & orphans
- ✅ **PASS** `broken-link` No broken internal links among 214 checked
- ⚠️ **WARN** `orphans` 1 sitemap URL was not linked from any crawled page: /orphan-landing
- ❌ **FAIL** `indexability` Sitemap lists a noindex page: /legacy

## Per-page issues
- ⚠️ **WARN** `img-alt` / : hero image has no alt attribute
