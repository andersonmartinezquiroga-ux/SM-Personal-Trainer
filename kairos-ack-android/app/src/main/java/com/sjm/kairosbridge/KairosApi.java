package com.sjm.kairosbridge;

import org.json.JSONObject;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

final class KairosApi {
    private static final String BASE = "https://dfqjwlsgqetyxdrsuviy.supabase.co/functions/v1/sjm_kairos_phone_v1";
    private KairosApi() {}

    static JSONObject call(String method, String route, JSONObject body, String executorKey) throws Exception {
        String endpoint = BASE + "?path=" + URLEncoder.encode(route, "UTF-8");
        HttpURLConnection c = (HttpURLConnection) new URL(endpoint).openConnection();
        c.setRequestMethod(method);
        c.setConnectTimeout(7000);
        c.setReadTimeout(7000);
        c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        if (executorKey != null && !executorKey.isEmpty()) {
            c.setRequestProperty("x-kairos-executor-key", executorKey);
        }
        try {
            if ("POST".equals(method)) {
                byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
                c.setDoOutput(true);
                c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                c.getOutputStream().write(bytes);
            }
            int status = c.getResponseCode();
            InputStream input = status >= 400 ? c.getErrorStream() : c.getInputStream();
            if (input == null) throw new IllegalStateException("Sin respuesta del servidor: " + status);
            try (InputStream stream = input; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096];
                int count;
                while ((count = stream.read(buffer)) != -1) {
                    output.write(buffer, 0, count);
                    if (output.size() > 16384) throw new IllegalStateException("Respuesta demasiado extensa");
                }
                JSONObject response = new JSONObject(output.toString(StandardCharsets.UTF_8.name()));
                if (status >= 400 && !response.optBoolean("ok")) {
                    throw new IllegalStateException("Servidor " + status + ": " + response.optString("error", "operación rechazada"));
                }
                return response;
            }
        } finally { c.disconnect(); }
    }

    static JSONObject ack(String key, String id, String result, String message) throws Exception {
        JSONObject body = new JSONObject();
        body.put("commandId", id);
        body.put("result", result);
        if (message != null) body.put("message", message);
        return call("POST", "/_api/kairos/phone_command_ack", body, key);
    }
}
