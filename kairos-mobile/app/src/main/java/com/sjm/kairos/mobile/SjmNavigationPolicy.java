package com.sjm.kairos.mobile;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/**
 * Política de navegación: solamente páginas conocidas de SJM y aplicaciones
 * aprobadas. No permite pagos, formularios ni navegación arbitraria.
 */
public final class SjmNavigationPolicy {
    private static final String HOST = "sjm-control-360.floot.app";
    private static final Set<String> PAGES = new HashSet<>(Arrays.asList(
        "/", "/mentor", "/kairos", "/estado", "/secretario", "/expedientes", "/sjm-panel-8"
    ));
    private static final Set<String> PACKAGES = new HashSet<>(Arrays.asList(
        "com.android.chrome", "com.google.android.gm", "com.arlosoft.macrodroid"
    ));
    private SjmNavigationPolicy() { }

    public static boolean isAllowedApp(String packageName) {
        return packageName != null && PACKAGES.contains(packageName);
    }
    public static boolean isAllowedUrl(String url) {
        if (url == null || url.length() > 300) return false;
        try {
            URI uri = new URI(url);
            return "https".equalsIgnoreCase(uri.getScheme())
                && HOST.equalsIgnoreCase(uri.getHost())
                && uri.getPort() == -1
                && uri.getUserInfo() == null
                && uri.getRawQuery() == null
                && uri.getRawFragment() == null
                && PAGES.contains(uri.getRawPath());
        } catch (URISyntaxException | IllegalArgumentException e) {
            return false;
        }
    }
}
