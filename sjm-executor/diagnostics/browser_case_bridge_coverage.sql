-- KAIRÓS 360: read-only reconciliation of browser jobs with case traces.
-- NO_CASE_TRACE means no case trace in this view; it does not mean lost execution.
-- Neither done nor a trace is proof of an external submission.
SELECT b.state, b.operation,
       coalesce(t.trace_status, 'NO_CASE_TRACE') AS trace_status,
       count(*) AS jobs,
       count(*) FILTER (WHERE b.request_id IS NULL) AS without_request_id,
       count(*) FILTER (WHERE b.completed_at IS NULL AND b.state IN ('done','failed')) AS terminal_without_completed_at
FROM sjm_ops.browser_jobs AS b
LEFT JOIN sjm_ops.browser_case_trace_v1 AS t ON t.browser_job_id = b.id
GROUP BY b.state, b.operation, coalesce(t.trace_status, 'NO_CASE_TRACE')
ORDER BY b.state, b.operation, trace_status;
