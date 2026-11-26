package com.sjm.kairos.mobile;

/** A local directional accessibility event is evidence of movement, not physical attribution. */
final class ScrollProofPolicy {
    private ScrollProofPolicy() {}
    static boolean matches(boolean down,int deltaY,long elapsedMs){
        return elapsedMs>=0 && elapsedMs<=4000 && (down?deltaY>0:deltaY<0);
    }
}
