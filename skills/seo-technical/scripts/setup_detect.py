"""
setup_detect.py - evidence for checklist items T1 (GSC + GA4) and T2 (sitemap to GSC and Bing).

Search Console and Bing Webmaster Tools can't be read from outside, but their footprints can:

  detect_tags(html, meta)  GA4 / GTM / legacy Universal Analytics tags, other analytics,
                           Google consent mode, and site-verification meta tags.
  dns_txt(name)            TXT records over DNS-over-HTTPS (Google, then Cloudflare), which
                           reveals a Search Console *Domain* property verified by DNS.
  findings(...)            turns the evidence into seo_check-style findings. Absence of a
                           footprint is never reported as a failure: verification can also be
                           done with an HTML file, GA or GTM, and analytics can load after consent.

Standard library only. This file is maintained in shared/ and copied into skills by `make sync`.
"""
import json
import re
import urllib.parse
import urllib.request

_GA4 = [
    re.compile(r"googletagmanager\.com/gtag/js\?(?:[^\"'<>\s]*&(?:amp;)?)?id=(G-[A-Z0-9]{4,14})"),
    re.compile(r"gtag\(\s*['\"]config['\"]\s*,\s*['\"](G-[A-Z0-9]{4,14})['\"]"),
    re.compile(r"['\"]?(?:measurement_?id|measurementId|gaId|ga4Id)['\"]?\s*[:=]\s*['\"](G-[A-Z0-9]{4,14})['\"]",
               re.I),
]
_GTM = [
    re.compile(r"googletagmanager\.com/(?:gtm\.js|ns\.html)\?(?:[^\"'<>\s]*&(?:amp;)?)?id=(GTM-[A-Z0-9]{4,10})"),
    re.compile(r"['\"](GTM-[A-Z0-9]{4,10})['\"]"),
]
_UA = re.compile(r"['\"](UA-\d{4,10}-\d{1,4})['\"]")
_UA_LIB = re.compile(r"google-analytics\.com/(?:analytics|ga)\.js")
_CONSENT = re.compile(r"gtag\(\s*['\"]consent['\"]")
OTHER_ANALYTICS = {
    "Plausible": re.compile(r"plausible\.io/js|data-domain=.{0,80}plausible", re.I),
    "Fathom": re.compile(r"usefathom\.com", re.I),
    "Matomo": re.compile(r"matomo\.(?:js|php)|piwik\.js|_paq\.push", re.I),
    "Umami": re.compile(r"umami(?:\.is)?[^\"']*\.js|data-website-id", re.I),
    "PostHog": re.compile(r"posthog", re.I),
    "Vercel Analytics": re.compile(r"/_vercel/insights/script\.js|va\.vercel-scripts\.com", re.I),
    "Cloudflare Web Analytics": re.compile(r"static\.cloudflareinsights\.com/beacon", re.I),
    "Microsoft Clarity": re.compile(r"clarity\.ms/tag", re.I),
    "Segment": re.compile(r"cdn\.segment\.com", re.I),
    "Simple Analytics": re.compile(r"scripts\.simpleanalyticscdn\.com", re.I),
}
VERIFY_META = {
    "google-site-verification": "Google Search Console",
    "msvalidate.01": "Bing Webmaster Tools",
    "yandex-verification": "Yandex Webmaster",
    "baidu-site-verification": "Baidu",
    "facebook-domain-verification": "Meta (Facebook)",
    "p:domain_verify": "Pinterest",
}


def _all(patterns, html):
    found = []
    for p in patterns:
        for m in p.finditer(html):
            if m.group(1) not in found:
                found.append(m.group(1))
    return found


def detect_tags(html, meta=None):
    """Return the analytics and verification footprints in one HTML document."""
    html = html or ""
    meta = {k.lower(): v for k, v in (meta or {}).items()}
    ua = [u for u in _UA.findall(html)]
    if not ua and _UA_LIB.search(html):
        ua = ["analytics.js"]
    return {
        "ga4": _all(_GA4, html),
        "gtm": _all(_GTM, html),
        "ua": list(dict.fromkeys(ua)),
        "consent_mode": bool(_CONSENT.search(html)),
        "other_analytics": [name for name, p in OTHER_ANALYTICS.items() if p.search(html)],
        "verification_meta": {VERIFY_META[k]: bool(meta.get(k)) for k in VERIFY_META if meta.get(k)},
    }


_GA4_IN_JS = re.compile(r"(?:['\"`]|[?&]id=)(G-[A-Z0-9]{8,12})(?![A-Za-z0-9_-])")
_GTM_IN_JS = re.compile(r"(?:['\"`]|[?&]id=)(GTM-[A-Z0-9]{4,10})(?![A-Za-z0-9_-])")


