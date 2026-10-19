"""Offline tests for the v1.2 checks: setup detection, duplicate content, schema rules, titles,
the checklist tracker, image weight, the HTML report and the new CLI outputs."""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(ROOT, "shared"))

import checklist  # noqa: E402
import gsc_analyze  # noqa: E402
import report_html  # noqa: E402
import schema_rules  # noqa: E402
import seo_check  # noqa: E402
import setup_detect  # noqa: E402
import similarity  # noqa: E402


def checks(findings, level=None):
    return [(l, c, m) for l, c, m in findings if level is None or l == level]


class SetupDetection(unittest.TestCase):
    def test_tags_and_verification(self):
        html = ('<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123XYZ"></script>'
                "<script>gtag('consent','default',{});gtag('config','G-ABC123XYZ');ga('create','UA-12345-1')</script>"
                '<script src="https://plausible.io/js/script.js"></script>'
                "<script>(function(w,d,s,l,i){})(window,document,'script','dataLayer','GTM-K9X2Q7');</script>")
        meta = {"google-site-verification": "abc", "msvalidate.01": "XYZ"}
        t = setup_detect.detect_tags(html, meta)
        self.assertEqual(t["ga4"], ["G-ABC123XYZ"])
        self.assertEqual(t["gtm"], ["GTM-K9X2Q7"])
        self.assertEqual(t["ua"], ["UA-12345-1"])
        self.assertTrue(t["consent_mode"])
        self.assertIn("Plausible", t["other_analytics"])
        self.assertTrue(t["verification_meta"]["Google Search Console"])
        f = setup_detect.findings(t)
        self.assertIn(("PASS", "analytics"), {(l, c) for l, c, _ in f})
        self.assertTrue(any(l == "WARN" and "Universal Analytics" in m for l, _, m in f))
        self.assertIn(("PASS", "bing-verification"), {(l, c) for l, c, _ in f})

    def test_gtm_only_and_nothing(self):
        gtm = setup_detect.findings(setup_detect.detect_tags("<script>'GTM-AB12CD'</script>", {}))
        self.assertEqual([l for l, c, _ in gtm if c == "analytics"], ["INFO"])
        none = setup_detect.findings(setup_detect.detect_tags("<p>hello G-SHOCK watches</p>", {}))
        self.assertEqual([l for l, c, _ in none if c == "analytics"], ["WARN"])
        self.assertEqual([l for l, c, _ in none if c == "gsc-verification"], ["INFO"])

    def test_ids_in_bundled_scripts(self):
        js = 'n="https://www.googletagmanager.com/gtag/js?id=G-BYTCY7SK2E";gtag("config",n)'
        self.assertEqual(setup_detect.ids_in_script(js)["ga4"], ["G-BYTCY7SK2E"])
        self.assertEqual(setup_detect.ids_in_script('var x="G-ABCDEFGH12"')["ga4"], [])  # no Google tag code
        f = setup_detect.findings({**setup_detect.detect_tags("", {}), "ga4": ["G-BYTCY7SK2E"],
                                   "source": "/_next/static/chunks/ga.js"})
        self.assertTrue(any(l == "PASS" and "loaded by JavaScript" in m for l, _, m in f))

    def test_dns_verification_resolution(self):
        records = {"example.com": ["v=spf1 -all", "google-site-verification=abc"]}
        resolver = lambda name: records.get(name, [])
        self.assertTrue(setup_detect.google_dns_verified("www.example.com", resolver))
        self.assertTrue(setup_detect.google_dns_verified("blog.example.com", resolver))
        self.assertFalse(setup_detect.google_dns_verified("other.org", resolver))
        self.assertIsNone(setup_detect.google_dns_verified("other.org", lambda n: None))
        self.assertEqual(setup_detect.domain_candidates("127.0.0.1"), [])
        f = setup_detect.findings(setup_detect.detect_tags("", {}), google_dns=True)
        self.assertIn(("PASS", "gsc-verification"), {(l, c) for l, c, _ in f})


