# Mentor Samuel — política de continuidad técnica

Estado: plan de ejecución, no conmutación automática desplegada.

## Objetivo
Conversación natural por voz que invoque acciones auditables de agenda, sesiones y pagos.

## Rutas
- Interfaz primaria: app SJM / Floot cuando permita edición.
- Alternativa: aplicación web propia alojada independientemente; repositorio GitHub como fuente.
- Datos: Airtable para alumnos, sesiones y pagos; Calendar para agenda. Supabase es candidato para cola de tareas, sujeto a pruebas.
- Voz: ChatGPT en conversación para uso inmediato; voz externa para aplicación independiente pendiente de integración y permisos.
- Navegación: ejecutor Playwright en Render para tareas web permitidas, sin suponer conexión completa con Control 360.

## Reglas de continuidad
1. Si Floot agota cuota, seguir en repositorio propio y otra ruta de despliegue.
2. Si falla un proveedor, no repetir indefinidamente; registrar error, cambiar de proveedor y verificar.
3. Nunca confirmar registro de clase, pago o cita sin respuesta verificable del proveedor.
4. No duplicar operaciones ante reintentos: identificador único por acción.
5. No enviar mensajes, postular, pagar ni firmar sin autorizaciones pertinentes.
6. No afirmar que el motor es autónomo hasta que voz → interpretación → acción → confirmación pase prueba integral.

## Próxima entrega verificable
Endpoint de órdenes con validación y pruebas; interfaz móvil y conexión autenticada a agenda y registros.