# COMTROL 360 — Modo conversación por voz (beta) · 13 noviembre 2026

## Qué se cambió
Se mantuvo la aplicación y proyecto existentes de Vercel: `sjm-kairos-cerebro-web`.
Repositorio: `andersonmartinezquiroga-ux/SM-Personal-Trainer`.
Archivo: `kairos-web/index.html`.
Commit: `693ce4c135d021e965c1b909e74d5bc21b43a5be`.
Despliegue de producción: `dpl_GbWAaS9d1krvV7TBnV85neKyA6SB` (READY).
URL: https://sjm-kairos-cerebro-web.vercel.app

Se agregó:
- Botón de onda de voz en encabezado y barra de escritura, y opción «Iniciar llamada de voz» en menú ⋯.
- Pantalla de llamada en modo oscuro con esfera de voz COMTROL 360, estado visual, silenciar/activar micrófono, subtítulos, repetir respuesta, opciones de voz del dispositivo y colgar.
- Reconocimiento de voz español (es-CO) mediante Web Speech API con permiso del usuario.
- Intento de reanudación automática del micrófono al finalizar cada respuesta, mientras la app permanece abierta y el navegador lo permita.
- Respuestas habladas mediante speechSynthesis del sistema (provisionales), sin exponer nuevas claves o secretos.
- Comando hablado para terminar llamada. La vista previa produce respuestas de demostración y no usa datos privados.
- Las solicitudes reales pasan por la función existente de Mentor con autenticación; no se habilita acceso privado usando el código de vista previa.
- No se tocaron radar, postulaciones, archivos ni estado de ejecución.

## Restricciones de operación que deben mostrarse honestamente
- **No se implementó voz en tiempo real de baja latencia ni conversación simultánea de doble vía** comparable a ChatGPT Live.
- **No** se garantiza comunicación con pantalla bloqueada o aplicación en segundo plano, ni detección permanente sin iniciar la función.
- El modo usa la voz disponible del navegador/dispositivo, **no voz natural premium del Mentor**.
- El navegador puede exigir nuevos gestos o permisos y puede no admitir reconocimiento continuo.
- El modo de vista previa no accede a Supabase ni ejecuta operaciones.
- Para lograr manos libres 24/7 y voz natural de alta calidad se requiere integrar una solución de audio en tiempo real con permisos de Android y prueba en Motorola.

## Evidencia y pruebas
- El módulo JavaScript nuevo superó comprobación de sintaxis.
- Vercel marcó el despliegue de producción READY.
- Dominio público y URL de despliegue respondieron HTTP 200, 139272 bytes.
- Contenido publicado verificado: todos los botones de la llamada, motor Web Speech, código de vista previa, catálogos de proyectos, modo oscuro y retoques tipográficos.
- **No verificado** aún: permiso de micrófono, reconocimiento en un Motorola, turnos sin pulsación, respuestas habladas y calidad de audio reales. No declarar autonomía ni voz natural certificadas.
