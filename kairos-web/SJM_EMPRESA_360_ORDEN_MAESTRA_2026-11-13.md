# ORDEN MAESTRA · SJM EMPRESA 360 IA EN COMTROL 360
Fecha: 13 de noviembre de 2026 (Colombia).
Prioridad absoluta: **Soluciones Empresariales 360°**.
Código existente: `andersonmartinezquiroga-ux/SM-Personal-Trainer/kairos-web/index.html`.
No se creó otra aplicación. Se preserva el front-end **COMTROL 360**, los proyectos SJM, el historial de navegador, las herramientas originales, la autenticación Supabase, el modo voz beta y el selector privado de archivos.

## Objetivo de producto
Una sola interfaz conversacional y accesible donde usuarios puedan solicitar soluciones empresariales con un ciclo verificable:
**necesidad → diagnóstico → propuesta → autorización → ejecución por herramienta → prueba → entrega → seguimiento**.
La interfaz es solo el punto de entrada; cada integración se habilitará únicamente después de una prueba real.

## Entrega de interfaz 13-nov-2026
Commit GitHub del código publicado: `ef19fdbcef976eb8675c9c45191d7d7aa7add2cf`.
Despliegue Vercel: `dpl_z2qfc9GsJP7f9ESYVJMqGvbU5mBr`, estado **READY**.
URL de producción: https://sjm-kairos-cerebro-web.vercel.app
Verificación: HTTP 200 tanto para dominio principal como URL de despliegue, JavaScript sintácticamente válido, 170957 bytes, diez módulos empresariales reconocibles en HTML.

**Menú principal, priorizado**: COMTROL 360 (chat), Soluciones Empresariales, Crear Web y Apps, Investigación y Proyectos, Diseño y Contenido, Automatizaciones y Tareas, Mis Empresas y Proyectos. Los módulos existentes del ecosistema quedan bajo «Otras herramientas SJM», sin perderse.
Menú desplegable superior y vista móvil adaptados; mantiene fuente grande y tema oscuro.

### Centro de 10 soluciones empresariales
1. Administración y operaciones.
2. Contabilidad, finanzas y proyecciones.
3. Nómina y recursos humanos.
4. Inventarios y compras.
5. Marketing y publicidad.
6. Ventas y CRM.
7. Auditorías y controles.
8. Investigación empresarial.
9. Proyectos y planes de negocio.
10. Automatización de procesos.

Cada tarjeta describe la necesidad y permite preparar un borrador de solicitud en chat. **No significa que el motor detrás ya pueda operar ese módulo.**

### Herramientas concretas añadidas a esta versión
- Ficha de diagnóstico empresarial de 3 campos (nombre comercial o alias opcional, sector, necesidad) que construye una solicitud revisable. No envía nada automáticamente.
- Descarga local de **plantillas CSV vacías** (inventario, flujo de caja, CRM). Las plantillas no calculan nóminas, no contabilizan operaciones ni constituyen bases empresariales conectadas.
- Catálogos de preparación de trabajo: web, apps, código, agentes IA, datos/paneles, pruebas; investigación, análisis, presupuestos y propuestas; informes, documentos, hojas de cálculo, presentaciones, publicidad, imágenes/video y traducciones.
- Sección de tareas para preparar programación recurrente y entrar a orquestación técnica ya existente. El formulario actual **no crea tareas**.

## Matriz de estados

### ✅ Implementado y comprobado (frontera de pruebas realizadas)
- Publicación de la aplicación **existente**, sin duplicación.
- Código actualizado en GitHub y despliegue de Vercel READY.
- HTML de producción servido con HTTP 200; comprobación sintáctica del script aprobada.
- Presencia comprobada en código público de los diez módulos, seis menús, ficha de diagnóstico y generadores de CSV.
- Conservación de autenticación existente, modo vista previa, proyectos y pantalla de voz; solo se comprobó presencia en código, no sesión funcional del usuario.

