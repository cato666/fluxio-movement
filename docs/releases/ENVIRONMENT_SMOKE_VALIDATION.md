# Environment Smoke Validation

Fecha: 2026-10-04 (America/Santiago).

## Estado

Diagnóstico de infraestructura realizado, sin cambios al código, configuración,
migraciones ni despliegue. No se enviaron mensajes WhatsApp.

**Health de Easypanel: aprobado. Smoke de Weekly/Kapso y Sharing real: pendiente.**
El entorno destino todavía debe confirmarse: se inspeccionaron el dominio de
Easypanel documentado y el sandbox local configurado con ngrok. No se dispone de
una sesión de administración de Easypanel ni de un alias SSH configurado para
leer su entorno interno. Se solicitó ese acceso sin pedir secretos por chat.

Baseline local aprobado conservado: Python 451/451, JavaScript 62/62, UX y ambos
E2E verdes. Estos resultados no sustituyen el smoke del entorno destino.

## Causa del 404

El código actual define `GET /health` en `app/main.py`, lo incluye en OpenAPI y
lo permite sin autenticación. No se encontró un `root_path` configurado en la
aplicación. `/health` comprueba acceso a PostgreSQL; `/api/health` comprueba además
la revisión esperada por la versión cargada del servicio.

El valor local de PUBLIC_BASE_URL es
`https://b369-186-104-25-125.ngrok-free.app`. La API de inspección de ngrok muestra
que ese túnel HTTPS apunta a **http://localhost:8002**, no directamente a FastAPI.
El listener 8002 pertenece a Python y ejecuta `tools/kapso-webhook-proxy.py`.
Su respuesta identifica `BaseHTTP/0.6 Python/3.12.14`.

En ese proxy, `/`, `/health`, `/api/health` y `/openapi.json` devuelven 404.
En cambio, `POST /webhooks/whatsapp/kapso` con cuerpo vacío sin firma devuelve
401 `Firma inválida`, tanto en 8002 como en el dominio ngrok. Por lo tanto, el
túnel está activo y alcanza un proxy que admite el webhook pero no las rutas de
la aplicación inspeccionadas. El 404 de health procede de esa capa de routing.

La API real del sandbox está en **127.0.0.1:8001 → contenedor:8000** y responde
200 en `/health`. La misma petición con el Host público de ngrok también devuelve
200. No hay evidencia de un rechazo por Host header en FastAPI.

El dominio de Easypanel documentado,
`https://proyectos-fluxio-movement.sgnetm.easypanel.host`, responde **200** con
`{"ok":true}` en `/health` y 200 con estado saludable en `/api/health`.
OpenAPI está accesible en la raíz y contiene `/health`, Bitácora y el webhook.
Las consultas HTTPS se realizaron con verificación normal de certificado;
no se omitió validación TLS. No fue necesario un base path para esas rutas.

| Destino | Servicio observado | Health | OpenAPI Weekly/Sharing |
|---|---|---:|---|
| Easypanel HTTPS | Uvicorn, aplicación Fluxio con Bitácora y webhook | 200 | Ausentes |
| ngrok HTTPS | Proxy Python hacia localhost:8002 | 404 | GET OpenAPI devuelve 404 |
| localhost:8002 | Proxy de webhook | 404 | GET OpenAPI devuelve 404 |
| localhost:8001 | API del sandbox Kapso | 200 | Ausentes en proceso cargado |
| localhost:8000 | Aplicación local anterior | 200 | Ausentes; webhook también ausente |

**Corrección aplicada:** ninguna. Se entregó el diagnóstico antes de modificar
código. En el sandbox, la corrección a evaluar es ampliar las rutas permitidas
del proxy o apuntar el túnel a la API manteniendo sus controles de acceso y HTTPS.
No se cambió la exposición pública de servicios. En Easypanel no se reprodujo
el 404 y no corresponde corregir `/health` en el código.

## Versión y migración

Easypanel no expone `/api/training-week`, sus controles de sharing ni el lector
público en OpenAPI. El `training.js` servido tampoco contiene los controles
semanales. Su versión pública observada todavía no incluye esta funcionalidad.
No se puede identificar su commit, imagen o migración exacta desde estos probes.

En el sandbox, el archivo estático montado sí contiene los controles semanales,
pero las rutas no están registradas en el proceso API actualmente cargado.
Esto es compatible con procesos anteriores que no se han recargado tras los
cambios del workspace; no se reiniciaron durante esta inspección.

La consulta directa, de solo lectura, al sandbox confirma:

- Alembic: **0020_whatsapp_capture**.
- `weekly_shares`: **no existe**.
- Migración requerida para el smoke semanal: **0021_weekly_shares**, pendiente.

