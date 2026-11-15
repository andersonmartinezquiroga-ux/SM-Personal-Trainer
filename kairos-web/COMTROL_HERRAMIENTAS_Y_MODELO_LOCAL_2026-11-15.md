# COMTROL 360 · Herramientas independientes y modelo abierto local · 15-nov-2026

**Producto:** la misma aplicación `kairos-web/index.html` y el Supabase SJM CONTROL 360 existente. No se creó otra aplicación ni suscripción.

## Implementaciones publicadas

### 1. Calculadora genuinamente local
En el chat: **Herramientas sin ChatGPT → Calcular**. Evalúa `+`, `-`, `*`, `/`, decimales, paréntesis y `%` (significa dividir entre 100), sin `eval()`, sin ChatGPT y sin red. Rechaza operadores inválidos, divisiones entre cero y magnitudes excesivas. Funciona incluso en vista previa. Se probaron 14 casos de expresiones normales y erróneas.

### 2. Consulta enciclopédica pública (no una búsqueda web general)
En el chat: **Herramientas sin ChatGPT → Buscar conocimiento público**. Requiere sesión autorizada y confirmación para enviar **únicamente el término** a Wikipedia en español. Acción del servidor `research_public` dentro de Edge `sjm_brain_hybrid_v1` versión **9**, con el control del propietario ya existente. Intenta devolver hasta tres artículos, resumen breve y URL de la fuente; nunca genera fuentes inventadas. Ninguna IA generativa recibe estas consultas y no se ejecutan acciones externas, salvo consultar la fuente pública.

**Estado de comprobación:** código de ruta desplegado y front-end publicado; **aún no hay E2E autenticada del servidor contactando Wikipedia**. Si la fuente no responde, la interfaz comunica error, sin inventar resultados. No afirma verificar noticias, precios actuales, oportunidades, convocatorias ni documentación empresarial.

### 3. IA local experimental abierta, de verdad generativa si se logra cargar
Tercera opción de chat **COMTROL · IA local**, separada de CONTROL y COMTROL IA nube. Utiliza [WebLLM](https://webllm.mlc.ai/docs/user/get_started.html) de MLC AI, con modelo oficial `SmolLM2-360M-Instruct-q4f32_1-MLC` de la [lista pública de modelos](https://github.com/mlc-ai/web-llm/blob/main/src/config.ts). Según esa lista, el modelo necesita aprox. **580 MB de memoria gráfica**; el tamaño de descarga y memoria real dependerán de archivos, navegador y GPU.

- **No descarga nada al abrir la aplicación.** El usuario pulsa **Comprobar mi dispositivo**, después **Descargar e iniciar IA local** y confirma descarga grande, consumo de batería/datos y posibilidad de incompatibilidad.
- El motor JavaScript se importa únicamente al pulsar, con `https://esm.run/@mlc-ai/web-llm`.
- El modelo genera respuesta directamente mediante `localModelEngine.chat.completions.create`, sin servidor de inferencia o token de ChatGPT. Las bibliotecas y los pesos deben descargarse de CDN/Hugging Face. Cuidado con conexiones móviles de datos y políticas de descarga.
- Mantiene como máximo dos intercambios anteriores del **propio modo local**; **no** pasa reportes del Mentor, códigos del Motorola ni otros chats al modelo.
- Botón **Liberar memoria**; al cerrar sesión también se intenta descargar el modelo de memoria.
- No ofrece llamadas de voz manos libres conectadas a la IA local todavía; permite escribir o dictar con el micrófono del navegador.
- Modelo pequeño experimental: puede inventar o equivocarse; no equivale a ChatGPT, y no usa herramientas, inventarios, ERP ni navegación por sí mismo.
- El modelo abierto no necesita suscripción a ChatGPT, pero **puede consumir datos de internet, espacio y recursos del dispositivo**.

**Estado de prueba:** JS validado, pantalla publicada, ejemplo de uso con **motor simulado** comprobó 11 casos (sin acceso a datos del Mentor, sin nube generativa, límite de mensajes, etc.). **NO se descargó, ejecutó ni probó el modelo real en Motorola.** No declarar IA local plenamente funcional ni paridad con ChatGPT.

## Evidencia y mantenimiento
- Despliegue principal: `dpl_jFJ8JskUkGq9CZEtJXZxs95QQxTM` estado READY, URL canónica https://sjm-kairos-cerebro-web.vercel.app, HTTP 200 y JavaScript sintácticamente válido. Conservados inventarios, CRM, espacios empresariales, dictado, memoria, cerebro y guía Crear mi empresa.
- Supabase: `sjm_brain_hybrid_v1` v9 ACTIVE, JWT habilitado, nuevo servicio de lectura pública con autorización. Código fuente actualizado: `kairos-web/supabase/functions/sjm_brain_hybrid_v1/index.ts`.
- Pruebas repetibles: `node kairos-web/tests/independent_tools_smoke.mjs` (sin conexión ni descarga). Son pruebas de lógica, no E2E en dispositivos.

## Próximas pruebas para acreditar este avance
1. Abrir en Motorola con Chrome: **COMTROL · IA local → Comprobar mi dispositivo**. Anotar si WebGPU está disponible.
2. Si es compatible, usar **Wi-Fi** y almacenamiento suficiente; confirmar la carga, esperar y preguntar algo simple. Guardar respuesta, tiempo de carga y error si ocurre.
3. Pulsar **Liberar memoria** y asegurar que la aplicación no se ralentiza después.
4. Probar una operación numérica sin iniciar sesión, desde vista previa (por ejemplo `(25000+5000)*2`, resultado `60000`).
5. Con sesión autorizada, buscar `Calzado` en Wikipedia y abrir fuentes; si falla, guardar mensaje de error para corregir acceso al proveedor.
6. Mantener auditoría de privacidad, permisos, memoria y costos antes de hacer del modelo local una opción predeterminada.

**Criterio:** seguir aproximadamente en 37–40 % orientativos de desarrollo global hasta demostrar el modelo y las herramientas en el Motorola y la IA general con tareas reales. Las pantallas no elevan ese porcentaje por sí solas.
