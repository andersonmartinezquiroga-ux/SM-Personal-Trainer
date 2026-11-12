"""SJM job browser: official career boards, inspection and draft without submission."""
import re
import json
from datetime import datetime, timezone
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,TimeoutError as PlaywrightTimeoutError
from form_adapter import classify_application_form

ALLOWED={
 "jobs.lever.co": re.compile(r"^/[A-Za-z0-9_-]+/[a-zA-Z0-9-]{25,}(?:/apply)?/?$"),
 "jobs.ashbyhq.com": re.compile(r"^/[A-Za-z0-9_-]+/[a-zA-Z0-9-]{25,}(?:/application)?/?$"),
 "freelancer.ypai.ai": re.compile(r"^/jobs/openings/(?:model-evaluator-co|data-annotator-co|text-annotator-co|pose-keypoint-annotator-co)$"),
 # Public, exact-case jobs only. No generic domain-wide browsing.
 # Generic public Workana listing adapter: GET only; Supabase still gates EXACT case URLs.
 # Never accepts /login, /account, /apply, querystrings or unsafe redirects.
 "www.workana.com": re.compile(r"^/(?:es/)?job/[a-z0-9][a-z0-9-]{7,168}[a-z0-9]/?$"),
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
              "www.workana.com","community.transperfect.com","myvirtualtrainer.co",
              "www.tusclases.co","agentify.teamtailor.com"}
BLOCKED_TERMS=("password","captcha","recaptcha","verification","otp","ssn","credit card","cvv")

def is_safe_readonly_asset(url,method):
    """Only GET/HEAD to fixed public job sites and vendor-owned static assets."""
    p=urlparse(url)
    if (p.scheme!="https" or p.port not in (None,443) or method not in ("GET","HEAD")
            or p.username or p.password or p.fragment):
        return False
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
    if p.query:
        raise ValueError("Query parameters are not approved for this inspection")
    if p.port not in (None,443) or not ALLOWED[p.hostname].fullmatch(p.path):
        raise ValueError("Path is not an approved job application path")
    if p.hostname=="www.workana.com" and p.path.rstrip("/") not in WORKANA_KNOWN_CASE_PATHS:
        raise ValueError("Workana job is not an expressly registered case URL")
    return url

def inspect(url, fields=None):
    """Return public form metadata, or fill a non-submitted draft. Never sends an external application."""
    url=checked_url(url)
    fields=fields or {}
    if fields and urlparse(url).hostname not in ("jobs.lever.co","jobs.ashbyhq.com","freelancer.ypai.ai"):
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
        page.goto(url,wait_until="domcontentloaded",timeout=25000)
        page.wait_for_timeout(1200)
        checked_url(page.url)  # Enforce exact allowlisted final path, not only host
        # Job boards often put the full application on a separate official URL.
        # FOLLOW PUBLIC GET ONLY: never click Submit and never transmit applicant data.
        result["followed_application_page"]=False
        apply_suffix={"jobs.ashbyhq.com":"/application","jobs.lever.co":"/apply"}.get(source)
        if apply_suffix and page.locator("input,select,textarea").count()==0:
            if not urlparse(page.url).path.rstrip("/").endswith(apply_suffix):
                application_url=url.rstrip("/")+apply_suffix
                checked_url(application_url)
                page.goto(application_url,wait_until="domcontentloaded",timeout=25000)
                page.wait_for_timeout(1400)
                checked_url(page.url)  # Revalidate application redirect path
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
        result["final_url"]=page.url
        result["title"]=(page.title() or "")[:180]
        result["challenge_detected"]=is_security_challenge_title(result["title"]) or (
            page.locator("iframe[src*='turnstile'], iframe[src*='recaptcha'], .cf-challenge-running, #challenge-running").count()>0)
        result["form_count"]=page.locator("form").count()
        result["has_apply_link"]=page.locator('a[href$="/apply"], a[href*="/application"]').count()>0
        result["fields"]=[]
        for node in page.locator("input, select, textarea").all()[:45]:
            typ=(node.get_attribute("type") or node.evaluate("(el) => el.tagName.toLowerCase()") or "").lower()
            name=(node.get_attribute("name") or node.get_attribute("id") or "")[:90]
            required=node.get_attribute("required") is not None or node.get_attribute("aria-required")=="true"
            label=node.evaluate("""el => {
                const lab=el.closest("label");
                return (lab?.innerText || el.getAttribute("aria-label") || el.getAttribute("placeholder") || "").slice(0,120)
            }""")
            result["fields"].append({"name":name,"type":typ,"label":label[:120],"required":bool(required)})
        # Only public field names/labels are collected. Never return or persist entered values.
        # This lets Control 360 stop BEFORE requesting forbidden personal details.
        result["required_fields"]=[
            {"name":x["name"],"type":x["type"],"label":x["label"][:95]}
            for x in result["fields"] if x["required"]
        ][:20]
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
        result["form_fields_total"]=len(result["fields"])
        result["form_inspection_status"]="complete" if result["fields"] else "incomplete_dynamic_or_no_form"
        # Public preflight evidence; absence of fields is NEVER evidence of an application.
        result["listing_visible"]=(not result["challenge_detected"]) and bool(result["title"]) and bool(page.locator("h1,h2").count())
        result["application_form_visible"]=(not result["challenge_detected"]) and bool(
            result["form_fields_total"] and (result["form_count"] or
              (source=="jobs.ashbyhq.com" and urlparse(page.url).path.endswith("/application"))))
        result["login_link_visible"]=page.locator('a[href*="/login"],a[href*="/signup"],a[href*="/auth/"]').count()>0
        result["apply_link_visible"]=page.locator('a[href*="/apply"], a[href*="/application"], a[href*="/signup"]').count()>0
        result["blocked_resource_metadata"]=blocked_resources[:12] if not result["fields"] else []
        result["consent_or_captcha_present"]=page.locator('iframe[src*="captcha"], [class*="captcha"], input[type="checkbox"]').count()>0
        result["adapter_summary"]=classify_application_form(
            url, result["fields"], challenge=result["challenge_detected"],
            form_visible=result["application_form_visible"],
            required_cv_hint=result["required_cv"] if source=="jobs.lever.co" else False
        )
        if fields:
            filled=[]
            for name,value in fields.items():
                if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,89}",name) or any(w in name.lower() for w in BLOCKED_TERMS):
                    raise ValueError("Unsafe field name")
                sel=page.locator(f'[name="{name}"]')
                if sel.count()!=1 or not sel.is_visible(): continue
                typ=(sel.get_attribute("type") or "").lower()
                if typ in ("checkbox","radio","file","password","hidden","submit","button"): continue
                if sel.evaluate("(el) => el.tagName.toLowerCase()")=="select":
                    sel.select_option(label=value)
                else: sel.fill(value)
                filled.append(name)
            result["filled_field_names"]=filled
            result["no_user_values_returned"]=True
        ctx.close()
        browser.close()
    return result