### 🔵 En desarrollo (requieren prueba funcional o conexión)
- Recorrido de interfaz con el usuario en Motorola: navegación, envío de diagnóstico, descarga CSV.
- Conversación en servidor y enrutamiento real al modelo/herramienta elegida para una solución empresarial.
- Gestión de inventario, marketing y proyecciones con datos reales y resultados demostrables.
- Integración de COMTROL con el orquestador de tareas, seguimiento de resultado y registro persistente.

### 🟡 Pendiente de integración
- Identidades de empresas, invitaciones, roles, tenencia multiempresa, RLS completo, almacenamiento por empresa y segregación de conversaciones.
- CRM real, ventas, inventario persistente, proyecciones y facturación conectada.
- Generación de Word, PDF, PPTX, apps, páginas y multimedia con herramientas instrumentadas y evidencia.
- Programador de automatizaciones desde chat con creación de ID, cancelación, historial, reintentos y límites.
- Motor de voz natural en tiempo real; hoy solo hay modo Web Speech beta de primer plano.

### 🔴 Bloqueado para operación comercial real hasta contar con controles
- Nómina y contabilidad sensibles: validación legal por jurisdicción, revisión profesional y autorización del titular.
- Auditoría formal y decisiones contractuales: flujos verificables, trazabilidad, permisos.
- Compartir datos reales de empresas clientes: no habilitar sin aislamiento de datos, políticas y controles.
- Autonomía manos libres con pantalla apagada: no certificable sin pruebas Android y motor de audio en tiempo real.

## Orden de ejecución propuesto
1. **Prueba real de interfaz** en Motorola en modo vista previa: menú, diagnóstico y archivos CSV; corregir fallas.
2. **Seguridad de clientes**: crear modelo de usuarios y empresas con políticas por empresa antes de admitir información sensible.
3. **Primer caso útil verificable**: inventario con CRUD protegido, historial de movimientos y exportación; o piloto de marketing con entregable verificable.
4. **Orquestador COMTROL**: de solicitud a autorización, ejecución, evidencia y estado, conectado a las herramientas existentes sin duplicarlas.
5. **Generación de informes y documentos** respaldada por herramientas reales.
6. **CRM, proyecciones, web y apps** con pruebas end-to-end.
7. **Nómina/contabilidad/auditorías** con cumplimiento legal, permisos y supervisión.
8. **Comercialización internacional**: aislamiento multiempresa y metering antes de establecer paquetes o suscripciones.

## Seguridad y honestidad comercial
El front-end actual conserva acceso principal a una cuenta específica del ecosistema SJM; **no es aún un SaaS multiempresa**. El código de vista previa es solo una demostración. No introducir datos bancarios, personales, laborales, contables ni clientes reales en la vista previa. Todas las operaciones sensibles deben ser revisables y autorizadas. Ningún botón que únicamente redacta un prompt puede presentarse como la ejecución de ese servicio.

No declarar autonomía total sin pruebas reales en Motorola y comprobantes.


## Ampliación — infraestructura, panel empresarial y experiencia comercial (13 noviembre 2026)

La aplicación única sigue alojada en `kairos-web/index.html` y publicada en https://sjm-kairos-cerebro-web.vercel.app. Se añadieron al front-end existente:

- **Infraestructura tecnológica:** menú para arquitectura, servidores, nube, alojamiento, redes, integraciones, seguridad, copias, despliegues y costos, con diagnóstico técnico guiado y plantilla CSV vacía. Es un **borrador**, nunca ejecución en servidores.
- **Contratación:** modalidades servicio puntual, paquete empresarial, servicio integral y suscripción a evaluar; el formulario prepara un diagnóstico y propuesta inicial, sin inventar presupuesto ni registrar aprobaciones.
- **Ciclo comercial:** elegir servicio → diagnóstico → propuesta y presupuesto → aprobación → ejecución y entrega → seguimiento. Las primeras fases solo generan solicitudes y el resto está pendiente de integración.
- **Panel por empresa:** entradas de panel, usuarios y roles, historial, entregables y archivos figuran como pendientes. El panel comercial multiempresa aún no existe como producto seguro.
- **Arquitectura de referencia:** motor IA intercambiable, conectores de herramientas, orquestación verificable, aislamiento por empresa, controles de seguridad y continuidad, y límites de costos. Es diseño de evolución, no funciones integradas y certificadas.
- **Integridad:** se conservaron chat, voz beta, portafolio SJM, plantillas, acceso existente, orquestación técnica y estilo oscuro con fuentes legibles.

