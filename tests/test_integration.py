"""End-to-end test of `seo_check.py site` against the local demo site (no internet needed)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))
sys.path.insert(0, os.path.join(HERE, "..", "examples"))

import demo_site  # noqa: E402
import seo_check  # noqa: E402


class SiteCheckAgainstDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server, cls.base = demo_site.serve(port=0)
        cls.report = seo_check.check_site(cls.base, sample=20, crawl=50, workers=4, dns=False, images=True)
        cls.findings = [(lvl, check, msg) for fs in cls.report["sections"].values() for lvl, check, msg in fs]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def has(self, level, check, text=""):
        return any(l == level and c == check and text in m for l, c, m in self.findings)

    def test_reads_sitemap_index_and_gzip_child(self):
        self.assertEqual(self.report["sitemap_url_count"], 9)

    def test_noindex_page_in_sitemap(self):
        self.assertTrue(self.has("FAIL", "indexability", "/legacy"))

    def test_soft_404(self):
        self.assertTrue(self.has("FAIL", "soft-404"))

    def test_broken_internal_link(self):
        self.assertTrue(self.has("FAIL", "broken-link", "/features/reports"))

    def test_redirect_chain(self):
        self.assertTrue(self.has("WARN", "internal-redirect", "2-hop redirect chain (301 -> 301)"))

    def test_cookie_bounce(self):
        self.assertTrue(self.has("WARN", "cookie-redirect", "/app"))

    def test_orphans(self):
        self.assertTrue(self.has("WARN", "orphans", "/orphan-landing"))

    def test_respects_robots_txt(self):
        self.assertTrue(self.has("INFO", "crawl", "disallowed by robots.txt"))

    def test_pricing_page_issues(self):
        pricing = next(p for p in self.report["pages"] if p["url"].endswith("/pricing"))
        checks = {(l, c) for l, c, _ in pricing["findings"]}
        for expected in (("WARN", "title"), ("WARN", "meta-description"), ("WARN", "canonical"), ("WARN", "h1")):
            self.assertIn(expected, checks)

    def test_sections_in_reading_order(self):
        names = list(self.report["sections"])
        self.assertEqual(names[:2], ["Hosts & HTTPS", "Search engine setup"])
        self.assertLess(names.index("Duplicate content"), names.index("Links & orphans"))

    def test_setup_without_analytics(self):
        self.assertTrue(self.has("WARN", "analytics", "No GA4"))
        self.assertTrue(self.has("INFO", "gsc-verification"))
        self.assertTrue(self.has("INFO", "bing-verification"))

    def test_duplicate_content(self):
        self.assertTrue(self.has("WARN", "near-duplicate", "/orphan-landing"))
        self.assertTrue(self.has("WARN", "repeated-block", "Freelancers lose hours"))
        self.assertTrue(self.has("INFO", "thin-content", "/blog/invoice-template-guide"))
        dup = self.report["sections"]["Duplicate content"]
        self.assertFalse(any("/legacy" in m for _, _, m in dup))  # noindex pages are left out

    def test_schema_and_image_weight_on_sampled_pages(self):
        def page_findings(path):
            return next(p for p in self.report["pages"] if p["url"].rstrip("/").endswith(path))["findings"]
        self.assertTrue(any(l == "WARN" and c == "schema" and "BreadcrumbList" in m
                            for l, c, m in page_findings("/features/invoicing")))
        self.assertTrue(any(l == "WARN" and c == "img-weight" and "hero.png" in m
                            for l, c, m in page_findings(self.base)))

    def test_crawl_stays_on_site(self):
        self.assertTrue(self.has("INFO", "crawl", "redirect to another site"))
        self.assertTrue(self.has("INFO", "offsite-redirect", "/partner"))
        dup = " ".join(m for _, _, m in self.report["sections"]["Duplicate content"])
        self.assertNotIn("localhost", dup)
        self.assertFalse(any("localhost" in p["final_url"] for p in self.report["pages"]))

    def test_fail_on_exit_code(self):
        self.assertEqual(seo_check.exit_code(self.findings, "FAIL"), 1)
        self.assertEqual(seo_check.exit_code([("PASS", "x", "")], "WARN"), 0)


if __name__ == "__main__":
    unittest.main()
