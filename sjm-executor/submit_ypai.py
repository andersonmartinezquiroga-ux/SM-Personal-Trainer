"""Strict, role-specific YPAI application runner.

The runner NEVER accepts arbitrary URLs, never uploads CV/media, never provides phone,
never solves CAPTCHA, and only acts for an exact case_key + role mapping after the API
has independently confirmed the case is explicitly approved.
"""
import re
import os
from datetime import datetime, timezone
from urllib.parse import urlparse
import json
import uuid
from urllib.request import Request, build_opener, HTTPRedirectHandler
from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout

ROLE_CONFIG = {
    "data-annotator-co": {
        "case_key": "radar:commercial:ingresos-ypai-data-annotator-co-20261016",
        "opening": "Data Annotator",
        "already_submitted": True,
    },
    "text-annotator-co": {
        "case_key": "radar:commercial:ingresos-ypai-text-annotator-co-20261016",
        "opening": "Text and NLP Annotator",
        "already_submitted": True,
    },
    "model-evaluator-co": {
        "case_key": "radar:commercial:ingresos-ypai-model-evaluator-co-20261016",
        "opening": "Model Evaluator",
        "already_submitted": True,
    },
    "motion-performer-co": {
        "case_key": "radar:commercial:ingresos-ypai-motion-performer-co-20261124",
        "opening": "Motion and Gesture Performer",
        "already_submitted": False,
    },
    "pose-keypoint-annotator-co": {
        "case_key": "radar:commercial:ingresos-ypai-pose-keypoint-co-20261016",
        "opening": "Pose and Keypoint Annotator",
        "already_submitted": True,
    },
}
BASE = "https://freelancer.ypai.ai/jobs/openings/"
READ_HOSTS = {
    "freelancer.ypai.ai", "ypai.ai", "www.ypai.ai", "fonts.googleapis.com",
    "fonts.gstatic.com", "static.cloudflareinsights.com", "cdnjs.cloudflare.com"
}
MAX_NAME = 120

# Exact field names observed in public inspection job 409. Any new field
# requires review; optional marketing and profile enrichment are never filled.
MOTION_REQUIRED_FIELDS = frozenset(("name", "email", "country", "consent"))
MOTION_REVIEWED_FIELDS = MOTION_REQUIRED_FIELDS | frozenset((
    "openingId", "postingSelection", "postingSelectionState", "_formStartTime",
    "website_url", "apply-country-search", "region", "city", "english_level",
    "education_level", "field_of_study", "apply-profession", "current_role",
    "specialty", "years_experience", "ai_work", "cv", "partner_learn_consent",
    "phone"
))

def motion_field_schema_ok(names, required):
    return (all(isinstance(n,str) and n in MOTION_REVIEWED_FIELDS for n in names)
            and len(set(names)) == len(names)
            and MOTION_REQUIRED_FIELDS.issubset(names)
            and set(required).issubset(MOTION_REQUIRED_FIELDS))

def clean_person(name, email, country, privacy_consent, contributor_agreement):
    if not isinstance(name, str) or not (3 <= len(name.strip()) <= MAX_NAME):
        raise ValueError("full_name_invalid")
    if not isinstance(email, str) or len(email) > 160 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email):
        raise ValueError("applicant_email_invalid")
    if country != "Colombia":
        raise ValueError("country_not_approved")
    if privacy_consent is not True or contributor_agreement is not True:
        raise ValueError("consent_or_contributor_agreement_not_approved")
    return name.strip(), email.strip()

def clean_motion_applicant(name, email, country, privacy_consent, contributor_agreement):
    # This case authorizes only application processing, not future contributor terms.
    if privacy_consent is not True or contributor_agreement is not False:
        raise ValueError("motion_application_only_consent_required")
    if not isinstance(name,str) or not (3 <= len(name.strip()) <= MAX_NAME):
        raise ValueError("full_name_invalid")
    if not isinstance(email,str) or len(email)>160 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}",email):
        raise ValueError("applicant_email_invalid")
    if country!="Colombia":
        raise ValueError("country_not_approved")
    return name.strip(),email.strip()

def validate_role_request(role_slug, case_key):
    cfg = ROLE_CONFIG.get(role_slug)
    if not cfg:
        raise ValueError("role_not_allowlisted")
    if case_key != cfg["case_key"]:
        raise ValueError("case_role_mismatch")
    if cfg["already_submitted"]:
        raise ValueError("application_already_submitted")
    return cfg

def role_url(role_slug):
    if role_slug not in ROLE_CONFIG:
        raise ValueError("role_not_allowlisted")
    return BASE + role_slug

