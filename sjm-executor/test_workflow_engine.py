"""Offline regression suite: no external POST, no false receipts."""
import unittest
import json
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
                                       filled_field_names=["name"], draft_offline=True,
                                       required_fields=[{"name":"name"}],
                                       unidentified_required_count=0,
                                       fields=[{"name":"name","required":True}])) as browser:
            r=prepare_workflow(WELLONIS,{"name":"SJM"})
        browser.assert_called_once_with(WELLONIS,fields={"name":"SJM"})
        self.assertEqual(r["workflow_steps"][3]["field_names"],["name"])
        self.assertEqual(r["workflow_stage"],"draft_filled_not_submitted")
        self.assertFalse(r["submitted"])

    def test_draft_readback_reports_missing_even_when_consent_required(self):
        with patch("workflow_engine.inspect",return_value=source(
            draft_offline=True,filled_field_names=["name","name","unrequested"])):
            r=prepare_workflow(WELLONIS,{"name":"Example","email":"example@example.invalid"})
        self.assertEqual(r["workflow_stage"],"owner_authorization_required")
        self.assertEqual(r["draft_verification"]["verified_field_names"],["name"])
        self.assertEqual(r["draft_verification"]["missing_field_names"],["email"])
        self.assertFalse(r["draft_verification"]["all_requested_fields_verified"])
        self.assertFalse(r["submitted"])

    def test_unisolated_draft_never_counts_as_verified(self):
        with patch("workflow_engine.inspect",return_value=source(filled_field_names=["name"])):
            r=prepare_workflow(WELLONIS,{"name":"Example"})
        self.assertEqual(r["draft_verification"]["verified_field_names"],[])
        self.assertFalse(r["draft_verification"]["all_requested_fields_verified"])

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

class ReviewedRadioTests(unittest.TestCase):
    def test_exact_reviewed_nonconsent_group(self):
        from applicant import reviewed_radio_choice
        url="https://freelancer.ypai.ai/jobs/openings/conversation-video-spanish-co"
        yes="Yes, Spanish is my first language"
        no="No, Spanish is not my first language"
        options=[dict(label=no,enabled=True,visible=True),dict(label=yes,enabled=True,visible=True)]
        self.assertEqual(reviewed_radio_choice(url,"l1",yes,options),1)
        self.assertEqual(reviewed_radio_choice(url,"l1",no,options),0)
        self.assertIsNone(reviewed_radio_choice(url,"consent",yes,options))
        self.assertIsNone(reviewed_radio_choice(url+"/other","l1",yes,options))
        self.assertIsNone(reviewed_radio_choice(url,"l1","Yes",options))
        self.assertIsNone(reviewed_radio_choice(url,"l1",yes,options+[options[1]]))
        self.assertIsNone(reviewed_radio_choice(url,"l1",yes,[dict(label=yes,enabled=False,visible=True)]))

class LocalAttachmentTests(unittest.TestCase):
    def test_pdf_attach_and_readback_without_network(self):
        from applicant import attach_pdf_in_isolated_draft
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            ctx=browser.new_context(service_workers="block")
            try:
                page=ctx.new_page()
                page.set_content('<form><label>CV<input type="file" name="resume" accept=".pdf"></label></form>')
                content=b"%PDF-1.4\\n% Local synthetic diagnostic only\\n%%EOF"
                result=attach_pdf_in_isolated_draft(page,"resume","offline-test.pdf",content)
                self.assertTrue(result["verified"])
                self.assertFalse(result["external_upload"])
                page.set_content('<form><input type="file" name="resume" accept=".jpg"></form>')
                self.assertEqual(attach_pdf_in_isolated_draft(page,"resume","offline-test.pdf",content)["reason"],"pdf_not_accepted")
                with self.assertRaises(ValueError):
                    attach_pdf_in_isolated_draft(page,"resume","../secret.pdf",content)
                with self.assertRaises(ValueError):
                    attach_pdf_in_isolated_draft(page,"resume","test.pdf",b"not a PDF")
            finally:
                ctx.close()
                browser.close()

