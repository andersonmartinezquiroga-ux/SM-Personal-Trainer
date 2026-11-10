# KAIRÓS — laboratorio aislado de herramientas

Este directorio no forma parte de los servicios de producción. No se ejecutan postulaciones ni se usan credenciales.

## Candidatos
- Browser Use (biblioteca Python MIT): navegación con agente; los modelos externos pueden costar.
- Activepieces: orquestación; despliegue completo requiere Docker Compose y recursos.
- Playwright existente: preferido para formularios deterministas.

## Prueba inicial reproducible
Ejecutar en un entorno aislado con Python 3.11+:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'browser-use' 
python -c 'import browser_use; print("browser-use import: OK")'
```

Esto solo verifica instalación/importación. No configura proveedor LLM, navegador, autenticación ni autonomía. No introducir tokens ni datos de candidatos. Registrar versión, tiempo, memoria y errores antes de proponer integración. Nunca ejecutar esto dentro del servicio Render activo.

## Criterios de aceptación
1. Costo de ejecución $0 verificable.
2. Instalación y prueba en entorno persistente.
3. No modifica candidaturas existentes ni envía formularios reales.
4. Manejo seguro de credenciales, límites y consentimiento.
5. Solo promover a producción después de prueba aislada y respaldo.

Fuentes: https://github.com/browser-use/browser-use ; https://www.activepieces.com/docs/install/options/docker-compose
