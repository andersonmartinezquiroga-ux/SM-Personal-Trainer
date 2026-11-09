-- KAIRÓS 360 | Read-only failure triage, 2026-11-09
-- Never auto-retry a human challenge, unapproved domain or controlled QA fault.
-- Inspect/self_test are NOT external submissions.
WITH classified AS (
 SELECT id, job_key, operation, state, attempts, created_at, completed_at,
        left(coalesce(last_error,''),300) AS error_excerpt,
        CASE
          WHEN operation='self_test' AND last_error='SJM_QA_CONTROLLED_FAULT_NO_EXTERNAL_TARGET'
            THEN 'EXPECTED_QA_FAULT_NO_RETRY'
          WHEN last_error ILIKE '%human_challenge%' OR last_error ILIKE '%captcha%' OR last_error ILIKE '%2fa%'
            THEN 'HUMAN_CHALLENGE_MANUAL_ONLY'
          WHEN last_error ILIKE '%domain_not_approved%'
            THEN 'DOMAIN_ALLOWLIST_REVIEW_NO_AUTO_RETRY'
          WHEN last_error ILIKE '%timeout%'
            THEN 'TIMEOUT_REVIEW_IDEMPOTENCY_FIRST'
          WHEN last_error ILIKE '%not_verified%'
            THEN 'TARGET_VERIFICATION_REQUIRED'
          ELSE 'MANUAL_TRIAGE'
        END AS triage
 FROM sjm_ops.browser_jobs
 WHERE state='failed'
)
SELECT triage, operation, count(*) AS jobs,
       min(created_at) AS first_seen, max(created_at) AS last_seen,
       array_agg(id ORDER BY created_at DESC) AS job_ids
FROM classified
GROUP BY triage,operation ORDER BY jobs DESC,triage;
