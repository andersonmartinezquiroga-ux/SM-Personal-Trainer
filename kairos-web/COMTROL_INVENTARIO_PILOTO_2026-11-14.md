# SJM Empresa 360 IA · Inventario piloto operativo

**Fecha:** 2026-11-14. **App existente:** `kairos-web/index.html` · https://sjm-kairos-cerebro-web.vercel.app. **Backend:** Supabase del CONTROL 360 existente, sin duplicar proyecto.

## Qué quedó técnicamente publicado
- Se incorporó un panel desplegable **«Inventario operativo · Piloto con base de datos»** en **Soluciones Empresariales 360°**, accesible también desde la tarjeta **Inventarios y Compras**.
- El titular autenticado puede crear un SKU, descripción, unidad y umbral de alerta; movimientos de entrada y salida se registran por RPC transaccional con verificación de existencias y prevención de repetidos.
- El reporte muestra existencias y alertas, historial de hasta 30 movimientos recientes y exporta CSV de existencias e historial del conjunto cargado.
- **No permite introducir cambios desde vista previa.** No se han creado productos ficticios automáticamente en las cuentas.
- RLS para cada owner, sin lectura anónima de artículos/movimientos y sin INSERT directo de movimientos para authenticated. RPC firmada usa `auth.uid()` y propietario del producto.
- El código fuente y la migración reproducible están en el repositorio existente, bajo `kairos-web/database/`.

## Prueba manual mínima en Motorola (pendiente)
1. Abrir la aplicación en **Chrome Android**, iniciar sesión autorizada (NO código de vista previa).
2. Ir a **Soluciones Empresariales → Inventarios y Compras → Abrir inventario operativo**.
3. Crear producto **ZAP-TEST-001**, **Zapato ficticio**, unidad `par`, alerta `2`.
4. Registrar **Entrada 10**; comprobar que indique **10 pares**.
5. Registrar **Salida 3**; comprobar que indique **7 pares**.
6. Intentar **Salida 8**; debe rechazar por stock insuficiente; verificar que continúe en **7 pares**.
7. Registrar **Salida 5**; comprobar que quede **2 pares** y aparezca alerta de bajo stock.
8. Descargar **CSV existencias** y **CSV movimientos**, comprobar números e identificadores.
9. Actualizar página, iniciar sesión si hace falta, comprobar persistencia de productos/movimientos.
10. Verificar con otra cuenta autenticada **SIN acceso al proyecto** que no se revelen productos ni historial (RLS owner_id). Requiere prueba controlada, no se certifica por la declaración del esquema.

## Evidencias / límites verificados
- Implementación SQL: migraciones creadas correctamente en Supabase.
- Inspección de privilegios: **RLS habilitada** en ambas tablas, usuario `anon` sin permiso SELECT; usuario autenticado **sin INSERT directo** en el kardex y con RPC autorizada.
- Aplicación y dependencias previas publicadas: desplegada en Vercel, HTTP 200 y análisis sintáctico JS correcto.
- **Pendiente**: pruebas completas de API con el token real del propietario y prueba de uso en Motorola; no declarar «funcionamiento integral confirmado» sin esto.
- Prototipo individual: **NO es ERP multiempresa ni cumple todavía permisos de clientes, respaldo comercial, pagos o auditoría legal**.
- Límite de 1.000 filas de vista; cuando se alcanza se bloquea exportación precisa y se exige paginación.

## Próximos trabajos
1. Ejecutar y registrar el piloto autenticado de diez pasos.
2. Incorporar paginación real del historial para evitar resultados truncados y procesos para reintentos no duplicados.
3. Crear espacios multiempresa con `organization_id`, roles, RLS tenant y pruebas de aislamiento cruzado.
4. Extender CRM/ventas y documentos facturables, permisos y aprobaciones.
5. Mantener separado **avance de desarrollo de COMTROL** y **pruebas de autonomía de CONTROL 360**. No inflar el porcentaje por una pantalla nueva.
