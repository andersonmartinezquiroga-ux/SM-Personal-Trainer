// Pure failover selection: no network calls, credentials or application submissions.
export function chooseProvider(task, providers, now = Date.now()) {
  if (!task || !task.id || !task.kind || !Array.isArray(providers)) throw new TypeError('invalid input');
  if (!['pending','queued','retry_ready'].includes(task.status)) return {state:'hold',reason:'task_not_runnable'};
  if (task.leaseUntil) {
    const leaseExpiry = Date.parse(task.leaseUntil);
    if (!Number.isFinite(leaseExpiry)) return {state:'hold',reason:'invalid_lease'};
    if (leaseExpiry > now) return {state:'hold',reason:'active_lease'};
  }
  if (task.requiresConsent && !task.consentRecorded) return {state:'hold',reason:'authorization_required'};
  if (task.submission && (typeof task.idempotencyKey !== 'string' || !task.idempotencyKey.trim())) return {state:'hold',reason:'missing_idempotency_key'};
  const candidates = providers.filter(p => p && p.enabled === true && p.healthy === true && p.freeQuotaVerified === true && p.estimatedCostUsd === 0 && Array.isArray(p.capabilities) && p.capabilities.includes(task.kind) && Number.isFinite(p.quotaRemaining) && p.quotaRemaining > 0 && (!p.expiresAt || (Number.isFinite(Date.parse(p.expiresAt)) && Date.parse(p.expiresAt) > now)) && (!p.cooldownUntil || (Number.isFinite(Date.parse(p.cooldownUntil)) && Date.parse(p.cooldownUntil) <= now)) && p.id !== task.lastFailedProvider);
  candidates.sort((a,b) => (b.quotaRemaining - a.quotaRemaining) || String(a.id).localeCompare(String(b.id)));
  return candidates.length ? {state:'ready',providerId:candidates[0].id,taskId:task.id} : {state:'queued',reason:'no_verified_free_provider'};
}