class LocalWizardTests(unittest.TestCase):
    def test_reviewed_transition_idempotent_and_no_submission(self):
        from applicant import advance_isolated_form_step
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            ctx=browser.new_context(service_workers="block")
            try:
                page=ctx.new_page()
                page.set_content("""<form><section id="a"><input name="first" required value="example"><button type="button" onclick="document.getElementById('a').hidden=true;document.getElementById('b').hidden=false">Next</button></section><section id="b" hidden><input name="second"><button type="submit">Next</button></section></form>""")
                result=advance_isolated_form_step(page,"first","second")
                self.assertTrue(result["verified"])
                self.assertEqual(result["action"],"advanced")
                self.assertFalse(result["external_submission"])
                self.assertEqual(advance_isolated_form_step(page,"first","second")["action"],"already_at_next_step")
                page.set_content('<form><input name="first" required value="example"><input name="second" hidden><button type="submit">Next</button></form>')
                self.assertFalse(advance_isolated_form_step(page,"first","second")["verified"])
                with self.assertRaises(ValueError):
                    advance_isolated_form_step(page,"first","second","Submit")
            finally:
                ctx.close()
                browser.close()

class ConditionalDraftTests(unittest.TestCase):
    def test_reviewed_order_without_inventing_fields(self):
        from applicant import ordered_draft_fields
        url="https://freelancer.ypai.ai/jobs/openings/conversation-video-spanish-co"
        fields={"specialty":"Example","field_of_study":"Example","education_level":"Reviewed choice","apply-profession":"Example role"}
        self.assertEqual([k for k,v in ordered_draft_fields(url,fields)],
                         ["education_level","apply-profession","specialty","field_of_study"])
        self.assertEqual(dict(ordered_draft_fields(url,fields)),fields)
        self.assertEqual(ordered_draft_fields(url,{"specialty":"Example"}),[("specialty","Example")])
        self.assertEqual(ordered_draft_fields("https://example.invalid",fields),list(fields.items()))

class ProfessionWidgetTests(unittest.TestCase):
    def test_id_based_profession_requires_exact_choice_and_backing(self):
        from applicant import select_reviewed_profession
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            ctx=browser.new_context(offline=True,service_workers="block")
            try:
                page=ctx.new_page()
                page.set_content("""<form><input id="apply-profession"><input type="hidden" name="current_role"><div role="listbox"><div role="option" onclick="document.querySelector('[name=current_role]').value='local-id';document.getElementById('apply-profession').value='Personal trainer'">Personal trainer</div></div></form>""")
                self.assertEqual(select_reviewed_profession(page.locator("form"),"Personal trainer"),(True,"profession_selection_verified"))
                page.set_content('<form><input id="apply-profession"><input type="hidden" name="current_role"></form>')
                self.assertEqual(select_reviewed_profession(page.locator("form"),"Personal trainer"),(False,"profession_requires_reviewed_local_choice"))
                self.assertEqual(page.locator('[name=current_role]').input_value(),"")
            finally:
                ctx.close()
                browser.close()

class FinalFieldConsistencyTests(unittest.TestCase):
    def test_id_lookup_ambiguity_and_final_readback(self):
        from applicant import exact_draft_locator,verify_draft_field
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            ctx=browser.new_context(offline=True,service_workers="block")
            try:
                page=ctx.new_page()
                page.set_content('<form><input id="city" value="Example"><select name="education"><option selected>Diploma</option></select></form>')
                form=page.locator("form")
                url="https://example.invalid"
                self.assertEqual(exact_draft_locator(form,"city").count(),1)
                self.assertTrue(verify_draft_field(form,url,"city","Example"))
                self.assertTrue(verify_draft_field(form,url,"education","Diploma"))
                page.locator("#city").fill("Changed")
                self.assertFalse(verify_draft_field(form,url,"city","Example"))
                page.set_content('<form><input id="city" value="Example"><input name="city" value="Example"></form>')
                self.assertFalse(verify_draft_field(page.locator("form"),url,"city","Example"))
                page.set_content('<form><input type="hidden" name="city" value="Example"></form>')
                self.assertFalse(verify_draft_field(page.locator("form"),url,"city","Example"))
            finally:
                ctx.close()
                browser.close()

