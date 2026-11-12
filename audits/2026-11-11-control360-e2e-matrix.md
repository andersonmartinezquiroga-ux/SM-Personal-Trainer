# CONTROL 360 + KAIRÓS — auditoría 14 estaciones
11 noviembre 2026, tarde Colombia. Pruebas de seguridad y aislamiento; ninguna candidatura ficticia enviada.

| N.º | Estación | Evidencia real | Estado |
|---|---|---|---|
| 1 | Objetivo | 115 expedientes y casos reales | BASE VERIFICADA |
| 2 | Búsqueda | Pausada por orden del fundador; simulada en laboratorio | NO INTEGRADA HOY |
| 3 | Captura | 115/115 handoffs | BASE VERIFICADA |
| 4 | Autenticidad/vigencia | Ejecutor inspecciona formularios; sin envío comercial | PARCIAL |
| 5 | Duplicados | 728 casos, 0 claves duplicadas | PARCIAL |
| 6 | Elegibilidad | 11 casos en needs_eligibility | BLOQUEADA |
| 7 | Prioridad | 34 casos prioridad 1-3 | BASE VERIFICADA |
| 8 | Preparación | 115 handoffs; 62 inspecciones pendientes | PARCIAL |
| 9 | Seguridad/autorización | 0 carriles autorizados, 0 filas preflight, acceso anónimo 401 | BLOQUEADA |
| 10 | Ejecución | Chromium real pasó formulario LOCAL; 0 operaciones submit en browser_jobs | BLOQUEADA PARA TERCEROS |
| 11 | Comprobación | 11 recibos históricos, 0 ACK de pulsos | BLOQUEADA PARA CICLO AUTÓNOMO |
| 12 | Registro | 144 browser_jobs: 124 done, 20 failed; done no es envío | PARCIAL |
| 13 | Seguimiento | 30 awaiting_response; reloj simulado probado | PARCIAL |
| 14 | Cierre/alertas | 5 closed; 3 avisos awaiting_bridge; teléfono tiene otros 16 avisos históricos completados | BLOQUEADA EN PUENTE |

## Prueba del ejecutor existente
GitHub Actions run 43108539319: 4 trabajos aprobados, incluido Chromium/Playwright ejecutando código existente de la rama sjm-executor-render y enviando un formulario LOCAL con comprobante RECIBIDO. También verifica accesos sin autorización. No es una postulación a empleador.
https://github.com/andersonmartinezquiroga-ux/SM-Personal-Trainer/actions/runs/43108539319

## Cuellos de botella confirmados
- 115 casos tienen handoff, pero 14/115 referencian browser_job (12 done, 2 failed).
- 59 necesidades de adaptador, 42 Workana.
- 0 registros en application_live_submit_preflight_v1.
- 144 browser_jobs: 121 inspect, 23 self_test, 0 submit. En total 124 done, 20 failed.
- 36 señales de pulso a las 17:00 Colombia, 0 ACK externos.
- Android: 1 teléfono habilitado, última señal 17:04 del 11-nov. Ruta public.sjm_kairos_phone_jobs_v1: 16 notificaciones completed históricas y 6 failed; último aviso completado 10-nov 19:37 Colombia. Ruta sjm_ops.kairos_mobile_queue_v1: 3 awaiting_bridge desde octubre/noviembre, 0 confirmadas.
- Floot: 500 escenarios sobre módulos de código auténtico, test PASS. Límite de uso 100/100 hasta 19:00 Colombia.
- 7 tablas sjm_ops sin RLS en diagnóstico, privilegios directos de select anon/auth no concedidos en muestras; no activar RLS sin revisión.

## Regla de aprobación
Exigir un expediente de prueba aislado que pase por los componentes auténticos: caso, decisión, autorizaciones, navegador real, acuse real del endpoint de prueba, registro, seguimiento acelerado, puente y ACK real Android. Simulaciones no son prueba de envío externo.
Estado: integración total NO APROBADA todavía. No modificar expedientes productivos ni enviar formularios ficticios a terceros.
Pruebas en lotes sin esperar 1 hora por caso; la programación horaria solo retoma/supervisa.
