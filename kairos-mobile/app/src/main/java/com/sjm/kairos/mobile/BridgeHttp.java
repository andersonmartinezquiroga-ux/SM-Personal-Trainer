package com.sjm.kairos.mobile;

import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Enlaces exclusivamente HTTPS al servidor propio de SJM. */
final class BridgeHttp {
    private static final String BASE = "https://dfqjwlsgqetyxdrsuviy.supabase.co/functions/v1/sjm_kairos_phone_v1";
    static JSONObject call(String endpoint, String method, JSONObject body, String executorKey) throws Exception {
        if (!endpoint.startsWith("/_api/kairos/") || endpoint.contains(".."))
            throw new IOException("Endpoint no permitido");
        HttpURLConnection connection = (HttpURLConnection) new URL(BASE + "?path=" + java.net.URLEncoder.encode(endpoint, "UTF-8")).openConnection();
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(9000);
        connection.setReadTimeout(9000);
        connection.setRequestMethod(method);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Cache-Control", "no-store");
        if (executorKey != null && !executorKey.isEmpty()) {
            connection.setRequestProperty("x-kairos-executor-key", executorKey);
        }
        try {
            if (body != null) {
                byte[] data = body.toString().getBytes(StandardCharsets.UTF_8);
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json");
                try (OutputStream stream = connection.getOutputStream()) { stream.write(data); }
            }
            int status = connection.getResponseCode();
            if (status >= 300 && status < 400) throw new IOException("Redirección inesperada del servidor");
            InputStream in = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
            String text;
            if (in == null) text = "{}";
            else {
                try (InputStream stream = in; ByteArrayOutputStream buffer = new ByteArrayOutputStream()) {
                    byte[] block = new byte[1024]; int n; int total = 0;
                    while ((n = stream.read(block)) != -1) {
                        total += n;
                        if (total > 128000) throw new IOException("Respuesta demasiado grande");
                        buffer.write(block, 0, n);
                    }
                    text = buffer.toString("UTF-8");
                }
            }
            JSONObject response = new JSONObject(text);
            if (status < 200 || status >= 300)
                throw new IOException(response.optString("error", "Servidor respondió " + status));
            return response;
        } finally { connection.disconnect(); }
    }
}
