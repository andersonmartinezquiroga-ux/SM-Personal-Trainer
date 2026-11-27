package com.sjm.kairos.mobile;
/** Compares only metadata of our own notification, never message contents. */
final class OwnNotificationProof {
    static final int ID=202;
    static String tag(String commandId){return "kairos-job:"+commandId;}
    static boolean matches(String pkg,String tag,String channel,String observedPkg,String observedTag,int id,String observedChannel){
        return pkg!=null && tag!=null && channel!=null && id==ID &&
            pkg.equals(observedPkg) && tag.equals(observedTag) && channel.equals(observedChannel);
    }
}
