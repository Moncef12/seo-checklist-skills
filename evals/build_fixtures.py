#!/usr/bin/env python3
"""Rebuild the fixture files of the v1.2 eval cases (deterministic). Run from the repo root:

    python3 evals/build_fixtures.py

Each case plants specific problems, listed in its case.yaml graders. The files are committed, so
this script only matters when a fixture needs to change.
"""
import csv
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
NAV = ('<header><a href="/">Payly</a><nav><a href="/features/recurring-invoices">Features</a> '
       '<a href="/pricing">Pricing</a> <a href="/templates">Templates</a> <a href="/blog/">Blog</a> '
       '<a href="/locations/austin">Austin</a></nav></header>')
FOOT = ("<footer><p>Payly is invoicing software for freelancers and small studios. Send invoices, take card "
        "payments, chase late clients automatically and see who owes you what, all in one place. Made in "
        "Austin, Texas. Terms, privacy and security.</p></footer>")


def page(title, main, head=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">{head}</head>'
            f"<body>{NAV}<main>{main}</main>{FOOT}</body></html>")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------------------------------------
# title-keyword-gaps (Q2)
# ---------------------------------------------------------------------------------------------
TITLES = {
    "/": "Billing App for Self-Employed People | Payly",
    "/pricing": "Payly Pricing: Plans for Freelancers, Agencies, Studios and Enterprise Teams",
    "/templates": "Free Invoice Templates for Freelancers (Word, PDF, Excel)",
    "/features/reminders": "Automatic Payment Reminders That Chase Late Clients",
    "/features/time-tracking": "Time Tracking for Freelancers, Built Into Your Invoices",
    "/integrations/stripe": "Stripe Integration | Payly",
    "/blog/": "Payly Blog",
    "/resources": "Payly Blog",
    "/blog/how-to-write-an-invoice": "HOW TO WRITE AN INVOICE THAT GETS PAID: WORKER CHECKLIST",
    "/blog/late-payment-fees": "Late Payment Fees: How Much Can You Charge? | Payly",
}
QUERIES = [  # query, page, clicks, impressions, position
    ("invoice software for freelancers", "/", 40, 12000, 4.2),
    ("payly", "/", 820, 900, 1.0),
    ("billing app", "/", 6, 300, 9.1),
    ("enterprise invoicing", "/pricing", 4, 2600, 7.8),
    ("payly pricing", "/pricing", 210, 400, 1.2),
    ("free invoice template", "/templates", 900, 10000, 2.1),
    ("invoice template word", "/templates", 120, 2200, 4.0),
    ("automatic payment reminders", "/features/reminders", 60, 1800, 5.5),
    ("time tracking for freelancers", "/features/time-tracking", 35, 1400, 6.3),
    ("stripe invoicing", "/integrations/stripe", 8, 1900, 8.2),
    ("payly stripe", "/integrations/stripe", 20, 60, 1.4),
    ("payly blog", "/blog/", 3, 120, 2.0),
    ("payly resources", "/resources", 1, 40, 3.5),
    ("how to write an invoice", "/blog/how-to-write-an-invoice", 30, 5000, 13.4),
    ("how to write an invoice for freelance work", "/blog/how-to-write-an-invoice", 9, 1100, 11.8),
    ("late fee for invoice", "/blog/late-payment-fees", 12, 1600, 9.7),
    ("how much late fee can i charge", "/blog/late-payment-fees", 5, 700, 12.2),
]


