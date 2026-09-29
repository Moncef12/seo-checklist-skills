#!/usr/bin/env python3
"""
seo_check.py - dependency-free SEO checks used by the seo-checklist skills.

  python3 seo_check.py page URL_OR_FILE [URL_OR_FILE ...] [--psi] [--json]
  python3 seo_check.py site https://example.com [--sample 20] [--crawl 40] [--json]

page  Audits the on-page elements of each URL (or local .html file): title,
      meta description, headings, intro text, images, internal links,
      canonical, robots, structured data, viewport, JS-rendering risk.
      --psi adds Core Web Vitals from the PageSpeed Insights API.

site  Checks the whole site: http/https/www consolidation, robots.txt,
      sitemaps, a sample of sitemap URLs (status, noindex, canonical),
      soft 404s, broken/redirecting internal links and orphan candidates.

Output is a Markdown report on stdout (JSON with --json). Every finding is
tagged FAIL / WARN / INFO / PASS so the caller can prioritise. Only the
Python 3.9+ standard library is used, so it runs anywhere.

This file is maintained in shared/ and copied into each skill's scripts/
folder by `make sync`. Edit the shared copy.
"""
import argparse
import gzip
import http.cookiejar
import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import uuid
import xml.etree.ElementTree as ET
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

__version__ = "1.0.0"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 seo-checklist-skills")
MAX_BYTES = 5_000_000
LEVELS = ("FAIL", "WARN", "INFO", "PASS")
ICON = {"FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️", "PASS": "✅"}


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # record hops ourselves
        return None


def _ssl_context(insecure=False):
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    try:  # python.org builds on macOS often ship without a CA bundle
        import certifi
        ctx.load_verify_locations(certifi.where())
    except Exception:
        pass
    return ctx


def configure(insecure=False):
    global _CTX
    _CTX = _ssl_context(insecure)


_CTX = None
configure()

CERT_HINT = ("SSL certificate verification failed on this machine. Fix: `pip install certifi`, or on a "
             "python.org macOS install run 'Install Certificates.command'; or re-run with --insecure.")


_THROTTLE = {"delay": 0.0, "next": 0.0}
_THROTTLE_LOCK = threading.Lock()


def set_delay(seconds):
    _THROTTLE["delay"] = max(0.0, seconds)


def _throttle():
    """Space request starts at least `delay` seconds apart across all threads."""
    if _THROTTLE["delay"] <= 0:
        return
    with _THROTTLE_LOCK:
        now = time.monotonic()
        start = max(now, _THROTTLE["next"])
        _THROTTLE["next"] = start + _THROTTLE["delay"]
    if start > now:
        time.sleep(start - now)


def fetch(url, timeout=15, max_redirects=10, max_bytes=MAX_BYTES):
    """GET a URL, following redirects manually so the chain is recorded."""
    chain, current, t0 = [], url, time.time()
    # fresh cookie jar per fetch: some sites set a cookie then redirect back
    opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=_CTX),
                                         urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    for _ in range(max_redirects + 1):
        _throttle()
        req = urllib.request.Request(current, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip",
        })
        body = b""
        try:
            resp = opener.open(req, timeout=timeout)
            status, headers = resp.status, resp.headers
            body = resp.read(max_bytes)
        except urllib.error.HTTPError as e:
            status, headers = e.code, e.headers
            if 300 <= status < 400 and headers.get("Location"):
                chain.append((current, status))
                current = urllib.parse.urljoin(current, headers["Location"])
                continue
            try:
                body = e.read(max_bytes)
            except Exception:
                pass
        except Exception as e:  # DNS, TLS, timeout...
            return {"url": url, "final_url": current, "status": None, "chain": chain,
                    "headers": {}, "body": b"", "error": f"{type(e).__name__}: {e}",
                    "elapsed": round(time.time() - t0, 2)}
        if (headers.get("Content-Encoding") or "").lower() == "gzip" and body:
            try:
                body = gzip.decompress(body)
            except Exception:
                pass
        return {"url": url, "final_url": current, "status": status, "chain": chain,
                "headers": {k.lower(): v for k, v in headers.items()}, "body": body,
                "error": None, "elapsed": round(time.time() - t0, 2)}
    return {"url": url, "final_url": current, "status": None, "chain": chain, "headers": {},
            "body": b"", "error": "too many redirects", "elapsed": round(time.time() - t0, 2)}


def decode(res):
    ct = res["headers"].get("content-type", "")
    m = re.search(r"charset=([\w-]+)", ct, re.I)
    try:
        return res["body"].decode(m.group(1) if m else "utf-8", errors="replace")
    except LookupError:
        return res["body"].decode("utf-8", errors="replace")


def is_html(res):
    ct = res["headers"].get("content-type", "")
    return "html" in ct or (not ct and res["body"][:500].lstrip().lower().startswith(b"<"))


def load_local(path):
    with open(path, "rb") as f:
        body = f.read()
    return {"url": path, "final_url": path, "status": 200, "chain": [],
            "headers": {"content-type": "text/html; charset=utf-8"}, "body": body,
            "error": None, "elapsed": 0}


