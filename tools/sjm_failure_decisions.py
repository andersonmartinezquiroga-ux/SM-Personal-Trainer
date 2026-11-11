#!/usr/bin/env python3
"""Diagnóstico conservador de incidencias SJM CONTROL 360.
Implementación de una política REAL de decisión (pura, sin efectos).
No envía candidaturas, no hace llamadas HTTP, no concede permisos.
Para conectarla a producción debe verificarse el consumidor y su bitácora.
"""
from dataclasses import dataclass, asdict
import re

@dataclass(frozen=True)
class Context:
    operation: str = "inspect"
    source_allowlisted: bool = False
    case_active: bool = False
    newer_job_exists: bool = False
    known_official_receipt: bool = False
    recent_job_count_24h: int = 0
    failure_age_minutes: int = 0
    authenticated: bool = False

def decide(error: str, ctx: Context) -> dict:
    """Devuelve una instrucción de reparación revisable, nunca la ejecuta."""
    if not isinstance(error, str) or len(error) > 2000:
        error = ""
    e = error.strip().lower()
    def result(code: str, next_step: str, auto: bool = False):
        return {"code": code, "next_step": next_step,
                "automatic_retry_allowed": bool(auto),
                "outbound_submission_allowed": False,
                "real_action_executed": False,
                "source": "fault_classifier_v1"}
    if ctx.known_official_receipt:
        return result("DO_NOT_DUPLICATE", "reconcile_official_receipt_and_follow_up")
    if "sjm_qa_controlled_fault" in e:
        return result("SYNTHETIC_FAULT", "keep_outside_real_cases")
    if "human_challenge" in e or "captcha" in e or "otp" in e:
        return result("HUMAN_CHALLENGE", "request_human_interaction_no_bypass")
    if "executor_domain_not_approved" in e or "unsupported_source" in e:
        return result("ADAPTER_GAP", "review_exact_domain_and_adapter_without_auto_allowlisting")
    if "consent" in e or "approval" in e or "privacy" in e:
        return result("NEEDS_APPROVAL", "specific_owner_approval")
    if "english" in e or "idioma" in e:
        return result("LANGUAGE", "interpret_form_and_verify_actual_eligibility")
    if "missing_transfer_ack" in e or "ack_missing" in e:
        return result("MISSING_HANDOFF_ACK", "reconcile_previous_stage_before_safe_replay")
    if "public_form_or_listing_not_verified" in e or re.match(r"^http:200(?:,|$)",e):
        return result("DYNAMIC_FORM_UNVERIFIED", "inspect_interactively_readonly")
    if re.match(r"^http:(400|422)(?:,|$)",e):
        return result("INVALID_REQUEST", "validate_adapter_contract_and_request_fields")
    if re.match(r"^http:(401|403)(?:,|$)",e):
        return result("AUTH_REQUIRED", "owner_sign_in_and_recheck")
    retryable = bool(re.match(r"^http:(429|502|503|504)(?:,|$)",e)
                     or (e.startswith("http:") and "timeout:true" in e and not
                         re.match(r"^http:(400|401|403)(?:,|$)",e)))
    if retryable:
        may = (
            ctx.operation == "inspect" and ctx.source_allowlisted and
            ctx.case_active and not ctx.newer_job_exists and
            not ctx.known_official_receipt and
            0 <= ctx.recent_job_count_24h < 3 and
            20 <= ctx.failure_age_minutes <= 1440
        )
        return result("TEMPORARY_NETWORK_ERROR",
                      "enqueue_idempotent_readonly_inspection" if may else
                      "hold_retry_and_inspect_case_state",may)
    return result("UNKNOWN_FAILURE","stop_and_request_diagnostics")

def summary_decisions(items):
    counts={}
    for error, context in items:
        code=decide(error,context)["code"]
        counts[code]=counts.get(code,0)+1
    return counts

if __name__ == "__main__":
    from dataclasses import replace
    c=Context(operation="inspect",source_allowlisted=True,case_active=True,
              recent_job_count_24h=1,failure_age_minutes=35)
    print(asdict(c),decide("HTTP:,Timeout of 100000 ms reached,timeout:true",c))
