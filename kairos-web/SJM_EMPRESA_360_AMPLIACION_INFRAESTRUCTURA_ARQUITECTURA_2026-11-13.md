# SJM EMPRESA 360 IA · Ampliación de orden y arquitectura modular
**Proyecto existente:** COMTROL 360 / KAIRÓS — SJM CONTROL 360.
**Fecha de versión:** 13 de noviembre de 2026.
**Fuente actualizada:** `kairos-web/index.html` en `andersonmartinezquiroga-ux/SM-Personal-Trainer`.
**Commit de la actualización:** `81efff2254c0fe4d93595ee18553d312650f6ee1`.
**Producción:** https://sjm-kairos-cerebro-web.vercel.app

## Decisiones de producto
COMTROL 360 mantiene un único chat central con voz beta. SOLUCIONES EMPRESARIALES 360° sigue como prioridad, visualmente destacada sin aumentar desproporcionadamente los botones. Los servicios se organizan por centros: empresas, creación web/apps, infraestructura tecnológica, investigación, diseño, automatizaciones, y proyectos/empresas.

Se añade una categoría de infraestructura que **no existía** como centro independiente: arquitecturas, nube, servidores, hosting y DNS, redes, seguridad, respaldos, integraciones, monitoreo, despliegues y optimización de costos.

**Solicitud comercial prevista:** servicio seleccionado → diagnóstico → propuesta de alcance y presupuesto basado en cifras verificables → autorización segura → ejecución por herramientas conectadas → entrega con evidencia → seguimiento.

**Servicios comerciales previstos:** solicitud individual, paquete empresarial, servicio integral o suscripción. La interfaz actual solo prepara borradores, no genera cotizaciones vinculantes ni activa suscripciones.

## Implementación verificada
✅ El archivo de producción responde HTTP 200 y sirve la nueva versión de 190265 caracteres, con script válido. Se comprobó la presencia de la navegación, catálogo técnico, formulario de diagnóstico, ruta comercial, modalidades y estados visibles de futura zona de clientes.
✅ La app mantiene el inicio de sesión protegido existente, proyectos SJM, pantalla de voz, modo demostración, plantillas y archivos.
✅ Descarga de una plantilla CSV vacía de diagnóstico de infraestructura integrada al código (no comprobada desde el Motorola).
🔵 Formulario técnico: prepara una consulta para que el usuario la revise y pulse Enviar. Requiere pruebas funcionales en navegador/Android.
🔵 Catálogo empresarial de 10 áreas más el centro de infraestructura. Las opciones producen solicitudes, **no procesan contabilidad, nómina ni operaciones reales**.

## Arquitectura objetivo (no implementada en producción)
1. **Identidad y empresas:** `organizations`, `organization_members`, `roles`, `permissions`; acceso privado por empresa y sesiones verificadas. Ningún usuario podrá enumerar datos de otra empresa.
2. **Solicitudes:** `service_catalog`, `service_requests`, `diagnoses`, `proposals`, `estimate_lines`. Cada presupuesto debe mostrar moneda, vigencia, supuestos y respaldo de costos; no generar precios inventados.
3. **Consentimiento:** `approvals` con identidad de responsable, fecha, alcance, versión y límite económico; acciones sensibles requieren confirmación humana.
4. **Ejecución:** `runs`, `run_steps`, `tool_connections`, `evidence`, `deliverables`; eventos idempotentes, reintentos acotados y confirmación de resultados.
5. **Continuidad:** `task_schedules`, `notifications`, `alerts`; no atribuir ejecución autónoma sin eventos verificables.
6. **Modelos y herramientas intercambiables:** `model_providers`, `model_routes`, `capabilities`; selección por capacidad, costo, privacidad y latencia, sin depender de un proveedor específico.
7. **Seguridad:** control de acceso servidor (RLS Supabase comprobada), segregación de Storage y búsquedas por organización, auditoría inmutable, permisos mínimos, cifrado/gestión de secretos, backups y restauración ensayada.
8. **Costos:** `usage_events`, `cost_limits`, `billing_plans` para controlar uso y prohibir cargos no autorizados. Precios comerciales y cobros quedan pendientes de validación.
9. **Experiencia:** un chat, voz, bandeja de aprobaciones, historial, panel de evidencias y estado separado para `draft`, `waiting_approval`, `queued`, `running`, `completed`, `failed`.

## Estados al 13-nov-2026
- ✅ **Implementado y probado en publicación:** navegación empresarial e infraestructura, menús moderados, formularios presentes en código, prototipos de flujo comercial, despliegue HTTP 200 y JS sintáctico.
- 🔵 **En desarrollo:** prueba real de formularios, experiencia en Motorola y conexión del modelo a soluciones empresariales.
- 🟡 **Pendiente de integración:** multiempresa segura, ofertas/presupuestos reales, aprobación formal, inventarios persistentes, CRM real, agentes especializados y automatizaciones completas.
- 🔴 **Bloqueado hasta contar con autorizaciones y controles:** datos privados de clientes, nómina/contabilidad, infraestructura productiva, despliegues de terceros, pagos y facturación.

## Orden de ejecución
**1.** Pruebas de interfaz en Motorola: acceso a infraestructura, selección, formulario de diagnóstico, plantilla CSV, chat y voz.
**2.** Diseño y ensayo de multiempresa con pruebas de aislamiento; no admitir datos de clientes reales hasta validar políticas.
**3.** Primer piloto acotado con empresa voluntaria y datos ficticios: inventario con alta/baja, historial y exportación auditada.
**4.** Flujo comercial de propuesta y aprobación con soporte de costos, permisos y estados reales.
**5.** Conexión del orquestador CONTROL 360: trabajo autorizado, evidencias, reintentos y supervisión.
**6.** Expansión modular: ventas/CRM, documentos, web/apps, infraestructura y modelos IA múltiples.

## Regla de veracidad
No convertir un enlace, formulario, respuesta HTTP o borrador en «IA operativa» o «servicio prestado». Cada módulo tendrá pruebas de negocio con datos autorizados y evidencia antes de pasar a confirmado.
