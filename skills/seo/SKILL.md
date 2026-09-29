---
name: seo
description: Command router for the SEO checklist skills. Invoked explicitly as /seo with a mode (audit, technical, page, rewrite, gsc, decliners, content, cannibal, compare, links, local, schema, cwv, fix, ci) or with just a URL for a full audit. With no argument it shows the command menu.
argument-hint: "[URL | audit | technical | page | rewrite | gsc | decliners | content | cannibal | compare | links | local | schema | cwv | fix | ci] [target]"
disable-model-invocation: true
---

# /seo router

Arguments: `$ARGUMENTS`

Split the arguments into a **mode** (the first word, if it matches the table below) and a **target** (everything else: a URL, file path, keyword, domain or pasted text). Then run the mode.

This router only dispatches. The detailed know-how lives in the six sibling skills. For each mode, load the skill named in the table. Use the Skill tool (e.g. `seo-checklist:seo-on-page`), or if that isn't available, read `../<skill>/SKILL.md` relative to this file. Then follow that skill, focused on the section named in the table.

## Mode routing

| Input | Mode | Skill → focus |
|---|---|---|
| *(empty)* | menu | Show the menu below. Nothing else. |
| a URL or domain with no mode | **auto: full audit** | `seo-audit` → the whole workflow |
| `audit <url>` | full audit | `seo-audit` → all 40 items, report template |
| `technical <url>` | technical check | `seo-technical` → the 13 technical items |
| `page <url\|file> [keyword]` | on-page review | `seo-on-page` → all 7 items + rewrites |
| `rewrite <url\|file\|text> <keyword>` | rewrites only | `seo-on-page` → O2, O3, O4, O5: title, meta, H1 and first two lines, 2-3 options each, counts verified with `lengths.py` |
| `gsc <export.zip\|csv>` | quick wins | `seo-quick-wins` → Q1-Q4 |
| `decliners <compare-export>` | traffic losses | `seo-quick-wins` → Q5 diagnosis + refresh plan |
| `content <domain\|topic>` | content plan | `seo-content` → C1, C2, C5, C6: gaps, winnable keywords, clusters, priorities |
| `cannibal <query_page.csv\|domain\|keyword>` | cannibalization | `seo-content` → C3, C4: owner URL + merge/redirect table |
| `compare <competitor>` | comparison pages | `seo-content` → C7, C8: "X vs Y", alternatives and listicle briefs |
| `links <domain>` | link plan | `seo-links` → L1-L4 |
| `local <business or url>` | local SEO | `seo-links` → L5 Google Business Profile, plus `LocalBusiness` schema |
| `schema <url\|file>` | structured data | `seo-technical` → T11, T13 + `references/fixes.md#structured-data`: ready-to-paste JSON-LD |
| `cwv <url>` | Core Web Vitals | `seo-technical` → T6: `seo_check.py page --psi`, fixes by metric and stack |
| `fix` | apply fixes | `seo-audit` → step 6: fix the findings from this conversation's audit in the open codebase. If no audit has run yet, ask for the URL and run `technical` first. |
| `ci <url>` | CI gate | `seo-technical`: add `seo_check.py site <url> --fail-on FAIL` to the project's CI (GitHub Actions, GitLab, etc.) |
| `help` | menu | Show the menu |

**Unrecognized first word:**
- If the whole input looks like a URL or domain, run the full audit.
- If it looks like a question or request ("why did my traffic drop?"), answer it with the closest mode, and say which mode you chose.
- Otherwise show the menu.

**Missing target:** ask for it in one short line (e.g. "Which URL should I audit?"). Don't show the whole menu.

## Menu

When showing the menu, print exactly this block and stop:

```
SEO Checklist: commands

/seo <url>                     → AUTO: full 40-point audit + prioritized report
/seo audit <url>               → Full audit (technical, on-page, content, quick wins, links)
/seo technical <url>           → Crawl, indexing, sitemaps, canonicals, redirects, schema
/seo page <url|file> [kw]      → On-page review of one page + rewrites
/seo rewrite <url|file> <kw>   → Title, meta, H1 and intro rewrites only (exact char counts)
/seo gsc <export.zip>          → Search Console quick wins: low CTR, page 2, questions
/seo decliners <compare.zip>   → Pages losing traffic: diagnosis + refresh plan
/seo content <domain|topic>    → Content plan: competitor gaps, low-KD keywords, clusters
/seo cannibal <data|keyword>   → Pages competing for one keyword → merge/redirect plan
/seo compare <competitor>      → "X vs Y", alternatives and "best X" page briefs
/seo links <domain>            → Link plan: mentions, backlink gap, lists, Reddit
/seo local <business>          → Google Business Profile + local schema
/seo schema <url|file>         → Ready-to-paste JSON-LD for a page
/seo cwv <url>                 → Core Web Vitals diagnosis + stack-specific fixes
/seo fix                       → Apply the audit's fixes in your codebase
/seo ci <url>                  → Add the SEO checker as a CI gate

Tip: you don't need commands. Just ask, e.g. "why isn't my blog indexed?"
```
