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
5. En variables del servicio, crea los valores de `.env.example`. Genera una contraseña fuerte para `POSTGRES_PASSWORD` y usa la misma contraseña codificada en `DATABASE_URL`:

```text
DATABASE_URL=postgresql+psycopg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@db:5432/<POSTGRES_DB>
```

6. Mantén `STORAGE_PATH=/data/storage` y define el límite deseado en `MAX_UPLOAD_MB`.
7. Despliega. El servicio `app` espera que `db` esté saludable antes de iniciar migraciones y seed.
8. En la sección de dominio de Easypanel, expón el servicio **`app`**, puerto **`8000`**, protocolo **HTTP**.
9. Verifica `https://tu-dominio/health` tras asignar el dominio.

No agregues Nginx, Caddy ni certificados al repositorio: Easypanel se encarga del proxy, dominio y HTTPS.

## Límites del MVP

No hay autenticación real todavía; las identidades son demo. El análisis es síncrono y las métricas dependen del ángulo de cámara. Conserva respaldos de los dos volúmenes antes de actualizar un entorno con datos reales.
