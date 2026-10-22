"""Release smoke for fail-closed YPAI proof classification (stdlib only)."""
import ast
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("submission_proof_gate.py")
spec = importlib.util.spec_from_file_location("submission_proof_gate", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SubmissionProofReleaseSmoke(unittest.TestCase):
    def test_import_has_no_missing_reconciler(self):
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertNotIn("receipt_reconciliation", imported)

    def test_static_page_is_not_receipt(self):
        result = module.assess_ypai_proof(source="public_job_page_html", evidence={"text": "Application received"})
        self.assertFalse(result.confirmed)

    def test_screenshot_is_not_receipt(self):
        self.assertFalse(module.assess_ypai_proof(source="public_job_page_screenshot", evidence={"text": "Application received"}).confirmed)

    def test_email_claim_is_not_independent_proof(self):
        self.assertFalse(module.assess_ypai_proof(source="gmail_official_receipt", evidence={"from": "noreply@ypai.ai", "confirmed": True}).confirmed)

    def test_post_submit_screen_needs_review(self):
        self.assertFalse(module.assess_ypai_proof(source="post_submit_browser_screen", evidence={"text": "Application received"}).confirmed)

    def test_private_row_is_not_new_receipt(self):
        self.assertFalse(module.assess_ypai_proof(source="supabase_private_receipt", evidence={"exists": True}).confirmed)

    def test_unknown_source_rejected(self):
        self.assertFalse(module.assess_ypai_proof(source="unknown", evidence={"confirmed": True}).confirmed)

    def test_no_private_payload_in_decision(self):
        result = module.assess_ypai_proof(source="unknown", evidence={"token": "do-not-echo"})
        self.assertEqual(set(vars(result)), {"confirmed", "reason"})


if __name__ == "__main__":
    unittest.main()
