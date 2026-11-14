package com.sjm.kairos.mobile;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.InputFilter;
import android.text.InputType;
import android.graphics.Color;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONObject;
import org.json.JSONArray;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Pantalla de vinculación mínima: ninguna credencial se pide por ChatGPT. */
public class MainActivity extends Activity {
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private TextView status;
    private EditText codeField;
    private Button linkButton;
    private TextView localProof;
    private TextView bridgeFeedback;
    private TextView lastResultFeedback;
    private Button bridgeButton;

    private TextView text(String value, int size) {
        TextView t = new TextView(this);
        t.setText(value); t.setTextColor(Color.rgb(230,238,246)); t.setTextSize(size);
        t.setPadding(4, 12, 4, 12);
        return t;
    }
    private Button button(String label, View.OnClickListener callback) {
        Button b = new Button(this); b.setText(label); b.setTextSize(16); b.setOnClickListener(callback);
        b.setAllCaps(false); return b;
    }
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(13,22,32));
        getWindow().setNavigationBarColor(Color.rgb(13,22,32));
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(15,25,36));
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(24,38,24,24);
        scroll.addView(layout);
        layout.addView(text("KAIRÓS MÓVIL · SJM CONTROL 360",23));
        layout.addView(text("VERSIÓN 0.3.14 · RESULTADOS VISIBLES",17));
        TextView immediateTapStatus=text("PRUEBA DE BOTÓN: aún no iniciada.",18);
        layout.addView(immediateTapStatus);
        layout.addView(text("Ejecutor privado para el Motorola. No modifica su MacroDroid ni permite pagos, mensajes o formularios.",16));
        status = text("Comprobando enlace local...",17); layout.addView(status);
        localProof = text("Última actividad: aún no comprobada",15);
        layout.addView(localProof);
        layout.addView(text("1. Revise su correo SJM para obtener el código privado de vinculación 0.3.6. No lo comparta en el chat.",17));
        layout.addView(button("ABRIR GMAIL PARA VER EL CÓDIGO",v -> openTrustedPage("https://mail.google.com")));
        layout.addView(button("🎙️ HABLAR CON EL CEREBRO KAIRÓS", v -> openTrustedPage("https://sjm-kairos-cerebro-web.vercel.app")));
        codeField = new EditText(this);
        codeField.setSingleLine(true);
        codeField.setTextColor(Color.WHITE);
        codeField.setHintTextColor(Color.rgb(160,177,191));
        codeField.setHint("Código temporal (10 caracteres)");
        codeField.setTextSize(20);
        codeField.setFilters(new InputFilter[]{new InputFilter.LengthFilter(11)});
        codeField.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);
        layout.addView(codeField);
        linkButton = button("2. Vincular este Motorola",v -> pair());
        layout.addView(linkButton);
        bridgeButton = button("COMPROBAR CONEXIÓN REAL con CONTROL 360", v -> verifyBridgeNow());
        layout.addView(bridgeButton);
        bridgeFeedback = text("ESTADO DEL PUENTE: toque COMPROBAR para ver el resultado AQUÍ.",17);
        layout.addView(bridgeFeedback);
        layout.addView(button("Ver último resultado de KAIRÓS", v -> showLastResultNearButton()));
        lastResultFeedback = text("Aquí aparecerá el último resultado justo debajo del botón. No envía órdenes nuevas.",17);
        layout.addView(lastResultFeedback);
        layout.addView(text("PRUEBA REAL · Pulsación de un botón propio",19));
        layout.addView(text("La prueba verifica Accesibilidad sin entrar en Gmail, bancos ni otras aplicaciones. Primero active KAIRÓS en Accesibilidad.",14));
        TextView tapFeedback = text("Prueba de pulsación pendiente",17);
        final boolean[] testArmed = {false};
        Button tapTarget = button("● DESTINO DE PRUEBA (NO PULSAR MANUALMENTE)",v -> {
            boolean remoteProof=LocalInteractionPolicy.consumeRemoteClick();
            if (testArmed[0]||remoteProof) {
                testArmed[0]=false;
                String success="PULSACIÓN REAL RECIBIDA: el servicio de KAIRÓS pulsó el destino.";
                immediateTapStatus.setText(success);
                tapFeedback.setText(success);
                Toast.makeText(this,"KAIRÓS PULSÓ EL BOTÓN DE PRUEBA",Toast.LENGTH_LONG).show();
                CommandReceiptStore.mark(this,
                    remoteProof
                     ? "PRUEBA REMOTA KAIRÓS: clic propio entregado al botón"
                     : "PRUEBA LOCAL DE ACCESIBILIDAD: pulsación recibida en botón KAIRÓS");
            } else {
                String manual="Pulsación manual detectada. No cuenta como prueba autónoma.";
                immediateTapStatus.setText(manual);
                tapFeedback.setText(manual);
                Toast.makeText(this,manual,Toast.LENGTH_LONG).show();
            }
        });
        tapTarget.setId(R.id.kairos_test_target);
        layout.addView(tapTarget);
        layout.addView(tapFeedback); // Mensaje justo al lado de los controles.
        Button requestTap = button("4. PEDIR A KAIRÓS QUE PULSE EL BOTÓN",v -> {
            String started="BOTÓN DETECTADO: comprobando Accesibilidad...";
            immediateTapStatus.setText(started);
            tapFeedback.setText(started);
            ((Button)v).setText("COMPROBANDO PULSACIÓN...");
            Toast.makeText(this,started,Toast.LENGTH_LONG).show();
            testArmed[0]=true;
            try {
                boolean requested=KairosAccessibility.clickOwnTestTarget();
                if(!requested) {
                    testArmed[0]=false;
                    String problem="SIN PULSACIÓN: KAIRÓS no pudo acceder al botón. Verifique que el servicio esté activo en Accesibilidad.";
                    immediateTapStatus.setText(problem);
                    tapFeedback.setText(problem);
                    Toast.makeText(this,problem,Toast.LENGTH_LONG).show();
                    ((Button)v).setText("VOLVER A PROBAR PULSACIÓN");
                } else {
                    ((Button)v).setText("PULSACIÓN SOLICITADA A ANDROID");
                    new Handler(Looper.getMainLooper()).postDelayed(()->{
                        if(testArmed[0]) {
                            testArmed[0]=false;
                            String pending="PULSACIÓN SIN CONFIRMACIÓN DEL BOTÓN. No se declara éxito.";
                            immediateTapStatus.setText(pending);
                            tapFeedback.setText(pending);
                            ((Button)v).setText("VOLVER A PROBAR PULSACIÓN");
                        }
                    },2000L);
                }
            } catch(Exception ex) {
                testArmed[0]=false;
                String error="ERROR LOCAL DE PULSACIÓN: "+ex.getClass().getSimpleName();
                immediateTapStatus.setText(error);
                tapFeedback.setText(error);
                Toast.makeText(this,error,Toast.LENGTH_LONG).show();
                ((Button)v).setText("VOLVER A PROBAR PULSACIÓN");
            }
        });
        layout.addView(requestTap);
        layout.addView(text("PRUEBA REAL · Escritura solo en KAIRÓS",19));
        layout.addView(text("Se escribe una frase fija de ensayo solo en este campo. No lee ni modifica Gmail, claves o formularios de otras apps.",14));
        EditText ownTest = new EditText(this);
        ownTest.setId(R.id.kairos_text_test_target);
        ownTest.setSingleLine(true);
        ownTest.setTextColor(Color.WHITE);
        ownTest.setHintTextColor(Color.rgb(160,177,191));
        ownTest.setHint("Campo de prueba propio");
        ownTest.setInputType(InputType.TYPE_CLASS_TEXT);
        ownTest.setFilters(new InputFilter[]{new InputFilter.LengthFilter(40)});
        layout.addView(ownTest);
        TextView typingProof = text("Escritura no probada",17);
        layout.addView(typingProof);
        layout.addView(button("5. PEDIR ESCRITURA A KAIRÓS EN ESTE CAMPO", v -> {
            ownTest.setText("");
            typingProof.setText("Solicitando escritura a Accesibilidad...");
            boolean requested=KairosAccessibility.fillOwnTestField();
            new Handler(Looper.getMainLooper()).postDelayed(()->{
                boolean confirmed=requested && LocalInteractionPolicy.PROOF_TEXT.equals(
                    ownTest.getText().toString());
                String result=confirmed
                    ? "ESCRITURA LOCAL CONFIRMADA EN EL CAMPO PROPIO."
                    : "ESCRITURA NO CONFIRMADA: no se declara éxito.";
                typingProof.setText(result);
                CommandReceiptStore.mark(this,result);
            },450L);
        }));
        layout.addView(text("PRUEBA REAL · Regreso desde pantalla propia",19));
        layout.addView(text("Se abre otra pantalla dentro de KAIRÓS y allí se pide a Accesibilidad regresar. No controla aplicaciones externas.",14));
        layout.addView(button("6. ABRIR PANTALLA INTERNA DE REGRESO",
            v -> startActivity(new Intent(this,SafeBackTestActivity.class))));

        layout.addView(button("Pausar / reanudar órdenes remotas", v -> {
            boolean paused = !CommandReceiptStore.isPaused(this);
            CommandReceiptStore.setPaused(this, paused);
            refreshLocalState();
        }));
        layout.addView(button("3. Activar KAIRÓS en Accesibilidad",v -> {
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));
        }));
        layout.addView(text("Dentro de Accesibilidad, busque KAIRÓS Móvil y actívelo. Es el único permiso imprescindible para recibir órdenes y solicitar apertura de aplicaciones.",15));
        layout.addView(text("Esta fase de respaldo remoto permite avisos de prueba; otras órdenes se habilitarán únicamente tras verificación. La única pulsación permitida en esta versión es una prueba voluntaria sobre un botón de KAIRÓS; no se leen pantallas de otras apps.",14));
        setContentView(scroll);
        refreshLocalState();
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},210);
        }
    }
    /** Solo enlaces HTTPS fijos y controlados; no recibe URL del servidor. */
    private void openTrustedPage(String url) {
        if (!url.equals("https://mail.google.com")
                && !url.equals("https://sjm-control-360.floot.app")
                && !url.equals("https://sjm-kairos-cerebro-web.vercel.app")) {
            status.setText("Enlace no autorizado.");
            return;
        }
        try {
            Intent open=new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            startActivity(open);
        } catch (Exception e) {
            status.setText("No se encontró navegador. Instale o habilite Chrome.");
        }
    }
    private void pair() {
        String code = codeField.getText().toString().replace("-", "").trim().toUpperCase();
        if (!code.matches("[0-9A-F]{10}")) {
            status.setText("Revise el código: son 10 caracteres, letras A-F y números.");
            return;
        }
        linkButton.setEnabled(false); status.setText("Vinculando de manera segura...");
        io.execute(() -> {
            try {
                JSONObject request = new JSONObject().put("code",code);
                JSONObject reply = BridgeHttp.call("/_api/kairos/executor_claim","POST",request,null);
                String key = reply.getString("executorKey");
                SecretStore.save(this,key);
                runOnUiThread(() -> {
                    codeField.setText("");
                    status.setText("VINCULADO. Active KAIRÓS Móvil en Ajustes → Accesibilidad. El servicio validará automáticamente la conexión.");
                    linkButton.setEnabled(true);
                    refreshLocalState();
                    verifyBridgeNow();
                });
            } catch(Exception e) {
                runOnUiThread(() -> {status.setText("Sin vincular: "+e.getMessage());linkButton.setEnabled(true);});
            }
        });
    }
    /** Todo estado se muestra al lado del botón y en un Toast de Android. */
    private void showBridgeMessage(String message) {
        status.setText(message);
        if (bridgeFeedback != null) bridgeFeedback.setText(message);
        Toast.makeText(this,message,Toast.LENGTH_LONG).show();
    }
    /** Prueba de red auténtica: un registro confirmado NO significa control de apps. */
    private void verifyBridgeNow() {
        String key=SecretStore.load(this);
        if(key==null) {
            showBridgeMessage("SIN VINCULAR: primero obtenga el código temporal por su correo SJM y vincule este Motorola.");
            return;
        }
        bridgeButton.setEnabled(false);
        linkButton.setEnabled(false);
        showBridgeMessage("BOTÓN DETECTADO: verificando conexión HTTPS con CONTROL 360...");
        io.execute(() -> {
            try {
                JSONArray scopes=new JSONArray().put("notify").put("open_app").put("open_url");
                JSONObject request=new JSONObject().put("action","register")
                    .put("version",1).put("appVersion","0.3.14").put("capabilities",scopes);
                JSONObject reply=BridgeHttp.call("/_api/kairos/phone_executor","POST",request,key);
                if(!reply.optBoolean("ok",false))
                    throw new IllegalStateException("El servidor no confirmó la vinculación");
                CommandReceiptStore.mark(this,
                    "REGISTRO REMOTO: CONTROL 360 confirmó conexión HTTPS; ejecución móvil no probada");
                runOnUiThread(() -> {
                    if(isFinishing() || isDestroyed()) return;
                    bridgeButton.setEnabled(true);
                    linkButton.setEnabled(true);
                    refreshLocalState();
                    showBridgeMessage("PUENTE SUPABASE CONECTADO: el servidor confirmó registro HTTPS. Falta probar una orden remota.");
                });
            } catch(Exception e) {
                String error=e.getClass().getSimpleName();
                CommandReceiptStore.mark(this,"SIN CONEXIÓN REAL con CONTROL 360: "+error);
                runOnUiThread(() -> {
                    if(isFinishing() || isDestroyed()) return;
                    bridgeButton.setEnabled(true);
                    linkButton.setEnabled(true);
                    refreshLocalState();
                    showBridgeMessage("NO CONECTADO: "+error+". Verifique código, internet y servidor.");
                });
            }
        });
    }
    /** Presenta la evidencia visible al lado del botón sin repetir órdenes ni consultar datos privados. */
    private void showLastResultNearButton() {
        if (lastResultFeedback == null) return;
        refreshLocalState();
        String checkedAt = java.text.DateFormat
            .getTimeInstance(java.text.DateFormat.MEDIUM)
            .format(new java.util.Date());
        String message = LastResultText.compose(
            checkedAt,
            CommandReceiptStore.status(this),
            CommandReceiptStore.bridgeStatus(this),
            CommandReceiptStore.getPending(this) != null,
            CommandReceiptStore.isPaused(this)
        );
        lastResultFeedback.setText(message);
        lastResultFeedback.announceForAccessibility(message);
    }
    private void refreshLocalState() {
        if (status == null || localProof == null) return;
        boolean linked = SecretStore.load(this) != null;
        status.setText(linked
            ? "CREDENCIAL LOCAL GUARDADA. Compruebe el último resultado para verificar la conexión real. Mantenga activo el servicio de Accesibilidad."
            : "SIN VINCULAR. Use el código temporal de respaldo que llegará a su correo SJM.");
        localProof.setText((CommandReceiptStore.isPaused(this) ? "PAUSADO por usted. No se reciben nuevas órdenes.\n" : "Órdenes remotas habilitadas.\n") +
            "SONDEO/ACUSE: " + CommandReceiptStore.bridgeStatus(this) +
            "\nÚltimo resultado local: " + CommandReceiptStore.status(this) +
            (CommandReceiptStore.getPending(this) != null
                ? "\nConfirmación de resultado pendiente de envío al servidor."
                : "") +
            "\nPOLL_OFFERED no es ejecución; ACK_RECEIVED_ACCEPTED confirma recepción, pero no pantalla.");
    }
    @Override protected void onResume() {
        super.onResume();
        refreshLocalState();
    }
    @Override protected void onDestroy() {io.shutdownNow();super.onDestroy();}
}
