# KAIRÓS 360 · actualización de navegación y archivos (13-nov-2026)

Repositorio existente: `andersonmartinezquiroga-ux/SM-Personal-Trainer`; archivo `kairos-web/index.html`.
Último commit: `b96a60eafe3ac8a71040d4528a61714bbacd8669`.
Vercel producción: `dpl_EeR3qTArrFCNBrRZjnZBtFwq5q7V`.
Dominio: https://sjm-kairos-cerebro-web.vercel.app

## Experiencia de interfaz
- Chat centrado en conversaciones, con letra legible, identidad azul/plata, encabezado desplegable «KAIRÓS 360», menú superior «⋯» y barra lateral que abre/cierra en móvil/escritorio.
- Barra lateral conserva navegación por proyectos SJM e historial; 14 fichas de proyecto, filtros y notas locales.
- Menú superior: Conversación, Mis proyectos, CONTROL 360, Mis archivos, Radares; «⋯» ofrece nueva conversación, exportación TXT, copiar respuesta, escuchar, archivos y configuración.
- El botón «＋» en la barra inferior tiene cuatro opciones: Archivos (todos los tipos del dispositivo), Fotos, Cámara, Mis archivos guardados.
- Se admiten hasta cinco archivos seleccionados por tanda y 15 MiB por archivo; se muestran nombre, tamaño y estado. Seleccionar NO carga ni envía automáticamente.

## Almacenamiento
- Se creó bucket privado `kairos-private-files` en el proyecto Supabase existente `dfqjwlsgqetyxdrsuviy`, con límite de tamaño de 15 MiB.
- Tres políticas de storage.objects verificadas: INSERT, SELECT y DELETE únicamente para usuario autenticado propietario y archivos bajo su prefijo de UUID. No se otorgó acceso anónimo ni pública lectura.
- En sesión autenticada, el botón explícito «Guardar en Mis archivos» invoca el almacenamiento protegido. «Mis archivos» permite listar, descargar y eliminar con confirmación.
- En vista previa con código `SJM-360-VISTA`, los archivos únicamente se seleccionan localmente; no se suben. La conexión real a archivos privados, el Mentor y los expedientes requiere autenticación en Supabase. **No se implementó la lectura de adjuntos por la IA ni análisis de PDF/Word/Excel**.

## Comprobaciones
- HTTP 200 del dominio de producción y URL de despliegue.
- JS incluido: comprobación sintáctica satisfactoria.
- Confirmado presencia de menú superior, menú ⋯, botones Archivos/Fotos/Cámara, código de vista previa, Supabase Auth y función de subida de Storage en el HTML de producción.
- Bucket privado y políticas RLS verificadas desde Supabase.
- **No probado**: clics y recorrido en Motorola; subida real con sesión autenticada; voz en móvil. No afirmar funcionalidades end-to-end ni autonomía plena.
