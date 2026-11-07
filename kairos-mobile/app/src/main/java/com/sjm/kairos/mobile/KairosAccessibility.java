package com.sjm.kairos.mobile;

import android.accessibilityservice.AccessibilityService;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.view.accessibility.AccessibilityEvent;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Servicio autorizado por el dueño. No lee texto ni ejecuta gestos.
 * Recibe órdenes limitadas del servidor. La apertura de apps es una solicitud
 * a Android; no garantiza que se haya mostrado una pantalla concreta.
 */
public class KairosAccessibility extends AccessibilityService {
    private static final String SERVICE_CHANNEL="kairos_service_1";
    private static final String ALERT_CHANNEL="kairos_alert_1";
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private final Handler handler=new Handler(Looper.getMainLooper());
    private long lastRegistered=0L;
    private boolean active=false;
    private final Runnable tick=new Runnable() {
        @Override public void run() {
            if(!active)return;
            io.execute(()->runBridge());
            handler.postDelayed(this,45_000L);
        }
    };
    @Override protected void onServiceConnected() {
        super.onServiceConnected();
        active=true;
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel(SERVICE_CHANNEL,
            "Estado de KAIRÓS",NotificationManager.IMPORTANCE_LOW));
        manager.createNotificationChannel(new NotificationChannel(ALERT_CHANNEL,
            "Avisos de KAIRÓS",NotificationManager.IMPORTANCE_HIGH));
        Notification notification=new Notification.Builder(this,SERVICE_CHANNEL)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("KAIRÓS Móvil activo")
            .setContentText("Enlace privado con SJM CONTROL 360")
            .setOngoing(true).build();
        try {
            if(Build.VERSION.SDK_INT>=29) {
                startForeground(101,notification,ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
            } else startForeground(101,notification);
        } catch(Exception e) {
            // El vínculo de Accesibilidad sigue activo aunque Android no autorice
            // iniciar el servicio en primer plano; no mentir sobre persistencia.
        }
        CommandReceiptStore.mark(this, "Servicio KAIRÓS habilitado en Accesibilidad");
        handler.postDelayed(tick,1000L);
    }
    private void runBridge() {
        String key=SecretStore.load(this);
        if(key==null || CommandReceiptStore.isPaused(this))return;
        try {
            retryPendingAck(key);
            if (CommandReceiptStore.getPending(this) != null) return;
            long now=System.currentTimeMillis();
            if(now-lastRegistered>8*60_000L){
                JSONArray capabilities=new JSONArray();
                capabilities.put("notify");capabilities.put("open_app");capabilities.put("open_url");
                JSONObject registration=new JSONObject()
                    .put("action","register").put("version",1).put("capabilities",capabilities);
                BridgeHttp.call("/_api/kairos/phone_executor","POST",registration,key);
                lastRegistered=now;
            }
            JSONObject pending=BridgeHttp.call("/_api/kairos/phone_command_poll","GET",null,key);
            if(!pending.optBoolean("shouldExecute",false))return;
            JSONObject command=pending.optJSONObject("command");
            if(command==null)return;
            String commandId=command.optString("id","");
            if(!commandId.matches("[0-9a-fA-F-]{36}"))return;
            JSONObject ack=new JSONObject().put("commandId",commandId).put("result","received");
            BridgeHttp.call("/_api/kairos/phone_command_ack","POST",ack,key);
            CommandReceiptStore.mark(this, "Orden " + command.optString("type") + " recibida; ejecutando");
            handler.post(()->{
                String result;
                boolean success=true;
                try {result=executeCommand(command);}
                catch(Exception e) {success=false;result="Acción no ejecutada: "+e.getClass().getSimpleName();}
                final String outcome = success ? "completed" : "failed";
                final String detail = result.length()>280 ? result.substring(0,280) : result;
                boolean stored = CommandReceiptStore.save(this, commandId, outcome, detail);
                CommandReceiptStore.mark(this, stored
                    ? "Resultado local guardado; confirmando con CONTROL 360"
                    : "No se pudo guardar el resultado; reintentando confirmación");
                io.execute(()->{
                    if (stored) {
                        retryPendingAck(key);
                    } else {
                        try {
                            JSONObject finished=new JSONObject().put("commandId", commandId)
                                .put("result", outcome).put("message", detail);
                            BridgeHttp.call("/_api/kairos/phone_command_ack","POST",finished,key);
                            CommandReceiptStore.mark(this, "Resultado confirmado por CONTROL 360");
                        } catch(Exception e) {
                            CommandReceiptStore.mark(this, "Confirmación pendiente: " + e.getClass().getSimpleName());
                        }
                    }
                });
            });
        }catch(Exception ignored) {
            // Fallos de red no implican que una orden se ejecutó.
        }
    }
    private void retryPendingAck(String key) {
        JSONObject receipt = CommandReceiptStore.getPending(this);
        if (receipt == null) return;
        try {
            JSONObject request = new JSONObject()
                .put("commandId", receipt.getString("commandId"))
                .put("result", receipt.getString("result"))
                .put("message", receipt.optString("message", ""));
            JSONObject response = BridgeHttp.call("/_api/kairos/phone_command_ack", "POST", request, key);
            if (response.optBoolean("ok", false)) {
                CommandReceiptStore.clear(this);
                CommandReceiptStore.mark(this, "Resultado confirmado por CONTROL 360");
            }
        } catch(Exception e) {
            CommandReceiptStore.mark(this, "Esperando conexión para confirmar resultado");
        }
    }

    private String executeCommand(JSONObject command) throws Exception {
        String type=command.optString("type","");
        JSONObject payload=command.optJSONObject("payload");
        if(payload==null)throw new SecurityException("Sin datos");
        if(type.equals("notify")){
            String message=payload.optString("message","");
            if(message.length()<3 || message.length()>280)throw new SecurityException("Texto no permitido");
            Notification n=new Notification.Builder(this,ALERT_CHANNEL)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("KAIRÓS 360 · Aviso")
                .setContentText(message)
                .setStyle(new Notification.BigTextStyle().bigText(message))
                .setAutoCancel(true).build();
            getSystemService(NotificationManager.class).notify((int)(System.currentTimeMillis()%20000)+202,n);
            return "Aviso solicitado al sistema de notificaciones Android";
        }
        if(type.equals("open_app")){
            String pkg=payload.optString("package","");
            if(!SjmNavigationPolicy.isAllowedApp(pkg))
                throw new SecurityException("Aplicación no autorizada");
            Intent open=getPackageManager().getLaunchIntentForPackage(pkg);
            if(open==null)throw new IllegalStateException("Aplicación no instalada o no visible");
            open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(open);
            return "Apertura solicitada a Android; pantalla no comprobada";
        }
        if(type.equals("open_url")){
            Uri uri=Uri.parse(payload.optString("url",""));
            if(!SjmNavigationPolicy.isAllowedUrl(uri.toString()))
                throw new SecurityException("Página no autorizada");
            Intent open=new Intent(Intent.ACTION_VIEW,uri);
            open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(open);
            return "Enlace SJM enviado a Android; pantalla no comprobada";
        }
        throw new SecurityException("Comando no autorizado");
    }
    @Override public void onAccessibilityEvent(AccessibilityEvent event) { /* No lee la pantalla. */ }
    @Override public void onInterrupt() {}
    @Override public boolean onUnbind(Intent intent) {
        active=false;handler.removeCallbacks(tick);io.shutdownNow();
        return super.onUnbind(intent);
    }
    @Override public void onDestroy() {
        active=false;handler.removeCallbacks(tick);io.shutdownNow();
        super.onDestroy();
    }
}
