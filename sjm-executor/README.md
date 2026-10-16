# SJM Playwright Executor — complemento de TinyFish y Floot

Servidor HTTP preparado para Render Docker, plan free. Supabase pendiente.

GET /healthz: estado HTTP, no comprueba Chromium.
POST /self-test: requiere Authorization: Bearer EXECUTOR_TOKEN. Ejecuta Chromium contra el formulario local incluido, valida nombre y email ficticios y devuelve evidencia JSON. Sin envíos externos por API. Una tarea simultánea.

Despliegue: subir estos archivos a la raíz de un repositorio, crear servicio Docker Free en Render con ese repositorio, configurar EXECUTOR_TOKEN como secreto y health check /healthz. render.yaml permite generar el secreto mediante Blueprint. No hay servicios pagos en esta configuración.

Pruebas locales del 16 octubre 2026 UTC: /healthz HTTP 200; petición sin token HTTP 401. Prueba de navegador pendiente: la descarga de Chromium falló en el entorno de preparación y la prueba devolvió HTTP 500. No desplegado ni probado en Render. validation.json contiene resultados reales.

Render Free puede suspender el servicio por inactividad; no ofrece ejecución continua garantizada. El sistema de archivos es temporal. Aún falta integrar la cola, resultados persistentes y acceso de mínimo privilegio con Supabase. No agregar claves de Supabase al repositorio.
