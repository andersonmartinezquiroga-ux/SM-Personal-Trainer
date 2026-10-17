# ACTUALIZACIÓN OPERATIVA — 17 OCT 2026, después del diagnóstico de colas

- **Diagnóstico de raíz**: `sjm_ops.worker_tick('cron')` es explícitamente `safe-control-only`; solo completa tareas `kind=self_check`, marca vencimientos y cuenta trabajos que esperan conector. `sjm_ops.orchestrator_tick` procesa revisiones internas y señales oficiales, pero no envía solicitudes laborales por sí solo. Un cron exitoso con `processed_count=0` no acredita postulaciones.
- **Incidentes corregidos**: `browser-executor-missing-20261015` y `browser-executor-unavailable-20261015` cerrados con prueba del Playwright desplegado y tres trabajos de prueba/verificación completados; `sjm-real-applications-dispatch-20261017` abierto, severidad crítica. Sin ocultar la limitación del envío real.
- **Nueva semilla diaria**: función `sjm_ops.seed_job_form_inspections_v1()`, cron 29 `sjm-job-form-seed-daily-v1`, 13:37 UTC. Solo encola lectura de cinco URLs públicas oficiales allowlisted: cuatro YPAI Colombia y Welo AI Trainers Spanish, nunca envía datos personales ni pulsa Enviar. 17 oct primer llamado creó browser_jobs #4, #5, #6 para pose/keypoint, texto NLP y evaluador de modelos. Trabajos #2 y #3 ya estaban inspeccionados en las últimas 23 horas y no se duplicaron.
- **Despachador existente**: `sjm_ops.browser_tick_v1()`, cron 28 cada dos minutos, envía trabajos solo `self_test` ficticios o `inspect` de los dominios autorizados, recoge respuestas, registra HTTP y número de campos. #4 en espera de respuesta del servidor en el primer chequeo; comprobar `browser_jobs.state` antes de afirmar éxito.
- **Puente al registro maestro**: `sjm_ops.bridge_public_browser_cases_v1()`, cron 30 `sjm-browser-to-control-bridge-v1` cada cinco minutos. Actualiza casos `commercial/radar` existentes cuando un trabajo de inspección pasa con `submitted=false`. No convierte el caso en `application_sent` sin un acuse real. Primer llamado actualizó dos casos, incluidos YPAI Data Annotator y Welo AI Trainers; los tres restantes se actualizarán solo después de una lectura exitosa.
- **Permisos**: funciones nuevas `SECURITY DEFINER` con `search_path=''`, permisos de ejecución revocados a `PUBLIC/anon/authenticated`, concedidos solo a `service_role`. Tabla `browser_jobs` privada con RLS, sin datos personales. Proteger credenciales existentes en Supabase Vault; no subirlas a GitHub.
- **Rutas**: `failover_routes.job_form_inspection/playwright_render` verificado; `browser_automation/playwright` registrado como existente, pero `verified=false` para envíos genéricos (no probado). TinyFish sin saldo, no pagar ni reintentar.
- **Postulación YPAI**: el fundador autorizó nombre, correo, Colombia, privacidad y términos específicos de colaborador; prohibió teléfono, CV, voz y nuevos contratos. Módulo `submit_ypai.py` instalado y probado con datos ficticios en GitHub/Render, pero `employer_applications.id=1` permanecía `authorized`, `attempts=0`, sin acuse en el último chequeo. El intento de conectar datos personales desde Supabase a Render fue bloqueado por controles de seguridad; NO eludir. Usar sesión de navegador interactiva autorizada en Work y verificar de forma visible confirmación real y Gmail; un solo envío, no duplicar. No marcar como enviado hasta prueba.
- **Avisos**: sistema `queue_urgent_deadlines` informa `delivery_provider_connected=false`, y las automatizaciones ChatGPT activas tienen notificaciones deshabilitadas. No afirmar alertas audibles ni push hasta que se habiliten/probadas.

---

# SJM Control 360 → Playwright — estado técnico verificado

Última revisión: 17 de octubre de 2026, 10:40 Colombia.