def _text(seed, n=120):
    words = ("invoice client payment freelance project hour rate tax receipt reminder due bank card late fee "
             "template report expense budget agency contract scope milestone deposit refund currency")
    vocab = words.split()
    x, out = seed, []
    for _ in range(n):
        x = (x * 1103515245 + 12345) % (1 << 31)
        out.append(vocab[x % len(vocab)])
    return " ".join(out)


class Similarity(unittest.TestCase):
    def test_pairs_canonical_skip_and_lsh(self):
        docs = {f"/p{i}": _text(i + 1) for i in range(80)}
        docs["/copy-of-p3"] = docs["/p3"]
        docs["/p7-variant"] = docs["/p7"].replace("invoice", "bill", 1)
        exact = similarity.near_duplicates(docs, threshold=0.8, exact_limit=1000)
        lsh = similarity.near_duplicates(docs, threshold=0.8, exact_limit=10)
        self.assertEqual(exact, lsh)  # banding finds the same pairs as the exact comparison
        pairs = {(a, b) for a, b, _ in exact}
        self.assertEqual(pairs, {("/copy-of-p3", "/p3"), ("/p7", "/p7-variant")})
        skip = similarity.near_duplicates(docs, threshold=0.8,
                                          skip=lambda a, b: {a, b} == {"/copy-of-p3", "/p3"})
        self.assertEqual({(a, b) for a, b, _ in skip}, {("/p7", "/p7-variant")})

    def test_repeated_blocks_and_findings(self):
        filler = ("In today's fast-paced world freelancers juggle many clients and need a simple way to send "
                  "invoices track payments and chase late payers without spending their whole evening on admin.")
        blocks = {"/a": [filler, "unique a"], "/b": [filler], "/c": [filler, "something else"], "/d": ["x"]}
        rep = similarity.repeated_blocks(blocks)
        self.assertEqual(rep[0][1], ["/a", "/b", "/c"])
        f = similarity.findings({k: " ".join(v) for k, v in blocks.items()}, blocks, total_pages=4)
        self.assertTrue(any(c == "repeated-block" and l == "WARN" for l, c, _ in f))
        long_pages = {k: " ".join(v) + " " + _text(i, 600) for i, (k, v) in enumerate(blocks.items())}
        f = similarity.findings(long_pages, blocks, total_pages=4)  # same note, but a small part of long pages
        self.assertEqual([l for l, c, _ in f if c == "repeated-block"], ["INFO"])


class SchemaRules(unittest.TestCase):
    def run_rules(self, obj):
        return schema_rules.check_blocks([json.dumps(obj)])

    def test_product_and_nested_offer(self):
        f = self.run_rules({"@context": "https://schema.org", "@type": "Product", "name": "Acme Pro"})
        self.assertTrue(any(l == "WARN" and "offers or review or aggregateRating" in m for l, _, m in f))
        f = self.run_rules({"@context": "https://schema.org", "@graph": [
            {"@type": "Product", "name": "Acme", "offers": {"@type": "Offer", "priceCurrency": "USD"},
             "review": {"@type": "Review", "reviewBody": "ok"}}]})
        self.assertTrue(any(l == "WARN" and m.startswith("Offer") and "price" in m for l, _, m in f))
        self.assertFalse(any(m.startswith("Review") for _, _, m in f))  # nested review isn't judged alone

    def test_breadcrumbs_faq_dates_and_context(self):
        f = self.run_rules({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "name": "Home", "item": "https://x.com/"}, {"@type": "ListItem", "position": 2}]})
        self.assertTrue(any("item 1 is missing position" in m for _, _, m in f))
        self.assertTrue(any("item 2 is missing name" in m for _, _, m in f))
        f = self.run_rules({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "Q?"}]})
        self.assertTrue(any(c == "schema-tip" and "government and health" in m for _, c, m in f))
        self.assertTrue(any(l == "WARN" and "acceptedAnswer" in m for l, _, m in f))
        f = self.run_rules({"@type": "Article", "headline": "x", "datePublished": "10/01/2026", "image": "/a.png"})
        self.assertTrue(any("no schema.org @context" in m for _, _, m in f))
        self.assertTrue(any("not an ISO 8601 date" in m for _, _, m in f))
        self.assertTrue(any(c == "schema-tip" and "relative URL" in m for _, c, m in f))

    def test_local_business_subtype_and_good_fixture(self):
        f = self.run_rules({"@context": "https://schema.org", "@type": "Dentist", "name": "Smile"})
        self.assertTrue(any(l == "WARN" and "address" in m for l, _, m in f))
        pg = seo_check.analyze_page(seo_check.load_local(os.path.join(FIX, "good_page.html")), local=True)
        self.assertFalse([x for x in pg["findings"] if x[1] == "schema" and x[0] != "PASS"])


