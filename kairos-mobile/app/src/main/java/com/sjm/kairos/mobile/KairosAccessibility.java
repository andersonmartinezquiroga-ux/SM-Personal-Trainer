package com.sjm.kairos.mobile;

import android.accessibilityservice.AccessibilityService;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.net.Uri;
import android.net.ConnectivityManager;
import android.net.Network;
import android.media.AudioManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.lang.ref.WeakReference;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Servicio autorizado por el dueño. No lee texto privado ni ejecuta gestos.
 * Excepción controlada: permite verificar un clic exclusivamente en un botón
 * de prueba de esta misma app, por solicitud explícita del dueño.
 * Recibe órdenes limitadas del servidor. La apertura de apps es una solicitud
 * a Android; no garantiza que se haya mostrado una pantalla concreta.
 */
public class KairosAccessibility extends AccessibilityService {
    private static final String SERVICE_CHANNEL="kairos_service_1";
    private static final String ALERT_CHANNEL="kairos_alert_1";
    private static volatile WeakReference<KairosAccessibility> connectedService =
        new WeakReference<>(null);
    private static final String LOCAL_TEST_PACKAGE = "com.sjm.kairos.mobile";
    private static final String LOCAL_TEST_VIEW_ID =
        "com.sjm.kairos.mobile:id/kairos_test_target";
    private static final String LOCAL_TEXT_ID="com.sjm.kairos.mobile:id/kairos_text_test_target";
    private static final String LOCAL_BACK_ID="com.sjm.kairos.mobile:id/kairos_back_test_marker";

    /**
     * Prueba opt-in. Nunca ejecuta órdenes remotas ni toca otras apps.
     * Devuelve true SOLO si Android aceptó ACTION_CLICK sobre el control propio.
     * El botón registra por separado la evidencia de que su listener se ejecutó.
     */
    static boolean clickOwnTestTarget() {
        KairosAccessibility service = connectedService.get();
        if (service == null || !service.active ||
            CommandReceiptStore.isPaused(service)) return false;
        AccessibilityNodeInfo root = service.getRootInActiveWindow();
        if (root == null || !LOCAL_TEST_PACKAGE.equals(String.valueOf(root.getPackageName())))
            return false;
        List<AccessibilityNodeInfo> matches = root.findAccessibilityNodeInfosByViewId(
            LOCAL_TEST_VIEW_ID);
        if (matches == null || matches.size() != 1) return false;
        AccessibilityNodeInfo target = matches.get(0);
        if (target == null || !target.isVisibleToUser() ||
            !target.isClickable() || !target.isEnabled() ||
            !LOCAL_TEST_PACKAGE.equals(String.valueOf(target.getPackageName())))
            return false;
        return target.performAction(AccessibilityNodeInfo.ACTION_CLICK);
    }

