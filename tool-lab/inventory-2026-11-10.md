# KAIRÓS · Auditoría de herramientas — 2026-11-10

## Infraestructura verificada por conectores
- Supabase `sjm-control` (`dfqjwlsgqetyxdrsuviy`): `ACTIVE_HEALTHY`.
- Render `sjm-playwright-executor`: servicio Docker, plan free, rama `sjm-executor-render`, autodeploy desactivado.
- Render `sjm-kairos-lab-alterno`: servicio Node, plan free, rama `feature/kairos-render-lab-v1`, autodeploy por commit.
- Vercel: `sjm-kairos-cerebro-web`, `sjm-control-360-respaldo`, `sjm-performance-premium`, `sjm-cobros-premium` registrados. Presencia no implica despliegue saludable.
- GitHub: `kairos-render-lab/failover.mjs` y `failover.test.mjs` presentes en rama aislada `audit/tool-evaluation-20261109`.

## Evaluación e incorporación sin costo
| Herramienta | Estado comprobado | Acción autorizada siguiente |
| --- | --- | --- |
| Codex | Acceso operativo de Codex CLI no verificado | Verificar entorno y autenticación; usar para parches y pruebas solo si existe acceso incluido sin costo adicional |
| Gemini CLI | No verificada instalación ni cuota | Probar versión y límites gratuitos en entorno aislado; no introducir claves en repositorio |
| OpenCode | No verificada instalación | Evaluar solo si aporta orquestación distinta y modelos gratuitos comprobados |
| n8n | No verificada instancia | Comparar con crons y automatizaciones existentes antes de desplegar |
| Replit | Conector disponible, proyecto/ejecución no auditados en este corte | Verificar proyecto antes de crear otro |
| Claude Code / Copilot | Opcionales, sin instalación verificada | No priorizar ni activar suscripción |

## Prueba de aceptación de efecto cadena
1. Crear tarea de inspección NO destructiva con clave idempotente.
2. Asignar a proveedor habilitado y con cuota gratuita verificada.
3. Registrar inicio, lease, salida, error y comprobante en Supabase.
4. Simular fallo y verificar que el proveedor alternativo retome la misma tarea sin duplicarla.
5. Verificar notificación Android solo con permiso vigente y acuse real.
6. Registrar ID de ejecución, commit y evidencia. Sin estos comprobantes, no declarar integración ni autonomía 24/7.

**No se han instalado Codex, Gemini CLI, OpenCode ni n8n durante esta auditoría. No se ha enviado ninguna postulación.**
