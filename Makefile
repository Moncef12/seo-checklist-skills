# Shared scripts live in shared/ and are copied into each skill so every skill
# folder stays self-contained (works when installed on its own or zipped for Claude.ai).
SEO_CHECK_SKILLS := seo-audit seo-technical seo-on-page
GSC_SKILLS       := seo-audit seo-quick-wins seo-content
LENGTH_SKILLS    := seo-audit seo-on-page seo-quick-wins
CLAUDE ?= claude

.PHONY: sync check-sync test lint validate package demo eval all

all: sync test lint validate

sync:
	@for s in $(SEO_CHECK_SKILLS); do cp shared/seo_check.py skills/$$s/scripts/; done
	@for s in $(GSC_SKILLS); do cp shared/gsc_analyze.py skills/$$s/scripts/; done
	@for s in $(LENGTH_SKILLS); do cp shared/lengths.py skills/$$s/scripts/; done
	@echo "synced shared scripts into skills"

check-sync:
	@fail=0; \
	for s in $(SEO_CHECK_SKILLS); do cmp -s shared/seo_check.py skills/$$s/scripts/seo_check.py || { echo "out of sync: $$s/seo_check.py"; fail=1; }; done; \
	for s in $(GSC_SKILLS); do cmp -s shared/gsc_analyze.py skills/$$s/scripts/gsc_analyze.py || { echo "out of sync: $$s/gsc_analyze.py"; fail=1; }; done; \
	for s in $(LENGTH_SKILLS); do cmp -s shared/lengths.py skills/$$s/scripts/lengths.py || { echo "out of sync: $$s/lengths.py"; fail=1; }; done; \
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

# One zip per skill for Claude.ai (Settings > Capabilities > Skills > Upload)
package: sync
	@rm -rf dist && mkdir -p dist
	@cd skills && for s in */; do s=$${s%/}; zip -qr ../dist/$$s.zip $$s -x '*/__pycache__/*' '*.pyc' '.DS_Store'; done
	@ls -1 dist
