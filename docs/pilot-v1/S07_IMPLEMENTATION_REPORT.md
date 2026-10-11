# S07 — Autenticación, sesiones y protección de origen

Fecha: 2026-10-11 (America/Santiago). Alcance exclusivo S07; S08 no iniciada.

Rama: `codex/pilot-v1-stabilization`.
Base aprobada: `06ee78c7a45479d6de21cbd598168efd20a7b13d`.
Candidato funcional final: `cccfb90a258800288ea2cdfd6f5923a01df56d25`.
El commit documental de entrega se obtiene con `git log -1 --format=%H -- docs/pilot-v1/S07_IMPLEMENTATION_REPORT.md` y se informa al presentar la etapa.

Estado: **lista para revisión técnica final de S07**. Pruebas locales obligatorias aprobadas; sin FAIL ni SKIPPED en las suites finales. El release permanece NO-GO. Esta etapa no autoriza publicar, migrar bases persistentes ni consumir proveedores.

## Auditoría y política aplicada

Se revisaron login/logout/me, SessionMiddleware y el guard central; mutaciones de bitácora y fotos/audio/interpretación; análisis/reanálisis y reviews/annotations de coaches; administración de usuarios, planes, organización y límites; creación/revocación de shares y vinculación/desvinculación de WhatsApp. Los GET revisados no son comandos de modificación; sus controles de identidad/propiedad se conservan.

La protección central cubre POST, PUT, PATCH y DELETE antes del guard de roles, de los endpoints y de cualquier proveedor. GET/HEAD/OPTIONS conservan su tratamiento de lectura/preflight; no se agrega CORS permisivo. El único endpoint excluido de la política de Origin es `/webhooks/whatsapp/kapso`, cuya firma, tamaño máximo, HTTPS productivo y persistencia antes del ACK siguen siendo obligatorios. La excepción no se extiende a rutas relacionadas ni al enlace de identidad.

### Rate limiting

| Variable | Valor por defecto | Contrato |
|---|---|---|
| `LOGIN_ACCOUNT_LIMIT` | 5 | Intentos por identificador normalizado de login y ventana, exista o no |
| `LOGIN_PEER_LIMIT` | 20 | Intentos por IP efectiva y ventana, compartidos entre identificadores |
| `LOGIN_WINDOW_SECONDS` | 300 | Ventana fija alineada al reloj único de PostgreSQL |

Cada intento HTTP admitido consume el cupo de IP antes de validar el cuerpo; cuerpos inválidos también cuentan. Cada login con cuerpo válido consume además el cupo del identificador normalizado, antes de consultar si existe. Se cuentan éxito, contraseña errónea, usuario inexistente y cuenta inactiva; el éxito no reinicia el contador. El agotamiento devuelve 429 con mensaje uniforme y Retry-After dependiente únicamente del fin de ventana, sin usuario, límites restantes ni información de existencia. Los 401 comparten el mensaje `Credenciales inválidas`.

Se reutiliza `AdminSetting` con la clave interna `login_admission`, no expuesta por la API de configuración. Sus buckets contienen HMAC-SHA256 de ventana/tipo/identificador usando SESSION_SECRET, contador y metadatos de ventana; no contienen nombres, IP sin seudonimizar, contraseñas, cookies ni IDs de usuario. Hay un máximo de 4096 buckets por ventana; saturación deniega nuevos buckets. Al admitir en la siguiente ventana se reemplazan los anteriores; si no hay tráfico quedan los seudónimos de la última ventana, sin historial acumulativo.

Un advisory lock PostgreSQL transaccional serializa cada admisión entre conexiones/procesos. La reserva se confirma en una transacción independiente: fallos de contraseña, rollback del endpoint o nueva instancia de la aplicación no devuelven intentos. El reloj se lee después de adquirir el lock; un retroceso de reloj no reinicia una ventana ya contada. El lock se libera antes de ejecutar scrypt. La indisponibilidad de persistencia/configuración impide autenticar, con respuesta genérica sin detalles de SQL.