### Estado explícito de esta ampliación

| Estado | Función |
|---|---|
| ✅ Publicado y comprobado por HTML/JS | Menú infraestructura, formulario de diagnóstico técnico, rutas comerciales, fichas de panel por empresa y arquitectura descriptiva. Producción responde HTTP 200 y el JavaScript se analizó sin errores sintácticos. |
| 🔵 En desarrollo | Primera entrega empresarial comprobable conectada a datos reales y a un proceso autorizado. Test de recorrido completo en Motorola aún pendiente. |
| 🟡 Pendiente de integración | Motor multimodelo, APIs empresariales, precios, contratos, facturación y motor real para automatizaciones en la UI. |
| 🔴 Restringido hasta aislamiento y autorización | Cuentas externas, empleados y clientes, nóminas, datos sensibles y cambios reales de infraestructura; requieren tenants, RLS, RBAC, auditoría, respaldos y pruebas de aislamiento. |

### Orden de implementación de backend comercial

1. Modelo de empresa/organización y usuario con permisos por rol, `organization_id` en tablas, políticas RLS, archivos separados y pruebas automáticas contra accesos cruzados.
2. Solicitud empresarial persistente: servicio, modalidad, alcance, consentimiento, estado y registro de cambios.
3. Diagnóstico técnico/comercial con información no sensible, presupuesto trazable y aprobación verificable antes de ejecutar.
4. Ejecución conectada al orquestador original CONTROL 360 (sin duplicar): id de tarea, permisos, reintentos, evidencias, estado real, factura solo si fue autorizada.
5. Primer piloto con datos ficticios y luego empresa voluntaria bajo acuerdos y autorización; empezar por inventarios o marketing, antes de nómina y contabilidad.

Nunca presentar la interfaz como SaaS ya protegido ni como trabajo empresarial ejecutado.


## Auditoría de madurez e integración COMTROL 360 — 14-nov-2026

Release de aplicación única: `kairos-web/index.html`, versión de tablero **v2.5**, commit `7184731dd67feb09da0224846fa8bdc1fafaeb21`, despliegue productivo en https://sjm-kairos-cerebro-web.vercel.app. Prueba técnica: respuesta HTTP 200, script válido, piezas anteriores de voz, chat, guía «Crear mi empresa» y controles de dictado preservadas. **Aún no hay prueba de usuario en Motorola para este panel.**

### Lo incorporado

1. **Tablero de madurez** dentro del módulo técnico CONTROL 360, sin otro proyecto ni menú lateral extra. Evaluación interna basada en diez áreas ponderadas, con la evidencia base, próximo bloqueo y aporte de cada área. Es una **estimación orientativa** y no un porcentaje objetivo de inteligencia o autonomía.
2. **Comprobación protegida bajo sesión** que consulta dos servicios ya existentes: `sjm_brain_hybrid_v1` (estado del cerebro) y `sjm_brain_plan_safe_v1` con `execute_read_only` (resumen Motorola, ejecutor, memoria y alertas). Verifica `readPerformed=true`, `readOnly=true`, `executedActions=0`. No ejecuta órdenes ni expone registros privados en la vista previa.
3. **Diez fichas de conocimiento por área empresarial**, en los módulos ya existentes: información mínima para comenzar, entregable esperado y validación/autorización. No constituyen una solución empresarial automatizada sin sus motores.
4. En «Mis Empresas y Proyectos» un acceso al progreso técnico de COMTROL, conservando el apartado de seguridad multiempresa pendiente.

