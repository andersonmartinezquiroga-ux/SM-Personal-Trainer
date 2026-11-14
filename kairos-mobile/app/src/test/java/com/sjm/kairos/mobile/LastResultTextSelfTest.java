package com.sjm.kairos.mobile;

public final class LastResultTextSelfTest {
    private static void assertContains(String value, String expected) {
        if (!value.contains(expected)) throw new AssertionError("Falta: "+expected);
    }
    public static void main(String[] args) {
        String noNew = LastResultText.compose("21:07", "Resultado confirmado por CONTROL 360 · 17:46",
            "ACK_RECEIVED_ACCEPTED · 17:46", false, false);
        assertContains(noNew, "CONSULTA LOCAL HECHA: 21:07");
        assertContains(noNew, "17:46");
        assertContains(noNew, "no ejecutó ni envió una orden nueva");
        assertContains(noNew, "SIN CONFIRMACIÓN PENDIENTE");
        String paused = LastResultText.compose("21:08", "", "", true, true);
        assertContains(paused, "ÓRDENES REMOTAS PAUSADAS");
        assertContains(paused, "falta enviar al servidor");
        assertContains(paused, "Aún no hay un resultado local");
        System.out.println("LAST_RESULT_TEXT 2/2 PASS (sin red, sin duplicados)");
    }
}
