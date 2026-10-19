# Contributing

## Layout

```
skills/seo/SKILL.md            /seo command router: menu + mode table -> sibling skills (Claude Code only)
skills/<skill>/SKILL.md        instructions Claude loads when the skill triggers (keep < ~150 lines)
skills/<skill>/references/     detail loaded on demand (framework fixes, templates, checklists)
skills/<skill>/scripts/        copies of shared/ - DO NOT edit here (`make sync` copies every module)
shared/seo_check.py            page and site checks, CLI, Markdown/JSON output
shared/gsc_analyze.py          Search Console exports: quick wins, decliners, cannibalization, titles
shared/similarity.py           near-duplicate and repeated-paragraph detection (C4)
shared/setup_detect.py         analytics and verification footprints, DNS-over-HTTPS (T1, T2)
shared/schema_rules.py         JSON-LD required/recommended properties per type (T13)
shared/report_html.py          the self-contained HTML report
shared/checklist.py            SEO-CHECKLIST.md tracker
shared/lengths.py              exact character counts and pixel widths
action.yml                     the GitHub Action (composite, runs shared/seo_check.py)
examples/demo_site.py          local demo site with planted issues (tests + sample reports)
tests/                         offline unit + integration tests
evals/<case>/case.yaml         behavioral evals run with `claude plugin eval`
evals/build_fixtures.py        rebuilds the fixtures of the v1.2 eval cases
```

## Workflow

1. Edit `shared/*.py` or the skill markdown. Modules use only the standard library and may import each other.
2. `make sync` copies every shared module into each skill that runs scripts. CI fails if a copy drifts or a stale one is left behind.
3. `make test lint validate`
4. For behavior changes, add or adjust an eval case, then run `make eval` (it costs a few dollars of
   API usage). Compare the with-plugin arm against the baseline.
5. Update `CHANGELOG.md`, bump `version` in `.claude-plugin/plugin.json` and `marketplace.json`,
   then tag `vX.Y.Z` to trigger the release workflow.

## Adding a /seo mode

1. Add a row to the mode table in `skills/seo/SKILL.md`, naming the target skill and its focus.
2. Add the mode to the `argument-hint` and to the menu block.
3. Run `make test`. `tests/test_router.py` fails if the menu, table and hint disagree, or if a
   route points at a skill that doesn't exist.

## Writing skill instructions

- The `description` frontmatter is the trigger. Say what the skill does *and* when to use it,
  including phrases users actually type.
- Explain *why* instead of stacking MUSTs. The model handles edge cases better when it knows the reason.
- Put deterministic work (fetching, parsing, counting, math) in scripts, and always give a manual
  fallback for environments without code execution.
- Never let a skill invent data (search volume, KD, backlinks). Mark it unknown and say what's needed.