### Evaluación de madurez, 37/100 puntos posibles

| Componente | Puntos | Fundamento de evaluación |
|---|---:|---|
| Interfaz y accesibilidad | 9/10 | Publicada y con voz beta; faltan pruebas de uso en Motorola. |
| Chat y cerebro IA | 5/15 | Mentor protegido; modelos generativos bajo configuración, sin equiparar a ChatGPT. |
| Orquestación CONTROL 360 | 7/15 | Colas, cron y registros, autonomía integral parcial. |
| Ejecutor web | 5/10 | Trabajos internos y errores verificables; pendiente resiliencia/acciones reales autorizadas. |
| Motorola y voz | 4/10 | Acuses parciales; todavía no prueba de operación constante ni voz natural en segundo plano. |
| Servicios empresariales | 2/15 | Catálogos/guías; ERP y CRM reales sin conectar. |
| Seguridad multiempresa | 0/10 | Sin aislamiento completo de clientes, roles ni RLS probadas por empresa. |
| Entregables profesionales | 1/5 | CSV y borradores locales, faltan Word/PDF/PPTX integrados. |
| Memoria y trazabilidad | 3/5 | Memoria operativa y registros existentes, sin memoria empresarial separada. |
| Contratación y seguimiento | 1/5 | Formulario de diagnóstico; aprobaciones/entregas facturables no integradas. |
| **TOTAL** | **37/100** | Estimación interna, no prueba integral. |

### Datos técnicos consultados el 14-nov-2026

- `sjm_ops.delivery_plan`: 1 de 8 fases figura `comprobado` (fase 1), siete `parcial`.
- `sjm_ops.block1_subpoint_progress_v1`: los diez subpuntos del Bloque 1 figuran `verified`. No generalizar ese resultado a los ocho bloques.
- `sjm_ops.browser_jobs`: 183 registros, 146 en estado `done` y 37 `failed`. Son trabajos de inspección/prueba, NO postulaciones reales.
- `public.sjm_kairos_phone_jobs_v1`: 80 registros, 49 `completed`, 31 `failed`. Son órdenes de prueba; falta confiabilidad continua.
- `sjm_ops.mentor_workflows`: 1 `completed`, 5 `blocked`; no se puede afirmar orquestación completa del Mentor.
- `sjm_ops.kairos_phone_health_v1`: conexión reportada `online` a las 09:29 hora de Colombia; un heartbeat puntual no certifica continuidad.
- Datos cambiantes: evitar conservar estas cifras como si fueran estado del momento. Consultarlas de nuevo mediante fuentes protegidas.

### Prioridad de desarrollo real (sin inversión obligatoria)

1. **Prueba móvil de la nueva pantalla** en navegador Chrome Android con sesión autorizada y evidencia visible.
2. **Diagnóstico del ciclo completo** de una orden (enviar → recibir → ejecutar → ACK → registro), sin ordenar operaciones sensibles.
3. **Primer servicio empresarial real con seguridad**: piloto de inventarios con modelos de datos y roles, movimientos auditables, CSV e informes. Solo con datos sintéticos hasta verificar aislamiento de clientes.
4. **Motor de creación de entregables** Word/PDF/Excel y archivos del usuario con controles y evidencia.
5. **Cerebro multimodelo + herramientas** con selección explícita, evaluación, costos y permisos.
6. **Identidad empresarial**: modelo por organización con RLS, pruebas de filtración cruzada, registros y consentimientos antes de clientes externos.
7. **Comercialización** únicamente después de casos reales probados y cálculo de costos.

**No certificar 100 %, no presentar simulación como resultado y no duplicar proyectos ni tareas programadas existentes.**


## Primera operación empresarial persistente — Inventarios (14 noviembre 2026)

