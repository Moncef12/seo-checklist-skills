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
        cls.report = seo_check.check_site(cls.base, sample=20, crawl=50, workers=4)
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

    def test_fail_on_exit_code(self):
        self.assertEqual(seo_check.exit_code(self.findings, "FAIL"), 1)
        self.assertEqual(seo_check.exit_code([("PASS", "x", "")], "WARN"), 0)


if __name__ == "__main__":
    unittest.main()
