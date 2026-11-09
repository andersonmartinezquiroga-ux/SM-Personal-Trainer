"""Offline regression checks for the existing Playwright navigation allowlist.

Run from sjm-executor/: python -m unittest discover -s diagnostics -p 'test_navigation_allowlist.py'
No browser, network, credentials, or submissions required.
"""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import MagicMock

ROOT = pathlib.Path(__file__).resolve().parents[1]

# applicant.py imports Playwright and form_adapter; checked_url itself needs neither.
sys.modules.setdefault("playwright", types.ModuleType("playwright"))
sync_api = types.ModuleType("playwright.sync_api")
sync_api.sync_playwright = MagicMock()
sync_api.TimeoutError = TimeoutError
sys.modules.setdefault("playwright.sync_api", sync_api)
adapter = types.ModuleType("form_adapter")
adapter.classify_application_form = MagicMock()
sys.modules.setdefault("form_adapter", adapter)
spec = importlib.util.spec_from_file_location("sjm_applicant_allowlist_test", ROOT / "applicant.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NavigationAllowlistTest(unittest.TestCase):
    BASE = "https://freelancer.ypai.ai/jobs/openings/data-annotator-co"

    def test_approved_public_get_url(self):
        self.assertEqual(module.checked_url(self.BASE), self.BASE)

    def test_reject_off_path_same_host(self):
        for suffix in ("/apply", "/../admin", "/login", "/private"):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                module.checked_url(self.BASE + suffix)

    def test_reject_host_spoofing(self):
        for url in (
            "https://freelancer.ypai.ai.evil.example/jobs/openings/data-annotator-co",
            "https://freelancer.ypai.ai@evil.example/jobs/openings/data-annotator-co",
            "https://evil.example@freelancer.ypai.ai/jobs/openings/data-annotator-co",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                module.checked_url(url)

    def test_reject_unsafe_protocol_port_fragment(self):
        for url in (
            self.BASE.replace("https:", "http:"),
            self.BASE.replace("freelancer.ypai.ai", "freelancer.ypai.ai:8443"),
            self.BASE + "#secret",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                module.checked_url(url)

    def test_reject_unknown_site(self):
        with self.assertRaises(ValueError):
            module.checked_url("https://example.org/")

    def test_asset_post_is_not_allowed(self):
        self.assertFalse(module.is_safe_readonly_asset(self.BASE, "POST"))

    def test_asset_http_is_not_allowed(self):
        self.assertFalse(module.is_safe_readonly_asset(self.BASE.replace("https:", "http:"), "GET"))


if __name__ == "__main__":
    unittest.main()
