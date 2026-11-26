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
        String chrome="com.android.chrome", bar="id:com.android.chrome:id/url_bar";
        check(VoiceActionPolicy.allowedConcurrentNavigationStep(chrome,"type",bar),"search bar write");
        check(VoiceActionPolicy.allowedConcurrentNavigationStep(chrome,"ime_search",bar),"submit search");
        check(VoiceActionPolicy.allowedConcurrentNavigationStep(chrome,"scroll_down",""),"scroll down");
        check(VoiceActionPolicy.allowedConcurrentNavigationStep(chrome,"scroll_up",""),"scroll up");
        check(!VoiceActionPolicy.allowedConcurrentNavigationStep(chrome,"tap","text:Enviar"),"no arbitrary click");
        check(!VoiceActionPolicy.allowedConcurrentNavigationStep(chrome,"type","id:password"),"no password");
        check(!VoiceActionPolicy.allowedConcurrentNavigationStep("com.google.android.youtube","scroll_down",""),"no media workflow");
        check(!VoiceActionPolicy.allowedConcurrentNavigationStep(chrome,"back",""),"no exit navigation");
        System.out.println("VOICE CONCURRENT NAVIGATION 8/8 OK");
    }
}