class Titles(unittest.TestCase):
    def test_title_check_on_static_build(self):
        rows = gsc_analyze.load_tables(os.path.join(FIX, "titles_query_page.csv"))["titles_query_page.csv"]
        res = gsc_analyze.titles(rows, html_dir=os.path.join(FIX, "titles_site"))
        by = {p["page"].replace("https://acme.example", "") or "/": p for p in res["pages"]}
        self.assertTrue(res["keyword_check"])
        self.assertEqual(by["/"]["level"], "FAIL")                       # synonym title, keyword missing
        self.assertEqual(by["/"]["query"], "invoice software for freelancers")  # top query by impressions
        self.assertIn("after the cut-off", " ".join(by["/pricing"]["issues"]))
        self.assertIn("cut off in results", " ".join(by["/blog/how-to-write-an-invoice"]["issues"]))
        self.assertLessEqual(by["/blog/how-to-write-an-invoice"]["chars"], 60)  # <= 60 chars, still too wide
        self.assertEqual(by["/templates"]["level"], "PASS")
        self.assertEqual(res["pages"][0]["level"], "FAIL")              # worst first

    def test_plural_and_gerund_matching(self):
        lvl, issues, _ = gsc_analyze.title_issues("Writing Invoices for Agencies | Acme", "write invoice agency")
        self.assertEqual((lvl, issues), ("PASS", []))


