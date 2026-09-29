---
name: seo-quick-wins
description: Finds the fastest SEO gains in Google Search Console data - queries/pages with high impressions but low CTR (rewrite title and meta), titles cut off or rewritten in site:domain results, old pages stuck on page 2 (positions 11-20), "People also ask" questions to answer in FAQs, and pages losing traffic or rankings that need a refresh. Use when someone shares a GSC export or screenshot, asks for SEO quick wins or low-hanging fruit, asks why clicks or traffic dropped, wants to improve CTR, or asks what to update first on an existing site.
---

# SEO quick wins

Quick wins come from pages Google *already* shows. Improving something at position 12 or with a 0.8% CTR moves traffic in weeks, whereas a new page takes months. Everything here starts from Search Console data.

## Get the data

Ask for the export if you don't have it. It takes about 30 seconds:
1. Go to GSC > **Performance** > **Search results**.
2. Set the date to **Last 3 months**.
3. Click **Export > Download CSV**. The `.zip` contains `Queries.csv` and `Pages.csv`.
4. **For decliners:** click the Date filter > **Compare** > "Compare last 3 months to previous period", then export again.

If the user can only paste a screenshot or table, read the numbers from it and apply the same logic by hand.

## Run the analysis

From this skill's directory:
```bash
python3 scripts/gsc_analyze.py quick-wins ~/Downloads/example.com-Performance-on-Search-2026-09-29.zip
python3 scripts/gsc_analyze.py decliners  ~/Downloads/compare-export.zip
```
Options: `--min-impressions 50` for small sites (the default is 100), `--top 50`, `--json`. In compare exports the first date range is treated as current; pass `--swap` if the columns are reversed.

## The 5 quick wins

**Q1. High impressions, low CTR → rewrite the title and meta description.** The script flags rows whose CTR is under half the typical CTR for their position, sorted by estimated missed clicks. For each flagged page:
1. Look at the live SERP for its top query. What are competitors promising? Are SERP features (AI Overview, PAA, video) pushing it down? If a feature is taking the clicks, a rewrite helps less, so say so.
2. Write 2 title options (50-60 characters) and a meta description (120-160 characters) that match the query's wording, add a concrete hook (a number, the year, "free", an outcome), and line up with the H1.
3. Record the before-CTR so the owner can compare after 2-4 weeks.

**Q2. `site:yourdomain.com` on Google → fix titles that are cut off or miss the keyword.** Search `site:domain.com` (and `site:domain.com/blog`) with web search, or ask the owner for a screenshot. Look for titles ending in "…", titles Google rewrote (different from the `<title>`), boilerplate titles ("Home", "Untitled", duplicates), and titles missing the page's main keyword. Cross-check with `seo_check.py page` from the seo-on-page or seo-audit skill for exact lengths.

**Q3. Old pages on page 2 (positions 11-20) → update them first.** They already have relevance, so they need a push. Typical upgrades:
- Close the content gaps against the top 3 results: missing subtopics and PAA questions.
- Put the direct answer in the first two lines.
- Refresh stats, examples and the year.
- Add 3-5 internal links from strong pages with a descriptive anchor.
- Improve the title to match the query better.
- Update `dateModified` if the change is substantive.

**Q4. "People also ask" on your keywords → answer them in quick FAQ sections or pages.** Collect PAA questions for the top keywords with a SERP tool (DataForSEO `serp_organic_live_advanced` returns `people_also_ask` items) or web search, and merge them with the script's "Question queries" list. Answer each in 40-60 words directly under an H2/H3 phrased as the question, on the most relevant existing page. Create a standalone page only when the question has real volume and deserves depth. Note that FAQ rich results are now limited to authoritative government and health sites, so the benefit is snippets, PAA and AI answers, not the FAQ dropdown.

**Q5. Pages losing traffic → refresh them before they drop further.** For each decliner, diagnose before prescribing:
- **Position dropped?** Competitors improved or intent shifted. Refresh against the current top 3.
- **Position stable but clicks down?** It's CTR or a SERP feature (an AI Overview, new ads). Rework the title and meta, and target the feature.
- **Impressions down, position stable?** Demand fell (seasonality or trend). Check Google Trends before rewriting anything.
- **Site-wide drop?** It's technical or a core update. Hand off to seo-technical and check the Google Search Status Dashboard for update dates.

## Output

```markdown
# Quick wins: <domain> (<date range>)
## Top 5 actions this week
1. <page>: <action> - est. +<n> clicks/mo
## 1. Low-CTR rewrites
| Page / query | Impr. | CTR → target | Current title (chars) | New title (chars) | New meta (chars) |
## 2. site: title issues
## 3. Page-2 upgrades
| Page | Pos. | Impr. | What to add |
## 4. PAA / FAQ answers
| Question | Put on page | 40-60-word answer |
## 5. Decliners
| Page | Clicks now/before | Diagnosis | Refresh plan |
```

Missed-click estimates use rough CTR curves. Present them as directional, not as promises.
