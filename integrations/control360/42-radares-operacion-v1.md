# SJM CONTROL 360 — Contrato operativo de 42 radares (v1)

Fecha: 2026-11-10. Estado: DISEÑO VERSIONADO, NO DESPLIEGUE. Sin coste obligatorio.

## Regiones
1 Latinoamérica y Caribe; 2 EE.UU. y Canadá; 3 Europa ampliada; 4 Oriente Medio y Norte de África; 5 Asia y Oceanía; 6 África subsahariana.

## Siete responsabilidades por región (42 carriles lógicos)
1. Empleo y clientes de entrenamiento (remoto o local elegible).
2. Donación DEFINITIVA de PC/GPU y componentes (sin préstamo, sin compras).
3. Subvenciones, financiación no reembolsable y premios.
4. Alianzas B2B, patrocinios y distribución de SJM Human Performance 360.
5. Apoyos técnicos: cloud, hardware, prototipado, laboratorios.
6. SJM Universal Translator: incubación, accesibilidad, socios.
7. Seguimiento de expedientes, respuestas y vencimientos de la región.

Un carril es una cola de trabajo, NO un agente ejecutándose 24/7. No afirmar 42 procesos activos sin métricas de ejecución.

## Máquina de estados y pruebas
IDENTIFICADO → ELEGIBILIDAD_VERIFICADA → PREPARADO → ENVIADO_CON_COMPROBANTE → RESPUESTA → DECISIÓN. Estados terminales separados: DESCARTADO (no elegible), VENCIDO (plazo comprobado), ARCHIVADO (historial preservado), RECHAZADO, APROBADO. Una consulta enviada NO es candidatura enviada. Una entrevista ya realizada NO es entrevista pendiente. Video enviado NO es selección. No deducir éxito de una recepción.

## Dedupe / no repetición
Clave canónica: organización + programa + convocatoria/ciclo + país + identidad de candidatura. Registrar identificadores de Gmail, Airtable, Supabase, navegador y enlace oficial. Unificar registros de origen sin borrar evidencia. Antes de enviar, buscar acuse y acciones previas en todas las fuentes. Si falta comprobante, etiquetar 'POR_VERIFICAR', no reenviar automáticamente.

## Reglas de ejecución
- Buscar → verificar fecha, elegibilidad Colombia, idiomas, costo $0 → cotejar histórico → preparar → ejecutar solo acciones permitidas → guardar prueba → vigilar respuestas → notificar Motorola.
- Candidaturas: nunca enviar sin requisitos reales ni inventar datos. CAPTCHA, identidad, pagos y consentimientos requieren usuario.
- Gmail: clasificar acuse automático, respuesta humana, rechazo, entrevista, rebote y aprobación por separado.
- Reintentos con backoff; idempotencia por clave; bloqueo de envíos duplicados; registros auditables.
- No mezclar regiones. No inflar números con registros fuente o duplicados. Contabilizar oportunidades únicas elegibles y candidaturas comprobadas.
- Separar historial completo de panel activo. Archivar, NO eliminar definitivamente, los vencidos/no elegibles con razón y evidencia.
- Las alertas urgentes deben tener fecha y fuente comprobadas; no inventar 'urgentes verificados'.

## Puertas de aceptación antes de ampliar
A. Conciliar las cifras de las fuentes con el panel (1.920 filas fuente observadas el 10-Nov; 802 sin región; la interfaz previa mostraba 1.115, diferencia pendiente de explicar).
B. Verificar los 84 posibles conflictos de estado/evidencia; no asumir que todos son errores.
C. Pruebas reales: candidatura ya enviada no se repite; entrevista ya realizada no se solicita; correo rebotado no se marca entregado; vencido no aparece activo.
D. Comprobar flujo completo en Android Motorola con evento real y acuse de notificación.
E. Solo después habilitar los 42 carriles con límites de tasa, supervisión y métricas por región.

## Arquitectura
Supabase = fuente central de verdad y auditoría; GitHub = código versionado; Render = servicios existentes que NO se deben interrumpir; Gmail = comunicaciones y evidencias; Airtable = respaldo; Floot = panel; MacroDroid/Android = alertas. n8n opcional cuando tenga persistencia, autenticación y credenciales seguras. Claude/Gemini opcionales, no declararlos conectados sin pruebas.