**Migración final del destino remoto: no verificable sin acceso administrativo.**
No se ejecutó `alembic upgrade` en una base persistente. El servicio remoto debe
recibir la versión aprobada mediante un deploy explícitamente autorizado antes
de intentar el smoke de Weekly/Sharing.

## Variables, secretos, storage y workers

Los resultados de esta tabla corresponden exclusivamente al sandbox Docker
local; no acreditan las variables de Easypanel.

| Comprobación | API sandbox | Worker sandbox |
|---|---|---|
| Proceso activo | Sí; contenedor healthy | Sí; comando app.whatsapp.worker |
| WHATSAPP_ENABLED | true | true |
| WHATSAPP_PROVIDER | kapso | kapso |
| PUBLIC_BASE_URL | Dominio ngrok configurado | **Vacío** |
| KAPSO_API_KEY / WEBHOOK_SECRET / PHONE_NUMBER_ID | Presentes | Presentes; iguales a API |
| WHATSAPP_ENCRYPTION_KEY / PHONE_HASH_KEY | Presentes, Vault válido | Presentes, Vault válido; iguales a API |
| DATABASE_URL / STORAGE_PATH | Configurados | Iguales a API |
| Storage /data/storage | Existe; permisos de lectura/escritura | Volumen montado; misma configuración |

No se imprimieron claves, firmas, teléfonos, payloads, IDs de atletas ni mensajes.
La comparación de secretos produjo solamente booleanos de presencia/igualdad.
La inspección de storage comprobó directorio y permisos, sin crear ni borrar
archivos persistentes. La configuración de proxy remoto, puertos internos,
labels, variables, salud de worker y volúmenes de Easypanel queda pendiente de
acceso a su administración; los puertos locales no permiten inferirlos.

## Smoke Kapso

| Paso solicitado | Evidencia actual |
|---|---|
| Webhook accesible | Easypanel y ngrok responden 401 al POST vacío sin firma |
| Firma válida | No ejercitada con un evento real nuevo de Kapso |
| Inbox persistido | No acreditado para este smoke |
| Identidad resuelta | No acreditada para este smoke |
| help | No enviado en este smoke |
| resumen semana | No enviado; rutas/migración semanal aún ausentes |
| compartir semana | No enviado; además worker local sin PUBLIC_BASE_URL |
| revocar semana | No enviado; no se creó enlace real |
| Outbound entregado por Kapso | No acreditado para este smoke |

El 401 confirma routing y rechazo de firma inválida, **no** firma válida ni
persistencia. La consulta agregada del sandbox muestra 1 identidad activa,
125 inbox DONE y outbox con 36 READ y 1 FAILED. Son registros históricos:
no prueban estos comandos ni entregas nuevas en el entorno destino.

No se fabricaron eventos firmados para presentarlos como tráfico real de Kapso.
Antes de enviar mensajes, confirmar entorno y atleta de prueba, disponer de la
versión/migración requerida, verificar PUBLIC_BASE_URL tanto en API como worker
y observar el evento nuevo y su receipt de entrega sin divulgar su contenido.

## Sharing en dominio real

No ejecutado: Easypanel todavía no sirve Weekly/Sharing; ngrok no publica las
rutas de lectura, y el sandbox no tiene la migración 0021 aplicada.

Quedan pendientes enlace válido, foto, revocación, expiración controlada y headers
reales `Cache-Control: no-store`, `X-Robots-Tag: noindex, nofollow`,
`Referrer-Policy: no-referrer`, ausencia de metadatos de identidad y origen correcto
del enlace. El TTL corto debe probarse en un entorno de smoke autorizado o con
un fixture temporal expresamente acordado; no se alteró el TTL productivo.

## Pendientes y siguiente paso

1. Confirmar si el destino es Easypanel o el sandbox ngrok.
2. Facilitar acceso administrativo de solo lectura al destino, sin secretos por
   chat, para verificar imagen/commit, routing, migración, variables y worker.
3. Si es Easypanel, autorizar explícitamente el deploy de la fase aprobada antes
   de aplicar 0021. Health ya funciona; el release semanal aún no está servido.
4. Si es el sandbox, acordar la corrección del proxy/túnel, recarga de API/worker,
   migración 0021 y PUBLIC_BASE_URL del worker, conservando base, claves y storage.
5. Con health y prerrequisitos verificados, ejecutar los comandos desde la
   identidad de prueba y confirmar eventos/receipts nuevos de Kapso.
6. Validar Sharing en el dominio real y completar este informe con evidencia
   sanitizada. Ninguna comprobación pendiente se considera aprobada por los
   resultados locales previos.
