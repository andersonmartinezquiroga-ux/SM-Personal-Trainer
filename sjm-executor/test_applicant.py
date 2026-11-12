"""Security checks for application inspector; real external form submission is never attempted."""
import unittest
from applicant import checked_url,inspect,is_security_challenge_title,is_safe_readonly_asset,is_safe_public_ashby_query,lever_required_resume_visible
import json

class SecurityTests(unittest.TestCase):
    def test_lever_custom_mandatory_resume_label(self):
        self.assertTrue(lever_required_resume_visible(
            "Submit your application\nResume/CV ✱\nATTACH RESUME/CV\nFull name✱"))
        self.assertTrue(lever_required_resume_visible("Hoja de vida *"))
        self.assertTrue(lever_required_resume_visible("Resume/CV\n✱\nATTACH RESUME/CV"))
        self.assertFalse(lever_required_resume_visible(
            "Resume/CV (optional)\nWe may process your CV per our privacy policy"))
        self.assertFalse(lever_required_resume_visible(
            "By applying, your resume will be reviewed"))
        self.assertFalse(lever_required_resume_visible(None))

    def test_official(self):
        url="https://jobs.lever.co/weloglobal/54157634-2cb4-4073-a1e6-4b51f3d411fd/apply"
        self.assertEqual(checked_url(url),url)
    def test_verified_ypai_colombia_pages(self):
        for role in ("model-evaluator-co","data-annotator-co","text-annotator-co","pose-keypoint-annotator-co"):
            u="https://freelancer.ypai.ai/jobs/openings/"+role
            self.assertEqual(checked_url(u),u)

    def test_workana_existing_case_slugs_are_get_only_and_no_privilege_bypass(self):
        safe=[
            "https://www.workana.com/es/job/especialista-en-creacion-y-estrategia-de-contenido-para-entrenador-personal-y-nutricionista-online",
            "https://www.workana.com/job/especialista-en-reactivacion-de-clientes-para-gimnasio-via-whatsapp-e-instagram",
            "https://www.workana.com/es/job/asistente-virtual-y-soporte-al-cliente-remoto-en-espanol",
        ]
        for url in safe:
            with self.subTest(url=url):
                self.assertEqual(checked_url(url),url)
                self.assertTrue(is_safe_readonly_asset(url,"GET"))
                self.assertFalse(is_safe_readonly_asset(url,"POST"))
        forbidden=[
            "https://www.workana.com/login",
            "https://www.workana.com/account/settings",
            "https://www.workana.com/job/a",
            "https://www.workana.com/es/job/../../login",
            "https://www.workana.com/job/test-slug-accepted?redirect=https://evil.invalid",
            "https://www.workana.com@127.0.0.1/es/job/safe-looking-name",
            "https://www.workana.com/es/job/uppercase-NOT-ALLOWED",
            "https://www.workana.com/es/job/valid-job-name/apply",
        ]
        for url in forbidden:
            with self.subTest(url=url), self.assertRaises(ValueError):
                checked_url(url)


    def test_marketplace_six_exact_readonly_batch(self):
        """The six registered platform entrypoints may be READ but never join/apply."""
        urls=(
            "https://conectapp.com.co/auth/register",
            "https://ko-fi.com/",
            "https://mindrift.ai/welcome",
            "https://www.fiverr.com/start_selling",
            "https://mostaql.com/",
            "https://www.superprof.ae/tutor/",
        )
        for u in urls:
            with self.subTest(url=u):
                self.assertEqual(checked_url(u),u)
                self.assertTrue(is_safe_readonly_asset(u,"GET"))
                self.assertFalse(is_safe_readonly_asset(u,"POST"))
                with self.assertRaises(ValueError):
                    inspect(u,{"full_name":"NEVER_SEND"})
        blocked=(
            "https://conectapp.com.co/auth/login",
            "https://ko-fi.com/account",
            "https://ko-fi.com/?checkout=1",
            "https://mindrift.ai/welcome?signup=1",
            "https://www.fiverr.com/login",
            "https://www.fiverr.com/start_selling?auth=1",
            "https://mostaql.com/projects",
            "https://www.superprof.ae/tutor/?pay=1",
            "https://www.superprof.ae/register",
        )
        for u in blocked:
            with self.subTest(url=u),self.assertRaises(ValueError):
                checked_url(u)

    def test_public_linkedin_co_and_ureed_exact_listing_readonly(self):
        public=(
            "https://co.linkedin.com/jobs/view/data-annotator-spanish-colombia-audio-es-co-at-lemon-r-4467880155",
            "https://public.ureed.com/freelancing/",
        )
        for u in public:
            with self.subTest(url=u):
                self.assertEqual(checked_url(u),u)
                self.assertTrue(is_safe_readonly_asset(u,"GET"))
                self.assertFalse(is_safe_readonly_asset(u,"POST"))
                with self.assertRaises(ValueError):
                    inspect(u,{"phone":"NO_PRIVATE_DATA"})
        forbidden=(
            "https://co.linkedin.com/login",
            "https://co.linkedin.com/jobs/view/other",
            public[0]+"?trk=123",
            "https://www.linkedin.com/jobs/view/data-annotator-spanish-colombia-audio-es-co-at-lemon-r-4467880155",
            "https://public.ureed.com/login",
            "https://public.ureed.com/freelancing/?apply=1",
            "https://public.ureed.com/freelancing/jobs",
        )
        for u in forbidden:
            with self.subTest(url=u),self.assertRaises(ValueError):
                checked_url(u)

    def test_two_fitness_source_urls_readonly_only(self):
        sources=(
            "https://gymstart.co/",
            "https://mantra.fit/careers/fitness-expert-job-in-spain/",
        )
        for u in sources:
            with self.subTest(u=u):
                self.assertEqual(checked_url(u),u)
                self.assertTrue(is_safe_readonly_asset(u,"GET"))
                self.assertFalse(is_safe_readonly_asset(u,"POST"))
                with self.assertRaises(ValueError):
                    inspect(u,{"name":"NO_PERSONAL_DATA"})
        blocked=(
            "http://gymstart.co/",
            "https://gymstart.co/login",
            "https://gymstart.co/?register=1",
            "https://gymstart.co/admin/",
            "https://mantra.fit/careers/another-job",
            "https://mantra.fit/login",
            "https://mantra.fit/careers/fitness-expert-job-in-spain/?apply=true",
            "https://mantra.fit@127.0.0.1/careers/fitness-expert-job-in-spain/",
        )
        for u in blocked:
            with self.subTest(u=u),self.assertRaises(ValueError):
                checked_url(u)

    def test_spe_colombia_exact_offer_get_only(self):
        u="https://personas.serviciodeempleo.gov.co/detalle_oferta.aspx?proceso_id=7&sede_id=1626514975"
        self.assertEqual(checked_url(u),u)
        self.assertTrue(is_safe_readonly_asset(u,"GET"))
        self.assertFalse(is_safe_readonly_asset(u,"POST"))
        with self.assertRaises(ValueError):
            inspect(u,{"phone":"NO_PERSONAL_DATA"})
        for bad in (
            "https://personas.serviciodeempleo.gov.co/detalle_oferta.aspx",
            "https://personas.serviciodeempleo.gov.co/detalle_oferta.aspx?sede_id=1626514975&proceso_id=7",
            u+"&redirect=https://evil.example",
            "https://personas.serviciodeempleo.gov.co/login",
            "https://personas.serviciodeempleo.gov.co/detalle_oferta.aspx?proceso_id=8&sede_id=1626514975",
            "http://personas.serviciodeempleo.gov.co/detalle_oferta.aspx?proceso_id=7&sede_id=1626514975"
        ):
            with self.subTest(url=bad),self.assertRaises(ValueError):
                checked_url(bad)

    def test_unisco_colombia_exact_path_readonly(self):
        url="https://www.unisco.com/es/careers/ai-coach-teacher-colombia"
        self.assertEqual(checked_url(url),url)
        self.assertTrue(is_safe_readonly_asset(url,"GET"))
        self.assertFalse(is_safe_readonly_asset(url,"POST"))
        with self.assertRaises(ValueError):
            inspect(url,{"email":"NEVER_SEND_PERSONAL_DATA"})
        for bad in (
            "https://www.unisco.com/login",
            "https://www.unisco.com/es/careers/another-role",
            url+"?apply=1",
            url+"/apply",
            "http://www.unisco.com/es/careers/ai-coach-teacher-colombia",
            "https://www.unisco.com@127.0.0.1/es/careers/ai-coach-teacher-colombia",
        ):
            with self.subTest(url=bad),self.assertRaises(ValueError):
                checked_url(bad)

    def test_getonbrd_exact_public_listing_readonly(self):
        url="https://www.getonbrd.com/jobs/operations-management/asistente-operativo-primera-milla-enviame-remote"
        self.assertEqual(checked_url(url),url)
        self.assertTrue(is_safe_readonly_asset(url,"GET"))
        self.assertFalse(is_safe_readonly_asset(url,"POST"))
        for bad in (
          "https://www.getonbrd.com/login",
          "https://www.getonbrd.com/jobs/operations-management/untracked-position",
          url+"?apply=true",
          url+"/apply",
          "http://www.getonbrd.com/jobs/operations-management/asistente-operativo-primera-milla-enviame-remote",
        ):
            with self.subTest(url=bad),self.assertRaises(ValueError):
                checked_url(bad)
        with self.assertRaises(ValueError):
            inspect(url,{"name":"DO_NOT_SEND_PRIVATE_DATA"})

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
    def test_new_verified_spanish_sources_exact_path_only(self):
        allowed=[
            "https://www.tusclases.co/anunciarse/profesor-particular",
            "https://agentify.teamtailor.com/es/jobs/7708719-agente-de-ventas-call-centre-en-espanol-colombia-virtual",
        ]
        for url in allowed:
            with self.subTest(url=url):
                self.assertEqual(checked_url(url),url)
                self.assertTrue(is_safe_readonly_asset(url,"GET"))
                self.assertFalse(is_safe_readonly_asset(url,"POST"))
                with self.assertRaises(ValueError):
                    inspect(url,{"name":"PRIVATE_VALUE_NEVER_SEND"})
        forbidden=[
            "https://www.tusclases.co/login",
            "https://www.tusclases.co/anunciarse/profesor-particular?redirect=https://evil.example",
            "https://agentify.teamtailor.com/es/jobs/other",
            "https://agentify.teamtailor.com/es/jobs/7708719-agente-de-ventas-call-centre-en-espanol-colombia-virtual?apply=true",
        ]
        for url in forbidden:
            with self.subTest(url=url),self.assertRaises(ValueError):
                checked_url(url)

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
    def test_allow_only_two_public_ashby_readonly_graphql_operations(self):
        class R:
            def __init__(self,op,query=None,variables=None,url="https://jobs.ashbyhq.com/api/non-user-graphql"):
                self.method="POST";self.url=url
                self.post_data=json.dumps({"operationName":op,
                    "query":query or ("query "+op+"($slug:String!) { job: jobPosting(slug:$slug) { id } }"),
                    "variables":{"organizationHostedJobsPageName":"anyone-ai","jobPostingId":"f90e4b5c-1682-4ddf-bb00-c8a11738a393"} if variables is None else variables})
        for op in ("ApiJobPosting","ApiOrganizationFromHostedJobsPageName"):
            self.assertTrue(is_safe_public_ashby_query(R(op)),op)
        self.assertTrue(is_safe_public_ashby_query(R(
            "ApiOrganizationFromHostedJobsPageName",
            variables={"organizationHostedJobsPageName":"anyone-ai","searchContext":{}})))
        forbidden=[
            R("CreateApplication"),
            R("ApiJobPosting",query="mutation ApiJobPosting { createApplication }"),
            R("ApiJobPosting",query="query ApiJobPosting { job {id} } mutation MakeApplication {apply}"),
            R("ApiJobPosting",variables={"email":"private@example.com"}),
            R("ApiJobPosting",variables={"name":"Samuel"}),
            R("ApiJobPosting",url="https://evil.example.com/api/non-user-graphql"),
            R("ApiJobPosting",url="https://jobs.ashbyhq.com/api/candidates")
        ]
        for bad in forbidden:
            with self.subTest(body=bad.post_data,url=bad.url):
                self.assertFalse(is_safe_public_ashby_query(bad))
        bad_method=R("ApiJobPosting");bad_method.method="GET"
        self.assertFalse(is_safe_public_ashby_query(bad_method))

    def test_only_public_ashby_static_assets_get(self):
        self.assertTrue(is_safe_readonly_asset("https://cdn.ashbyprd.com/frontend_non_user/app/.vite/manifest.json","GET"))
        self.assertTrue(is_safe_readonly_asset("https://app.ashbyhq.com/api/images/org-theme-logo/known.png","GET"))
        self.assertFalse(is_safe_readonly_asset("https://app.ashbyhq.com/api/applications","POST"))
        self.assertFalse(is_safe_readonly_asset("https://app.ashbyhq.com/api/candidates","GET"))
        self.assertFalse(is_safe_readonly_asset("https://app.ashbyhq.com/api/images/org-theme-logo/known.png","POST"))
        self.assertFalse(is_safe_readonly_asset("http://127.0.0.1/api/images/a","GET"))
        self.assertFalse(is_safe_readonly_asset("https://cdn.ashbyprd.com/internal/admin","GET"))
    def test_detect_challenge_without_claiming_listing(self):
        self.assertTrue(is_security_challenge_title("Just a moment..."))
        self.assertTrue(is_security_challenge_title("Verify you are human"))
        self.assertFalse(is_security_challenge_title("AI Agent Evaluator"))
        self.assertFalse(is_security_challenge_title("Data Annotator, Colombia | YPAI Jobs"))
    def test_no_personal_draft_on_listing_pages(self):
        with self.assertRaises(ValueError):
            inspect("https://www.workana.com/es/job/asistente-virtual-y-soporte-al-cliente-remoto-en-espanol",{"name":"PROHIBITED_TEST"})
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
