"""SJM Mentor — private WSGI HTTP boundary (development/test only).

This module is NOT a production authentication provider or a public server.
The hosting environment MUST provide:
  * trusted HTTPS with request limits
  * a VERIFIED identity callback (JWT signature, issuer, audience, expiration)
  * a pinned owner subject from server-side protected configuration
  * privileged SQL adapters that are NEVER exposed to the client
  * rate limits and private logs
Never accept a client supplied "verified_subject" or raw claim as identity.

A fake verifier and in-memory SQL adapters are used only by offline tests.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping

from gateway_core import (
    AccessDenied,
    InvalidInput,
    get_owner_mentor_receipt,
    submit_owner_mentor_text,
)

_REQUEST_RE = re.compile(r"^/v1/mentor/commands/([A-Za-z0-9_-]{4,100})$")
_MAX_BODY_BYTES = 8192


def _reject_duplicate_keys(pairs):
    """Reject ambiguous JSON object keys, including in nested objects."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_non_json_constant(value):
    """Reject NaN/Infinity, which Python accepts but JSON does not."""
    raise ValueError("nonstandard_json_constant")


class MentorHTTPApp:
    """WSGI adapter. Authentication and database access are injected by host."""

    def __init__(
        self,
        *,
        owner_subject: str,
        verify_bearer_token: Callable[[str], str | None],
        submit_to_privileged_sql: Callable[[str, str], Mapping],
        read_privileged_receipt: Callable[[str], Mapping],
    ):
        self.owner_subject = owner_subject
        self.verify_bearer_token = verify_bearer_token
        self.submit_to_privileged_sql = submit_to_privileged_sql
        self.read_privileged_receipt = read_privileged_receipt

    @staticmethod
    def _respond(start_response, status, payload, *, extra_headers=()):
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(data))),
            ("Cache-Control", "no-store, private"),
            ("Pragma", "no-cache"),
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Security-Policy", "default-src 'none'"),
            *extra_headers,
        ]
        start_response(status, headers)
        return [data]

    def __call__(self, environ, start_response):
        def respond(status, data):
            return self._respond(start_response, status, data)

        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "GET")
        submit_route = path == "/v1/mentor/commands"
        receipt_key = _REQUEST_RE.fullmatch(path)
        if not submit_route and not receipt_key:
            return respond("404 Not Found", {"error": "not_found"})
        if (submit_route and method != "POST") or (receipt_key and method != "GET"):
            return self._respond(
                start_response,
                "405 Method Not Allowed",
                {"error": "method_not_allowed"},
                extra_headers=(("Allow", "POST" if submit_route else "GET"),),
            )

        authorization = environ.get("HTTP_AUTHORIZATION", "")
        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            return respond("401 Unauthorized", {"error": "authentication_required"})
        bearer = authorization[len("Bearer "):]
        if not bearer or len(bearer) > 8192:
            return respond("401 Unauthorized", {"error": "authentication_required"})
        try:
            verified_subject = self.verify_bearer_token(bearer)
        except Exception:
            # Never expose token validation errors or provider details.
            return respond("401 Unauthorized", {"error": "authentication_required"})
        if not isinstance(verified_subject, str) or not verified_subject:
            return respond("401 Unauthorized", {"error": "authentication_required"})

        try:
            # No DB access or content parsing before trusted owner authorization.
            from gateway_core import require_verified_owner
            require_verified_owner(verified_subject, self.owner_subject)
        except AccessDenied:
            return respond("403 Forbidden", {"error": "owner_only"})

        if receipt_key:
            try:
                result = get_owner_mentor_receipt(
                    verified_subject=verified_subject,
                    owner_subject=self.owner_subject,
                    request_key=receipt_key.group(1),
                    read_privileged_receipt=self.read_privileged_receipt,
                )
            except InvalidInput:
                return respond("400 Bad Request", {"error": "invalid_request_key"})
            except Exception:
                return respond("502 Bad Gateway", {"error": "backend_unavailable"})
            if not result.get("found", False) and result.get("state") == "not_found":
                return respond("404 Not Found", result)
            return respond("200 OK", result)

        if not environ.get("CONTENT_TYPE", "").lower().startswith("application/json"):
            return respond("415 Unsupported Media Type", {"error": "json_required"})
        try:
            nbytes = int(environ.get("CONTENT_LENGTH") or "-1")
        except (ValueError, TypeError):
            return respond("400 Bad Request", {"error": "invalid_content_length"})
        if nbytes < 2 or nbytes > _MAX_BODY_BYTES:
            return respond("413 Content Too Large", {"error": "body_length_rejected"})
        try:
            raw = environ["wsgi.input"].read(nbytes)
            body = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_non_json_constant,
            )
        except (UnicodeDecodeError, ValueError, KeyError):
            return respond("400 Bad Request", {"error": "invalid_json"})
        if not isinstance(body, dict) or set(body) != {"phrase", "request_key"}:
            return respond("400 Bad Request", {"error": "unsupported_parameters"})
        try:
            result = submit_owner_mentor_text(
                verified_subject=verified_subject,
                owner_subject=self.owner_subject,
                phrase=body["phrase"],
                request_key=body["request_key"],
                submit_to_privileged_sql=self.submit_to_privileged_sql,
            )
        except InvalidInput:
            return respond("400 Bad Request", {"error": "invalid_input"})
        except AccessDenied:
            return respond("403 Forbidden", {"error": "owner_only"})
        except Exception:
            return respond("502 Bad Gateway", {"error": "backend_unavailable"})
        return respond("202 Accepted" if result.get("state") in ("queued", "running") else "200 OK", result)
