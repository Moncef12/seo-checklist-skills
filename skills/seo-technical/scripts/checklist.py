#!/usr/bin/env python3
"""
checklist.py - keep a living SEO-CHECKLIST.md in the project and update it after every audit.

  python3 checklist.py init   [--file SEO-CHECKLIST.md] [--site https://example.com]
  python3 checklist.py update [--file SEO-CHECKLIST.md] --statuses statuses.json [--site URL] [--date YYYY-MM-DD]
  python3 checklist.py update [--file SEO-CHECKLIST.md] --set T5=pass:"self-canonical on all pages" --set Q2=fail
  python3 checklist.py show   [--file SEO-CHECKLIST.md]

The checklist has the 40 items in five sections, so it can be worked through one section at a
time. Each run records the new status of the items it has evidence for, keeps the others, and
lists what changed since the previous run (fixed, regressed, newly checked). Ticking a box by hand
(- [x]) is respected: the item counts as done until a later audit finds otherwise.

statuses.json maps item IDs to a status, optionally with a note:
  {"T1": {"status": "unknown", "note": "no GSC access"}, "T5": "pass", "O2": {"status": "fail", "note": "..."}}
Statuses: pass, needs-work, fail, unknown, na (aliases: ok, done, warn, partial, ?, n/a, skip).

The file stores its machine-readable state in an HTML comment at the end, so updates never depend
on parsing the prose. Standard library only. Maintained in shared/ and copied into skills by `make sync`.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile

__version__ = "1.2.0"
SECTIONS = ["Technical", "Quick wins", "On-page", "Content", "Links"]
ITEMS = [
    ("T1", "Technical", "Set up GSC and GA4"),
    ("T2", "Technical", "Submit sitemap to GSC and Bing"),
    ("T3", "Technical", "Fix indexing issues"),
    ("T4", "Technical", "Check robots.txt and noindex tags"),
    ("T5", "Technical", "Add canonical tags"),
    ("T6", "Technical", "Fix Core Web Vitals"),
    ("T7", "Technical", "Make the site mobile friendly"),
    ("T8", "Technical", "Check JS content is crawlable"),
    ("T9", "Technical", "Fix broken links, 404s, redirect chains"),
    ("T10", "Technical", "Use clean, descriptive URLs"),
    ("T11", "Technical", "Add breadcrumbs"),
    ("T12", "Technical", "Fix orphan pages"),
    ("T13", "Technical", "Add schema, test in Rich Results"),
    ("Q1", "Quick wins", "High impressions, low CTR in GSC"),
    ("Q2", "Quick wins", "Search `site:yourdomain.com` on Google"),
    ("Q3", "Quick wins", "Old pages ranking on page 2"),
    ("Q4", "Quick wins", "\"People also ask\" on your keywords"),
    ("Q5", "Quick wins", "Pages losing traffic or rankings"),
    ("O1", "On-page", "Match every page to search intent"),
    ("O2", "On-page", "Titles 50-60 characters"),
    ("O3", "On-page", "Unique meta descriptions"),
    ("O4", "On-page", "Fix heading structure"),
    ("O5", "On-page", "Answer the query in the first 2 lines"),
    ("O6", "On-page", "Optimize images, add alt text"),
    ("O7", "On-page", "Internal links to important pages"),
    ("C1", "Content", "Find your competitors' keywords"),
    ("C2", "Content", "Find high-volume, low-KD keywords"),
    ("C3", "Content", "Fix keyword cannibalization"),
    ("C4", "Content", "Merge thin or overlapping pages"),
    ("C5", "Content", "Topic clusters around pillar pages"),
    ("C6", "Content", "Pages for each feature and use case"),
    ("C7", "Content", "Comparison and alternatives pages"),
    ("C8", "Content", "The best listicles in your category"),
    ("C9", "Content", "Author bio and E-E-A-T signals"),
    ("C10", "Content", "Update dateModified on refresh"),
    ("L1", "Links", "Turn brand mentions into backlinks"),
    ("L2", "Links", "Backlink gap"),
    ("L3", "Links", "Get into other sites' \"best X\" lists"),
    ("L4", "Links", "Show up in Reddit threads that rank"),
    ("L5", "Links", "Google Business Profile (local businesses)"),
]
IDS = [i for i, _, _ in ITEMS]
STATUS = {  # canonical -> (icon, label, counts as done)
    "pass": ("✅", "Pass", True),
    "needs-work": ("⚠️", "Needs work", False),
    "fail": ("❌", "Fail", False),
    "unknown": ("❓", "Unknown", False),
    "na": ("➖", "N/A", True),
}
ALIASES = {"ok": "pass", "done": "pass", "passed": "pass", "✅": "pass", "warn": "needs-work",
           "warning": "needs-work", "partial": "needs-work", "needs work": "needs-work", "⚠️": "needs-work",
           "failed": "fail", "❌": "fail", "?": "unknown", "❓": "unknown", "todo": "unknown",
           "n/a": "na", "skip": "na", "not applicable": "na", "➖": "na"}
RANK = {"fail": 0, "needs-work": 1, "unknown": 2, "pass": 3, "na": 3}
STATE_RE = re.compile(r"<!-- seo-checklist:state (\{.*?\}) -->", re.S)
LINE_RE = re.compile(r"^- \[( |x|X)\] .*?\*\*(T1[0-3]|T[1-9]|Q[1-5]|O[1-7]|C10|C[1-9]|L[1-5])\*\*", re.M)


def norm_status(value):
    s = str(value).strip().lower()
    s = ALIASES.get(s, s)
    if s not in STATUS:
        raise ValueError(f"unknown status {value!r} (use: {', '.join(STATUS)})")
    return s


def load(path):
    """Return (state, manual_ticks). A missing file gives an empty state."""
    if not os.path.exists(path):
        return {"version": 1, "site": None, "runs": [], "items": {}}, {}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = STATE_RE.search(text)
    state = json.loads(m.group(1)) if m else {"version": 1, "site": None, "runs": [], "items": {}}
    ticks = {item: box.lower() == "x" for box, item in LINE_RE.findall(text)}
    return state, ticks


def parse_updates(statuses_file=None, sets=()):
    updates = {}
    if statuses_file:
        with open(statuses_file, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):  # [{"id": "T1", "status": "...", "note": "..."}]
            data = {d["id"]: d for d in data}
        for key, val in data.items():
            if isinstance(val, dict):
                updates[key.upper()] = (norm_status(val.get("status")), (val.get("note") or "").strip())
            else:
                updates[key.upper()] = (norm_status(val), "")
    for s in sets:
        m = re.fullmatch(r"\s*([A-Za-z]\d{1,2})\s*=\s*([^:]+?)\s*(?::(.*))?", s, re.S)
        if not m:
            raise ValueError(f"--set expects ID=STATUS[:note], got {s!r}")
        updates[m.group(1).upper()] = (norm_status(m.group(2)), (m.group(3) or "").strip().strip('"'))
    bad = [k for k in updates if k not in IDS]
    if bad:
        raise ValueError(f"unknown item ID(s): {', '.join(bad)} (valid: T1-T13, Q1-Q5, O1-O7, C1-C10, L1-L5)")
    return updates


def apply(state, ticks, updates, date, site=None):
    """Merge one run into the state. Returns the list of changes [(id, old, new)]."""
    items = state.setdefault("items", {})
    changes = []
    for item, ticked in ticks.items():  # a box ticked or unticked by hand since the last run
        cur = items.get(item, {}).get("status", "unknown")
        if item in updates:
            continue
        if ticked and not STATUS[cur][2]:
            items[item] = {**items.get(item, {}), "status": "pass", "note": "marked done by hand", "since": date}
            changes.append((item, cur, "pass"))
        elif not ticked and STATUS[cur][2] and cur != "na":
            items[item] = {**items.get(item, {}), "status": "needs-work", "note": "unticked by hand",
                           "since": date}
            changes.append((item, cur, "needs-work"))
    for item, (status, note) in updates.items():
        old = items.get(item, {}).get("status")
        entry = items.setdefault(item, {})
        if old != status:
            entry["since"] = date
            changes.append((item, old or "new", status))
            entry.setdefault("history", []).append([date, status])
        entry["status"] = status
        if note or old != status:
            entry["note"] = note
        entry["checked"] = date
    if site:
        state["site"] = site
    if date not in state.setdefault("runs", []):
        state["runs"].append(date)
    state["last_changes"] = [list(c) for c in changes]
    return changes


def counts(state):
    c = {k: 0 for k in STATUS}
    for item in IDS:
        c[state.get("items", {}).get(item, {}).get("status", "unknown")] += 1
    return c


def render(state):
    items = state.get("items", {})
    c = counts(state)
    applicable = len(IDS) - c["na"]
    done = c["pass"]
    pct = round(100 * done / applicable) if applicable else 100
    bar = "█" * round(pct / 5) + "░" * (20 - round(pct / 5))
    runs = state.get("runs", [])
    lines = ["# SEO checklist", ""]
    if state.get("site"):
        lines.append(f"Site: {state['site']}  ")
    lines += [f"Last updated: {runs[-1] if runs else 'never'} · {len(runs)} run(s)", "",
              f"**Progress: {done}/{applicable} done ({pct}%)** `{bar}`  ",
              f"❌ {c['fail']} failing · ⚠️ {c['needs-work']} need work · ❓ {c['unknown']} unknown"
              + (f" · ➖ {c['na']} not applicable" if c["na"] else ""), ""]
    changes = state.get("last_changes") or []
    if changes:
        new = [x for x in changes if x[1] == "new"]
        better = [x for x in changes if x[1] != "new" and RANK.get(x[2], 2) > RANK.get(x[1], 2)]
        worse = [x for x in changes if x[1] != "new" and RANK.get(x[2], 2) < RANK.get(x[1], 2)]
        other = [x for x in changes if x not in new and x not in better and x not in worse]
        title = dict((i, t) for i, _, t in ITEMS)

        def fmt(x):
            old = "new" if x[1] == "new" else STATUS[x[1]][0]
            return f"- **{x[0]}** {title[x[0]]}: {old} → {STATUS[x[2]][0]} {STATUS[x[2]][1]}"
        lines += ["## Changes in the last run", ""]
        if better:
            lines += ["Improved:", ""] + [fmt(x) for x in better] + [""]
        if worse:
            lines += ["Got worse:", ""] + [fmt(x) for x in worse] + [""]
        if new:
            lines += ["Newly checked:", ""] + [fmt(x) for x in sorted(new, key=lambda x: RANK[x[2]])] + [""]
        if other:
            lines += [fmt(x) for x in other] + [""]
    for section in SECTIONS:
        sec = [(i, t) for i, s, t in ITEMS if s == section]
        sec_done = sum(1 for i, _ in sec if STATUS[items.get(i, {}).get("status", "unknown")][2])
        lines += [f"## {section} ({sec_done}/{len(sec)})", ""]
        for i, t in sec:
            e = items.get(i, {})
            st = e.get("status", "unknown")
            icon, label, is_done = STATUS[st]
            note = f": {e['note']}" if e.get("note") else ""
            since = f" _(since {e['since']})_" if e.get("since") and st != "unknown" else ""
            lines.append(f"- [{'x' if is_done else ' '}] {icon} **{i}** {t} · {label}{note}{since}")
        lines.append("")
    lines += ["---", "",
              "Updated by `/seo checklist` (seo-checklist-skills). Tick a box by hand when you fix something "
              "the audit can't see, and the next run keeps it. Statuses: ✅ pass · ⚠️ needs work · ❌ fail · "
              "❓ unknown (needs data or access) · ➖ not applicable.", "",
              f"<!-- seo-checklist:state {_state_json(state)} -->", ""]
    return "\n".join(lines)


def _state_json(state):
    # "-->" inside a note would end the HTML comment early; \u003e decodes back to ">"
    return json.dumps(state, ensure_ascii=False, sort_keys=True).replace("-->", "--\\u003e")


def save(path, text):
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".seo-checklist-", suffix=".md")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def summary(state):
    c = counts(state)
    items = state.get("items", {})
    title = dict((i, t) for i, _, t in ITEMS)
    todo = sorted((i for i in IDS if items.get(i, {}).get("status", "unknown") in ("fail", "needs-work")),
                  key=lambda i: (RANK[items[i]["status"]], IDS.index(i)))
    out = [f"{c['pass']}/{len(IDS) - c['na']} done · {c['fail']} fail · {c['needs-work']} need work · "
           f"{c['unknown']} unknown"]
    if todo:
        out.append("Next: " + "; ".join(f"{i} {title[i]}" for i in todo[:5]))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "update", "show"):
        p = sub.add_parser(name)
        p.add_argument("--file", default="SEO-CHECKLIST.md")
        if name != "show":
            p.add_argument("--site")
            p.add_argument("--date", default=dt.date.today().isoformat())
        if name == "update":
            p.add_argument("--statuses", help="JSON file mapping item IDs to statuses")
            p.add_argument("--set", action="append", default=[], help='ID=STATUS[:note], repeatable')
    a = ap.parse_args(argv)
    state, ticks = load(a.file)
    if a.cmd == "show":
        if not os.path.exists(a.file):
            sys.exit(f"{a.file} doesn't exist yet - run `checklist.py init` or `update` first")
        print(summary(state))
        return 0
    if a.cmd == "init" and os.path.exists(a.file):
        print(f"{a.file} already exists - kept as is.\n" + summary(state))
        return 0
    try:
        updates = parse_updates(getattr(a, "statuses", None), getattr(a, "set", ()))
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.cmd == "update" and not updates:
        print("error: nothing to update - pass --statuses FILE or --set ID=STATUS", file=sys.stderr)
        return 2
    changes = apply(state, ticks, updates, a.date, a.site)
    save(a.file, render(state))
    print(f"Wrote {a.file} ({len(changes)} change(s)).\n" + summary(state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
