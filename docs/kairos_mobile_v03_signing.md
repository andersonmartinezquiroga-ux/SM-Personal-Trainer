# KAIRÓS Móvil V0.3 · Firma permanente y migración segura

Estado de desarrollo: flujo de compilación GitHub Actions enlazado a un servicio Render gratuito. La llave privada de firma se almacena en el entorno protegido de Render, no en este repositorio.

Certificado público previsto: ECDSA P-256 (alias interno: `kairos_release_2026`), SHA-256 `31:70:DE:F7:7F:C7:1B:05:60:B8:7B:B9:BF:C1:2E:AA:62:05:83:C6:34:07:11:95:C3:F7:12:CD:1C:87:77:38`. Verificar siempre que el APK firmado coincida con este valor antes de distribuir.

Control de acceso a la llave: GitHub OpenID Connect con verificación criptográfica de la firma RS256/JWKS, audiencia fija `sjm-kairos-signing-v1`, repositorio propietario, ID del repositorio, rama y workflow exactos. No copiar la clave a GitHub Secrets ni incluirla en el código o en los logs.

V0.1 y V0.2 fueron firmadas con certificados de depuración efímeros de los runners. Android **no permite instalar V0.3 como actualización directa** sobre V0.1. Se requerirá una única migración supervisada: antes de la nueva instalación preservar evidencia de vinculación, desinstalar V0.1, instalar V0.3, vincular mediante código temporal, reactivar Accesibilidad y verificar notificación/abrir una app. Conservar MacroDroid V0.1 operativo durante la migración; no modificarlo. No desinstalar por el usuario sin indicaciones explícitas y una prueba aprobada del APK.

La V0.3 inicial conserva las funciones seguras de V0.2: notificaciones, apertura de apps permitidas, páginas oficiales SJM, reintento de confirmación y pausa local. **No** habilita automáticamente gestos, clics, navegación libre, lecturas de Gmail, pagos ni envío de formularios.

Aviso de continuidad: si el certificado privado de Render se pierde, Android no permitirá futuras actualizaciones firmadas por otra clave. Guardar una copia cifrada en un almacén privado del propietario cuando esté disponible (nunca en repositorio público).