class GreenhouseExactAdapterTests(unittest.TestCase):
    def test_exact_readonly_paths(self):
        from applicant import checked_url,is_safe_readonly_asset
        from form_adapter import classify_application_form
        urls=["https://job-boards.greenhouse.io/agency/jobs/4675669101",
              "https://job-boards.greenhouse.io/agency/jobs/4787634101",
              "https://job-boards.greenhouse.io/agency/jobs/4778246101",
              "https://job-boards.eu.greenhouse.io/agency/jobs/4784908101"]
        for url in urls:
            self.assertEqual(checked_url(url),url)
            self.assertTrue(is_safe_readonly_asset(url,"GET"))
            self.assertFalse(is_safe_readonly_asset(url,"POST"))
            self.assertEqual(classify_application_form(url,[])["adapter"],"greenhouse_exact_listing_readonly")
            with self.assertRaises(ValueError):
                checked_url(url+"?token=x")
            with self.assertRaises(ValueError):
                checked_url(url+"/apply")
        with self.assertRaises(ValueError):
            checked_url("https://job-boards.greenhouse.io/agency/jobs/123")
        self.assertFalse(is_safe_readonly_asset("https://job-boards.greenhouse.io/api/apply","GET"))

class PublicFieldMetadataTests(unittest.TestCase):
    def test_external_labels_and_custom_widgets_without_values(self):
        from applicant import public_field_metadata
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            ctx=browser.new_context(offline=True,service_workers="block")
            try:
                page=ctx.new_page()
                page.set_content('<form><label for="degree">Education level</label><input id="degree" role="combobox" aria-required="true" value="private example"><span id="question">Language proficiency</span><input name="q" aria-labelledby="question" required><input required></form>')
                degree=public_field_metadata(page.locator("#degree"))
                self.assertEqual(degree["label"],"Education level")
                self.assertEqual(degree["identity"],"id")
                self.assertTrue(degree["custom_choice"])
                self.assertTrue(degree["required"])
                self.assertNotIn("private example",str(degree))
                self.assertEqual(public_field_metadata(page.locator('[name="q"]'))["label"],"Language proficiency")
                self.assertEqual(public_field_metadata(page.locator('input').last)["identity"],"unidentified")
            finally:
                ctx.close()
                browser.close()

class GreenhouseDraftScopeTests(unittest.TestCase):
    def test_only_exact_synthetic_diagnostic_enabled(self):
        from applicant import approved_draft_mapping,GREENHOUSE_DRAFT_DIAGNOSTIC_URL,GREENHOUSE_SYNTHETIC_FIELDS
        u=GREENHOUSE_DRAFT_DIAGNOSTIC_URL
        self.assertTrue(approved_draft_mapping(u,dict(GREENHOUSE_SYNTHETIC_FIELDS)))
        self.assertFalse(approved_draft_mapping(u,{"first_name":"Other"}))
        self.assertFalse(approved_draft_mapping(u,{**GREENHOUSE_SYNTHETIC_FIELDS,"consent":"yes"}))
        self.assertFalse(approved_draft_mapping("https://job-boards.greenhouse.io/agency/jobs/4787634101",GREENHOUSE_SYNTHETIC_FIELDS))
        self.assertTrue(approved_draft_mapping(u,{}))

class FullFormReadinessTests(unittest.TestCase):
    def test_verified_subset_does_not_clear_required_fields(self):
        with patch("workflow_engine.inspect",return_value=source(
            draft_offline=True,filled_field_names=["name"],
            required_fields=[{"name":"name"},{"name":"city"}],
            unidentified_required_count=2)):
            r=prepare_workflow(WELLONIS,{"name":"Example"})
        self.assertTrue(r["draft_verification"]["all_requested_fields_verified"])
        self.assertFalse(r["full_form_readiness"]["full_form_verified"])
        self.assertEqual(r["full_form_readiness"]["required_field_names_missing"],["city"])
        self.assertEqual(r["next_action"],"resolve_remaining_required_fields")

