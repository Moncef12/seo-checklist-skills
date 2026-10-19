"""
report_html.py - self-contained HTML report for seo_check.py (--html report.html).

One file, no external assets, so it opens offline and works as a CI artifact. Dark by default
with a light theme for light-mode systems. Every value that comes from a crawled site (titles,
URLs, messages) is HTML-escaped, so a hostile page can't inject markup into the report.

Standard library only. This file is maintained in shared/ and copied into skills by `make sync`.
"""
import datetime as dt
import html
from collections import Counter

LEVELS = ("FAIL", "WARN", "INFO", "PASS")
MANUAL = [
    ("GSC and GA4 linked, Page indexing report reviewed", "needs access"),
    ("Sitemap submitted in GSC and Bing Webmaster Tools", "needs access"),
    ("Core Web Vitals field data (run `page URL --psi` or open GSC)", "needs data"),
    ("Rich results tested at search.google.com/test/rich-results", "manual"),
]

CSS = """
:root{--bg:#0d0f13;--panel:#151920;--panel2:#1a1f27;--line:#252b35;--text:#e8eaee;--muted:#8b93a1;
--fail-bg:rgba(239,68,68,.16);--fail:#f87171;--warn-bg:rgba(245,158,11,.16);--warn:#fbbf24;
--pass-bg:rgba(34,197,94,.15);--pass:#4ade80;--info-bg:rgba(96,165,250,.14);--info:#93c5fd;
--q-bg:rgba(148,163,184,.14);--q:#a5b4fc;--accent:#e07a5f}
@media (prefers-color-scheme: light){:root{--bg:#f6f5f2;--panel:#ffffff;--panel2:#fbfaf8;--line:#e6e3dd;
--text:#1d2026;--muted:#6b7280;--fail-bg:#fde8e8;--fail:#b42318;--warn-bg:#fdf3dc;--warn:#9a6700;
--pass-bg:#e3f6e8;--pass:#16723b;--info-bg:#e7effc;--info:#1d4ed8;--q-bg:#eef0f4;--q:#4338ca;--accent:#c2552f}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",
Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:40px 20px 64px}
.kicker{color:var(--accent);font-weight:700;letter-spacing:.18em;font-size:12px;text-transform:uppercase}
h1{font-size:34px;line-height:1.1;margin:10px 0 6px;letter-spacing:-.02em;word-break:break-word}
.sub{color:var(--muted);margin:0 0 26px}
.stats{display:flex;gap:28px;flex-wrap:wrap;margin:0 0 30px}
.stat b{display:block;font-size:34px;line-height:1;letter-spacing:-.02em}
.stat span{color:var(--muted);font-size:11px;letter-spacing:.14em;text-transform:uppercase}
.stat.fail b{color:var(--fail)}.stat.warn b{color:var(--warn)}.stat.pass b{color:var(--pass)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin:0 0 18px;overflow:hidden}
.bar{display:flex;align-items:center;gap:7px;padding:12px 16px;border-bottom:1px solid var(--line);
background:var(--panel2)}
.dot{width:10px;height:10px;border-radius:50%;background:var(--line)}
.bar h2{margin:0 0 0 8px;font-size:14px;font-weight:600}
.bar .count{margin-left:auto;color:var(--muted);font-size:12px}
.row{display:flex;align-items:flex-start;gap:14px;padding:11px 16px;border-top:1px solid var(--line)}
.row:first-of-type{border-top:0}
.badge{flex:0 0 auto;min-width:52px;text-align:center;font:700 11px/1 ui-monospace,SFMono-Regular,Menlo,
Consolas,monospace;letter-spacing:.06em;padding:6px 8px;border-radius:6px;margin-top:1px}
.FAIL{background:var(--fail-bg);color:var(--fail)}.WARN{background:var(--warn-bg);color:var(--warn)}
.PASS{background:var(--pass-bg);color:var(--pass)}.INFO{background:var(--info-bg);color:var(--info)}
.Q{background:var(--q-bg);color:var(--q)}
.msg{flex:1;min-width:0;overflow-wrap:anywhere}
.hint{flex:0 0 auto;color:var(--muted);font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
details{border-top:1px solid var(--line)}details>summary{cursor:pointer;padding:11px 16px;color:var(--muted);
font-size:13px;list-style:none}details>summary::before{content:"▸ "}details[open]>summary::before{content:"▾ "}
.page-meta{padding:4px 16px 12px;color:var(--muted);font-size:13px;overflow-wrap:anywhere}
.page-meta b{color:var(--text);font-weight:600}
footer{color:var(--muted);font-size:12px;margin-top:28px}
a{color:inherit}
@media (max-width:640px){.hint{display:none}h1{font-size:26px}.stats{gap:18px}}
"""