Se implementó y publicó en la **aplicación existente** un piloto propietario de inventarios. Está en `Soluciones Empresariales → Inventarios y Compras → Abrir inventario operativo`. Usa **las dos tablas nuevas de Supabase** `public.sjm_business_inventory_items_v1` y `public.sjm_business_inventory_movements_v1`, más la función transaccional `public.sjm_inventory_register_movement_v1`.

Capacidades desarrolladas: crear productos identificados por SKU y umbral, registrar entradas y salidas, rechazar stock negativo, impedir repetición de solicitudes mediante clave única, calcular existencias desde movimientos, mostrar alertas y descargar CSV de existencias/comprobantes. No modifica inventario en modo vista previa, ni genera productos automáticamente.

**Evidencia técnica de publicación:** despliegue de Vercel `dpl_7UEgmZ8oMAd2srMWcbQRsgEDasQc` en estado READY, URL de producción HTTP 200, JavaScript sintácticamente válido. Migraciones Supabase `sjm_empresa360_inventory_pilot_owner_isolated_20261114` y `sjm_empresa360_inventory_idempotent_owner_rpc_v2` correctamente aplicadas. RLS activada en ambas tablas, `anon` sin SELECT, `authenticated` sin INSERT directo al kardex y RPC autorizada. Al realizar la comprobación había **0 productos y 0 movimientos**: es honesto **no declarar prueba de uso real**.

**Pendiente crítico para cerrar esta fase:** entrar desde Motorola con sesión válida, crear SKU ficticio, realizar entrada, salida correcta, salida imposible, alerta, exportación y recarga, dejando comprobantes. Guía detallada: `kairos-web/COMTROL_INVENTARIO_PILOTO_2026-11-14.md`. SQL reproducible: `kairos-web/database/20261114_sjm_inventory_pilot.sql`. La empresa multiusuario/multi-tenant **no existe todavía**; solo aislamiento por usuario.

**Porcentaje:** se mantiene la evaluación de 37/100 hasta que una prueba autenticada confirme el ciclo completo. El nuevo módulo no autoriza elevar porcentajes ni afirmar comercialización lista.


## Segunda operación empresarial persistente — Ventas y CRM (14 noviembre 2026)

Se implementó y publicó una sección **«Ventas y CRM · Piloto con datos protegidos»** en la aplicación única COMTROL 360, con botón «Abrir CRM operativo» en la tarjeta Ventas y CRM.

**Operativo a nivel de código y base de datos:** crear una oportunidad con alias ficticio (sin nombres/contactos), descripción y monto estimado COP; avanzar entre seis estados; registrar cada transición con comprobante y clave de idempotencia; lectura de historial; resumen de oportunidades abiertas y valor estimado **excluyendo ganadas/perdidas**; descarga de dos CSV. No hay facturas, pagos, correos ni servicios contratados.

**Backend creado en Supabase existente:** `public.sjm_business_crm_opportunities_v1`, `public.sjm_business_crm_stage_events_v1`, `public.sjm_crm_advance_stage_v1`, migración `sjm_empresa360_crm_owner_isolated_pilot_20261114`. RLS por `owner_id=auth.uid()`; anónimo sin lectura; `authenticated` sin UPDATE directo de oportunidades ni INSERT al historial; RPC autenticada y transaccional para cambios de etapa.

**Pruebas:** transacción de QA con ROLLBACK validó creación ficticia, cambio de etapa, clave repetida, prohibición UPDATE y acceso de un segundo usuario. Verificación posterior: **cero oportunidades y cero eventos guardados**; pruebas de seguridad RLS y privilegios positivas. Versión final desplegada Vercel `dpl_7YUuCCcb3rgqUaJ1DQGTF2tCkpBm` estado READY; dominio público HTTP 200; código JS validado; se preservaron inventario, dictado, guía de creación de empresas, CONTROL y voz.

**Prueba aún pendiente:** sesión auténtica en Motorola y verificación de pantalla, creación ficticia, cambios de etapa, historial CSV y persistencia. No declarar CRM listo para datos de clientes reales. El diseño sigue siendo **un usuario/titular**, no espacios protegidos por empresa.

