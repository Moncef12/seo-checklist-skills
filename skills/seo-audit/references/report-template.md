# Report template

Use this structure for the audit deliverable. Write it as a Markdown file (`seo-audit-<domain>-<YYYY-MM-DD>.md`) unless the user asks for something else. Keep the language plain: the reader may be a founder, not an SEO.

```markdown
# SEO audit: <domain>
<date> · Scope: <pages/sections checked> · Data: <crawl sample N, GSC yes/no, keyword tool yes/no>

## Executive summary
- <Overall state in one sentence, e.g. "Technically solid, but 40% of sitemap URLs are noindex">
- <Biggest risk>
- <Biggest opportunity, quantified if possible, e.g. "~1,200 missed clicks/mo on 8 low-CTR queries">
- <What is unknown and what data would settle it>
- <The one thing to do this week>

## Scorecard
| Section | ✅ | ⚠️ | ❌ | ❓ |
|---|---|---|---|---|
| Technical (13) | | | | |
| Quick wins (5) | | | | |
| On-page (7) | | | | |
| Content (10) | | | | |
| Links (5) | | | | |

## Top priorities
| # | Fix | Why it matters | Effort | Impact |
|---|---|---|---|---|
| 1 | <specific action> | <evidence + consequence> | S/M/L | High/Med/Low |
...(5-10 rows)

## Findings by section
### Technical
- ❌ **T4 robots.txt / noindex**: <evidence>. **Do:** <exact change>.
- ✅ **T5 Canonicals**: self-referencing on all 20 sampled pages.
- ❓ **T1 GSC & GA4**: can't verify from outside. **Need:** confirmation or GSC access.
...
(repeat for each section, all 40 items, most severe first within a section)

## Rewrites ready to paste
| URL | Current title (chars) | New title (chars) | New meta description (chars) |
|---|---|---|---|

## Next steps
1. This week: ...
2. This month: ...
3. Ongoing: ...
```

Guidelines:
- Every ❌/⚠️ gets a **Do:** line with a concrete action. Every ❓ gets a **Need:** line.
- Quote evidence (the URL, status code, title text, numbers). Don't write "some pages".
- Count characters in rewritten titles and descriptions and show the count. Verify with `python3 scripts/lengths.py --title "..." --meta "..."` rather than counting by eye.
- If you fixed things in the codebase, add a "Changes made" section listing files and what changed.
