# SM Personal Trainer 2.1

Versión preparada para evolucionar desde una app local a una plataforma real.

## Incluye
- Panel del entrenador
- Gestión local de alumnos
- Alta de nuevos alumnos
- Rutinas completas
- Asignación de rutinas
- Historial de asignaciones
- Registro de progreso
- Peso, cintura, pecho y brazo
- Separación entre UI y datos mediante TrainingRepository
- Esquema SQL preparado para Supabase/PostgreSQL
- Punto de integración para Firebase o Supabase

## Estado actual
Los datos funcionan como demostración local mientras la app está abierta. No se incluyen credenciales ni claves remotas.

## Próxima fase
- Autenticación real
- Sincronización entre teléfonos
- Datos privados por alumno
- Base persistente
- Videos e imágenes
- Notificaciones


## GitHub Actions
Esta versión incluye `.github/workflows/android-build.yml` para compilar automáticamente un APK de prueba en GitHub.

Consulta `GITHUB_APK_INSTRUCTIONS.md` para los pasos desde el navegador.
