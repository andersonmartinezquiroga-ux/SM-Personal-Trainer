-- KAIRÓS 360: audit persisted browser result evidence (read only).
-- 'done' means the worker finished; it does NOT prove an external submission.
-- Never promote self_test or inspect to a real submission.
WITH classified AS (
 SELECT id, job_key, operation, state, attempts, created_at, completed_at,
        response_summary,
        CASE
          WHEN operation IN ('inspect','self_test') THEN 'NON_SUBMISSION_OPERATION'
          WHEN state <> 'done' THEN 'NOT_COMPLETED'
          WHEN completed_at IS NULL THEN 'DONE_WITHOUT_COMPLETED_AT'
          WHEN response_summary IS NULL OR response_summary = '{}'::jsonb THEN 'DONE_WITHOUT_RESULT'
          WHEN lower(coalesce(response_summary->>'submitted','false')) = 'true'
            THEN 'SUBMISSION_FLAG_REQUIRES_EXTERNAL_RECEIPT'
          ELSE 'DONE_NO_SUBMISSION_PROOF'
        END AS evidence_gate
 FROM sjm_ops.browser_jobs
)
SELECT evidence_gate, operation, count(*) AS jobs,
       array_agg(id ORDER BY created_at DESC) AS job_ids
FROM classified
GROUP BY evidence_gate, operation
ORDER BY evidence_gate, operation;
