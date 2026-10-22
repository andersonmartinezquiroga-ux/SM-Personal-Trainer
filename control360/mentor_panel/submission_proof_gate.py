"""SJM Control 360: fail-closed evidence classifier (offline; no submissions).

The public vacancy page may contain static 'Application received' HTML.
An official Gmail receipt must be corroborated independently via trusted
Gmail/Supabase adapters before updating the private receipt ledger.
This module deliberately never accepts caller-provided evidence as proof.
"""
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ProofDecision:
    confirmed: bool
    reason: str


def assess_ypai_proof(*, source: str, evidence: Mapping | None) -> ProofDecision:
    if source == "gmail_official_receipt":
        return ProofDecision(False, "requires_independent_gmail_reconciliation")
    if source in ("public_job_page_html", "public_job_page_screenshot", "search_snippet"):
        return ProofDecision(False, "static_public_confirmation_copy_not_evidence")
    if source == "post_submit_browser_screen":
        return ProofDecision(False, "needs_independent_live_session_review")
    if source == "supabase_private_receipt":
        return ProofDecision(False, "existing_receipt_requires_case_reconciliation")
    return ProofDecision(False, "unknown_or_missing_evidence")
