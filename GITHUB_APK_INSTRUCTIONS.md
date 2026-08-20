# Cómo generar el APK desde GitHub

Esta versión incluye GitHub Actions para compilar el APK automáticamente.

## Desde el celular o navegador

1. Entra a GitHub.
2. Crea un repositorio nuevo llamado:
   `SM-Personal-Trainer`
3. Sube todos los archivos y carpetas de este proyecto.
4. Verifica que exista:
   `.github/workflows/android-build.yml`
5. En GitHub abre la pestaña:
   `Actions`
6. Entra en:
   `Build Android APK`
7. Pulsa:
   `Run workflow`
8. Espera a que termine la compilación.
9. Abre la ejecución completada.
10. En la sección `Artifacts`, descarga:
    `SM-Personal-Trainer-debug`
11. Descomprime el archivo descargado.
12. Dentro estará:
    `app-debug.apk`

Ese APK se puede instalar en un teléfono Android.

## Importante
Android puede pedir permiso para instalar aplicaciones desde el navegador o gestor de archivos.

## Estado de esta versión
- Compilación automática preparada.
- APK debug para pruebas.
- Todavía no es una versión firmada para Google Play.
- La base de datos sigue en modo local/demo.

## Próxima fase recomendada
- Firebase o Supabase real.
- Login de alumnos.
- Sincronización entre dispositivos.
- APK firmado / AAB para Google Play.
