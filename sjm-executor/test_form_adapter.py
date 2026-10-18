"""Offline public metadata fixture tests. No web traffic or employer applications."""
import unittest
from form_adapter import classify_application_form as classify

class FormAdapterTests(unittest.TestCase):
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