# --------------------------------------------------------------------------
# HTML parsing
# --------------------------------------------------------------------------

class PageParser(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = None
        self.titles = 0
        self.meta = {}
        self.links = []
        self.headings = []
        self.images = []
        self.anchors = []
        self.jsonld_raw = []
        self.scripts = 0
        self.text = []
        self.intro = []
        self._in_title = False
        self._title_buf = []
        self._heading = None
        self._anchor = None
        self._jsonld = None
        self._skip = 0
        self._h1_done = False
        self.empty_app_root = False
        self._root_watch = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title" and not self._skip:
            self.titles += 1
            self._in_title = self.title is None
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or a.get("http-equiv") or "").lower()
            if key:
                self.meta.setdefault(key, a.get("content", ""))
            if a.get("charset"):
                self.meta.setdefault("charset", a["charset"])
        elif tag == "link":
            self.links.append(a)
        elif re.fullmatch(r"h[1-6]", tag) and not self._skip:
            self._heading = [int(tag[1]), []]
        elif tag == "img":
            self.images.append(a)
        elif tag == "a":
            self._anchor = [a.get("href", ""), [], a.get("rel", "").lower()]
        elif tag == "script":
            self.scripts += 1
            if "ld+json" in a.get("type", "").lower():
                self._jsonld = []
            else:
                self._skip += 1
        elif tag in self.SKIP:
            self._skip += 1
        elif tag == "div" and a.get("id") in ("root", "app", "__next", "__nuxt", "svelte"):
            self._root_watch = {"depth": 0, "text": 0}

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = " ".join("".join(self._title_buf).split())
        elif re.fullmatch(r"h[1-6]", tag) and self._heading:
            level, buf = self._heading
            self.headings.append((level, " ".join("".join(buf).split())))
            self._heading = None
            if level == 1:
                self._h1_done = True
        elif tag == "a" and self._anchor:
            href, buf, rel = self._anchor
            self.anchors.append((href, " ".join("".join(buf).split()), rel))
            self._anchor = None
        elif tag == "script":
            if self._jsonld is not None:
                self.jsonld_raw.append("".join(self._jsonld))
                self._jsonld = None
            elif self._skip:
                self._skip -= 1
        elif tag in self.SKIP and self._skip:
            self._skip -= 1
        elif tag == "div" and self._root_watch is not None:
            if self._root_watch["text"] < 20:
                self.empty_app_root = True
            self._root_watch = None

    def handle_data(self, data):
        if self._jsonld is not None:
            self._jsonld.append(data)
            return
        if self._in_title:
            self._title_buf.append(data)
            return
        if self._skip:
            return
        self.text.append(data)
        if self._root_watch is not None:
            self._root_watch["text"] += len(data.strip())
        if self._heading:
            self._heading[1].append(data)
        if self._anchor:
            self._anchor[1].append(data)
        if self._h1_done and not self._heading and len(self.intro) < 80:
            self.intro.extend(data.split())


def parse_html(html):
    p = PageParser()
    try:
        p.feed(html)
        p.close()
    except Exception:
        pass
    return p


def jsonld_types(raw_blocks):
    types, date_modified, errors = [], False, 0

    def walk(node):
        nonlocal date_modified
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, list):
                types.extend(str(x) for x in t)
            elif t:
                types.append(str(t))
            if "dateModified" in node:
                date_modified = True
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for raw in raw_blocks:
        try:
            walk(json.loads(raw))
        except Exception:
            errors += 1
    return types, date_modified, errors


# --------------------------------------------------------------------------
# Page analysis
# --------------------------------------------------------------------------

def same_site(a, b):
    ha = urllib.parse.urlparse(a).hostname or ""
    hb = urllib.parse.urlparse(b).hostname or ""
    return ha.removeprefix("www.") == hb.removeprefix("www.")


def url_issues(url):
    issues = []
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        return issues
    if any(c.isupper() for c in p.path):
        issues.append("uppercase letters in path")
    if "_" in p.path:
        issues.append("underscores in path (hyphens are preferred)")
    if len(urllib.parse.parse_qs(p.query)) >= 2:
        issues.append("2+ query parameters")
    if len(url) > 100:
        issues.append(f"long URL ({len(url)} chars)")
    if re.search(r"\.(php|aspx?|jsp|cfm)$", p.path, re.I):
        issues.append("technology file extension in URL")
    if re.search(r"/\d{4,}(/|$)", p.path) and not re.search(r"/20\d\d/", p.path):
        issues.append("opaque numeric ID in path")
    return issues


