"""One-time YPAI submissions for explicit user authorization on 2026-10-20 (Colombia time)."""
import json, os
from datetime import datetime
from zoneinfo import ZoneInfo
from submit_ypai import apply_ypai_role

EXPECTED_DATE = "2026-10-20"
ROLES = [
    ("text-annotator-co", "radar:commercial:ingresos-ypai-text-annotator-co-20261016"),
    ("model-evaluator-co", "radar:commercial:ingresos-ypai-model-evaluator-co-20261016"),
    ("pose-keypoint-annotator-co", "radar:commercial:ingresos-ypai-pose-keypoint-co-20261016"),
]

def main():
    local_date = datetime.now(ZoneInfo("America/Bogota")).date().isoformat()
    if local_date != EXPECTED_DATE:
        print("SJM_YPAI_BATCH_NOOP wrong_local_date", flush=True)
        return
    approved = {x.strip() for x in os.environ.get("YPAI_APPROVED_CASES","").split(",") if x.strip()}
    if any(case not in approved for _, case in ROLES):
        print("SJM_YPAI_BATCH_BLOCKED missing_exact_approval", flush=True)
        return
    name = os.environ.get("YPAI_APPLICANT_NAME","").strip()
    email = os.environ.get("YPAI_APPLICANT_EMAIL","").strip()
    country = os.environ.get("YPAI_APPLICANT_COUNTRY","").strip()
    if not name or not email or country != "Colombia":
        print("SJM_YPAI_BATCH_BLOCKED applicant_env", flush=True)
        return
    for role_slug, case_key in ROLES:
        try:
            result = apply_ypai_role(role_slug, case_key, name, email, country, True, True)
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
