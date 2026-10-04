# Weekly Summary + Sharing — Release Validation

Fecha: 2026-10-04 (America/Santiago).

## Alcance y estado

Validación de la fase aprobada, sin nuevas funcionalidades ni despliegue.
Las pruebas usan PostgreSQL descartable (`movement_test`), almacenamiento
temporal, usuarios sintéticos y un servidor HTTP local. Nunca se utiliza la
base productiva ni se envían mensajes reales por Kapso.

**Validación local: APROBADA. Publicación: condicionada a configurar y validar
el dominio público y al smoke real de WhatsApp en el entorno destino.**
El dominio local actual devuelve 404 en health. No se ejecutó deploy.
Los hashes de 103 archivos de `app/` y `migrations/` se conservaron: únicamente
se agregaron pruebas, runner e informe de release.

## Migración 0021

Secuencia comprobada: `0020_whatsapp_capture → 0021_weekly_shares →
0020_whatsapp_capture → 0021_weekly_shares`.

En cada paso se compara el contenido completo de todas las tablas preexistentes
mediante JSON canónico; también se compara el SHA256 del archivo de foto.
El fixture incluye usuarios, atleta, coaches, sesión, nota personal, foto e
identidad de WhatsApp vinculada. Las demás tablas se comparan incluso vacías.
No se observaron pérdidas ni cambios en esos datos. Se verifica la revisión
exacta, la aparición/desaparición de `weekly_shares` y `alembic check`.

**Rollback:** downgrade a 0020 elimina `weekly_shares` y todos sus enlaces y
copias. Los entrenamientos, fotos e identidades preexistentes se conservan.
Upgrade posterior recrea la tabla vacía; no recupera los enlaces eliminados.
Respaldar la base antes del cambio si esos enlaces deben conservarse.

Evidencia: `results/releases/weekly-sharing-20261004/migration-roundtrip.json`.

## Variables y dominio

```dotenv
PUBLIC_BASE_URL=https://<dominio-del-entorno>
WEEKLY_SHARE_TOKEN_TTL_HOURS=168
```

`PUBLIC_BASE_URL` debe ser una URL HTTPS absoluta, sin credenciales, query ni
fragmento. Se recibe del entorno; no hay dominio fijado en el código de Weekly
Summary, Sharing ni el constructor del enlace en WhatsApp. Compose pasa ambas
variables a `app` y `whatsapp-worker` mediante el bloque compartido de entorno.
El dominio del despliegue debe configurarse en Easypanel; no copiar el túnel
local como configuración productiva.

Valor realmente leído de `.env` durante esta validación:
`https://b369-186-104-25-125.ngrok-free.app`.
El test de WhatsApp genera un enlace con ese origen exacto. Un GET HTTPS de
`/health` respondió **404**: el dominio local no acredita servicio saludable.
El dominio público del release y su acceso HTTPS quedan pendientes de comprobar
en el entorno destino, después de su configuración y despliegue autorizado.

Variables de infraestructura existentes: `DATABASE_URL`, `STORAGE_PATH` y
`SESSION_SECRET`; conservar base, volúmenes y secreto de sesión. Para WhatsApp
siguen siendo necesarias `WHATSAPP_ENABLED=true`, `WHATSAPP_PROVIDER=kapso`,
`KAPSO_PHONE_NUMBER_ID`, `KAPSO_API_KEY`, `KAPSO_WEBHOOK_SECRET`,
`WHATSAPP_ENCRYPTION_KEY`, `PHONE_HASH_KEY` y la versión/keyring correspondientes
al entorno. No rotar esas claves como parte de este release.

## Enlaces, contenido y seguridad

| Caso | HTML | Foto | Resultado |
|---|---:|---:|---|
| Token válido | 200 | 200 JPEG válido | Copia autorizada visible |
| Token expirado | 404 | 404 | Sin contenido de la copia |
| Token revocado | 404 | 404 | Sin contenido de la copia |
| Token inexistente de formato válido | 404 | 404 | Sin contenido de la copia |
| Token de A con identificador de foto de B | — | 404 | Cruce denegado |

