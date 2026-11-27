package com.sjm.kairos.mobile;
public final class ScrollProofPolicySelfTest{
    public static void main(String[] args){
        if(!ScrollProofPolicy.matches(true,12,300)||!ScrollProofPolicy.matches(false,-12,300)||
           ScrollProofPolicy.matches(true,-12,300)||ScrollProofPolicy.matches(false,12,300)||
           ScrollProofPolicy.matches(true,0,300)||ScrollProofPolicy.matches(false,-1,300)||
           ScrollProofPolicy.matches(true,12,-1)||ScrollProofPolicy.matches(true,12,4001))throw new AssertionError("directional");
        if(!ScrollProofPolicy.matchesPositions(true,0,20,60,100,100,300)||
           !ScrollProofPolicy.matchesPositions(false,-1,60,20,100,100,300)||
           ScrollProofPolicy.matchesPositions(true,0,60,20,100,100,300)||
           ScrollProofPolicy.matchesPositions(true,-12,20,60,100,100,300)||
           ScrollProofPolicy.matchesPositions(true,0,20,60,100,120,300)||
           ScrollProofPolicy.matchesPositions(true,0,-1,60,100,100,300)||
           ScrollProofPolicy.matchesPositions(true,0,20,101,100,100,300)||
           ScrollProofPolicy.matchesPositions(true,0,20,60,100,100,4001))throw new AssertionError("positions");
        System.out.println("SCROLL_PROOF_POLICY PASS 16 checks");
    }
}
