"""Security regression: inconsistent receipt metadata must fail closed."""
import unittest
from gateway_core import get_owner_mentor_receipt

OWNER = "qa-verified-owner-subject"

class ReceiptConsistencyTests(unittest.TestCase):
    def check(self, receipt):
        return get_owner_mentor_receipt(
            verified_subject=OWNER, owner_subject=OWNER,
            request_key="qa-receipt-20261020",
            read_privileged_receipt=lambda key: receipt,
        )

    def test_privacy_exposure_flag_blocks(self):
        got = self.check({"found": True, "state": "completed", "details_exposed": True})
        self.assertEqual(got, {"found": False, "state": "blocked", "details_exposed": False})

    def test_completed_with_found_false_blocks(self):
        got = self.check({"found": False, "state": "completed", "details_exposed": False})
        self.assertEqual(got["state"], "blocked")

    def test_not_found_with_found_true_blocks(self):
        got = self.check({"found": True, "state": "not_found", "details_exposed": False})
        self.assertEqual(got["state"], "blocked")

    def test_missing_found_blocks(self):
        got = self.check({"state": "completed", "details_exposed": False})
        self.assertEqual(got["state"], "blocked")

    def test_realistic_valid_receipt_remains_accepted(self):
        got = self.check({"found": True, "state": "completed", "details_exposed": False,
                          "command_id": 17, "is_final": True, "evidence_present": True,
                          "evidence_digest": "qa-digest", "private_result": "must-not-leak"})
        self.assertEqual(got["state"], "completed")
        self.assertNotIn("private_result", got)

    def test_not_found_still_accepted(self):
        got = self.check({"found": False, "state": "not_found", "details_exposed": False})
        self.assertEqual(got["state"], "not_found")

if __name__ == "__main__":
    unittest.main()
