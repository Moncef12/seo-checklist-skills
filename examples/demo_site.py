#!/usr/bin/env python3
"""
A tiny fictional SaaS site ("Acme Invoice") with deliberate SEO problems.

    python3 examples/demo_site.py            # serves on http://127.0.0.1:8799
    python3 examples/demo_site.py --port 0   # random free port

Used by the integration tests and to generate the sample reports in examples/.
Planted issues (what a good audit should find):

  - 2-hop redirect chain  /old-pricing -> /pricing-2023 -> /pricing  (linked from a blog post)
  - broken internal link  /features/reports (404)                    (linked from the homepage)
  - noindex page listed in the sitemap      /legacy
  - orphan page in the sitemap              /orphan-landing
  - soft 404: unknown URLs return 200 "Page not found"
  - cookie bounce: /app redirects to itself to set a cookie
  - /pricing: 78-char title, no meta description, no canonical, two H1s
  - /blog/invoice-template-guide: thin (under 100 words) and competes with /templates
  - image without alt text and without dimensions on the homepage, and it weighs ~350 KB
  - no analytics tag and no search-engine verification on the homepage
  - /features/invoicing has an empty BreadcrumbList (schema without its required items)
  - the same filler paragraph on most pages, and near-duplicate text on /pricing and /orphan-landing
  - /partner (linked from the blog) redirects to another host; the crawler must not wander off-site
  - /admin/ is disallowed in robots.txt (the checker must not crawl it)
Standard library only.
"""
import argparse
import gzip
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BRAND = "Acme Invoice"


def page(title, body, *, desc=None, canonical=True, path="/", schema=None, noindex=False, extra_head=""):
    head = [f"<title>{title}</title>", '<meta name="viewport" content="width=device-width, initial-scale=1">']
    if desc:
        head.append(f'<meta name="description" content="{desc}">')
    if canonical:
        head.append(f'<link rel="canonical" href="{{origin}}{path}">')
    if noindex:
        head.append('<meta name="robots" content="noindex">')
    if schema:
        head.append(f'<script type="application/ld+json">{schema}</script>')
    nav = ('<nav><a href="/">Home</a> <a href="/features/invoicing">Invoicing</a> '
           '<a href="/pricing">Pricing</a> <a href="/templates">Templates</a> <a href="/blog/">Blog</a> '
           '<a href="/app">Log in</a> <a href="/admin/">Admin</a></nav>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">{"".join(head)}{extra_head}</head>'
            f"<body>{nav}<main>{body}</main><footer>&copy; {BRAND}</footer></body></html>")


LOREM = ("Freelancers lose hours every month chasing unpaid invoices. A clear invoice with payment terms, "
         "an itemised list of work, your bank or card details and a due date gets paid faster. ") * 6

PAGES = {
    "/": page(
        f"{BRAND}: Online Invoicing Software for Freelancers",
        "<h1>Invoicing software for freelancers</h1>"
        "<p>Acme Invoice lets freelancers create an invoice in under a minute and chases late payers "
        "automatically, so you get paid faster.</p>"
        '<img src="/img/hero.png">'
        "<h2>Features</h2><p>" + LOREM + "</p>"
        '<p>See <a href="/features/invoicing">invoicing</a> and <a href="/features/reports">reports</a>.</p>',
        desc="Create professional invoices in under a minute, automate payment reminders and get paid faster. "
             "Free for up to 5 clients.",
        schema='{"@context":"https://schema.org","@type":"Organization","name":"Acme Invoice","url":"/"}'),
    "/pricing": page(
        "Pricing - Acme Invoice - Plans for Freelancers, Agencies, Teams and Enterprises",
        "<h1>Pricing</h1><h1>Simple plans</h1><p>" + LOREM + "</p>",
        canonical=False, path="/pricing"),
    "/features/invoicing": page(
        "Automated Invoicing for Freelancers: Send in 60 Seconds",
        "<h1>Automated invoicing</h1><p>Send a branded invoice in 60 seconds and let Acme chase payment.</p>"
        "<h2>How it works</h2><p>" + LOREM + "</p>"
        '<p><a href="/templates">Free invoice templates</a> · <a href="/pricing">Pricing</a></p>',
        desc="Send branded invoices in 60 seconds, add online card payments and let automatic reminders "
             "chase late clients for you.",
        path="/features/invoicing",
        schema='{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[]}'),
    "/templates": page(
        "Free Invoice Templates for Freelancers (Word, PDF, Excel)",
        "<h1>Free invoice templates</h1><p>Download a free invoice template in Word, PDF or Excel, or fill "
        "one in online and send it in a minute.</p><h2>Templates</h2><p>" + LOREM + "</p>",
        desc="Download free invoice templates for freelancers in Word, PDF and Excel, or fill one in online "
             "and send it in under a minute.",
        path="/templates"),
    "/blog/": page(
        f"Invoicing and Getting Paid: Guides for Freelancers | {BRAND}",
        '<h1>Blog</h1><ul><li><a href="/blog/how-to-write-an-invoice">How to write an invoice</a></li>'
        '<li><a href="/blog/invoice-template-guide">Invoice template guide</a></li></ul>'
        '<p><a href="/partner">Partner offers</a></p>',
        desc="Practical guides on writing invoices, payment terms and getting paid on time as a freelancer "
             "or small agency owner.",
        path="/blog/"),
    "/blog/how-to-write-an-invoice": page(
        "How to Write an Invoice: Step-by-Step Guide With Examples",
        "<h1>How to write an invoice</h1><p>To write an invoice, list your details, the client's details, "
        "an invoice number and date, itemised services, the total and payment terms.</p>"
        "<h2>1. Add your business details</h2><p>" + LOREM + "</p>"
        '<p>Old link: <a href="/old-pricing">see our pricing</a>.</p>',
        desc="Learn how to write an invoice step by step: what to include, payment terms, numbering and a "
             "free example you can copy today.",
        path="/blog/how-to-write-an-invoice",
        schema='{"@context":"https://schema.org","@type":"BlogPosting","headline":"How to write an invoice",'
               '"author":{"@type":"Person","name":"Jane Doe"},"datePublished":"2025-01-10"}'),
    "/blog/invoice-template-guide": page(
        "Invoice Template Guide",
        "<h1>Invoice template</h1><p>Here is an invoice template. Invoice templates are useful. "
        'Download our invoice template on the <a href="/templates">templates page</a>.</p>',
        desc="Our invoice template guide.",
        path="/blog/invoice-template-guide"),
    "/pricing-2023": None,  # redirect hop
    "/legacy": page(
        "Legacy Plans for Existing Customers | Acme Invoice",
        "<h1>Legacy plans</h1><p>" + LOREM + "</p>",
        desc="Details of legacy plans kept for existing customers who signed up before 2024.",
        path="/legacy", noindex=True),
    "/orphan-landing": page(
        "Invoicing Software for Photographers: Get Paid for Shoots",
        "<h1>Invoicing for photographers</h1><p>" + LOREM + "</p>",
        desc="Invoice clients for shoots, licensing and prints, take deposits online and get paid before "
             "delivery day.",
        path="/orphan-landing"),
    "/app": page("Log in | Acme Invoice", "<h1>Log in</h1><form></form>", path="/app", noindex=True),
    "/admin/": page("Admin", "<h1>Admin</h1>", path="/admin/", noindex=True),
}

