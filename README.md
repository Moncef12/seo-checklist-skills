# SEO Checklist Skills for Claude

The **40-point SEO checklist** as six Claude skills. Ask Claude to "audit my SEO" or "what should I fix first in Search Console?" and it runs real checks, grades every item, and hands back a prioritized plan with paste-ready fixes. With the site's codebase open, it can also apply those fixes.

Works in **Claude Code** (as a plugin) and **Claude.ai / Claude Desktop** (as uploaded skills).

| Skill | Checklist items | Triggers on |
|---|---|---|
| **seo-audit** | All 40, orchestrated into one prioritized report | "audit my SEO", "why am I not ranking", "SEO health check" |
| **seo-technical** | GSC/GA4 · sitemaps · indexing · robots/noindex · canonicals · Core Web Vitals · mobile · JS crawlability · broken links/redirects · clean URLs · breadcrumbs · orphans · schema | indexing issues, sitemaps, canonicals, redirects, CWV, structured data |
| **seo-on-page** | Search intent · titles 50-60 chars · unique meta descriptions · headings · answer in first 2 lines · images/alt · internal links | "make this page rank", title/meta rewrites, "is this page optimized" |
| **seo-content** | Competitor keywords · high-volume/low-KD · cannibalization · merge thin pages · topic clusters · feature & use-case pages · comparison/alternatives · listicles · E-E-A-T · dateModified | keyword research, content plans, cannibalization, comparison pages |
| **seo-quick-wins** | Low CTR · `site:` title check · page-2 pages · People Also Ask · decliners | GSC exports, "quick wins", "traffic dropped" |
| **seo-links** | Brand mentions · backlink gap · "best X" lists · Reddit threads · Google Business Profile | backlinks, outreach, Reddit, local SEO |

## What's inside

- **`seo_check.py`** is a site and page checker built on the Python standard library only.
  - The `site` command checks http/https/www consolidation, robots.txt, sitemaps (including indexes and gzip), and a URL sample for status, noindex and canonical mismatches. It also finds soft 404s, crawls for broken or redirecting internal links and cookie-bounce redirects, and lists orphan candidates.
  - The `page` command checks the title and meta with character counts, the heading outline, the intro after the H1, images, internal links, JSON-LD types and validity, canonical, viewport, JS-rendering risk, and Core Web Vitals via PageSpeed Insights (`--psi`).
- **`gsc_analyze.py`** takes a Google Search Console export (pass the `.zip` directly) and finds low-CTR rows, page-2 rankings, question queries, decliners (from compare-mode exports) and keyword cannibalization (from query+page data).
- **References** load only when needed: framework-specific fixes (Next.js, Nuxt, Astro, SvelteKit, WordPress, nginx, Vercel, Netlify), the full checklist with verification methods, a report template, content page templates and outreach emails.
- **Optional MCP integrations:** if a keyword or SERP tool is connected (DataForSEO, Ahrefs, Semrush), the skills use it for competitor keywords, keyword difficulty, SERP intent and People Also Ask. Without one, they fall back to web search and your exports, and they never invent search volumes.

## Install

### Claude Code (plugin)

```bash
/plugin marketplace add Moncef12/seo-checklist-skills
/plugin install seo-checklist@seo-checklist-skills
```

Skills are namespaced, e.g. `/seo-checklist:seo-audit`, but Claude also picks them up automatically from what you ask.

### Claude Code (manual)

```bash
git clone https://github.com/Moncef12/seo-checklist-skills
cp -r seo-checklist-skills/skills/* ~/.claude/skills/
```

### Claude.ai / Claude Desktop

```bash
make package   # builds dist/<skill>.zip for each skill
```

Then go to **Settings > Capabilities > Skills > Upload skill** and upload each zip (code execution must be enabled).

**Requirements:** Python 3.9+ for the bundled scripts. No pip installs are needed.

## Usage examples

```text
Audit the SEO of https://example.com - the pages that matter are /pricing and /blog.
Here's my GSC export (~/Downloads/example.com-Performance.zip). What are my quick wins?
Rewrite the title, meta and intro of app/blog/[slug]/page.tsx for "invoice software for freelancers".
/blog/invoice-guide and /templates compete for "invoice template". What do I do?
Plan a topic cluster and alternatives pages for our project management SaaS vs Asana and Trello.
Find link opportunities: who links to Linear and Height but not to us?
```

You can also run the scripts directly:

```bash
python3 skills/seo-technical/scripts/seo_check.py site https://example.com --sample 25 --crawl 100
python3 skills/seo-on-page/scripts/seo_check.py page https://example.com/pricing --psi
python3 skills/seo-quick-wins/scripts/gsc_analyze.py quick-wins ~/Downloads/gsc-export.zip
```

## How the skills are built

The skills follow Anthropic's skill-authoring guidance:

- **Progressive disclosure.** Short, "pushy" descriptions (what the skill does and when to use it) are always in context. The SKILL.md bodies stay under ~150 lines, and long material lives in `references/`, one level deep, with a table of contents.
- **Deterministic work goes in scripts.** Fetching, parsing, counting characters and CTR math live in tested scripts instead of being redone by the model on every run.
- **Explain the why.** Instructions give reasons, such as "robots.txt blocks crawling, not indexing", instead of rigid MUST rules, so Claude can handle edge cases.
- **Honest grading.** Items that can't be verified from outside (GSC setup, backlink profile) are marked ❓ with the data needed to settle them, never guessed.
- **Self-contained skills.** Shared scripts live in `shared/` and are copied into each skill by `make sync`, so any single skill works on its own, and CI fails if the copies drift.

## Development

```bash
make sync        # copy shared/*.py into the skills that use them
make test        # offline unit tests against fixtures
make validate    # claude plugin validate . --strict
claude plugin eval . --runs 1 -j 4   # behavioral evals (with vs. without the plugin)
```

The eval cases in `evals/<case>/` pair a realistic prompt with an LLM grader rubric. Add one whenever you find a failure mode.

## Credits

The checklist is adapted from **"The only SEO checklist you'll need"** by [Okara](https://okara.ai). The skills, scripts and guidance in this repo are independent work and are not affiliated with or endorsed by Okara.

## License

MIT
