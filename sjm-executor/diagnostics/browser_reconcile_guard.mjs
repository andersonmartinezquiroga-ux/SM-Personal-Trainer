// KAIRÓS 360 — pure, fail-closed reconciliation guard.
// No network, browser, credentials or external submissions.
const TERMINAL = new Set(['done', 'failed']);
const HUMAN_BLOCK = /captcha|2fa|otp|verification|human|unauthori[sz]ed|forbidden|payment|contract|signature/i;
export function reconcileBrowserJob(job) {
  if (!job || !job.id || !job.operation || !job.state) return {action:'manual_review', reason:'missing_identity'};
  if (job.operation !== 'inspect' && job.operation !== 'self_test') return {action:'manual_review', reason:'unsupported_operation'};
  if (job.operation === 'self_test') return {action:'never_retry', reason:'local_test_not_external'};
  if (HUMAN_BLOCK.test(String(job.error_message ?? '') + ' ' + String(job.error_code ?? ''))) return {action:'never_retry', reason:'human_or_sensitive_block'};
  if (!job.request_id) return {action:'manual_review', reason:'missing_request_id'};
  if (!TERMINAL.has(job.state)) return {action:'manual_review', reason:'nonterminal_reconcile_first'};
  if (job.state === 'done') return {action:'never_retry', reason:'already_completed'};
  // Failed inspection may have navigated before a disconnect. Never blindly replay.
  return {action:'manual_review', reason:'failed_inspection_requires_evidence'};
}
export function isExternalSubmissionProven(job) {
  // This module only handles inspection and local tests. Neither proves a submission.
  return false;
}
