package com.sjm.kairosbridge;

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

final class SecureKey {
    private static final String ALIAS = "sjm-kairos-executor-bridge";
    private SecureKey() {}

    private static SecretKey key() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
        ks.load(null);
        if (ks.containsAlias(ALIAS)) return (SecretKey) ks.getKey(ALIAS, null);
        KeyGenerator gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        gen.init(new KeyGenParameterSpec.Builder(ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build());
        return gen.generateKey();
    }

    static void save(Context ctx, String value) throws Exception {
        if (!value.matches("[a-f0-9]{64}")) throw new IllegalArgumentException("Credencial no válida");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key());
        byte[] data = cipher.doFinal(value.getBytes(StandardCharsets.UTF_8));
        SharedPreferences.Editor edit = ctx.getSharedPreferences("bridge", Context.MODE_PRIVATE).edit();
        edit.putString("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP));
        edit.putString("cipher", Base64.encodeToString(data, Base64.NO_WRAP));
        if (!edit.commit()) throw new IllegalStateException("No se guardó la vinculación");
    }

    static String read(Context ctx) throws Exception {
        SharedPreferences pref = ctx.getSharedPreferences("bridge", Context.MODE_PRIVATE);
        String iv = pref.getString("iv", null);
        String data = pref.getString("cipher", null);
        if (iv == null || data == null) return null;
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key(),
                new GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)));
        return new String(cipher.doFinal(Base64.decode(data, Base64.NO_WRAP)),
                StandardCharsets.UTF_8);
    }
}
