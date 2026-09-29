# Fix two pages competing for one keyword

**Skill:** `seo-content`. Claude picks the owner URL, gives a check that decides between merging and changing focus, and delivers a redirect table with the content to keep.

## You

> Two of our pages keep swapping places for "invoice template": /templates (our main template gallery, 300 clicks/mo, avg pos 3) and /blog/invoice-template-guide (a 900-word post, 40 clicks/mo, avg pos 8.5). Sometimes neither shows on page 1. What should we do?

## Claude

**Pick one page to own "invoice template," and make that page `/templates`.** It already earns about 7x the clicks, and it matches what people searching that term want: a template they can use right away, not a guide about templates. The blog post should either merge into `/templates` or stop targeting that keyword. When Google can't tell which of two URLs is the answer, it swaps them back and forth, and sometimes drops both, which fits what you're seeing.

### Step 1: Check where the blog post's 40 clicks come from (about 10 minutes)

In Google Search Console, go to Performance, filter Page = `/blog/invoice-template-guide`, and open the Queries tab. What you find decides the next step:

- **Most clicks come from "invoice template" and close variants** ("free invoice template", "invoice template word"): the post isn't bringing in anything the gallery can't. **Merge it (Option A).**
- **Most clicks come from how-to questions** ("what to include on an invoice", "how to write an invoice", "invoice vs receipt"): the post has its own audience. **Change its focus (Option B).**

### Option A: Merge the post into /templates (my default choice)

| Old URL → Target URL | Reason | Content to keep |
|---|---|---|
| `/blog/invoice-template-guide` → `/templates` (or `/templates/invoice` if you have that page) | Both pages target the same search intent; the post ranks worse and gets 7x fewer clicks | A short "What to include on an invoice" checklist, 3–5 FAQs (for example: required fields, payment terms, numbering), and any unique examples or screenshots |

1. Add the useful parts of the post to `/templates`, below the templates themselves, so the templates stay first on the page.
2. Permanently redirect (301) the blog URL to `/templates`.
3. Update every internal link that points to the post.
4. Remove the post from the sitemap.

### Option B: Change the blog post's focus

- Rewrite the title and H1 around the how-to question it actually gets traffic for, e.g. *"What to Include on an Invoice (Checklist + Free Template)"*. Remove "invoice template" as the main phrase.
- Keep the URL. Changing it means adding a redirect for little gain.
- Near the top of the post, add a prominent link to `/templates` with the anchor text "invoice template".

### Do these in either case

- **Fix internal link text.** Search the site for links whose anchor text is "invoice template" (or similar) and point them all at `/templates`. Mixed signals from your own links are a common cause of this swapping.
- **Consider a dedicated page for invoice templates.** For a big head term like "invoice template", Google usually ranks pages about that one template type, often offering Word, Excel and PDF versions. A general gallery ranking #3 is doing well, but a `/templates/invoice` page might hold the position more reliably. If you have one or build one, it should be the page that owns the keyword instead of the gallery, and the steps above apply the same way.
- **Watch it for 4–6 weeks.** In Search Console, check query "invoice template" with the Pages tab. You want one URL getting nearly all the impressions and a steadier position. Expect some movement for 1–3 weeks after the redirect.

If you can export query+page data from Search Console (through the API, the Search Analytics for Sheets add-on, or Looker Studio), I can check the rest of your important keywords for the same problem.
---
<sub>Real, unedited output recorded on 2026-09-29 during the plugin's eval run (Claude Code, Opus 5.5, seo-checklist v1.0.0). "Acme Invoice" is a fictional demo company.</sub>