class LocalComboboxChoiceTests(unittest.TestCase):
    def test_only_linked_public_options_are_collected(self):
        from applicant import inspect_local_combobox_choices
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            ctx=browser.new_context(offline=True,service_workers="block")
            try:
                page=ctx.new_page()
                page.set_content('<form><input id="degree" role="combobox" aria-controls="degree-list"><div role="listbox" id="degree-list"><div role="option">Diploma</div><div role="option" aria-disabled="true">Unavailable</div></div><div role="listbox" id="other"><div role="option">Other field</div></div></form>')
                result=inspect_local_combobox_choices(page,"degree")
                self.assertEqual(result["labels"],["Diploma"])
                self.assertEqual(page.locator("#degree").input_value(),"")
                self.assertEqual(inspect_local_combobox_choices(page,"absent")["status"],"combobox_not_unique")
            finally:
                ctx.close()
                browser.close()

class UnlinkedComboboxTests(unittest.TestCase):
    def test_unique_new_visible_list_and_reject_ambiguous(self):
        from applicant import inspect_local_combobox_choices
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            ctx=browser.new_context(offline=True,service_workers="block")
            try:
                page=ctx.new_page()
                page.set_content("""<form><input id="degree" role="combobox" onclick="document.getElementById('opts').hidden=false"><div id="opts" role="listbox" hidden><div role="option">Diploma</div></div></form>""")
                self.assertEqual(inspect_local_combobox_choices(page,"degree")["labels"],["Diploma"])
                page.set_content("""<form><input id="degree" role="combobox"><div role="listbox"><div role="option">Unrelated</div></div></form>""")
                self.assertEqual(inspect_local_combobox_choices(page,"degree")["status"],"unlinked_listbox")
                page.set_content("""<form><input id="degree" role="combobox" onclick="document.querySelectorAll('[role=listbox]').forEach(x=>x.hidden=false)"><div role="listbox" hidden><div role="option">A</div></div><div role="listbox" hidden><div role="option">B</div></div></form>""")
                self.assertEqual(inspect_local_combobox_choices(page,"degree")["status"],"listbox_not_unique")
            finally:
                ctx.close()
                browser.close()

