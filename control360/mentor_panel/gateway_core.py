"""SJM Control 360: provider-neutral Mentor gateway core.

This module NEVER authenticates a user by itself. A future HTTPS gateway MUST
first verify the session/JWT cryptographically with an identity provider,
pass its verified subject here, and keep privileged SQL credentials server-side.

Pure standard-library logic, so it can be tested on GitHub Actions without
secrets, Floot, Render or Supabase network access.
"""
from __future__ import annotations

import hmac
import re
from typing import Any, Callable, Mapping

_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{4,100}$")
_ROUTES = frozenset({
    "approved_status",
    "approved_projects",
    "approved_official_sources",
    "approved_composite",
    "unrecognized",
})
_STATES = frozenset({
    "queued", "running", "completed", "failed", "blocked", "cancelled",
    "not_found", "invalid_request_key",
})
_RECEIPT_KEYS = frozenset({
    "found", "command_id", "state", "intent", "authorization_level",
    "requested_at", "finished_at", "is_final", "evidence_type",
    "evidence_present", "evidence_digest", "details_exposed",
})


class AccessDenied(Exception):
    """The app has no verified, authorized owner session."""


class InvalidInput(Exception):
    """The client supplied malformed text or request key."""


def require_verified_owner(verified_subject: str | None, owner_subject: str | None) -> None:
    """Both values must come from trusted server configuration/verifier.

    In particular, a client-supplied user ID is NOT a verified_subject.
    """
    if not isinstance(verified_subject, str) or not isinstance(owner_subject, str):
        raise AccessDenied("verified_owner_session_required")
    if len(verified_subject) < 6 or len(owner_subject) < 6:
        raise AccessDenied("verified_owner_session_required")
    if not hmac.compare_digest(verified_subject, owner_subject):
        raise AccessDenied("verified_owner_session_required")


def require_key(request_key: str) -> None:
    if not isinstance(request_key, str) or not _KEY_RE.fullmatch(request_key):
        raise InvalidInput("invalid_request_key")


def submit_owner_mentor_text(
    *,
    verified_subject: str | None,
    owner_subject: str | None,
    phrase: str,
    request_key: str,
    submit_to_privileged_sql: Callable[[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    """Server-only adapter around sjm_ops.receive_mentor_text(text, key).

    Returns a minimal status: no raw instructions, private payloads or secrets.
    """
    require_verified_owner(verified_subject, owner_subject)
    require_key(request_key)
    if not isinstance(phrase, str) or not 3 <= len(phrase) <= 1000:
        raise InvalidInput("invalid_length")

    response = submit_to_privileged_sql(phrase, request_key)
    if not isinstance(response, Mapping):
        return {"state": "blocked", "reason": "malformed_backend_response"}
    route = response.get("route")
    state = response.get("status")
    if route not in _ROUTES or state not in _STATES:
        return {"state": "blocked", "reason": "unrecognized_backend_state"}
    result = response.get("result")
    duplicate_value = result.get("duplicate", False) if isinstance(result, Mapping) else False
    if type(duplicate_value) is not bool:
        return {"state": "blocked", "reason": "malformed_duplicate_flag"}
    was_duplicate = duplicate_value
    return {
        "state": state,
        "route": route,
        "request_key": request_key,
        "duplicate": was_duplicate,
        "finished": state in {"completed", "failed", "blocked", "cancelled"},
        "backend_receipt_required": state in {"queued", "running"},
        "raw_backend_data_exposed": False,
    }


def get_owner_mentor_receipt(
    *,
    verified_subject: str | None,
    owner_subject: str | None,
    request_key: str,
    read_privileged_receipt: Callable[[str], Mapping[str, Any]],
) -> dict[str, Any]:
    """Server-only adapter around sjm_ops.mentor_command_receipt_v1(key)."""
    require_verified_owner(verified_subject, owner_subject)
    require_key(request_key)
    raw = read_privileged_receipt(request_key)
    if not isinstance(raw, Mapping):
        return {"found": False, "state": "blocked", "details_exposed": False}
    if raw.get("state") not in _STATES:
        return {"found": False, "state": "blocked", "details_exposed": False}

    # Receipt flags must be genuine booleans: strings like "false" are unsafe.
    for flag in ("found", "is_final", "evidence_present", "details_exposed"):
        if flag in raw and type(raw[flag]) is not bool:
            return {"found": False, "state": "blocked", "details_exposed": False}

    # The allowlist ensures SQL future extra fields (including private results)
    # can never reach the mobile/browser caller automatically.
    # Reject nested values even if their field names are allowlisted.
    for name in _RECEIPT_KEYS:
        if name in raw and type(raw[name]) not in (str, int, bool, type(None)):
            return {"found": False, "state": "blocked", "details_exposed": False}
    result = {name: raw[name] for name in _RECEIPT_KEYS if name in raw}
    result["details_exposed"] = False
    return result
