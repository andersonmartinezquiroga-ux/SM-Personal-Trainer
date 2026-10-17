"""Security checks for application inspector; real external form submission is never attempted."""
import unittest
from applicant import checked_url

class SecurityTests(unittest.TestCase):
    def test_official(self):
        url="https://jobs.lever.co/weloglobal/54157634-2cb4-4073-a1e6-4b51f3d411fd/apply"
        self.assertEqual(checked_url(url),url)
    def test_verified_ypai_colombia_pages(self):
        for role in ("model-evaluator-co","data-annotator-co","text-annotator-co","pose-keypoint-annotator-co"):
            u="https://freelancer.ypai.ai/jobs/openings/"+role
            self.assertEqual(checked_url(u),u)
    def test_ypai_arbitrary_path_blocked(self):
        with self.assertRaises(ValueError):
            checked_url("https://freelancer.ypai.ai/account/delete")
    def test_verified_public_sources(self):
        official=[
            "https://www.workana.com/es/job/asistente-virtual-y-soporte-al-cliente-remoto-en-espanol",
            "https://www.workana.com/es/job/asistente-virtual-full-time-para-configuracion-de-apps-y-gestion-de-clientes",
            "https://community.transperfect.com/jobs/720525-audio-quality-assurance-reviewer-spanish-colombia",
            "https://myvirtualtrainer.co/",
            "https://jobs.lever.co/weloglobal/9bf1acc5-82ec-446b-9cb0-429f08b9d8f1/apply"
        ]
        for url in official:
            with self.subTest(url=url):
                self.assertEqual(checked_url(url),url)
    def test_no_cross_scope_sites_or_profile_pages(self):
        forbidden=[
            "https://www.workana.com/login",
            "https://www.workana.com/es/job/anything-else",
            "https://community.transperfect.com/connect/login",
            "https://community.transperfect.com/jobs/random",
            "https://myvirtualtrainer.co/wp-admin/",
            "https://myvirtualtrainer.co/wp-json/wp/v2/users",
            "https://www.workana.com@127.0.0.1/",
        ]
        for url in forbidden:
            with self.subTest(url=url),self.assertRaises(ValueError):
                checked_url(url)
    def test_disallowed(self):
        for url in ("http://127.0.0.1:8765/","https://localhost/","http://169.254.169.254/",
                    "https://example.com/","https://jobs.lever.co/internal"):
            with self.subTest(url=url), self.assertRaises(ValueError): checked_url(url)
    def test_embedded_credentials(self):
        with self.assertRaises(ValueError):
            checked_url("https://a@jobs.lever.co/weloglobal/54157634-2cb4-4073-a1e6-4b51f3d411fd/apply")
    def test_no_arbitrary_queries(self):
        with self.assertRaises(ValueError):
            checked_url("https://jobs.ashbyhq.com/other/path")
if __name__=="__main__":unittest.main()