**Documentos:** `kairos-web/database/20261114_sjm_crm_pilot.sql` y `kairos-web/COMTROL_CRM_PILOTO_2026-11-14.md`. Mantener la evaluación orientativa global **37/100** hasta completar pruebas de uso. Próximo desarrollo prioritario: prueba móvil E2E, paginación real, modelo `organization_id` y control de permisos por empresa antes de CRM comercial real.


## Tercera capacidad persistente — Espacios privados por empresa y proyectos (14 noviembre 2026)

**Aplicación única conservada:** `kairos-web/index.html`, implementación `COMTROL · Espacios privados por empresa v2.8`, despliegue Vercel `dpl_BYUT8uc4An6ZjockEtQAciAf5ahr` READY, dominio de producción https://sjm-kairos-cerebro-web.vercel.app, comprobación HTTP 200, JavaScript válido. No hubo duplicación de aplicaciones.

**Nueva función:** `Mis Empresas y Proyectos → Espacios privados por empresa`. El titular autenticado puede crear hasta 20 alias de empresa y asociar proyectos borrador con nombre, descripción y fase inicial, consultar esos espacios y registrar más proyectos. Se utilizan nombres ficticios y no se solicitan identificadores ni información personal de terceros. La vista previa no consulta ni guarda información privada.

**Base de datos real** existente Supabase (misma cuenta y proyecto de CONTROL 360), migración `sjm_empresa360_org_workspace_and_project_rls_20261114`:
- `public.sjm_business_organizations_v1`: espacios organizacionales.
- `public.sjm_business_org_members_v1`: membresías y roles `owner/admin/viewer`; solo el creador queda como `owner`. NO hay invitaciones habilitadas.
- `public.sjm_business_org_projects_v1`: proyectos registrados con `org_id`, permisos select por membresía e insert solo para miembros owner/admin.
- `public.sjm_business_member_role_v1`: consulta protegida de rol asociada al usuario autenticado.
- `public.sjm_business_create_org_v1`: creación transaccional de espacio y membresía `owner`; no se permite INSERT directo de organizaciones ni membresías por clientes web.
- RLS habilitada en las tres tablas, lectura anónima revocada; no se puede invitar a un usuario desde el front-end.

**Prueba técnica reversible realizada:** se creó empresa ficticia y su proyecto dentro de una transacción, se verificó rol `owner`, lectura propia, ausencia de lectura cruzada por otra identidad simulada y rechazo de inserción en la empresa ajena; `ROLLBACK` sin registros persistentes. Lectura posterior: **0 empresas, 0 membresías, 0 proyectos**, RLS habilitada en tres tablas, `anon` sin acceso, `authenticated` sin inserción directa de empresas ni invitaciones. Pruebas independientes de UI y sesión real en Motorola: **PENDIENTES**.

**Limitación significativa:** el nuevo aislamiento de organización aplica a empresas y **proyectos de prueba**, pero los módulos anteriores de inventarios y CRM siguen aislados por `owner_id` (cuenta) y **NO tienen `org_id`**. No permitir información empresarial real de clientes ni presentar el producto como plataforma SaaS multiempresa hasta migrar datos, roles, archivos y permisos, con pruebas adversariales y entrega real en Motorola.

**Siguientes puntos de trabajo prioritarios:** (1) prueba auténtica de creación de espacio y proyecto en Motorola; (2) asociar inventario y CRM a organizaciones verificadas manteniendo integridad y sin romper datos; (3) roles con invitaciones solo bajo aprobación y auditoría; (4) pagos, contratos, documentos y orquestación únicamente después de autorización y pruebas completas.

Se mantiene la evaluación orientativa **37/100** hasta validar el piloto de punta a punta; nunca declarar autonomía o madurez mayores solo por una migración o pantalla.


