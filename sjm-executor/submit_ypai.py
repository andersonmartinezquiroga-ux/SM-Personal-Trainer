"""One-shot, narrowly scoped and user-authorized YPAI job application.

NEVER uses arbitrary input URLs, never uploads media/CV/phone, never solves captchas,
and never agrees to additional contracts. Called once by the guarded database queue.
"""
import re
from datetime import datetime,timezone
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,TimeoutError as BrowserTimeout

YPAI_URL="https://freelancer.ypai.ai/jobs/openings/data-annotator-co"
READ_HOSTS={"freelancer.ypai.ai","ypai.ai","www.ypai.ai","fonts.googleapis.com",
            "fonts.gstatic.com","static.cloudflareinsights.com","cdnjs.cloudflare.com"}
MAX_NAME=120
CONFIRMATION="Thank you for applying for Data Annotator"

def clean_person(name,email,country,privacy_consent,contributor_agreement):
    if not isinstance(name,str) or not (3<=len(name.strip())<=MAX_NAME):
        raise ValueError("full_name_invalid")
    if not isinstance(email,str) or len(email)>160 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}",email):
        raise ValueError("applicant_email_invalid")
    if country!="Colombia":raise ValueError("country_not_approved")
    if privacy_consent is not True or contributor_agreement is not True:
        raise ValueError("consent_or_contributor_agreement_not_approved")
    return name.strip(),email.strip()

