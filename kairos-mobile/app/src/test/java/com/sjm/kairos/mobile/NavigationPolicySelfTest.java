package com.sjm.kairos.mobile;

public final class NavigationPolicySelfTest {
    private static void expect(boolean actual, String label) {
        if (!actual) throw new AssertionError(label);
    }
    public static void main(String[] args) {
        expect(SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app/mentor"),"own mentor");
        expect(SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app/kairos"),"own kairos");
        expect(SjmNavigationPolicy.isAllowedApp("com.arlosoft.macrodroid"),"Macrodroid");
        expect(!SjmNavigationPolicy.isAllowedApp("com.android.settings"),"settings blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("http://sjm-control-360.floot.app/mentor"),"http blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://evil.com/mentor"),"other hosts blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app.evil.com/mentor"),"lookalike blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app/mentor?do=pay"),"query blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://evil.com@sjm-control-360.floot.app/mentor"),"credentials blocked");
        expect(!SjmNavigationPolicy.isAllowedUrl("https://sjm-control-360.floot.app/_api/kairos/phone_poll"),"api blocked");
        System.out.println("KAIRÓS v0.2: 10 pruebas de navegación segura OK");
    }
}