    /** Solo escribe frase fija en el campo de ensayo de esta misma APK. */
    static boolean fillOwnTestField() {
        KairosAccessibility service=connectedService.get();
        if(service==null||!service.active||CommandReceiptStore.isPaused(service))return false;
        AccessibilityNodeInfo root=service.getRootInActiveWindow();
        if(root==null||!LocalInteractionPolicy.isOwnPackage(String.valueOf(root.getPackageName())))return false;
        List<AccessibilityNodeInfo> found=root.findAccessibilityNodeInfosByViewId(LOCAL_TEXT_ID);
        if(found==null||found.size()!=1)return false;
        AccessibilityNodeInfo target=found.get(0);
        if(target==null||!target.isEnabled()||!target.isVisibleToUser()||
           !target.isEditable()||
           !LocalInteractionPolicy.isOwnPackage(String.valueOf(target.getPackageName())))
           return false;
        android.os.Bundle args=new android.os.Bundle();
        args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,
            LocalInteractionPolicy.PROOF_TEXT);
        return target.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,args);
    }

    /** Solo regresa desde pantalla interna identificada de KAIRÓS. */
    static boolean backFromOwnTestScreen() {
        KairosAccessibility service=connectedService.get();
        if(service==null||!service.active||CommandReceiptStore.isPaused(service))return false;
        AccessibilityNodeInfo root=service.getRootInActiveWindow();
        if(root==null||!LocalInteractionPolicy.isOwnPackage(String.valueOf(root.getPackageName())))return false;
        List<AccessibilityNodeInfo> found=root.findAccessibilityNodeInfosByViewId(LOCAL_BACK_ID);
        if(found==null||found.size()!=1||!found.get(0).isVisibleToUser())return false;
        return service.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK);
    }

    /** An owner-approved remote click is still confined to the internal KAIRÓS test button. */
    private boolean clickOwnRemoteTarget(){
        LocalInteractionPolicy.armRemoteClick();
        boolean started=clickOwnTestTarget();
        if(!started) LocalInteractionPolicy.cancelRemoteClick();
        return started;
    }
    /** Returns true only when the fixed proof phrase appears in OUR editable test field. */
    private boolean fixedOwnTextIsVisible(){
        AccessibilityNodeInfo root=getRootInActiveWindow();
        if(root==null||!LocalInteractionPolicy.isOwnPackage(
                String.valueOf(root.getPackageName()))) return false;
        List<AccessibilityNodeInfo> matches=root.findAccessibilityNodeInfosByViewId(LOCAL_TEXT_ID);
        if(matches==null||matches.size()!=1)return false;
        AccessibilityNodeInfo field=matches.get(0);
        return field!=null&&field.isEnabled()&&field.isEditable()&&field.isVisibleToUser()&&
            LocalInteractionPolicy.isOwnPackage(String.valueOf(field.getPackageName()))&&
            LocalInteractionPolicy.isProofText(String.valueOf(field.getText()));
    }
    private boolean returnedToOwnMain(){
        AccessibilityNodeInfo root=getRootInActiveWindow();
        if(root==null||!LocalInteractionPolicy.isOwnPackage(
                String.valueOf(root.getPackageName())))return false;
        List<AccessibilityNodeInfo> markers=root.findAccessibilityNodeInfosByViewId(LOCAL_BACK_ID);
        List<AccessibilityNodeInfo> home=root.findAccessibilityNodeInfosByViewId(LOCAL_TEXT_ID);
        return (markers==null||markers.isEmpty())&&home!=null&&!home.isEmpty();
    }
    private void verifyOwnLocalAction(String key,String id,String action,int attempt){
        handler.postDelayed(()->{
            if(!active||!verifyingForeground)return;
            boolean success=false;
            try{
                if("click".equals(action))success=LocalInteractionPolicy.remoteClickWasConfirmed();
                else if("write".equals(action))success=fixedOwnTextIsVisible();
                else if("back".equals(action))success=returnedToOwnMain();
            }catch(RuntimeException ignored){}
            if(success){
                verifyingForeground=false;
                storeAndConfirm(key,id,"completed",
                    "OWN_APP_"+action.toUpperCase(java.util.Locale.ROOT)+
                    "_VERIFIED: control restringido dentro de KAIRÓS");
            } else if(attempt<6) {
                verifyOwnLocalAction(key,id,action,attempt+1);
            }else{
                verifyingForeground=false;
                storeAndConfirm(key,id,"failed",
                    "OWN_APP_TEST_NOT_VERIFIED: control propio no visible o no confirmado");
            }
        },attempt==0?350L:350L);
    }

    /** Own-package-only activation before server-origin local proof.
     * Other apps, screens, user data and forms remain inaccessible.
     * BACK never force-opens MainActivity; it requires the private marker. */
    private void startRemoteOwnAppTest(String key,String commandId,JSONObject command) {
        JSONObject body=command.optJSONObject("payload");
        String action=body==null?"":body.optString("action","");
        if(!("click".equals(action)||"write".equals(action)||"back".equals(action))) {
            storeAndConfirm(key,commandId,"failed","OWN_APP_ACTION_NOT_ALLOWED");
            return;
        }
        verifyingForeground=true;
        if(!"back".equals(action)) {
            try {
                Intent own=getPackageManager().getLaunchIntentForPackage(LOCAL_TEST_PACKAGE);
                if(own==null)throw new IllegalStateException("OWN_APP_LAUNCH_UNAVAILABLE");
                own.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                    |Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    |Intent.FLAG_ACTIVITY_SINGLE_TOP);
                startActivity(own);
            }catch(RuntimeException e){
                verifyingForeground=false;
                storeAndConfirm(key,commandId,"failed",
                    "OWN_APP_FOREGROUND_LAUNCH_DENIED: "+e.getClass().getSimpleName());
                return;
            }
        }
        // Android may need time to display the activity after reopening it.
        handler.postDelayed(()->{
            if(!active || !verifyingForeground)return;
            try {
                if(!"back".equals(action)) {
                    prepareOwnTargetVisibility(action);
                    handler.postDelayed(()->runRemoteOwnTestStep(key,commandId,command,action),450L);
                }else {
                    runRemoteOwnTestStep(key,commandId,command,action);
                }
            }catch(RuntimeException e) {
                verifyingForeground=false;
                storeAndConfirm(key,commandId,"failed",
                    "OWN_APP_PREPARATION_FAILED: "+e.getClass().getSimpleName());
            }
        },1200L);
    }
    /** Scroll a matched KAIRÓS-only test widget into view, if necessary. */
    private void prepareOwnTargetVisibility(String action) {
        AccessibilityNodeInfo root=getRootInActiveWindow();
        if(root==null || !LocalInteractionPolicy.isOwnPackage(
            String.valueOf(root.getPackageName())))return;
        final String id="click".equals(action)?LOCAL_TEST_VIEW_ID:LOCAL_TEXT_ID;
        List<AccessibilityNodeInfo> matches=root.findAccessibilityNodeInfosByViewId(id);
        if(matches!=null&&matches.size()==1) {
            AccessibilityNodeInfo target=matches.get(0);
            if(target!=null&&!target.isVisibleToUser())
                target.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SHOW_ON_SCREEN.getId());
        }
    }
    private String ownTestFailureReason(String action){
        AccessibilityNodeInfo root=getRootInActiveWindow();
        if(root==null)return "OWN_APP_NO_ACTIVE_WINDOW";
        if(!LocalInteractionPolicy.isOwnPackage(String.valueOf(root.getPackageName())))
            return "OWN_APP_NOT_FOREGROUND";
        String id="click".equals(action)?LOCAL_TEST_VIEW_ID:
                  "write".equals(action)?LOCAL_TEXT_ID:LOCAL_BACK_ID;
        List<AccessibilityNodeInfo> matches=root.findAccessibilityNodeInfosByViewId(id);
        if(matches==null||matches.size()!=1)return "OWN_APP_TARGET_NOT_FOUND";
        AccessibilityNodeInfo target=matches.get(0);
        if(target==null||!target.isEnabled())return "OWN_APP_TARGET_DISABLED";
        if(!target.isVisibleToUser())return "OWN_APP_TARGET_NOT_VISIBLE";
        return "OWN_APP_ACCESSIBILITY_ACTION_DENIED";
    }
    private void runRemoteOwnTestStep(
        String key,String commandId,JSONObject command,String action) {
        if(!active||!verifyingForeground)return;
        try {
            executeCommand(command);
            verifyOwnLocalAction(key,commandId,action,0);
        }catch(Exception ex){
            verifyingForeground=false;
            String reason=ownTestFailureReason(action);
            storeAndConfirm(key,commandId,"failed",reason);
        }
    }

    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private final Handler handler=new Handler(Looper.getMainLooper());
    private volatile long lastRegistered=0L;
    private volatile boolean active=false;
    private final AtomicBoolean bridgeInFlight=new AtomicBoolean(false);
    private volatile boolean verifyingForeground=false;
    private ConnectivityManager connectivityManager;
    private ConnectivityManager.NetworkCallback networkCallback;

    /** Evita acumular consultas a la red si Android retrasa un ciclo. */
    private void requestBridge() {
        if(!active || !bridgeInFlight.compareAndSet(false,true)) return;
        try {
            io.execute(() -> {
                try { if(active)runBridge(); }
                finally { bridgeInFlight.set(false); }
            });
        } catch(RejectedExecutionException ignored) {
            bridgeInFlight.set(false);
        }
    }
    /** Consulta inmediatamente cuando Android vuelve a tener red por defecto. */
    private void watchConnectivity() {
        connectivityManager=getSystemService(ConnectivityManager.class);
        if(connectivityManager==null)return;
        ConnectivityManager.NetworkCallback callback=new ConnectivityManager.NetworkCallback() {
            @Override public void onAvailable(Network network) {
                lastRegistered=0L;
                requestBridge();
            }
        };
        try {
            connectivityManager.registerDefaultNetworkCallback(callback);
            networkCallback=callback;
        } catch(RuntimeException ex) {
            // Si Android limita los callbacks, queda el temporizador como respaldo.
            CommandReceiptStore.mark(this,"Monitor de red no disponible; consulta periódica activa");
        }
    }
    private void stopWatchingConnectivity() {
        if(connectivityManager!=null && networkCallback!=null) {
            try {connectivityManager.unregisterNetworkCallback(networkCallback);}
            catch(RuntimeException ignored) {}
            networkCallback=null;
        }
    }
    private final Runnable tick=new Runnable() {
        @Override public void run() {
            if(!active)return;
            requestBridge();
            handler.postDelayed(this,45_000L);
        }
    };
    @Override protected void onServiceConnected() {
        super.onServiceConnected();
        active=true;
        connectedService = new WeakReference<>(this);
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
        watchConnectivity();
        handler.postDelayed(tick,1000L);
    }
    /** Evita interrumpir llamadas o clases por voz. La orden queda en
     * queued en Supabase para ser recogida al terminar la comunicación.
     * No se envía un ACK received hasta que el teléfono esté disponible. */
    private boolean hasActiveCommunication() {
        AudioManager audioManager=getSystemService(AudioManager.class);
        if(audioManager==null) return true; // conservador: sin estado confiable, no intervenir
        int mode=audioManager.getMode();
        return mode==AudioManager.MODE_IN_CALL ||
               mode==AudioManager.MODE_IN_COMMUNICATION;
    }
    private void runBridge() {
        String key=SecretStore.load(this);
        if(key==null || CommandReceiptStore.isPaused(this))return;
        try {
            retryPendingAck(key);
            if (CommandReceiptStore.getPending(this) != null || verifyingForeground) return;
            long now=System.currentTimeMillis();
            if(now-lastRegistered>8*60_000L){
                JSONArray capabilities=new JSONArray();
                capabilities.put("notify");capabilities.put("open_app");capabilities.put("open_url");
                JSONObject registration=new JSONObject()
                    .put("action","register").put("version",1).put("appVersion","0.3.12")
                    .put("capabilities",capabilities);
                JSONObject registered=BridgeHttp.call("/_api/kairos/phone_executor","POST",registration,key);
                if (!registered.optBoolean("ok",false)) throw new IllegalStateException("Registro no confirmado");
                lastRegistered=now;
            }
            // El sondeo puede reservar una orden en el servidor. Nunca reservarla
            // durante una llamada/clase por voz: podria expirar antes del ACK.
            if(hasActiveCommunication()) return;
            JSONObject pending=BridgeHttp.call("/_api/kairos/phone_command_poll","GET",null,key);
            if(!pending.optBoolean("shouldExecute",false))return;
            JSONObject command=pending.optJSONObject("command");
            if(command==null)return;
            String commandId=command.optString("id","");
            if(!commandId.matches("[0-9a-fA-F-]{36}"))return;
            // Antes del ACK, posponer CUALQUIER acción externa durante
            // comunicación activa; Android la procesará en un próximo sondeo.
            if(hasActiveCommunication()){
                CommandReceiptStore.mark(this,"Orden pospuesta hasta terminar la comunicación");
                return;
            }
            JSONObject ack=new JSONObject().put("commandId",commandId).put("result","received");
            JSONObject received=BridgeHttp.call("/_api/kairos/phone_command_ack","POST",ack,key);
            if (!received.optBoolean("ok",false)) throw new IllegalStateException("Recepción no confirmada");
            CommandReceiptStore.mark(this, "Orden " + command.optString("type") + " recibida; ejecutando");
            handler.post(()->{
                try {
                    if("local_test".equals(command.optString("type",""))) {
                        startRemoteOwnAppTest(key,commandId,command);
                        return;
                    }
                    String result=executeCommand(command);
                    if("open_app".equals(command.optString("type",""))) {
                        JSONObject body=command.optJSONObject("payload");
                        String expected=body==null?"":body.optString("package","");
                        if(!ForegroundProofPolicy.isAllowedExpected(expected)) {
                            storeAndConfirm(key,commandId,"failed","APP_FOREGROUND_POLICY_DENIED");
                            return;
                        }
                        verifyingForeground=true;
                        verifyChromeForeground(key,commandId,expected,0);
                        return;
                    }
                    storeAndConfirm(key,commandId,"completed",result);
                } catch(Exception e) {
                    String reason;
                    if(e instanceof IllegalStateException &&
                       "Notificaciones deshabilitadas en Android".equals(e.getMessage()))
                        reason="NOTIFICATIONS_DISABLED: habilitar permiso de avisos en Android";
                    else if(e instanceof IllegalStateException &&
                        "Aviso suspendido durante comunicación activa".equals(e.getMessage()))
                        reason="CALL_ACTIVE: aviso no presentado durante comunicación";
                    else reason="Acción no ejecutada: "+e.getClass().getSimpleName();
                    storeAndConfirm(key,commandId,"failed",reason);
                }
            });
        }catch(Exception e) {
            // No confundir servicio Android encendido con puente remoto conectado.
            // Mensaje local sin URL, credenciales ni datos privados.
            CommandReceiptStore.mark(this,
                "CONTROL 360 sin conexión comprobada: " + e.getClass().getSimpleName());
        }
    }
    /** Confirma únicamente que el paquete de Chrome está visible.
     * Jamás lee texto, contraseñas, formularios ni contenido de otras apps. */
    private void verifyChromeForeground(String key,String commandId,String expected,int attempt) {
        handler.postDelayed(()->{
            if(!active || !verifyingForeground) return;
            String visible="";
            try {
                AccessibilityNodeInfo root=getRootInActiveWindow();
                if(root!=null && root.getPackageName()!=null)
                    visible=String.valueOf(root.getPackageName());
            }catch(RuntimeException ignored) {
                // No reclamar éxito si Android niega acceso a la ventana.
            }
            if(ForegroundProofPolicy.matches(expected,visible)) {
                verifyingForeground=false;
                storeAndConfirm(key,commandId,"completed",
                    "CHROME_FOREGROUND_CONFIRMED: paquete Chrome visible por Accesibilidad");
                return;
            }
            if(attempt<8) {
                verifyChromeForeground(key,commandId,expected,attempt+1);
            } else {
                verifyingForeground=false;
                storeAndConfirm(key,commandId,"failed",
                    "CHROME_FOREGROUND_NOT_CONFIRMED: ventana no verificada");
            }
        },attempt==0?950L:650L);
    }
    /** Guarda un recibo duradero ANTES de intentar enviarlo por la red. */
    private void storeAndConfirm(String key,String commandId,String result,String detail) {
        String limited=detail==null?"":detail.substring(0,Math.min(detail.length(),280));
        boolean stored=CommandReceiptStore.save(this,commandId,result,limited);
        CommandReceiptStore.mark(this,stored
           ? "Resultado local guardado; confirmando con CONTROL 360"
           : "No se pudo guardar el resultado; confirmando con CONTROL 360");
        try {
            io.execute(()->{
                if(stored) {
                    retryPendingAck(key);
                    return;
                }
                try {
                    JSONObject finished=new JSONObject().put("commandId",commandId)
                        .put("result",result).put("message",limited);
                    JSONObject response=BridgeHttp.call(
                        "/_api/kairos/phone_command_ack","POST",finished,key);
                    if(!response.optBoolean("ok",false))
                        throw new IllegalStateException("Acuse no confirmado");
                    CommandReceiptStore.mark(this,"Resultado confirmado por CONTROL 360");
                }catch(Exception ignored) {
                    CommandReceiptStore.mark(this,"Confirmación remota pendiente");
                }
            });
        }catch(RejectedExecutionException ignored) {
            CommandReceiptStore.mark(this,"Conexión interrumpida; resultado pendiente");
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
            // No afirmar entrega cuando Android tiene los avisos deshabilitados.
            NotificationManager notificationManager=getSystemService(NotificationManager.class);
            if (notificationManager == null || !notificationManager.areNotificationsEnabled())
                throw new IllegalStateException("Notificaciones deshabilitadas en Android");
            android.media.AudioManager audioManager=getSystemService(android.media.AudioManager.class);
            if (audioManager != null &&
                (audioManager.getMode() == android.media.AudioManager.MODE_IN_CALL ||
                 audioManager.getMode() == android.media.AudioManager.MODE_IN_COMMUNICATION))
                throw new IllegalStateException("Aviso suspendido durante comunicación activa");
            String message=payload.optString("message","");
            if(message.length()<3 || message.length()>280)throw new SecurityException("Texto no permitido");
            Notification n=new Notification.Builder(this,ALERT_CHANNEL)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("KAIRÓS 360 · Aviso")
                .setContentText(message)
                .setStyle(new Notification.BigTextStyle().bigText(message))
                .setAutoCancel(true).build();
            notificationManager.notify((int)(System.currentTimeMillis()%20000)+202,n);
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
        if(type.equals("local_test")){
            String action=payload.optString("action","");
            if("click".equals(action)){
                if(!clickOwnRemoteTarget())throw new IllegalStateException("Botón KAIRÓS no visible");
                return "LOCAL_CLICK_REQUESTED_NOT_YET_PROVED";
            }
            if("write".equals(action)){
                if(!fillOwnTestField())throw new IllegalStateException("Campo KAIRÓS no visible");
                return "LOCAL_WRITE_REQUESTED_NOT_YET_PROVED";
            }
            if("back".equals(action)){
                if(!backFromOwnTestScreen())throw new IllegalStateException("Pantalla de prueba KAIRÓS no visible");
                return "LOCAL_BACK_REQUESTED_NOT_YET_PROVED";
            }
            throw new SecurityException("Prueba local no autorizada");
        }
        throw new SecurityException("Comando no autorizado");
    }
    @Override public void onAccessibilityEvent(AccessibilityEvent event) { /* No lee la pantalla. */ }
    @Override public void onInterrupt() {}
    @Override public boolean onUnbind(Intent intent) {
        active=false;stopWatchingConnectivity();connectedService.clear();handler.removeCallbacks(tick);io.shutdownNow();
        return super.onUnbind(intent);
    }
    @Override public void onDestroy() {
        active=false;stopWatchingConnectivity();connectedService.clear();handler.removeCallbacks(tick);io.shutdownNow();
        super.onDestroy();
    }
}
