#!/usr/bin/env python3
"""
gsc_analyze.py - find SEO quick wins in Google Search Console exports.

  python3 gsc_analyze.py quick-wins  EXPORT.zip|Queries.csv|Pages.csv [--min-impressions 100]
  python3 gsc_analyze.py decliners   EXPORT.zip|Pages.csv   (export made in "Compare" mode)
  python3 gsc_analyze.py cannibalization query_page.csv     (query + page rows, e.g. API export)
  python3 gsc_analyze.py titles query_page.csv [--html-dir out/ --base https://example.com]

quick-wins       High impressions but low CTR for the position (rewrite title/meta),
                 queries/pages sitting on page 2 (positions 11-20, update first) and
                 question-style queries (answer them in FAQ sections/pages).
decliners        Pages or queries losing clicks or position between two periods.
cannibalization  Queries where several of your URLs split the impressions.
titles           The `site:` check (checklist Q2) with data: fetches each page's live <title>
                 and flags titles that miss the page's top query, cut it off past ~600 px,
                 or would be truncated. Needs query + page rows for the keyword check; with
                 Pages.csv alone it checks length and truncation only. --html-dir reads a
                 static build instead of fetching (/a/b -> a/b.html, a/b/index.html or a__b.html).

How to export from GSC: Performance > Search results > pick a date range
(3 months is a good default) > Export > Download CSV. That gives a .zip with
Queries.csv and Pages.csv; pass the .zip directly. For decliners, first click
the date filter > Compare > "Compare last 3 months to previous period".
Standard library only (Python 3.9+).

This file is maintained in shared/ and copied into skills by `make sync`.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.parse
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

__version__ = "1.2.0"

# Rough organic CTR by position (blended desktop+mobile, industry studies).
# Real CTR varies a lot with SERP features; used only to flag outliers.
EXPECTED_CTR = {1: .28, 2: .15, 3: .10, 4: .075, 5: .055, 6: .045, 7: .035,
                8: .03, 9: .025, 10: .02}
QUESTION = re.compile(r"^(how|what|why|when|where|which|who|whose|can|could|does|do|did|is|are|"
                      r"should|will|would|was|were|best way|difference between|"      # EN
                      r"comment|pourquoi|quand|quel|quelle|quels|combien|où|qu'est|est-ce|"  # FR
                      r"cómo|como|qué|que es|por qué|cuándo|cuál|dónde|"               # ES/PT
                      r"wie|was|warum|wann|welche|wo)\b|\?$", re.I)                   # DE


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def _num(v):
    """Parse GSC numbers in any locale: 1,234 / 1.234 / 1 234 / 0.33% / 0,33 %."""
    if v is None:
        return 0.0
    s = str(v).strip().replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
    pct = s.endswith("%")
    s = s.rstrip("%")
    if "," in s and "." in s:  # both separators: the last one is the decimal mark
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:  # "1,234" is thousands; "12,5" / "0,33" is a decimal comma
        s = s.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", s) else s.replace(",", ".")
    try:
        n = float(s)
    except ValueError:
        return 0.0
    return n / 100 if pct else n


def _read_csv_text(text):
    text = text.lstrip("﻿")
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(io.StringIO(text), dialect=dialect))


def load_tables(path):
    """Return {name: rows}. A GSC zip yields Queries/Pages; a CSV yields itself."""
    if path.lower().endswith(".zip"):
        out = {}
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                base = n.rsplit("/", 1)[-1]
                if base.lower() in ("queries.csv", "pages.csv"):
                    out[base[:-4]] = _read_csv_text(z.read(n).decode("utf-8", "replace"))
        if not out:
            sys.exit(f"{path}: no Queries.csv or Pages.csv inside - is this a GSC Performance export?")
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        return {path.rsplit("/", 1)[-1]: _read_csv_text(f.read())}


METRICS = ("clicks", "impressions", "ctr", "position")
# Localized GSC column names (EN, FR, DE, ES, PT, IT, NL)
ALIASES = {
    "clicks": ("clicks", "clics", "klicks", "clics", "cliques", "clic", "klikken"),
    "impressions": ("impressions", "impressionen", "impresiones", "impressões", "impressioni", "vertoningen"),
    "ctr": ("ctr",),
    "position": ("position", "posición", "posição", "posizione", "positie"),
}
_METRIC_RE = re.compile(r"^(.*?)\s*(" + "|".join(sorted({a for v in ALIASES.values() for a in v}, key=len,
                                                         reverse=True)) + r")$", re.I)
_CANON = {a: m for m, v in ALIASES.items() for a in v}


def split_columns(rows):
    """Identify the dimension column(s) and one or two metric groups.

    GSC names comparison columns like "Last 3 months Clicks" / "Previous 3 months Clicks";
    plain exports just use "Clicks". Returns (dims, [group_prefix, ...], colmap)
    where colmap[(prefix, metric)] = column name. The first group is the most recent.
    """
    cols = list(rows[0].keys()) if rows else []
    colmap, prefixes, dims = {}, [], []
    for c in cols:
        m = _METRIC_RE.match(c.strip())
        if m:
            prefix = m.group(1).strip()
            colmap[(prefix, _CANON[m.group(2).lower()])] = c
            if prefix not in prefixes:
                prefixes.append(prefix)
        else:
            dims.append(c)
    return dims, prefixes, colmap


def normalize(rows, prefix_index=0):
    dims, prefixes, colmap = split_columns(rows)
    if not prefixes:
        sys.exit("Could not find Clicks/Impressions/CTR/Position columns.")
    p = prefixes[prefix_index]
    out = []
    for r in rows:
        rec = {"key": " | ".join((r.get(d) or "").strip() for d in dims[:1])}
        for d in dims:
            rec[d.strip().lower()] = (r.get(d) or "").strip()
        for m in METRICS:
            rec[m] = _num(r.get(colmap.get((p, m))))
        if rec["impressions"] and not rec["ctr"] and colmap.get((p, "ctr")) is None:
            rec["ctr"] = rec["clicks"] / rec["impressions"]
        out.append(rec)
    return dims, out


# --------------------------------------------------------------------------
# Analyses
# --------------------------------------------------------------------------

def expected_ctr(pos):
    return EXPECTED_CTR.get(max(1, round(pos)), 0.01)


def quick_wins(rows, min_impr):
    dims, recs = normalize(rows)
    low_ctr, page_two, questions = [], [], []
    for r in recs:
        pos, imp, ctr = r["position"], r["impressions"], r["ctr"]
        if not imp or not pos:
            continue
        if pos <= 10.5 and imp >= min_impr:
            exp = expected_ctr(pos)
            if ctr < exp * 0.5:
                r["expected_ctr"] = exp
                r["missed_clicks"] = round(imp * (exp - ctr))
                low_ctr.append(r)
        elif 10.5 < pos <= 20.5 and imp >= min_impr / 2:
            page_two.append(r)
        if QUESTION.search(r["key"]) and imp >= min_impr / 5:
            questions.append(r)
    low_ctr.sort(key=lambda r: -r["missed_clicks"])
    page_two.sort(key=lambda r: -r["impressions"])
    questions.sort(key=lambda r: -r["impressions"])
    return {"dimension": dims[0] if dims else "key", "low_ctr": low_ctr,
            "page_two": page_two, "questions": questions}


def decliners(rows, min_clicks_lost, swap=False):
    dims, prefixes, _ = split_columns(rows)
    if len(prefixes) < 2:
        sys.exit("Need a comparison export (two date ranges). In GSC: Date > Compare, then export.")
    cur_i, prev_i = (1, 0) if swap else (0, 1)
    _, cur = normalize(rows, cur_i)
    _, prev = normalize(rows, prev_i)
    out = []
    for c, p in zip(cur, prev):
        lost = p["clicks"] - c["clicks"]
        pos_drop = (c["position"] - p["position"]) if c["position"] and p["position"] else 0
        if lost >= min_clicks_lost or (pos_drop >= 2 and p["impressions"] >= 100):
            out.append({"key": c["key"], "clicks_now": c["clicks"], "clicks_before": p["clicks"],
                        "clicks_lost": lost,
                        "pct": round(-100 * lost / p["clicks"]) if p["clicks"] else None,
                        "position_now": c["position"], "position_before": p["position"],
                        "impressions_now": c["impressions"], "impressions_before": p["impressions"]})
    out.sort(key=lambda r: -r["clicks_lost"])
    return {"dimension": dims[0] if dims else "key", "current": prefixes[cur_i],
            "previous": prefixes[prev_i], "decliners": out}


def query_page_columns(dims):
    low = [d.strip().lower() for d in dims]
    qcol = next((d for d in low if any(k in d for k in ("quer", "keyword", "requête", "suchanfrage",
                                                               "consulta", "mot"))), None)
    pcol = next((d for d in low if any(k in d for k in ("page", "url", "landing", "seite", "página",
                                                               "pagina"))), None)
    return qcol, pcol


def cannibalization(rows, min_share):
    dims, recs = normalize(rows)
    qcol, pcol = query_page_columns(dims)
    if not qcol or not pcol:
        sys.exit(f"Need both a query and a page column; found {dims}. Export query+page rows "
                 "(GSC API, Search Analytics for Sheets, or Looker Studio).")
    by_q = defaultdict(list)
    for r in recs:
        by_q[r[qcol]].append(r)
    out = []
    for q, rs in by_q.items():
        total = sum(r["impressions"] for r in rs)
        if total <= 0:
            continue
        competing = [r for r in rs if r["impressions"] / total >= min_share]
        if len(competing) >= 2:
            competing.sort(key=lambda r: -r["impressions"])
            out.append({"query": q, "impressions": total, "clicks": sum(r["clicks"] for r in rs),
                        "pages": [{"page": r[pcol], "share": round(r["impressions"] / total, 2),
                                   "position": round(r["position"], 1), "clicks": r["clicks"]}
                                  for r in competing]})
    out.sort(key=lambda r: -r["impressions"])
    return {"cannibalized": out}


_STOPWORDS_TEXT = """a an the and or of for to in on at by with from is are be my your our how what why when
where which who can do does vs versus near me de la le les des du un une et pour en sur avec der die das und
für mit von zu el los las del y para con por que"""
STOPWORDS = set(_STOPWORDS_TEXT.split())
TITLE_PX = 600


def _variants(w):
    """A word and its likely singular forms, so "invoices" matches "invoice" and "agencies" "agency"."""
    out = {w}
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        out.add(w[:-1])
    if len(w) > 4 and w.endswith("es"):
        out.add(w[:-2])
    if len(w) > 4 and w.endswith("ies"):
        out.add(w[:-3] + "y")
    if len(w) > 5 and w.endswith("ing"):  # writing -> write / writ, planning -> plann
        out |= {w[:-3], w[:-3] + "e"}
    if len(w) > 4 and w.endswith("e"):    # write -> writ, so it meets "writing"
        out.add(w[:-1])
    return out


def _words(text):
    return [w for w in re.findall(r"[\w']+", (text or "").lower()) if w not in STOPWORDS]


def _covers(text_words, term):
    pool = set()
    for w in text_words:
        pool |= _variants(w)
    return bool(_variants(term) & pool)


def title_issues(title, query, px=None, visible_part=None):
    """Return (level, [issues], info) for one page title against its top query."""
    if not title:
        return "FAIL", ["no <title>"], {}
    issues, level = [], "PASS"
    width = px(title) if px else len(title) * 10
    shown = visible_part(title, TITLE_PX) if visible_part else title[:60]
    info = {"chars": len(title), "px": width, "visible": shown}
    if query:
        q = list(dict.fromkeys(_words(query)))
        have, seen = _words(title), _words(shown)
        missing = [t for t in q if not _covers(have, t)]
        hidden = [t for t in q if _covers(have, t) and not _covers(seen, t)]
        if q and len(missing) == len(q):
            issues.append(f"misses the keyword \"{query}\" entirely")
            level = "FAIL"
        elif missing:
            issues.append(f"keyword only partly there (missing: {', '.join(missing)})")
            level = "WARN"
        if hidden:
            issues.append(f"keyword falls after the cut-off ({', '.join(hidden)} hidden by \"...\")")
            level = "FAIL" if level == "FAIL" else "WARN"
    if width > TITLE_PX:
        issues.append(f"cut off in results (~{width}px > {TITLE_PX}px, {len(title)} chars)")
        level = "FAIL" if level == "FAIL" else "WARN"
    elif len(title) < 30:
        issues.append(f"short ({len(title)} chars): room for the keyword and a reason to click")
        if level == "PASS":
            level = "INFO"
    return level, issues, info


def _html_file_for(url, html_dir):
    path = urllib.parse.urlparse(url).path.strip("/")
    names = ["index.html"] if not path else [f"{path}.html", f"{path}/index.html", path.replace("/", "__") + ".html",
                                              path]
    for n in names:
        f = os.path.join(html_dir, n)
        if os.path.isfile(f):
            return f
    return None


def fetch_titles(urls, html_dir=None, workers=8):
    """{url: title or None}. Uses seo_check's fetch/parser so redirects, gzip and charsets behave the same."""
    import seo_check  # noqa: E402  (sibling script; only needed for this mode)

    def one(u):
        if html_dir:
            f = _html_file_for(u, html_dir)
            if not f:
                return u, None, "no matching file in --html-dir"
            res = seo_check.load_local(f)
        else:
            res = seo_check.fetch(u)
            if res["error"] or res["status"] != 200:
                return u, None, res["error"] or f"HTTP {res['status']}"
        return u, seo_check.parse_html(seo_check.decode(res)).title, None
    with ThreadPoolExecutor(workers) as ex:
        return {u: (t, err) for u, t, err in ex.map(one, urls)}


