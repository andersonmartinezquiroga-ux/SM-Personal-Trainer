"""SJM job browser: official career boards, inspection and draft without submission."""
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ALLOWED={
 "jobs.lever.co": re.compile(r"^/[A-Za-z0-9_-]+/[a-zA-Z0-9-]{25,}(?:/apply)?/?$"),
 "jobs.ashbyhq.com": re.compile(r"^/[A-Za-z0-9_-]+/[a-zA-Z0-9-]{25,}(?:/application)?/?$"),
 "freelancer.ypai.ai": re.compile(r"^/jobs/openings/(?:model-evaluator-co|data-annotator-co|text-annotator-co|pose-keypoint-annotator-co)$")
}
STATIC_HOSTS={"jobs.lever.co","assets.lever.co","cdn.lever.co","jobs.ashbyhq.com","cdn.ashbyhq.com",
              "fonts.googleapis.com","fonts.gstatic.com","cdnjs.cloudflare.com",
              "code.jquery.com","static.cloudflareinsights.com","freelancer.ypai.ai","ypai.ai","www.ypai.ai"}
BLOCKED_TERMS=("password","captcha","recaptcha","verification","otp","ssn","credit card","cvv")

def checked_url(url):
    if not isinstance(url,str) or len(url)>500: raise ValueError("Invalid URL")
    p=urlparse(url)
    if p.scheme!="https" or p.username or p.password or p.fragment or p.hostname not in ALLOWED:
        raise ValueError("Domain not on approved job application allowlist")
    if p.port not in (None,443) or not ALLOWED[p.hostname].fullmatch(p.path):
        raise ValueError("Path is not an approved job application path")
    return url

def inspect(url, fields=None):
    """Return public form metadata, or fill a non-submitted draft. Never sends an external application."""
    url=checked_url(url)
    fields=fields or {}
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
        def route_only_known(route):
            try:
                u=urlparse(route.request.url)
                if u.scheme=="https" and u.hostname in STATIC_HOSTS and u.port in (None,443) and route.request.method in ("GET","HEAD"):
                    return route.continue_()
            except Exception: pass
            if len(blocked_resources)<20:
                blocked_resources.append({"method":route.request.method,
                  "host":urlparse(route.request.url).hostname,
                  "path":urlparse(route.request.url).path[:110]})
            return route.abort()
        ctx.route("**/*",route_only_known)
        page.goto(url,wait_until="domcontentloaded",timeout=25000)
        page.wait_for_timeout(1200)
        if urlparse(page.url).hostname!=source: raise ValueError("Unexpected cross-site redirect")
        # On Ashby the public vacancy description contains no form inputs; the
        # official application page is a separate, same-origin /application URL.
        # Visit this READ-ONLY page before reporting a zero-field failure.
        result["followed_application_page"]=False
        if source=="jobs.ashbyhq.com" and page.locator("input,select,textarea").count()==0:
            if not urlparse(page.url).path.rstrip("/").endswith("/application"):
                application_url=url.rstrip("/")+"/application"
                checked_url(application_url)
                page.goto(application_url,wait_until="domcontentloaded",timeout=25000)
                page.wait_for_timeout(1400)
                if urlparse(page.url).hostname!=source:
                    raise ValueError("Unexpected cross-site redirect from application")
                result["followed_application_page"]=True
        result["final_url"]=page.url
        result["title"]=(page.title() or "")[:180]
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
        result["form_fields_total"]=len(result["fields"])
        result["form_inspection_status"]="complete" if result["fields"] else "incomplete_dynamic_or_no_form"
        result["blocked_resource_metadata"]=blocked_resources[:12] if not result["fields"] else []
        result["consent_or_captcha_present"]=page.locator('iframe[src*="captcha"], [class*="captcha"], input[type="checkbox"]').count()>0
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
