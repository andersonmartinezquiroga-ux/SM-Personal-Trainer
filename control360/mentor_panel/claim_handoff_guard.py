"""SJM Control 360: offline fail-closed preflight for a RESERVED claim.

NEVER submits a form. Inputs marked trusted MUST be fetched by an
authenticated backend, never accepted from browser JSON or a public client.
"""
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlsplit
from uuid import UUID
import re

_ALLOWED_PATH = re.compile(r"^/jobs/openings/[a-z0-9-]+$")


@dataclass(frozen=True)
class HandoffDecision:
    review_ready: bool
    reason: str
    form_submitted: bool = False


def assess_reserved_claim(*, case_key: str, official_url: str,
                          trusted_case_key: str, trusted_official_url: str,
                          claim_result: Mapping | None,
                          official_receipt_exists: bool,
                          owner_session_verified: bool) -> HandoffDecision:
    """Fail closed. Only allows live-form review, NOT form submission.

    Gateway must independently verify claim ownership, current receipt
    status, owner session, and live form terms immediately before acting.
    """
    def deny(reason: str) -> HandoffDecision:
        return HandoffDecision(False, reason)

    if owner_session_verified is not True:
        return deny("owner_session_unverified")
    if not all(isinstance(v, str) and v for v in
               (case_key, official_url, trusted_case_key, trusted_official_url)):
        return deny("missing_case_or_url")
    if case_key != trusted_case_key or official_url != trusted_official_url:
        return deny("trusted_case_url_mismatch")
    try:
        url = urlsplit(official_url)
    except ValueError:
        return deny("invalid_official_url")
    if (url.scheme != "https" or url.netloc != "freelancer.ypai.ai"
            or not _ALLOWED_PATH.fullmatch(url.path) or url.query or url.fragment):
        return deny("unverified_official_url")
    if official_receipt_exists is not False:
        return deny("receipt_present_or_unknown")
    if not isinstance(claim_result, Mapping):
        return deny("missing_trusted_claim")
    if (claim_result.get("reserved") is not True
            or claim_result.get("form_submitted") is not False
            or claim_result.get("reason") != "reservation_only_live_form_review_required"):
        return deny("reservation_not_verified")
    claim_id = claim_result.get("claim_id")
    try:
        if not isinstance(claim_id, str) or str(UUID(claim_id)) != claim_id.lower():
            raise ValueError("bad UUID")
    except (ValueError, AttributeError):
        return deny("invalid_claim_id")
    return HandoffDecision(True, "reservation_for_live_review_only")