class GreenhouseOfficialChoiceTests(unittest.TestCase):
    def test_exact_public_identifier_required_after_selection(self):
        from applicant import select_greenhouse_public_choice,greenhouse_choice_verified,approved_draft_mapping,GREENHOUSE_DRAFT_DIAGNOSTIC_URL,GREENHOUSE_CHOICE_DIAGNOSTIC_FIELDS
        from playwright.sync_api import sync_playwright
        name="question_7532304101"
        self.assertTrue(approved_draft_mapping(GREENHOUSE_DRAFT_DIAGNOSTIC_URL,GREENHOUSE_CHOICE_DIAGNOSTIC_FIELDS))
        self.assertFalse(approved_draft_mapping(GREENHOUSE_DRAFT_DIAGNOSTIC_URL,{name:"Other"}))
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            ctx=browser.new_context(offline=True,service_workers="block")
            try:
                page=ctx.new_page()
                page.set_content("""<form><input id="question_7532304101" role="combobox" aria-controls="options"><input type="hidden" name="question_7532304101"><div id="options" role="listbox"><div role="option" onclick="document.querySelector('input[type=hidden]').value='44515238101'">Colombia</div></div></form>""")
                form=page.locator("form")
                self.assertFalse(greenhouse_choice_verified(form,name,"Colombia"))
                self.assertTrue(select_greenhouse_public_choice(page,form,name,"Colombia")[0])
                self.assertTrue(greenhouse_choice_verified(form,name,"Colombia"))
                page.locator('input[type="hidden"]').evaluate("el=>el.value='wrong'")
                self.assertFalse(greenhouse_choice_verified(form,name,"Colombia"))
            finally:
                ctx.close()
                browser.close()

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

    def test_readonly_gate_blocks_before_chromium_and_personal_data(self):
        from submit_ypai import apply_ypai_role
        key="radar:commercial:ingresos-ypai-motion-performer-co-20261124"
        with patch.dict("os.environ",{
            "YPAI_MOTION_SUBMIT_URL":"https://freelancer.ypai.ai/api/jobs/apply",
            "SUBMISSION_TOKEN":""}), patch("submit_ypai.sync_playwright") as chromium:
            result=apply_ypai_role("motion-performer-co",key,"Example Applicant",
                                    "example@example.invalid","Colombia",True,False)
            chromium.assert_not_called()
        self.assertEqual(result["status"],"blocked_owner_final_form_review_required")
        self.assertFalse(result["attempted_submit"])
        self.assertFalse(result["browser_opened"])
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertNotIn("example@example.invalid",str(result))

    def test_readonly_gate_rejects_missing_auth_and_accepts_only_exact_status(self):
        from submit_ypai import motion_readiness_before_browser, motion_applicant_digest
        from unittest.mock import patch
        with patch.dict("os.environ",{"SUBMISSION_TOKEN":"fictional-test-credential-000000"}):
            with patch("submit_ypai.build_opener") as opener:
                response=opener.return_value.open.return_value.__enter__.return_value
                response.status=200
                response.read.return_value=json.dumps({
                    "read_only":True,"external_submission":False,
                    "claim_reserved":False,
                    "case_key":"radar:commercial:ingresos-ypai-motion-performer-co-20261124",
                    "safe_to_submit":False,
                    "final_form_preflight_verified":False,
                    "identity_digest_matches_reviewed_applicant":False
                }).encode()
                with self.assertRaisesRegex(ValueError,"owner_reviewed_exact_final_form_preflight_required"):
                    motion_readiness_before_browser("Example Applicant","example@example.invalid")
                request=opener.return_value.open.call_args.args[0]
                self.assertEqual(json.loads(request.data)["identity_digest"],
                    motion_applicant_digest("Example Applicant","example@example.invalid"))
                self.assertNotIn(b"Example Applicant",request.data)
                self.assertNotIn(b"example@example.invalid",request.data)
                self.assertEqual(request.get_method(),"POST")
            with patch("submit_ypai.build_opener") as opener:
                response=opener.return_value.open.return_value.__enter__.return_value
                response.status=200
                response.read.return_value=json.dumps({
                    "read_only":True,"external_submission":False,
                    "claim_reserved":False,
                    "case_key":"radar:commercial:ingresos-ypai-motion-performer-co-20261124",
                    "safe_to_submit":True,
                    "final_form_preflight_verified":True,
                    "identity_digest_matches_reviewed_applicant":True
                }).encode()
                self.assertTrue(motion_readiness_before_browser("Example Applicant","example@example.invalid"))
            with patch("submit_ypai.build_opener") as opener:
                opener.return_value.open.side_effect=TimeoutError()
                with self.assertRaisesRegex(ValueError,"readiness_unavailable_no_browser_no_retry"):
                    motion_readiness_before_browser("Example Applicant","example@example.invalid")

    def test_reviewed_identity_digest_normalizes_spaces_and_accents(self):
        from submit_ypai import motion_applicant_digest
        import hashlib
        name="José Miguel Ejemplo"
        expected=hashlib.sha256((name.lower()+"\x00"+"example@domain.test").encode("utf-8")).hexdigest()
        self.assertEqual(motion_applicant_digest(name,"EXAMPLE@DOMAIN.TEST"),expected)
        self.assertEqual(motion_applicant_digest("  José Miguel Ejemplo  ","example@domain.test"),expected)

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

