-- KAIRÓS 360: read-only idempotency and lease audit.
-- This does NOT retry, submit, or claim any job.
-- Duplicate job_key is a warning, not proof of duplicate external submissions.
WITH keyed AS (
 SELECT job_key, count(*) AS total,
        count(*) FILTER (WHERE state IN ('queued','running','dispatched')) AS active,
        count(*) FILTER (WHERE state='done') AS completed,
        count(*) FILTER (WHERE state='failed') AS failed,
        array_agg(id ORDER BY created_at DESC) AS job_ids
 FROM sjm_ops.browser_jobs
 WHERE job_key IS NOT NULL
 GROUP BY job_key
 HAVING count(*) > 1
), stale AS (
 SELECT id,job_key,operation,state,attempts,
        coalesce(last_checked_at,dispatched_at,created_at) AS last_seen
 FROM sjm_ops.browser_jobs
 WHERE state IN ('queued','running','dispatched')
   AND coalesce(last_checked_at,dispatched_at,created_at) < now()-interval '20 minutes'
)
SELECT 'DUPLICATE_JOB_KEY_REVIEW' AS finding, job_key AS reference,
       total AS affected, job_ids::text AS details
FROM keyed
UNION ALL
SELECT 'STALE_ACTIVE_JOB_NO_AUTO_RETRY', coalesce(job_key,id::text),
       1, concat('state=',state,'; attempts=',attempts,'; last_seen=',last_seen)
FROM stale
ORDER BY finding,reference;
