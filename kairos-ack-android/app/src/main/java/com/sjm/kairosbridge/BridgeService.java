package com.sjm.kairosbridge;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.os.Build;
import android.os.IBinder;
import org.json.JSONObject;

public final class BridgeService extends Service {
    static final String ACTION_START = "com.sjm.kairosbridge.START";
    static final String ACTION_STOP = "com.sjm.kairosbridge.STOP";
    private static final String STATUS_CHANNEL = "kairos_bridge_status";
    private static final String ALERT_CHANNEL = "kairos_bridge_alerts_v1";
    private volatile boolean running = false;
    private Thread worker;

    @Override public IBinder onBind(Intent intent) { return null; }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }
        createChannels();
        try {
            startForeground(101, foregroundNotification());
        } catch (Exception exception) {
            saveState("No se pudo iniciar el servicio: " + exception.getClass().getSimpleName());
            stopSelf();
            return START_NOT_STICKY;
        }
        if (!running) {
            running = true;
            worker = new Thread(this::receiveLoop, "Kairos-ack-receiver");
            worker.start();
        }
        return START_NOT_STICKY;
    }

    private void createChannels() {
        NotificationManager nm = getSystemService(NotificationManager.class);
        NotificationChannel status = new NotificationChannel(STATUS_CHANNEL,
                "KAIRÓS — receptor activo", NotificationManager.IMPORTANCE_LOW);
        nm.createNotificationChannel(status);
        NotificationChannel alerts = new NotificationChannel(ALERT_CHANNEL,
                "KAIRÓS — avisos", NotificationManager.IMPORTANCE_HIGH);
        alerts.setDescription("Avisos remotos autorizados de KAIRÓS CONTROL 4.0");
        alerts.enableVibration(true);
        alerts.setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION),
                new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION).build());
        nm.createNotificationChannel(alerts);
    }

    private Notification foregroundNotification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pending = PendingIntent.getActivity(this, 1, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        return new Notification.Builder(this, STATUS_CHANNEL)
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setContentTitle("KAIRÓS: recepción habilitada")
                .setContentText("Servicio activo mientras Android lo permita")
                .setContentIntent(pending)
                .setOngoing(true).build();
    }

    private void saveState(String status) {
        getSharedPreferences("bridge", MODE_PRIVATE).edit()
                .putString("last_event", status).apply();
    }

    private void receiveLoop() {
        while (running) {
            try {
                String key = SecureKey.read(this);
                if (key == null) {
                    saveState("No hay vinculación; recepción detenida.");
                    break;
                }
                JSONObject response = KairosApi.call("GET",
                        "/_api/kairos/phone_command_poll", null, key);
                if (response.optBoolean("ok") && response.optBoolean("shouldExecute")) {
                    JSONObject command = response.optJSONObject("command");
                    if (command != null) handleCommand(key, command);
                }
            } catch (Exception ex) {
                saveState("Error de conexión/lectura: " + ex.getClass().getSimpleName());
            }
            try { Thread.sleep(10000); }
            catch (InterruptedException ignored) { Thread.currentThread().interrupt(); break; }
        }
        running = false;
        stopSelf();
    }

    private void handleCommand(String key, JSONObject command) {
        String id = command.optString("id", "");
        if (!id.matches("[0-9a-fA-F-]{36}")) return;
        if (!"notify".equals(command.optString("type"))) {
            // Nunca afirmar ejecución de acciones que esta app NO implementa.
            saveState("Orden no soportada ignorada: sin acuse.");
            return;
        }
        try {
            // La autorización atómica del servidor DEBE preceder al efecto en Android.
            JSONObject accepted = KairosApi.ack(key, id, "received", null);
            if (!accepted.optBoolean("ok") || !"received".equals(accepted.optString("status"))) {
                saveState("El servidor no autorizó recepción; orden no ejecutada.");
                return;
            }
        } catch (Exception err) {
            saveState("Recepción no autorizada/confirmada; orden no ejecutada.");
            return;
        }

        try {
            if (Build.VERSION.SDK_INT >= 33 &&
                    checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                throw new SecurityException("Permiso de notificaciones denegado");
            }
            JSONObject payload = command.optJSONObject("payload");
            String message = payload == null ? "Aviso KAIRÓS" : payload.optString("message", "Aviso KAIRÓS");
            if (message.length() > 240) message = message.substring(0, 240);
            Notification notice = new Notification.Builder(this, ALERT_CHANNEL)
                    .setSmallIcon(android.R.drawable.ic_dialog_info)
                    .setContentTitle("KAIRÓS CONTROL 4.0")
                    .setContentText(message)
                    .setStyle(new Notification.BigTextStyle().bigText(message))
                    .setAutoCancel(true).build();
            getSystemService(NotificationManager.class).notify(id.hashCode(), notice);
            // "completed" = API local notify() invocado sin error; NO prueba audición o visualización.
            JSONObject completed = KairosApi.ack(key, id, "completed",
                    "ANDROID_NOTIFICATION_POSTED: visual/audio confirmation pending owner");
            saveState(completed.optBoolean("ok")
                    ? "Notificación publicada y acuse completado; falta prueba audible."
                    : "Notificación publicada; confirmación final no aceptada.");
        } catch (Exception error) {
            try {
                KairosApi.ack(key, id, "failed",
                        "ANDROID_NOTIFICATION_FAILED: " + error.getClass().getSimpleName());
            } catch (Exception ignored) { /* Estado conservador: nunca reejecutar el mismo job. */ }
            saveState("Notificación no publicada: " + error.getClass().getSimpleName());
        }
    }

    @Override public void onTimeout(int startId, int fgsType) {
        // Android 15 limita los servicios dataSync; no prometer ejecución permanente.
        saveState("Android terminó el tiempo permitido del servicio.");
        stopSelf();
    }

    @Override public void onDestroy() {
        running = false;
        if (worker != null) worker.interrupt();
        super.onDestroy();
    }
}
