package com.sjm.kairos.mobile;

public final class ScrollProofPolicySelfTest {
    public static void main(String[] args){
        if(!ScrollProofPolicy.matches(true,12,300) || !ScrollProofPolicy.matches(false,-12,300) ||
            ScrollProofPolicy.matches(true,-12,300) || ScrollProofPolicy.matches(false,12,300) ||
            ScrollProofPolicy.matches(true,0,300) || ScrollProofPolicy.matches(true,12,-1) ||
            ScrollProofPolicy.matches(true,12,4001))throw new AssertionError("Directional proof policy");
        System.out.println("SCROLL_PROOF_POLICY 7/7 PASS");
    }
}
