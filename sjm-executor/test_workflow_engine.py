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

class SubmissionOutcomeTests(unittest.TestCase):
    def test_confirmed_requires_browser_post_and_receipt(self):
        from api_v2 import normalize_role_result
        result = dict(attempted_submit=True, confirmed=True, status="application_received",
                      confirmation_marker="thank you for applying", outgoing_post_count=1,
                      receipt_visible_after_click=True, receipt_http_status=200)
        self.assertIs(normalize_role_result(result)["submitted"], True)
        for change in ({"outgoing_post_count":0}, {"outgoing_post_count":2},
                       {"receipt_visible_after_click":False}, {"receipt_http_status":400},
                       {"confirmation_marker":None},
                       {"attempted_submit":False}, {"confirmed":False}):
            with self.subTest(change=change):
                outcome=normalize_role_result(dict(result, **change))
                self.assertIsNone(outcome["submitted"])
                self.assertFalse(outcome["automatic_retry_allowed"])

    def test_uncertain_and_invalid_results_fail_closed(self):
        from api_v2 import normalize_role_result, submission_outcome_uncertain
        for result in (None, {}, {"attempted_submit":True,"confirmed":False,
                                     "status":"submission_uncertain_timeout"}):
            with self.subTest(result=result):
                outcome=normalize_role_result(result)
                self.assertIsNone(outcome["submitted"])
                self.assertFalse(outcome["automatic_retry_allowed"])
        for error in (TimeoutError(),ConnectionResetError(),ValueError()):
            self.assertIsNone(submission_outcome_uncertain(error)["submitted"])

    def test_known_pre_submit_block_never_claims_receipt(self):
        from api_v2 import normalize_role_result
        outcome=normalize_role_result({"attempted_submit":False,"confirmed":False,
                                      "status":"blocked_role_not_open"})
        self.assertIs(outcome["submitted"],False)
        self.assertFalse(outcome["automatic_retry_allowed"])

class MotionRoleTests(unittest.TestCase):
    def test_exact_role_not_any_other_case(self):
        from submit_ypai import validate_role_request
        from applicant import checked_url
        key="radar:commercial:ingresos-ypai-motion-performer-co-20261124"
        url="https://freelancer.ypai.ai/jobs/openings/motion-performer-co"
        self.assertEqual(checked_url(url),url)
        self.assertEqual(validate_role_request("motion-performer-co",key)["opening"],
                         "Motion and Gesture Performer")
        with self.assertRaises(ValueError):
            validate_role_request("motion-performer-co","another-case")
        with self.assertRaises(ValueError):
            checked_url(url+"/submit")

    def test_motion_consent_is_application_only(self):
        from submit_ypai import clean_motion_applicant
        args=("Example Applicant","example@example.invalid","Colombia")
        self.assertEqual(clean_motion_applicant(*args,True,False),args[:2])
        for privacy,contract in ((True,True),(False,False),(True,None)):
            with self.assertRaises(ValueError):
                clean_motion_applicant(*args,privacy,contract)
        for invalid in ("invalid","name @example.invalid","name@example"):
            with self.assertRaises(ValueError):
                clean_motion_applicant("Example Applicant",invalid,"Colombia",True,False)

    def test_observed_motion_fields_and_optional_marketing(self):
        from submit_ypai import motion_field_schema_ok, MOTION_REVIEWED_FIELDS
        fields=sorted(MOTION_REVIEWED_FIELDS)
        self.assertTrue(motion_field_schema_ok(fields, ["name","email","consent"]))
        for invalid in (fields+["unknown_field"],fields+["name"],
                        [n for n in fields if n!="country"]):
            self.assertFalse(motion_field_schema_ok(invalid, ["name","email","consent"]))
        for required in ("partner_learn_consent","phone","cv","city"):
            self.assertFalse(motion_field_schema_ok(fields, ["name","email","consent",required]))

    def test_claim_bridge_accepts_only_durable_positive_reservation(self):
        from submit_ypai import reserve_motion_once
        import json
        claim="18c4d291-cdf2-45b4-90b9-b4057f36441a"
        with patch.dict("os.environ",{"SUBMISSION_TOKEN":"fictional-test-credential-000000"}):
            with patch("submit_ypai.build_opener") as opener:
                response=opener.return_value.open.return_value.__enter__.return_value
                response.status=200
                response.read.return_value=json.dumps({"reserved":True,"claim_id":claim,"form_submitted":False}).encode()
                self.assertEqual(reserve_motion_once(),claim)
                opener.return_value.open.assert_called_once()
            for data in ({"reserved":False},{"reserved":True,"claim_id":"invalid","form_submitted":False},{"reserved":True,"claim_id":claim,"form_submitted":True}):
                with patch("submit_ypai.build_opener") as opener:
                    response=opener.return_value.open.return_value.__enter__.return_value
                    response.status=200
                    response.read.return_value=json.dumps(data).encode()
                    with self.assertRaises(ValueError):
                        reserve_motion_once()
                    opener.return_value.open.assert_called_once()
            with patch("submit_ypai.build_opener") as opener:
                opener.return_value.open.side_effect=TimeoutError()
                with self.assertRaises(ValueError):
                    reserve_motion_once()
                opener.return_value.open.assert_called_once()

    def test_endpoint_missing_or_outside_origin_fails_closed(self):
        from submit_ypai import verified_submit_endpoint
        with patch.dict("os.environ",{"YPAI_MOTION_SUBMIT_URL":""}):
            with self.assertRaises(ValueError):
                verified_submit_endpoint("motion-performer-co")
        exact="https://freelancer.ypai.ai/api/jobs/apply"
        with patch.dict("os.environ",{"YPAI_MOTION_SUBMIT_URL":exact}):
            self.assertEqual(verified_submit_endpoint("motion-performer-co"),exact)
            with self.assertRaises(ValueError):
                verified_submit_endpoint("text-annotator-co")
        for bad in ("https://freelancer.ypai.ai/api/jobs/funnel",
                    "https://freelancer.ypai.ai/api/client-log",
                    "https://example.com/submit","http://freelancer.ypai.ai/submit",
                    "https://freelancer.ypai.ai/submit?token=x"):
            with patch.dict("os.environ",{"YPAI_MOTION_SUBMIT_URL":bad}):
                with self.assertRaises(ValueError):
                    verified_submit_endpoint("motion-performer-co")

if __name__=="__main__": unittest.main()
