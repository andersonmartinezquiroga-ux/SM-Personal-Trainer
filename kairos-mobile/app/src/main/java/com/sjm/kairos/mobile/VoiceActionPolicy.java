package com.sjm.kairos.mobile;

/** Keep voice and media independent; concurrent navigation is deliberately narrow. */
final class VoiceActionPolicy {
    private VoiceActionPolicy() {}
    static boolean allowedDuringCommunication(String type) {
        return "notify".equals(type) || "local_test".equals(type);
    }
    static boolean allowedConcurrentNavigationStep(String pkg,String action,String selector) {
        if(!"com.android.chrome".equals(pkg) || action==null)return false;
        if("wait".equals(action) || "scroll_down".equals(action) || "scroll_up".equals(action))
            return selector==null || selector.isEmpty();
        if("tap".equals(action) || "type".equals(action) || "ime_search".equals(action))
            return "id:com.android.chrome:id/url_bar".equals(selector) ||
                   "id:com.android.chrome:id/search_box_text".equals(selector);
        return false;
    }
}