def ids_in_script(js):
    """GA4 / GTM IDs inside a JavaScript file, only if the file loads Google's tag (avoids stray matches)."""
    js = js or ""
    if "googletagmanager" not in js and "gtag(" not in js:
        return {"ga4": [], "gtm": []}
    return {"ga4": list(dict.fromkeys(_GA4_IN_JS.findall(js))),
            "gtm": list(dict.fromkeys(_GTM_IN_JS.findall(js)))}


def _doh(url, headers, timeout, ctx):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        data = json.loads(r.read(200_000))
    return [a.get("data", "").strip('"') for a in data.get("Answer", []) if a.get("type") == 16]


def dns_txt(name, timeout=8, ctx=None):
    """TXT records for `name` via DNS-over-HTTPS. Returns a list, or None if DNS couldn't be queried."""
    q = urllib.parse.urlencode({"name": name, "type": "TXT"})
    for url, headers in ((f"https://dns.google/resolve?{q}", {}),
                         (f"https://cloudflare-dns.com/dns-query?{q}", {"Accept": "application/dns-json"})):
        try:
            return _doh(url, {"User-Agent": "seo-checklist-skills", **headers}, timeout, ctx)
        except Exception:
            continue
    return None


def domain_candidates(host):
    """example.co.uk -> ['example.co.uk', 'co.uk'] is harmless; blog.example.com -> both levels."""
    host = (host or "").lower().removeprefix("www.")
    labels = host.split(".")
    if len(labels) < 2 or re.fullmatch(r"[\d.]+|localhost", host):
        return []
    return [".".join(labels[i:]) for i in range(0, max(1, len(labels) - 1))][:3]


def google_dns_verified(host, resolver=dns_txt):
    """True / False if DNS answered, None if no DNS lookup was possible."""
    answered = False
    for name in domain_candidates(host):
        records = resolver(name)
        if records is None:
            continue
        answered = True
        if any(r.startswith("google-site-verification=") for r in records):
            return True
    return False if answered else None


def findings(tags, google_dns=None, bing_file=None):
    """Turn detect_tags() output (+ optional DNS / BingSiteAuth.xml results) into findings."""
    f = []
    where = f" in the site's own script {tags['source']} (loaded by JavaScript)" if tags.get("source") else ""
    if tags["ga4"]:
        f.append(("PASS", "analytics", "GA4 tag found" + where + ": " + ", ".join(tags["ga4"])))
    elif tags["gtm"]:
        f.append(("INFO", "analytics", f"Google Tag Manager container {', '.join(tags['gtm'])} found. GA4 may be "
                                       "configured inside it, which can't be seen from outside - confirm in GTM"))
    else:
        others = tags["other_analytics"]
        extra = f" (found {', '.join(others)} instead)" if others else ""
        f.append(("WARN", "analytics", "No GA4 or Google Tag Manager tag in the homepage HTML or its scripts" + extra +
                  ". If it loads after cookie consent or server-side, confirm it in GA4 > Realtime"))
    if tags["ua"]:
        f.append(("WARN", "analytics", f"Legacy Universal Analytics ({', '.join(tags['ua'])}) stopped processing "
                                       "data in July 2023 - remove it and use GA4"))
    if tags["consent_mode"]:
        f.append(("INFO", "analytics", "Google consent mode is set up"))

    meta = tags["verification_meta"]
    if google_dns:
        f.append(("PASS", "gsc-verification", "Search Console Domain property verified by DNS "
                                              "(google-site-verification TXT record)"))
    elif meta.get("Google Search Console"):
        f.append(("PASS", "gsc-verification", "Search Console verification meta tag found (URL-prefix property). "
                                              "A Domain property verified by DNS also covers http/https and "
                                              "subdomains"))
    else:
        dns_note = "" if google_dns is False else " (DNS wasn't checked)"
        f.append(("INFO", "gsc-verification", "No Search Console verification visible in DNS or meta tags" + dns_note +
                  ". It may be verified another way (HTML file, GA, GTM) - confirm in Search Console"))
    if meta.get("Bing Webmaster Tools") or bing_file:
        how = "msvalidate.01 meta tag" if meta.get("Bing Webmaster Tools") else "BingSiteAuth.xml"
        f.append(("PASS", "bing-verification", f"Bing Webmaster Tools verification found ({how})"))
    else:
        f.append(("INFO", "bing-verification", "No Bing Webmaster Tools verification visible. Bing can import the "
                                               "site and its sitemaps from Search Console in one click - confirm "
                                               "it's added"))
    for name in meta:
        if name not in ("Google Search Console", "Bing Webmaster Tools"):
            f.append(("INFO", "verification", f"{name} verification tag found"))
    return f
