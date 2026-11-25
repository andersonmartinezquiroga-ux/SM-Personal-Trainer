"""SJM job browser: official career boards, inspection and draft without submission."""
import re
import json
from datetime import datetime, timezone
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,TimeoutError as PlaywrightTimeoutError
from form_adapter import classify_application_form

ALLOWED={
 # Four exact registered Greenhouse listings; public inspection only.
 "job-boards.greenhouse.io": re.compile(r"^/agency/jobs/(?:4675669101|4787634101|4778246101)/?$"),
 "job-boards.eu.greenhouse.io": re.compile(r"^/agency/jobs/4784908101/?$"),
 "jobs.lever.co": re.compile(r"^/[A-Za-z0-9_-]+/[a-zA-Z0-9-]{25,}(?:/apply)?/?$"),
 "jobs.ashbyhq.com": re.compile(r"^/[A-Za-z0-9_-]+/[a-zA-Z0-9-]{25,}(?:/application)?/?$"),
 "freelancer.ypai.ai": re.compile(r"^/jobs/openings/(?:model-evaluator-co|data-annotator-co|text-annotator-co|pose-keypoint-annotator-co|motion-performer-co|conversation-video-spanish-co|conversational-speech-contributor-co)$"),
 # Public, exact-case jobs only. No generic domain-wide browsing.
 # Generic public Workana listing adapter: GET only; Supabase still gates EXACT case URLs.
 # Never accepts /login, /account, /apply, querystrings or unsafe redirects.
 "www.workana.com": re.compile(r"^/(?:es/)?job/[a-z0-9][a-z0-9-]{7,168}[a-z0-9]/?$"),
 # Exact active SJM commercial case; public GET inspection only, no sign-in or submission.
 "www.getonbrd.com": re.compile(r"^/jobs/operations-management/asistente-operativo-primera-milla-enviame-remote/?$"),
 # Exact registered Colombia remote role: public inspection only, no credentials or submission.
 # Colombian government job URL, exact public query params, GET-only.
 # Exact publicly listed SJM source URLs. GET only; no login, payment or submission.
 "gymstart.co": re.compile(r"^/$"),
 # Wellonis Founding Coach: PUBLIC enrollment preflight, NEVER register or accept terms.
 # Existing Skulearn coach case: exact public form, read-only.
 "skulearn.com": re.compile(r"^/become-a-coach/?$"),
 "wellonis.com": re.compile(r"^/signup/partner/?$"),
 "www.wellonis.com": re.compile(r"^/signup/partner/?$"),
 # Original Jobbers online-coach lead: exact public sign-up path only; no account actions.
 "www.jobbers.io": re.compile(r"^/provider-signup/?$"),
 "jobbers.io": re.compile(r"^/provider-signup/?$"),
 # Existing Supabase-registered Colombian opportunities. Exact public URLs, read-only.
 "www.careers-page.com": re.compile(r"^/mobidea/job/LR8Y485X/?$"),
 "www.instruimos.com": re.compile(r"^/TrabajeNosotros[.]awp$"),
 # Four EXISTING Supabase-vetted Magneto public listings. READ-ONLY EXACT URLs only.
 "www.magneto365.com": re.compile(r"^/co/empleos/(?:asesor-comercial-sin-experiencia-partime-1144830|asistente-de-ventas-con-o-sin-experiencia-fusagasuga-1141783|auxiliar-de-servicio-al-cliente-sin-experiencia-por-temporada-manizales-1141475|operador-de-tienda-ara-fusagasuga-cundinamarca-1140758)/?$"),
 "mantra.fit": re.compile(r"^/careers/fitness-expert-job-in-spain/?$"),
 # Exact SJM tracked public listings. No account/session access or submissions.
 "co.linkedin.com": re.compile(r"^/jobs/view/data-annotator-spanish-colombia-audio-es-co-at-lemon-r-4467880155/?$"),
 "public.ureed.com": re.compile(r"^/freelancing/?$"),
 # Batch 2026-11-12: six tracked public signup/creator-marketplace entrypoints, GET-only.
 "conectapp.com.co": re.compile(r"^/auth/register/?$"),
 "ko-fi.com": re.compile(r"^/$"),
 "mindrift.ai": re.compile(r"^/welcome/?$"),
 "www.fiverr.com": re.compile(r"^/start_selling/?$"),
 "mostaql.com": re.compile(r"^/$"),
 "www.superprof.ae": re.compile(r"^/tutor/?$"),
 "personas.serviciodeempleo.gov.co": re.compile(r"^/detalle_oferta[.]aspx$"),
 "www.unisco.com": re.compile(r"^/es/careers/ai-coach-teacher-colombia/?$"),
 "community.transperfect.com": re.compile(r"^/jobs/720525-audio-quality-assurance-reviewer-spanish-colombia/?$"),
 "myvirtualtrainer.co": re.compile(r"^/$"),
 # Two verified public Spanish-language sources. Exact paths only, inspection only.
 "www.tusclases.co": re.compile(r"^/anunciarse/profesor-particular/?$"),
 "agentify.teamtailor.com": re.compile(r"^/es/jobs/7708719-agente-de-ventas-call-centre-en-espanol-colombia-virtual/?$")
}
WORKANA_KNOWN_CASE_PATHS=frozenset((
    "/es/job/asistente-de-marketing-proactivo-para-gestion-de-redes-sociales",
    "/es/job/asistente-virtual-confiable-y-detallista-para-gestion-de-datos",
    "/es/job/asistente-virtual-confiable-y-organizado-para-soporte-administrativo-remoto-12",
    "/es/job/asistente-virtual-detallista-con-fluidez-en-espanol-para-tareas-administrativas",
    "/es/job/asistente-virtual-full-time-para-configuracion-de-apps-y-gestion-de-clientes",
    "/es/job/asistente-virtual-hispanohablante-confiable-y-detallista-para-soporte-administrativo-remoto-86",
    "/es/job/asistente-virtual-para-digitacion-entrada-de-datos-y-transcripcion-de-textos",
    "/es/job/asistente-virtual-para-entrada-de-datos-detallada-de-sitios-web-a-google-sheets",
    "/es/job/asistente-virtual-proactiva-para-atencion-al-cliente-y-ventas-en-e-commerce",
    "/es/job/asistente-virtual-y-entrada-de-datos-habla-hispana",
    "/es/job/asistente-virtual-y-soporte-al-cliente-remoto-en-espanol",
    "/es/job/asistentes-virtuales-para-soporte-administrativo-remoto-en-latam",
    "/es/job/automatizacion-de-respuestas-para-captar-la-atencion-del-publico",
    "/es/job/buscamos-talento-para-prime-by-chetezz-equipo-de-ventas-marketing-y-operaciones",
    "/es/job/community-manager-y-creador-de-contenido-para-redes-sociales-de-negocio-deportivo",
    "/es/job/community-manager-y-creador-de-contenido-para-redes-sociales-de-tienda-de-nutricion-deportiva",
    "/es/job/contratar-asistente-virtual-especialista-en-entrada-de-datos-para-trabajo-continuo",
    "/es/job/contratar-asistente-virtual-para-gestion-administrativa-atencion-al-cliente",
    "/es/job/contratar-personal-trainer-especializado-en-educacion-y-salud-fisica-para-programas-personalizados",
    "/es/job/creacion-y-gestion-de-presupuestos-y-tarifas-de-proveedores",
    "/es/job/creador-de-contenido-especializado-para-equipos-de-gimnasio",
    "/es/job/desarrollo-de-contenido-y-estrategia-para-proyecto-de-cuidado-fisico",
    "/es/job/desarrollo-de-sistema-interno-para-seguimiento-de-kpis-y-metas-busco-precio-muy-competitivo",
    "/es/job/editor-de-contenido-fitness-para-reels-y-stories-de-instagram",
    "/es/job/especialista-en-contenido-visual-y-edicion-para-redes-sociales-de-gimnasio",
    "/es/job/especialista-en-creacion-y-estrategia-de-contenido-para-entrenador-personal-y-nutricionista-online",
    "/es/job/extraccion-de-valoraciones-web-y-compilacion-en-excel",
    "/es/job/redaccion-y-correccion-de-documentos-cortos-en-espanol-5",
    "/es/job/remote-spanish-speaking-virtual-assistant-for-beginner-friendly-support",
    "/es/job/servicio-profesional-de-transcripcion-de-textos-y-audios-para-audiencia-latinoamericana",
    "/es/job/spanish-speaking-virtual-assistant-for-data-entry-and-administrative-tasks",
    "/job/asistencia-operativa-para-creacion-de-redes-sociales-y-programacion-de-contenido-de-libro",
    "/job/asistente-virtual-confiable-y-organizado-para-tareas-administrativas-remotas-10",
    "/job/asistente-virtual-para-entrada-de-datos-web-a-google-sheets-con-alta-precision",
    "/job/asistente-virtual-para-soporte-administrativo-y-atencion-al-cliente-negocio-fitness-online",
    "/job/asistente-virtual-remoto-en-espanol-para-principiantes",
    "/job/creacion-de-rutinas-de-entrenamiento-personalizadas-para-todas-las-edades-y-desarrollo-personal",
    "/job/diseno-de-rutinas-de-ejercicio-personalizadas-para-el-hogar",
    "/job/escritura-sencilla-de-documentos-de-ms-word-408",
    "/job/especialista-en-reactivacion-de-clientes-para-gimnasio-via-whatsapp-e-instagram",
    "/job/sales-setter-experto-a-en-fitness-para-gestion-de-instagram-y-conversion-de-leads",
    "/job/spanish-speaking-virtual-assistant-for-data-entry-and-administrative-support",
))

