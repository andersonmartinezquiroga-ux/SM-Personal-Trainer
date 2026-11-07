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
        layout.addView(text("Ejecutor privado para el Motorola. No modifica su MacroDroid ni permite pagos, mensajes o formularios.",16));
        status = text("Comprobando enlace local...",17); layout.addView(status);
        localProof = text("Última actividad: aún no comprobada",15);
        layout.addView(localProof);
        layout.addView(text("1. Abra CONTROL 360 → Mentor → KAIRÓS 03 y pulse «Generar código».",17));
        layout.addView(button("ABRIR CONTROL 360 PARA GENERAR CÓDIGO",v -> openTrustedPage("https://sjm-control-360.floot.app")));
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
        layout.addView(button("COMPROBAR CONEXIÓN REAL con CONTROL 360", v -> verifyBridgeNow()));
        layout.addView(button("Ver último resultado de KAIRÓS", v -> refreshLocalState()));
        layout.addView(button("Pausar / reanudar órdenes remotas", v -> {
            boolean paused = !CommandReceiptStore.isPaused(this);
            CommandReceiptStore.setPaused(this, paused);
            refreshLocalState();
        }));
        layout.addView(button("3. Activar KAIRÓS en Accesibilidad",v -> {
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));
        }));
        layout.addView(text("Dentro de Accesibilidad, busque KAIRÓS Móvil y actívelo. Es el único permiso imprescindible para recibir órdenes y solicitar apertura de aplicaciones.",15));
        layout.addView(text("Las órdenes remotas están limitadas a avisos, Chrome, Gmail, MacroDroid y el sitio SJM. No se lee la pantalla ni se pulsan botones automáticamente en esta primera versión.",14));
        setContentView(scroll);
        refreshLocalState();
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},210);
        }
    }
    /** Solo enlaces HTTPS fijos y controlados; no recibe URL del servidor. */
    private void openTrustedPage(String url) {
        if (!url.equals("https://sjm-control-360.floot.app")
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
    /** Prueba de red auténtica y sin órdenes: no simula respuesta del servidor. */
    private void verifyBridgeNow() {
        String key=SecretStore.load(this);
        if(key==null){
            status.setText("NO VINCULADO. Primero genere un código y vincule el Motorola.");
            return;
        }
        linkButton.setEnabled(false);
        status.setText("Conectando con CONTROL 360 por HTTPS...");
        io.execute(() -> {
            try {
                JSONArray scopes=new JSONArray().put("notify").put("open_app").put("open_url");
                JSONObject request=new JSONObject().put("action","register")
                    .put("version",1).put("capabilities",scopes);
                JSONObject reply=BridgeHttp.call("/_api/kairos/phone_executor","POST",request,key);
                if(!reply.optBoolean("ok",false))
                    throw new IllegalStateException("El servidor respondió sin confirmar la vinculación");
                CommandReceiptStore.mark(this,
                    "CONEXIÓN REAL: CONTROL 360 confirmó el registro remoto");
                runOnUiThread(() -> {
                    linkButton.setEnabled(true);
                    refreshLocalState();
                    status.setText("PUENTE CONECTADO: registro confirmado por el servidor.");
                });
            } catch(Exception e) {
                String error=e.getClass().getSimpleName();
                CommandReceiptStore.mark(this,
                    "SIN CONEXIÓN REAL con CONTROL 360: "+error);
                runOnUiThread(() -> {
                    linkButton.setEnabled(true);
                    refreshLocalState();
                    status.setText("NO CONECTADO: revise internet, código y servicio. "+error);
                });
            }
        });
    }
    private void refreshLocalState() {
        if (status == null || localProof == null) return;
        boolean linked = SecretStore.load(this) != null;
        status.setText(linked
            ? "CREDENCIAL LOCAL GUARDADA. Compruebe el último resultado para verificar la conexión real. Mantenga activo el servicio de Accesibilidad."
            : "SIN VINCULAR. Genere un código temporal en CONTROL 360.");
        localProof.setText((CommandReceiptStore.isPaused(this) ? "PAUSADO por usted. No se reciben nuevas órdenes.\n" : "Órdenes remotas habilitadas.\n") + "Último resultado local: " + CommandReceiptStore.status(this) +
            (CommandReceiptStore.getPending(this) != null
                ? "\nConfirmación de resultado pendiente de envío al servidor."
                : ""));
    }
    @Override protected void onResume() {
        super.onResume();
        refreshLocalState();
    }
    @Override protected void onDestroy() {io.shutdownNow();super.onDestroy();}
}
