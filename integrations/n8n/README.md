# KAIRÓS 360 · n8n integration (staging)

Estado: preparado en rama separada, NO desplegado ni conectado a cuentas.

## Objetivo
Gmail → detectar respuestas, acuses, rebotes y plazos → clasificar sin confundir consulta con postulación → contrastar en Supabase → crear evento idempotente → notificar al Motorola solo ante novedad real.

## Condiciones antes de activar
1. Instancia n8n con HTTPS y autenticación.
2. PostgreSQL persistente dedicado a n8n, con respaldo. Render Free usa disco efímero: NO ejecutar n8n productivo sobre SQLite local en Render Free.
3. Credenciales Gmail OAuth, Supabase service role y clave de notificación en gestor de secretos, nunca en GitHub ni en el navegador.
4. Clave idempotente: Gmail message_id + tipo de evento; no duplicar candidaturas.
5. Eventos: respuesta humana, acuse automático, rebote, invitación, vencimiento, error. No convertir 'consulta enviada' en 'postulación enviada'.
6. Probar con un correo real conocido y verificar registro + alerta en Motorola; después activar automatización.
7. Claude y Gemini: proveedores opcionales por API, habilitar solo cuando exista autorización de cuenta y presupuesto/cuota gratuita verificable. No suponer API gratuita.

## Fuentes verificadas (10 nov 2026)
- SweatCircle: Gmail 1a1c57e162728e2a, acuse de candidatura recibida, pendiente revisión.
- Chase21: Gmail 1a1c62f7e435c9b8, respuesta humana; ingreso internacional previsto febrero 2027, no postulación formal.
- No reenviar automáticamente ni publicar datos privados.

## Bloqueadores actuales
- Render workspace autorizado: tea-das534e0tbcc73ds7s70.
- Render servicios existentes: sjm-kairos-lab-alterno y sjm-playwright-executor; no modificar sin pruebas.
- Falta almacenamiento PostgreSQL persistente para n8n y credenciales OAuth n8n.
- No declarar servicio instalado ni 24/7 hasta superar prueba real.

## Plan de integración
Implementar en entorno aislado, guardar comprobantes, validar eventos de Gmail, deduplicar y finalmente vincular a CONTROL 360.