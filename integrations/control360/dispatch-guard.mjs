// SJM CONTROL 360: fail-closed dispatch guard (Node 18+, no dependencies).
// Integration required: caller MUST fetch the current row from
// sjm_ops.control360_radar_queue_reconciled_v3 immediately before dispatch.
// This module does NOT send applications or contact external services.
const DENIED = new Set([
  "SIN_REGION_VERIFICADA", "INVESTIGAR_NO_ENVIAR", "ARCHIVADO",
  "SEGUIMIENTO_NO_DUPLICAR", "BLOQUEADO", "ACUSE_AUDITAR",
  "REVISION_MANUAL_PREVIA_SIN_ENVIO", "YA_ENVIADA_ACUSE_GMAIL_20261104",
  "YA_ENVIADA_ACUSE_GMAIL_20261030",
  "CONSULTA_ENVIADA_FORMULARIO_NO_ENVIADO",
  "CONSULTA_ENVIADA_DOSSIER_PENDIENTE"
]);
export function authorizeDispatch(row) {
  if (!row || typeof row !== "object") return {allowed:false, reason:"MISSING_RECORD"};
  if (!row.source_system || !row.source_id) return {allowed:false, reason:"MISSING_SOURCE_KEY"};
  if (!Number.isInteger(row.resolved_radar) || row.resolved_radar < 1 || row.resolved_radar > 6)
    return {allowed:false, reason:"REGION_UNVERIFIED"};
  const state = row.permiso_ejecucion;
  if (typeof state !== "string" || DENIED.has(state))
    return {allowed:false, reason:state || "STATE_UNKNOWN"};
  // No dispatchable status is currently defined. Do not infer authorization
  // from an unrecognized/new state.
  return {allowed:false, reason:"NO_APPROVED_DISPATCH_STATE"};
}
