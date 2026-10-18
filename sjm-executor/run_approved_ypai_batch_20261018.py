"""One-time YPAI batch authorized by the user on 2026-10-18.

Exact roles only. No phone, CV, recordings, CAPTCHA solving, or extra terms.
Safe on later cron dates: exits unless UTC date is exactly 2026-10-18 and batch id matches.
"""
import json, os
from datetime import datetime, timezone
from submit_ypai import apply_ypai_role

EXPECTED_BATCH = "sjm-ypai-three-20261018-v1"
ROLES = [
    ("text-annotator-co", "radar:commercial:ingresos-ypai-text-annotator-co-20261016"),
    ("model-evaluator-co", "radar:commercial:ingresos-ypai-model-evaluator-co-20261016"),
    ("pose-keypoint-annotator-co", "radar:commercial:ingresos-ypai-pose-keypoint-co-20261016"),
]

def main():
    now = datetime.now(timezone.utc)
    if now.date().isoformat() != "2026-10-18":
        print("SJM_BATCH_NOOP wrong_date", flush=True)
        return
    if os.environ.get("YPAI_BATCH_ID") != EXPECTED_BATCH:
        print("SJM_BATCH_NOOP wrong_batch", flush=True)
        return
    approved = {x.strip() for x in os.environ.get("YPAI_APPROVED_CASES", "").split(",") if x.strip()}
    if any(case not in approved for _, case in ROLES):
        print("SJM_BATCH_BLOCKED missing_exact_approval", flush=True)
        return

    name = os.environ.get("YPAI_APPLICANT_NAME", "").strip()
    email = os.environ.get("YPAI_APPLICANT_EMAIL", "").strip()
    country = os.environ.get("YPAI_APPLICANT_COUNTRY", "").strip()
    if not name or not email or country != "Colombia":
        print("SJM_BATCH_BLOCKED applicant_env", flush=True)
        return

    for role_slug, case_key in ROLES:
        try:
            result = apply_ypai_role(
                role_slug, case_key, name, email, country, True, True
            )
            safe = {
                "role_slug": role_slug,
                "case_key": case_key,
                "status": result.get("status"),
                "attempted_submit": bool(result.get("attempted_submit")),
                "confirmed": bool(result.get("confirmed")),
                "confirmation_marker": result.get("confirmation_marker"),
                "required_field": result.get("required_field"),
                "invalid_fields": result.get("invalid_fields"),
            }
        except Exception as exc:
            safe = {
                "role_slug": role_slug,
                "case_key": case_key,
                "status": "runner_exception",
                "attempted_submit": False,
                "confirmed": False,
                "error_type": type(exc).__name__,
            }
        print("SJM_YPAI_RESULT " + json.dumps(safe, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
