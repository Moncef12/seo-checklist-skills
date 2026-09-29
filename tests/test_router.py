"""Keeps the /seo router consistent: menu, routing table, argument-hint and sibling skills must agree."""
import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
with open(os.path.join(ROOT, "skills", "seo", "SKILL.md"), encoding="utf-8") as _f:
    ROUTER = _f.read()
SKILLS = {d for d in os.listdir(os.path.join(ROOT, "skills")) if d != "seo"}


def menu_modes():
    block = ROUTER.split("## Menu", 1)[1]
    return {m for m in re.findall(r"^/seo (\w[\w-]*)", block, re.M)}


def table_modes():
    return set(re.findall(r"^\| `(\w[\w-]*)[ `]", ROUTER, re.M))


def hint_modes():
    hint = re.search(r'argument-hint: "\[(.*?)\]', ROUTER).group(1)
    return {m.strip() for m in hint.split("|")} - {"URL"}


class RouterConsistency(unittest.TestCase):
    def test_every_menu_command_is_routed(self):
        self.assertEqual(menu_modes() - table_modes(), set())

    def test_argument_hint_matches_table(self):
        self.assertEqual(hint_modes(), table_modes() - {"help"})

    def test_routes_point_to_real_skills(self):
        targets = set(re.findall(r"\| `(seo-[\w-]+)`", ROUTER))
        self.assertTrue(targets)
        self.assertEqual(targets - SKILLS, set())

    def test_router_is_explicit_only(self):
        self.assertIn("disable-model-invocation: true", ROUTER)


if __name__ == "__main__":
    unittest.main()