def titles(rows, html_dir=None, max_pages=50, min_impr=0, base=None):
    import lengths  # noqa: E402

    dims, recs = normalize(rows)
    qcol, pcol = query_page_columns(dims)
    if not pcol:
        sys.exit(f"Need a page column; found {dims}. Use Pages.csv or a query + page export.")
    by_page = defaultdict(list)
    for r in recs:
        by_page[r[pcol]].append(r)
    pages = []
    for page, rs in by_page.items():
        impr = sum(r["impressions"] for r in rs)
        if impr < min_impr:
            continue
        top = max(rs, key=lambda r: r["impressions"]) if qcol else None
        pages.append({"page": page, "impressions": impr, "clicks": sum(r["clicks"] for r in rs),
                      "query": top[qcol] if top else None,
                      "query_impressions": top["impressions"] if top else None,
                      "position": top["position"] if top else rs[0]["position"]})
    pages.sort(key=lambda p: -p["impressions"])
    pages = pages[:max_pages]

    def full(u):
        return urllib.parse.urljoin(base, u) if base and not u.startswith(("http://", "https://")) else u
    got = fetch_titles([full(p["page"]) for p in pages], html_dir=html_dir)
    counts = defaultdict(int)
    for p in pages:
        title, err = got[full(p["page"])]
        if title:
            counts[title] += 1
    rank = {"FAIL": 0, "WARN": 1, "INFO": 2, "PASS": 3}
    for p in pages:
        title, err = got[full(p["page"])]
        p["title"] = title
        if err:
            p.update(level="INFO", issues=[f"couldn't read the title ({err})"], chars=None, px=None)
            continue
        level, issues, info = title_issues(title, p["query"], lengths.px, lengths.visible_part)
        if title and counts[title] > 1:
            issues.append(f"same title as {counts[title] - 1} other page(s)")
            level = "WARN" if level in ("PASS", "INFO") else level
        p.update(level=level, issues=issues, **info)
    pages.sort(key=lambda p: (rank[p["level"]], -p["impressions"]))
    return {"keyword_check": bool(qcol), "pages": pages}


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def _fmt(n):
    return f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |")
    return "\n".join(out)