Para usuarios inexistentes/inactivos se verifica un hash sintético con los mismos parámetros scrypt; hashes inválidos también realizan trabajo scrypt. El rechazo de la contraseña demo productiva ocurre después de ese trabajo. Las pruebas verifican el trabajo criptográfico equivalente y respuestas uniformes; no prometen tiempo matemáticamente constante para BD/red/sistema operativo.

### Sesiones y CSRF/Origin

Producción requiere `WEB_ALLOWED_ORIGINS`: lista exacta de orígenes HTTPS, separados por coma, sin comodines, credenciales, path, query o fragmento. Se rechazan Origin desconocido, `null`, malformado o múltiple; también solicitudes marcadas `Sec-Fetch-Site: cross-site`. No se deriva la confianza del Host ni de X-Forwarded-Host.

En producción toda mutación web requiere Origin permitido y esquema HTTPS efectivo; ausencia de Origin devuelve 403, incluso con cookie válida. Esta validación estricta constituye la barrera CSRF, junto con SameSite y ausencia de CORS permisivo: no se agrega un token CSRF ni cambian los cuerpos/contratos OpenAPI existentes. Los fetch del frontend conservan su funcionamiento porque el navegador emite Origin automáticamente. Integraciones HTTP productivas con sesión deberán enviar el Origin aprobado; no se habilita fallback por Referer.

En desarrollo/test, ausencia de Origin se acepta exclusivamente para solicitudes sin cabeceras `Sec-Fetch-*`, como TestClient/CLI local. Un navegador identificado por esas cabeceras sin Origin se bloquea. Los orígenes locales por defecto son `http://localhost:8000` y `http://127.0.0.1:8000`; otros puertos requieren configuración explícita. Esta excepción no existe en producción.

La cookie mantiene HttpOnly, SameSite=Lax, Secure en producción, alcance de host y vencimiento firmado de 14 días. Login borra campos previos de sesión y conserva únicamente el ID autenticado; logout elimina la cookie del navegador. Cookies alteradas/vencidas son rechazadas. Las respuestas de autenticación y rechazo de seguridad usan Cache-Control: no-store. Los endpoints siguen consultando el estado/rol/propiedad actuales de la cuenta.

### Proxies

`FORWARDED_ALLOW_IPS` debe estar presente en producción. Puede estar vacío para no confiar en proxies; acepta solo IP/CIDR explícitos, nunca `*`, nombres de host ni redes /0. `scripts/start-app.sh` pasa este valor explícitamente a Uvicorn con `--proxy-headers`; elimina la confianza implícita anterior en loopback. Uvicorn interpreta X-Forwarded-Proto/For únicamente para peers confiables. X-Forwarded-Host no determina el origen permitido.

Compose comparte la misma configuración validada entre app y worker, no incorpora servicios ni cambia redes/puertos. En EasyPanel se debe verificar el dominio público HTTPS, que el proxy preserve Origin y sanee la cadena forwarded, y las IP/CIDR mínimas reales del proxy. La configuración vacía bloquea mutaciones detrás de un proxy HTTP, aunque el health sea sano; no se debe ampliar la lista indiscriminadamente para evitar ese bloqueo. No se visitó ni modificó EasyPanel.

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `app/main.py` | Middleware central; admisión por identificador; hash sintético y limpieza de sesión en login |
| `app/services/auth.py` | Trabajo scrypt también al rechazar hashes inválidos y credencial demo |
| `app/services/login_security.py` | Contadores durables, concurrentes y acotados, reloj DB y telemetría mínima |
| `app/web_security.py` | Política Origin/HTTPS, admisión por IP, preflight de configuración y no-store |
| `app/security_config.py` | Preflight común app/worker y errores CLI sin valores ni traceback |
| `scripts/start-app.sh` | Confianza explícita de proxies; access log continúa deshabilitado |
| `docker-compose.yml` | Variables de orígenes, proxies y login; mismos servicios/redes/puertos |
| `tests/conftest.py` | Límites amplios solo para aislar las suites históricas; S07 ensaya límites reales |
| `tests/test_security_configuration.py` | Configuración productiva sintética y Origin explícito en regresión S04 |
| `tests/test_session_security.py` | Casos S07, concurrencia HTTP/DB, cookies, proxies, sharing/admin y firma |
| `docs/pilot-v1/S07_IMPLEMENTATION_REPORT.md` | Evidencia, contratos y riesgos de la etapa |
| `docs/pilot-v1/GO_NO_GO_CHECKLIST.md` | Estado y tres pendientes heredados visibles, sin certificar release |