def build_titles():
    base = os.path.join(ROOT, "title-keyword-gaps")
    for path, title in TITLES.items():
        rel = "index.html" if path == "/" else path.strip("/") + ("/index.html" if path.endswith("/") else ".html")
        write(os.path.join(base, "site", rel), page(title, f"<h1>{title.split('|')[0].strip()}</h1>"
                                                           "<p>Placeholder body copy for this template.</p>"))
    os.makedirs(os.path.join(base, "gsc"), exist_ok=True)
    with open(os.path.join(base, "gsc", "query_page.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["query", "page", "clicks", "impressions", "ctr", "position"])
        for q, p, c, i, pos in QUERIES:
            w.writerow([q, "https://getpayly.example" + p, c, i, f"{100 * c / i:.2f}%", pos])


# ---------------------------------------------------------------------------------------------
# near-duplicate-pages (C4)
# ---------------------------------------------------------------------------------------------
WHY = ("Why freelancers switch to Payly: invoices go out in under a minute, clients pay by card or bank "
       "transfer from the invoice itself, reminders go out on their own when a payment is late, and you can "
       "see at a glance who owes you money and how much is coming in this month.")


def city_page(city, county, landmark, extra):
    return (f"<h1>Invoicing software for freelancers in {city}</h1>"
            f"<p>Payly helps freelancers and small studios in {city} send professional invoices, take card "
            f"payments and get paid on time. Whether you design brands near {landmark} or write code for "
            f"startups across {county}, Payly keeps your billing in one place so you can spend your time on "
            "client work instead of chasing payments.</p>"
            f"<p>Freelancers in {city} use Payly to send branded invoices in under a minute, add a pay now "
            "button to every invoice, schedule recurring invoices for retainers, and let automatic reminders "
            "follow up with late clients. Payments land in your bank account in two business days and every "
            "invoice is stored with its payment history for tax time.</p>"
            f"<p>Getting started in {city} takes five minutes. Import your clients from a spreadsheet, choose "
            "an invoice template, connect Stripe or your bank, and send your first invoice. Your first five "
            "clients are free, and paid plans start at nine dollars a month with no setup fee.</p>"
            f"<p>{extra}</p>")


GUIDE_A = ("<h1>Invoice numbering: the complete guide</h1>"
           "<p>Every invoice you send needs a unique invoice number. The number lets you and your client refer "
           "to the same document, keeps your records in order, and is required by tax authorities in most "
           "countries. A good numbering system is simple, sequential and never reuses a number.</p>"
           "<p>The most common format is a plain sequence such as 001, 002 and 003. Many freelancers add a "
           "prefix for the year, like 2026-001, so the sequence restarts each January and old invoices are easy "
           "to find. Agencies with several clients often add a client code, such as ACME-2026-004.</p>"
           "<p>Whatever format you choose, stick to it. Don't skip numbers, don't reuse a cancelled number, and "
           "keep the sequence going even when you change templates or software. If you cancel an invoice, issue "
           "a credit note that references the original number instead of deleting it.</p>"
           "<p>Payly numbers invoices for you automatically. You set the format once, with a prefix, the year "
           "or a client code, and every new invoice gets the next number in the sequence.</p>")
GUIDE_B = GUIDE_A.replace("Invoice numbering: the complete guide", "How to number your invoices") \
    .replace("Every invoice you send needs a unique invoice number.",
             "Each invoice you send must have its own number.") \
    .replace("Many freelancers add a prefix", "Lots of freelancers put a prefix") \
    .replace("Whatever format you choose, stick to it.", "Pick one format and keep using it.")
RECURRING = ("<h1>Recurring invoices for retainers</h1>"
             "<p>Recurring invoices send themselves on a schedule, so retainer clients are billed on time every "
             "month without you lifting a finger. Set the amount, the start date and how often to bill, weekly, "
             "monthly or yearly, and Payly creates and sends each invoice automatically.</p>"
             "<p>Clients can save a card or set up a bank debit so payments are collected on the due date. If a "
             "payment fails, Payly retries it and emails the client a secure link to update their details. You "
             "can pause, change or end a recurring invoice at any time, and every change is logged.</p>"
             "<p>Recurring invoices work with every plan, support taxes and discounts, and show up in your cash "
             "flow forecast so you know exactly how much retainer income is coming in next month and next "
             "quarter. Combine them with automatic reminders for the clients who still pay by transfer.</p>")
SUBSCRIPTIONS = RECURRING.replace("Recurring invoices for retainers", "Subscription billing for freelancers") \
    .replace("Recurring invoices send themselves on a schedule", "Subscription billing sends invoices on a schedule") \
    .replace("Recurring invoices work with every plan", "Subscription billing works with every plan")


VOCAB = """account accrual advance agreement allowance amount annual approval archive audit balance
bank batch billing bonus branch budget calendar card cash catalog category charge checkout claim client
code commission contract cost coupon credit currency customer cycle dashboard date debit deadline deposit
detail discount document draft due earning email entry estimate exchange expense export fee filter
forecast form freelancer fund grant history hourly import income installment insight inventory invoice
item journal label ledger limit line loan log margin member method milestone mobile month note notice
offer order owner package partner payee payment payout payroll period plan policy portal price profile
profit project proposal quarter quote rate receipt record refund reminder report request retainer
revenue review rule salary schedule seat service session setting share signature software statement
status subscription summary supplier tax team template term timesheet total transfer trial upload user
vendor voucher wallet week withdrawal workflow year""".split()


def unique(topic, n_words=170):
    """Readable-enough filler that shares almost no 3-word sequence with any other page."""
    x = sum(map(ord, topic)) * 7919
    out = []
    for i in range(n_words):
        x = (x * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        out.append(VOCAB[(x >> 33) % len(VOCAB)])
        if i % 12 == 11:
            out[-1] += "."
    return "<p>" + f"{topic.capitalize()}: " + " ".join(out) + "</p>"


def build_dupes():
    base = os.path.join(ROOT, "near-duplicate-pages", "site")
    canon = '<link rel="canonical" href="https://payly.example{}">'
    pages = {
        "index.html": ("Invoicing Software for Freelancers | Payly", "<h1>Get paid faster</h1>" + unique("solo work")
                       + f"<p>{WHY}</p>"),
        "pricing.html": ("Pricing | Payly", "<h1>Pricing</h1>" + unique("pricing plans")),
        "pricing-2024.html": ("Pricing | Payly", "<h1>Pricing</h1>" + unique("pricing plans")),
        "locations__austin.html": ("Invoicing Software for Freelancers in Austin | Payly",
                                   city_page("Austin", "Travis County", "South Congress",
                                             "Austin freelancers can join our monthly invoicing workshop.")),
        "locations__round-rock.html": ("Invoicing Software for Freelancers in Round Rock | Payly",
                                       city_page("Round Rock", "Williamson County", "Dell Diamond",
                                                 "Round Rock freelancers get a free onboarding call.")),
        "locations__dallas.html": ("Invoicing Software for Freelancers in Dallas | Payly",
                                   "<h1>Payly for Dallas agencies</h1>" + unique("Dallas agencies", 220)),
        "blog__invoice-numbering-guide.html": ("Invoice Numbering: The Complete Guide | Payly", GUIDE_A),
        "blog__how-to-number-invoices.html": ("How to Number Your Invoices | Payly", GUIDE_B),
        "features__recurring-invoices.html": ("Recurring Invoices for Retainers | Payly", RECURRING + f"<p>{WHY}</p>"),
        "features__subscription-billing.html": ("Subscription Billing for Freelancers | Payly",
                                                SUBSCRIPTIONS + f"<p>{WHY}</p>"),
        "blog__tips.html": ("Tips | Payly", "<h1>Tips</h1><p>Send invoices early. Follow up politely. Use clear "
                                            "payment terms. Offer card payments. Keep records.</p>"),
    }
    topics = ["expense tracking", "time tracking", "estimates", "client portal", "late fees", "tax reports",
              "multi-currency", "team accounts", "mobile app", "bank sync", "proposals"]
    for i, t in enumerate(topics):
        slug = t.replace(" ", "-")
        body = f"<h1>{t.title()}</h1>" + unique(t)
        if i < 4:
            body += f"<p>{WHY}</p>"
        pages[f"features__{slug}.html"] = (f"{t.title()} for Freelancers | Payly", body)
    for name, (title, main) in pages.items():
        url = "/" if name == "index.html" else "/" + name[:-5].replace("__", "/")
        head = canon.format("/pricing" if name == "pricing-2024.html" else url)
        write(os.path.join(base, name), page(title, main, head))


# ---------------------------------------------------------------------------------------------
# schema-required-fields (T13) and setup-detection (T1/T2)
# ---------------------------------------------------------------------------------------------
def ld(obj):
    return f'<script type="application/ld+json">{json.dumps(obj)}</script>'


def build_schema():
    base = os.path.join(ROOT, "schema-required-fields", "pages")
    ctx = "https://schema.org"
    docs = {
        "product.html": ("Payly Pro Plan", {"@context": ctx, "@type": "Product", "name": "Payly Pro",
                                            "image": "https://payly.example/pro.png",
                                            "description": "Unlimited invoices and clients."}),
        "breadcrumbs.html": ("Recurring invoices", {"@context": ctx, "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "name": "Home", "item": "https://payly.example/"},
            {"@type": "ListItem", "position": 2, "name": "Features"},
            {"@type": "ListItem", "position": 3, "name": "Recurring invoices"}]}),
        "faq.html": ("Invoicing FAQ", {"@context": ctx, "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "Is Payly free?",
             "acceptedAnswer": {"@type": "Answer", "text": "Yes, for up to five clients."}},
            {"@type": "Question", "name": "Can clients pay by card?",
             "acceptedAnswer": {"@type": "Answer", "text": "Yes, cards and bank transfers."}}]}),
        "dentist.html": ("Brightsmile Dental Austin", {"@context": ctx, "@type": "Dentist",
                                                       "name": "Brightsmile Dental", "telephone": "+1-512-555-0100",
                                                       "url": "https://brightsmile.example/"}),
        "article.html": ("How to write an invoice", {"@context": ctx, "@type": "BlogPosting",
                                                     "headline": "How to write an invoice",
                                                     "datePublished": "10/03/2026",
                                                     "author": {"@type": "Person", "name": "Jane Doe"},
                                                     "image": "https://payly.example/invoice.png"}),
        "event.html": ("Invoicing workshop", {"@context": ctx, "@type": "Event", "name": "Get Paid Faster workshop",
                                              "startDate": "2026-11-12T18:00-06:00",
                                              "description": "A free evening workshop for freelancers."}),
    }
    for name, (h1, obj) in docs.items():
        write(os.path.join(base, name), page(f"{h1} | Payly", f"<h1>{h1}</h1><p>Content for {h1}.</p>", ld(obj)))

    setup = os.path.join(ROOT, "setup-detection", "site", "homepage.html")
    head = ('<meta name="google-site-verification" content="q8Hk2-Zx7vYpL0aT3nR9sWm1cE4bD6fG5hJ8kN2oP4u">'
            "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),"
            "event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s);j.async=true;"
            "j.src='https://www.googletagmanager.com/gtm.js?id='+i;f.parentNode.insertBefore(j,f);"
            "})(window,document,'script','dataLayer','GTM-W7K2QX9');</script>"
            "<script>(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;})(window,document,'script',"
            "'https://www.google-analytics.com/analytics.js','ga');ga('create', 'UA-48213377-2', 'auto');"
            "ga('send', 'pageview');</script>")
    write(setup, page("Payly: Invoicing Software for Freelancers", "<h1>Get paid faster</h1><p>Payly sends "
                      "invoices, takes card payments and chases late clients for you.</p>", head))


