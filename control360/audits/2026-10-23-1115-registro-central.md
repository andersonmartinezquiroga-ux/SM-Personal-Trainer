# SJM Control 360 — Auditoría de registro central (2026-10-23 11:15 COT)

Estado: **PARCIAL / EN CONCILIACIÓN**. Documento de evidencia, no autorización de envío.

## Hallazgo nuevo (solo investigación)
- Clave: `workana-ia-data-latam-irene-20261023`
- Fuente: Workana / Irene R. (contratista independiente).
- Anuncio: https://www.workana.com/job/convocatoria-proyecto-de-recopilacion-de-datos-latam
- Publicado: 2026-10-08. Consultado: 2026-10-23. Página muestra abierto/evaluando propuestas.
- Promesa anunciada: USD 4/h y USD 400 por 100 horas, no garantizados.
- Registro Airtable: `recuyLoSlTrUG0bky`; escritura y lectura posterior exitosas.
- Ingesta privada Supabase: `sjm_ops.c360_ingest_external_v1` devolvió `received=1, changed=1`.
- Lectura posterior: `control360_registry_v1` contiene `source_system=airtable_opportunities`, mismo `source_id`, `status=Verificando requisitos`; radar NULL, método unassigned.
- Próxima acción: verificar modelo de móvil compatible, actividades y si exigen voz/video, condiciones de privacidad y contrato, disponibilidad y existencia de propuesta previa. No postular sin resolver. No hay acuse de envío.
- Fecha de revisión: 2026-10-23. Fecha límite: no indicada.

## Protección contra duplicados
- Consulta a Gmail, Airtable y `sjm_ops.cases` antes de registrar: sin coincidencia con este anuncio.
- La tabla privada `sjm_ops.official_application_receipts_v1` sigue con **3** recepciones YPAI: Data Annotator, Text/NLP Annotator y Model Evaluator. Nunca duplicar.
- No se envió ninguna candidatura nueva en este ciclo.

## Pruebas de conciliación del ciclo
- `select sjm_ops.c360_refresh_sources_v1();` => `visited=829, updated=0, unmapped=778` (2026-10-23T16:15:36Z).
- `select sjm_ops.c360_health_check_v1();` => `totalRegistry=908, sourceCount=14, sin_radar=359, sin_siguiente_accion=148, sin_enlace_documentado=7, duplicateUrlGroups=129, radarDeliveriesLast24h=0` (2026-10-23T16:15:38Z).
- Sincronización automática Airtable → Supabase **no verificada**. La ingesta de esta ficha fue manual y comprobada.
- Sin región inferida. La ubicación de la contratista no está acreditada.

## Consultas reproducibles de solo lectura
```sql
select source_system, source_id, payload->>'status' as status,
       payload->>'original_key' as original_key,
       detected_radar, radar_method
from sjm_ops.control360_registry_v1
where source_system = 'airtable_opportunities'
  and source_id = 'recuyLoSlTrUG0bky';

select case_key, role_label, receipt_origin, received_at
from sjm_ops.official_application_receipts_v1
order by received_at;

select sjm_ops.c360_health_check_v1();
```

## Seguridad
No incluir OTP, enlaces privados, claves, tokens, documentos de identidad ni datos bancarios. No modificar permisos RLS masivamente. No confundir una investigación con contacto, postulación, selección o contratación.