STATIC_HOSTS={"jobs.lever.co","assets.lever.co","cdn.lever.co","jobs.ashbyhq.com","cdn.ashbyhq.com",
              "fonts.googleapis.com","fonts.gstatic.com","cdnjs.cloudflare.com",
              "code.jquery.com","static.cloudflareinsights.com","freelancer.ypai.ai","ypai.ai","www.ypai.ai",
              "www.workana.com","www.getonbrd.com","community.transperfect.com","myvirtualtrainer.co",
              "www.tusclases.co","agentify.teamtailor.com","www.unisco.com","personas.serviciodeempleo.gov.co","gymstart.co","mantra.fit","co.linkedin.com","public.ureed.com","conectapp.com.co","ko-fi.com","mindrift.ai","www.fiverr.com","mostaql.com","www.superprof.ae","wellonis.com","www.wellonis.com","www.jobbers.io","jobbers.io",
              "www.careers-page.com","www.instruimos.com"}
BLOCKED_TERMS=("password","captcha","recaptcha","verification","otp","ssn","credit card","cvv")

def is_safe_readonly_asset(url,method):
    """Only GET/HEAD to fixed public job sites and vendor-owned static assets."""
    p=urlparse(url)
    if (p.scheme!="https" or p.port not in (None,443) or method not in ("GET","HEAD")
            or p.username or p.password or p.fragment):
        return False
    if p.hostname in ("job-boards.greenhouse.io","job-boards.eu.greenhouse.io"):
        return not p.query and bool(ALLOWED[p.hostname].fullmatch(p.path) or p.path.startswith("/_next/static/"))
    if p.hostname=="skulearn.com":
        # Exact public application page only; no account or API routes.
        return not p.query and bool(ALLOWED[p.hostname].fullmatch(p.path))
    if p.hostname=="www.magneto365.com":
        # Fixed GET/HEAD listing paths or inert front-end static assets only.
        # No login, profile, apply, cookies, form POST or dynamic account calls.
        return not p.query and bool(
            ALLOWED[p.hostname].fullmatch(p.path) or
            p.path.startswith("/_next/static/")
        )
    if p.hostname=="app.ashbyhq.com":
        return p.path.startswith("/api/images/")
    if p.hostname=="cdn.ashbyprd.com":
        return p.path.startswith("/frontend_non_user/") or p.path.startswith("/cdn_assets/")
    return p.hostname in STATIC_HOSTS

ASHBY_PUBLIC_QUERIES=frozenset(("ApiJobPosting","ApiOrganizationFromHostedJobsPageName"))

def is_safe_public_ashby_query(request):
    """Two named public GraphQL QUERIES only, never a mutation/application POST."""
    try:
        u=urlparse(request.url)
        if not (request.method=="POST" and u.scheme=="https"
                and u.hostname=="jobs.ashbyhq.com" and u.port in (None,443)
                and u.path=="/api/non-user-graphql" and not u.query and not u.fragment
                and not u.username and not u.password):
            return False
        raw=request.post_data or ""
        if len(raw)>18000:
            return False
        data=json.loads(raw)
        if not isinstance(data,dict) or set(data)-{"query","operationName","variables"}:
            return False
        op=data.get("operationName")
        query=data.get("query")
        if op not in ASHBY_PUBLIC_QUERIES or not isinstance(query,str):
            return False
        if not re.match(r"^\s*query\s+"+re.escape(op)+r"\b",query):
            return False
        if re.search(r"\bmutation\b|\bsubscription\b",query,re.IGNORECASE):
            return False
        variables=data.get("variables") or {}
        # Only public Ashby listing identifiers observed on the official page.
        # 'organizationHostedJobsPageName' is a PUBLIC organization slug, not a person.
        if not isinstance(variables,dict) or set(variables)-{
            "organizationHostedJobsPageName","jobPostingId","searchContext"}:
            return False
        if variables.get("organizationHostedJobsPageName")!="anyone-ai":
            return False
        job=variables.get("jobPostingId")
        if job is not None and (not isinstance(job,str)
                or not re.fullmatch(r"[a-fA-F0-9-]{36}",job)):
            return False
        context=variables.get("searchContext")
        if context is not None:
            if not isinstance(context,(dict,str)) or len(json.dumps(context))>550:
                return False
            if "@" in json.dumps(context) or re.search(
                r'"(?:email|phone|password|token|accessToken|fullName|firstName|lastName)"\s*:',
                json.dumps(context),re.I):
                return False
        return True
    except (TypeError,ValueError,AttributeError):
        return False

def is_security_challenge_title(title):
    """Classification only: NEVER bypass or solve a browser challenge."""
    value=(title or "").strip().lower()
    return value in ("just a moment...","just a moment","attention required!","verify you are human") or "cloudflare challenge" in value

def is_source_access_blocked_title(title):
    """Distinguish a site access-denial page from an actual job listing."""
    if not isinstance(title, str):
        return False
    value = " ".join(title.strip().lower().split())
    return value in (
        "the url you requested has been blocked",
        "access denied",
        "url blocked",
        "la url solicitada ha sido bloqueada",
    )