La copia contiene exclusivamente fecha, título, entrenamiento, resultado,
nota/adaptaciones, RPE y referencia de su foto. Se verifican marcadores distintos
para entrenamiento, resultado y nota, así como decodificación real de la foto.
No se comparten `source_text`, videos, bloques internos ni campos de identidad.
La respuesta pública no expone `athlete_id`, UUID del atleta ni teléfono de
transporte. El código escapa texto HTML; la suite semanal verifica XSS y que
ediciones posteriores no modifiquen la copia.

Las consultas privadas y la revocación se restringen al atleta propietario.
A no puede leer la sesión/foto privada de B, revocar sus enlaces, listar sus
enlaces ni acceder a una foto de B mediante un token de A. Un enlace válido de
B sí permite leer su copia a cualquier destinatario que lo posea: esa es la
autorización explícita del sharing, sin exigir cuenta.

HTML válido y denegado, y fotos válidas y denegadas, verifican:

- `Cache-Control: no-store`.
- `X-Robots-Tag: noindex, nofollow`.
- `Referrer-Policy: no-referrer`.

El HTML incluye también las metas robots/referrer y una CSP que restringe
contenido a recursos propios y bloquea frames (`frame-ancestors 'none'`).
Las fotos usan `X-Content-Type-Options: nosniff`. Los tokens tienen 32 bytes
aleatorios; PostgreSQL guarda SHA256, nunca el token en claro en esa tabla.

## Revocación y expiración

El recorrido comprueba generar enlace → abrir 200 → revocar → abrir 404.
La revocación aplica también a la foto. La revocación conjunta incluye todos los
enlaces de la semana seleccionada y conserva los enlaces de otras semanas.

Se usa TTL configurado a 1 hora y un reloj de fixture: a los 59 minutos devuelve
200; exactamente al vencer devuelve 404. También se comprueba que 168 horas
equivalen a siete días. No se espera tiempo real ni se cambia el TTL productivo.

## WhatsApp

Se prueban los comandos exactos `resumen semana`, `compartir semana` y
`revocar semana` mediante webhook firmado, inbox, worker, servicio compartido y
outbox reales contra la base descartable. El proveedor es `FakeProvider`;
no se acreditan entrega, recepción en un teléfono ni funcionamiento real de Kapso.

El enlace generado utiliza el valor real de `PUBLIC_BASE_URL` leído por el
runner. Se confirma la revocación y que retransmitir cada mismo webhook no
duplica su procesamiento. Evidencia: `whatsapp-domain.json`.

## Pruebas y E2E

| Gate reejecutado | Resultado |
|---|---|
| Release específico + Weekly Summary/Sharing | 17 passed |
| Python completo | 451 passed, 3 avisos preexistentes, 235.15 s |
| JavaScript completo | 62 passed, 0 failed, 0 skipped |
| Athlete UX específico | 18 passed |
| Coach UX específico | 23 passed |
| Bitácora UX específico | 17 passed |
| E2E Athlete + Coach + Bitácora | 6 flujos PASS, sin errores JavaScript |
| E2E Weekly Summary + Sharing | PASS en escritorio 1440 px y móvil 390 px |
| Alembic final | 0021_weekly_shares (head), metadata sin drift |
| Integridad del código productivo | 103 hashes sin cambios |

El primer E2E no alcanzó a correr porque el probe de PowerShell agotó su espera,
aunque Uvicorn había arrancado. Se cambió únicamente el runner para consultar
health desde el contenedor. La primera recuperación detectó que faltaba cargar
Playwright en modo E2EOnly; se corrigió esa variable en el runner. La ejecución
final repitió los 17 gates específicos y ambos E2E, y terminó con exit code 0.
No se repitieron las regresiones completas aprobadas por ajustes del harness.
Los logs iniciales y los finales se conservan por separado.

Los seis flujos HTTP cubren Bitácora por texto, foto y audio, análisis/solicitud
del atleta, revisión/comentario/completado del coach y feedback del atleta.
El E2E semanal comprueba navegación, creación del enlace, lectura anónima de
ambas fotos, ausencia de overflow y denegación tras revocar. IA externa e
inferencia de pose usan fixtures deterministas; HTTP, PostgreSQL, permisos,
almacenamiento y FFmpeg son reales. No es evaluación de precisión biomecánica.

