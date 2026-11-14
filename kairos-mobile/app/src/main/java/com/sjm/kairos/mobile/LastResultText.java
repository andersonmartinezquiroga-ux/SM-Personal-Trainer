package com.sjm.kairos.mobile;

/**
 * Mensaje explicativo de consulta LOCAL, sin credenciales, sin red y sin datos de apps ajenas.
 * La hora de la consulta nunca implica que se haya recibido una orden nueva.
 */
final class LastResultText {
    private LastResultText() {}

    static String compose(String checkedAt, String localStatus, String bridgeStatus,
                          boolean hasPendingReceipt, boolean paused) {
        String last = localStatus == null || localStatus.trim().isEmpty()
            ? "Aún no hay un resultado local guardado." : localStatus;
        String bridge = bridgeStatus == null || bridgeStatus.trim().isEmpty()
            ? "Sin información reciente del sondeo." : bridgeStatus;
        return "CONSULTA LOCAL HECHA: " + checkedAt
            + "\nÚLTIMO RESULTADO GUARDADO: " + last
            + "\nSONDEO / ACUSE: " + bridge
            + (paused ? "\nÓRDENES REMOTAS PAUSADAS POR EL TITULAR." : "\nÓRDENES REMOTAS HABILITADAS.")
            + (hasPendingReceipt
                ? "\nATENCIÓN: falta enviar al servidor una confirmación pendiente."
                : "\nSIN CONFIRMACIÓN PENDIENTE EN ESTE TELÉFONO.")
            + "\nEsta consulta no ejecutó ni envió una orden nueva. Un resultado antiguo no prueba actividad actual.";
    }
}
