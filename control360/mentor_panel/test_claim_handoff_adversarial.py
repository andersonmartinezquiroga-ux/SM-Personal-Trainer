"""Adversarial offline tests for the reserved-claim handoff; no submissions."""
import importlib.util
from pathlib import Path
import sys
import unittest

spec = importlib.util.spec_from_file_location("sjm_claim_handoff_adversarial", Path(__file__).with_name("claim_handoff_guard.py"))
guard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = guard
spec.loader.exec_module(guard)
CASE = "radar:commercial:ingresos-ypai-pose-keypoint-co-20261016"
URL = "https://freelancer.ypai.ai/jobs/openings/pose-keypoint-annotator-co"
CLAIM = {"reserved": True, "claim_id": "af0c4b1a-8cb1-47bd-89ab-5bb7f55b3a42",
         "reason": "reservation_only_live_form_review_required", "form_submitted": False}

def decide(**changes):
    args = dict(case_key=CASE, official_url=URL, trusted_case_key=CASE,
                trusted_official_url=URL, claim_result=CLAIM,
                official_receipt_exists=False, owner_session_verified=True)
    args.update(changes)
    return guard.assess_reserved_claim(**args)

class AdversarialClaimHandoffTests(unittest.TestCase):
    def test_control_valid_only_allows_review_never_submit(self):
        d = decide()
        self.assertTrue(d.review_ready)
        self.assertIs(d.form_submitted, False)

    def test_session_truthy_nonboolean_is_not_verified(self):
        for value in (1, "true", [], {"verified": True}, None):
            with self.subTest(value=repr(value)):
                self.assertFalse(decide(owner_session_verified=value).review_ready)

    def test_receipt_falsey_nonboolean_is_not_absent(self):
        for value in (0, "false", "", [], {}, None):
            with self.subTest(value=repr(value)):
                self.assertFalse(decide(official_receipt_exists=value).review_ready)

    def test_reserved_truthy_nonboolean_is_rejected(self):
        for value in (1, "true", [True]):
            with self.subTest(value=repr(value)):
                self.assertFalse(decide(claim_result={**CLAIM, "reserved": value}).review_ready)

    def test_submitted_falsey_nonboolean_is_rejected(self):
        for value in (0, "false", None):
            with self.subTest(value=repr(value)):
                self.assertFalse(decide(claim_result={**CLAIM, "form_submitted": value}).review_ready)

    def test_url_tricks_are_rejected_even_if_marked_trusted(self):
        urls = [
            URL.replace("freelancer.ypai.ai", "freelancer.ypai.ai.evil.test"),
            URL.replace("freelancer.ypai.ai", "user@freelancer.ypai.ai"),
            URL.replace("freelancer.ypai.ai", "freelancer.ypai.ai:443"),
            URL.replace("freelancer.ypai.ai", "FREELANCER.YPAI.AI"),
            URL.replace("/jobs/openings/", "/jobs/openings/../"),
            URL.replace("/jobs/openings/", "/jobs%2fopenings/"),
            URL + "/", URL + "#receipt", URL + "?submitted=true",
            "https://[bad/jobs/openings/pose-keypoint-annotator-co",
        ]
        for u in urls:
            with self.subTest(url=u):
                self.assertFalse(decide(official_url=u, trusted_official_url=u).review_ready)

    def test_invalid_claim_ids_rejected(self):
        for value in (None, 42, "", "af0c4b1a8cb147bd89ab5bb7f55b3a42",
                      "{af0c4b1a-8cb1-47bd-89ab-5bb7f55b3a42}"):
            with self.subTest(value=repr(value)):
                self.assertFalse(decide(claim_result={**CLAIM, "claim_id": value}).review_ready)

    def test_case_type_and_claim_shape_rejected(self):
        self.assertFalse(decide(case_key=None).review_ready)
        self.assertFalse(decide(claim_result=[CLAIM]).review_ready)

    def test_no_secret_reflection_on_deny(self):
        d = decide(claim_result={**CLAIM, "claim_id": "invalid", "secret": "CANARY_PRIVATE_4711"})
        self.assertFalse(d.review_ready)
        self.assertNotIn("CANARY_PRIVATE_4711", repr(d))
        self.assertIs(d.form_submitted, False)

if __name__ == "__main__":
    unittest.main()
