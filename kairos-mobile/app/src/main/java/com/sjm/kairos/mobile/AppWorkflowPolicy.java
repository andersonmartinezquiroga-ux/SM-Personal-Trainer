package com.sjm.kairos.mobile;

import java.util.Locale;

/** Shared, testable safety contract for owner-approved multi-step app workflows. */
public final class AppWorkflowPolicy {
    private AppWorkflowPolicy() {}
    public static final int MAX_STEPS=8;
    public static boolean isValidPackage(String pkg) {
        if(pkg==null || pkg.length()<5 || pkg.length()>130 ||
            !pkg.matches("[a-zA-Z][a-zA-Z0-9_]*(\\.[a-zA-Z][a-zA-Z0-9_]*)+"))return false;
        String s=pkg.toLowerCase(Locale.ROOT);
        return !s.equals("com.android.settings") &&
            !s.equals("com.google.android.packageinstaller") &&
            !s.equals("com.android.packageinstaller") &&
            !s.equals("com.android.systemui") &&
            !s.equals("com.google.android.permissioncontroller") &&
            !s.equals("com.android.permissioncontroller") &&
            !s.equals("com.android.vending") &&
            !s.equals("com.sjm.kairos.mobile");
    }
    public static boolean isValidSelector(String selector) {
        if(selector==null || selector.length()<4 || selector.length()>160)return false;
        String x=selector.toLowerCase(Locale.ROOT);
        if(x.contains("password") || x.contains("passwd") || x.contains("contrase") ||
           x.contains("pin_code") || x.contains("cvv") || x.contains("otp") ||
           x.contains("security_code") || x.contains("one_time"))return false;
        return (selector.startsWith("id:") && selector.length()>3) ||
               (selector.startsWith("text:") && selector.length()>5) ||
               (selector.startsWith("desc:") && selector.length()>5) ||
               (selector.startsWith("hint:") && selector.length()>5);
    }
    public static boolean isSensitiveClick(String selector){
        if(selector==null)return true;
        String s=selector.toLowerCase(Locale.ROOT);
        String[] blocked={"send","enviar","submit","purchase","checkout","buy now",
            "comprar","pagar","pay","transfer","transferir","borrar","delete",
            "eliminar","logout","cerrar sesión","confirmar pago","autorizar pago",
            "aceptar términos","grant permission","conceder permiso",
            "install","instalar","uninstall","desinstalar","save password","guardar contraseña"};
        for(String term:blocked)if(s.contains(term))return true;
        return false;
    }
    public static boolean isAllowedStep(String action,String selector,String value){
        if(action==null)return false;
        switch(action){
            case "tap":
                return isValidSelector(selector) && !isSensitiveClick(selector)
                    && (value==null || value.isEmpty());
            case "type":
                return isValidSelector(selector) && value!=null &&
                    value.length()>=1 && value.length()<=400 && !value.contains("\u0000");
            case "ime_search":
                return isValidSelector(selector) && (value==null || value.isEmpty());
            case "youtube_play_video":
                return (selector==null || selector.isEmpty()) && value!=null &&
                       value.matches("[A-Za-z0-9_-]{11}");
            case "tap_video":
                if(selector!=null&&!selector.isEmpty() || value==null ||
                   value.length()<7 || value.length()>160 || value.contains("\u0000")) return false;
                String[] parts=value.split("\\|",-1);
                return parts.length==2 && parts[0].trim().length()>=3 &&
                       parts[1].trim().length()>=3 && !isSensitiveClick(value);
            case "scroll_down": case "scroll_up":
                return (selector==null || selector.isEmpty() || isValidSelector(selector))
                    && (value==null || value.isEmpty());
            case "back":
                return (selector==null || selector.isEmpty()) &&
                    (value==null || value.isEmpty());
            case "wait":
                return (selector==null || selector.isEmpty()) &&
                    value!=null && ("400".equals(value)||"800".equals(value)||"1200".equals(value));
            default: return false;
        }
    }
}
