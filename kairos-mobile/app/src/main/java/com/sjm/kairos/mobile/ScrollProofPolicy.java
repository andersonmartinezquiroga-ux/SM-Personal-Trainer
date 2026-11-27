package com.sjm.kairos.mobile;
/** A local directional web event is evidence of movement, not physical attribution. */
final class ScrollProofPolicy {
    private ScrollProofPolicy() {}
    static boolean matches(boolean down,int deltaY,long elapsedMs){
        return elapsedMs>=0&&elapsedMs<=4000&&(down?deltaY>=2:deltaY<=-2);
    }
    static boolean matchesPositions(boolean down,int deltaY,int previous,int current,int previousMax,int max,long elapsedMs){
        if(elapsedMs<0||elapsedMs>4000||max<=0||previousMax!=max||
           previous<0||current<0||previous>max||current>max)return false;
        // -1 may represent unavailable delta; do not treat it as proof.
        if(Math.abs((long)deltaY)>=2&&!matches(down,deltaY,elapsedMs))return false;
        long difference=(long)current-previous;
        return down?difference>=2:difference<=-2;
    }
}
