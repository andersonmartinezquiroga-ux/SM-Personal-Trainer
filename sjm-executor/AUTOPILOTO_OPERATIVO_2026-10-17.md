# REPARACIÓN EN CURSO — SJM AUTÓNOMO 360 — 17 OCT 2026

## Lo realizado con pruebas reales (no confundir con candidaturas enviadas)

1. **Motor / enrutamiento de fuentes públicas:** tabla RLS `sjm_ops.public_job_site_allowlist` con 11 URLs exactas de casos ya identificados; 9 activas para inspección y 2 Workana desactivadas tras challenge humano. `browser_dispatch_v1` solo procesa URLs de esta lista. `application_pipeline_tick_v1` enlaza las oportunidades oficiales a la cola y no repite URLs recién procesadas. Los 11 casos conocidos pasaron por la clasificación; se crearon cinco trabajos nuevos sin enviar formularios.
2. **Lectura de portales:** módulo `sjm-executor/applicant.py` ampliado con GET/HEAD a sitios públicos específicos Workana, TransPerfect, Welo y My Virtual Trainer. Nunca transmite nombres, correos, CV, grabaciones, ni pulsa Enviar. Detecta challenge humano; NO resolverlo ni clasificarlo como éxito. Pruebas: GitHub Actions `39073133551` (16 unitarias + E2E), versión Render `dep-db9uvdgm7kps73er1cig` LIVE. Producción: TransPerfect `browser_jobs #13` DONE (HTTP 200, listing, 3 elementos HTML, no formulario de postulación confirmado); Welo Circinus `#14` DONE (HTTP 200, listing, enlace Apply); My Virtual Trainer `#15` DONE (HTTP 200, listing sin formulario). Todos `submitted=false`.
3. **Adaptador Welo /apply:** Playwright sigue el enlace oficial GET a `/apply` y leyó **24 campos** del formulario sin introducir datos. Prueba E2E `39073837860` PASS; nueva versión `dep-db9v4hbncjis73apdsgg` LIVE. Trabajo de verificación desde Supabase `browser_jobs #16` encolado: esperar finalización DONE antes de atribuir prueba de producción. `public_job_site_allowlist` Welo Circinus cambió a `inspection_class=form`.
4. **Adaptador Anyone AI:** lectura pública del anuncio se logra, pero el formulario requiere POST GraphQL `jobs.ashbyhq.com/api/non-user-graphql`. No habilitar POST genérico sin comprobar que es solamente lectura; actualmente inspector registra 0 campos y deriva a Work. Cargar recursos estáticos GET de `app.ashbyhq.com/api/images/` y `cdn.ashbyprd.com` fue probado sin exposición personal (`39073457545` PASS), pero no resuelve el formulario.
5. **Autorizaciones puntuales:** tabla RLS `sjm_ops.application_consent_gate`, acceso service-role solamente; consulta `application_approval_ready_v1(case_key)` con doble aprobación explícita y fecha/referencia, nunca inferir por analogía. Cron #35 cada 10 minutos `sjm_ops.application_consent_prepare_v1()`; primera ejecución creó **6 permisos PENDIENTES** para 3 vacantes YPAI (enviar y aceptar términos por separado) y segunda ejecución creó 0 duplicados. CERO nuevas aprobaciones concedidas automáticamente. El caso YPAI Data Annotator ya enviado figura `previously_submitted=true` y no puede entrar en otro envío.
6. **Estados / comprobantes:** ampliado el campo evidencia `official_listing_read_only` para separar la página pública del formulario. `browser_collect_v1` confirma DOM/título, distingue formulario/listado y marca challenge como fallido, sin falsear el resultado. `application_pipeline_tick_v1` pasó con 4 cambios de etapa tras corregir el nuevo valor en `application_pipeline_evidence_level_check`; no se crearon candidaturas externas. Registro YPAI Data Annotator continúa en `application_sent` desde sesión Work según reporte de confirmación visible del fundador y registro previo, sin correo de acuse nuevo; NO duplicar.

## Qué falta por comprobar para cerrar el sistema completo

- **Envío real desde el motor para múltiples empleadores:** NO habilitado. La automatización Playwright sigue siendo GET solo para portales externos, salvo formulario ficticio local. Necesita adaptadores por empresa, política de autorización y prueba real de envío + recibo con consentimiento específico.
- **Inicio desatendido de sesiones Work**: este entorno no ofrece acción directa para lanzar Work en segundo plano; las instrucciones se preparan en `application_handoffs`, pero `launched_work=false`. No fingir ejecución.
- **Confirmaciones y seguimiento Gmail:** el correo se puede revisar por las automatizaciones de ChatGPT; la entrega automática desde Supabase a Gmail no está integrada con proveedor OAuth. No afirmar recepción sin acuse.
- **Android audible:** no hay señal confirmada de push/sonido; depende de ajustes y permisos del móvil.
- **Challenge humano de Workana:** dos rutas en allowlist deshabilitadas, mantener en `needs_adapter` para revisión manual de sitio, sin tratar de sortear CF.
- **Seguridad:** nuevas tablas con RLS; auditoría de tablas históricas aún pendiente y se debe hacer por dependencias, no activar masivamente.

**Criterio de finalización:** una candidatura real de otra vacante, ejecutada y confirmada por flujo apropiado y autorización específica, vinculada automáticamente a caso con acuse; luego probar aviso móvil. Un README o un cron correcto no equivalen a este resultado.

---

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
