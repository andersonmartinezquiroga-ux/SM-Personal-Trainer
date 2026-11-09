package com.sjm.kairos.mobile;

/** Pruebas sin Android: no aceptar solo una solicitud de apertura como evidencia. */
public final class ForegroundProofPolicySelfTest {
    private static void check(boolean ok,String label) {
        if(!ok)throw new AssertionError(label);
    }
    public static void main(String[] args) {
        check(ForegroundProofPolicy.isAllowedExpected("com.android.chrome"),"chrome allowed");
        check(ForegroundProofPolicy.matches("com.android.chrome","com.android.chrome"),"chrome confirmed");
        check(!ForegroundProofPolicy.matches("com.android.chrome","com.google.android.gm"),"gmail not chrome");
        check(!ForegroundProofPolicy.matches("com.android.chrome","com.android.settings"),"settings blocked");
        check(!ForegroundProofPolicy.matches("com.android.chrome",""),"missing window blocked");
        check(!ForegroundProofPolicy.matches("com.android.chrome",null),"null window blocked");
        check(!ForegroundProofPolicy.matches("com.google.android.gm","com.google.android.gm"),"gmail test not allowed");
        check(!ForegroundProofPolicy.matches(null,"com.android.chrome"),"null expected blocked");
        check(!ForegroundProofPolicy.matches("com.android.chrome.fake","com.android.chrome"),"lookalike blocked");
        System.out.println("KAIRÓS foreground policy: 9 checks OK");
    }
}
