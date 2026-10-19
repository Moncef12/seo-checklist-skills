---
name: seo-on-page
description: Optimizes individual pages for search - matches the page to search intent, rewrites titles (50-60 chars) and unique meta descriptions, fixes heading structure, makes the first two lines answer the query, optimizes images and alt text, and adds internal links to important pages. Use whenever someone wants a page, post, landing page or product page to rank better, asks to write or fix a title tag, meta description, H1 or alt text, asks "is this page SEO optimized", or pastes a URL/HTML/draft and a target keyword - even if they only say "make this rank".
---

# On-page SEO

On-page work decides whether a page that *can* rank actually *does*. The goal is a page that fits what the searcher wanted, says so in the snippet, and answers straight away.

## Inputs

- **The page:** a URL, a local HTML file, a file in the codebase, or pasted draft text.
- **Target keyword** (plus 2-3 secondaries). If none is given, infer it from the page, then confirm it with GSC queries or a keyword tool when available. Say which keyword you're optimizing for, because every recommendation depends on it.

## Workflow

1. **Measure.** From this skill's directory:
   ```bash
   python3 scripts/seo_check.py page https://example.com/page [more URLs or ./file.html]
   ```
   The output includes the title and description with character counts, the heading outline, the "intro after H1", image stats, internal links, schema and canonical. If the script can't run or the input is pasted text, read it directly and count characters carefully. Accurate counts are the point of this skill.
2. **Check intent on the live SERP.** Use a SERP tool (e.g. DataForSEO `serp_organic_live_advanced`) or web search for the keyword. Note what ranks: page type (guide, listicle, tool, product, category, comparison), format, angle ("for beginners", "2026", "free"), freshness, and SERP features (PAA, video, local pack). If the page's type doesn't match, say so first. No title tweak fixes a product page competing against listicles.
3. **Grade and rewrite the 7 items below.** For titles, descriptions, H1s and intros, write 2-3 options with character counts rather than advice. Verify every count before presenting it. Models miscount characters, and a wrong count defeats the purpose:
   ```bash
   python3 scripts/lengths.py --title "Option A" "Option B" --meta "Description A"
   ```
   The helper prints exact counts plus a pixel-width estimate (Google truncates titles around 600 px). Without a shell, count carefully and say the counts are approximate.
4. **Apply.** If you're in the codebase, edit through the framework's metadata system. The seo-technical skill's `references/fixes.md` shows the patterns. Otherwise hand back a paste-ready table.

## The 7 on-page items

**O1. Match search intent.** The dominant SERP type sets the format. Informational queries need a guide or answer. Commercial investigation needs a comparison or list. Transactional queries need a product or pricing page. Navigational queries need the brand page. Mixed SERPs usually mean you can win with the best version of the most common type.

**O2. Titles, 50-60 characters.** Google truncates around 600 px, which is roughly 50-60 characters.
- Put the primary keyword near the start, add a reason to click, and put the brand last (or drop it on long titles).
- Make every title unique across the site.
- Formulas: `Keyword: Benefit | Brand`, `Keyword - X Ways to Outcome (Year)`, `Best Keyword for Audience in Year`, `Keyword vs Keyword: Honest Comparison`.
- Example: "Invoice Software" (16 chars) becomes "Invoice Software for Freelancers: Get Paid 2x Faster | Payly" (60 chars).
- Google rewrites titles that are stuffed, vague, or mismatched with the H1. Keep the title and H1 close in meaning.

**O3. Unique meta descriptions, about 120-160 characters.** Descriptions aren't a ranking factor but they drive CTR. Include the keyword (Google bolds it), a specific benefit or proof, and an implicit call to action. Every page needs its own, because duplicates get ignored.

**O4. Heading structure.** Use one H1 stating the topic, H2s for the main sections (often mirroring PAA questions and subtopics), and H3s under H2s. Don't skip levels, and don't use headings for styling. The outline should read like a table of contents.

**O5. Answer the query in the first 2 lines.** Put the direct answer right after the H1: a definition, the number, the verdict, or the top pick. This wins featured snippets and AI Overview citations and reduces pogo-sticking. Story and context come after.
- Weak: "In today's fast-paced world, many businesses wonder about..."
- Strong: "A good email open rate is 35-45% in 2026, but it varies by industry: B2B SaaS averages ~38%, ecommerce ~30%."

**O6. Images and alt text.**
- Use WebP/AVIF, sized to how they're displayed, with `width`/`height` set. `seo_check.py page` measures each image's file weight (HEAD requests, or file sizes for a local build) and flags anything over 200 KB, plus a lazy-loaded first image.
- Lazy-load images below the fold, but never the hero/LCP image.
- Use descriptive file names (`blue-running-shoe-side.webp`).
- Alt text describes the image for someone who can't see it and includes the keyword only where it's naturally accurate. Decorative images get `alt=""`.

**O7. Internal links to important pages.** Add 3-5 contextual links from relevant, strong pages (high traffic or backlinks) to the page you want to rank, and from this page onward to its pillar and money pages. Anchors should say what the target is ("invoice templates"), not "click here". GSC > Links > Top linked pages shows what's under-linked.

## Output format

```markdown
## <URL> - target: "<keyword>" (<intent>)
| Item | Status | Finding | Do |
|---|---|---|---|
| O1 Intent | ⚠️ | SERP is 8/10 listicles; page is a product page | Create a "best X" list page, link to product |
...
### Rewrites
| | Current (chars) | Option A (chars) | Option B (chars) |
|---|---|---|---|
| Title | ... | ... | ... |
| Meta description | ... | ... | ... |
| H1 | ... | ... | |
| First 2 lines | ... | ... | |
### Internal links to add
| From page | Anchor text | To |
```

Count characters exactly: they're the point of the rewrite. If the user asked about many pages, add a summary table at the top and put the full detail only on the pages that need it.