Evidencia local en `results/releases/weekly-sharing-20261004/`:
`python-targeted.log`, `python-full.log`, `javascript-full.log`,
`athlete-ux.log`, `coach-ux.log`, `bitacora-ux.log`,
`athlete-coach-bitacora-e2e.log`, `weekly-sharing-e2e.log`,
`alembic-current.log`, las matrices JSON y `summary.json`.
Las capturas semanales están en `results/weekly/`.
Estos directorios de resultados son locales y están ignorados por Git.

Reproducción:

```powershell
./scripts/test-weekly-release.ps1 -PublicBaseUrl 'https://<dominio-del-entorno>' -PlaywrightModule '<ruta-al-modulo-playwright>'
```

El runner usa la imagen de pruebas existente `fluxio-whatsapp-tests:phase2`,
registra su ID, ejecuta primero los gates específicos, después regresión y UX,
y finalmente ambos E2E con fixtures independientes. Comprueba hashes del código
productivo antes/después y elimina únicamente sus contenedores y base temporal.
`-E2EOnly` permite recuperar los E2E y sus gates específicos sin repetir la
regresión completa; sus logs anteriores deben corresponder al mismo código.

Imagen registrada:
`sha256:63f83c0226a451897ebd0d62483812f647f4f56535bf004385cefa70cf4d31eb`.

## Riesgos pendientes

- El dominio local respondió 404; falta dominio estable y validación del acceso
  HTTPS en el entorno destino, incluida la foto compartida y sus headers detrás
  del proxy. No se ha validado el release instalado en producción.
- Falta smoke real con Kapso para los tres comandos, usando el dominio destino.
- Downgrade borra los enlaces/copias nuevos. Respaldo previo para rollback.
- Quien tenga el enlace puede leer y copiar lo autorizado. Revocación y
  expiración impiden accesos futuros, pero no retiran copias ya descargadas.
- Notas, resultados y fotos son contenido del atleta. Se omite la identidad de
  transporte; no se garantiza anonimizar un teléfono escrito dentro de una nota
  o visible en la foto autorizada.
- El texto es una copia fija; las fotos referencian el archivo original. Si se
  elimina la foto, el enlace no conserva una copia independiente de ese archivo.
- Expirar o revocar restringe el acceso, pero conserva la copia en PostgreSQL;
  este release no incorpora un proceso de borrado de snapshots.
- `noindex` es una directiva para crawlers y `no-store` para caches; no convierten
  un enlace filtrado en un recurso secreto. Evitar registrar tokens completos en
  logs de proxy/analytics y revisar sus políticas antes de habilitar el release.

## Checklist de deploy (sin ejecutar)

- [ ] Aprobar ventana y confirmar dominio HTTPS estable del entorno destino.
- [ ] Respaldar PostgreSQL y almacenamiento; conservar claves y volúmenes.
- [ ] Configurar `PUBLIC_BASE_URL=https://<dominio>` en app y worker, TTL 168.
- [ ] Confirmar revisión instalada 0020 y una sola cabeza de migraciones.
- [ ] Desplegar la versión aprobada y ejecutar upgrade a 0021 mediante el arranque
  existente; verificar `alembic current` y salud de app/worker.
- [ ] Validar en el dominio destino resumen, enlace anónimo y foto con headers.
- [ ] Crear/abrir/revocar un enlace y comprobar denegación de HTML y foto.
- [ ] Probar con Kapso real resumen/compartir/revocar y confirmar origen del enlace.
- [ ] Confirmar aislamiento A/B, no cache de proxy y políticas de logs/indexación.
- [ ] Registrar evidencia y autorización antes de habilitar a usuarios reales.
- [ ] Si hay rollback, detener la versión que requiere 0021 antes de downgrade
  y restaurar código compatible con 0020; aceptar pérdida de enlaces nuevos o
  recuperar el respaldo correspondiente.
