# SJM Control 360 — Mentor / puente seguro para panel móvil (V1)

**Estado real 19-oct-2026:** motor de órdenes por texto ejecuta acciones internas permitidas; consulta de recibos probada, interfaz móvil autenticada AÚN PENDIENTE. Desarrollo aislado en esta rama, no desplegado ni mezclado con la aplicación Android de entrenamiento.

## Componentes existentes y probados
- SQL: `sjm_ops.receive_mentor_text(text,request_key)`: sólo permite intenciones concretas (estado, proyectos, fuentes oficiales, revisión compuesta), bloquea frases desconocidas. Sin modelo generativo ni reconocimiento de audio.
- SQL: `sjm_ops.mentor_command_receipt_v1(request_key)`: lectura resumida de estado, autorización, fecha y digest, **sin instrucción completa, resultados crudos ni secretos**.
- Comando 17 `qa-natural-control-20261019-1`: pasó a completed con comprobante del motor Supabase.
- Control de privacidad: la función de recibos es SECURITY INVOKER y **NO** tiene permiso EXECUTE para `anon`, `authenticated` ni `service_role`. Esta es una decisión intencional mientras falte el puente de identidad.
- `sjm_qa.run_mentor_receipt_v1`: 10/10 controles reales de solo lectura; cron de regresión cada hora minuto 43. `sjm_qa.run_mentor_language_v2`: 26/26 comprobaciones de frases, cron minuto 37.
- Las pruebas se ejecutaron en el backend con privilegios administrativos; **NO implican que el teléfono esté conectado**.

## Contrato mínimo para interfaz
1. El usuario inicia sesión una vez mediante una vía segura, idealmente Supabase Auth o sistema equivalente que valide a un solo propietario.
2. Frontend envía una frase y una clave de solicitud única; NUNCA contiene ni almacena contraseñas de base de datos, claves `service_role` o tokens de automatización.
3. Gateway en servidor valida sesión + dueño autorizado, limita frecuencia, rechaza acciones no aprobadas, luego invoca `receive_mentor_text` usando identidad de servicio guardada en el servidor.
4. UI recibe `request_key` y `queued` con hora; consulta un endpoint restringido hasta `completed`, `failed`, `blocked` o vencimiento; el gateway accede a `mentor_command_receipt_v1` por una ruta privilegiada deliberadamente habilitada después de evaluación.
5. Mostrar estado, tiempo y evidencia sin información privada; nunca presentar `queued` como `completed`.
6. Respetar idempotencia por `request_key` para que dobles toques no ejecuten órdenes dos veces.
7. Registro y alertas privadas; el correo, push Android y la voz requieren pruebas independientes.

## Bloqueo de identidad detectado
En este proyecto Supabase, `auth.users` y `auth.identities` estaban vacíos al 19 de octubre. No exponer API privada públicamente ni conceder permisos a `anon` o `authenticated` sólo para hacer funcionar una demo. Configurar una identidad verificada y autorización por usuario antes de conectar el panel real.

## Respuestas resumidas de estado
```json
{
  "found": true,
  "command_id": 17,
  "state": "completed",
  "intent": "estado_sistema",
  "authorization_level": "automatic",
  "is_final": true,
  "evidence_type": "internal_live_status",
  "evidence_present": true,
  "details_exposed": false
}
```
Estados de errores: `invalid_request_key` y `not_found` no envían nada al ejecutor.

## Requisitos para marcar V1 completa
- Una sesión de propietario probada desde Android, sin secretos en cliente.
- Flujo completo interfaz -> gateway -> comando interno -> recibo -> interfaz con cierre correcto, duplicación bloqueada.
- Solicitudes sin sesión reciben 401 y otras identidades reciben 403; cero fuga de datos.
- Bloqueos de acciones delicadas sin firmas, envíos, cobros ni modificaciones de permisos no autorizados.
- Voz final seleccionada: referencia a voz conversacional natural tipo ChatGPT en español colombiano `es-CO`. La voz exacta de ChatGPT no se da por integrable; no usar TTS robótico como sustitución definitiva.
- El sábado 24 es meta de evaluación **máxima**, no fecha de espera: entregar antes cada hito probado.

## Continuidad multirruta
- Supabase + GitHub: primer camino para motor y código.
- GitHub Actions: pruebas de navegador ficticio sin Render, run 39308776625 success.
- Render: ejecutor ya desplegado, restringido; no postular a empleos por pruebas.
- Floot: UI opcional, nunca bloqueo para el backend.
- Vercel: despliegue alternativo sólo después de recuperar permisos de cuenta; en la sesión 19-oct el conector devolvió 403 en el scope intentado.
- No pagar, no exponer claves, no duplicar crons ni crear proyectos de pago.

**Este documento describe un contrato técnico, no una afirmación de integración móvil terminada.**
