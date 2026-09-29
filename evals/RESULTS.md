# Eval results

Behavioral evals run with `claude plugin eval` (Claude Code 2.1.284, agent model Opus 5.5, default Haiku judge with 3 votes per grader). Each case runs **3× with the plugin and 3× without it** (the baseline), with the same prompt and tools. Date: 2026-09-29.

| Case | What it tests | With plugin | Baseline | Skill fired |
|---|---|---|---|---|
| `onpage-rewrite` | Title/meta/H1/intro rewrites for a keyword, with character counts | **0.83** | 0.50 | 3/3 |
| `content-cannibalization` | Diagnosis plus an executable merge/redirect plan | **0.67** | 0.50 | 3/3 |
| `audit-static-site` | Full audit of a static export: planted issues, honest unknowns, priorities | 1.00 | 1.00 | 3/3 |
| `gsc-export` | Quick wins from raw Search Console CSVs, and knowing decliners need a compare export | 1.00 | 1.00 | 3/3 |
| `technical-deindex` | robots.txt vs noindex, and the FAQ rich-results reality | 1.00 | 1.00 | 3/3 |
| `links-ethical` | Declining link schemes and giving a concrete compliant plan | 1.00 | 1.00 | 3/3 |
| `no-trigger-google-ads` | Near-miss (paid search): the SEO skills must **not** trigger | 1.00 | 1.00 | **0/3 ✓** |
| **Mean** | | **0.93** | 0.86 | 18/18 on target, 0/3 false |

## What this shows

- **Triggering is reliable.** The right skill loaded in every one of the 18 SEO runs, and never on the Google Ads near-miss.
- **The biggest gains are on deliverable-shaped tasks.** With the plugin, Claude produces multiple rewrite options with verified character counts and paste-ready merge/redirect tables. The baseline gives good advice but less executable output.
- **The baseline is strong on SEO knowledge.** On the pure-knowledge cases (robots vs noindex, link ethics, reading a GSC export), Opus 5.5 without the plugin already passes, and the plugin keeps that quality.
- **The plugin adds real checks, and they cost more.** In the audit case, the plugin arm runs the bundled checker across every page: about 17 turns and $0.65 per run, against about 4 turns and $0.33 for the baseline. That's how it catches issues that are easy to miss by reading HTML, such as orphans, soft 404s, redirect chains and cookie loops.

## Bugs the evals caught (and fixes)

1. **Sandboxed scripts.** When the checker couldn't read files in a sandbox, the skill stopped and asked the user to change settings. Every script-backed skill now falls back to applying the same rules by hand. Verified with a re-run.
2. **Character counting.** Models miscount title lengths. Added `lengths.py` (exact counts plus a pixel-width estimate), which the on-page, quick-wins and audit skills use before presenting rewrites.

## Caveats

- Three cases were re-run after a usage-limit interruption. The table uses the clean runs, and the on-page row reflects the version with `lengths.py`.
- The Haiku judge is noisy on long answers. Two of the with-plugin failures above (`content-cannibalization`, `onpage-rewrite` meta/structure) contained every required element on manual review. The scores are reported as judged, without adjustment.
- The LLM judge can't reliably verify character counts, so the grader checks that counts are present and in range. The counts themselves were verified with `lengths.py` on sample outputs.

Reproduce with `make eval` (about $8-10 of usage for the full suite at 3 runs per case).