## Cerebro IA independiente y planificador local — 14 noviembre 2026

**Objetivo fijo SJM:** el producto COMTROL 360 debe llegar a poder operar sin suscripción a ChatGPT, con interfaz sencilla de conversación y herramientas propias. Eso no significa prometer paridad actual con ChatGPT ni gratuidad asegurada de la inferencia; un modelo abierto puede necesitar nube, GPU o servidor.

**Trabajos realizados sobre las aplicaciones y servicios existentes (sin crear otro proyecto):**
1. Edge Function `sjm_brain_hybrid_v1` **versión 7** desplegada ACTIVE con verificación JWT y el mismo control de acceso del propietario. Se preservaron rutas `status` y `ask` y se añadió `ask_independent` para respuestas de un modelo externo independiente sin basarlas en la respuesta del Mentor. La ruta no ejecuta herramientas, pagos, postulaciones ni acciones externas; exige consentimiento expreso para enviar solo la pregunta.
2. Adaptador con endpoint HTTPS fijado **en secretos del servidor**, no por el navegador. Rechaza endpoints directos de OpenAI/ChatGPT, direcciones locales inseguras y preguntas con patrones de credenciales. Verificar el proveedor real y su modelo antes de declarar independencia; un intermediario podría ocultar el origen. `status` informa `independent_model_configured`, `independent_model_name` y host del proveedor únicamente a usuario autorizado. `independent_self_test` contiene políticas sin consumo de IA.
3. Interfaz `kairos-web/index.html` añadió selector `CONTROL · Supervisión` / `COMTROL · IA independiente`, consentimiento por cada pregunta, mensaje claro cuando no está configurado, y prueba de seguridad desde la propia pantalla. El modo de conversación por voz sigue usando Mentor (evita enviar automáticamente grabaciones ambientales al proveedor).
4. Generador **local sin ChatGPT** en guía `Crear mi empresa`: a partir de los ocho pasos del usuario, produce plan estructurado Markdown de estrategia, mercado, finanzas sin cifras inventadas, legalidad, herramientas, lanzamiento y 30 días. Es una **plantilla programada**, NO un modelo generativo y NO verifica datos externos.
5. Código de la función preservado en el repositorio `kairos-web/supabase/functions/sjm_brain_hybrid_v1/index.ts`. Manual de configuración, seguridad y pruebas en `kairos-web/COMTROL_CEREBRO_INDEPENDIENTE_2026-11-14.md`.

**Evidencia técnica:**
- Supabase: `sjm_brain_hybrid_v1` v7 ACTIVE, JWT=true, código fuente consultado después del despliegue.
- Vercel: `dpl_4g2uJP8oVL6RCM9gnfhUE2EpFedM` READY, versión productiva HTTP 200, JavaScript sintácticamente válido y módulos previos conservados.
- Generador local ensayado con empresa ficticia de zapatos: produjo resumen, mercado, localización, plan y avisos; ninguna llamada de red.
- Prueba aislada de reglas del adaptador: 8/8 casos mediante simulador URL en V8; NO reemplaza prueba HTTP autenticada a la función Supabase ni inferencia.
- **PENDIENTE CRÍTICO:** verificar un proveedor/modelo **realmente independiente y, si se elige, sin pagos obligatorios**, configurarlo en secretos del servidor y ejecutar una respuesta E2E con cuenta autorizada y consentimiento, sin exponer claves. No afirmar que el chatbot general ya usa un LLM independiente hasta completar esos pasos.
- No se ha medido oficialmente el porcentaje. Conservar la referencia interna `37/100` antes de pruebas integrales, sin aumentarla por diseño o código no probado en dispositivo real.

**Próximas prioridades:** escoger inferencia viable sin pago obligatorio o autoalojamiento con recursos SJM; configurar modelo y confirmar respuesta real; habilitar memoria conversacional en backend separada por usuario/organización; preservar autorización para herramientas; pruebas de Motorola y evaluación de seguridad multiempresa.
