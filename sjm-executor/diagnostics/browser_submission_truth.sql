-- KAIRÓS 360: diagnóstico de resultados del ejecutor (solo lectura).
-- IMPORTANTE: submitted=true en self_test NO es una candidatura real.
-- Un candidato externo requiere además acuse oficial independiente.
SELECT
  COUNT(*) AS total_jobs,
  COUNT(*) FILTER (WHERE operation = 'inspect') AS inspections_only,
  COUNT(*) FILTER (WHERE operation = 'self_test') AS local_tests_only,
  COUNT(*) FILTER (WHERE response_summary->>'submitted' = 'true' AND operation = 'self_test') AS fake_form_successes,
  COUNT(*) FILTER (
    WHERE operation NOT IN ('inspect', 'self_test')
      AND state = 'done'
      AND response_summary->>'submitted' = 'true'
      AND COALESCE(response_summary->>'semantic_status', '') NOT IN ('self_test','inspection_candidate_only')
  ) AS external_submission_candidates_not_receipts
FROM sjm_ops.browser_jobs;
-- No sumar external_submission_candidates_not_receipts a postulaciones oficiales
-- hasta cruzar con sjm_ops.official_application_receipts_v1 y verificar acuse.
