"""Safety preflight checks: never start a browser for forbidden submissions.

These tests never launch Chromium, visit an external site, or submit a form.
"""
import unittest
from unittest.mock import patch

from executor import run


class ExecutorSafetyTests(unittest.TestCase):
    def test_external_submission_rejected_before_browser_start(self):
        with patch("executor.sync_playwright") as browser:
            with self.assertRaisesRegex(ValueError, "External form submission disabled"):
                run("https://example.org/apply", "unused.json",
                    submit=True, allow_host="example.org")
            browser.assert_not_called()

    def test_unapproved_host_rejected_before_browser_start(self):
        with patch("executor.sync_playwright") as browser:
            with self.assertRaisesRegex(ValueError, "Host not authorized"):
                run("https://other.example.org/apply", "unused.json",
                    submit=False, allow_host="example.org")
            browser.assert_not_called()

    def test_lookalike_loopback_host_never_counts_as_local(self):
        with patch("executor.sync_playwright") as browser:
            with self.assertRaisesRegex(ValueError, "External form submission disabled"):
                run("http://localhost.example.org/apply", "unused.json",
                    submit=True, allow_host="localhost.example.org")
            browser.assert_not_called()


if __name__ == "__main__":
    unittest.main()
