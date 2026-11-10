# KAIRÓS — Evidencia de pruebas de failover (10 nov 2026)

Fuente: rama `audit/tool-evaluation-20261109`, archivos `kairos-render-lab/failover.mjs` y `kairos-render-lab/failover.test.mjs`.

Se recuperó el contenido de ambos archivos desde GitHub y se ejecutó una copia idéntica en un entorno aislado con **Node.js v22.16.0**, comando `node --test failover.test.mjs`.

Resultado TAP: **8 pruebas, 8 aprobadas, 0 fallidas**, duración 130.626313 ms.

Casos: selección por cuota; recuperación tras fallo; bloqueo de lease/consentimiento; prevención de envíos sin idempotencia; ausencia de proveedores gratuitos; vencimiento; cooldown; recuperación tras cooldown.

Alcance: prueba local de lógica pura. **No** acredita despliegue, integración real con Render/GitHub/Supabase, ejecución de postulaciones, ni entrega al Motorola. Antes de producción: verificar contratos de proveedores, integración transaccional y pruebas extremo a extremo con ACK y auditoría.
