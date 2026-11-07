package com.sjm.kairos.mobile;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
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
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Pantalla de vinculación mínima: ninguna credencial se pide por ChatGPT. */
public class MainActivity extends Activity {
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private TextView status;
    private EditText codeField;
    private Button linkButton;

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
        status = text("Comprobando...",17); layout.addView(status);
        layout.addView(text("1. Abra CONTROL 360 → Mentor → KAIRÓS 03 y pulse «Generar código».",17));
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
        layout.addView(button("3. Activar KAIRÓS en Accesibilidad",v -> {
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));
        }));
        layout.addView(text("Dentro de Accesibilidad, busque KAIRÓS Móvil y actívelo. Es el único permiso imprescindible para recibir órdenes y solicitar apertura de aplicaciones.",15));
        layout.addView(text("Las órdenes remotas están limitadas a avisos, Chrome, Gmail, MacroDroid y el sitio SJM. No se lee la pantalla ni se pulsan botones automáticamente en esta primera versión.",14));
        setContentView(scroll);
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},210);
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
                });
            } catch(Exception e) {
                runOnUiThread(() -> {status.setText("Sin vincular: "+e.getMessage());linkButton.setEnabled(true);});
            }
        });
    }
    @Override protected void onResume() {
        super.onResume();
        if(status!=null && SecretStore.load(this)!=null) {
            status.setText("Clave de vinculación guardada en este teléfono. Si ya activó KAIRÓS Móvil en Accesibilidad, el servicio comprobará el enlace.");
        }
    }
    @Override protected void onDestroy() {io.shutdownNow();super.onDestroy();}
}
