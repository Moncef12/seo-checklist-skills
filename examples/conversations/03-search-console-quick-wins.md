# Find quick wins in a Search Console export

**Skill:** `seo-quick-wins`. Claude ranks what to fix first by estimated missed clicks. It won't guess at "pages losing traffic" from a single-period export; instead it explains exactly which export to download.

> [!NOTE]
> This run happened in a sandbox that blocked the analysis script, so the skill used its fallback: it read the CSVs directly and applied the same thresholds by hand.

## You

> I exported my Search Console performance data (last 3 months) - Queries.csv and Pages.csv are in the gsc-data folder in your additional working directories. What should I fix first to get more traffic? Also I want to know which pages are losing traffic.

## Claude

I checked both CSVs by hand. The analysis script couldn't run because the sandbox blocks shell access to the `gsc-data` folder, but the Read tool could open the files and there are only 9 rows, so I applied the same rules manually. The estimates below are rough and based on typical click rates for each position. The export covers 3 months, so I've divided by 3 to get monthly figures.

### Which pages are losing traffic: this export can't tell you

`Queries.csv` and `Pages.csv` cover a single period and include no earlier numbers to compare against, so nothing in them shows a decline. To find which pages are losing traffic:

1. Go to GSC > **Performance** > **Search results**.
2. Click **Date** > **Compare** > "Compare last 3 months to previous period" > **Apply**.
3. Click **Export > Download CSV** and put the new files in `gsc-data`.

With that export I can split any decline into three causes: a lower ranking, a stable ranking with fewer clicks per view, or fewer searches overall (e.g. seasonal). Each one needs a different fix.

### What to fix first

| # | Page / query | The problem | Action | Est. gain |
|---|---|---|---|---|
| 1 | **Homepage** `/` | 20,000 views in Google results (impressions) at position 3.1, but only **2.5%** of viewers click. About 10% is typical at that position | Rewrite the title and meta description | **~+500 clicks/mo** |
| 2 | Query **"invoice software"** | 12,000 impressions at position 4.2, but only **0.33%** click. About 7.5% is typical | Same fix, and it's probably the same page (see below) | ~+290 clicks/mo (likely overlaps with #1) |
| 3 | `/blog/write-invoice` + **"how to write an invoice"** | Stuck on page 2 (position 13) with 5,000–6,000 impressions and about 10 clicks/mo | Update the content to push it onto page 1 | ~+100 clicks/mo if it reaches the top 5 |
| 4 | **"what is a pro forma invoice"** | Position 16.8, 800 impressions | Add a short answer section | Small, but easy |

**1–2. Homepage and "invoice software".** Your two biggest opportunities are almost certainly the same problem. The exports aren't linked, so I can't confirm that "invoice software" lands on the homepage, but it's very likely. A 0.33% click rate at position 4 is extremely low. Before rewriting, search "invoice software" on Google yourself:
- If the results are mostly ads and "best invoice software" lists, the searchers want comparisons. A title rewrite will help only a little, and a comparison-style page would help more.
- If the results are normal product pages, the title is the problem. Here are two options:
  - `Invoice Software That Gets You Paid Faster | Payly` (50 characters)
  - `Payly: Invoice Software for Small Businesses & Freelancers` (58 characters)
  - Meta description (139 characters): `Create, send and track professional invoices in minutes. Payly automates reminders and online payments so you get paid faster. Try it free.`
  - Only keep "free" if you actually have a free plan or trial. Write down today's rates (2.5% and 0.33%) so you can compare after 2–4 weeks.

**3. `/blog/write-invoice`.** Google already sees this page as relevant, so it needs improving rather than replacing:
- Put a direct answer in the first two lines: what goes on an invoice, in order.
- Look at the top 3 Google results and add any subtopics they cover that you don't, such as required fields, numbering, payment terms and examples.
- Add links to it from `/templates`. That's your strongest page with 900 clicks and a healthy 9% click rate, and "how to write an invoice" pairs naturally with "free invoice template".
- New title: `How to Write an Invoice: Step-by-Step Guide + Free Template` (59 characters).
- Update the "last updated" date once the changes are real.

**4. "what is a pro forma invoice".** Add a section headed with that question to the write-invoice guide or the templates page, with a 40–60 word answer right under it. Give it its own page only if the number of views grows.

### Already working, so leave these alone
- **"free invoice template"** and `/templates`: position 2.1 with a 9% click rate.
- **"invoice app for freelancers"**: 8% at position 3.5, above typical.
- **"payly login"**: 75% of people searching your brand name click through, as expected.

One more check you can do yourself: search `site:example.com` on Google and see whether any titles are cut off with "…" or differ from what you wrote. I couldn't see your live titles or search results from here.

**Bottom line:** fix the homepage title and meta description this week, then update the write-invoice guide. And send me the comparison export so I can tell you which pages are losing traffic.
---
<sub>Real, unedited output recorded on 2026-09-29 during the plugin's eval run (Claude Code, Opus 5.5, seo-checklist v1.0.0). "Acme Invoice" is a fictional demo company.</sub>