def verified_submit_endpoint(role_slug):
    # Exact server-side configuration, never a client-supplied destination.
    if role_slug != "motion-performer-co":
        raise ValueError("role_submission_disabled")
    endpoint = os.environ.get("YPAI_MOTION_SUBMIT_URL", "")
    # Observed twice during isolated click diagnostic 416. The network was
    # disabled; neither request reached YPAI. Retain a separate explicit opt-in.
    if endpoint != "https://freelancer.ypai.ai/api/jobs/apply":
        raise ValueError("verified_submit_endpoint_required")
    u = urlparse(endpoint)
    if (u.scheme != "https" or u.hostname != "freelancer.ypai.ai"
            or u.port not in (None, 443) or u.username or u.password
            or u.query or u.fragment or not u.path or u.path == "/"
            or not re.fullmatch(r"/[A-Za-z0-9_/-]+", u.path)):
        raise ValueError("verified_submit_endpoint_required")
    return endpoint

class ClaimNoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def reserve_motion_once():
    """Consume the unique database reservation before the only possible click.
    A lost response is terminal for automatic retry; the DB might have reserved it."""
    token=os.environ.get("SUBMISSION_TOKEN","")
    if len(token)<25 or len(token)>512:
        raise ValueError("submission_credential_unavailable")
    req=Request(
        "https://dfqjwlsgqetyxdrsuviy.supabase.co/functions/v1/sjm_c360_motion_claim_bridge_v1",
        data=b"{}",method="POST",
        headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    try:
        with build_opener(ClaimNoRedirect()).open(req,timeout=12) as response:
            raw=response.read(4097)
            if response.status!=200 or len(raw)>4096:
                raise ValueError("claim_outcome_uncertain")
            data=json.loads(raw)
        if not isinstance(data,dict) or data.get("reserved") is not True or data.get("form_submitted") is not False:
            raise ValueError("claim_denied")
        return str(uuid.UUID(data["claim_id"]))
    except Exception:
        # Never retry and never include credentials, response body or personal data.
        raise ValueError("claim_denied_or_uncertain_no_retry") from None

def motion_readiness_before_browser():
    """Read-only authenticated Supabase preflight, BEFORE browser or applicant data.

    This separate endpoint cannot reserve a claim and accepts only {}.
    Network ambiguity fails closed; no retry and no personal fields sent.
    It does NOT create an authenticated YPAI browser session.
    """
    token = os.environ.get("SUBMISSION_TOKEN", "")
    if not 25 <= len(token) <= 512:
        raise ValueError("submission_credential_unavailable")
    req = Request(
        "https://dfqjwlsgqetyxdrsuviy.supabase.co/functions/v1/sjm_c360_motion_readiness_bridge_v1",
        data=b"{}", method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json"})
    try:
        with build_opener(ClaimNoRedirect()).open(req, timeout=11) as response:
            raw = response.read(4097)
            if response.status != 200 or len(raw) > 4096:
                raise ValueError("readiness_response_invalid")
            result = json.loads(raw)
    except Exception:
        raise ValueError("readiness_unavailable_no_browser_no_retry") from None
    if (not isinstance(result, dict)
            or result.get("read_only") is not True
            or result.get("external_submission") is not False
            or result.get("claim_reserved") is not False
            or result.get("case_key") !=
                "radar:commercial:ingresos-ypai-motion-performer-co-20261124"):
        raise ValueError("readiness_response_invalid")
    if (result.get("safe_to_submit") is not True
            or result.get("authenticated_final_form_preflight_verified") is not True):
        raise ValueError("authenticated_final_form_preflight_required")
    return True


def visible_role_receipt(page, opening):
    heading = page.get_by_text("Application received", exact=True)
    message = page.get_by_text("Thank you for applying for " + opening + ".", exact=False)
    return (heading.count() == 1 and heading.first.is_visible()
            and message.count() == 1 and message.first.is_visible())

def apply_ypai_role(role_slug, case_key, name, email, country,
                    privacy_consent, contributor_agreement):
    cfg = validate_role_request(role_slug, case_key)
    validator = clean_motion_applicant if role_slug == "motion-performer-co" else clean_person
    name, email = validator(
        name, email, country, privacy_consent, contributor_agreement
    )
    target = role_url(role_slug)
    endpoint = verified_submit_endpoint(role_slug)
    out = {
        "employer": "YPAI",
        "opening": cfg["opening"],
        "role_slug": role_slug,
        "case_key": case_key,
        "country": "Colombia",
        "personal_data_fields": ["name", "email", "country"],
        "consent_to_processing": True,
        "contributor_terms_approved": contributor_agreement is True,
        "cv_uploaded": False,
        "phone_provided": False,
        "voice_or_images_uploaded": False,
        "attempted_submit": False,
        "confirmed": False,
        "status": "preparing",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
    }
    if role_slug == "motion-performer-co":
        # An approved application/privacy consent is NOT an authenticated session.
        # Reuse the live DB gate, but never pretend a public form is a reviewed one.
        try:
            motion_readiness_before_browser()
        except ValueError as exc:
            out["status"] = "blocked_authenticated_preflight_required"
            out["blocker"] = str(exc)
            out["automatic_retry_allowed"] = False
            out["browser_opened"] = False
            return out

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(
            ignore_https_errors=False,
            accept_downloads=False,
            service_workers="block",
            permissions=[],
        )
        page = ctx.new_page()
        page.set_default_timeout(6500)
        posts = []
        post_statuses = []
        filling_started = False
        def record_post_response(response):
            if response.request.method == "POST" and response.url == endpoint:
                post_statuses.append(response.status)
        page.on("response", record_post_response)

        def route_guard(route):
            try:
                req = route.request
                u = urlparse(req.url)
                host = u.hostname
                if u.scheme != "https" or u.port not in (None, 443):
                    return route.abort()
                if req.method in ("GET", "HEAD") and host in READ_HOSTS:
                    # No query-bearing GET after personal values are entered.
                    if filling_started and u.query:
                        return route.abort()
                    return route.continue_()
                # Permit exactly one verified form POST only AFTER the explicit click boundary.
                if req.method == "POST" and req.url == endpoint and out["attempted_submit"] and not posts:
                    posts.append({"host": host, "path": u.path[:130]})
                    return route.continue_()
            except Exception:
                pass
            return route.abort()

        ctx.route("**/*", route_guard)
        try:
            page.goto(target, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(1400)
            if page.url.rstrip("/") != target.rstrip("/"):
                out["status"] = "blocked_unexpected_redirect"
                return out
            if page.locator("text=Applications open").count() == 0:
                out["status"] = "blocked_role_not_open"
                return out
            challenge = page.locator(
                "iframe[src*='captcha'],iframe[src*='turnstile'],.cf-turnstile,"
                "[data-sitekey],input[name='cf-turnstile-response']"
            )
            if challenge.count() > 0:
                out["status"] = "blocked_captcha_or_challenge"
                return out
            forms = page.locator("form")
            if forms.count() != 1:
                out["status"] = "blocked_unexpected_form_count"
                return out
            form = forms.first
            if not form.locator('[name="name"]').is_visible():
                pattern=re.compile(r"^apply(?: now| for this role| for this job)?$",re.I)
                controls=page.get_by_role("button",name=pattern).all()+page.get_by_role("link",name=pattern).all()
                visible=[x for x in controls if x.is_visible() and x.get_attribute("type")!="submit"]
                if len(visible)!=1:
                    out["status"]="blocked_public_apply_control_not_unique"
                    return out
                visible[0].click()
            if not form.locator('[name="name"]').is_visible():
                out["status"]="blocked_form_not_visible"
                return out
            elements = form.locator("input,select,textarea").all()
            names = [x.get_attribute("name") for x in elements]
            required_names = [el.get_attribute("name") for el in elements
                              if el.get_attribute("required") is not None
                              or el.get_attribute("aria-required") == "true"]
            if not motion_field_schema_ok(names, required_names):
                out["status"] = "blocked_unreviewed_form_schema"
                return out

            blocked_names = (
                "phone", "cv", "resume", "birth", "age", "passport", "idnumber",
                "photo", "audio", "voice", "password", "payment", "bank",
                "address", "ssn",
            )
            for element in elements:
                field = (element.get_attribute("name") or "").lower()
                typ = (element.get_attribute("type") or "").lower()
                required = (
                    element.get_attribute("required") is not None
                    or element.get_attribute("aria-required") == "true"
                )
                if required and (
                    typ == "file" or any(item in field for item in blocked_names)
                ):
                    out["status"] = "blocked_unapproved_required_field"
                    out["required_field"] = field[:45] or typ
                    return out

            cboxes = form.locator('input[type="checkbox"]')
            checkbox_names = [el.get_attribute("name") for el in cboxes.all()]
            if (len(set(checkbox_names)) != len(checkbox_names)
                    or "consent" not in checkbox_names
                    or not set(checkbox_names).issubset({"consent","partner_learn_consent"})):
                out["status"] = "blocked_additional_checkbox"
                return out
            consent = form.locator('input[type="checkbox"][name="consent"]')
            marketing = form.locator('input[type="checkbox"][name="partner_learn_consent"]')
            if marketing.count() and marketing.first.is_checked():
                out["status"] = "blocked_preselected_optional_marketing"
                return out
            consent_text = consent.first.evaluate(
                """el => (el.closest('label')?.innerText || el.parentElement?.innerText || '').trim()"""
            )
            lowered = consent_text.lower()
            if "processing my application" not in lowered:
                out["status"] = "blocked_changed_consent_text"
                return out
            out["consent_text_fingerprint"] = re.sub(r"\s+", " ", consent_text)[:220]

            filling_started = True
            form.locator('[name="name"]').fill(name)
            form.locator('[name="email"]').fill(email)
            country_input = form.locator('select[name="country"]')
            if country_input.count() != 1:
                out["status"] = "blocked_country_not_select"
                return out
            # Job 416 confirmed a visible custom country picker and hidden select.
            if country_input.is_visible():
                try:
                    country_input.select_option(label="Colombia")
                except Exception:
                    out["status"] = "blocked_country_unavailable"
                    return out
            else:
                search=form.locator('[name="apply-country-search"], #apply-country-search')
                if search.count()!=1 or not search.is_visible():
                    out["status"]="blocked_country_picker_missing"
                    return out
                search.fill("Colombia")
                page.wait_for_timeout(500)
                choices=[x for x in page.get_by_text("Colombia",exact=True).all()
                         if x.is_visible() and x.evaluate("el=>el.tagName.toLowerCase()")!="option"]
                if len(choices)!=1:
                    out["status"]="blocked_country_picker_not_unique"
                    return out
                choices[0].click()
            if country_input.input_value() not in ("CO","co","Colombia","colombia"):
                out["status"]="blocked_country_selection_unverified"
                return out

            # Never populate optional sensitive fields either.
            for field in ("phone", "cv", "resume", "region", "website_url", "audio", "voice"):
                loc = form.locator(f'[name="{field}"]')
                if loc.count() and (
                    loc.first.get_attribute("required") is not None
                    or loc.first.get_attribute("aria-required") == "true"
                ):
                    out["status"] = "blocked_unapproved_required_field"
                    out["required_field"] = field
                    return out

            consent.first.check()
            if marketing.count() and marketing.first.is_checked():
                out["status"] = "blocked_optional_marketing_changed"
                return out
            invalid = form.evaluate(
                """el=>Array.from(el.querySelectorAll('input,select,textarea'))
                .filter(x=>!x.checkValidity()).map(x=>x.name||x.id)"""
            )
            if invalid:
                out["status"] = "blocked_form_validation"
                out["invalid_fields"] = [str(x)[:60] for x in invalid[:8]]
                return out
            if challenge.count() > 0:
                out["status"] = "blocked_captcha_or_challenge"
                return out

            buttons = form.locator('button[type="submit"],input[type="submit"]')
            if buttons.count() != 1:
                out["status"] = "blocked_submit_control_changed"
                return out
            if not buttons.first.is_enabled():
                out["status"] = "blocked_submit_disabled"
                return out

            # A pre-existing visible receipt is not a new submission.
            if visible_role_receipt(page, cfg["opening"]):
                out["status"] = "blocked_preexisting_visible_receipt"
                return out
            # No local flag or caller-supplied claim is enough. The database
            # checks the exact authenticated preflight and reserves this case once.
            try:
                out["submission_claim_id"]=reserve_motion_once()
            except ValueError:
                out["status"]="blocked_durable_claim_denied_or_uncertain"
                out["automatic_retry_allowed"]=False
                return out
            # Exactly one click. Never retry automatically after ambiguity.
            out["attempted_submit"] = True
            buttons.first.click(timeout=10000, no_wait_after=True)
            try:
                page.wait_for_timeout(5000)
                if (len(posts) == 1 and len(post_statuses) == 1
                        and 200 <= post_statuses[0] < 300
                        and visible_role_receipt(page, cfg["opening"])
                        and urlparse(page.url).hostname == "freelancer.ypai.ai"):
                    out["confirmed"] = True
                    out["status"] = "application_received"
                    out["confirmation_marker"] = "application received"
                    out["receipt_http_status"] = post_statuses[0]
                    out["receipt_visible_after_click"] = True
                else:
                    alerts = page.locator('[role="alert"],[aria-live="assertive"]')
                    out["status"] = "submission_uncertain"
                    out["visible_alert_count"] = sum(
                        int(x.is_visible()) for x in alerts.all()[:10]
                    )
            except BrowserTimeout:
                out["status"] = "submission_uncertain_timeout"
            out["outgoing_post_count"] = len(posts)
            return out
        finally:
            ctx.close()
            browser.close()

# Backward-compatible constants/functions retained for old tests and the locked Data Annotator route.
YPAI_URL = role_url("data-annotator-co")
def apply_ypai(name, email, country, privacy_consent, contributor_agreement):
    raise ValueError("application_already_submitted")