## Instalado y comprobado
- Repositorio: `andersonmartinezquiroga-ux/SM-Personal-Trainer`, rama `sjm-executor-render`.
- Servidor existente: `sjm-playwright-executor`, Render Free, `https://sjm-playwright-executor.onrender.com`.
- API `api_v2.py`: `GET /healthz`, `POST /self-test`, `POST /jobs/inspect`, `POST /jobs/draft`. Las operaciones POST requieren bearer privado. No hay una ruta de presentación externa.
- El navegador Chromium de Render pasa su prueba local de relleno y pulsación de formulario ficticio `RECIBIDO`, e inspecciona páginas externas de lectura solamente. Verificado desde GitHub Actions: https://github.com/andersonmartinezquiroga-ux/SM-Personal-Trainer/actions/runs/39040982197
- Comprobación adicional de formularios de Welo y de YPAI Data Annotator: https://github.com/andersonmartinezquiroga-ux/SM-Personal-Trainer/actions/runs/39045633888
- Supabase `dfqjwlsgqetyxdrsuviy`, tabla privada `sjm_ops.browser_jobs`, RLS activado, sin políticas para anon/authenticated, sin credenciales en repositorio ni en informes.
- Funciones privadas `sjm_ops.browser_dispatch_v1()` (envío HTTP limitado a inspección o formulario ficticio), `sjm_ops.browser_collect_v1()` (recupera respuesta y guarda resumen sin datos personales), `sjm_ops.browser_tick_v1()` (control de concurrencia y ciclo).
- Credencial almacenada como secreto de Supabase Vault bajo el identificador `sjm_render_executor_inspector_v1`; no registrar su valor.
- `pg_cron` job n.º 28, `sjm-browser-workflow-v1`, ejecuta cada 2 minutos, comprobado en `cron.job_run_details` a 15:34, 15:36, 15:38 y 15:40 UTC.

## Evidencia extremo a extremo Supabase → Render → Supabase
- `sjm_ops.browser_jobs.id=1`: prueba local ficticia, estado `done`, petición 105, HTTP 200, confirmación `RECIBIDO`, sin candidaturas reales.
- `id=2`: página oficial Welo AI Trainers Network, `done`, petición 106, HTTP 200, 45 campos, `submitted=false`.
- `id=3`: página oficial YPAI Data Annotator Colombia, `done`, petición 107, HTTP 200, 10 campos, `submitted=false`. Importante: trabajo DESPACHADO AUTOMÁTICAMENTE por cron a las 15:38 UTC y RECOGIDO AUTOMÁTICAMENTE a las 15:40 UTC, sin intervención manual.
- Las rutas aceptan solo dominios y rutas concretas: empleos oficiales de Welo/Appen (Lever), Anyone AI (Ashby) y cuatro publicaciones YPAI Colombia. Todo HTTP externo GET/HEAD; sin POST a empleadores.

## Qué NO está hecho todavía
- **Ninguna candidatura laboral externa enviada con este ejecutor**. No contabilizar formularios leídos como aplicaciones.
- El flujo de datos personales, archivos CV, revisión de requisitos, autorización de consentimiento legal y pulsación real de Enviar requiere un adaptador por empleador y prueba final.
- El sistema principal `sjm_ops.work_queue` no está migrado a `browser_jobs`; esta última es la primera cola autónoma verificada. No confundir las dos.
- No activar `sjm_ops.failover_routes.browser_automation.playwright` como envío verificado; solamente `job_form_inspection/playwright_render` tiene prueba y marca `verified=true`.
- No sortear CAPTCHA, OTP, Turnstile, login, T&C o permisos personales. No guardar datos personales en GitHub.

## Primera candidata para envío autorizado
YPAI `https://freelancer.ypai.ai/jobs/openings/data-annotator-co`:
- Página activa para remoto Colombia, CV opcional, teléfono opcional, campos nombre, email, país y consentimiento; puede crear un perfil Freelance YPAI.
- Exige aprobación personal de la política de privacidad y tratamiento de los datos de la solicitud (hasta 2 años según formulario); no consentir por el fundador sin su autorización explícita.
- Se requiere validar el envío real, el acuse visible y/o correo oficial. Antes de ello mantener `0` candidaturas nuevas de YPAI.

## Operación / supervisión
Consulta manual de estado solo lectura:
```sql
select id,job_key,operation,state,request_id,response_summary,last_error,completed_at
from sjm_ops.browser_jobs order by id desc limit 15;
```
No añadir trabajos genéricos: el despachador solo permite `self_test` e `inspect`. Un error debe registrarse, nunca falsear éxito.
