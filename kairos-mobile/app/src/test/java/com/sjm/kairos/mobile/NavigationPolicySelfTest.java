package com.sjm.kairos.mobile;

public final class NavigationPolicySelfTest {
    private static void expect(boolean actual, String label) {
        if (!actual) throw new AssertionError(label);
    }
    public static void main(String[] args) {
        expect(SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app/mentor"),"own mentor");
        expect(SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app/kairos"),"own kairos");
        expect(SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360-respaldo.vercel.app/"),"backup SJM root");
        expect(SjmNavigationPolicy.isAllowedUrl("https://sjm-kairos-conversacion-sjm-pruebas.vercel.app/"),"conversation SJM root");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360-respaldo.vercel.app/estado"),"unpublished deep link blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-kairos-conversacion-sjm-pruebas.vercel.app/mentor"),"unpublished chat route blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360-respaldo.vercel.app/?pay=true"),"query blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360-respaldo.vercel.app/#token"),"fragment blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360-respaldo.vercel.app.evil.com/"),"lookalike blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://evil.com@sjm-control-360-respaldo.vercel.app/"),"userinfo blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("http://sjm-control-360-respaldo.vercel.app/"),"plaintext blocked");
        expect(SjmNavigationPolicy.isAllowedApp("com.arlosoft.macrodroid"),"Macrodroid");
        expect(SjmNavigationPolicy.isAllowedApp("com.whatsapp"),"WhatsApp");
        expect(SjmNavigationPolicy.isAllowedApp("com.microsoft.office.outlook"),"Outlook");
        expect(SjmNavigationPolicy.isAllowedApp("com.google.android.apps.docs"),"Drive");
        expect(SjmNavigationPolicy.isAllowedApp("com.google.android.youtube"),"YouTube launch allowed");
        expect(!SjmNavigationPolicy.isAllowedApp("com.android.settings"),"settings blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("http://sjm-control-360.floot.app/mentor"),"http blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://evil.com/mentor"),"other hosts blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app.evil.com/mentor"),"lookalike blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app/mentor?do=pay"),"query blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://evil.com@sjm-control-360.floot.app/mentor"),"credentials blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app/_api/kairos/phone_poll"),"api blocked");
        System.out.println("KAIRÓS 0.3.25: navegación segura SJM verificada");
    }
}