def analyze_page(res, local=False):
    """Return a dict of metrics plus findings [(level, check, message)]."""
    url = res["url"]
    f = []
    out = {"url": url, "final_url": res["final_url"], "status": res["status"],
           "error": res["error"], "elapsed": res["elapsed"], "findings": f,
           "redirects": [f"{s} {u}" for u, s in res["chain"]]}

    if res["error"]:
        f.append(("FAIL", "fetch", f"Could not fetch: {res['error']}"))
        if "CERTIFICATE" in res["error"]:
            f.append(("INFO", "fetch", CERT_HINT))
        return out
    if res["status"] != 200:
        f.append(("FAIL", "status", f"HTTP {res['status']} (expected 200)"))
    if len(res["chain"]) > 1:
        f.append(("WARN", "redirect-chain",
                  f"{len(res['chain'])}-hop redirect chain: " +
                  " -> ".join([u for u, _ in res["chain"]] + [res["final_url"]])))
    elif res["chain"]:
        code = res["chain"][0][1]
        lvl = "WARN" if code in (302, 303, 307) else "INFO"
        f.append((lvl, "redirect", f"Redirects ({code}) to {res['final_url']}"
                  + (" - use 301/308 for permanent moves" if lvl == "WARN" else "")))
    if not is_html(res):
        f.append(("INFO", "content-type", f"Not HTML ({res['headers'].get('content-type')})"))
        return out

    p = parse_html(decode(res))
    base = res["final_url"]
    words = " ".join(p.text).split()
    out["word_count"] = len(words)

    # Indexability
    robots = " ".join(filter(None, [p.meta.get("robots", ""), p.meta.get("googlebot", ""),
                                    res["headers"].get("x-robots-tag", "")])).lower()
    out["noindex"] = "noindex" in robots or "none" in robots.split(",")
    if out["noindex"]:
        f.append(("WARN", "noindex", f"Page is noindex ({robots.strip()}) - fine only if intentional"))
    canon = [l.get("href", "") for l in p.links if "canonical" in l.get("rel", "").lower().split()]
    out["canonical"] = urllib.parse.urljoin(base, canon[0]) if canon else None
    if len(canon) > 1:
        f.append(("FAIL", "canonical", f"{len(canon)} canonical tags - Google may ignore all of them"))
    elif not canon:
        f.append(("WARN", "canonical", "No canonical tag"))
    elif not local and out["canonical"].rstrip("/") != base.rstrip("/"):
        f.append(("INFO", "canonical", f"Canonical points elsewhere: {out['canonical']}"))
    else:
        f.append(("PASS", "canonical", "Self-referencing canonical"))

    # Title
    out["title"] = p.title
    tl = len(p.title or "")
    out["title_length"] = tl
    if not p.title:
        f.append(("FAIL", "title", "Missing <title>"))
    elif tl < 30 or tl > 70:
        f.append(("WARN", "title", f"Title is {tl} chars (target 50-60): \"{p.title}\""))
    elif tl < 50 or tl > 60:
        f.append(("INFO", "title", f"Title is {tl} chars (target 50-60): \"{p.title}\""))
    else:
        f.append(("PASS", "title", f"Title is {tl} chars"))
    if p.titles > 1:
        f.append(("WARN", "title", f"{p.titles} <title> tags"))

    # Meta description
    desc = p.meta.get("description")
    out["meta_description"] = desc
    dl = len(desc or "")
    out["meta_description_length"] = dl
    if not desc:
        f.append(("WARN", "meta-description", "Missing meta description"))
    elif dl < 70 or dl > 170:
        f.append(("WARN", "meta-description", f"Meta description is {dl} chars (target ~120-160)"))
    else:
        f.append(("PASS", "meta-description", f"Meta description is {dl} chars"))

    # Headings
    out["headings"] = [f"H{lvl}: {txt}" for lvl, txt in p.headings[:40]]
    h1s = [t for lvl, t in p.headings if lvl == 1]
    if not h1s:
        f.append(("FAIL", "h1", "No H1"))
    elif len(h1s) > 1:
        f.append(("WARN", "h1", f"{len(h1s)} H1s: {h1s[:3]}"))
    else:
        f.append(("PASS", "h1", f"One H1: \"{h1s[0]}\""))
    prev, skips = 0, []
    for lvl, txt in p.headings:
        if prev and lvl > prev + 1:
            skips.append(f"H{prev}->H{lvl} (\"{txt[:40]}\")")
        prev = lvl
    if skips:
        f.append(("WARN", "heading-order", "Skipped heading levels: " + "; ".join(skips[:5])))
    out["intro"] = " ".join(p.intro[:60])

    # Mobile / language
    if "viewport" not in p.meta:
        f.append(("FAIL", "viewport", "No meta viewport - page will not render mobile-friendly"))
    if not p.lang:
        f.append(("INFO", "lang", "No <html lang> attribute"))

    # Images
    imgs = p.images
    no_alt = [i.get("src", "")[:80] for i in imgs if "alt" not in i]
    no_dims = [i for i in imgs if not (i.get("width") and i.get("height"))]
    legacy = [i for i in imgs if re.search(r"\.(jpe?g|png|gif|bmp)(\?|$)", i.get("src", ""), re.I)]
    out["images"] = {"total": len(imgs), "missing_alt": len(no_alt), "missing_dimensions": len(no_dims),
                     "legacy_format": len(legacy),
                     "lazy": sum(1 for i in imgs if i.get("loading") == "lazy")}
    if no_alt:
        f.append(("WARN", "img-alt", f"{len(no_alt)}/{len(imgs)} images have no alt attribute, e.g. {no_alt[:3]}"))
    elif imgs:
        f.append(("PASS", "img-alt", f"All {len(imgs)} images have an alt attribute"))
    if no_dims:
        f.append(("INFO", "img-dimensions", f"{len(no_dims)} images lack width/height (layout shift risk)"))
    if legacy:
        f.append(("INFO", "img-format", f"{len(legacy)} images are JPG/PNG/GIF - consider WebP/AVIF"))
    if len(imgs) > 3 and not out["images"]["lazy"]:
        f.append(("INFO", "img-lazy", "No loading=\"lazy\" on any image"))

    # Links
    internal, external, nofollow_int = [], [], 0
    for href, text, rel in p.anchors:
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absu = urllib.parse.urljoin(base, href).split("#")[0]
        if local or same_site(absu, base):
            internal.append((absu, text))
            if "nofollow" in rel:
                nofollow_int += 1
        else:
            external.append(absu)
    out["internal_links"] = len(internal)
    out["external_links"] = len(external)
    out["_internal_urls"] = [u for u, _ in internal]
    generic = [t for _, t in internal if t.lower() in ("click here", "here", "read more", "learn more", "more")]
    if not internal:
        f.append(("WARN", "internal-links", "No internal links found in the HTML"))
    if nofollow_int:
        f.append(("WARN", "internal-links", f"{nofollow_int} internal links are nofollow"))
    if generic:
        f.append(("INFO", "anchor-text", f"{len(generic)} internal links use generic anchor text (\"{generic[0]}\")"))

    # Structured data
    types, date_mod, bad = jsonld_types(p.jsonld_raw)
    out["schema_types"] = sorted(set(types))
    out["has_date_modified"] = date_mod
    if bad:
        f.append(("FAIL", "schema", f"{bad} JSON-LD block(s) are invalid JSON"))
    if not types:
        f.append(("WARN", "schema", "No JSON-LD structured data"))
    else:
        f.append(("PASS", "schema", "JSON-LD types: " + ", ".join(out["schema_types"])))
    if "BreadcrumbList" not in types and not local and urllib.parse.urlparse(base).path not in ("", "/"):
        f.append(("INFO", "breadcrumbs", "No BreadcrumbList schema on this inner page"))

    # Social
    missing_og = [k for k in ("og:title", "og:description", "og:image") if k not in p.meta]
    if missing_og:
        f.append(("INFO", "open-graph", "Missing " + ", ".join(missing_og)))

    # Thin / JS-rendered content
    if len(words) < 80 and (p.scripts >= 3 or p.empty_app_root):
        f.append(("WARN", "js-rendering",
                  f"Only {len(words)} words in raw HTML with {p.scripts} scripts - content is probably "
                  "client-side rendered. Verify with GSC URL Inspection > View crawled page, "
                  "or use SSR/SSG for indexable content."))
    elif len(words) < 300:
        f.append(("INFO", "thin-content", f"{len(words)} words of visible text"))

    # URL hygiene
    if not local:
        for issue in url_issues(base):
            f.append(("INFO", "url", issue))
        if res["elapsed"] > 2.5:
            f.append(("INFO", "response-time", f"HTML took {res['elapsed']}s to download"))
    return out


