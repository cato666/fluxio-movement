# Fluxio Movement

FastAPI, PostgreSQL, MediaPipe, OpenCV y FFmpeg para analizar videos de entrenamiento y entregar revisiones de coaches. El despliegue usa Docker Compose; Easypanel administra dominio, HTTPS, proxy y logs.

## Ejecutar localmente

1. Copia `.env.example` a `.env` y reemplaza los valores de desarrollo.
2. Ejecuta:

```bash
docker compose up --build -d
docker compose ps
```

3. Abre `http://localhost:8000/demo`.

La aplicación espera PostgreSQL, ejecuta `alembic upgrade head`, aplica el seed idempotente y luego inicia Uvicorn en `0.0.0.0:8000`. Verifica el despliegue con:

```bash
curl http://localhost:8000/health
```

La respuesta correcta es `{"ok":true}`. No contiene detalles de conexión.

## Variables de entorno

Usa [.env.example](.env.example) como referencia. No subas `.env` al repositorio.

| Variable | Uso |
| --- | --- |
| `APP_ENV` | Entorno de ejecución, por ejemplo `production`. |
| `SESSION_SECRET` | Secreto aleatorio largo para firmar las sesiones. Obligatorio en producción. |
| `POSTGRES_DB` | Base de datos PostgreSQL. |
| `POSTGRES_USER` | Usuario PostgreSQL. |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL. |
| `DATABASE_URL` | URL SQLAlchemy usando el hostname interno `db`. |
| `STORAGE_PATH` | Ruta de almacenamiento; Compose usa `/data/storage`. |
| `MAX_UPLOAD_MB` | Límite máximo de cada video. |
| `APP_PORT` | Puerto local opcional, por defecto `8000`. |

## Persistencia

Docker Compose crea dos volúmenes nombrados:

- `postgres_data`: datos PostgreSQL.
- `app_storage`: archivos en `/data/storage`.

Dentro de `app_storage` los artefactos se organizan en:

```text
/data/storage/original
/data/storage/annotated
/data/storage/analysis
/data/storage/temp
```

No publiques PostgreSQL al host. Para comprobar persistencia, ejecuta:

```bash
docker compose down
docker compose up -d
```

No uses `docker compose down -v`: elimina los volúmenes persistentes.

## Easypanel en Contabo

1. En Easypanel crea el proyecto **`fluxio-movement`**.
2. Crea un **Compose Service**.
3. En **Source**, conecta GitHub y selecciona el repositorio **`fluxio-movement`** y la rama a desplegar.
4. Usa el archivo `docker-compose.yml` del repositorio.
5. En variables del servicio, crea los valores de `.env.example`. Define también `SESSION_SECRET` con un valor aleatorio de al menos 32 caracteres. Genera una contraseña fuerte para `POSTGRES_PASSWORD` y usa la misma contraseña codificada en `DATABASE_URL`:

```text
DATABASE_URL=postgresql+psycopg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@db:5432/<POSTGRES_DB>
SESSION_SECRET=<secreto-aleatorio-largo>
```

6. Mantén `STORAGE_PATH=/data/storage` y define el límite deseado en `MAX_UPLOAD_MB`.
7. Despliega. El servicio `app` espera que `db` esté saludable antes de iniciar migraciones y seed.
8. En la sección de dominio de Easypanel, expón el servicio **`app`**, puerto **`8000`**, protocolo **HTTP**.
9. Verifica `https://tu-dominio/health` tras asignar el dominio.

No agregues Nginx, Caddy ni certificados al repositorio: Easypanel se encarga del proxy, dominio y HTTPS.

## Límites del MVP

## Biblioteca de ejercicios

La sección **Exercise Library** (`/exercises`) está disponible para usuarios autenticados.
`GET /api/exercises` permite combinar filtros `category`, `priority` y
`analysis_status`; `GET /api/exercises/{exercise_id}` devuelve el detalle (404 si
no existe). `GET /api/exercise-categories` expone la taxonomía configurada.

El catálogo vive en `app/services/exercise_library/exercises.json`; la taxonomía
en `taxonomy.json`. Los perfiles del detector conservan su formato y aceptan
metadata opcional validada, accesible mediante `ExerciseProfile.library`.
`detector_profiles` enlaza el catálogo con los detectores existentes sin cambiar
alias, umbrales ni señales. `supported` indica soporte de conteo de repeticiones,
no detección de todos los errores técnicos. `air_squat` referencia el detector
de squat; las variantes power conservan `reference_only` porque los alias
genéricos existentes no validan su recepción específica.

Los 20 ejercicios tienen referencias del canal oficial CrossFit. Solo se guardan
URLs e identificadores: no se descargan videos. Los segmentos están pendientes
de revisión editorial (`segments_status: pending_review`); se admite inicio y
fin finitos y ordenados, y construir embeds por segmento. Los errores iniciales
tienen `detectable: false`. En `reference_only`, las cámaras son vistas previstas
para futuras implementaciones. `ExerciseFinding` define un contrato futuro sin
ejecutar razonamiento ni agregar modelos.

No hay autenticación real todavía; las identidades son demo. El análisis es síncrono y las métricas dependen del ángulo de cámara. Conserva respaldos de los dos volúmenes antes de actualizar un entorno con datos reales.
