"""Offline regression checks: no production identities or services."""
import unittest
from gateway_core import AccessDenied, require_verified_owner


class OwnerSessionBoundaryTests(unittest.TestCase):
    def test_missing_verified_subject_rejected(self):
        with self.assertRaises(AccessDenied):
            require_verified_owner(None, "fictional-owner-123456")

    def test_other_verified_subject_rejected(self):
        with self.assertRaises(AccessDenied):
            require_verified_owner("fictional-other-123456", "fictional-owner-123456")


if __name__ == "__main__":
    unittest.main()