# ---------------------------------------------------------------------------------------------
# checklist-tracker
# ---------------------------------------------------------------------------------------------
def build_tracker():
    base = os.path.join(ROOT, "checklist-tracker", "project")
    os.makedirs(base, exist_ok=True)
    md = os.path.join(base, "SEO-CHECKLIST.md")
    if os.path.exists(md):
        os.remove(md)
    first = {"T1": {"status": "unknown", "note": "no GSC access yet"},
             "T2": {"status": "needs-work", "note": "sitemap exists, submission unconfirmed"},
             "T3": {"status": "pass", "note": "all sampled URLs indexable"},
             "T4": "pass", "T5": {"status": "fail", "note": "no canonical on 6 of 10 templates"},
             "T7": "pass", "T8": "pass",
             "T9": {"status": "fail", "note": "3 broken internal links, 1 redirect chain"},
             "T10": "pass", "T11": {"status": "needs-work", "note": "no BreadcrumbList schema"},
             "T12": {"status": "fail", "note": "/orphan-landing not linked"},
             "T13": {"status": "needs-work", "note": "Organization only"},
             "O2": {"status": "fail", "note": "/pricing title is 79 chars"},
             "O3": {"status": "fail", "note": "4 pages share one description"},
             "O4": "pass", "O6": {"status": "needs-work", "note": "hero image has no alt"},
             "L5": "na"}
    status_file = os.path.join(base, ".statuses.json")
    with open(status_file, "w") as f:
        json.dump(first, f)
    script = os.path.join(ROOT, "..", "shared", "checklist.py")
    subprocess.run([sys.executable, script, "update", "--file", md, "--statuses", status_file,
                    "--site", "https://getpayly.example", "--date", "2026-09-29"], check=True, capture_output=True)
    os.remove(status_file)
    write(os.path.join(base, "todays-check.md"), """# Technical SEO check: https://getpayly.example (2026-10-19)

**Summary:** ❌ 2 FAIL | ⚠️ 5 WARN | ℹ️ 7 INFO | ✅ 9 PASS

## Search engine setup
- ✅ **PASS** `analytics` GA4 tag found: G-8XK2PL4QZ1
- ✅ **PASS** `gsc-verification` Search Console Domain property verified by DNS (google-site-verification TXT record)
- ℹ️ **INFO** `bing-verification` No Bing Webmaster Tools verification visible

## Sample of 20 URLs
- ✅ **PASS** `canonical` Self-referencing canonical on all 20 sampled pages
- ⚠️ **WARN** `title` 1/20 sampled pages: /pricing title is 79 chars (target 50-60)
- ✅ **PASS** `meta-description` Every sampled page has its own description (120-158 chars)
- ⚠️ **WARN** `schema` /features/invoicing: BreadcrumbList is missing required itemListElement

## 404 handling
- ❌ **FAIL** `soft-404` Non-existent URLs return 200 (soft 404) - return a real 404 status

## Links & orphans
- ✅ **PASS** `broken-link` No broken internal links among 214 checked
- ⚠️ **WARN** `orphans` 1 sitemap URL was not linked from any crawled page: /orphan-landing
- ❌ **FAIL** `indexability` Sitemap lists a noindex page: /legacy

## Per-page issues
- ⚠️ **WARN** `img-alt` / : hero image has no alt attribute
""")


if __name__ == "__main__":
    build_titles()
    build_dupes()
    build_schema()
    build_tracker()
    print("fixtures rebuilt")
