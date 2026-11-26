package com.sjm.kairos.mobile;
public final class OwnedUrlProofPolicySelfTest {
    public static void main(String[] args){
        String u="https://sjm-control-360.floot.app/estado";
        if(!OwnedUrlProofPolicy.matches(u,u) ||
           !OwnedUrlProofPolicy.matches(u,"sjm-control-360.floot.app/estado") ||
           !OwnedUrlProofPolicy.matches("https://sjm-control-360.floot.app/","sjm-control-360.floot.app") ||
           OwnedUrlProofPolicy.matches(u,"sjm-control-360.floot.app/estado-falso") ||
           OwnedUrlProofPolicy.matches(u,u+"?token=x") ||
           OwnedUrlProofPolicy.matches(u,"http://sjm-control-360.floot.app/estado") ||
           OwnedUrlProofPolicy.matches(u,"https://sjm-control-360.floot.app.evil.test/estado") ||
           OwnedUrlProofPolicy.matches("https://example.com/","example.com") ||
           OwnedUrlProofPolicy.matches(u,""))
            throw new AssertionError("owned URL exact proof");
        System.out.println("OWNED_URL_PROOF 9/9 PASS");
    }
}
