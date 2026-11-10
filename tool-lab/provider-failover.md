# KAIRÓS — proveedores de respaldo (evaluación)

Fecha: 2026-11-09. Solo investigación y configuración documental. Ninguna cuenta externa creada ni despliegue autorizado.

## Capas de redundancia
- Estado y cola: Supabase existente. Mantener idempotencia, arrendamientos de tareas y comprobantes.
- Ejecutor de navegador: Render/Playwright existente; GitHub Actions para pruebas y trabajos acotados, respetando cuotas.
- Coordinación ligera: Cloudflare Workers Free (100000 solicitudes/día, 10ms CPU por solicitud, 5 cron triggers por cuenta; no sirve para navegador pesado).
- Contenedores bajo demanda: Google Cloud Run (cuota gratuita, requiere verificar facturación, disponibilidad y límites).
- VM de respaldo: Oracle Cloud Always Free (registro puede exigir tarjeta y capacidad no garantizada).
- Alternativas a evaluar: Deno Deploy, Activepieces, n8n, Browser Use, Stagehand; confirmar cuotas antes de uso.

## Política de conmutación
1. Obtener tarea desde cola persistente con clave idempotente y lease temporal.
2. Evaluar salud, cuota restante y costo máximo $0 de cada proveedor; bloquear si no hay verificación de gratuidad.
3. Elegir ejecutor compatible por tipo de tarea. No enviar la misma postulación en paralelo.
4. Guardar resultado y evidencia antes de liberar tareas sucesoras.
5. En errores transitorios, reintentar con backoff y número máximo de intentos. En errores de autorización, CAPTCHA o identidad, solicitar intervención.
6. Si todos los ejecutores fallan, conservar la tarea en cola y alertar; nunca declarar éxito.

## Referencias oficiales
- https://developers.cloudflare.com/workers/platform/limits/
- https://cloud.google.com/run
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## Próxima prueba
Medir health y cuota de los ejecutores actuales y probar una tarea no destructiva de extremo a extremo; no conectar proveedores externos sin credenciales/autorización y sin límite de gasto verificable.