def pagespeed(url, strategy="mobile"):
    """Core Web Vitals via the public PageSpeed Insights API (keyless, rate-limited)."""
    q = urllib.parse.urlencode({"url": url, "strategy": strategy, "category": "performance"})
    key = os.environ.get("PSI_API_KEY")
    if key:
        q += "&key=" + key
    try:
        req = urllib.request.Request(
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + q,
            headers={"User-Agent": UA})
        data = json.loads(urllib.request.urlopen(req, timeout=90, context=_CTX).read())
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    field = data.get("loadingExperience", {}).get("metrics", {})
    pick = lambda k: field.get(k, {}).get("percentile")
    lh = data.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    return {
        "field_data": bool(field),
        "field_overall": data.get("loadingExperience", {}).get("overall_category"),
        "lcp_ms": pick("LARGEST_CONTENTFUL_PAINT_MS"),
        "inp_ms": pick("INTERACTION_TO_NEXT_PAINT"),
        "cls": None if pick("CUMULATIVE_LAYOUT_SHIFT_SCORE") is None
        else pick("CUMULATIVE_LAYOUT_SHIFT_SCORE") / 100,
        "lab_performance_score": round((lh.get("categories", {}).get("performance", {}).get("score") or 0) * 100),
        "lab_lcp": audits.get("largest-contentful-paint", {}).get("displayValue"),
        "lab_cls": audits.get("cumulative-layout-shift", {}).get("displayValue"),
        "lab_tbt": audits.get("total-blocking-time", {}).get("displayValue"),
    }


