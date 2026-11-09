package com.sjm.kairos.mobile;

import java.util.concurrent.atomic.AtomicLong;

/** Nunca permite escritura en aplicaciones externas ni texto arbitrario. */
final class LocalInteractionPolicy {
    static final String OWN_PACKAGE="com.sjm.kairos.mobile";
    static final String PROOF_TEXT="KAIROS PRUEBA LOCAL 0310";
    private LocalInteractionPolicy(){}
    /** One-time, three-second in-process proof for a *server requested* own-app click. */
    private static final AtomicLong remoteArmedAt=new AtomicLong(0L);
    private static final AtomicLong remoteConfirmedAt=new AtomicLong(0L);
    static void armRemoteClick(){
        remoteConfirmedAt.set(0L);
        remoteArmedAt.set(System.nanoTime());
    }
    static void cancelRemoteClick(){ remoteArmedAt.set(0L); remoteConfirmedAt.set(0L); }
    static boolean consumeRemoteClick(){
        long armed=remoteArmedAt.get();
        long now=System.nanoTime();
        if(armed<=0L || now-armed<0L || now-armed>3_000_000_000L) return false;
        if(!remoteArmedAt.compareAndSet(armed,0L))return false;
        remoteConfirmedAt.set(now);
        return true;
    }
    static boolean remoteClickWasConfirmed(){return remoteConfirmedAt.get()>0L;}

    static boolean isOwnPackage(String s){return OWN_PACKAGE.equals(s);}
    static boolean isProofText(String s){return PROOF_TEXT.equals(s);}
}
