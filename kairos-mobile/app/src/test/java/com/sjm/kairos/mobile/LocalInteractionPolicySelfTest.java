package com.sjm.kairos.mobile;
public final class LocalInteractionPolicySelfTest {
    private static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);}
    public static void main(String[] args){
        check(LocalInteractionPolicy.isOwnPackage("com.sjm.kairos.mobile"),"own app");
        check(!LocalInteractionPolicy.isOwnPackage("com.android.chrome"),"Chrome blocked");
        check(!LocalInteractionPolicy.isOwnPackage("com.google.android.gm"),"Gmail blocked");
        check(!LocalInteractionPolicy.isOwnPackage("com.android.settings"),"settings blocked");
        check(!LocalInteractionPolicy.isOwnPackage("com.sjm.kairos.mobile.evil"),"lookalike blocked");
        check(!LocalInteractionPolicy.isOwnPackage(null),"null package blocked");
        check(LocalInteractionPolicy.isProofText(LocalInteractionPolicy.PROOF_TEXT),"fixed proof");
        check(!LocalInteractionPolicy.isProofText("secreto"),"secrets blocked");
        check(!LocalInteractionPolicy.isProofText(""),"empty blocked");
        check(!LocalInteractionPolicy.isProofText(null),"null text blocked");
        System.out.println("KAIRÓS política de interacción local: 10 verificaciones OK");
    }
}
