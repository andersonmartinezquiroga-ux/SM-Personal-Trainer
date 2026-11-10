"""Server-side Supabase Auth user verification for the SJM Mentor gateway.

Candidate only: no user is created, no server is deployed, and no token is
trusted based on its unverified JWT payload. The configured project reference
and API key must come from server configuration, never from an HTTP client.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.request import Request, build_opener, HTTPRedirectHandler
from uuid import UUID

_PROJECT_RE = re.compile(r"^[a-z0-9]{20}$")
_JWT_RE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
_MAX_RESPONSE = 65536


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class SupabaseAuthVerifier:
    """Callable adapter for MentorHTTPApp.verify_bearer_token.

    Each call asks Supabase Auth /auth/v1/user to validate the token. Network,
    schema, and authentication errors fail closed. The returned UUID is not
    enough for authorization: MentorHTTPApp separately compares it with the
    pinned owner UUID from protected server configuration.
    """

    def __init__(self, *, project_ref: str, api_key: str, opener=None, timeout=4):
        if not isinstance(project_ref, str) or not _PROJECT_RE.fullmatch(project_ref):
            raise ValueError("invalid_project_ref")
        if not isinstance(api_key, str) or not api_key or any(c in api_key for c in "\r\n"):
            raise ValueError("invalid_server_api_key")
        if type(timeout) not in (int, float) or not 0 < timeout <= 10:
            raise ValueError("invalid_timeout")
        self._url = f"https://{project_ref}.supabase.co/auth/v1/user"
        self._api_key = api_key
        self._opener = opener or build_opener(_NoRedirect()).open
        self._timeout = timeout

    def __call__(self, bearer_token: str) -> str | None:
        if (not isinstance(bearer_token, str)
                or not 16 <= len(bearer_token) <= 4096
                or not _JWT_RE.fullmatch(bearer_token)):
            return None
        request = Request(self._url, headers={
            "Authorization": "Bearer " + bearer_token,
            "apikey": self._api_key,
            "Accept": "application/json",
        }, method="GET")
        try:
            with self._opener(request, timeout=self._timeout) as response:
                if response.status != 200:
                    return None
                final_url = response.geturl() if hasattr(response, "geturl") else self._url
                if final_url != self._url:
                    return None
                raw = response.read(_MAX_RESPONSE + 1)
            if len(raw) > _MAX_RESPONSE:
                return None
            def reject_duplicate_keys(pairs):
                data = {}
                for key, value in pairs:
                    if key in data:
                        raise ValueError("duplicate_json_key")
                    data[key] = value
                return data
            user = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
        except Exception:
            return None
        if not isinstance(user, dict):
            return None
        if user.get("aud") != "authenticated" or user.get("role") != "authenticated":
            return None
        if "is_anonymous" in user and type(user["is_anonymous"]) is not bool:
            return None
        if user.get("is_anonymous") is True:
            return None
        if user.get("banned_until") is not None or user.get("deleted_at") is not None:
            return None
        email_confirmation = user.get("email_confirmed_at")
        phone_confirmation = user.get("phone_confirmed_at")
        for timestamp in (email_confirmation, phone_confirmation):
            if timestamp is None:
                continue
            if not isinstance(timestamp, str) or not timestamp.strip():
                return None
            try:
                parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                return None
            if parsed_time.tzinfo is None or parsed_time.utcoffset() is None:
                return None
        if not (email_confirmation or phone_confirmation):
            return None
        subject = user.get("id")
        if not isinstance(subject, str):
            return None
        try:
            parsed = UUID(subject)
        except (ValueError, AttributeError):
            return None
        return str(parsed) if str(parsed) == subject.lower() else None
