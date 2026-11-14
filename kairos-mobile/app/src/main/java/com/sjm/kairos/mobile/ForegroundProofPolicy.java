package com.sjm.kairos.mobile;

/**
 * Solo etiqueta del paquete: no procesa textos, capturas, credenciales
 * o contenido de la ventana. Comprueba solo los paquetes autorizados.
 */
final class ForegroundProofPolicy {
    private static final String CHROME="com.android.chrome";
    private static final String YOUTUBE="com.google.android.youtube";
    private ForegroundProofPolicy() {}
    static boolean isAllowedExpected(String packageName) {
        return CHROME.equals(packageName) || YOUTUBE.equals(packageName);
    }
    static boolean matches(String expected,String visible) {
        return isAllowedExpected(expected) && expected.equals(visible);
    }
}
