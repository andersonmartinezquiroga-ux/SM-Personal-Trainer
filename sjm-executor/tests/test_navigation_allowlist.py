"""Regression checks for the existing browser navigation allowlist.

Run from repository root:
    python -m unittest discover -s sjm-executor/tests -p 'test_navigation_allowlist.py'
No browser, network, credentials, or external applications are accessed.
"""
import ast
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

SOURCE = Path(__file__).resolve().parents[1] / "applicant.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
selected = [node for node in tree.body if
            isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "ALLOWED" for t in node.targets)
            or isinstance(node, ast.FunctionDef) and node.name == "checked_url"]
assert len(selected) == 2, "Expected one ALLOWED assignment and checked_url function"
namespace = {"re": re, "urlparse": urlparse}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), "exec"), namespace)
checked_url = namespace["checked_url"]


class NavigationAllowlistRegression(unittest.TestCase):
    def setUp(self):
        self.valid = "https://jobs.lever.co/example/" + "a" * 26

    def test_exact_allowed_navigation(self):
        self.assertEqual(checked_url(self.valid), self.valid)
        self.assertEqual(checked_url(self.valid + "/apply"), self.valid + "/apply")

    def test_redirect_to_other_path_same_host_is_blocked(self):
        for url in (self.valid + "/submit", "https://jobs.lever.co/api/apply",
                    "https://jobs.lever.co/login", self.valid + "/apply/submit"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                checked_url(url)

    def test_redirect_to_other_host_is_blocked(self):
        for url in ("https://evil.example/" + "a" * 26,
                    "https://jobs.lever.co.evil.example/example/" + "a" * 26):
            with self.subTest(url=url), self.assertRaises(ValueError):
                checked_url(url)

    def test_unsafe_scheme_credentials_fragment_and_port(self):
        for url in (self.valid.replace("https:", "http:"),
                    self.valid.replace("https://", "https://user:secret@"),
                    self.valid + "#fragment",
                    self.valid.replace("jobs.lever.co", "jobs.lever.co:8443")):
            with self.subTest(url=url), self.assertRaises(ValueError):
                checked_url(url)

    def test_reject_non_string_and_overlong(self):
        for url in (None, 7, "x" * 501):
            with self.subTest(url=url), self.assertRaises(ValueError):
                checked_url(url)


if __name__ == "__main__":
    unittest.main()
