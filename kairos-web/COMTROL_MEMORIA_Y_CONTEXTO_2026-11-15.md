# COMTROL 360 · Memoria y contexto de conversaciones — 15 noviembre 2026

## Estado verificado
**Mis conversaciones — respaldos privados**, dentro del chat de la app existente COMTROL 360, está publicado en producción con la misma base de datos y autorización SJM. El titular puede elegir manualmente **Guardar conversación**, **Buscar mis respaldos** y **Recuperar selección**. Esto **NO** equivale a una memoria autónoma del modelo IA: es un mecanismo explícito de respaldo y recuperación de mensajes. No hay sincronización automática, no se cargan todos los chats por defecto y no se comparten mensajes con proveedores LLM al guardarlos.

El respaldo de un chat toma como máximo sus últimos 30 mensajes de texto (cada mensaje acotado, total cercano a 90 KB), y alerta de posibles contraseñas o códigos. Se recomienda NO guardar datos sensibles. La restauración no sobrescribe una conversación existente en el dispositivo.

**Backend:** migración `comtrol_owner_only_explicit_conversation_backups_20261115`, tabla `public.sjm_comtrol_chat_backups_v1`, RLS por `auth.uid()`, acceso anónimo bloqueado. Pruebas reversibles: propietario inserta y actualiza, segundo usuario no puede leer ni modificar, ni insertar como el titular; ROLLBACK sin datos de prueba persistidos. Lectura final: 0 respaldos guardados.

**Motor IA independiente:** función `sjm_brain_hybrid_v1` versión 8 ACTIVE, JWT habilitado. Puede recibir opcionalmente **hasta 4 mensajes anteriores** únicamente cuando se marque expresamente consentimiento para contexto y también consentimiento para la pregunta. Se validan rol (user/assistant), tamaño y patrones de credenciales; no se solicita ni recupera historial desde Supabase por este endpoint.

El cliente web limita el contexto a **pares anteriores de preguntas/respuestas del modelo independiente**, excluyendo resúmenes de CONTROL, datos del Motorola y códigos de vinculación. Una comprobación aislada verificó 7/7 casos de validación y selección de contexto, incluyendo la exclusión de una respuesta de Mentor que contenía un código temporal ficticio.

## Pruebas adicionales obligatorias
1. Entrar en Chrome Motorola con sesión real, NO vista previa.
2. Escribir dos mensajes ficticios en un chat; abrir «Mis conversaciones · respaldos privados».
3. Pulsar Guardar conversación; confirmar que se guardó; consultar Buscar mis respaldos.
4. En otro dispositivo con **la misma cuenta autorizada** iniciar sesión, elegir la copia y recuperarla; comprobar que el chat aparece íntegro dentro del límite.
5. Verificar que un segundo usuario autenticado no puede leer ni sobrescribir copias del titular. La prueba de RLS en base está hecha; falta navegador completo.
6. Probar recuperación de conexión, respuestas inválidas y límite de tamaño.
7. Para el modelo independiente: configurar primero un proveedor de modelo abierto verdaderamente externo a ChatGPT, autorizar cada pregunta y opcionalmente el contexto; comprobar que el servidor informa cuántos mensajes fueron enviados. Si no hay proveedor configurado, no afirmar inteligencia generativa autónoma.
8. Revisar política de retención y eliminación de backups con controles del usuario antes de ofrecer el producto a empresas; actualmente NO existe borrado directo de copias.

## Evidencia de release
- Archivo web `kairos-web/index.html`: UI versión v3.1, producción Vercel `dpl_AApN3nMucCHPUyLCtbXA8QvY48VW` READY, URL https://sjm-kairos-cerebro-web.vercel.app.
- HTTP 200 para el dominio y sintaxis JS verificada; módulos de inventario, CRM, espacios empresariales, voz, dictado y planes conservados.
- Supabase Edge Function `sjm_brain_hybrid_v1` versión 8, código sincronizado con `kairos-web/supabase/functions/sjm_brain_hybrid_v1/index.ts`.
- Prueba verdadera de inferencia con proveedor independiente **aún no realizada**. Tampoco E2E en Motorola. Mantener madurez estimada sin aumentos no demostrados.

## Próximo paso
**Conectar un modelo libre de pago obligatorio** (si el proveedor confirma condiciones viables, o autoalojado con recursos propios), activar la conexión segura con credenciales solo en servidor, probar preguntas con y sin contexto; después implementar memoria contextual persistente y controles de eliminación y cifrado de los datos empresariales.

## Control del titular: eliminar respaldo (15 noviembre 2026)
Se añadió **Eliminar respaldo de nube** con confirmación explícita dentro del mismo panel. Elimina únicamente el registro de Supabase seleccionado, sin modificar el historial local del dispositivo. La política RLS `sjm_chat_backups_owner_delete` y permiso DELETE autenticado se aplicaron mediante la migración `comtrol_owner_explicit_delete_private_chat_backups_20261115`. Una transacción reversible probó eliminación propia (1 fila), bloqueo de borrado ajeno (0 filas) y ROLLBACK sin dejar datos. Solo la cuenta propietaria tiene acceso según `owner_id=auth.uid()`.

**Publicación final:** Vercel `dpl_CnQkTnoFo7jG3k12kbCKuvRFJXfv` READY, URL canónica HTTP 200 y script JS válido. Supabase `sjm_brain_hybrid_v1` v8 sigue ACTIVE/JWT. Prueba de uso real Chrome Android y modelo LLM independiente aún pendientes.