Sin dependencias nuevas, cambios de modelo ni migración S07. Head permanece `0023_consumption_reservations`; la cadena se ejecutó desde cero solamente en PostgreSQL tmpfs desechable. No se ejecutaron migraciones persistentes. Cuerpos API, consentimiento weekly-live-v1, cuotas S06 e identidades/reviews S02–S03 no cambian.

## Pruebas y evidencia

| Verificación | Resultado / evidencia |
|---|---|
| Suite Python completa del candidato final | **PASS: 703**, 213,70 s; cero fallos, errores u omisiones; `s07-full-final.xml` |
| Conjunto dirigido S07 + autenticación + configuración S04 | **PASS: 111**, 49,15 s; `s07-targeted-final.xml` |
| Caso adicional HTTPS permitido: admin, bitácora, consentimiento, replay y revocación | **PASS**, ejecución dirigida y también incluido en la suite final |
| Suite JavaScript completa, nueve archivos `*.test.cjs` | **PASS: 69**, 20,897 s; cero fallos u omisiones; interfaz/transportes con servidor simulado |
| Login correcto, erróneo, inexistente, inactivo y hash corrupto | **PASS**, respuestas y trabajo scrypt verificados |
| Cupos compartidos entre conexiones; concurrencia HTTP/DB; recuperación; reloj atrasado | **PASS**, último cupo no excedido, persistencia independiente y recuperación de ventana |
| POST/PUT/PATCH/DELETE: origen permitido, hostil, null/malformado/múltiple | **PASS**, más ausencia de Origin según entorno y metadata cross-site |
| Administración y enlaces compartidos | **PASS**, rechazos sin efecto y flujo HTTPS permitido con opt-in/replay/revocación |
| Cookies de la aplicación productiva, expiración/alteración, logout y limpieza de sesión | **PASS**, producción importada en proceso aislado y composición real de middleware |
| Proxy HTTPS confiable y X-Forwarded-* desde peer no confiable | **PASS local**, middleware real Uvicorn; no acredita EasyPanel |
| Webhook Kapso con firma válida/inválida y excepción acotada | **PASS**, firma verificada localmente, ningún envío físico |
| Regresiones S02–S06 y contratos existentes | **PASS**, incluidas en las 703: cuentas inactivas/colas, coach, credenciales, sharing, cuotas/IA/audio/chat/video |
| Migraciones desde cero en base desechable y head único | **PASS**, candidato/base en `0023_consumption_reservations`; sin migración S07 |
| Fuente ejecutada versus candidato | **PASS**, SHA-256 de 183 archivos de app/tests/scripts/migraciones/configuración, cero diferencias |
| Sintaxis Compose con env-file sintético | **PASS**, `docker compose --env-file <fixture temporal> config --quiet`; sin lanzar servicios |
| Secretos/artefactos locales y estado original | **PASS**, escaneo de patrones sin hallazgos; 153 huellas originales y estado Git intactos |
| E2E integrado navegador/servidor S05 | **BLOCKED**, no sustituido por mocks/TestClient |
| Costos adicionales reales de video; paridad/pruebas EasyPanel y proveedores reales | **SKIPPED / PENDIENTE**, no ejecutados ni autorizados; gates siguen abiertos |

La suite Python deja tres advertencias preexistentes (alias anyio BlockingPortal y eventos on_event/lifespan); no son fallos ni pruebas omitidas. Las ejecuciones completas anteriores de 701/702 casos se preservan como evidencia intermedia y no sustituyen el resultado final de 703.

