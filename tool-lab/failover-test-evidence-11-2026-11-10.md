# KAIRÓS — 11 pruebas de failover

Rama: `audit/tool-evaluation-20261109`.
Commits de código: `c081e5b565fd3824da30e79da06a46c1d07680fb` y `bf4d07988cbf7288e3eca9d157e27047f5cbde4a`.

Se ejecutó una copia de ambos archivos con `node --test failover.test.mjs` en entorno aislado.

Resultado TAP: **11 tests, 11 pass, 0 fail**, 133.733725 ms.

Nuevas barreras: lease mal formado produce `hold`; idempotencyKey en blanco produce `hold`; cuota no numérica se descarta. Sin cambios en producción. Pendiente integrar y probar con ejecutores reales, auditoría y ACK Motorola.
