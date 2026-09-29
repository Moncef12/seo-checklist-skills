---
name: seo-links
description: Builds backlinks and off-site visibility the sustainable way - turning unlinked brand mentions into links, backlink gap analysis (who links to competitors but not you), getting into other sites' "best X" lists, showing up in Reddit threads that rank on Google, and setting up/optimizing a Google Business Profile for local businesses. Use when someone asks how to get backlinks, improve domain authority, do link building or outreach, find link opportunities, get listed in roundups, use Reddit for SEO, or rank on Google Maps/local pack.
---

# Links and off-site SEO

Links and mentions are how Google, and increasingly AI answer engines, decide who to trust. The tactics below earn them. Buying links, PBNs, link exchanges at scale and Reddit astroturfing all break Google's spam policies or community rules and can sink a site, so steer requests like that toward these tactics instead.

## The 5 link items

**L1. Turn brand mentions into backlinks.** Sites that already mention you are the warmest outreach targets there are.
1. Find mentions: web search `"Brand Name" -site:brand.com` (plus the product name and founder name), Google Alerts, or a mentions tool (Ahrefs Content Explorer, Brand24, Mention).
2. Check each page for an existing link to you. Keep the ones without a link on indexable pages.
3. Send a short, friendly email to the author asking to link the mention (template in `references/outreach.md`). Point to the most useful URL, not always the homepage.

Also reclaim broken links. Look for backlinks pointing to your 404 URLs (the GSC Links report, or a backlink tool's "broken backlinks") and 301 those URLs to the closest live page.

**L2. Backlink gap: who links to competitors.** A backlink tool is required: Ahrefs Link Intersect, Semrush Backlink Gap, Moz Link Explorer, or DataForSEO Backlinks API if connected. Without one, mark this ❓ and ask for an export.
1. Enter 3-5 competitors and find the domains linking to **2 or more of them** but not to you. Those sites link to the category, not to a single company.
2. Classify the opportunities: directories and review sites (G2, Capterra, niche directories), resource pages, listicles (L3), guest-post venues, podcasts, integration and partner pages, and news or data coverage.
3. Prioritize by relevance first, then authority. Skip spammy domains even when their metrics look good.

**L3. Get into other sites' "best X" lists.** Search "best [category]", "top [category] tools", "[category] for [audience]" and "[competitor] alternatives". Every page ranking in the top 20 that doesn't list you is a target.
- Pitch the author with something that makes the update easy: a one-paragraph description in their format, a screenshot, a free account or trial, and a unique angle ("the only one with X").
- Keep a tracker with these columns: URL, rank, author, contacted, follow-up, status.
- Paid placement is common on these lists. If a site charges, the link should be `rel="sponsored"` to comply with Google's policies, so value it for referral traffic, not SEO.

**L4. Show up in Reddit threads that rank.** Reddit threads often rank on page 1 and get cited by AI answers.
1. Find threads that rank: search `site:reddit.com [keyword]` and note which appear in the normal SERP for your money keywords.
2. Take part genuinely: answer the actual question, disclose your affiliation ("I work on X"), mention your product only when it truly fits, and follow each subreddit's self-promotion rules.
3. Build real account history. A brand-new account posting links gets removed and hurts the brand.

Never use fake accounts, vote manipulation or undisclosed shilling. Reddit bans it, communities notice, and it becomes a reputational problem that ranks too.

**L5. Google Business Profile (local businesses only).** Skip this item and mark it N/A for online-only businesses. For businesses with a location or service area:
1. Claim and verify at business.google.com. Pick the primary category carefully, because it's the biggest local ranking factor, then add relevant secondary categories.
2. Keep NAP (name, address, phone) identical to the website footer and major directories (Apple Business Connect, Bing Places, Yelp, industry directories).
3. Fill in everything: hours (and holiday hours), services or products, description, photos (real, recent, regular), and attributes.
4. Reviews: ask every happy customer with a direct review link, and reply to all reviews, especially negative ones, calmly and helpfully. Never buy reviews or gate them.
5. Post updates or offers periodically, answer Q&A, and add `LocalBusiness` schema to the site (see seo-technical `references/fixes.md#structured-data`).

## Deliverable

```markdown
# Link plan: <domain>
## Top opportunities
| # | Opportunity | Type | Why | Next step |
## Unlinked mentions (L1)
| Page | Mentions | Contact | Suggested link target | Status |
## Backlink gap (L2)
| Domain | Links to (competitors) | Type | Priority |
## "Best X" lists to pitch (L3)
| Query | Page | Rank | Includes competitors | Pitch angle |
## Reddit threads (L4)
| Thread | Ranks for | Rank | Helpful contribution to make |
## Google Business Profile (L5)
Checklist status, or N/A
```

Outreach email templates are in `references/outreach.md`. Personalize every email with a specific detail from the target page. Mass templated outreach gets ignored.
