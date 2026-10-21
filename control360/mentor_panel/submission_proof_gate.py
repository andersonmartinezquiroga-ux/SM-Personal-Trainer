"""Reject static public YPAI 'Application received' copy as proof.

The public vacancy HTML can contain confirmation text before submission.
This module is read-only and never submits forms or stores private tokens.
"""
from dataclasses import dataclass
from typing import Mapping
from receipt_reconciliation import classify_email

@dataclass(frozen=True)
class ProofDecision:
    confirmed: bool
    reason: str

def assess_ypai_proof(*, source: str, evidence: Mapping | None) -> ProofDecision:
    if source == 'gmail_official_receipt':
        verdict = classify_email(evidence)
        if verdict.status == 'confirmed_receipt':
            return ProofDecision(True, 'known_independently_verified_official_receipt')
        return ProofDecision(False, 'email_not_independently_verified')
    if source in ('public_job_page_html', 'public_job_page_screenshot', 'search_snippet'):
        return ProofDecision(False, 'static_public_confirmation_copy_not_evidence')
    if source == 'post_submit_browser_screen':
        return ProofDecision(False, 'needs_independent_live_session_review')
    if source == 'supabase_private_receipt':
        return ProofDecision(False, 'existing_receipt_requires_case_reconciliation')
    return ProofDecision(False, 'unknown_or_missing_evidence')
