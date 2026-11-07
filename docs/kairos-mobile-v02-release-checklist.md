# KAIRÓS Móvil — entrega de desarrollo V0.2 (6 nov 2026, Colombia)

## Evidencia obtenida
- V0.1 sigue instalada y activa en Motorola. Evidencia del usuario: notificación recibida, MacroDroid abierto y página oficial de CONTROL 360 abierta sin tocar el teléfono.
- Servidor Floot SJM CONTROL 360 publicó la API de emparejamiento y un ejecutor con comandos permitidos `notify`, `open_app`, `open_url`; no existe todavía comando remoto de gestos/taps.
- V0.2 compilada exitosamente en GitHub Actions workflow run `42334453400`; las 10 pruebas Java de navegación segura pasaron.
- V0.2 añade outbox local para reintento de confirmaciones, botón de pausa del usuario y whitelist de URLs oficiales. **No está instalada ni probada en el Motorola.**

## Bloqueador real: firma Android
- APK V0.1 certificado SHA256: `e5c26b0f783cebec74e8341171075c8555b045a51f37035ee770b5c4fc83e602`.
- APK V0.2 certificado SHA256: `9d4be7fb6968265a7ab7790e3776e29ac1824bdf3c66a3273cfad8cf7a54e2b4`.
- Son firmas distintas por usar keystore de depuración efímero de GitHub Actions. **No instalar el V0.2 encima del V0.1**: Android rechaza la actualización y, al desinstalar, se pierde el secreto de enlace (almacenado en Android Keystore).
- Antes de pedir otra instalación, preparar firma de actualización persistente usando un **GitHub Actions secret privado** o un proceso de firma privado, nunca incluir la clave privada en este repositorio público.
- Una **única migración** puede requerir desvinculación y revinculación (código de 10 caracteres), manteniendo MacroDroid sin cambios; explicar previamente al dueño y esperar confirmación para la instalación.

## Próximo paso backend
- Cuota diaria Floot agotada durante el trabajo. Restablece a 2026-11-08T00:00Z (2026-11-07, 19:00 Colombia), salvo levantamiento previo.
- Cuando haya cupo, investigar por qué V0.1 recibió/mostró un aviso pero no confirmó `completed`. V0.2 posee reintentos locales pero no se debe afirmar que corrige en producción antes de probar.
- Para navegación de pantalla, diseñar comandos de solo lectura y pasos limitados a dominios SJM, autorización expresa, sin acciones externas ni formularios y con resultado comprobable. No anunciar capacidad hasta pruebas sobre dispositivo.
- Mantener `KAIRÓS 02` MacroDroid en funcionamiento.

## Seguridad y continuidad
- No pagos, contratos, correos o postulaciones automáticas sin aprobación.
- No leer contenido ajeno sin permisos expresos.
- No mostrar token del ejecutor ni clave MacroDroid en capturas; rotar las claves expuestas cuando se haga la próxima migración controlada.