def render_quick_wins(name, res, top):
    d = res["dimension"]
    lines = [f"## {name}", ""]
    lines += [f"### High impressions, low CTR ({len(res['low_ctr'])}) - rewrite title and meta description", ""]
    if res["low_ctr"]:
        lines.append(table([d, "Impr.", "Clicks", "CTR", "Expected", "Pos.", "Missed clicks"],
                           [[r["key"], _fmt(r["impressions"]), _fmt(r["clicks"]), f"{r['ctr']:.1%}",
                             f"~{r['expected_ctr']:.0%}", f"{r['position']:.1f}", _fmt(r["missed_clicks"])]
                            for r in res["low_ctr"][:top]]))
    else:
        lines.append("None above the impression threshold.")
    lines += ["", f"### Page 2 - positions 11-20 ({len(res['page_two'])}) - update these first", ""]
    if res["page_two"]:
        lines.append(table([d, "Impr.", "Clicks", "Pos."],
                           [[r["key"], _fmt(r["impressions"]), _fmt(r["clicks"]), f"{r['position']:.1f}"]
                            for r in res["page_two"][:top]]))
    else:
        lines.append("None.")
    if res["questions"]:
        lines += ["", f"### Question queries ({len(res['questions'])}) - "
                      "answer in FAQ sections or quick-answer pages", ""]
        lines.append(table([d, "Impr.", "Clicks", "Pos."],
                           [[r["key"], _fmt(r["impressions"]), _fmt(r["clicks"]), f"{r['position']:.1f}"]
                            for r in res["questions"][:top]]))
    return "\n".join(lines) + "\n"