class Checklist(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.file = os.path.join(self.dir, "SEO-CHECKLIST.md")

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = checklist.main(list(args) + ["--file", self.file])
        return code, out.getvalue()

    def test_items_match_reference_checklist(self):
        with open(os.path.join(ROOT, "skills", "seo-audit", "references", "checklist.md"), encoding="utf-8") as f:
            ref = re.findall(r"^\| ([TQOCL]\d+) \| ([^|]+?) \|", f.read(), re.M)
        self.assertEqual([(i, t) for i, _, t in checklist.ITEMS], ref)

    def test_init_update_manual_tick_and_roundtrip(self):
        self.assertEqual(self.run_cli("init", "--date", "2026-10-01")[0], 0)
        with open(self.file, encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(text.count("- [ ]"), 40)
        self.assertIn("Progress: 0/40", text)
        statuses = os.path.join(self.dir, "s.json")
        with open(statuses, "w") as f:
            json.dump({"T5": "pass", "O2": {"status": "fail", "note": "pricing title is 79 chars --> fix"},
                       "L5": "na"}, f)
        self.assertEqual(self.run_cli("update", "--statuses", statuses, "--date", "2026-10-02")[0], 0)
        with open(self.file, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("Progress: 1/39", text)               # L5 is N/A, so 39 apply
        self.assertIn("pricing title is 79 chars --> fix", text)
        state, _ = checklist.load(self.file)                  # "-->" in a note doesn't break the state
        self.assertEqual(state["items"]["O2"]["status"], "fail")
        self.assertEqual(checklist.render(state), text)       # re-rendering is stable
        with open(self.file, "w", encoding="utf-8") as f:     # the user ticks T1 by hand
            f.write(re.sub(r"- \[ \] (\S+) \*\*T1\*\*", r"- [x] \1 **T1**", text))
        self.run_cli("update", "--set", "O2=pass:fixed", "--date", "2026-10-03")
        state, _ = checklist.load(self.file)
        self.assertEqual(state["items"]["T1"]["status"], "pass")
        self.assertEqual(state["items"]["T1"]["note"], "marked done by hand")
        self.assertEqual(state["items"]["O2"]["history"], [["2026-10-02", "fail"], ["2026-10-03", "pass"]])
        with open(self.file, encoding="utf-8") as f:
            self.assertIn("Improved:", f.read())

    def test_rejects_bad_ids_and_statuses(self):
        self.assertEqual(self.run_cli("update", "--set", "Z9=pass")[0], 2)
        self.assertEqual(self.run_cli("update", "--set", "T1=great")[0], 2)
        self.assertFalse(os.path.exists(self.file))


class ImagesReportCli(unittest.TestCase):
    def test_local_image_weight(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "img"))
        with open(os.path.join(d, "img", "big.jpg"), "wb") as f:
            f.write(b"\0" * 260_000)
        with open(os.path.join(d, "img", "small.webp"), "wb") as f:
            f.write(b"\0" * 9_000)
        page = os.path.join(d, "index.html")
        with open(page, "w") as f:
            f.write('<html><head><title>t</title></head><body><h1>x</h1><img src="/img/big.jpg" alt="a" '
                    'loading="lazy"><img src="img/small.webp" alt="b"></body></html>')
        pg = seo_check.analyze_page(seo_check.load_local(page), local=True, images=True)
        warn = [m for l, c, m in pg["findings"] if c == "img-weight" and l == "WARN"]
        self.assertTrue(warn and "big.jpg (253 KB)" in warn[0])
        self.assertTrue(any(c == "img-lazy" and "first image" in m.lower() for _, c, m in pg["findings"]))

    def test_html_report_escapes_site_content(self):
        pg = {"url": "https://x.com/<b>", "title": "<script>alert(1)</script>", "title_length": 25,
              "findings": [("WARN", "title", 'Title is "<script>alert(1)</script>"')]}
        out = report_html.render_pages([pg])
        self.assertNotIn("<script", out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", out)

    def test_cli_cross_page_html_counts_and_color(self):
        d = tempfile.mkdtemp()
        body = _text(5, 150)
        for name in ("a.html", "b.html"):
            with open(os.path.join(d, name), "w") as f:
                f.write(f"<html><head><title>Same title</title></head><body><main><h1>x</h1><p>{body}</p>"
                        "</main></body></html>")
        html_path, counts_path = os.path.join(d, "r.html"), os.path.join(d, "c.json")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            seo_check.main(["page", os.path.join(d, "a.html"), os.path.join(d, "b.html"), "--html", html_path,
                            "--counts", counts_path, "--json"])
        data = json.loads(out.getvalue())
        cross = data[-1]
        self.assertEqual(cross["url"], "(across pages)")
        found = {c for _, c, _ in cross["findings"]}
        self.assertTrue({"duplicates", "near-duplicate"} <= found)
        with open(counts_path) as f:
            self.assertEqual(set(json.load(f)), {"FAIL", "WARN", "INFO", "PASS"})
        with open(html_path, encoding="utf-8") as f:
            self.assertIn("Across these pages", f.read())
        colored = io.StringIO()
        with contextlib.redirect_stdout(colored):
            seo_check.main(["page", os.path.join(d, "a.html"), "--color", "always"])
        self.assertIn("\033[", colored.getvalue())


if __name__ == "__main__":
    unittest.main()
