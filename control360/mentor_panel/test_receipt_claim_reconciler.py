"""Offline regression tests; synthetic data only, no external submissions."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('sjm_reconcile', Path(__file__).with_name('receipt_claim_reconciler.py'))
import sys
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

A = 'case-ypai-data'
B = 'case-ypai-text'
C = 'case-ypai-model'
D = 'case-ypai-pose'
URLS = {k: 'https://freelancer.ypai.ai/jobs/openings/' + k for k in (A, B, C, D)}
RECEIPTS = [{'case_key': k, 'application_url': URLS[k]} for k in (A, B, C)]


def audit(**changes):
    kw = dict(receipts=RECEIPTS, claims=[], trusted_cases=URLS,
              auth_user_count=1, receipts_rls=True, claims_rls=True,
              public_execute_granted=False, external_gateway_connected=True,
              expected_receipt_case_keys=frozenset((A, B, C)))
    kw.update(changes)
    return module.audit_snapshot(**kw)


class TestReconcile(unittest.TestCase):
    def test_healthy_snapshot_still_never_authorizes_submission(self):
        result = audit()
        self.assertTrue(result.passed)
        self.assertFalse(result.submission_authorized)
    def test_missing_owner_auth_blocks(self):
        self.assertIn('owner_auth_missing', audit(auth_user_count=0).findings)
    def test_auth_count_boolean_does_not_pass(self):
        self.assertIn('owner_auth_missing', audit(auth_user_count=True).findings)
    def test_rls_missing_blocks(self):
        self.assertIn('rls_missing_or_unverified', audit(claims_rls=False).findings)
    def test_public_execute_blocks(self):
        self.assertIn('public_execute_not_verified_denied', audit(public_execute_granted=True).findings)
    def test_gateway_disconnected_blocks(self):
        self.assertIn('external_gateway_not_connected', audit(external_gateway_connected=False).findings)
    def test_missing_receipt_detected(self):
        self.assertIn('official_receipts_missing_or_unexpected', audit(receipts=RECEIPTS[:2]).findings)
    def test_duplicate_receipt_detected(self):
        self.assertIn('duplicate_official_receipt', audit(receipts=RECEIPTS+[RECEIPTS[0]]).findings)
    def test_untrusted_url_detected(self):
        self.assertIn('receipt_trusted_url_mismatch', audit(receipts=[{**RECEIPTS[0], 'application_url':'https://evil.test'}]+RECEIPTS[1:]).findings)
    def test_claim_for_submitted_case_blocked(self):
        self.assertIn('claim_conflicts_with_official_receipt', audit(claims=[{**RECEIPTS[0], 'state':'reserved'}]).findings)
    def test_unknown_claim_blocked(self):
        self.assertIn('claim_trusted_url_mismatch', audit(claims=[{'case_key':'unknown', 'application_url':'https://bad.test', 'state':'reserved'}]).findings)
    def test_duplicate_claim_detected(self):
        row = {'case_key':D, 'application_url':URLS[D], 'state':'reserved'}
        self.assertIn('duplicate_claim', audit(claims=[row,row]).findings)
    def test_unknown_state_detected(self):
        self.assertIn('unknown_claim_state', audit(claims=[{'case_key':D, 'application_url':URLS[D], 'state':'sent?'}]).findings)
    def test_invalid_shapes_fail_closed(self):
        self.assertIn('invalid_snapshot_shape', audit(receipts=None).findings)
    def test_missing_catalog_fails_closed(self):
        self.assertIn("trusted_case_catalog_missing", audit(trusted_cases=None).findings)
    def test_unexpected_receipt_detected(self):
        self.assertIn('official_receipts_missing_or_unexpected', audit(receipts=RECEIPTS+[{'case_key':D, 'application_url':URLS[D]}]).findings)

if __name__ == '__main__':
    unittest.main()
