"""Offline tests for the shared scripts. Run: python3 -m unittest discover -s tests -v"""
import contextlib
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(HERE, "..", "shared"))

import gsc_analyze  # noqa: E402
import lengths  # noqa: E402
import seo_check  # noqa: E402


def page(name):
    return seo_check.analyze_page(seo_check.load_local(os.path.join(FIX, name)), local=True)


def levels(pg, check):
    return {lvl for lvl, c, _ in pg["findings"] if c == check}


class PageChecks(unittest.TestCase):
    def test_bad_page_flags_core_problems(self):
        pg = page("bad_page.html")
        self.assertIn("WARN", levels(pg, "title"))          # "Home" is 4 chars
        self.assertIn("WARN", levels(pg, "meta-description"))
        self.assertIn("FAIL", levels(pg, "h1"))
        self.assertIn("WARN", levels(pg, "heading-order"))  # H2 -> H4
        self.assertIn("FAIL", levels(pg, "viewport"))
        self.assertIn("FAIL", levels(pg, "schema"))          # invalid JSON-LD
        self.assertIn("WARN", levels(pg, "canonical"))
        self.assertIn("WARN", levels(pg, "internal-links"))  # nofollow internal
        self.assertEqual(pg["images"]["missing_alt"], 1)     # alt="" is valid (decorative)

    def test_good_page_passes(self):
        pg = page("good_page.html")
        self.assertEqual(pg["title_length"], 52)
        for check in ("title", "meta-description", "h1", "canonical", "schema", "img-alt"):
            self.assertEqual(levels(pg, check), {"PASS"}, check)
        self.assertFalse(any(lvl == "FAIL" for lvl, _, _ in pg["findings"]))
        self.assertTrue(pg["has_date_modified"])
        self.assertIn("BreadcrumbList", pg["schema_types"])
        self.assertTrue(pg["intro"].startswith("Payly lets freelancers"))

    def test_url_issues(self):
        self.assertIn("underscores in path (hyphens are preferred)",
                      seo_check.url_issues("https://x.com/My_Page"))
        self.assertEqual(seo_check.url_issues("https://x.com/clean-url"), [])

    def test_sitemap_parsing(self):
        xml = (b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
               b'<url><loc>https://x.com/a</loc><lastmod>2026-01-01</lastmod></url>'
               b'<url><loc>https://x.com/b</loc></url></urlset>')
        kind, entries = seo_check.parse_sitemap(xml)
        self.assertEqual(kind, "urlset")
        self.assertEqual(entries, [("https://x.com/a", "2026-01-01"), ("https://x.com/b", None)])

    def test_cli_page_markdown(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            seo_check.main(["page", os.path.join(FIX, "bad_page.html")])
        self.assertIn("No H1", out.getvalue())


class LengthChecks(unittest.TestCase):
    def test_exact_counts_and_verdicts(self):
        out = io.StringIO()
        title = "Invoice Software for Freelancers: Get Paid Faster | Acme"
        with contextlib.redirect_stdout(out):
            lengths.main(["--title", title, "Home", "--meta", "x" * 170])
        text = out.getvalue()
        self.assertIn(f"| title | {len(title)} |", text)
        self.assertIn("| title | 4 |", text)
        self.assertIn("short (target 50-60)", text)
        self.assertIn("long (target 120-160)", text)

    def test_pixel_estimate_orders_widths(self):
        self.assertGreater(lengths.px("WWWW"), lengths.px("iiii"))


class GscChecks(unittest.TestCase):
    def test_quick_wins_from_zip(self):
        tables = gsc_analyze.load_tables(os.path.join(FIX, "gsc_export.zip"))
        self.assertEqual(set(tables), {"Queries", "Pages"})
        res = gsc_analyze.quick_wins(tables["Queries"], 100)
        self.assertEqual([r["key"] for r in res["low_ctr"]], ["invoice software"])
        self.assertEqual({r["key"] for r in res["page_two"]},
                         {"how to write an invoice", "what is a pro forma invoice"})
        self.assertIn("how to write an invoice", [r["key"] for r in res["questions"]])

    def test_number_parsing_all_locales(self):
        n = gsc_analyze._num
        self.assertEqual(n("1,234"), 1234)
        self.assertEqual(n("12 000"), 12000)
        self.assertEqual(n("1.234,5"), 1234.5)
        self.assertAlmostEqual(n("0,33 %"), 0.0033)
        self.assertAlmostEqual(n("4.5%"), 0.045)
        self.assertEqual(n("4,2"), 4.2)

    def test_french_export(self):
        rows = gsc_analyze.load_tables(os.path.join(FIX, "Queries_fr.csv"))["Queries_fr.csv"]
        res = gsc_analyze.quick_wins(rows, 100)
        self.assertEqual([r["key"] for r in res["low_ctr"]], ["logiciel de facturation"])
        self.assertEqual([r["key"] for r in res["page_two"]], ["comment faire une facture"])

    def test_decliners(self):
        rows = gsc_analyze.load_tables(os.path.join(FIX, "compare_pages.csv"))["compare_pages.csv"]
        res = gsc_analyze.decliners(rows, 10)
        keys = [r["key"] for r in res["decliners"]]
        self.assertEqual(keys[0], "https://example.com/templates")    # lost 500 clicks
        self.assertIn("https://example.com/blog/old", keys)           # position 14.5 -> 18
        self.assertNotIn("https://example.com/", keys)

    def test_cannibalization(self):
        rows = gsc_analyze.load_tables(os.path.join(FIX, "query_page.csv"))["query_page.csv"]
        res = gsc_analyze.cannibalization(rows, 0.1)
        self.assertEqual(len(res["cannibalized"]), 1)
        c = res["cannibalized"][0]
        self.assertEqual(c["query"], "invoice template")
        self.assertEqual(len(c["pages"]), 2)  # the 1% page is below the share threshold


if __name__ == "__main__":
    unittest.main()
