"""Read-only, fail-closed reconciliation for SJM Control 360 application safety.

Accepts only backend-supplied snapshots; NEVER submits, reserves, or grants access.
The result is diagnostic and NEVER authorization to submit an application.
"""
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

@dataclass(frozen=True)
class AuditResult:
    passed: bool
    findings: tuple[str, ...]
    receipt_count: int
    active_claim_count: int
    submission_authorized: bool = False


def audit_snapshot(*, receipts: Sequence[Mapping], claims: Sequence[Mapping],
                   trusted_cases: Mapping[str, str], auth_user_count: int,
                   receipts_rls: bool, claims_rls: bool,
                   public_execute_granted: bool, external_gateway_connected: bool,
                   expected_receipt_case_keys: frozenset[str]) -> AuditResult:
    """Verify consistency; deny readiness if anything is missing or unexpected.

    Snapshots and trusted_cases MUST be fetched independently on a trusted server.
    Passing this audit never authorizes a form submission.
    """
    findings = []
    if type(auth_user_count) is not int or auth_user_count < 1:
        findings.append("owner_auth_missing")
    if receipts_rls is not True or claims_rls is not True:
        findings.append("rls_missing_or_unverified")
    if public_execute_granted is not False:
        findings.append("public_execute_not_verified_denied")
    if external_gateway_connected is not True:
        findings.append("external_gateway_not_connected")
    if not isinstance(trusted_cases, Mapping) or not trusted_cases:
        findings.append("trusted_case_catalog_missing")
        trusted_cases = {}
    if not isinstance(receipts, (list, tuple)) or not isinstance(claims, (list, tuple)):
        return AuditResult(False, tuple(findings + ["invalid_snapshot_shape"]), 0, 0)
    if not isinstance(expected_receipt_case_keys, frozenset):
        findings.append("expected_receipts_unverified")
        expected_receipt_case_keys = frozenset()
    seen_receipt_cases, seen_receipt_urls = set(), set()
    for row in receipts:
        if not isinstance(row, Mapping):
            findings.append("invalid_receipt_row")
            continue
        case, url = row.get("case_key"), row.get("application_url")
        if not isinstance(case, str) or not isinstance(url, str) or not case or not url:
            findings.append("invalid_receipt_identity")
            continue
        if case in seen_receipt_cases or url in seen_receipt_urls:
            findings.append("duplicate_official_receipt")
        seen_receipt_cases.add(case)
        seen_receipt_urls.add(url)
        if trusted_cases.get(case) != url:
            findings.append("receipt_trusted_url_mismatch")
    if seen_receipt_cases != expected_receipt_case_keys:
        findings.append("official_receipts_missing_or_unexpected")
    seen_claim_cases = set()
    for row in claims:
        if not isinstance(row, Mapping):
            findings.append("invalid_claim_row")
            continue
        case, url, state = row.get("case_key"), row.get("application_url"), row.get("state")
        if not isinstance(case, str) or not isinstance(url, str) or not case or not url:
            findings.append("invalid_claim_identity")
            continue
        if case in seen_claim_cases:
            findings.append("duplicate_claim")
        seen_claim_cases.add(case)
        if trusted_cases.get(case) != url:
            findings.append("claim_trusted_url_mismatch")
        if case in seen_receipt_cases or url in seen_receipt_urls:
            findings.append("claim_conflicts_with_official_receipt")
        if state not in ("reserved", "released", "expired", "submitted"):
            findings.append("unknown_claim_state")
    return AuditResult(not findings, tuple(sorted(set(findings))),
                       len(receipts), len(claims))
