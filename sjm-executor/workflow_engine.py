"""SJM CONTROL 360: a bounded, truthful browser workflow prepare stage.

This runs on the user's OWN Playwright/Render service. It performs inspection,
and optional non-submitted DOM filling on separately allowlisted portals. It
never clicks Submit, accepts conditions, supplies passwords, solves CAPTCHA,
or claims receipt from the employer. The next action must be explicit.
"""
import re
from applicant import inspect, checked_url

SAFE_FIELD_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,89}$")
UNSAFE_FIELD_NAMES = (
    "password", "passcode", "otp", "token", "captcha",
    "creditcard", "cardnumber", "cvv", "terms", "consent",
    "agreement", "privacy", "ssn", "documentid"
)

def _safe_fields(value):
    if value is None:
        return {}
    if not isinstance(value, dict) or len(value) > 12:
        raise ValueError("invalid_workflow_fields")
    clean = {}
    for k, v in value.items():
        if not isinstance(k, str) or not SAFE_FIELD_NAME.fullmatch(k):
            raise ValueError("unsafe_workflow_field_name")
        key = re.sub(r"[^a-z]", "", k.lower())
        if any(part in key for part in UNSAFE_FIELD_NAMES):
            raise ValueError("owner_consent_or_credentials_required")
        if not isinstance(v, str) or not 1 <= len(v) <= 300:
            raise ValueError("invalid_workflow_field_value")
        clean[k] = v
    return clean

def prepare_workflow(url, requested_fields=None):
    """Return public evidence + staged instructions without false submission."""
    checked_url(url)  # strict allowlisted HTTPS origin/path before any browser call
    fields = _safe_fields(requested_fields)
    public = inspect(url, fields=fields)
    if public.get("submitted") is not False:
        raise ValueError("unexpected_external_submission_flag")
    summary = public.get("adapter_summary") or {}
    if not isinstance(summary, dict):
        summary = {}
    filled = public.get("filled_field_names") or []
    if not isinstance(filled, list):
        raise ValueError("invalid_draft_evidence")
    filled = [x for x in filled if x in fields]
    required_scopes = summary.get("required_approval_scopes") or []
    if not isinstance(required_scopes, list):
        required_scopes = []
    # Never confuse a typed value with a submitted/persisted application.
    if public.get("challenge_detected"):
        stage = "human_challenge_required"
    elif not public.get("application_form_visible"):
        stage = "interactive_form_or_login_required"
    elif public.get("consent_or_captcha_present") or required_scopes:
        stage = "owner_authorization_required"
    elif fields and len(filled) != len(fields):
        stage = "draft_partial_not_submitted"
    elif fields:
        stage = "draft_filled_not_submitted"
    else:
        stage = "form_ready_for_owner_review"

    public["workflow_schema"] = "sjm-own-executor-workflow-v1"
    public["workflow_stage"] = stage
    public["workflow_steps"] = [
        {"step": "source", "status": "checked", "proof": "exact_allowlisted_https_path"},
        {"step": "investigate", "status": "checked" if public.get("listing_visible") else "needs_review"},
        {"step": "form", "status": "inspected" if public.get("application_form_visible") else "blocked"},
        {"step": "fill", "status": "draft_only" if filled else "not_requested_or_unavailable",
         "field_names": filled},
        {"step": "authorization", "status": "owner_review_required",
         "scopes": required_scopes},
        {"step": "submit", "status": "not_executed"},
        {"step": "receipt", "status": "not_available"}
    ]
    public["next_action"] = (
        "owner_login_or_challenge" if stage in (
            "human_challenge_required", "interactive_form_or_login_required")
        else "review_terms_and_authorize_specific_case" if stage == "owner_authorization_required"
        else "review_form_and_authorize_submission"
    )
    public["external_submission"] = False
    public["completion_verified"] = False
    public["submitted"] = False
    return public
