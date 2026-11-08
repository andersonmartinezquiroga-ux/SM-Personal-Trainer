package com.sjm.kairos.mobile;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONObject;

/**
 * Buzón privado y duradero para la confirmación de las órdenes.
 * No guarda claves, contenido de Gmail ni información de pantalla.
 * La confirmación solo se elimina cuando el servidor responde OK.
 */
final class CommandReceiptStore {
    private static final String PREFS = "kairos_command_receipts_v2";
    private static final String PENDING = "pending";
    private CommandReceiptStore() {}

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
    static synchronized boolean save(Context context, String commandId, String result, String message) {
        if (commandId == null || !commandId.matches("[0-9a-fA-F-]{36}")
            || !("completed".equals(result) || "failed".equals(result))) return false;
        try {
            JSONObject receipt = new JSONObject();
            receipt.put("commandId", commandId);
            receipt.put("result", result);
            receipt.put("message", message == null ? "" : message.substring(0, Math.min(message.length(), 280)));
            receipt.put("storedAt", System.currentTimeMillis());
            return prefs(context).edit().putString(PENDING, receipt.toString()).commit();
        } catch (Exception e) { return false; }
    }
    static synchronized JSONObject getPending(Context context) {
        String raw = prefs(context).getString(PENDING, "");
        if (raw == null || raw.isEmpty()) return null;
        try {
            JSONObject receipt = new JSONObject(raw);
            // No eliminar la confirmación cuando se pierde internet: mantenerla hasta ACK real.
            // Si expira por tiempo, el servidor podría volver a entregar la orden ya ejecutada.
            if (!receipt.has("storedAt") || !receipt.has("commandId")
                    || !receipt.has("result")) return null;
            return receipt;
        } catch (Exception e) { clear(context); return null; }
    }
    static boolean isPaused(Context context) {
        return prefs(context).getBoolean("paused", false);
    }
    static void setPaused(Context context, boolean paused) {
        prefs(context).edit().putBoolean("paused", paused).commit();
    }
    static synchronized void clear(Context context) {
        prefs(context).edit().remove(PENDING).commit();
    }
    static synchronized void mark(Context context, String description) {
        String shortText = description == null ? "" : description.substring(0, Math.min(description.length(), 140));
        prefs(context).edit()
            .putString("lastStatus", shortText)
            .putLong("lastStatusTime", System.currentTimeMillis()).apply();
    }
    static String status(Context context) {
        SharedPreferences p = prefs(context);
        String value = p.getString("lastStatus", "Aún sin órdenes comprobadas");
        long at = p.getLong("lastStatusTime", 0);
        if (at <= 0) return value;
        java.text.DateFormat time = java.text.DateFormat.getTimeInstance(java.text.DateFormat.SHORT);
        return value + " · " + time.format(new java.util.Date(at));
    }
}
