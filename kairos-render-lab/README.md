# KAIRÓS · Nodo alterno de laboratorio (Render Free)
Servidor Node.js sin dependencias, publicado por separado para poder trabajar cuando Floot alcance la cuota. `GET /health` confirma que Render opera; `POST /validate` verifica una orden contra una lista cerrada sin ejecutarla. Este nodo **no** contiene claves, no está conectado al Motorola, no reemplaza a Floot ni pretende ser un broker de comandos hasta tener autenticación y persistencia.

La meta posterior es un canal alterno autenticado y auditable con almacenamiento persistente (Supabase), renovación de claves y migración explícita de la app Android. No cambiar la configuración actual del usuario sin prueba de extremo a extremo. Sin pagos ni contratos.