def lever_required_resume_visible(text):
    """Only an explicitly mandatory resume label counts; ignore generic privacy text."""
    if not isinstance(text, str):
        return False
    return bool(re.search(
        r'(?im)^[ \t]*(?:resume[ \t]*/[ \t]*cv|r[eé]sum[eé][ \t]*/[ \t]*cv|resume|r[eé]sum[eé]|curriculum vitae|hoja de vida|cv)[ \t]*(?:\r?\n[ \t]*)?(?:\*|✱|✳|\(required\)|\(obligatorio\))[ \t]*$',
        text[:18000]
    ))

def checked_url(url):
    if not isinstance(url,str) or len(url)>500: raise ValueError("Invalid URL")
    p=urlparse(url)
    if p.scheme!="https" or p.username or p.password or p.fragment or p.hostname not in ALLOWED:
        raise ValueError("Domain not on approved job application allowlist")
    if p.query and not (
        p.hostname=="personas.serviciodeempleo.gov.co"
        and p.path=="/detalle_oferta.aspx"
        and p.query=="proceso_id=7&sede_id=1626514975"
    ):
        raise ValueError("Query parameters are not approved for this inspection")
    if p.hostname=="personas.serviciodeempleo.gov.co" and p.query!="proceso_id=7&sede_id=1626514975":
        raise ValueError("Government job source requires exact public case query")
    if p.port not in (None,443) or not ALLOWED[p.hostname].fullmatch(p.path):
        raise ValueError("Path is not an approved job application path")
    if p.hostname=="www.workana.com" and p.path.rstrip("/") not in WORKANA_KNOWN_CASE_PATHS:
        raise ValueError("Workana job is not an expressly registered case URL")
    return url

def checked_browser_location(final_url, requested_url):
    """Validate Workana's post-load address without broadening permitted requests.

    The requested URL, network navigations and redirects still pass checked_url,
    which rejects ALL Workana query strings. Workana may modify browser history
    after a successful public GET. Only a same-origin, same-path history URL
    may be canonically reported without its query string.
    """
    checked_url(requested_url)
    try:
        return checked_url(final_url)
    except ValueError:
        expected = urlparse(requested_url)
        actual = urlparse(final_url) if isinstance(final_url, str) and len(final_url) <= 1000 else None
        if not actual or expected.hostname != "www.workana.com":
            raise
        if (actual.scheme != "https" or actual.netloc != expected.netloc
                or actual.path != expected.path or actual.params or actual.fragment
                or not actual.query or actual.username or actual.password
                or actual.port not in (None, 443)):
            raise
        # Reject signals of a navigation, login, form action or sensitive token.
        # The input URL itself and ALL outgoing navigation requests remain strict.
        from urllib.parse import parse_qsl
        forbidden = {
            "apply", "submit", "login", "checkout", "payment", "redirect",
            "redirect_uri", "return", "return_url", "next", "destination",
            "url", "token", "access_token", "id_token", "auth", "session",
            "password", "email", "phone", "resume", "cv", "code"
        }
        if any(name.lower() in forbidden for name, _ in parse_qsl(actual.query, keep_blank_values=True)):
            raise
        canonical = actual._replace(query="").geturl()
        checked_url(canonical)
        return canonical

def navigate_public_page(page, url):
    """Bounded read-only navigation; tolerate slow nonessential resources.
    Never retry a submission or interact with a challenge.
    """
    checked_url(url)
    try:
        response=page.goto(url,wait_until="commit",timeout=18000)
    except PlaywrightTimeoutError:
        # Only the approved public GET may be retried, at most once.
        if page.url not in ("about:blank",url):
            checked_browser_location(page.url,url)
        response=page.goto(url,wait_until="commit",timeout=12000)
    checked_browser_location(page.url,url)
    if response is not None and response.status>=400:
        raise ValueError("Public source HTTP status "+str(response.status))
    # Inspect DOM once it has meaningful content, without waiting for all scripts.
    page.locator("body").wait_for(state="attached",timeout=8000)
    try:
        page.locator("h1,h2,form,input").first.wait_for(state="attached",timeout=5000)
    except PlaywrightTimeoutError:
        # The existing inspection must still validate title, challenge and fields.
        pass
    checked_browser_location(page.url,url)


def reviewed_radio_choice(url, name, answer, options):
    """Resolve only a reviewed non-consent radio group, using exact labels.
    Unknown groups and ambiguous or disabled choices require human review.
    """
    if url != "https://freelancer.ypai.ai/jobs/openings/conversation-video-spanish-co" or name != "l1":
        return None
    approved={"Yes, Spanish is my first language","No, Spanish is not my first language"}
    if answer not in approved or not isinstance(options,list):
        return None
    matches=[i for i,opt in enumerate(options) if opt.get("label")==answer
             and opt.get("enabled") is True and opt.get("visible") is True]
    return matches[0] if len(matches)==1 else None


def attach_pdf_in_isolated_draft(page, field_name, filename, content):
    """Attach approved in-memory PDF to a single local draft, not a submission.
    No path/URL reading, no credentials, no network. The caller must bind the
    document to the case and verify its authorization before using real data.
    """
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,89}",field_name):
        raise ValueError("invalid_attachment_field")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}\.pdf",filename,re.I):
        raise ValueError("invalid_attachment_name")
    if not isinstance(content,bytes) or not content.startswith(b"%PDF-") or len(content)>5*1024*1024:
        raise ValueError("invalid_pdf_content")
    context=page.context
    context.set_offline(True)
    context.route("**/*",lambda route:route.abort())
    forms=[f for f in page.locator("form").all() if f.is_visible()]
    if len(forms)!=1:
        return {"verified":False,"reason":"visible_form_not_unique","external_upload":False}
    target=forms[0].locator(f'input[type="file"][name="{field_name}"]')
    if target.count()!=1 or not target.is_enabled():
        return {"verified":False,"reason":"file_field_not_unique_or_enabled","external_upload":False}
    accept=(target.get_attribute("accept") or "").strip().lower()
    if accept and not any(x.strip() in (".pdf","application/pdf","*/*") for x in accept.split(",")):
        return {"verified":False,"reason":"pdf_not_accepted","external_upload":False}
    target.set_input_files({"name":filename,"mimeType":"application/pdf","buffer":content},timeout=2500)
    readback=target.evaluate("el=>Array.from(el.files||[]).map(f=>({name:f.name,size:f.size,type:f.type}))")
    ok=readback==[{"name":filename,"size":len(content),"type":"application/pdf"}]
    return {"verified":ok,"reason":"local_file_readback" if ok else "file_readback_mismatch",
            "external_upload":False}


