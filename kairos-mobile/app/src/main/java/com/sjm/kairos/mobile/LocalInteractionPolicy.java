package com.sjm.kairos.mobile;

/** Nunca permite escritura en aplicaciones externas ni texto arbitrario. */
final class LocalInteractionPolicy {
    static final String OWN_PACKAGE="com.sjm.kairos.mobile";
    static final String PROOF_TEXT="KAIROS PRUEBA LOCAL 0310";
    private LocalInteractionPolicy(){}
    static boolean isOwnPackage(String s){return OWN_PACKAGE.equals(s);}
    static boolean isProofText(String s){return PROOF_TEXT.equals(s);}
}
