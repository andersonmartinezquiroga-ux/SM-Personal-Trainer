# SJM Autopilot Queue

Este directorio contiene la cola remota del SJM Autopilot local.

- `manifest.json`: lista de tareas disponibles.
- `tasks/`: scripts de construcción para Unreal Engine.
- El agente local solo ejecuta tareas habilitadas y aún no completadas.
- Cada tarea se valida con SHA-256 antes de ejecutarse.
