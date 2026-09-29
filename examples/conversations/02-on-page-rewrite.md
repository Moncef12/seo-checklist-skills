# Rewrite a page for a target keyword

**Skill:** `seo-on-page`. Claude grades the 7 on-page items, writes two rewrite options for each element with character counts verified by `lengths.py`, and hands back paste-ready HTML.

## You

> Can you make this page rank better for "invoice software for freelancers"? Here's the head and top of the body: ```html <title>Home</title> <meta name="description" content="Welcome to Acme Invoice"> <body> <h2>Welcome to Acme Invoice</h2> <p>In today's fast-paced world, many freelancers struggle with getting paid on time.</p> <img src="/hero.png"> ```

## Claude

### Homepage: target "invoice software for freelancers" (commercial/transactional intent)

I couldn't check the live search results because I have no search tool in this session. Queries like this usually show a mix of product homepages and "best invoicing apps" lists. A product homepage can rank for it, but you may also want a separate comparison page later.

| Item | Status | Finding | Do |
|---|---|---|---|
| O1 Intent | ⚠️ | A product page fits the query, but nothing on the page says what the product is | State "invoice software for freelancers" in the title, H1 and first line |
| O2 Title | ❌ | "Home" (4 chars): no keyword and no reason to click | Use one of the rewrites below (50–60 chars) |
| O3 Meta | ❌ | "Welcome to Acme Invoice" (23 chars): no keyword, no benefit | Use a rewrite below (120–160 chars) |
| O4 Headings | ❌ | There's no H1; the page opens with an H2 | Change it to a single `<h1>` that contains the keyword, and use H2s for sections below it |
| O5 First 2 lines | ❌ | "In today's fast-paced world…" is filler | Open with what the product is and who it's for |
| O6 Image | ❌ | `/hero.png` has no alt text, no width/height, a generic filename and uses PNG | See the fix below |
| O7 Internal links | ❓ | Not visible in this snippet | Link to the features, pricing and templates pages with descriptive anchor text |

#### Rewrites (character counts checked with the script)

| | Current (chars) | Option A (chars) | Option B (chars) |
|---|---|---|---|
| Title | Home (4) | Invoice Software for Freelancers: Get Paid Faster \| Acme (56) | Invoice Software for Freelancers - Get Paid on Time \| Acme (58) |
| Meta description | Welcome to Acme Invoice (23) | Acme Invoice is invoice software for freelancers. Send professional invoices in minutes, automate payment reminders and get paid on time. Try it free. (150) | Simple invoice software for freelancers: create branded invoices, accept card and bank payments, and chase late clients automatically. Start free today. (152) |
| H1 | Welcome to Acme Invoice (h2) | Invoice Software for Freelancers Who Want to Get Paid on Time | Simple Invoice Software for Freelancers |
| First 2 lines | In today's fast-paced world, many freelancers struggle… | Acme Invoice is invoice software built for freelancers. Send a professional invoice in under a minute, accept online payments, and let automatic reminders chase late clients for you. | |

**Check the claims before you publish.** "Try it free", card/bank payments, automatic reminders and "under a minute" are placeholders I made up. Keep only the ones that are true, and replace them with real proof where you have it, such as "Used by 12,000 freelancers" or "average payment in 9 days".

#### Paste-ready HTML

```html
<title>Invoice Software for Freelancers: Get Paid Faster | Acme</title>
<meta name="description" content="Acme Invoice is invoice software for freelancers. Send professional invoices in minutes, automate payment reminders and get paid on time. Try it free.">
<body>
<h1>Invoice Software for Freelancers Who Want to Get Paid on Time</h1>
<p>Acme Invoice is invoice software built for freelancers. Send a professional invoice in under a minute, accept online payments, and let automatic reminders chase late clients for you.</p>
<img src="/freelancer-invoice-dashboard.webp" width="1200" height="700"
     alt="Acme Invoice dashboard showing a freelancer's sent, paid and overdue invoices"
     fetchpriority="high">
```

Notes on the image:
- Convert it to WebP and set the width/height to its real display size.
- Don't lazy-load it. It's the hero image, so lazy-loading would slow the page's main visible content (LCP).
- Make the alt text describe what the image actually shows.

#### Internal links to add

| From page | Anchor text | To |
|---|---|---|
| Homepage (below intro) | freelance invoice templates | /templates |
| Homepage | automatic payment reminders | /features/reminders |
| Homepage | pricing for freelancers | /pricing |
| Blog posts about getting paid | invoice software for freelancers | / |

If you share the rest of the page or point me to the file in your codebase, I can check the full heading outline and internal links and make the edits directly.
---
<sub>Real, unedited output recorded on 2026-09-29 during the plugin's eval run (Claude Code, Opus 5.5, seo-checklist v1.0.0). "Acme Invoice" is a fictional demo company.</sub>