def advance_isolated_form_step(page, current_field, next_field, button_label="Next"):
    """Advance a reviewed local wizard step only; never submit or navigate online.
    Checkpoint is DOM evidence for the current browser session, not a receipt.
    """
    for key in (current_field,next_field):
        if not isinstance(key,str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,89}",key):
            raise ValueError("invalid_step_marker")
    if current_field==next_field or button_label not in ("Next","Continue","Siguiente","Continuar"):
        raise ValueError("invalid_step_transition")
    page.context.set_offline(True)
    page.context.route("**/*",lambda route:route.abort())
    def visible_marker(key):
        nodes=page.locator(f'input[name="{key}"],select[name="{key}"],textarea[name="{key}"]')
        return nodes.count()==1 and nodes.is_visible()
    if visible_marker(next_field) and not visible_marker(current_field):
        return {"verified":True,"action":"already_at_next_step","external_submission":False}
    if not visible_marker(current_field) or visible_marker(next_field):
        return {"verified":False,"action":"ambiguous_step","external_submission":False}
    forms=[f for f in page.locator("form").all() if f.is_visible()]
    if len(forms)!=1:
        return {"verified":False,"action":"ambiguous_form","external_submission":False}
    controls=[b for b in forms[0].get_by_role("button",name=button_label,exact=True).all()
              if b.is_visible() and b.is_enabled() and b.get_attribute("type")=="button"]
    if len(controls)!=1:
        return {"verified":False,"action":"next_control_not_unique_or_safe","external_submission":False}
    # Never continue past an unchecked required consent or a human challenge.
    if forms[0].locator('input[type="checkbox"][required]:not(:checked)').count() or page.locator('iframe[src*="captcha"],iframe[src*="turnstile"]').count():
        return {"verified":False,"action":"owner_review_required","external_submission":False}
    if not forms[0].evaluate("""f=>Array.from(f.elements).filter(e=>e.getClientRects().length&&e.willValidate).every(e=>e.checkValidity())"""):
        return {"verified":False,"action":"invalid_current_fields","external_submission":False}
    try:
        controls[0].click(timeout=2000,no_wait_after=True)
        page.locator(f'[name="{next_field}"]').wait_for(state="visible",timeout=2500)
    except PlaywrightTimeoutError:
        return {"verified":False,"action":"transition_unverified_do_not_repeat","external_submission":False}
    ok=visible_marker(next_field) and not visible_marker(current_field)
    return {"verified":ok,"action":"advanced" if ok else "transition_unverified_do_not_repeat","external_submission":False}


def select_reviewed_profession(form, answer):
    """Resolve the observed id-based profession widget, not a hidden input.
    Require an exact visible local option and evidence of the backing field.
    Caller already isolated the browser from all network requests.
    """
    target=form.locator('input#apply-profession')
    backing=form.locator('input[type="hidden"][name="current_role"]')
    if target.count()!=1 or backing.count()!=1 or not target.is_visible() or not target.is_enabled():
        return False,"field_missing_or_ambiguous"
    try:
        target.fill(answer,timeout=2500)
        # A typed suggestion is not a selected profession.
        options=form.get_by_role("option",name=answer,exact=True)
        try:
            options.first.wait_for(state="visible",timeout=1800)
        except PlaywrightTimeoutError:
            return False,"profession_requires_reviewed_local_choice"
        visible=[o for o in options.all() if o.is_visible() and o.is_enabled()]
        if len(visible)!=1:
            return False,"profession_requires_reviewed_local_choice"
        visible[0].click(timeout=2500)
        if target.input_value(timeout=2000)==answer and backing.input_value(timeout=2000).strip():
            return True,"profession_selection_verified"
        return False,"readback_mismatch"
    except PlaywrightTimeoutError:
        return False,"field_action_timeout"


