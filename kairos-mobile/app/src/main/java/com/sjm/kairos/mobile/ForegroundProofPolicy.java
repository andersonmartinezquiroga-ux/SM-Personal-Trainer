package com.sjm.kairos.mobile;

/**
 * Solo etiqueta del paquete: no procesa textos, capturas, credenciales
 * o contenido de la ventana. Limita la prueba remota a Chrome.
 */
final class ForegroundProofPolicy {
    private static final String CHROME="com.android.chrome";
    private ForegroundProofPolicy() {}
    static boolean isAllowedExpected(String packageName) {
        return CHROME.equals(packageName);
    }
    static boolean matches(String expected,String visible) {
        return isAllowedExpected(expected) && CHROME.equals(visible);
    }
}
