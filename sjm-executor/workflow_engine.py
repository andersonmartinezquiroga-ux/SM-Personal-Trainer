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
    "agreement", "privacy", "ssn", "documentid",
    # Never auto-fill identity, financial, authentication or legal-signature
    # fields, even in an offline draft. They require direct owner handling.
    "passport", "nationalid", "governmentid", "identitynumber",
    "documentnumber", "dateofbirth", "birthdate", "bankaccount",
    "accountnumber", "routingnumber", "iban", "swiftcode",
    "apikey", "secretkey", "signature", "securityquestion",
    "securityanswer"
)
UNSAFE_EXACT_FIELD_NAMES = frozenset(("pin", "dob", "cvc"))

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
        if key in UNSAFE_EXACT_FIELD_NAMES or any(
            part in key for part in UNSAFE_FIELD_NAMES
        ):
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
    # The Tusclases public wizard exposes only a partial step at a time.
    # An empty required-fields list from a snapshot is not completion proof.
    partial_wizard = summary.get("adapter") == "tusclases_teacher_wizard_readonly"
    filled = public.get("filled_field_names") or []
    if not isinstance(filled, list):
        raise ValueError("invalid_draft_evidence")
    # Only explicitly requested fields read back in a network-isolated draft count.
    filled = list(dict.fromkeys(x for x in filled if isinstance(x,str) and x in fields)) if public.get("draft_offline") is True else []
    missing = [x for x in fields if x not in filled]
    public["draft_verification"] = {"requested_field_names":list(fields),
        "verified_field_names":filled,"missing_field_names":missing,
        "all_requested_fields_verified":bool(fields) and not missing,
        "offline":public.get("draft_offline") is True,"persisted_externally":False}
    # A verified subset is never equivalent to a fully completed form.
    required = public.get("required_fields")
    unknown = public.get("unidentified_required_count")
    required_names = sorted(set(x["name"] for x in required if isinstance(x,dict) and isinstance(x.get("name"),str) and x["name"])) if isinstance(required,list) else []
    pending_required = [x for x in required_names if x not in filled]
    # Only explicitly optional fields with complete public metadata may be
    # deferred. Unknown field identities are not silently treated as optional.
    metadata = public.get("fields")
    # The inspector caps its required-field summary. Compare the complete
    # visible metadata against that summary so a truncated or corrupted list
    # never becomes an apparently review-ready form.
    valid_fields = [
        x for x in metadata
        if isinstance(x, dict) and isinstance(x.get("name"), str)
        and x["name"].strip() and type(x.get("required")) is bool
    ] if isinstance(metadata, list) else []
    field_names = [x["name"] for x in valid_fields]
    required_from_fields = {x["name"] for x in valid_fields if x["required"]}
    valid_required = [
        x["name"] for x in required
        if isinstance(x, dict) and isinstance(x.get("name"), str)
        and x["name"].strip()
    ] if isinstance(required, list) else []
    metadata_complete = (
        not partial_wizard
        and isinstance(metadata, list) and bool(metadata)
        and len(valid_fields) == len(metadata)
        and len(set(field_names)) == len(field_names)
        and isinstance(required, list)
        and len(valid_required) == len(required)
        and len(set(valid_required)) == len(valid_required)
        and set(valid_required) == required_from_fields
        and type(unknown) is int and unknown == 0
    )
    known_optional = {
        x["name"] for x in metadata
        if isinstance(x,dict) and isinstance(x.get("name"),str)
        and x.get("required") is False
    } if metadata_complete else set()
    optional_missing = [x for x in missing if x in known_optional and x not in required_names]
    unresolved_missing = [x for x in missing if x not in optional_missing]
    public["draft_verification"]["optional_missing_field_names"] = optional_missing
    public["draft_verification"]["unresolved_missing_field_names"] = unresolved_missing
    public["full_form_readiness"] = {
        "required_field_names_missing":pending_required,
        "unidentified_required_count":unknown if isinstance(unknown,int) and unknown>=0 else None,
        "metadata_complete":metadata_complete,
        "full_form_verified":False
    }
    required_scopes = summary.get("required_approval_scopes") or []
    if not isinstance(required_scopes, list):
        required_scopes = []
    # Never confuse a typed value with a submitted/persisted application.
    if public.get("source_access_blocked"):
        stage = "source_access_blocked"
    elif public.get("challenge_detected"):
        stage = "human_challenge_required"
    elif not public.get("application_form_visible"):
        stage = "interactive_form_or_login_required"
    elif partial_wizard:
        stage = "interactive_form_or_login_required"
    elif public.get("consent_or_captcha_present") or required_scopes:
        stage = "owner_authorization_required"
    elif fields and (pending_required or not metadata_complete or unresolved_missing or len(filled) != len(fields)):
        stage = "draft_partial_not_submitted"
    elif fields:
        stage = "draft_filled_not_submitted"
    elif not metadata_complete:
        stage = "incomplete_form_metadata"
    elif pending_required:
        # A visible form is NOT ready for final review while required fields
        # remain empty, even if no draft was requested from this endpoint.
        stage = "required_fields_unfilled"
    else:
        stage = "form_ready_for_owner_review"

    public["workflow_schema"] = "sjm-own-executor-workflow-v1"
    public["workflow_stage"] = stage
    public["workflow_steps"] = [
        {"step": "source", "status": "checked", "proof": "exact_allowlisted_https_path"},
        {"step": "investigate", "status": "checked" if public.get("listing_visible") else "needs_review"},
        {"step": "form", "status": "inspected" if public.get("application_form_visible") else "blocked"},
        {"step": "fill", "status": ("draft_verified_offline" if fields and not missing else
            "draft_partial_not_submitted" if fields else "not_requested_or_unavailable"),
         "field_names": filled, "missing_field_names": missing},
        {"step": "authorization", "status": "owner_review_required",
         "scopes": required_scopes},
        {"step": "submit", "status": "not_executed"},
        {"step": "receipt", "status": "not_available"}
    ]
    public["next_action"] = (
        "skip_blocked_source_and_continue" if stage == "source_access_blocked"
        else "inspect_remaining_wizard_steps" if partial_wizard and stage == "interactive_form_or_login_required"
        else "owner_login_or_challenge" if stage in (
            "human_challenge_required", "interactive_form_or_login_required")
        else "resolve_remaining_required_fields" if fields and (pending_required or type(unknown) is not int or unknown != 0 or not isinstance(required, list) or unresolved_missing)
        else "review_terms_and_authorize_specific_case" if stage == "owner_authorization_required"
        else "inspect_complete_form_metadata" if not metadata_complete
        else "prepare_required_fields_for_owner_review" if pending_required
        else "review_optional_fields_before_submission" if optional_missing
        else "review_form_and_authorize_submission"
    )
    public["external_submission"] = False
    public["completion_verified"] = False
    public["submitted"] = False
    return public