def _e(s):
    return html.escape(str(s), quote=True)


def _rows(findings, show_info=True):
    out = []
    for lvl in LEVELS:
        for level, check, msg in findings:
            if level == lvl and (show_info or level in ("FAIL", "WARN")):
                out.append(f'<div class="row"><span class="badge {lvl}">{lvl}</span>'
                           f'<span class="msg">{_e(msg)}</span><span class="hint">{_e(check)}</span></div>')
    return "".join(out)


def _panel(title, findings, dots=False, show_info=True):
    c = Counter(l for l, _, _ in findings)
    count = " · ".join(f"{c[lvl]} {lvl.lower()}" for lvl in ("FAIL", "WARN") if c[lvl]) or "no issues"
    head = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>' if dots else ""
    body = _rows(findings, show_info) or '<div class="row"><span class="msg">Nothing to report.</span></div>'
    return (f'<section class="panel"><div class="bar">{head}<h2>{_e(title)}</h2>'
            f'<span class="count">{_e(count)}</span></div>{body}</section>')


def _stats(findings):
    c = Counter(l for l, _, _ in findings)
    return '<div class="stats">' + "".join(
        f'<div class="stat {lvl.lower()}"><b>{c.get(lvl, 0)}</b><span>{lvl}</span></div>'
        for lvl in LEVELS) + "</div>"


def _page_block(pg):
    bad = [x for x in pg["findings"] if x[0] in ("FAIL", "WARN")]
    meta = (f'<div class="page-meta"><b>Title ({_e(pg.get("title_length"))}):</b> {_e(pg.get("title"))}<br>'
            f'<b>Meta description ({_e(pg.get("meta_description_length"))}):</b> '
            f'{_e(pg.get("meta_description"))}<br><b>Canonical:</b> {_e(pg.get("canonical"))} · '
            f'<b>Words:</b> {_e(pg.get("word_count"))} · <b>Schema:</b> '
            f'{_e(", ".join(pg.get("schema_types") or []) or "none")}</div>') if "title" in pg else ""
    return (f'<section class="panel"><div class="bar"><h2>{_e(pg["url"])}</h2>'
            f'<span class="count">{len(bad)} issue(s)</span></div>{meta}'
            f'{_rows(pg["findings"]) or ""}</section>')


def _doc(title, kicker, sub, body):
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="color-scheme" content="dark light"><title>{_e(title)}</title>'
            f'<style>{CSS}</style></head><body><div class="wrap"><div class="kicker">{_e(kicker)}</div>'
            f'<h1>{_e(title)}</h1><p class="sub">{_e(sub)}</p>{body}'
            f'<footer>Generated {stamp} by seo_check.py · seo-checklist-skills</footer></div></body></html>')


def render_site(rep):
    sections = rep["sections"]
    all_f = [x for fs in sections.values() for x in fs]
    parts = [_stats(all_f)]
    for i, (name, fs) in enumerate(sections.items()):
        parts.append(_panel(name, fs, dots=(i == 0)))
    manual = "".join(f'<div class="row"><span class="badge Q">?</span><span class="msg">{_e(t)}</span>'
                     f'<span class="hint">{_e(h)}</span></div>' for t, h in MANUAL)
    parts.append(f'<section class="panel"><div class="bar"><h2>Not checkable from outside</h2>'
                 f'<span class="count">verify manually</span></div>{manual}</section>')
    pages = [pg for pg in rep.get("pages", []) if any(x[0] in ("FAIL", "WARN") for x in pg["findings"])]
    if pages:
        inner = "".join(_page_block(pg) for pg in pages)
        parts.append(f'<details><summary>Per-page issues in the sample ({len(pages)} pages)</summary>'
                     f'{inner}</details>')
    sub = f"{rep.get('sitemap_url_count', 0)} sitemap URLs · {len(rep.get('pages', []))} pages sampled"
    return _doc(rep["origin"], "Technical SEO check", sub, "".join(parts))


def render_pages(pages, cross=None):
    all_f = [x for pg in pages for x in pg["findings"]] + list(cross or [])
    parts = [_stats(all_f)]
    if cross:
        parts.append(_panel("Across these pages", cross, dots=True))
    parts += [_page_block(pg) for pg in pages]
    title = pages[0]["url"] if len(pages) == 1 else f"{len(pages)} pages"
    return _doc(title, "On-page SEO check", "Titles, meta, headings, images, schema and more", "".join(parts))
