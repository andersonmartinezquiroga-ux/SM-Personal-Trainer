"""Offline regression suite: no external POST, no false receipts."""
import unittest
from unittest.mock import patch
from workflow_engine import prepare_workflow, _safe_fields

WELLONIS = "https://wellonis.com/signup/partner"

def source(**override):
    d = {"url":WELLONIS, "submitted":False, "listing_visible":True,
         "application_form_visible":True, "challenge_detected":False,
         "consent_or_captcha_present":True,
         "adapter_summary":{"adapter":"wellonis_partner_signup_readonly",
                            "required_approval_scopes":["terms_or_privacy"]},
         "filled_field_names":[]}
    d.update(override)
    return d

class WorkflowTests(unittest.TestCase):
    def test_signed_readonly_preflight_stops_at_owner_terms(self):
        with patch("workflow_engine.inspect",return_value=source()) as browser:
            r=prepare_workflow(WELLONIS)
            browser.assert_called_once_with(WELLONIS,fields={})
        self.assertEqual(r["workflow_stage"],"owner_authorization_required")
        self.assertEqual(r["workflow_steps"][-2]["status"],"not_executed")
        self.assertEqual(r["workflow_steps"][-1]["status"],"not_available")
        self.assertFalse(r["submitted"])
        self.assertFalse(r["completion_verified"])

    def test_draft_can_fill_text_without_being_submission(self):
        with patch("workflow_engine.inspect",
                   return_value=source(consent_or_captcha_present=False,
                                       adapter_summary={"required_approval_scopes":[]},
                                       filled_field_names=["name"])) as browser:
            r=prepare_workflow(WELLONIS,{"name":"SJM"})
        browser.assert_called_once_with(WELLONIS,fields={"name":"SJM"})
        self.assertEqual(r["workflow_steps"][3]["field_names"],["name"])
        self.assertEqual(r["workflow_stage"],"draft_filled_not_submitted")
        self.assertFalse(r["submitted"])

    def test_credentials_and_terms_cannot_be_autofilled(self):
        for name in ("password","access_token","agree_terms","privacyConsent",
                     "captcha","cardNumber","otp"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                _safe_fields({name:"forbidden"})
        with self.assertRaises(ValueError):_safe_fields({"email":""})
        with self.assertRaises(ValueError):_safe_fields({1:"value"})

    def test_unapproved_source_rejected_before_browser(self):
        with patch("workflow_engine.inspect") as browser:
            with self.assertRaises(ValueError):
                prepare_workflow("https://wellonis.com/admin")
            browser.assert_not_called()

    def test_security_challenge_never_signals_success(self):
        with patch("workflow_engine.inspect",return_value=source(challenge_detected=True)):
            r=prepare_workflow(WELLONIS)
        self.assertEqual(r["workflow_stage"],"human_challenge_required")
        self.assertFalse(r["external_submission"])

    def test_no_false_success_on_inspector_invariant_failure(self):
        with patch("workflow_engine.inspect",return_value=source(submitted=True)):
            with self.assertRaises(ValueError):
                prepare_workflow(WELLONIS)

if __name__=="__main__": unittest.main()