class MotionTransportGateTests(unittest.TestCase):
    """Exercise the real HTTP handler with a mocked runner; no network or POST."""
    def test_default_off_does_not_call_runner(self):
        from api_v2 import API
        from unittest.mock import Mock
        handler=Mock()
        handler.path="/jobs/submit-ypai-role"
        handler.authorized_submission.return_value=True
        handler.parse_json.return_value={
            "role_slug":"motion-performer-co",
            "case_key":"radar:commercial:ingresos-ypai-motion-performer-co-20261124"}
        with patch.dict("os.environ",{"C360_MOTION_LIVE_ROUTE_ENABLED":""}), \
             patch("api_v2.approved_case_keys",return_value={handler.parse_json.return_value["case_key"]}), \
             patch("api_v2.apply_ypai_role") as runner:
            API.do_POST(handler)
            runner.assert_not_called()
        handler.reply.assert_called_once_with(403,{"error":"durable_claim_and_exact_approval_required","submitted":False})

    def test_enabled_transport_still_requires_case_approval(self):
        from api_v2 import API
        from unittest.mock import Mock
        handler=Mock()
        handler.path="/jobs/submit-ypai-role"
        handler.authorized_submission.return_value=True
        handler.parse_json.return_value={"role_slug":"motion-performer-co","case_key":"not-approved"}
        with patch.dict("os.environ",{"C360_MOTION_LIVE_ROUTE_ENABLED":"1"}), \
             patch("api_v2.approved_case_keys",return_value=set()), \
             patch("api_v2.apply_ypai_role") as runner:
            API.do_POST(handler)
            runner.assert_not_called()
        handler.reply.assert_called_once_with(403,{"error":"case_not_explicitly_approved","submitted":False})

    def test_invalid_submission_token_stops_before_payload(self):
        from api_v2 import API
        from unittest.mock import Mock
        handler=Mock()
        handler.path="/jobs/submit-ypai-role"
        handler.authorized_submission.return_value=False
        with patch("api_v2.apply_ypai_role") as runner:
            API.do_POST(handler)
            runner.assert_not_called()
        handler.parse_json.assert_not_called()
        handler.reply.assert_called_once_with(401,{"error":"unauthorized"})


class OptionalDraftBlockerTests(unittest.TestCase):
    def test_known_optional_blocker_does_not_masquerade_as_required(self):
        with patch("workflow_engine.inspect",return_value=source(
            fields=[{"name":"specialty","required":False}],
            required_fields=[],unidentified_required_count=0,
            draft_offline=True,filled_field_names=[])):
            r=prepare_workflow(WELLONIS,{"specialty":"Example"})
        self.assertEqual(r["draft_verification"]["optional_missing_field_names"],["specialty"])
        self.assertEqual(r["draft_verification"]["unresolved_missing_field_names"],[])
        self.assertEqual(r["next_action"],"review_terms_and_authorize_specific_case")
        self.assertFalse(r["full_form_readiness"]["full_form_verified"])
        self.assertFalse(r["submitted"])

    def test_unknown_metadata_cannot_defer_missing_field(self):
        with patch("workflow_engine.inspect",return_value=source(
            fields=[],required_fields=[],unidentified_required_count=1,
            draft_offline=True,filled_field_names=[])):
            r=prepare_workflow(WELLONIS,{"specialty":"Example"})
        self.assertEqual(r["draft_verification"]["optional_missing_field_names"],[])
        self.assertEqual(r["next_action"],"resolve_remaining_required_fields")
        self.assertFalse(r["submitted"])

    def test_required_field_still_blocks_despite_optional_metadata(self):
        with patch("workflow_engine.inspect",return_value=source(
            fields=[{"name":"name","required":False}],
            required_fields=[{"name":"name"}],unidentified_required_count=0,
            draft_offline=True,filled_field_names=[])):
            r=prepare_workflow(WELLONIS,{"name":"Example"})
        self.assertEqual(r["draft_verification"]["optional_missing_field_names"],[])
        self.assertEqual(r["next_action"],"resolve_remaining_required_fields")
        self.assertFalse(r["submitted"])


if __name__=="__main__": unittest.main()
