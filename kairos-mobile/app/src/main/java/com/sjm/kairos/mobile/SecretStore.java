package com.sjm.kairos.mobile;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Credencial cifrada dentro del Android Keystore; nunca incluida en el APK. */
final class SecretStore {
    private static final String ALIAS = "SJM_KAIROS_EXECUTOR_V1";
    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences("kairos_private", Context.MODE_PRIVATE);
    }
    private static SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        SecretKey found = (SecretKey) store.getKey(ALIAS, null);
        if (found != null) return found;
        KeyGenerator gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        gen.init(new KeyGenParameterSpec.Builder(ALIAS,
            KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256).build());
        return gen.generateKey();
    }
    static void save(Context ctx, String token) throws Exception {
        if (token == null || !token.matches("[0-9a-f]{64}"))
            throw new SecurityException("Clave del servidor inválida");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key());
        byte[] ct = cipher.doFinal(token.getBytes(StandardCharsets.UTF_8));
        String data = Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP) + "." +
            Base64.encodeToString(ct, Base64.NO_WRAP);
        prefs(ctx).edit().putString("key", data).apply();
    }
    static String load(Context ctx) {
        String text = prefs(ctx).getString("key", "");
        if (text.isEmpty()) return null;
        try {
            String[] parts = text.split("\\.");
            if (parts.length != 2) return null;
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, key(),
                new GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)));
            return new String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)),
                StandardCharsets.UTF_8);
        } catch (Exception e) { return null; }
    }
    static void clear(Context ctx) { prefs(ctx).edit().clear().apply(); }
}
