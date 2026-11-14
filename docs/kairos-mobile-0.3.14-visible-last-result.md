# KAIRÓS Móvil 0.3.14 — Corrección del botón de resultado

Incidencia observada en Motorola 0.3.12, 13-nov-2026: tocar «Ver último resultado de KAIRÓS» no mostraba ningún cambio visible en esa zona. El código de 0.3.13 actualizaba \`status\` y \`localProof\` situados **por encima del botón**: la pantalla estaba desplazada al botón, de modo que los cambios no se veían.

Cambio correctivo:
- Muestra un panel de resultado inmediatamente después de «Ver último resultado».
- Indica hora de **consulta local**, el último estado local guardado (incluida su hora original), etapa de sondeo/acuse, pausa y confirmación pendiente.
- Declara explícitamente que consultar el resultado **no ejecuta órdenes remotas** ni prueba actividad nueva.
- No cambia credenciales, API, permisos, MacroDroid ni políticas de seguridad.
- Aplica \`versionCode=17\` y \`versionName=0.3.14\`, firmada con la misma firma del flujo v0.3.13 cuando GitHub Actions termine.

Pruebas: \`LastResultTextSelfTest\` contiene casos para último resultado antiguo y estado pausado/acuse pendiente; se corre junto a los test de navegación en workflow existente. **No** afirmar compilación, firma, publicación ni instalación hasta verificación de la ejecución y la liberación GitHub. 

Para actualizar desde 0.3.12: solo APK release del repositorio y certificado verificado, instalar encima sin desinstalar ni renovar el código. Probar visualmente que tras pulsar aparece el texto bajo el botón (aunque no haya una orden nueva). Si Android rechaza la firma, detenerse, sin desinstalar.