def exact_draft_locator(form, name):
    """Resolve an observed field name or ID; never choose among duplicates."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,89}",name):
        raise ValueError("invalid_field_identity")
    return form.locator(f'input[name="{name}"],textarea[name="{name}"],select[name="{name}"],input[id="{name}"],textarea[id="{name}"],select[id="{name}"]')


def verify_draft_field(form, url, name, value):
    """Recheck after all actions, because later fields may reset earlier values."""
    if url=="https://freelancer.ypai.ai/jobs/openings/conversation-video-spanish-co" and name=="apply-profession":
        target=form.locator('input#apply-profession')
        backing=form.locator('input[type="hidden"][name="current_role"]')
        return target.count()==1 and backing.count()==1 and target.is_visible() and target.is_enabled() and target.input_value(timeout=1500)==value and bool(backing.input_value(timeout=1500).strip())
    if url==GREENHOUSE_DRAFT_DIAGNOSTIC_URL and name in GREENHOUSE_CHOICE_IDS:
        return greenhouse_choice_verified(form,name,value)
    sel=exact_draft_locator(form,name)
    if sel.count()>0 and all((x.get_attribute("type") or "").lower()=="radio" for x in sel.all()):
        options=sel.all()
        metadata=[{"label":x.evaluate("""el=>Array.from(el.labels||[]).map(l=>l.innerText.trim()).join(' ')"""),"visible":x.is_visible(),"enabled":x.is_enabled()} for x in options]
        idx=reviewed_radio_choice(url,name,value,metadata)
        return idx is not None and options[idx].is_checked() and sum(x.is_checked() for x in options)==1
    if sel.count()!=1 or not sel.is_visible() or not sel.is_enabled():
        return False
    typ=(sel.get_attribute("type") or "").lower()
    if public_field_metadata(sel)["custom_choice"]:
        return False
    if typ in ("checkbox","radio","file","password","hidden","submit","button","reset"):
        return False
    if sel.evaluate("(el) => el.tagName.toLowerCase()")=="select":
        selected=sel.locator("option:checked")
        return selected.count()==1 and selected.inner_text(timeout=1500)==value
    return sel.input_value(timeout=1500)==value


def ordered_draft_fields(url, fields):
    """Apply only known prerequisites first; never invent missing answers."""
    if url=="https://freelancer.ypai.ai/jobs/openings/conversation-video-spanish-co":
        first=("name","email","country","region","city","l1","english_level",
               "education_level","apply-profession","years_experience")
        return [(k,fields[k]) for k in first if k in fields]+[(k,v) for k,v in fields.items() if k not in first]
    return list(fields.items())


def public_field_metadata(node):
    """Read public labels and widget semantics, never entered values."""
    return node.evaluate("""el => {
        const clean=s=>String(s||'').replace(/\s+/g,' ').trim().slice(0,120);
        const labels=Array.from(el.labels||[]).map(l=>clean(l.innerText)).filter(Boolean);
        const referenced=(el.getAttribute('aria-labelledby')||'').split(/\s+/).filter(Boolean)
            .map(id=>document.getElementById(id)).filter(Boolean).map(l=>clean(l.innerText)).filter(Boolean);
        const name=(el.getAttribute('name')||el.id||'').slice(0,90);
        const type=(el.getAttribute('type')||el.tagName.toLowerCase()).toLowerCase();
        const role=clean(el.getAttribute('role'));
        const label=clean(referenced.join(' ')||el.getAttribute('aria-label')||labels.join(' ')||el.closest('label')?.innerText||el.getAttribute('placeholder'));
        return {name,type,label,role,
          required:el.hasAttribute('required')||el.getAttribute('aria-required')==='true',
          identity:el.getAttribute('name')?'name':el.id?'id':'unidentified',
          custom_choice:role==='combobox'||el.hasAttribute('aria-autocomplete'),
          visible:!!(el.getClientRects().length&&getComputedStyle(el).visibility!=='hidden'),
          enabled:!el.disabled&&el.getAttribute('aria-disabled')!=='true'};
    }""".replace("\\s","\\\\s"))


def inspect_local_combobox_choices(page, name):
    """Read a bounded public option list from an offline, unfilled form."""
    forms=[f for f in page.locator("form").all() if f.is_visible()]
    if len(forms)!=1:
        return {"status":"form_not_unique","labels":[]}
    field=exact_draft_locator(forms[0],name)
    if field.count()!=1 or not field.is_visible() or not field.is_enabled() or field.get_attribute("role")!="combobox":
        return {"status":"combobox_not_unique","labels":[]}
    try:
        # A fallback is valid only if there was no visible list before the
        # click and exactly one new list appears while this control is focused.
        before=page.locator('[role="listbox"]:visible').count()
        field.click(timeout=1500)
        list_id=field.get_attribute("aria-controls") or field.get_attribute("aria-owns") or ""
        if re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}",list_id):
            box=page.locator(f'[id="{list_id}"][role="listbox"]')
            box.wait_for(state="visible",timeout=1200)
        elif before==0 and field.evaluate("el=>document.activeElement===el"):
            box=page.locator('[role="listbox"]:visible')
            box.first.wait_for(state="visible",timeout=1200)
            if not field.evaluate("el=>document.activeElement===el"):
                return {"status":"unlinked_listbox","labels":[]}
        else:
            return {"status":"unlinked_listbox","labels":[]}
        if box.count()!=1:
            return {"status":"listbox_not_unique","labels":[]}
        options=box.get_by_role("option").all()
        labels=[]
        for option in options[:100]:
            if option.is_visible() and option.get_attribute("aria-disabled")!="true":
                label=option.inner_text(timeout=1000).strip()[:100]
                if label and label not in labels:
                    labels.append(label)
        field.press("Escape",timeout=1000)
        return {"status":"visible_options_observed" if labels else "no_local_options","labels":labels,"truncated":len(options)>100}
    except PlaywrightTimeoutError:
        return {"status":"local_options_unavailable","labels":[]}


GREENHOUSE_DRAFT_DIAGNOSTIC_URL="https://job-boards.greenhouse.io/agency/jobs/4675669101"
GREENHOUSE_SYNTHETIC_FIELDS={"first_name":"Example","last_name":"Applicant","email":"example@example.invalid"}

# Exact public option identifiers obtained from the official job-board API.
GREENHOUSE_CHOICE_DIAGNOSTIC_FIELDS={
    "question_7532304101":"Colombia",
    "question_8412132101":"I am not located in the United States of America currently"
}
GREENHOUSE_CHOICE_IDS={"question_7532304101":"44515238101","question_8412132101":"56217483101"}

def greenhouse_choice_verified(form,name,value):
    if GREENHOUSE_CHOICE_DIAGNOSTIC_FIELDS.get(name)!=value:
        return False
    target=exact_draft_locator(form,name)
    # The visible ID and separate hidden name can coexist. Inspect separately.
    visible=[x for x in target.all() if x.is_visible() and x.is_enabled()]
    hidden=form.locator(f'input[type="hidden"][name="{name}"]')
    return len(visible)==1 and hidden.count()==1 and hidden.input_value(timeout=1500)==GREENHOUSE_CHOICE_IDS[name]

def select_greenhouse_public_choice(page,form,name,value):
    if GREENHOUSE_CHOICE_DIAGNOSTIC_FIELDS.get(name)!=value:
        return False,"field_requires_separate_review"
    target=exact_draft_locator(form,name)
    visible=[x for x in target.all() if x.is_visible() and x.is_enabled()]
    if len(visible)!=1 or visible[0].get_attribute("role")!="combobox":
        return False,"field_missing_or_ambiguous"
    field=visible[0]
    try:
        before=page.locator('[role="listbox"]:visible').count()
        field.click(timeout=1500)
        field.fill(value,timeout=1500)
        linked=field.get_attribute("aria-controls") or field.get_attribute("aria-owns") or ""
        if re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}",linked):
            box=page.locator(f'[id="{linked}"][role="listbox"]')
        elif before==0 and field.evaluate("el=>document.activeElement===el"):
            box=page.locator('[role="listbox"]:visible')
        else:
            return False,"field_requires_separate_review"
        box.first.wait_for(state="visible",timeout=1800)
        if box.count()!=1:
            return False,"field_requires_separate_review"
        option=box.get_by_role("option",name=value,exact=True)
        option.first.wait_for(state="visible",timeout=1800)
        if option.count()!=1 or not option.is_visible() or option.get_attribute("aria-disabled")=="true":
            return False,"select_label_missing_or_ambiguous"
        option.click(timeout=1500)
        return (True,"verified") if greenhouse_choice_verified(form,name,value) else (False,"readback_mismatch")
    except PlaywrightTimeoutError:
        return False,"field_action_timeout"

def approved_draft_mapping(url,fields):
    if not fields:
        return True
    if urlparse(url).hostname in ("job-boards.greenhouse.io","job-boards.eu.greenhouse.io"):
        return url==GREENHOUSE_DRAFT_DIAGNOSTIC_URL and fields in (GREENHOUSE_SYNTHETIC_FIELDS,GREENHOUSE_CHOICE_DIAGNOSTIC_FIELDS)
    return urlparse(url).hostname in ("jobs.lever.co","jobs.ashbyhq.com","freelancer.ypai.ai")


def inspect(url, fields=None):
    """Return public form metadata, or fill a non-submitted draft. Never sends an external application."""
    url=checked_url(url)
    fields=fields or {}
    if not approved_draft_mapping(url,fields):
        raise ValueError("Drafting is disabled for newly approved public listing sites")
    if not isinstance(fields,dict) or len(fields)>20: raise ValueError("Invalid field mapping")
    if any(not isinstance(k,str) or not isinstance(v,str) or len(v)>3000 for k,v in fields.items()):
        raise ValueError("Invalid field value")
    result={"url":url,"checked_at_utc":datetime.now(timezone.utc).isoformat(),
            "mode":"draft_not_submitted" if fields else "read_only","submitted":False}
    source=urlparse(url).hostname
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        ctx=browser.new_context(ignore_https_errors=False,accept_downloads=False,service_workers="block")
        page=ctx.new_page()
        page.set_default_timeout(7000)
        blocked_resources=[]
        ashby_query_statuses=[]
        motion_public_scripts=[]
        motion_role=(source=="freelancer.ypai.ai" and
                     urlparse(url).path=="/jobs/openings/motion-performer-co")
        def remember_motion_public_script(response):
            try:
                dest=urlparse(response.url)
                if (response.request.resource_type=="script" and
                    response.request.method=="GET" and response.status==200 and
                    dest.scheme=="https" and dest.hostname=="freelancer.ypai.ai" and
                    dest.port in (None,443) and not dest.username and not dest.password and
                    len(motion_public_scripts)<16):
                    motion_public_scripts.append(response)
            except Exception:
                pass
        if motion_role:
            page.on("response",remember_motion_public_script)
        def record_public_graphql_status(response):
            dest=urlparse(response.url)
            if dest.hostname=="jobs.ashbyhq.com" and dest.path=="/api/non-user-graphql" and len(ashby_query_statuses)<12:
                ashby_query_statuses.append(response.status)
        if source=="jobs.ashbyhq.com":
            page.on("response",record_public_graphql_status)
        def route_only_known(route):
            try:
                u=urlparse(route.request.url)
                # Reject unsafe frame redirects BEFORE issuing the network request.
                if route.request.is_navigation_request():
                    if route.request.method != "GET":
                        return route.abort()
                    checked_url(route.request.url)
                    return route.continue_()
                if is_safe_readonly_asset(route.request.url,route.request.method):
                    return route.continue_()
                # Ashby renders public form fields through two strictly READ-ONLY GraphQL
                # queries sent as POST. Refuse every mutation, personal data, and other POST.
                if is_safe_public_ashby_query(route.request):
                    return route.continue_()
            except Exception: pass
            if len(blocked_resources)<20:
                metadata={"method":route.request.method,
                  "host":urlparse(route.request.url).hostname,
                  "path":urlparse(route.request.url).path[:110]}
                if (route.request.method=="POST" and
                    urlparse(route.request.url).hostname=="jobs.ashbyhq.com" and
                    urlparse(route.request.url).path=="/api/non-user-graphql"):
                    try:
                        payload=json.loads(route.request.post_data or "{}")
                        if isinstance(payload,dict):
                            q=payload.get("query") or ""
                            operation=payload.get("operationName") or ""
                            metadata["graphql_operation"]=str(operation)[:90]
                            metadata["graphql_kind"]="query" if re.match(r"^\s*query\b",q) else (
                                "mutation" if re.match(r"^\s*mutation\b",q) else "other")
                            metadata["has_query_string"]=bool(q)
                            metadata["body_length"]=len(route.request.post_data or "")
                            metadata["graphql_query_prefix"]=str(q).strip()[:85]
                            metadata["variable_keys"]=list((payload.get("variables") or {}).keys())[:12] if isinstance(payload.get("variables"),dict) else []
                    except (ValueError,TypeError):metadata["graphql_kind"]="unknown"
                blocked_resources.append(metadata)
            return route.abort()
        ctx.route("**/*",route_only_known)
        navigate_public_page(page,url)
        page.wait_for_timeout(1200)
        checked_browser_location(page.url, url)  # Allow only safe same-path Workana history metadata
        # Job boards often put the full application on a separate official URL.
        # FOLLOW PUBLIC GET ONLY: never click Submit and never transmit applicant data.
        result["followed_application_page"]=False
        apply_suffix={"jobs.ashbyhq.com":"/application","jobs.lever.co":"/apply"}.get(source)
        if apply_suffix and page.locator("input,select,textarea").count()==0:
            if not urlparse(page.url).path.rstrip("/").endswith(apply_suffix):
                application_url=url.rstrip("/")+apply_suffix
                checked_url(application_url)
                navigate_public_page(page,application_url)
                page.wait_for_timeout(1400)
                checked_browser_location(page.url, application_url)  # Keep apply redirects strictly scoped
                result["followed_application_page"]=True
        # On a CPU-limited free Render instance, public Ashby GraphQL hydration
        # may take much longer than on GitHub Actions. Wait for the actual fields,
        # not a fixed 1.4s sleep, and never mistake a blank shell for an inspection.
        if source=="jobs.ashbyhq.com":
            try:
                page.locator("input, select, textarea").first.wait_for(state="attached",timeout=26000)
                result["public_form_rendered"]=True
            except PlaywrightTimeoutError:
                result["public_form_rendered"]=False
            result["public_graphql_http_statuses"]=ashby_query_statuses[:10]
        result["final_url"]=checked_browser_location(page.url, url if not result["followed_application_page"] else application_url)
        result["title"]=(page.title() or "")[:180]
        result["challenge_detected"]=is_security_challenge_title(result["title"]) or (
            page.locator("iframe[src*='turnstile'], iframe[src*='recaptcha'], .cf-challenge-running, #challenge-running").count()>0)
        result["source_access_blocked"]=is_source_access_blocked_title(result["title"])
        result["form_count"]=page.locator("form").count()
        # Only public form destination metadata for the new exact YPAI case.
        # No form values, cookies, POST requests or credentials are collected.
        if source=="freelancer.ypai.ai" and urlparse(url).path=="/jobs/openings/motion-performer-co":
            form=page.locator("form")
            if form.count()==1:
                target=form.first.evaluate("(el) => ({url:el.action, method:el.method})")
                parsed=urlparse(target.get("url",""))
                if parsed.scheme=="https" and parsed.hostname==source and parsed.port in (None,443) and not (parsed.username or parsed.password or parsed.query or parsed.fragment):
                    result["public_form_action_path"]=parsed.path
                    result["public_form_method"]=str(target.get("method","")).lower()
            # Read public code only. Do not invoke a handler, fill a form, or
            # transmit even fictional submissions to discover the destination.
            observed=page.evaluate(r"""() => {
                const candidates = new Set();
                for (const script of document.scripts) {
                    const code=script.textContent || "";
                    for (const match of code.matchAll(/\bfetch\s*\(\s*['"]((?:https:\/\/freelancer\.ypai\.ai)?\/api\/[A-Za-z0-9_/-]+)['"]/g)) {
                        candidates.add(match[1]);
                    }
                }
                const consent=document.querySelector('form input[name="consent"]');
                return {paths:[...candidates].slice(0,15),
                    consent:consent ? (consent.closest('label')?.innerText ||
                        consent.parentElement?.innerText || '').trim().slice(0,1500) : '',
                    optional_marketing_checked:!!document.querySelector(
                        'form input[name="partner_learn_consent"]:checked')};
            }""")
            result["public_inline_api_candidates"]=observed["paths"]
            # Inspect only already-loaded public same-origin JS responses.
            # No extra fetches, handler invocation, form clicks or POSTs.
            script_candidates=set()
            inspected_scripts=0
            for response in motion_public_scripts:
                try:
                    length=response.headers.get("content-length","")
                    if length.isdigit() and int(length)>2000000:
                        continue
                    body=response.body()
                    if len(body)>2000000:
                        continue
                    inspected_scripts+=1
                    code=body.decode("utf-8",errors="replace")
                    for match in re.finditer(r"""["'](/api/[A-Za-z0-9_/-]{2,120})["']""",code):
                        path=match.group(1)
                        if re.search(r"apply|applicat|opening",path,re.I):
                            script_candidates.add(path)
                except Exception:
                    continue
            result["public_loaded_script_count"]=inspected_scripts
            result["public_script_application_path_candidates"]=sorted(script_candidates)[:20]
            result["public_application_consent_text"]=observed["consent"]
            result["public_optional_marketing_prechecked"]=observed["optional_marketing_checked"]
        result["has_apply_link"]=page.locator('a[href$="/apply"], a[href*="/application"]').count()>0
        result["fields"]=[]
        for node in page.locator("input, select, textarea").all()[:45]:
            result["fields"].append(public_field_metadata(node))
        # Only public field names/labels are collected. Never return or persist entered values.
        # This lets Control 360 stop BEFORE requesting forbidden personal details.
        result["required_fields"]=[
            {"name":x["name"],"type":x["type"],"label":x["label"][:95],
             "identity":x["identity"],"custom_choice":x["custom_choice"],
             "visible":x["visible"],"enabled":x["enabled"]}
            for x in result["fields"] if x["required"] and x["name"]
        ][:40]
        result["unidentified_required_count"]=sum(1 for x in result["fields"] if x["required"] and not x["name"])
        req_text=" ".join((x["name"]+" "+x["label"]).lower()
                          for x in result["required_fields"])
        result["required_phone"]=any(
            x["type"] not in ("checkbox","radio","hidden") and
            (x["type"]=="tel" or bool(re.search(
                r"\b(phone|telephone|tel[eé]fono|celular|mobile)\b",
                (x["name"]+" "+x["label"]).lower())))
            for x in result["required_fields"])
        result["required_cv"]=any(
            x["type"] not in ("checkbox","radio","hidden") and
            (x["name"].lower()=="_systemfield_resume" or
              bool(re.search(r"\b(resume|curriculum|cv)\b",x["name"].lower())) or
              (x["type"]=="file" and bool(re.search(
               r"\b(resume|curriculum|cv)\b",x["label"].lower()))))
            for x in result["required_fields"])
        if source=="jobs.lever.co" and not result["required_cv"]:
            # Lever sometimes renders Resume/CV as a custom upload widget,
            # not as an HTML input with the required attribute.
            # A visible mandatory label is stronger than missing input metadata.
            result["required_cv"]=lever_required_resume_visible(
                page.locator("body").inner_text(timeout=7000))
        result["required_file_upload"]=(
            any(x["type"]=="file" for x in result["required_fields"]) or
            (source=="jobs.lever.co" and result["required_cv"])
        )
        # Public choices only, never the selected value or applicant inputs.
        result["reviewed_public_choices"]={}
        if url=="https://freelancer.ypai.ai/jobs/openings/conversation-video-spanish-co":
            for key in ("education_level","english_level","years_experience"):
                select=page.locator(f'form select[name="{key}"]')
                if select.count()==1:
                    result["reviewed_public_choices"][key]=select.evaluate("""el=>Array.from(el.options).filter(o=>!o.disabled&&o.value).slice(0,40).map(o=>o.textContent.trim().slice(0,100))""")
        result["document_requirements"]=[]
        for node in page.locator('input[type="file"]').all()[:15]:
            result["document_requirements"].append({
                "field_name":(node.get_attribute("name") or node.get_attribute("id") or "")[:90],
                "required":node.get_attribute("required") is not None or node.get_attribute("aria-required")=="true",
                "accept":(node.get_attribute("accept") or "")[:160],
                "multiple":node.get_attribute("multiple") is not None,
                "attachment_state":"not_attached"
            })
        result["form_fields_total"]=len(result["fields"])
        result["form_inspection_status"]="complete" if result["fields"] else "incomplete_dynamic_or_no_form"
        # Public preflight evidence; absence of fields is NEVER evidence of an application.
        result["listing_visible"]=(not result["challenge_detected"]) and (not result["source_access_blocked"]) and bool(result["title"]) and bool(page.locator("h1,h2").count())
        result["application_form_visible"]=(not result["challenge_detected"]) and (not result["source_access_blocked"]) and bool(
            result["form_fields_total"] and (result["form_count"] or
              (source=="jobs.ashbyhq.com" and urlparse(page.url).path.endswith("/application"))))
        result["login_link_visible"]=page.locator('a[href*="/login"],a[href*="/signup"],a[href*="/auth/"]').count()>0
        result["apply_link_visible"]=page.locator('a[href*="/apply"], a[href*="/application"], a[href*="/signup"]').count()>0
        result["blocked_resource_metadata"]=blocked_resources[:12] if not result["fields"] else []
        result["consent_or_captcha_present"]=page.locator('iframe[src*="captcha"], [class*="captcha"], input[type="checkbox"]').count()>0
        result["adapter_summary"]=classify_application_form(
            url, result["fields"], challenge=result["challenge_detected"],
            source_blocked=result["source_access_blocked"],
            form_visible=result["application_form_visible"],
            required_cv_hint=result["required_cv"] if source=="jobs.lever.co" else False
        )
        if source in ("job-boards.greenhouse.io","job-boards.eu.greenhouse.io") and not fields and result["application_form_visible"]:
            ctx.set_offline(True)
            ctx.route("**/*",lambda route:route.abort())
            result["local_combobox_options"]={}
            # Only fixed public, non-consent fields, no typing or selecting values.
            for key in ("country","degree--0","discipline--0"):
                result["local_combobox_options"][key]=inspect_local_combobox_choices(page,key)
        if (url=="https://freelancer.ypai.ai/jobs/openings/conversation-video-spanish-co"
                and not fields and result["application_form_visible"]
                and not result["challenge_detected"] and not result["source_access_blocked"]):
            # Discover public profession choices without personal data or network writes.
            ctx.set_offline(True)
            ctx.route("**/*",lambda route:route.abort())
            choices={"status":"form_unavailable","labels":[]}
            try:
                form=page.locator("form")
                if form.count()==1:
                    if not form.locator('[name="name"]').is_visible():
                        buttons=page.get_by_role("button",name=re.compile(r"^apply(?: now| for this role| for this job)?$",re.I))
                        visible=[b for b in buttons.all() if b.is_visible() and b.is_enabled()
                                 and b.get_attribute("type")!="submit"]
                        if len(visible)==1:
                            visible[0].click(timeout=2500,no_wait_after=True)
                    if form.locator('[name="name"]').is_visible():
                        choices=inspect_local_combobox_choices(page,"apply-profession")
            except PlaywrightTimeoutError:
                choices={"status":"local_options_unavailable","labels":[]}
            result["reviewed_public_choices"]["apply-profession"]=choices["labels"]
            result["reviewed_public_choices"]["profession_observation_status"]=choices["status"]
            # Specialty is dependent on the exact reviewed profession. Do not guess.
            result["reviewed_public_choices"]["specialty_observation_status"]="requires_verified_profession"
        if fields:
            # Draft data stays in the local browser: no network activity after public inspection.
            if result['challenge_detected'] or result['source_access_blocked']:
                raise ValueError('Draft blocked by source or human challenge')
            ctx.set_offline(True)
            ctx.route('**/*', lambda route: route.abort())
            filled=[]
            unverified=[]
            reasons={}
            # Exact YPAI public Apply control opens a dialog locally. The
            # browser is offline and all network requests are blocked first.
            if source=="freelancer.ypai.ai" and result["application_form_visible"]:
                form=page.locator("form")
                if form.count()==1 and not form.locator('[name="name"]').is_visible():
                    controls=page.get_by_role("button",name=re.compile(r"^apply(?: now| for this role| for this job)?$",re.I))
                    visible=[x for x in controls.all() if x.is_visible() and x.is_enabled()
                             and x.get_attribute("type")!="submit"]
                    if len(visible)==1:
                        try:
                            visible[0].click(timeout=2500,no_wait_after=True)
                        except PlaywrightTimeoutError:
                            pass
            # Restrict writes to the single visible application form. Never
            # select an arbitrary same-named field outside that form.
            forms=[f for f in page.locator("form").all() if f.is_visible()]
            for name,value in ordered_draft_fields(url,fields):
                normalized=re.sub(r"[^a-z]","",name.lower())
                if (not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,89}",name)
                    or any(re.sub(r"[^a-z]","",w) in normalized for w in BLOCKED_TERMS)
                    or any(w in normalized for w in ("consent","terms","privacy","agreement","token","passcode","documentid","cardnumber"))):
                    raise ValueError("Unsafe field name")
                if len(forms)!=1:
                    reasons[name]="visible_form_not_unique"
                    continue
                if url=="https://freelancer.ypai.ai/jobs/openings/conversation-video-spanish-co" and name=="apply-profession":
                    ok,reason=select_reviewed_profession(forms[0],value)
                    if ok:
                        filled.append(name)
                    else:
                        reasons[name]=reason
                    continue
                if url==GREENHOUSE_DRAFT_DIAGNOSTIC_URL and name in GREENHOUSE_CHOICE_IDS:
                    ok,reason=select_greenhouse_public_choice(page,forms[0],name,value)
                    if ok:
                        filled.append(name)
                    else:
                        reasons[name]=reason
                    continue
                sel=exact_draft_locator(forms[0],name)
                if sel.count()>0 and all((x.get_attribute("type") or "").lower()=="radio" for x in sel.all()):
                    # Only a reviewed, non-consent question may be selected.
                    # The DOM is offline; no account creation or external write.
                    options=sel.all()
                    metadata=[{"label":x.evaluate("""el=>Array.from(el.labels||[]).map(l=>l.innerText.trim()).join(' ')"""),
                               "visible":x.is_visible(),"enabled":x.is_enabled()} for x in options]
                    idx=reviewed_radio_choice(url,name,value,metadata)
                    if idx is None:
                        reasons[name]="radio_requires_review_or_unique_label"
                        continue
                    try:
                        options[idx].check(timeout=2500)
                        if options[idx].is_checked() and sum(x.is_checked() for x in options)==1:
                            filled.append(name)
                        else:
                            reasons[name]="radio_readback_mismatch"
                    except PlaywrightTimeoutError:
                        reasons[name]="field_action_timeout"
                    continue
                if sel.count()!=1:
                    reasons[name]="field_missing_or_ambiguous"
                    continue
                if not sel.is_visible() or not sel.is_enabled():
                    # A conditional field is not a failed write and must not be
                    # forced visible. Report the real state and possible prerequisites.
                    reasons[name]="field_hidden_or_disabled_requires_prior_answer"
                    continue
                typ=(sel.get_attribute("type") or "").lower()
                # A typed string is not evidence that a custom choice was selected.
                if public_field_metadata(sel)["custom_choice"]:
                    reasons[name]="field_requires_separate_review"
                    continue
                if typ in ("checkbox","radio","file","password","hidden","submit","button","reset"):
                    reasons[name]="field_requires_separate_review"
                    continue
                try:
                    is_select=sel.evaluate("(el) => el.tagName.toLowerCase()")=="select"
                    if is_select:
                        labels=sel.evaluate("""el=>Array.from(el.options).filter(o=>!o.disabled&&o.value).map(o=>o.textContent.trim())""")
                        if labels.count(value)!=1:
                            reasons[name]="select_label_missing_or_ambiguous"
                            continue
                        sel.select_option(label=value,timeout=2500)
                        observed=sel.locator('option:checked').inner_text(timeout=2500)
                    else:
                        sel.fill(value,timeout=2500)
                        observed=sel.input_value(timeout=2500)
                    if observed==value:
                        filled.append(name)
                    else:
                        reasons[name]="readback_mismatch"
                except PlaywrightTimeoutError:
                    reasons[name]="field_action_timeout"
            # End-of-draft consistency check. Never claim a value survives a
            # dependent change unless it is still present in the final DOM.
            final_forms=[f for f in page.locator("form").all() if f.is_visible()]
            for name in filled[:]:
                try:
                    valid=len(final_forms)==1 and verify_draft_field(final_forms[0],url,name,fields[name])
                except PlaywrightTimeoutError:
                    valid=False
                if not valid:
                    filled.remove(name)
                    reasons[name]="final_readback_changed_or_unavailable"
            unverified=[name for name in fields if name not in filled]
            result['draft_offline']=True
            result['unverified_field_names']=unverified
            result['draft_field_failure_reasons']=reasons
            result["filled_field_names"]=filled
            result["no_user_values_returned"]=True
        if motion_role and not fields and result["application_form_visible"] and not result["challenge_detected"]:
            # Strictly local diagnostic. All requests are aborted and Chromium is
            # offline BEFORE any synthetic value or form interaction. The result
            # contains request method/path only, never values, cookies or bodies.
            probe={"offline":False,"clicked":False,"requests":[],"external_submission":False}
            def abort_and_record_probe(route):
                req=route.request
                try:
                    parsed=urlparse(req.url)
                    if req.method in ("POST","PUT","PATCH") and parsed.hostname=="freelancer.ypai.ai" and not parsed.username and not parsed.password:
                        if len(probe["requests"])<8:
                            probe["requests"].append({"method":req.method,"path":parsed.path[:150]})
                finally:
                    route.abort()
            try:
                ctx.set_offline(True)
                ctx.route("**/*",abort_and_record_probe)
                probe["offline"]=True
                probe["step"]="locate_form"
                form=page.locator("form")
                if form.count()!=1:
                    raise ValueError("unexpected_form")
                form=form.first
                # The public listing contains a hidden dialog. Open it using
                # the visible public apply control, never a submit control.
                probe["initial_form_visible"]=form.is_visible()
                if not form.locator('[name="name"]').is_visible():
                    probe["step"]="open_public_form"
                    candidates=page.get_by_role("button",name=re.compile(r"^apply(?: now| for this role| for this job)?$",re.I))
                    links=page.get_by_role("link",name=re.compile(r"^apply(?: now| for this role| for this job)?$",re.I))
                    visible=[x for x in candidates.all()+links.all() if x.is_visible() and x.get_attribute("type")!="submit"]
                    probe["visible_apply_controls"]=len(visible)
                    if len(visible)!=1:
                        probe["public_button_labels"]=[(x.inner_text() or "").strip()[:70] for x in page.get_by_role("button").all()[:20] if x.is_visible()]
                        raise ValueError("public_apply_control_not_unique")
                    visible[0].click(timeout=3000,no_wait_after=True)
                probe["step"]="name"
                form.locator('[name="name"]').fill("Offline Test",timeout=3000)
                probe["step"]="email"
                form.locator('[name="email"]').fill("offline-test@example.invalid",timeout=3000)
                probe["step"]="country"
                country=form.locator('select[name="country"]')
                if country.count()!=1:
                    raise ValueError("unexpected_country")
                if country.is_visible():
                    try:
                        country.select_option(label="Colombia",timeout=2000)
                    except Exception:
                        country.select_option(value="CO",timeout=2000)
                else:
                    search=form.locator('[name="apply-country-search"], #apply-country-search')
                    probe["country_search_count"]=search.count()
                    probe["country_options"]=[{"value":x.get_attribute("value"),"label":(x.inner_text() or "")[:90]} for x in country.locator("option").all() if "colombia" in (x.inner_text() or "").lower() or (x.get_attribute("value") or "").lower()=="co"]
                    if search.count()!=1 or not search.is_visible():
                        raise ValueError("country_picker_missing_or_hidden")
                    search.fill("Colombia",timeout=2500)
                    page.wait_for_timeout(500)
                    options=page.get_by_text("Colombia",exact=True)
                    choices=[x for x in options.all() if x.is_visible() and x.evaluate("el=>el.tagName.toLowerCase()")!="option"]
                    probe["country_visible_choices"]=len(choices)
                    if len(choices)!=1:
                        # The search may be a combobox; inspect its actual options rather than forcing a hidden select.
                        probe["country_picker_roles"]=[(x.inner_text() or "").strip()[:90] for x in page.get_by_role("option").all()[:15] if x.is_visible()]
                        raise ValueError("country_picker_not_unique")
                    choices[0].click(timeout=2500)
                probe["country_selection_verified"]=country.input_value() in ("CO","co","Colombia","colombia")
                if not probe["country_selection_verified"]:
                    raise ValueError("country_selection_unverified")
                probe["step"]="privacy"
                consent=form.locator('input[type="checkbox"][name="consent"]')
                optional=form.locator('input[type="checkbox"][name="partner_learn_consent"]')
                if consent.count()!=1 or (optional.count() and optional.first.is_checked()):
                    raise ValueError("unexpected_consent")
                consent.check(timeout=2500)
                probe["step"]="validate"
                invalid=form.evaluate("""el=>Array.from(el.querySelectorAll('input,select,textarea')).filter(x=>!x.checkValidity()).map(x=>x.name||x.id)""")
                probe["invalid_field_names"]=[str(x)[:80] for x in invalid[:10]]
                buttons=form.locator('button[type="submit"],input[type="submit"]')
                probe["step"]="submit_control"
                if not invalid and buttons.count()==1 and buttons.first.is_visible() and buttons.first.is_enabled():
                    probe["clicked"]=True
                    buttons.first.click(timeout=3000,no_wait_after=True)
                    page.wait_for_timeout(1500)
                    probe["step"]="offline_click_complete"
            except Exception as exc:
                probe["diagnostic_error"]=type(exc).__name__
                if isinstance(exc,ValueError):
                    probe["diagnostic_reason"]=str(exc)[:100]
            result["motion_offline_diagnostic"]=probe
        ctx.close()
        browser.close()
    return result
