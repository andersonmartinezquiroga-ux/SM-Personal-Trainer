"""Unit tests for narrowly scoped personal-data submission; NEVER contacts YPAI."""
import unittest
from submit_ypai import clean_person,YPAI_URL

class OneTimeYpaiGateTests(unittest.TestCase):
    def test_expected_target(self):
        self.assertEqual(YPAI_URL,"https://freelancer.ypai.ai/jobs/openings/data-annotator-co")
    def test_valid_consent(self):
        self.assertEqual(clean_person("Test Person","test@example.invalid","Colombia",True,True),
                         ("Test Person","test@example.invalid"))
    def test_disallow_wrong_country(self):
        with self.assertRaises(ValueError):
            clean_person("Test Person","test@example.invalid","USA",True,True)
    def test_disallow_without_privacy_consent(self):
        with self.assertRaises(ValueError):
            clean_person("Test Person","test@example.invalid","Colombia",False,True)
    def test_disallow_without_contributor_terms(self):
        with self.assertRaises(ValueError):
            clean_person("Test Person","test@example.invalid","Colombia",True,False)
    def test_no_empty_email(self):
        with self.assertRaises(ValueError):
            clean_person("Test Person","", "Colombia",True,True)

if __name__=="__main__":unittest.main()
