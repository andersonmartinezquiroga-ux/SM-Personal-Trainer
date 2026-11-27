package com.sjm.kairos.mobile;
public final class OwnNotificationProofSelfTest {
    public static void main(String[] args){
        String pkg="com.sjm.kairos.mobile",tag=OwnNotificationProof.tag("test-job"),channel="kairos_alert_1";
        if(!OwnNotificationProof.matches(pkg,tag,channel,pkg,tag,202,channel))throw new AssertionError("exact");
        if(OwnNotificationProof.matches(pkg,tag,channel,"other",tag,202,channel))throw new AssertionError("package");
        if(OwnNotificationProof.matches(pkg,tag,channel,pkg,"other",202,channel))throw new AssertionError("tag");
        if(OwnNotificationProof.matches(pkg,tag,channel,pkg,tag,101,channel))throw new AssertionError("foreground service");
        if(OwnNotificationProof.matches(pkg,tag,channel,pkg,tag,202,"other"))throw new AssertionError("channel");
        if(OwnNotificationProof.matches(pkg,tag,channel,pkg,null,202,channel))throw new AssertionError("missing tag");
        System.out.println("OWN_NOTIFICATION_PROOF PASS 6 cases");
    }
}
