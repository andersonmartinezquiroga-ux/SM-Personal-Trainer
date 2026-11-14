# KAIRÓS 0.3.15 — consistencia de versión reportada

**Incidencia de producción 13-nov-2026 21:43–21:50 COT:** app visual y registro manual HTTPS en Motorola 0.3.14; al reactivar Accesibilidad, `KairosAccessibility.runBridge()` enviaba periódicamente `appVersion: "0.3.13"`, sobrescribiendo el número en Supabase aunque APK real seguía en 0.3.14. Esto NO fue una reinstalación/downgrade.

**Corrección:** `MainActivity.verifyBridgeNow()` y `KairosAccessibility.runBridge()` reportan `getPackageManager().getPackageInfo(getPackageName(),0).versionName` (metadato confiable del APK instalado), sin valores numéricos incrustados. `versionCode=18`, `versionName=0.3.15`. Seguridad y permisos sin ampliar; sin enviar notificaciones ni órdenes de prueba al compilar.

**Prueba CI añadida:** valida versión 0.3.15 en Gradle y pantalla y que ambos componentes obtengan `appVersion` del PackageManager en vez de una constante literal. El flujo habitual agrega compilación real firmada, APK Signature Scheme v2 y certificado permanente.

**Estado real que no debe confundirse:** el usuario ya confirmó físicamente servicio Accesibilidad activo, consulta `POLL_EMPTY` periódica y aviso visual de recuperación del servidor a las 21:45; el job de recuperación d9b3b18c recibió ACK completado. Otro job e29c81fb venció SIN ejecución. El aviso no probó sonido especial. No declarar autonomía general.

**Instalación futura:** no forzar mientras batería baja. Después del build/release y cuando el usuario esté disponible y con carga, actualizar encima sin desinstalar ni revincular. Verificar versión visual y backend persistente durante al menos dos intervalos de sondeo, no confundir latido con ejecución de orden.
