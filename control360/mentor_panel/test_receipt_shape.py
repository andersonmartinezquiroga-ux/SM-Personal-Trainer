"""SJM Control 360: regression tests for nested receipt values."""
import unittest
from gateway_core import get_owner_mentor_receipt

OWNER = "fictional-owner-subject-123"

class ReceiptShapeTests(unittest.TestCase):
    def check_blocked(self, key, value):
        payload = {
            "found": True, "command_id": 9, "state": "completed",
            "intent": "estado_sistema", "authorization_level": "automatic",
        }
        payload[key] = value
        result = get_owner_mentor_receipt(
            verified_subject=OWNER,
            owner_subject=OWNER,
            request_key="qa-receipt-shape-1",
            read_privileged_receipt=lambda _: payload,
        )
        self.assertEqual(result, {
            "found": False, "state": "blocked", "details_exposed": False,
        })

    def test_nested_digest_rejected(self):
        self.check_blocked("evidence_digest", {"nested": "redacted"})

    def test_nested_evidence_type_rejected(self):
        self.check_blocked("evidence_type", ["unexpected"])

    def test_nested_command_id_rejected(self):
        self.check_blocked("command_id", {"id": 9})

if __name__ == "__main__":
    unittest.main()