HERO_BYTES = 350_000
REDIRECTS = {"/old-pricing": "/pricing-2023", "/pricing-2023": "/pricing"}
SITEMAP_PAGES = ["/", "/pricing", "/features/invoicing", "/templates", "/legacy", "/orphan-landing"]
SITEMAP_BLOG = ["/blog/", "/blog/how-to-write-an-invoice", "/blog/invoice-template-guide"]


def urlset(origin, paths):
    items = "".join(f"<url><loc>{origin}{p}</loc><lastmod>2026-09-01</lastmod></url>" for p in paths)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>').encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_HEAD(self):
        self._head_only = True
        try:
            self.do_GET()
        finally:
            self._head_only = False

    def _send(self, status, body=b"", ctype="text/html; charset=utf-8", headers=()):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        if not getattr(self, "_head_only", False):
            self.wfile.write(body)

    def do_GET(self):
        origin = f"http://{self.headers.get('Host')}"
        path = self.path.split("?")[0]
        if path == "/robots.txt":
            return self._send(200, f"User-agent: *\nDisallow: /admin/\nSitemap: {origin}/sitemap_index.xml\n"
                              .encode(), "text/plain")
        if path == "/sitemap_index.xml":
            body = ('<?xml version="1.0" encoding="UTF-8"?>'
                    '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    f"<sitemap><loc>{origin}/sitemap-pages.xml</loc></sitemap>"
                    f"<sitemap><loc>{origin}/sitemap-blog.xml.gz</loc></sitemap></sitemapindex>").encode()
            return self._send(200, body, "application/xml")
        if path == "/sitemap-pages.xml":
            return self._send(200, urlset(origin, SITEMAP_PAGES), "application/xml")
        if path == "/sitemap-blog.xml.gz":
            return self._send(200, gzip.compress(urlset(origin, SITEMAP_BLOG)), "application/gzip")
        if path == "/partner":  # same server under another hostname = a different site
            return self._send(301, headers=[("Location", f"http://localhost:{self.server.server_address[1]}/")])
        if path in REDIRECTS:
            return self._send(301, headers=[("Location", REDIRECTS[path])])
        if path == "/app" and "session=1" not in (self.headers.get("Cookie") or ""):
            return self._send(302, headers=[("Location", "/app"), ("Set-Cookie", "session=1; Path=/")])
        if path.startswith("/img/"):
            size = HERO_BYTES if path == "/img/hero.png" else 8
            return self._send(200, (b"\x89PNG\r\n\x1a\n" + b"\0" * size)[:max(size, 8)], "image/png")
        html = PAGES.get(path)
        if html is None:
            if path == "/features/reports":
                return self._send(404, b"<h1>Not found</h1>")
            # soft 404: friendly page with a 200 status
            return self._send(200, page("Page not found", "<h1>Oops, page not found</h1>").encode())
        return self._send(200, html.replace("{origin}", origin).encode())


def serve(port=8799):
    """Start the demo site in a background thread; returns (server, base_url)."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Serve the Acme Invoice demo site")
    ap.add_argument("--port", type=int, default=8799)
    port = ap.parse_args().port
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Acme Invoice demo site on http://127.0.0.1:{server.server_address[1]}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
