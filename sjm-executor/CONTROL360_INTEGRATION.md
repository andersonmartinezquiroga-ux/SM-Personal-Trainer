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
