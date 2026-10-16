# SJM Control 360 → Playwright: contrato de integración (v1, 2026-10-16)

Estado: diseño versionado, **NO desplegado ni conectado**. Sin servicios pagos.

## Flujo de extremo a extremo
1. Control 360 crea trabajo de prueba en `sjm_ops.work_queue` con `is_test=true`, `dedupe_key` único, `kind` de prueba y estado inicial permitido por el esquema.
2. Un despachador autenticado toma una tarea a la vez con bloqueo transaccional y marca el intento. Nunca enviar una tarea a un proveedor con `verified=false` en `sjm_ops.failover_routes`.
3. El despachador llama `POST /self-test` del servicio Render con `Authorization: Bearer EXECUTOR_TOKEN`, secreto exclusivamente en el gestor de secretos del servidor.
4. Exige HTTP 200 y valida que los dos resultados de Playwright indiquen éxito y que el formulario ficticio confirme `RECIBIDO`. Un 200 por sí solo no prueba un trabajo real.
5. Persiste resultado JSON sin datos sensibles, hora, identificador de trabajo y evidencia en Supabase. Actualiza estado `done` solo si se confirmó persistencia; si no, reintento limitado con backoff.
6. Registra `sjm_ops.runs` y muestra estado en Control 360. Verifica también errores, 401, 429, 500, reinicio y duplicados.

## Límites de seguridad
- `/self-test` únicamente usa localhost y datos ficticios. **Prohibido** usarlo para formularios o postulaciones externas.
- Ningún trabajo externo sin validación de elegibilidad, autorización correspondiente, reglas del sitio y comprobante.
- Aislar clientes, controlar acceso a resultados, no guardar tokens en logs ni GitHub.
- Render Free puede dormir: una prueba exitosa no garantiza disponibilidad permanente.
- `GET /healthz` solo verifica HTTP, no Chromium ni conexión a Supabase.

## Criterios de aceptación
- [ ] Un trabajo de prueba atraviesa cola → despachador → Render → Supabase → Control 360.
- [ ] Evidencia consultable con idempotencia y sin duplicados.
- [ ] Fallo simulado genera reintento controlado y aviso, no falso éxito.
- [ ] Prueba de acceso denegado y secreto protegido.
- [ ] Recién entonces habilitar la ruta Playwright como `verified=true`.

## Próxima implementación
Crear despachador de mínimo privilegio (por ejemplo, Edge Function Supabase) con secreto de Render; añadir tabla de evidencias con políticas de acceso; instrumentar pruebas; conectar vista de Control 360. Mantener TinyFish y Floot como herramientas complementarias.
