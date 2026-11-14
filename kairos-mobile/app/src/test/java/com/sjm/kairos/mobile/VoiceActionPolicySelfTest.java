package com.sjm.kairos.mobile;
public final class VoiceActionPolicySelfTest {
    private static void check(boolean ok,String detail){if(!ok)throw new AssertionError(detail);}
    public static void main(String[] args) {
        check(VoiceActionPolicy.allowedDuringCommunication("notify"),"notify during voice");
        check(VoiceActionPolicy.allowedDuringCommunication("local_test"),"KAIRÓS own-app test during voice");
        check(!VoiceActionPolicy.allowedDuringCommunication("open_app"),"no external app during voice");
        check(!VoiceActionPolicy.allowedDuringCommunication("open_url"),"no external URL during voice");
        check(!VoiceActionPolicy.allowedDuringCommunication("speak"),"no speech interrupt");
        check(!VoiceActionPolicy.allowedDuringCommunication(null),"null blocked");
        System.out.println("VOICE LOCAL-TEST POLICY 6/6 OK");
    }
}
