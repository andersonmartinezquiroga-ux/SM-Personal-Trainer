package com.sjm.kairos.mobile;

/** Fixed public labels only; no substring matching, arbitrary selector, or password. */
final class OwnedDiagnosticControlPolicy {
    static final String RUN="Comprobar mi dispositivo";
    static final String EXPAND="Comprobar compatibilidad de este dispositivo (sin descargas)";
    static boolean isAllowedLabel(String label){return RUN.equals(label)||EXPAND.equals(label);}
    private static String normalize(CharSequence value){
        return value==null||value.length()>180?"":value.toString().replaceAll("[\\s\\p{Z}]+"," ").trim();
    }
    static boolean matches(String label,CharSequence text,CharSequence description){
        return isAllowedLabel(label)&&(label.equals(normalize(text))||label.equals(normalize(description)));
    }
}