def render_decliners(name, res, top):
    lines = [f"## {name}: {res['current']} vs {res['previous']}", "",
             f"{len(res['decliners'])} {res['dimension'].lower()} losing clicks or position "
             "- refresh them before they drop further.", ""]
    if res["decliners"]:
        lines.append(table([res["dimension"], "Clicks now", "Before", "Lost", "%", "Pos. now", "Pos. before"],
                           [[r["key"], _fmt(r["clicks_now"]), _fmt(r["clicks_before"]), _fmt(r["clicks_lost"]),
                             f"{r['pct']}%" if r["pct"] is not None else "-",
                             f"{r['position_now']:.1f}", f"{r['position_before']:.1f}"]
                            for r in res["decliners"][:top]]))
    return "\n".join(lines) + "\n"


def render_cannibalization(res, top):
    lines = [f"## Keyword cannibalization ({len(res['cannibalized'])} queries)", ""]
    for r in res["cannibalized"][:top]:
        lines.append(f"**{r['query']}** - {_fmt(r['impressions'])} impr., {_fmt(r['clicks'])} clicks")
        for p in r["pages"]:
            lines.append(f"- {p['page']} - {p['share']:.0%} of impressions, pos. {p['position']}, "
                         f"{_fmt(p['clicks'])} clicks")
        lines.append("")
    if not res["cannibalized"]:
        lines.append("No queries split between multiple URLs above the share threshold.")
    return "\n".join(lines) + "\n"


