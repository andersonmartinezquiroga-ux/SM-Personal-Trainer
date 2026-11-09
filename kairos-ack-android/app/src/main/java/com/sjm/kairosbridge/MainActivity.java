package com.sjm.kairosbridge;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.text.InputFilter;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Locale;

public final class MainActivity extends Activity {
    private TextView state;
    private EditText pairingCode;
    private Button pairButton;
    private Button startButton;

    private void show(String message) { runOnUiThread(() -> state.setText(message)); }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        ScrollView scroll = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        int pad = (int)(24 * getResources().getDisplayMetrics().density);
        box.setPadding(pad, pad, pad, pad);
        box.setBackgroundColor(0xFF101115);
        scroll.addView(box);

        TextView title = new TextView(this);
        title.setText("KAIRÓS CONTROL 4.0 — ACUSE");
        title.setTextColor(0xFFE5C17B);
        title.setTextSize(23);
        title.setGravity(Gravity.CENTER);
        box.addView(title);

        TextView help = new TextView(this);
        help.setText("\nPuente alternativo de notificaciones. No sustituye la aplicación actual. Vincule con un código temporal autorizado y active la recepción. Una confirmación del servidor NO demuestra por sí sola que el teléfono sonó.");
        help.setTextColor(0xFFFFFFFF);
        help.setTextSize(15);
        box.addView(help);

        pairingCode = new EditText(this);
        pairingCode.setSingleLine(true);
        pairingCode.setHint("Código de vinculación (10 caracteres)");
        pairingCode.setHintTextColor(0xFFAAAAAA);
        pairingCode.setTextColor(0xFFFFFFFF);
        pairingCode.setFilters(new InputFilter[]{new InputFilter.LengthFilter(14)});
        box.addView(pairingCode);

        pairButton = new Button(this);
        pairButton.setText("Vincular dispositivo");
        box.addView(pairButton);

        startButton = new Button(this);
        startButton.setText("Activar recepción");
        box.addView(startButton);

        Button stopButton = new Button(this);
        stopButton.setText("Detener recepción");
        box.addView(stopButton);

        state = new TextView(this);
        state.setTextColor(0xFFFFFFFF);
        state.setTextSize(15);
        state.setPadding(0,pad,0,0);
        box.addView(state);
        setContentView(scroll);

        pairButton.setOnClickListener(v -> pair());
        startButton.setOnClickListener(v -> startBridge());
        stopButton.setOnClickListener(v -> {
            Intent intent = new Intent(this, BridgeService.class);
            intent.setAction(BridgeService.ACTION_STOP);
            startService(intent);
            show("Recepción detenida por el usuario.");
        });
        if (Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 100);
        }
        try { show(SecureKey.read(this) == null ?
                "Pendiente de vinculación." : "Vinculado: puede activar la recepción."); }
        catch (Exception ex) { show("Error al leer vinculación segura. Vincule nuevamente."); }
    }

    @Override protected void onResume() {
        super.onResume();
        if (state != null) {
            String last = getSharedPreferences("bridge", MODE_PRIVATE).getString("last_event", "");
            if (!last.isEmpty()) state.append("\nÚltimo evento: " + last);
        }
    }

    private void pair() {
        String code = pairingCode.getText().toString().replace("-", "").trim().toUpperCase(Locale.ROOT);
        if (!code.matches("[0-9A-F]{10}")) {
            show("Código inválido. Use 10 caracteres hexadecimales.");
            return;
        }
        pairButton.setEnabled(false);
        show("Vinculación segura en curso...");
        new Thread(() -> {
            try {
                JSONObject request = new JSONObject().put("code", code);
                JSONObject response = KairosApi.call("POST", "/_api/kairos/executor_claim", request, null);
                if (!response.optBoolean("ok")) throw new Exception("Código rechazado por el servidor.");
                String token = response.getString("executorKey");
                SecureKey.save(getApplicationContext(), token);
                JSONObject registration = new JSONObject()
                        .put("action", "register").put("version", 1)
                        .put("appVersion", "0.1.0")
                        .put("capabilities", new JSONArray().put("notify"));
                JSONObject registered = KairosApi.call("POST", "/_api/kairos/phone_executor", registration, token);
                if (!registered.optBoolean("ok")) throw new Exception("No se confirmó el registro.");
                show("Vinculación confirmada. Active la recepción en este Motorola.");
            } catch (Exception e) {
                show("No se completó la vinculación: " + e.getMessage());
            } finally {
                runOnUiThread(() -> pairButton.setEnabled(true));
            }
        }, "Kairos-pair").start();
    }

    private void startBridge() {
        try {
            if (SecureKey.read(this) == null) {
                show("Primero vincule el dispositivo con un código temporal.");
                return;
            }
            if (Build.VERSION.SDK_INT >= 33 &&
                    checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 101);
                show("Autorice las notificaciones y luego pulse Activar recepción.");
                return;
            }
            Intent i = new Intent(this, BridgeService.class);
            i.setAction(BridgeService.ACTION_START);
            startForegroundService(i);
            show("Activación solicitada. Compruebe la notificación permanente de KAIRÓS.");
        } catch (Exception ex) { show("No se inició recepción: " + ex.getMessage()); }
    }
}