def cwv_findings(psi):
    f = []
    if "error" in psi:
        return [("INFO", "cwv", f"PageSpeed Insights unavailable: {psi['error']} (set PSI_API_KEY to raise quota)")]
    if not psi["field_data"]:
        f.append(("INFO", "cwv", "No CrUX field data (low traffic) - using lab data only"))
    else:
        for name, val, good, poor, unit in (("LCP", psi["lcp_ms"], 2500, 4000, "ms"),
                                            ("INP", psi["inp_ms"], 200, 500, "ms"),
                                            ("CLS", psi["cls"], 0.1, 0.25, "")):
            if val is None:
                continue
            lvl = "PASS" if val <= good else ("WARN" if val <= poor else "FAIL")
            f.append((lvl, "cwv", f"{name} p75 = {val}{unit} (good <= {good}{unit})"))
    f.append(("INFO", "cwv", f"Lighthouse mobile performance {psi['lab_performance_score']}/100 "
                             f"(LCP {psi['lab_lcp']}, CLS {psi['lab_cls']}, TBT {psi['lab_tbt']})"))
    return f


# --------------------------------------------------------------------------
# Site checks
# --------------------------------------------------------------------------

def normalize_origin(url):
    if "://" not in url:
        url = "https://" + url
    p = urllib.parse.urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def parse_sitemap(xml_bytes):
    """Return (kind, [(loc, lastmod)]) where kind is 'index' or 'urlset'."""
    if xml_bytes[:2] == b"\x1f\x8b":
        xml_bytes = gzip.decompress(xml_bytes)
    root = ET.fromstring(xml_bytes)
    tag = root.tag.split("}")[-1]
    entries = []
    for node in root:
        loc = lastmod = None
        for child in node:
            name = child.tag.split("}")[-1]
            if name == "loc":
                loc = (child.text or "").strip()
            elif name == "lastmod":
                lastmod = (child.text or "").strip()
        if loc:
            entries.append((loc, lastmod))
    return ("index" if tag == "sitemapindex" else "urlset"), entries


