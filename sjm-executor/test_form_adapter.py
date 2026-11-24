"""Offline public metadata fixture tests. No web traffic or employer applications."""
import unittest
from form_adapter import classify_application_form as classify

class FormAdapterTests(unittest.TestCase):


    def test_mobidea_instruimos_semantic_block_not_marked_ready(self):
        listing=classify('https://www.careers-page.com/mobidea/job/LR8Y485X',[],form_visible=False)
        self.assertEqual(listing['adapter'],'mobidea_careers_listing_readonly')
        self.assertEqual(listing['preflight_state'],'needs_interactive_form_inspection')
        self.assertFalse(listing['submitted'])
        blocked=classify('https://www.instruimos.com/TrabajeNosotros.awp',
          [{'name':'email','type':'email','required':True}],
          source_blocked=True,form_visible=True)
        self.assertEqual(blocked['adapter'],'instruimos_public_jobs_readonly')
        self.assertEqual(blocked['preflight_state'],'source_access_blocked')
        self.assertFalse(blocked['automatic_submission_enabled'])
        self.assertFalse(blocked['submitted'])


    def test_magneto_registered_public_form_needs_review_never_submits(self):
        url="https://www.magneto365.com/co/empleos/asistente-de-ventas-con-o-sin-experiencia-fusagasuga-1141783"
        base=[{"name":"email","type":"email","label":"Correo electronico","required":True}]
        result=classify(url,base,form_visible=True)
        self.assertEqual(result["adapter"],"magneto_listing_readonly")
        self.assertEqual(result["preflight_state"],"needs_eligibility_and_terms_review")
        self.assertFalse(result["submitted"])
        self.assertFalse(result["automatic_submission_enabled"])
        legal=classify(url,base+[{"name":"terms","type":"checkbox","label":"Acepto terminos de privacidad","required":True}],form_visible=True)
        self.assertEqual(legal["preflight_state"],"needs_specific_authorization")
        self.assertIn("terms_or_privacy",legal["required_approval_scopes"])
        self.assertFalse(legal["automatic_submission_enabled"])

    def test_jobbers_public_legal_gate(self):
        url="https://www.jobbers.io/provider-signup/"
        result=classify(url,[{"name":"email","type":"email","required":True},
                            {"name":"terms","type":"checkbox",
                             "label":"I accept Terms and Privacy","required":True}],form_visible=True)
        self.assertEqual(result["adapter"],"jobbers_partner_signup_readonly")
        self.assertEqual(result["preflight_state"],"needs_specific_authorization")
        self.assertFalse(result["automatic_submission_enabled"])
        self.assertIn("terms_or_privacy",result["required_approval_scopes"])

    def test_wellonis_requires_owner_terms_and_never_submits(self):
        r=classify('https://wellonis.com/signup/partner',
          [{'name':'email','type':'email','required':True},
           {'name':'partnerAgreement','type':'checkbox',
            'label':'I accept the Partner Terms and Privacy Policy','required':True}],
          form_visible=True)
        self.assertEqual(r['adapter'],'wellonis_partner_signup_readonly')
        self.assertEqual(r['preflight_state'],'needs_specific_authorization')
        self.assertIn('terms_or_privacy',r['required_approval_scopes'])
        self.assertFalse(r['automatic_submission_enabled'])
        self.assertFalse(r['submitted'])

    def test_ypai_with_consent(self):
        r=classify('https://freelancer.ypai.ai/jobs/openings/text-annotator-co',
          [{'name':'email','type':'email','required':True},
           {'name':'privacyConsent','type':'checkbox','label':'I agree to privacy policy','required':True}],
          form_visible=True)
        self.assertEqual(r['adapter'],'ypai_colombia')
        self.assertEqual(r['preflight_state'],'needs_specific_authorization')
        self.assertEqual(r['required_approval_scopes'],['terms_or_privacy'])
        self.assertFalse(r['automatic_submission_enabled'])

    def test_ypai_consent_mentions_optional_cv(self):
        r=classify('https://freelancer.ypai.ai/jobs/openings/text-annotator-co',
          [{'name':'name','type':'text','required':True},
           {'name':'consent','type':'checkbox',
            'label':'I consent to YPAI processing my application, and any CV I upload',
            'required':True}],form_visible=True)
        self.assertFalse(r['required_cv'])
        self.assertFalse(r['required_phone'])
        self.assertEqual(r['required_approval_scopes'],['terms_or_privacy'])

    def test_generic_required_file_not_assume_cv(self):
        r=classify('https://jobs.lever.co/weloglobal/uuid/apply',
          [{'name':'sample_audio','label':'Audio sample','type':'file','required':True}],
          form_visible=True)
        self.assertFalse(r['required_cv'])
        self.assertTrue(r['file_upload_present'])
        self.assertFalse(r['automatic_submission_enabled'])

    def test_ashby_requires_phone_cv(self):
        r=classify('https://jobs.ashbyhq.com/anyone-ai/uuid/application',
          [{'name':'phone','type':'tel','required':True},
           {'name':'_systemfield_resume','type':'file','required':True}],form_visible=True)
        self.assertTrue(r['required_phone'])
        self.assertTrue(r['required_cv'])
        self.assertEqual(r['required_approval_scopes'],['phone','cv'])
        self.assertFalse(r['submitted'])

    def test_lever_custom_upload_requires_cv_when_explicitly_marked(self):
        r=classify('https://jobs.lever.co/weloglobal/uuid/apply',
          [{'name':'name','type':'text','required':True},
           {'name':'phone','type':'tel','required':True}],
          form_visible=True, required_cv_hint=True)
        self.assertTrue(r['required_cv'])
        self.assertTrue(r['file_upload_present'])
        self.assertEqual(r['required_approval_scopes'],['phone','cv'])
        self.assertEqual(r['preflight_state'],'needs_specific_authorization')
        self.assertFalse(r['automatic_submission_enabled'])

    def test_optional_cv_does_not_mislabel_required(self):
        r=classify('https://jobs.lever.co/weloglobal/uuid/apply',
          [{'name':'resume','type':'file','required':False}],form_visible=True)
        self.assertTrue(r['file_upload_present'])
        self.assertFalse(r['required_cv'])
        self.assertFalse(r['automatic_submission_enabled'])

    def test_workana_challenge_never_eligible(self):
        r=classify('https://www.workana.com/es/job/asistente-virtual',[],challenge=True)
        self.assertEqual(r['preflight_state'],'requires_human_challenge')

    def test_missing_dynamic_form_not_submission(self):
        r=classify('https://jobs.ashbyhq.com/anyone-ai/uuid/application',[],form_visible=False)
        self.assertEqual(r['preflight_state'],'needs_interactive_form_inspection')
        self.assertFalse(r['submitted'])

    def test_unrecognized_site(self):
        r=classify('https://other-employer.invalid/apply',[{'name':'email','required':True}],form_visible=True)
        self.assertEqual(r['preflight_state'],'unsupported_source')

    def test_unknown_required_checkbox_conservative(self):
        r=classify('https://freelancer.ypai.ai/jobs/openings/model-evaluator-co',
          [{'name':'agree','type':'checkbox','required':True}],form_visible=True)
        self.assertTrue(r['legal_consent_review_required'])

    def test_fields_never_returned_as_values(self):
        r=classify('https://freelancer.ypai.ai/jobs/openings/text-annotator-co',
          [{'name':'email','label':'somebody@example.com','type':'email','required':True}],form_visible=True)
        self.assertNotIn('somebody@example.com',str(r))
        self.assertNotIn('email',str(r))

if __name__=='__main__':
    unittest.main()
