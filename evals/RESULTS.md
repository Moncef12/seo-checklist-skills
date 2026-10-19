# Eval results (v1.2.0)

Behavioral evals run with `claude plugin eval` (Claude Code 2.1.303, the default agent model, Sonnet judge with 3 votes per grader). Each case runs **3× with the plugin and 3× without it** (the baseline), with the same prompt, tools and files. Fixtures are copied into each run's working directory by the case's `scaffold.sh` (`--scaffold`), so the bundled scripts can read them. Date: 2026-10-19. Reproduce with `make eval` (about $20-25 of usage).

| Case | What it tests | With plugin | Baseline | Δ | Skill fired |
|---|---|---|---|---|---|
| `onpage-rewrite` | Title/meta/H1/intro rewrites with character counts | **1.00** | 0.00 | +1.00 | 3/3 |
| `audit-static-site` | Full audit of a static export: planted issues, honest unknowns, priorities | **1.00** | 0.67 | +0.33 | 3/3 |
| `links-ethical` | Declining link schemes and giving a compliant plan | **0.83** | 0.50 | +0.33 | 3/3 |
| `technical-deindex` | robots.txt vs noindex, and the FAQ rich-results reality | **1.00** | 0.67 | +0.33 | 3/3 |
| `gsc-export` | Quick wins from raw Search Console CSVs | **1.00** | 0.78 | +0.22 | 3/3 |
| `checklist-tracker` | **New.** Update SEO-CHECKLIST.md from today's check and report what changed | **0.89** | 0.67 | +0.22 | 3/3 |
| `title-keyword-gaps` | **New.** Titles vs. each page's top query; a 56-character title cut off by pixel width | **1.00** | 0.80 | +0.20 | 3/3 |
| `near-duplicate-pages` | **New.** 22 pages: a city-swap doorway pair, rewritten pairs, a canonical to respect | **1.00** | 0.87 | +0.13 | 3/3 |
| `schema-required-fields` | **New.** JSON-LD that is valid JSON but not eligible for rich results | 1.00 | 1.00 | +0.00 | 3/3 |
| `setup-detection` | **New.** GTM vs GA4, a legacy UA tag, the verification method | 1.00 | 1.00 | +0.00 | 3/3 |
| `content-cannibalization` | Diagnosis plus an executable merge/redirect plan | 0.50 | 0.50 | +0.00 | 3/3 |
| `no-trigger-google-ads` | Near-miss (paid search): the SEO skills must **not** trigger | 1.00 | 1.00 | +0.00 | **0/3 ✓** |
| **Mean** | | **0.93** | 0.71 | **+0.23** | 33/33 on target, 0/3 false |

The `checklist-tracker` row comes from a re-run after its trigger fix (see below); every other row is from the full run.

## What this shows

- **The plugin never made an answer worse,** and it lifted 8 of 12 cases. The biggest gains are on deliverables: rewrites with verified character counts (+1.00), a full audit that marks unknowns honestly (+0.33), and concrete link and de-indexing plans (+0.33).
- **The new checks pay off where reading files by eye is hard.** In `title-keyword-gaps` the baseline missed the rewrite counts in every run. In `near-duplicate-pages` it once treated a page that already declares its canonical as a problem to fix, and once proposed merging pages that are distinct. With the plugin, the scripts found the city-swap pair (91% the same text) and the pixel-width cut-off every time.
- **Plain Claude is already strong at reading markup.** On `schema-required-fields` and `setup-detection` the baseline scored 1.00 too: Opus reads JSON-LD and analytics snippets correctly when the files are small. The scripts matter more on a real site, where there are hundreds of pages and the GA4 tag hides in a JavaScript bundle (`site` mode).
- **Triggering is reliable.** The right skill loaded in all 33 SEO runs and never on the Google Ads near-miss.

## How the evals were fixed along the way

1. **Sandboxed scripts.** The first v1.2 run gave each case its files as read-only extra folders. The eval sandbox doesn't let the shell read those, so the scripts never ran and every scripted case fell back to manual analysis (the skills are written to do that). The cases now copy their fixtures into the run's working directory with `scaffold.sh`. That run's numbers are not used here.
2. **Trigger gap.** In the full run, `checklist-tracker` loaded the skill in 1 of 3 runs (the other two edited the file by hand). The seo-audit description now mentions updating a checklist progress file; the re-run loaded it 3 of 3 times.
3. **Grader changes, each because the grader was wrong, not the answer:**
   - `gsc-export` required the action list at the *end*; the skill deliberately puts "Top 5 actions this week" first. It now accepts the list at the top or the end.
   - `checklist-tracker` required T9 (broken links, 404s, redirect chains) to pass, but today's check shows a new soft 404, which reasonably belongs under T9. It now accepts T9 failing for that reason only.
   - The judge moved from Haiku to Sonnet. Haiku failed a correct, complete `setup-detection` answer, which made the plugin arm look worse than the baseline.

## Caveats

- **`content-cannibalization` stays at 0.50 in both arms.** The Sonnet judge failed `actionable-deliverable` in 5 of 6 runs, including answers that contain every listed element (redirect table with the content to keep, internal link and anchor updates, sitemap removal, a Search Console check) on manual review. It's reported as judged.
- **LLM judges are noisy on long files.** The tracker grader reads an ~8,000-character checklist; one with-plugin run failed on a 2-to-1 vote with a correct file.
- **The fixtures are synthetic** (a fictional invoicing SaaS), generated by `evals/build_fixtures.py`, and the new cases were written by the plugin's author. The scripts were also run on four live production sites before release; those runs found three bugs that the fixtures didn't (GA4 in JavaScript bundles, an off-site redirect followed by the crawler, noisy repeated-paragraph warnings).
- **Cost.** The plugin arm costs more because it runs checkers: the full suite cost $23.00 plus $2.43 for the tracker re-run.
