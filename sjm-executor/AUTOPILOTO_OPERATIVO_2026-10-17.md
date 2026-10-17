## Revalidación y avisos — 17 oct 2026, 21:29 UTC

- Cron de clasificación #33 comprobado `succeeded` a 21:15, 21:20 y 21:25 UTC; cron de instrucciones #34 `succeeded` a 21:16, 21:21 y 21:26 UTC; ambos sin duplicar los 11 expedientes al repetir.
- Seguridad Supabase comprobada: `application_pipeline`, `application_pipeline_events`, `application_handoffs`, `browser_jobs` tienen `RLS=true`; `anon` y `authenticated` **no tienen permiso SELECT**.
- Gmail: aviso real enviado a **la propia cuenta conectada** con asunto `[SJM Control 360] Avance automático — 17 oct`, Gmail message ID `1a14bc496969aae5`; búsqueda de Gmail verificó el mensaje. `sjm_ops.notifications_outbox.id=112` marcado `delivered` con `channel=gmail` y recibo. Esto prueba **un envío por conector**, NO todavía entrega push de la automatización sin intervención ni sonido Android.
- El endpoint de YPAI anteriormente autorizado quedó cerrado de forma permanente para esa candidatura (`HTTP 410`) y en Render `live`; GitHub E2E `39070433084` y smoke remoto `39070672086` aprobados. Sin enviar dos veces.
- La semilla de inspección diaria `seed_job_form_inspections_v1` ahora **excluye casos `application_sent`, `response`, `approved`, `rejected`** para evitar trabajo repetido sobre solicitudes ya completadas.
- Elegibilidad oficial de las tres oportunidades YPAI restantes verificada y registrada en `sjm_ops.cases` y Airtable; Text/NLP y Model Evaluator potencialmente accesibles desde Colombia sin CV ni tasas, con consentimiento para cada vacante. Pose/Keypoint exige disponer de PC/pantalla adecuados. Ninguna de las tres enviada.
- Anyone AI formulario verdadero `/application` localizado y registrado; exige revisar experiencia y privacidad de uso de servicios conectados. Inspector propio read-only sigue con 0 campos (job #9, fallo de renderizado JavaScript); no postulación.

---

# SJM Control 360 — Autopiloto de postulaciones (estado verificable)

**Fecha:** 17 de octubre de 2026. **Entorno:** Supabase `dfqjwlsgqetyxdrsuviy`, Render gratuito `sjm-playwright-executor`, GitHub rama `sjm-executor-render`.

## Arquitectura funcionando

```text
Radar / expedientes oficiales (sjm_ops.cases)
  └─ cron #33: sjm_ops.application_pipeline_tick_v1() — cada 5 minutos
       ├─ clasifica fase de las vacantes e impide contar lecturas como envíos
       ├─ registra cambios privados en application_pipeline_events
       └─ encola SOLO inspecciones públicas de URLs exactas verificadas
            └─ cron #28: browser_tick_v1() (Supabase Vault → Render Playwright, token)
                 └─ lee DOM formulario, SIN enviar datos personales/aceptar términos
                      └─ cron #30: bridge_public_browser_cases_v1() — evidencia en casos
  └─ cron #34: application_handoffs_sync_v1() — cada 5 minutos
       └─ crea instrucción única para sesión Work, autorización específica o seguimiento
  └─ cron #31: application_watchdog_v1() — cada 10 minutos
       └─ detecta trabajos vencidos, formularios dinámicos, pendientes sin acuse
  └─ automatizaciones de ChatGPT existentes: SJM Alertas urgentes y SJM Resultados
       └─ revisiones en sus ciclos programados; móvil/push requieren permisos del dispositivo
```

## Resultados probados

- Funciones instaladas en Supabase: `application_pipeline_tick_v1()`, `application_handoffs_sync_v1()`.
- Tablas privadas nuevas `application_pipeline`, `application_pipeline_events`, `application_handoffs`: RLS activo; acceso `anon` y `authenticated` revocado. Sin nombre, email, teléfono, CV ni credenciales del candidato.
- Primera ejecución: **11 expedientes oficiales con URL**, 11 handoffs generados. Segunda ejecución idéntica: **0 expedientes duplicados**.
- Estado inicial: 1 `awaiting_response` (YPAI Data Annotator), 3 `needs_user_approval` (otras vacantes YPAI), 7 `needs_work` (revisión de requisitos o sitio requiere navegador dinámico).
- Cron #33 y #34 activo, con primeras ejecuciones `succeeded` comprobadas en `cron.job_run_details`.
- Render, Playwright y la verificación de seguridad funcionan: E2E GitHub Actions **39070433084**, production smoke **39070672086**, ambos `success`.
- **Duplicados YPAI Data Annotator bloqueados**: el endpoint antiguo `/jobs/submit-ypai` responde HTTP 410 incluso con credencial de envío válida. Prueba automatizada aprobada; despliegue Render **dep-db9ud3brjlhs73873qsg** figura `live`.
- **Anyone AI**: se encontró dirección oficial real `https://jobs.ashbyhq.com/anyone-ai/f90e4b5c-1682-4ddf-bb00-c8a11738a393/application`. El formulario existe y solicita datos adicionales; inspector Playwright restringido dio HTTP 200 pero 0 campos (trabajo #9, `failed`). Se requiere adaptar carga JavaScript y revisar consentimiento. Ninguna postulación realizada a Anyone AI.

## Distinguir estados y evidencias

1. `browser_jobs.done`: **solo página/formulario público leído**, NO postulación.
2. `application_pipeline.needs_user_approval`: se necesita consentimiento específico para esa vacante; no enviar.
3. `application_handoffs.needs_work`: instrucción preparada, **NO significa que Work esté abierto o ejecutándose**.
4. `sjm_ops.cases.application_sent`: candidatura declarada enviada; conservar fuente de evidencia (usuario, confirmación sitio, Gmail).
5. YPAI Data Annotator: el usuario informó envío en Work, reportó confirmación «Application received» y el expediente se reconcilió en Supabase como `confirmed`, `attempts=1`; **hasta la última comprobación no hay correo oficial YPAI en Gmail**, y la pantalla Work no fue adjuntada a este repositorio. Mantener seguimiento sin duplicar.
6. **Enviar aplicaciones universalmente sin sesión Work**: NO implementado. La ejecución vía Playwright está autorizada solo para lecturas seguras y pruebas locales ficticias. Nunca sortear restricciones de proveedores para transmitir datos personales.

## Consultas para revisión técnica

```sql
select stage,count(*) from sjm_ops.application_pipeline group by stage;
select status,count(*) from sjm_ops.application_handoffs group by status;
select jobid,jobname,active,schedule from cron.job where jobid in (28,30,31,33,34);
select application_key,status,attempts,receipt
from sjm_ops.employer_applications where employer='YPAI';
```

## Pendientes verdaderos para automatización completa

- Desarrollar y verificar adaptadores específicos para los portales compatibles, solo cuando los términos permitan automatizar y los datos/consentimientos estén autorizados.
- Habilitar un canal seguro de activación en Work para sesiones que requieren login/CAPTCHA; **no existe apertura desatendida de Work desde Supabase en este contexto**.
- Obtener/validar acuses oficiales de cada solicitud y retroalimentarlos al registro maestro sin inventar solicitudes.
- Probar envío automatizado de notificaciones a Android; las notificaciones de las tareas ChatGPT están deshabilitadas según la última revisión. Gmail recibió un correo de prueba en la sesión anterior, pero la notificación móvil audible no está confirmada.
- Revisar el hallazgo de tablas históricas sin RLS en `sjm_ops` por separado y con análisis de dependencias: nunca cambiarlas en bloque sin aprobación y pruebas.

**Reglas:** sin compras, contratos nuevos, equity, datos falsos, CAPTCHA/OTP eludidos, duplicados ni secretos en GitHub. No contactar fuentes excluidas por decisión del fundador.
