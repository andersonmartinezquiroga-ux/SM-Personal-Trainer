# COMTROL 360 · Ventas y CRM · Piloto 14 noviembre 2026

## Estado
Nueva capacidad **publicada** en la MISMA app web SJM COMTROL 360; módulo desplegable en **Soluciones Empresariales → Ventas y CRM → Abrir CRM operativo**, sin crear segundo proyecto.

El titular autenticado puede registrar una oportunidad con **alias de empresa ficticia**, descripción corta y valor estimado en COP; consultar el estado del embudo; avanzar manualmente entre etapas (Nuevo, Contactado, Propuesta, Negociación, Ganado, Perdido); consultar un historial de cambios con identificadores verificables y exportar oportunidades e historial a CSV.

**No** se gestionan datos personales reales ni se envían correos, se crean facturas, se realizan cobros o se contabilizan ventas. Todo valor indicado es una previsión y no ingreso recibido.

## Seguridad
- Tabla `public.sjm_business_crm_opportunities_v1`: RLS, `owner_id=auth.uid()`, authenticated **solo SELECT/INSERT** y la etapa inicial debe ser `nuevo`.
- Tabla `public.sjm_business_crm_stage_events_v1`: historial de cambios, RLS SELECT para el mismo propietario, **no INSERT directo** para usuarios.
- RPC `public.sjm_crm_advance_stage_v1`: exige sesión y que la oportunidad pertenezca a la cuenta; bloquea la repetición de una misma clave sin duplicar cambios; actualización de etapa + registro de evento en una sola transacción.
- Vista previa sin acceso a datos protegidos. Se limita a 1.000 elementos o eventos y se bloquean exportaciones incompletas. No existe aún aislamiento de múltiples empresas de un mismo usuario.

## Evidencia técnica y prueba pendiente
- Migración aplicada en el Supabase existente: `sjm_empresa360_crm_owner_isolated_pilot_20261114`.
- Prueba de base de datos con transacción reversible: alta ficticia, cambio de etapa, prevención de duplicación, RLS y denegación de cambios directos y cruzados; `ROLLBACK` sin dejar registros.
- Comprobación posterior: 0 oportunidades/0 eventos; RLS habilitado en ambas tablas, `anon` sin SELECT ni ejecución de RPC, `authenticated` sin UPDATE directo ni INSERT al historial; RPC autorizada.
- Front-end publicado en producción en https://sjm-kairos-cerebro-web.vercel.app, HTTP 200 y JS analizado. Se verificó preservación de inventario, dictado, guía Crear mi empresa, panel de control y chat/voz.
- **FALTA**: E2E con sesión auténtica desde Chrome Android/Motorola y control visual de persistencia; sin ello el piloto NO queda certificado como listo para clientes reales.

## Protocolo de prueba en Motorola
1. Abrir COMTROL 360 con sesión autorizada del titular, NO en modo vista previa.
2. Entrar en Soluciones Empresariales → Ventas y CRM → Abrir CRM operativo.
3. Crear alias `Empresa ficticia de zapatos`, oportunidad `Pedido piloto 10 pares`, valor `250000 COP`.
4. Verificar que aparezca en etapa **Nuevo**, con **valor potencial** no facturado.
5. Cambiar etapa a **Contactado** y comprobar comprobante nuevo en historial.
6. Cambiar a **Propuesta**, comprobar historial de 2 etapas y CSV.
7. Cerrar y reabrir la aplicación; confirmar persistencia.
8. Verificar que otra sesión autenticada NO pueda leer o cambiar el registro de este usuario (RLS). No usar identidades de clientes reales para probar.

## Próximos pasos
- Completar E2E con sesión real, automatizar pruebas de regresión y evidencias.
- Paginación de historiales, recuperación de errores, valoración consistente y permisos.
- Crear entidad **organización** con roles y separación multiempresa, políticas RLS y comprobación adversarial de aislamiento antes de admitir información de clientes reales.
- Integrar cotizaciones, productos, entregables y motor IA intercambiable con aprobaciones explícitas.
- Mantener la evaluación global **37/100** hasta evidencias adicionales; ninguna pantalla nueva eleva por sí sola la madurez de la IA.