def render_titles(res, top):
    icon = {"FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️", "PASS": "✅"}
    pages = res["pages"]
    bad = [p for p in pages if p["level"] in ("FAIL", "WARN")]
    lines = ["## Titles vs. top queries (the `site:` check)", "",
             f"{len(bad)} of {len(pages)} pages need a new title." +
             ("" if res["keyword_check"] else " Keyword check skipped: this export has no query column "
                                               "(use a query + page export)."), ""]
    rows = []
    for p in pages[:top]:
        q = f"{p['query']} ({_fmt(p['query_impressions'])})" if p.get("query") else "-"
        size = f"{p['chars']} / ~{p['px']}px" if p.get("chars") else "-"
        rows.append([f"{icon[p['level']]} {p['page']}", q, p.get("title") or "-", size,
                     "; ".join(p["issues"]) or "ok"])
    lines.append(table(["Page", "Top query (impr.)", "Live title", "Chars / px", "Issue"], rows))
    lines += ["", "Google shows about 600 px of a title (roughly 50-60 characters) and rewrites titles that are "
                  "too long, stuffed or don't match the query. Put the top query near the start, then a reason "
                  "to click. Check exact counts with lengths.py before publishing."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["quick-wins", "decliners", "cannibalization", "titles"])
    ap.add_argument("path")
    ap.add_argument("--min-impressions", type=float, default=100,
                    help="quick-wins: impression floor for low-CTR rows (default 100)")
    ap.add_argument("--min-clicks-lost", type=float, default=10, help="decliners: default 10")
    ap.add_argument("--min-share", type=float, default=0.1,
                    help="cannibalization: min impression share per URL (default 0.1)")
    ap.add_argument("--swap", action="store_true", help="decliners: treat the 2nd date range as current")
    ap.add_argument("--html-dir", help="titles: read titles from a static build folder instead of fetching")
    ap.add_argument("--base", help="titles: site origin for relative page paths")
    ap.add_argument("--max-pages", type=int, default=50, help="titles: pages to check (default 50)")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args(argv)

    tables = load_tables(a.path)
    if a.mode == "titles":  # one table with a page column; prefer query + page rows
        scored = []
        for name, rows in tables.items():
            if rows:
                q, pg = query_page_columns(split_columns(rows)[0])
                if pg:
                    scored.append((bool(q), name))
        if not scored:
            sys.exit("titles needs Pages.csv or a query + page export (no page column found)")
        best = max(scored)[1]
        tables = {best: tables[best]}
    results, md = {}, []
    for name, rows in tables.items():
        if not rows:
            continue
        if a.mode == "quick-wins":
            res = quick_wins(rows, a.min_impressions)
            md.append(render_quick_wins(name, res, a.top))
        elif a.mode == "titles":
            res = titles(rows, html_dir=a.html_dir, max_pages=a.max_pages, base=a.base)
            md.append(render_titles(res, a.top))
        elif a.mode == "decliners":
            res = decliners(rows, a.min_clicks_lost, a.swap)
            md.append(render_decliners(name, res, a.top))
        else:
            res = cannibalization(rows, a.min_share)
            md.append(render_cannibalization(res, a.top))
        results[name] = res
    if a.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"# GSC {a.mode}\n")
        print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
