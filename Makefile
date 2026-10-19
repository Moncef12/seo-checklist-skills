# Shared scripts live in shared/ and are copied into each skill so every skill folder stays
# self-contained (works when installed on its own or zipped for Claude.ai). Every skill that runs
# scripts gets all of them: the modules import each other, and one rule is simpler than five lists.
SCRIPT_SKILLS := seo-audit seo-technical seo-on-page seo-quick-wins seo-content
CLAUDE ?= claude

.PHONY: sync check-sync test lint validate package demo eval all

all: sync test lint validate

sync:
	@for s in $(SCRIPT_SKILLS); do mkdir -p skills/$$s/scripts; rm -f skills/$$s/scripts/*.py; \
		cp shared/*.py skills/$$s/scripts/; done
	@echo "synced shared scripts into: $(SCRIPT_SKILLS)"

check-sync:
	@fail=0; \
	for s in $(SCRIPT_SKILLS); do \
		for f in shared/*.py; do cmp -s $$f skills/$$s/scripts/$$(basename $$f) || \
			{ echo "out of sync: $$s/scripts/$$(basename $$f)"; fail=1; }; done; \
		for f in skills/$$s/scripts/*.py; do [ -f shared/$$(basename $$f) ] || \
			{ echo "stale copy: $$f (not in shared/)"; fail=1; }; done; \
	done; \
	[ $$fail -eq 0 ] && echo "scripts in sync" || { echo "run: make sync"; exit 1; }

test:
	python3 -m unittest discover -s tests -v

lint:
	ruff check shared tests examples

validate:
	$(CLAUDE) plugin validate . --strict
	$(CLAUDE) plugin validate .claude-plugin/plugin.json --strict

# Local demo site with planted SEO issues: http://127.0.0.1:8799
demo:
	python3 examples/demo_site.py --port 8799

# Behavioral evals, with vs. without the plugin (uses your Claude credentials; ~$5-10)
eval:
	$(CLAUDE) plugin eval . --runs 3 -j 6 --allow-tools Bash Write --trust-plugin

# One zip per skill for Claude.ai (Settings > Capabilities > Skills > Upload).
# The /seo router is a Claude Code slash command (uses argument-hint etc.), so it's plugin-only.
package: sync
	@rm -rf dist && mkdir -p dist
	@cd skills && for s in */; do s=$${s%/}; [ "$$s" = seo ] && continue; \
		zip -qr ../dist/$$s.zip $$s -x '*/__pycache__/*' '*.pyc' '.DS_Store'; done
	@ls -1 dist
