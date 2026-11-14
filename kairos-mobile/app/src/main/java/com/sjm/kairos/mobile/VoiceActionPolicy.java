package com.sjm.kairos.mobile;
/** Voice protection: only owner-approved, own-package accessibility tests may run
 * alongside notices. No external workflows, apps or URLs may run during a call. */
final class VoiceActionPolicy {
    private VoiceActionPolicy() {}
    static boolean allowedDuringCommunication(String type) {
        return "notify".equals(type) || "local_test".equals(type);
    }
}