def check_site(start, sample=20, crawl=40, workers=8):
    origin = normalize_origin(start)
    parsed = urllib.parse.urlparse(origin)
    bare = parsed.hostname.removeprefix("www.")
    port = f":{parsed.port}" if parsed.port else ""
    report = {"origin": origin, "sections": {}}
    S = report["sections"]

    # 1. Host / protocol consolidation
    f = []
    is_ip = bool(re.fullmatch(r"[\d.]+|\[[0-9a-f:]+\]|localhost", bare))
    hosts = (bare,) if is_ip else (bare, "www." + bare)
    variants = [f"{s}://{h}{port}/" for s in ("http", "https") for h in hosts]
    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(lambda u: fetch(u, max_bytes=200_000), variants))
    finals = {}
    for r in results:
        if r["error"]:
            f.append(("INFO", "hosts", f"{r['url']} -> unreachable ({r['error'][:60]})"))
            continue
        hops = " -> ".join(f"{u} [{s}]" for u, s in r["chain"]) or "no redirect"
        finals[r["url"]] = r["final_url"]
        f.append(("INFO", "hosts", f"{r['url']} -> {r['final_url']} [{r['status']}] via {hops}"))
        if any(s in (302, 303, 307) for _, s in r["chain"]):
            f.append(("WARN", "hosts", f"{r['url']} uses a temporary redirect - use 301/308"))
        if len(r["chain"]) > 1:
            f.append(("WARN", "hosts", f"{r['url']} takes {len(r['chain'])} hops - collapse to one"))
    if not finals:
        errs = " ".join(r["error"] or "" for r in results)
        sys.exit(f"Site unreachable: {results[-1]['error']}\n" + (CERT_HINT if "CERTIFICATE" in errs else ""))
    distinct = {u.rstrip("/") for u in finals.values()}
    if len(distinct) > 1:
        f.append(("FAIL", "hosts", f"Variants resolve to {len(distinct)} different URLs {sorted(distinct)} "
                                   "- duplicate site versions; 301 all to one canonical origin"))
    elif distinct:
        canonical_origin = normalize_origin(next(iter(distinct)))
        f.append(("PASS", "hosts", f"All reachable variants consolidate to {canonical_origin}"))
        if canonical_origin.startswith("http://") and not is_ip:
            f.append(("FAIL", "https", "Site does not use HTTPS"))
        origin = canonical_origin
        report["origin"] = origin
    S["Hosts & HTTPS"] = f

    # 2. robots.txt
    f = []
    rp = urllib.robotparser.RobotFileParser()
    robots = fetch(origin + "/robots.txt", max_bytes=500_000)
    sitemap_urls = []
    if robots["status"] == 200 and not is_html(robots):
        txt = decode(robots)
        rp.parse(txt.splitlines())
        sitemap_urls = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", txt)
        f.append(("PASS", "robots", f"robots.txt found ({len(txt.splitlines())} lines, "
                                    f"{len(sitemap_urls)} Sitemap: lines)"))
        if not rp.can_fetch("Googlebot", origin + "/"):
            f.append(("FAIL", "robots", "robots.txt blocks Googlebot from the homepage"))
        dis = re.findall(r"(?im)^\s*disallow:\s*(\S+)", txt)
        if dis:
            f.append(("INFO", "robots", "Disallow rules: " + ", ".join(dis[:15])))
        for asset in ("/*.js", "/*.css", "/_next/", "/assets/", "/static/", "/wp-includes/"):
            if any(d.rstrip("*") == asset.rstrip("*") for d in dis):
                f.append(("WARN", "robots", f"robots.txt disallows {asset} - Google needs JS/CSS to render"))
        if not sitemap_urls:
            f.append(("WARN", "robots", "No Sitemap: line in robots.txt"))
    else:
        rp.parse([])
        f.append(("WARN", "robots", f"No usable robots.txt (HTTP {robots['status']}) - "
                                    "add one with a Sitemap: line"))
    S["robots.txt"] = f

    # 3. Sitemaps
    f = []
    declared = set(sitemap_urls)
    if not sitemap_urls:  # guess common locations; stay quiet if a guess is wrong
        sitemap_urls = [origin + p for p in ("/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml")]
    urls, lastmods, seen_maps, queue, found = [], 0, set(), deque(sitemap_urls), []
    while queue and len(seen_maps) < 25 and len(urls) < 50_000:
        sm = queue.popleft()
        if sm in seen_maps:
            continue
        seen_maps.add(sm)
        r = fetch(sm, max_bytes=50_000_000)
        if r["status"] != 200 or not r["body"]:
            if sm in declared:
                f.append(("FAIL", "sitemap", f"Declared sitemap {sm} returns {r['status'] or r['error']}"))
            continue
        try:
            kind, entries = parse_sitemap(r["body"])
        except Exception:
            if sm in declared:
                f.append(("FAIL", "sitemap", f"{sm} is not valid sitemap XML"))
            continue
        found.append(sm)
        if kind == "index":
            declared.update(loc for loc, _ in entries)
            queue.extend(loc for loc, _ in entries)
        else:
            urls.extend(loc for loc, _ in entries)
            lastmods += sum(1 for _, lm in entries if lm)
    urls = list(dict.fromkeys(urls))
    report["sitemap_url_count"] = len(urls)
    if not urls:
        f.append(("FAIL", "sitemap", "No XML sitemap found - create one and submit it to GSC and Bing"))
    else:
        f.append(("PASS", "sitemap", f"{len(urls)} URLs across {len(found)} sitemap file(s)"))
        if lastmods < len(urls) * 0.5:
            f.append(("INFO", "sitemap", f"Only {lastmods}/{len(urls)} URLs have <lastmod>"))
        off = [u for u in urls if not same_site(u, origin)]
        if off:
            f.append(("WARN", "sitemap", f"{len(off)} sitemap URLs are on another host, e.g. {off[0]}"))
        insecure = [u for u in urls if u.startswith("http://") and origin.startswith("https://")]
        if insecure:
            f.append(("WARN", "sitemap", f"{len(insecure)} sitemap URLs use http://"))
    f.append(("INFO", "sitemap", "Confirm the sitemap is submitted in GSC (Sitemaps report) and "
                                 "Bing Webmaster Tools - that cannot be checked from outside."))
    S["Sitemaps"] = f

    # 4. Sample of sitemap URLs + homepage
    f = []
    step = max(1, len(urls) // max(sample, 1))
    sample_urls, seen_norm = [], set()
    for u in [origin + "/"] + urls[::step][:sample]:
        if u.rstrip("/") not in seen_norm:
            seen_norm.add(u.rstrip("/"))
            sample_urls.append(u)
    with ThreadPoolExecutor(workers) as ex:
        pages = list(ex.map(lambda u: analyze_page(fetch(u)), sample_urls))
    report["pages"] = pages
    in_sitemap = set(urls)
    for pg in pages:
        u = pg["url"]
        listed = u in in_sitemap
        if pg["error"] or pg["status"] != 200:
            f.append(("FAIL" if listed else "WARN", "indexability",
                      f"{u} -> {pg['status'] or pg['error']}" + (" (listed in sitemap)" if listed else "")))
            continue
        if pg["redirects"] and listed:
            f.append(("WARN", "indexability", f"Sitemap lists a redirecting URL: {u} -> {pg['final_url']}"))
        if pg.get("noindex") and listed:
            f.append(("FAIL", "indexability", f"Sitemap lists a noindex page: {u}"))
        if not rp.can_fetch("Googlebot", u):
            f.append(("FAIL", "indexability", f"Blocked by robots.txt: {u}"))
        c = pg.get("canonical")
        if listed and c and c.rstrip("/") != pg["final_url"].rstrip("/"):
            f.append(("WARN", "indexability", f"Sitemap URL canonicalises elsewhere: {u} -> {c}"))
    ok = [p for p in pages if p["status"] == 200 and "word_count" in p]
    titles = Counter(p.get("title") for p in ok if p.get("title"))
    descs = Counter(p.get("meta_description") for p in ok if p.get("meta_description"))
    dup_t = [t for t, n in titles.items() if n > 1]
    dup_d = [d for d, n in descs.items() if n > 1]
    if dup_t:
        f.append(("WARN", "duplicates",
                  f"{len(dup_t)} titles are shared by several sampled pages, e.g. \"{dup_t[0]}\""))
    if dup_d:
        f.append(("WARN", "duplicates", f"{len(dup_d)} meta descriptions are duplicated, e.g. \"{dup_d[0][:80]}\""))
    agg = Counter()
    for p in ok:
        for lvl, check, _ in p["findings"]:
            if lvl in ("FAIL", "WARN"):
                agg[(lvl, check)] += 1
    for (lvl, check), n in agg.most_common():
        f.append((lvl, check, f"{n}/{len(ok)} sampled pages: {check} issue (see per-page detail)"))
    if not any(lvl in ("FAIL", "WARN") for lvl, _, _ in f):
        f.append(("PASS", "indexability", f"All {len(pages)} sampled URLs are 200, indexable and self-canonical"))
    S[f"Sample of {len(pages)} URLs"] = f

    # 5. Soft 404
    f = []
    r = fetch(f"{origin}/seo-check-{uuid.uuid4().hex[:10]}", max_bytes=200_000)
    if r["status"] == 200:
        f.append(("FAIL", "soft-404", "Non-existent URLs return 200 (soft 404) - return a real 404 status"))
    elif r["status"] in (404, 410):
        f.append(("PASS", "soft-404", f"Missing pages return {r['status']}"))
    else:
        f.append(("INFO", "soft-404", f"Missing pages return {r['status'] or r['error']} "
                                      f"(final URL {r['final_url']})"))
    S["404 handling"] = f

    # 6. Crawl for broken links, redirects, orphans
    f = []
    seen, linked, sources, skipped = set(), set(), {}, set()
    queue = deque([origin + "/"])
    crawled = 0
    allowed = lambda u: rp.can_fetch(UA, u)  # this crawler obeys robots.txt itself
    while queue and crawled < crawl:
        batch = []
        while queue and len(batch) < workers and crawled + len(batch) < crawl:
            u = queue.popleft()
            key = u.rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            if allowed(u):
                batch.append(u)
            else:
                skipped.add(u)
        if not batch:
            break
        with ThreadPoolExecutor(workers) as ex:
            got = list(ex.map(fetch, batch))
        for r in got:
            crawled += 1
            if r["status"] != 200 or not is_html(r):
                continue
            a = analyze_page(r)
            for link in a.get("_internal_urls", []):
                link = link.split("?")[0] if "?" in link and "page=" not in link else link
                if not link.startswith(("http://", "https://")):
                    continue
                if re.search(r"\.(jpg|jpeg|png|gif|webp|avif|svg|pdf|zip|mp4|css|js)$", link, re.I):
                    continue
                linked.add(link.rstrip("/"))
                sources.setdefault(link, r["url"])
                if link.rstrip("/") not in seen:
                    queue.append(link)
    frontier_done = not any(u.rstrip("/") not in seen for u in queue)
    fresh = [u for u in sources if u.rstrip("/") not in seen and allowed(u)]
    targets = fresh[:200] + [u for u in sources if u.rstrip("/") in seen and allowed(u)][:200]
    with ThreadPoolExecutor(workers) as ex:
        checks = list(ex.map(lambda u: fetch(u, max_bytes=50_000), targets))
    broken = [(c["url"], c["status"] or c["error"]) for c in checks
              if c["error"] or (c["status"] or 0) >= 400]
    redirected = [(c["url"], c["final_url"], c["chain"]) for c in checks if c["chain"] and not c["error"]]
    for u, st in broken[:25]:
        f.append(("FAIL", "broken-link", f"{u} -> {st} (linked from {sources.get(u)})"))
    for u, dest, chain in redirected[:15]:
        if dest.rstrip("/") == u.rstrip("/"):
            f.append(("WARN", "cookie-redirect", f"{u} redirects to itself to set a cookie (linked from "
                                                 f"{sources.get(u)}). Googlebot crawls without cookies - check it "
                                                 "renders in GSC URL Inspection, or noindex it if it is an app page"))
        else:
            hops = " -> ".join(str(code) for _, code in chain)
            kind = f"{len(chain)}-hop redirect chain ({hops})" if len(chain) > 1 else f"a {hops} redirect"
            f.append(("WARN", "internal-redirect", f"Internal link {u} goes through {kind} to {dest} (linked from "
                                                   f"{sources.get(u)}) - link to the final URL"))
    if not broken:
        f.append(("PASS", "broken-link", f"No broken internal links among {len(targets)} checked"))
    if skipped:
        f.append(("INFO", "crawl", f"Skipped {len(skipped)} URLs disallowed by robots.txt"))
    f.append(("INFO", "crawl", f"Crawled {crawled} pages, found {len(sources)} unique internal links"
                               + ("" if frontier_done
                                  else f" (stopped at --crawl {crawl}; raise it for full coverage)")))
    orphans = [u for u in urls if u.rstrip("/") not in linked and u.rstrip("/") != origin]
    if urls and orphans:
        lvl = "WARN" if frontier_done else "INFO"
        note = "" if frontier_done else " - candidates only, the crawl did not cover the whole site"
        f.append((lvl, "orphans", f"{len(orphans)} sitemap URLs were not linked from any crawled page{note}. "
                                  f"e.g. {orphans[:5]}"))
    S["Links & orphans"] = f
    return report


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_findings(findings, show_pass=True):
    lines = []
    for lvl in LEVELS:
        for l, check, msg in findings:
            if l == lvl and (show_pass or l != "PASS"):
                lines.append(f"- {ICON[l]} **{l}** `{check}` {msg}")
    return lines


def summarize(findings):
    c = Counter(l for l, _, _ in findings)
    return " | ".join(f"{ICON[l]} {c.get(l, 0)} {l}" for l in LEVELS)


def render_page(pg):
    lines = [f"## {pg['url']}", ""]
    if pg.get("title") is not None or pg.get("word_count") is not None:
        lines += [f"- **Status:** {pg['status']}  **Words:** {pg.get('word_count')}  "
                  f"**Internal links:** {pg.get('internal_links')}  **External:** {pg.get('external_links')}",
                  f"- **Title ({pg.get('title_length')}):** {pg.get('title')}",
                  f"- **Meta description ({pg.get('meta_description_length')}):** {pg.get('meta_description')}",
                  f"- **Canonical:** {pg.get('canonical')}",
                  f"- **Schema:** {', '.join(pg.get('schema_types') or []) or 'none'}"
                  f"  (dateModified: {'yes' if pg.get('has_date_modified') else 'no'})",
                  f"- **Intro after H1:** {pg.get('intro') or '(none found)'}", ""]
        if pg.get("headings"):
            lines += ["<details><summary>Heading outline</summary>", ""]
            lines += [f"    {h}" for h in pg["headings"]] + ["", "</details>", ""]
    lines += [summarize(pg["findings"]), ""] + render_findings(pg["findings"]) + [""]
    return "\n".join(lines)


def render_site(rep):
    all_f = [x for fs in rep["sections"].values() for x in fs]
    lines = [f"# Technical SEO check: {rep['origin']}", "",
             f"**Summary:** {summarize(all_f)}", ""]
    for name, fs in rep["sections"].items():
        lines += [f"## {name}", ""] + render_findings(fs) + [""]
    lines += ["## Per-page issues in the sample", ""]
    for pg in rep.get("pages", []):
        bad = [x for x in pg["findings"] if x[0] in ("FAIL", "WARN")]
        if bad:
            lines += [f"**{pg['url']}**"] + render_findings(bad) + [""]
    lines += ["## Not checkable from outside (verify manually)", "",
              "- GSC + GA4 installed and verified; GSC Page indexing report reviewed",
              "- Sitemap submitted to GSC and Bing Webmaster Tools",
              "- Core Web Vitals field data: run `page URL --psi` on key templates or open GSC > Core Web Vitals",
              "- Rich results: test key templates at https://search.google.com/test/rich-results", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("page", help="audit individual pages")
    pp.add_argument("targets", nargs="+", help="URLs or local .html files")
    pp.add_argument("--psi", action="store_true", help="add Core Web Vitals from PageSpeed Insights")
    pp.add_argument("--json", action="store_true")
    sp = sub.add_parser("site", help="site-wide technical checks")
    sp.add_argument("url")
    sp.add_argument("--sample", type=int, default=20, help="sitemap URLs to inspect (default 20)")
    sp.add_argument("--crawl", type=int, default=40, help="pages to crawl for links (default 40)")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--workers", type=int, default=8, help="parallel requests (default 8)")
    for p in (pp, sp):
        p.add_argument("--insecure", action="store_true", help="skip TLS certificate verification")
        p.add_argument("--delay", type=float, default=0.0,
                       help="minimum seconds between requests (be gentle with small servers)")
        p.add_argument("--fail-on", choices=["FAIL", "WARN"],
                       help="exit 1 if any finding at this level (or worse) - for CI pipelines")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)
    configure(args.insecure)
    set_delay(args.delay)

    if args.cmd == "page":
        pages = []
        for t in args.targets:
            local = os.path.exists(t)
            if not local and "://" not in t:
                t = "https://" + t
            pg = analyze_page(load_local(t) if local else fetch(t), local=local)
            if args.psi and not local:
                pg["cwv"] = pagespeed(pg["final_url"])
                pg["findings"].extend(cwv_findings(pg["cwv"]))
            pg.pop("_internal_urls", None)
            pages.append(pg)
        if args.json:
            print(json.dumps(pages, indent=2, default=str))
        else:
            print("# On-page SEO check\n")
            for pg in pages:
                print(render_page(pg))
        return exit_code([x for pg in pages for x in pg["findings"]], args.fail_on)

    rep = check_site(args.url, sample=args.sample, crawl=args.crawl, workers=max(1, args.workers))
    for pg in rep.get("pages", []):
        pg.pop("_internal_urls", None)
    print(json.dumps(rep, indent=2, default=str) if args.json else render_site(rep))
    return exit_code([x for fs in rep["sections"].values() for x in fs], args.fail_on)


def exit_code(findings, fail_on):
    if not fail_on:
        return 0
    bad = {"FAIL"} if fail_on == "FAIL" else {"FAIL", "WARN"}
    return 1 if any(lvl in bad for lvl, _, _ in findings) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
