"""Offline safety regression; no network, credentials or external submissions."""
import importlib.util
from pathlib import Path
import sys
import unittest

spec = importlib.util.spec_from_file_location("claim_handoff_guard", Path(__file__).with_name("claim_handoff_guard.py"))
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

CASE = "radar:commercial:ingresos-ypai-pose-keypoint-co-20261016"
URL = "https://freelancer.ypai.ai/jobs/openings/pose-keypoint-annotator-co"
CLAIM = {"reserved": True, "claim_id": "af0c4b1a-8cb1-47bd-89ab-5bb7f55b3a42",
         "reason": "reservation_only_live_form_review_required", "form_submitted": False}


def decide(**overrides):
    args = dict(case_key=CASE, official_url=URL, trusted_case_key=CASE,
                trusted_official_url=URL, claim_result=CLAIM,
                official_receipt_exists=False, owner_session_verified=True)
    args.update(overrides)
    return module.assess_reserved_claim(**args)


class ClaimHandoffGuardTests(unittest.TestCase):
    def test_valid_reservation_only_allows_review(self):
        d = decide()
        self.assertTrue(d.review_ready)
        self.assertFalse(d.form_submitted)

    def test_owner_session_required(self):
        self.assertFalse(decide(owner_session_verified=False).review_ready)

    def test_missing_case_blocked(self):
        self.assertFalse(decide(case_key="").review_ready)

    def test_case_mismatch_blocked(self):
        self.assertFalse(decide(case_key="other").review_ready)

    def test_url_mismatch_blocked(self):
        self.assertFalse(decide(official_url=URL + "-wrong").review_ready)

    def test_query_token_blocked(self):
        u = URL + "?token=secret"
        self.assertFalse(decide(official_url=u, trusted_official_url=u).review_ready)

    def test_http_blocked(self):
        u = URL.replace("https:", "http:")
        self.assertFalse(decide(official_url=u, trusted_official_url=u).review_ready)

    def test_host_spoof_blocked(self):
        u = "https://freelancer.ypai.ai.evil.test/jobs/openings/pose-keypoint-annotator-co"
        self.assertFalse(decide(official_url=u, trusted_official_url=u).review_ready)

    def test_existing_receipt_blocked(self):
        self.assertFalse(decide(official_receipt_exists=True).review_ready)

    def test_unknown_receipt_status_blocked(self):
        self.assertFalse(decide(official_receipt_exists=None).review_ready)

    def test_missing_claim_blocked(self):
        self.assertFalse(decide(claim_result=None).review_ready)

    def test_failed_claim_blocked(self):
        self.assertFalse(decide(claim_result={**CLAIM, "reserved": False}).review_ready)

    def test_invalid_claim_id_blocked(self):
        self.assertFalse(decide(claim_result={**CLAIM, "claim_id": "abc"}).review_ready)

    def test_claim_saying_submitted_blocked(self):
        self.assertFalse(decide(claim_result={**CLAIM, "form_submitted": True}).review_ready)

    def test_wrong_claim_reason_blocked(self):
        self.assertFalse(decide(claim_result={**CLAIM, "reason": "unknown"}).review_ready)

    def test_no_sensitive_payload_in_output(self):
        d = decide(claim_result={**CLAIM, "secret": "do-not-echo"})
        self.assertEqual(set(vars(d)), {"review_ready", "reason", "form_submitted"})
        self.assertNotIn("do-not-echo", repr(d))


if __name__ == "__main__":
    unittest.main()
