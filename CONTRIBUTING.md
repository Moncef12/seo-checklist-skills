# Contributing

## Layout

```
skills/seo/SKILL.md            /seo command router: menu + mode table -> sibling skills (Claude Code only)
skills/<skill>/SKILL.md        instructions Claude loads when the skill triggers (keep < ~150 lines)
skills/<skill>/references/     detail loaded on demand (framework fixes, templates, checklists)
skills/<skill>/scripts/        copies of shared/ scripts - DO NOT edit here
shared/                        source of truth for seo_check.py and gsc_analyze.py
examples/demo_site.py          local demo site with planted issues (tests + sample reports)
tests/                         offline unit + integration tests
evals/<case>/case.yaml         behavioral evals run with `claude plugin eval`
```

## Workflow

1. Edit `shared/*.py` or the skill markdown.
2. `make sync` copies shared scripts into the skills that use them. CI fails if the copies drift.
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
