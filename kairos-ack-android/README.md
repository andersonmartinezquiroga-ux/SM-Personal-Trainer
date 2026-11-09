# KAIRÓS Android ACK Bridge — prototipo alternativo

**Alcance:** app **separada**, de prueba, que no reemplaza el cliente KAIRÓS 0.3.12 ni el SM Personal Trainer. El código está en rama de revisión, no desplegado. Usa la función Supabase existente `sjm_kairos_phone_v1` y el contrato de servidor `phone_command_poll` / `phone_command_ack`.

## Seguridad y secuencia

1. El propietario solicita un código temporal por el flujo oficial; la app ejecuta `executor_claim`. No se registra ninguna clave fija, email ni credencial de administración en Git.
2. El token del ejecutor se cifra mediante Android Keystore (AES-GCM); no se muestra ni registra en logs.
3. El usuario pulsa **Activar recepción** y concede permiso de notificaciones. Solo entonces se inicia un servicio de primer plano.
4. Cada 10 s, mientras Android permita mantener el servicio, consulta la cola de ese dispositivo.
5. Para `notify`, llama a `phone_command_ack` con `received` y **solo si el servidor lo acepta** invoca NotificationManager. Inmediatamente envía `completed` o `failed`. No admite otros comandos.
6. Los comandos cerrados, vencidos, no autorizados o desconocidos no se ejecutan; no se duplican.
7. `completed` acredita que Android aceptó la llamada para publicar la notificación; **no acredita sonido visible ni que el usuario la oyó**. Requiere prueba física en Motorola.

## Restricciones honestas

- Este proyecto es un bypass de receptor opcional: crea otro dispositivo lógico con una vinculación nueva; no repara el código instalado de KAIRÓS 0.3.12 ni reutiliza su token.
- Un servicio `dataSync` tiene límites del sistema en Android 15. **No asegura operación 24/7**; solo sirve para una prueba real supervisada.
- Android puede silenciar notificaciones por permisos, canal, No molestar o restricciones del fabricante.
- La versión disponible aquí **no está probada en el teléfono**; solo marcarse como instalada cuando exista APK compilado y prueba real.
- No publicar claves de vinculación ni tokens en capturas o informes.

## Compilación sin Floot

`./gradlew -p kairos-ack-android :app:assembleDebug`

CI independiente: `.github/workflows/kairos-ack-android.yml`. Al obtener un build verde, descargar el artifact `KAIRÓS-ACK-Bridge-debug` de GitHub Actions, extraer APK, instalar en Motorola (permiso de instalación fuera de Play Store si necesario) y vincular mediante código oficial. No instalar reemplazando la app actual: tiene otro ID de paquete.
