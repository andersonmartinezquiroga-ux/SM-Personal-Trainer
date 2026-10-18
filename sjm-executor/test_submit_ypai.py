"""Unit tests for role-specific YPAI safety gates; NEVER contacts YPAI."""
import unittest
from submit_ypai import (
    clean_person, validate_role_request, role_url, YPAI_URL, ROLE_CONFIG
)

class YpaiGateTests(unittest.TestCase):
    def test_old_data_target_is_stable_and_locked(self):
        self.assertEqual(
            YPAI_URL,
            "https://freelancer.ypai.ai/jobs/openings/data-annotator-co",
        )
        self.assertTrue(ROLE_CONFIG["data-annotator-co"]["already_submitted"])

    def test_valid_consent(self):
        self.assertEqual(
            clean_person("Test Person", "test@example.invalid", "Colombia", True, True),
            ("Test Person", "test@example.invalid"),
        )

    def test_role_case_pair_required(self):
        cfg = validate_role_request(
            "text-annotator-co",
            "radar:commercial:ingresos-ypai-text-annotator-co-20261016",
        )
        self.assertEqual(cfg["opening"], "Text and NLP Annotator")

    def test_role_case_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            validate_role_request(
                "text-annotator-co",
                "radar:commercial:ingresos-ypai-model-evaluator-co-20261016",
            )

    def test_already_submitted_data_role_rejected(self):
        with self.assertRaises(ValueError):
            validate_role_request(
                "data-annotator-co",
                "radar:commercial:ingresos-ypai-data-annotator-co-20261016",
            )

    def test_unknown_role_rejected(self):
        with self.assertRaises(ValueError):
            role_url("arbitrary-role")

    def test_wrong_country_rejected(self):
        with self.assertRaises(ValueError):
            clean_person("Test Person", "test@example.invalid", "USA", True, True)

    def test_missing_privacy_consent_rejected(self):
        with self.assertRaises(ValueError):
            clean_person("Test Person", "test@example.invalid", "Colombia", False, True)

    def test_missing_terms_rejected(self):
        with self.assertRaises(ValueError):
            clean_person("Test Person", "test@example.invalid", "Colombia", True, False)

    def test_empty_email_rejected(self):
        with self.assertRaises(ValueError):
            clean_person("Test Person", "", "Colombia", True, True)

if __name__ == "__main__":
    unittest.main()
