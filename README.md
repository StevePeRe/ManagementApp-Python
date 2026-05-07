# Backend (iteración 2) - Migración Java
Esta fase replica la base del backend del proyecto original con FastAPI:
- Endpoints REST en `/api/tasks`
- Modelo `Task` con estados `CREATED`, `RUNNING`, `DONE`
- Persistencia con SQLAlchemy
- Pytest para testing
- Manejo de errores básico (`400` y `404`) compatible con el formato anterior
- Scheduler de estados (cada minuto):
  - `CREATED` -> `RUNNING` cuando supera 2 minutos desde `created_at`
  - `RUNNING` -> `DONE` cuando supera 8 minutos desde `started_at`

## Ejecutar en local
1. Instalar dependencias:
   - `uv sync --python <ruta_python_uv>`
2. Levantar API:
   - `uv run --python <ruta_python_uv> uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload`
3. Probar salud:
   - `GET http://localhost:8080/health`

## Variables de entorno
- Puedes usar `DATABASE_URL` directo (PostgreSQL o SQLite).
- O activar `USE_POSTGRES=true` y definir:
  - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- También se aceptan aliases de Spring:
  - `SPRING_DATASOURCE_URL`
  - `SPRING_DATASOURCE_USERNAME`
  - `SPRING_DATASOURCE_PASSWORD`

## Scheduler configurable
- `SCHEDULER_ENABLED=true|false`
- `SCHEDULER_INTERVAL_SECONDS=60`
- `TASK_CREATED_TO_RUNNING_MINUTES=2`
- `TASK_RUNNING_TO_DONE_MINUTES=8`

## Notas de desarrollo
Para el desarrollo de esta aplicación he trabajado con [OpenCode](https://opencode.ai/) como herramienta de apoyo. Lo he utilizado porque me ofrece soporte durante la implementación del proyecto, facilita el análisis del código y proporciona una forma flexible de trabajar sobre el desarrollo desde un entorno técnico orientado a terminal.
