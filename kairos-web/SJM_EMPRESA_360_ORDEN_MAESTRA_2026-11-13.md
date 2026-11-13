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