Comandos principales: `docker exec -w /tmp/s05 -e WEEKLY_RELEASE_PUBLIC_BASE_URL=https://fluxio-s07.invalid fluxio-s05-tests-20261010 pytest -q --tb=short --junitxml=/tmp/s07-full-final.xml`; dirigido: el mismo runner con `tests/test_session_security.py tests/test_basic_auth.py tests/test_security_configuration.py`. JavaScript: Node incluido en el runtime, `--test` sobre los nueve archivos `tests/*.test.cjs`, con NODE_PATH hacia las dependencias locales. El dominio .invalid es sintético y se usa por fixtures; no se conecta a un servicio.

Entorno: imagen existente `fluxio-whatsapp-tests:phase2`; PostgreSQL 17.6 en `fluxio-s05-db-20261010` con PGDATA tmpfs y sin volúmenes persistentes; runner `fluxio-s05-tests-20261010`. Red existente `fluxio-s01-validation-20261010`, interna; runner sin puertos publicados, candidato montado read-only y copiado a `/tmp/s05`. Conftest exige TEST_DATABASE_RESET=1 y base exactamente movement_test antes de reset. Proveedores simulados y claves de proveedor vacías en el runner; no se invocaron servicios reales ni se creó ninguna cuenta real.

Evidencia XML y verificación de fuente: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s07-validation-20261011/`. Capturas de interfaz simulada conservadas fuera del candidato: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s07-js-evidence-20261011/`. No sustituyen el E2E integrado pendiente.

Errores corregidos durante la etapa: import faltante detectado antes de colección; cookie de prueba asociada al dominio anterior; identidad de excepción CLI durante preflight; carrera potencial del cambio de ventana detectada en revisión. Ninguno se considera resuelto por omitir pruebas; la evidencia final corresponde a la corrección y su regresión.

## Riesgos y pendientes heredados

- **BLOCKED — S05:** E2E integrado navegador/servidor real. ASGI/TestClient y navegación con backend simulado son evidencias separadas. No se publicó un puerto ni se amplió la red para resolverlo.
- **PENDIENTE — video:** parametrización y verificación del costo adicional de cómputo, almacenamiento y otras operaciones facturables, con reserva/control suficientes. Las pruebas S06 de reserva/fail-closed pasan; no certifican precios ni un techo monetario real. No se cambia ese control en S07.
- **PENDIENTE — EasyPanel:** paridad commit/digest/esquema/configuración/TLS/proxy, validaciones reales autorizadas y smoke del candidato. No ejecutadas; no PASS.
- Una ventana fija admite ráfagas en sus bordes. Una IP/NAT compartida puede agotar el límite conjunto; un tercero puede forzar espera sobre un identificador conocido. Saturación global de buckets deniega identificadores nuevos hasta la recuperación. Para este piloto los valores son configurables sin servicios externos; se debe validar su adecuación operacional.
- El límite por identificador admite los alias de login existentes como identificadores independientes; no se modifica ese contrato ni se informa si pertenecen a la misma cuenta. El límite de IP los agrupa. Rotar SESSION_SECRET invalida sesiones y cambia seudónimos; modificar ventana/límites requiere configuración operativa controlada, coherente entre réplicas.
- Se conserva la sesión firmada sin almacenamiento servidor: logout elimina la cookie local, pero no revoca una copia robada de una sesión aún vigente. Desactivación y checks de permisos actuales sí siguen bloqueando acceso. No se agrega un sistema nuevo de revocación de sesiones en esta etapa.
- La validación de cookies/proxy es local con ASGI y el middleware real de Uvicorn; no acredita los proxies EasyPanel ni reemplaza pruebas del navegador contra el servidor real. No se reconstruyó/publicó una imagen de release.

## Recomendación de cierre

Recomiendo aceptar el cierre técnico local de S07 tras revisar este reporte y el diff del candidato funcional indicado. Las garantías ensayadas de login, origen, cookies/proxy, firma y regresiones pasan. El commit documental de entrega añade exclusivamente este reporte y el checklist actualizado.

Pilot v1.0 permanece **NO-GO** por los tres pendientes heredados y los demás gates de release sin certificar. No se modificó el workspace original, no se amplió/publicó ninguna red/puerto, no se hizo push/merge/deploy ni consumo real. Se detienen solamente los contenedores desechables reutilizados después de copiar la evidencia. S08 no iniciada; esperar revisión explícita antes de otra etapa.
