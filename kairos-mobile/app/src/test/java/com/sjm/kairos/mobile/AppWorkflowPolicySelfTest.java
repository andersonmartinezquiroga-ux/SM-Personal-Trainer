package com.sjm.kairos.mobile;

public final class AppWorkflowPolicySelfTest {
    static void check(boolean ok, String reason){if(!ok)throw new AssertionError(reason);}
    public static void main(String[] args){
        check(AppWorkflowPolicy.isValidPackage("com.google.android.youtube"),"youtube");
        check(AppWorkflowPolicy.isValidPackage("com.whatsapp"),"whatsapp");
        check(AppWorkflowPolicy.isValidPackage("com.microsoft.office.outlook"),"outlook");
        check(!AppWorkflowPolicy.isValidPackage("com.android.settings"),"settings blocked");
        check(!AppWorkflowPolicy.isValidPackage("com.android.systemui"),"system ui blocked");
        check(!AppWorkflowPolicy.isValidPackage("a;rm"),"invalid package blocked");
        check(AppWorkflowPolicy.isAllowedStep("tap","text:Buscar",null),"tap search");
        check(AppWorkflowPolicy.isAllowedStep("type","hint:Search","KAIRÓS prueba"),"type search");
        check(AppWorkflowPolicy.isAllowedStep("scroll_down","",null),"scroll");
        check(AppWorkflowPolicy.isAllowedStep("back","",null),"back");
        check(!AppWorkflowPolicy.isAllowedStep("tap","text:Enviar",null),"send blocked");
        check(!AppWorkflowPolicy.isAllowedStep("tap","id:com.app:id/delete",null),"delete blocked");
        check(!AppWorkflowPolicy.isAllowedStep("type","id:com.app:id/password","x"),"password blocked");
        check(!AppWorkflowPolicy.isAllowedStep("type","hint:Buscar",""),"blank typed text blocked");
        check(!AppWorkflowPolicy.isAllowedStep("tap","id:com.app:id/pay",null),"pay blocked");
        check(AppWorkflowPolicy.isAllowedStep("ime_search","id:com.google.android.youtube:id/search_edit_text",""),"IME search allowed");
        check(AppWorkflowPolicy.isAllowedStep("tap_video","","Hosanna|Marco Barrientos"),"matched video allowed");
        check(!AppWorkflowPolicy.isAllowedStep("tap_video","","Hosanna"),"video requires song and artist");
        check(!AppWorkflowPolicy.isAllowedStep("tap_video","","Hosanna|"),"video requires real artist");
        check(!AppWorkflowPolicy.isAllowedStep("tap_video","","Comprar|pagar"),"sensitive video blocked");
        check(!AppWorkflowPolicy.isAllowedStep("ime_search","",""),"IME needs a field");
        check(AppWorkflowPolicy.isAllowedStep("youtube_play_video","","RHZTk79wAL4"),"verified video ID accepted");
        check(!AppWorkflowPolicy.isAllowedStep("youtube_play_video","","https://www.youtube.com/watch?v=RHZTk79wAL4"),"URLs disallowed");
        check(!AppWorkflowPolicy.isAllowedStep("youtube_play_video","","not-a-video"),"video ID length limited");
        check(!AppWorkflowPolicy.isAllowedStep("youtube_play_video","desc:Buscar","RHZTk79wAL4"),"video action cannot inject selector");
        check(AppWorkflowPolicy.isAllowedStep("wait","","800"),"bounded wait");
        check(!AppWorkflowPolicy.isAllowedStep("wait","","80000"),"unbounded wait");
        System.out.println("KAIRÓS generic workflow policy 17/17 PASS");
    }
}
