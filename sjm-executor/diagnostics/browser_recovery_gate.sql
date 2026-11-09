-- KAIRÓS 360: read-only recovery gate for browser_jobs
-- No retries are performed by this query. All external submissions require independent receipt.
WITH jobs AS (
 SELECT id, job_key, operation, state, attempts, created_at, dispatched_at,
        completed_at, last_checked_at, last_error,
        CASE
          WHEN state IN ('queued','running','dispatched') AND
               coalesce(last_checked_at,dispatched_at,created_at) < now()-interval '20 minutes'
            THEN 'STALE_REQUIRES_LEASE_AND_OWNER_REVIEW'
          WHEN state='failed' AND (coalesce(last_error,'') ILIKE '%captcha%' OR
               coalesce(last_error,'') ILIKE '%2fa%' OR coalesce(last_error,'') ILIKE '%human_challenge%')
            THEN 'HUMAN_VERIFICATION_NO_RETRY'
          WHEN state='failed' AND (coalesce(last_error,'') ILIKE '%domain_not_approved%' OR
               coalesce(last_error,'') ILIKE '%not_verified%')
            THEN 'TARGET_OR_ALLOWLIST_REVIEW_NO_RETRY'
          WHEN state='failed' AND operation='self_test'
            THEN 'QA_FAILURE_NO_EXTERNAL_RETRY'
          WHEN state='failed' AND coalesce(last_error,'') ILIKE '%timeout%'
            THEN 'TIMEOUT_RECONCILE_RESULT_BEFORE_RETRY'
          WHEN state='failed' THEN 'MANUAL_REVIEW'
          ELSE 'NO_RECOVERY_REQUIRED'
        END AS recovery_gate
 FROM sjm_ops.browser_jobs
)
SELECT recovery_gate, operation, count(*) AS jobs,
       array_agg(id ORDER BY created_at DESC) AS job_ids
FROM jobs
GROUP BY recovery_gate,operation
ORDER BY jobs DESC,recovery_gate;
