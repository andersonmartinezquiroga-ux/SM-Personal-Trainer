"""Offline authentication regression for SJM executor routes.

Tests only role boundaries; no browser, employers, or network requests.
"""
import unittest
from unittest.mock import Mock, patch

from api_v2 import API


class ApiAuthorizationTests(unittest.TestCase):
    @staticmethod
    def handler(path, credential):
        handler = API.__new__(API)
        handler.path = path
        handler.headers = {"Authorization": "Bearer " + credential}
        return handler

    @patch.dict("os.environ", {
        "EXECUTOR_TOKEN": "executor-unit-secret",
        "INSPECTOR_TOKEN": "inspector-unit-secret",
        "SUBMISSION_TOKEN": "submission-unit-secret",
    }, clear=True)
    def test_inspector_can_use_only_inspection_within_job_routes(self):
        allowed = self.handler("/jobs/inspect", "inspector-unit-secret")
        self.assertTrue(allowed.authorized_for_job())

        for path in ("/jobs/draft", "/jobs/prepare", "/self-test"):
            with self.subTest(path=path):
                handler = self.handler(path, "inspector-unit-secret")
                self.assertFalse(handler.authorized_for_job())
                handler.reply = Mock(return_value="blocked")
                handler.parse_json = Mock(side_effect=AssertionError("unauthorized body parsed"))
                self.assertEqual(handler.do_POST(), "blocked")
                handler.reply.assert_called_once_with(401, {"error": "unauthorized"})
                handler.parse_json.assert_not_called()

    @patch.dict("os.environ", {
        "EXECUTOR_TOKEN": "executor-unit-secret",
        "INSPECTOR_TOKEN": "inspector-unit-secret",
        "SUBMISSION_TOKEN": "submission-unit-secret",
    }, clear=True)
    def test_executor_remains_authorized_for_existing_non_submission_jobs(self):
        for path in ("/jobs/inspect", "/jobs/draft", "/jobs/prepare", "/self-test"):
            with self.subTest(path=path):
                handler = self.handler(path, "executor-unit-secret")
                self.assertTrue(handler.authorized_for_job())

    @patch.dict("os.environ", {
        "EXECUTOR_TOKEN": "executor-unit-secret",
        "INSPECTOR_TOKEN": "inspector-unit-secret",
        "SUBMISSION_TOKEN": "submission-unit-secret",
    }, clear=True)
    def test_submission_token_does_not_grant_browser_preparation(self):
        handler = self.handler("/jobs/prepare", "submission-unit-secret")
        self.assertFalse(handler.authorized_for_job())
        self.assertFalse(handler.authorized())

    def test_healthz_release_commit_matches_only_verified_full_sha(self):
        valid = "86ff616f749fc713075769acb45bf61d8008b27e"
        with patch.dict("os.environ", {"RENDER_GIT_COMMIT": valid}, clear=True):
            handler = self.handler("/healthz", "")
            handler.reply = Mock(side_effect=lambda status, body: body)
            result = handler.do_GET()
            self.assertEqual(result["release_commit"], valid)
            self.assertEqual(result["service"], "sjm-playwright-executor")
            self.assertEqual(result["external_submission"], "disabled_without_exact_case_approval")

        for invalid in ("", "short", "abc1234", "Z" * 40, "a" * 41):
            with self.subTest(commit=invalid), patch.dict(
                "os.environ", {"RENDER_GIT_COMMIT": invalid}, clear=True
            ):
                handler = self.handler("/healthz", "")
                handler.reply = Mock(side_effect=lambda status, body: body)
                self.assertEqual(handler.do_GET()["release_commit"], "unversioned")

    def test_prepare_response_carries_same_validated_release_identity(self):
        valid = "86ff616f749fc713075769acb45bf61d8008b27e"
        with patch.dict("os.environ", {"RENDER_GIT_COMMIT": valid}, clear=True):
            from api_v2 import release_commit
            self.assertEqual(release_commit(), valid)
        with patch.dict("os.environ", {"RENDER_GIT_COMMIT": "bad-token"}, clear=True):
            from api_v2 import release_commit
            self.assertEqual(release_commit(), "unversioned")

    @patch.dict("os.environ", {
        "INSPECTOR_TOKEN": "inspector-unit-secret",
    }, clear=True)
    def test_missing_executor_token_fails_closed(self):
        self.assertFalse(self.handler("/jobs/prepare", "inspector-unit-secret").authorized_for_job())
        self.assertFalse(self.handler("/self-test", "").authorized_for_job())
        self.assertTrue(self.handler("/jobs/inspect", "inspector-unit-secret").authorized_for_job())


if __name__ == "__main__":
    unittest.main()
