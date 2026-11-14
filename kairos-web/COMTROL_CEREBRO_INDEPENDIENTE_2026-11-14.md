# COMTROL 360 · Motor independiente general (14 noviembre 2026)

## Objetivo
COMTROL es una aplicación y backend propios de SJM. Debe poder operar sin suscripción a ChatGPT. **Separar el servidor y la interfaz de ChatGPT no implica que ya exista un modelo LLM propio**. La arquitectura ahora admite conectar un modelo distinto por HTTPS bajo control SJM.

## Desarrollado y publicado
- Edge Function **sjm_brain_hybrid_v1** versión **7** en el Supabase existente, con autenticación y autorización del propietario (no se amplía la lista de acceso).
- Rutas anteriores `status`, `ask` (Mentor de CONTROL) conservadas.
- Nueva `ask_independent`: conversación general sin depender del informe del Mentor. Recibe solo la pregunta actual; no envía historial, expedientes, identidad de titular ni claves.
- El proveedor, modelo y clave solo se leen de variables privadas del servidor, **jamás** de HTML ni del navegador. Requiere consentimiento explícito por mensaje.
- Bloqueo de solicitudes con datos de autenticación sensibles y rechazo de los dominios directos de OpenAI/ChatGPT para modo independiente. **Eso no garantiza que un intermediario no redirija a otro proveedor**; debe verificarse el modelo real mediante documentación y prueba.
- `independent_self_test` comprueba cinco reglas sin hacer solicitudes a modelos externos. Requiere sesión válida del titular. No sustituye una prueba con modelo real.
- Selección visible en chat: **CONTROL · Supervisión** / **COMTROL · IA independiente** con indicador de configuración y autorización por pregunta. El modo de voz automático mantiene Mentor y no transmite voz automáticamente al modelo independiente.
- Guía de empresa: botón **Generar plan base sin nube** crea un archivo Markdown local por reglas, sin ChatGPT ni ningún proveedor. **No es un modelo de IA**, una investigación actual ni un trámite.

## Configuración posterior de un modelo realmente independiente
El administrador de Supabase debe configurar estos secretos **en el servidor**, nunca copiarlos a chat/GitHub/código cliente:
- `SJM_BRAIN_CLOUD_ENABLED=true`
- `SJM_BRAIN_CLOUD_URL` = endpoint HTTPS compatible con el formato `chat/completions` de un modelo distinto de OpenAI, por ejemplo un servidor de inferencia de modelo abierto.
- `SJM_BRAIN_CLOUD_MODEL` = identificador exacto del modelo realmente disponible.
- `SJM_BRAIN_CLOUD_API_KEY` = token secreto del proveedor, si lo requiere.

Los planes gratuitos y límites de un proveedor pueden cambiar. No asumir que es gratuito sin confirmar los términos y el volumen esperado. El código acepta servidores HTTPS de inferencia autoalojados compatibles; no compra servidores ni crea cuentas externas.

## Pruebas para declarar el cerebro independiente operativo
1. Iniciar sesión como titular y consultar `status`; `independent_model_configured` debe ser verdadero, sin publicar secretos.
2. Ejecutar `independent_self_test` y exigir 5 de 5 políticas, 0 llamadas externas.
3. Seleccionar IA independiente; enviar la pregunta ficticia «¿Cómo podría funcionar una tienda de zapatos?» con consentimiento, comprobar `mode=independent_model`, respuesta real del proveedor y `executedActions=0`.
4. Repetir sin consentimiento: debe negarse, sin llamada al proveedor.
5. Enviar una pregunta con una credencial ficticia: debe bloquearse antes del proveedor.
6. Comprobar caída del proveedor y falta de configuración: mostrar error explícito, nunca atribuirlo al Mentor ni fingir respuesta generativa.
7. Probar en Motorola y revisar costos/privacidad del proveedor por separado.
8. Mantener cifrado/retención y aislamiento de datos de empresas antes de usar información sensible.

## Evidencia disponible hoy
- Edge Function versión 7, estado ACTIVE y JWT habilitado. La prueba final de inferencia con un modelo externo **no se realizó porque no hay confirmación de proveedor independiente configurado y autorizado**.
- Frontend desplegado a producción (Vercel) con HTTP 200, sintaxis JS válida y módulos previos conservados.
- Generador de plan local probado con datos ficticios de negocio de zapatos (secciones y datos correctos; cero llamadas de red).
- No declarar 100 % ni alterar evaluación histórica `37/100` sin datos E2E. Siguiente cierre: conseguir proveedor abierto gratuito viable/autoalojado, configurar servidor, probar y documentar.
