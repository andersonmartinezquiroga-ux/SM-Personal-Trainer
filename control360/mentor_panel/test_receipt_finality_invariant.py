"""Regression: Mentor receipt finality must agree with its state (offline)."""
import unittest
from gateway_core import get_owner_mentor_receipt

OWNER = "owner-test-123456"


def receipt(state, final):
    return get_owner_mentor_receipt(
        verified_subject=OWNER, owner_subject=OWNER,
        request_key="test_1234",
        read_privileged_receipt=lambda key: {
            "found": True, "state": state,
            "is_final": final, "details_exposed": False,
        },
    )


class ReceiptFinalityInvariantTests(unittest.TestCase):
    def test_queued_cannot_claim_final(self):
        self.assertEqual(receipt("queued", True)["state"], "blocked")

    def test_running_cannot_claim_final(self):
        self.assertEqual(receipt("running", True)["state"], "blocked")

    def test_completed_cannot_claim_unfinished(self):
        self.assertEqual(receipt("completed", False)["state"], "blocked")

    def test_failed_cannot_claim_unfinished(self):
        self.assertEqual(receipt("failed", False)["state"], "blocked")

    def test_queued_consistent(self):
        self.assertEqual(receipt("queued", False)["state"], "queued")

    def test_completed_consistent(self):
        self.assertEqual(receipt("completed", True)["state"], "completed")


if __name__ == "__main__":
    unittest.main()