def apply_ypai(name,email,country,privacy_consent,contributor_agreement):
    name,email=clean_person(name,email,country,privacy_consent,contributor_agreement)
    out={"employer":"YPAI","opening":"Data Annotator","country":"Colombia",
         "personal_data_fields":["name","email","country"],"consent_to_processing":True,
         "contributor_terms_approved":True,"cv_uploaded":False,"phone_provided":False,
         "voice_or_images_uploaded":False,"attempted_submit":False,"confirmed":False,
         "status":"preparing","checked_utc":datetime.now(timezone.utc).isoformat()}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        ctx=browser.new_context(ignore_https_errors=False,accept_downloads=False,
                                service_workers="block",permissions=[])
        page=ctx.new_page()
        page.set_default_timeout(6500)
        posts=[]
        def route_guard(route):
            try:
                req=route.request
                u=urlparse(req.url)
                host=u.hostname
                if u.scheme!="https" or u.port not in (None,443):return route.abort()
                if req.method in ("GET","HEAD") and host in READ_HOSTS:
                    return route.continue_()
                # Only permit state-changing traffic to the SAME verified employer host.
                if req.method=="POST" and host=="freelancer.ypai.ai":
                    posts.append({"host":host,"path":u.path[:130]})
                    return route.continue_()
            except Exception:
                pass
            return route.abort()
        ctx.route("**/*",route_guard)
        try:
            page.goto(YPAI_URL,wait_until="domcontentloaded",timeout=25000)
            page.wait_for_timeout(1400)
            if urlparse(page.url).hostname!="freelancer.ypai.ai":
                out["status"]="blocked_unexpected_redirect"
                return out
            if not page.locator("text=Applications open").first.is_visible():
                out["status"]="blocked_role_not_open"
                return out
            # No captcha workarounds or automated challenge response.
            challenge=page.locator("iframe[src*='captcha'],iframe[src*='turnstile'],.cf-turnstile,[data-sitekey],input[name='cf-turnstile-response']")
            if challenge.count()>0:
                out["status"]="blocked_captcha_or_challenge"
                return out
            forms=page.locator("form")
            if forms.count()!=1:
                out["status"]="blocked_unexpected_form_count"
                return out
            form=forms.first
            names=[x.get_attribute("name") for x in form.locator("input,select,textarea").all()]
            for mandatory in ("name","email","country","consent"):
                if mandatory not in names:
                    out["status"]="blocked_unexpected_fields"
                    return out
            if len(set(x for x in names if x))>14:
                out["status"]="blocked_extra_fields"
                return out
            # Disallow required personal or payment fields beyond agreed minimum.
            blocked_names=("phone","cv","birth","age","passport","idnumber","photo",
                           "audio","voice","password","payment","bank","address","ssn")
            for element in form.locator("input,select,textarea").all():
                field=(element.get_attribute("name") or "").lower()
                required=(element.get_attribute("required") is not None
                          or element.get_attribute("aria-required")=="true")
                if required and any(item in field for item in blocked_names):
                    out["status"]="blocked_unapproved_required_field"
                    out["required_field"]=field[:45]
                    return out
            cboxes=form.locator('input[type="checkbox"]')
            if cboxes.count()!=1 or cboxes.first.get_attribute("name")!="consent":
                out["status"]="blocked_additional_checkbox"
                return out
            consent_text=cboxes.first.evaluate("""el => (el.closest('label')?.innerText || el.parentElement?.innerText || '').trim()""")
            if "processing my application" not in consent_text.lower():
                out["status"]="blocked_changed_consent_text"
                return out
            if page.locator('input[name="phone"]').count() and page.locator('input[name="phone"]').first.get_attribute("required") is not None:
                out["status"]="blocked_phone_required"
                return out
            form.locator('[name="name"]').fill(name)
            form.locator('[name="email"]').fill(email)
            country_input=form.locator('select[name="country"]')
            if country_input.count()!=1:
                out["status"]="blocked_country_not_select"
                return out
            try:country_input.select_option(label="Colombia")
            except Exception:
                try:country_input.select_option(value="CO")
                except Exception:
                    out["status"]="blocked_country_unavailable"
                    return out
            # Never enter phone, CV, region, or honeypot. A mandatory region stops.
            for field in ("phone","cv","region","website_url"):
                loc=form.locator(f'[name="{field}"]')
                if loc.count() and (loc.first.get_attribute("required") is not None or
                                    loc.first.get_attribute("aria-required")=="true"):
                    out["status"]="blocked_unapproved_required_field"
                    out["required_field"]=field
                    return out
            # User approved the processing consent and formation of this precise contributor account.
            cboxes.first.check()
            invalid=form.evaluate("""el=>Array.from(el.querySelectorAll('input,select,textarea')).filter(x=>!x.checkValidity()).map(x=>x.name||x.id)""")
            if invalid:
                out["status"]="blocked_form_validation"
                out["invalid_fields"]=[str(x)[:60] for x in invalid[:8]]
                return out
            if page.locator("iframe[src*='captcha'],iframe[src*='turnstile'],.cf-turnstile,[data-sitekey],input[name='cf-turnstile-response']").count()>0:
                out["status"]="blocked_captcha_or_challenge"
                return out
            # Only one submit click, and no repeat even for timeout or network uncertainty.
            buttons=form.locator('button[type="submit"],input[type="submit"]')
            if buttons.count()!=1:
                out["status"]="blocked_submit_control_changed"
                return out
            if not buttons.first.is_enabled():
                out["status"]="blocked_submit_disabled"
                return out
            out["attempted_submit"]=True
            buttons.first.click(timeout=10000,no_wait_after=True)
            try:
                page.wait_for_timeout(5000)
                visible=page.get_by_text(CONFIRMATION,exact=False).all()
                confirmed=any(node.is_visible() for node in visible[:10])
                if confirmed:
                    out["confirmed"]=True
                    out["status"]="application_received"
                    out["confirmation_text"]=CONFIRMATION
                else:
                    alerts=page.locator('[role="alert"],[aria-live="assertive"]')
                    out["status"]="submission_uncertain"
                    out["visible_alert_count"]=sum(int(x.is_visible()) for x in alerts.all()[:10])
            except BrowserTimeout:
                out["status"]="submission_uncertain_timeout"
            out["outgoing_post_count"]=len(posts)
            return out
        finally:
            ctx.close()
            browser.close()
