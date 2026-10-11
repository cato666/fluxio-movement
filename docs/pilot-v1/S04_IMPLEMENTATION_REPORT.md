# S04 — Seguridad del arranque y conservación de credenciales

Fecha: 2026-10-10. Alcance: exclusivamente S04; S05 no iniciada.

Rama: `codex/pilot-v1-stabilization`.
Base aprobada: `7179c17a103c8379ba3413d2acd00020b96f0783`.
Commit funcional final: `42d6627a48fee9a8001ae5051e25d17b87d7fa5d`.
El commit documental de cierre se identifica con `git log -1 --format=%H -- docs/pilot-v1/S04_IMPLEMENTATION_REPORT.md`; su SHA se comunica al entregar la etapa. No modifica el código probado.

Estado de cierre: Lista para revisión final de S04. Todas las pruebas obligatorias locales pasan; publicación no autorizada.

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `app/security_config.py` | Política común de entorno, flags, seed y secretos; errores solo con nombre de configuración. |
| `scripts/start-app.sh` | Validación antes de DB/migraciones, seed condicional, acceso Uvicorn sin URLs en logs. |
| `app/seed.py` | Seed de desarrollo explícito, insert-only, sin actualizaciones de usuarios existentes. |
| `app/database.py` | Validación antes de construir engine; ocultación de parámetros SQL. |
| `app/main.py` | Un solo secreto para firmar/verificar sesiones; HTTPS en producción; logs sin excepciones, stderr ni rutas sensibles. |
| `app/services/auth.py` | Rechazo del login con la contraseña demo heredada en producción, sin reescribir hashes. |
| `app/whatsapp/worker.py` | Misma validación antes de importar DB y antes de cada run_once. |
| `docker-compose.yml` | Seed deshabilitado y sin contraseña demo de respaldo; entorno compartido app/worker y validación incluso si el worker duerme. |
| `.env.example` | Secretos vacíos e instrucciones explícitas de configuración/desarrollo. |
| `tests/conftest.py` | Fixtures declaran desarrollo y habilitación del seed; conserva guard de DB desechable. |
| `tests/test_security_configuration.py` | 40 casos nuevos: producción/desarrollo, claves, logs, arranque y persistencia de credenciales. |
| `docs/pilot-v1/S04_IMPLEMENTATION_REPORT.md` | Evidencia y límites de S04. |

No cambios de modelos, migraciones, dependencias ni contratos HTTP. No nuevos módulos ni tareas posteriores.

## Configuración anterior y nueva

No se registran valores de contraseñas, tokens ni claves en este informe.

| Configuración | Antes | Después |
|---|---|---|
| Entorno | Desarrollo implícito en Python; Compose usa producción por defecto. | Se conserva desarrollo local implícito para la app. Solo development/test/production son válidos; un typo falla. Para seed, development debe declararse explícitamente. Compose continúa usando producción. |
| Sesiones | Respaldo conocido aceptable también en producción; firma de guard leía env en cada petición. | Producción exige secreto explícito de al menos 32 caracteres, 8 caracteres distintos y sin marcadores conocidos de demo/placeholder. Firma y middleware comparten el secreto resuelto. Cookies Secure en producción. Respaldo exclusivamente no productivo. |
| Seed | Automático en cada arranque; upsert reemplazaba hash y metadatos. | Solo APP_ENV=development + ENABLE_DEMO_SEED=true + DEMO_PASSWORD explícito. Producción/test rechazan habilitarlo. Producción rechaza DEMO_PASSWORD configurado. Sin flags no se ejecuta. |
| Usuarios existentes | Arranque podía sobrescribir contraseña e indicador interno. | ON CONFLICT DO NOTHING para ID o username; no cambia hash, nombre, rol, actividad ni privilegios. Solo crea perfiles de usuarios recién insertados. |
| Contraseña demo heredada | Podía iniciar sesión en producción si existía el usuario. | Login 401 genérico en producción; hashes conservados. Una contraseña distinta de una cuenta existente continúa funcionando. |
| PostgreSQL | Python disponía de URL con credencial local de respaldo; Compose exigía valores pero aceptaba placeholders. | Producción exige URL PostgreSQL explícita, usuario, host, DB, puerto válido y contraseña de al menos 16 caracteres sin marcadores inseguros. POSTGRES_PASSWORD, si está presente en el proceso, se valida igual. El respaldo local queda solo fuera de producción. |
| IA | API key vacía por defecto. | En producción la clave es obligatoria si cualquiera de razonamiento, interpretación o voz está habilitada. Flags mal escritos fallan. Deshabilitando explícitamente los tres no se exige clave. |
| WhatsApp | Deshabilitado por defecto; Vault y firma rechazaban configuración ausente cuando se usaban. | Si está habilitado en producción, el arranque exige proveedor Kapso, API key no vacía/no placeholder, ID de número, secreto webhook seguro, lookup key y keyring válidos. Deshabilitado no exige estas claves. |
| Cifrado | Fernet versionado y HMAC de teléfono. | Mismo formato y prioridad de clave única sobre versión actual del keyring. Se conservan versiones históricas válidas. Hash key decodificada >=32 bytes; cifrado Fernet de 32 bytes; ambas con diversidad mínima y separadas. Claves débiles/ausentes/malformadas fallan antes de DB/IA. |
| Logs | Algunas excepciones completas, stderr de FFmpeg, ruta de petición y access log podían revelar parámetros/tokens. | Mensajes genéricos con IDs operativos, sin tracebacks/payloads; SQL hide_parameters; arranque canónico con --no-access-log. |

Las comprobaciones de longitud/diversidad y marcadores no certifican aleatoriedad. Los secretos locales deben generarse con un generador criptográfico. Las API keys son credenciales opacas emitidas por sus proveedores: se exige presencia y rechazo de placeholders, sin inventar formatos específicos ni verificar proveedores reales.

La política se ejecuta antes del polling de PostgreSQL y Alembic en el script. Importar app.main, app.database o el worker en producción también la aplica. No se imprime la URL, JSON de claves ni valor rechazado. El worker valida incluso con el canal deshabilitado en Compose y en cada run_once. La app mantiene configuración de sesión estable durante la vida del proceso; cambios de entorno requieren reiniciar con la nueva configuración.

## Pruebas y entorno

Docker Engine 28.3.2. Imagen existente `fluxio-whatsapp-tests:phase2`, sin rebuild ni descarga de dependencias. Contenedores exclusivos de S04: `fluxio-s04-db-20261010` y `fluxio-s04-tests-20261010`.

PostgreSQL 17.6: DB movement_test nueva en tmpfs; sin volumen persistente. Red `fluxio-s01-validation-20261010`, Internal=true; sin salida a proveedores. Código montado readonly y copiado al filesystem desechable para ejecutar. OpenAI/Kapso reales sin configurar; proveedores de fixtures simulados. Las credenciales sintéticas de producción se generan en memoria, sin llamadas externas.

El guard existente exige TEST_DATABASE_RESET=1 y DB movement_test antes de TRUNCATE. Se ejecutaron migraciones solo en esta DB. La prueba de reinicios usa el script real de arranque (validación, espera DB, Alembic y seed), dos veces en desarrollo y dos en producción; reemplaza únicamente uvicorn por un no-op para terminar el proceso. Ajusta/restaura exclusivamente el password del rol PostgreSQL de este contenedor desechable para satisfacer la política productiva; no toca usuarios ni datos reales.

| Verificación | Resultado |
|---|---|
| Dirigidas finales: S04 + S02 + S03 + contratos | PASS: 93 casos, 40.77 s; incluye 40 S04, 22 S02, 29 S03 y 2 contratos. |
| Python completa sobre contenido final | PASS: 564 casos, 164.16 s; cero FAIL/ERROR/SKIPPED. Incluye 40 S04 y regresiones completas S02/S03, registro, reviews y biomecánica soportada. |
| JavaScript, nueve archivos .test.cjs | PASS: 65 casos, 18.31 s; cero FAIL/SKIPPED. |
| Producción sin sesión válida / con demo / configuración insegura | PASS: import de app y worker y arranque canónico se bloquean antes de DB. |
| Hashes y seed | PASS: hashes de cuenta editada y cuenta real sintética conservados; reinicios repetidos sin cambios; producción no repone demo ausente; seed solo desarrollo explícito. |
| App/worker y cifrado versionado | PASS: ambos imports aceptan configuración válida sin conectar; ciphertext nuevo/histórico se descifra y lookup se conserva. |
| Logs | PASS: error SQL simulado con sentinel sensible no aparece en caplog; errores de configuración no imprimen valores; imports no imprimen claves sintéticas. |
| Compose y script | PASS: docker compose config --quiet, sin arrancar servicios; sh -n; git diff --check. |
| OpenAPI y migraciones | PASS: baseline OpenAPI íntegro y suites de roundtrip/Alembic check; head 0022_administration, sin migraciones nuevas. |
| Copia ejecutada vs candidato | PASS: SHA-256 de 175 archivos app/tests/scripts/migrations y configuración Alembic/pytest coincide; cero diferencias. |
| Workspace original | PASS final: 153 hashes y estado Git iguales a snapshot S01; rama y HEAD originales intactos. |
| Archivos locales y credenciales rastreadas | PASS: 251 rutas rastreadas auditadas; sin .env real, logs, private keys ni artefactos .impeccable; sin coincidencias de patrones de claves privadas/OpenAI. Escaneo heurístico, no certificación universal de secretos. |
| EasyPanel / servicios reales / cuentas y bases persistentes | SKIPPED por restricción; sin conexión ni despliegue. |

Comandos principales, en la copia desechable:

    pytest -q tests/test_security_configuration.py tests/test_whatsapp_account_status.py tests/test_coach_authorization.py tests/test_whatsapp_contracts.py --junitxml=/tmp/s04-targeted-final.xml
    WEEKLY_RELEASE_PUBLIC_BASE_URL=https://fluxio-s04.invalid pytest -q --junitxml=/tmp/s04-full-final.xml

JavaScript: node --test sobre los nueve tests/*.test.cjs, usando runtime bundled y Playwright local. El dominio .invalid solo habilita un test de contrato con FakeProvider; no se contacta.

Las ejecuciones intermedias también pasaron (35 casos S04 iniciales; 92 dirigidas; 563 suite completa antes del último caso de desarrollo explícito). Se repitió la suite tras cerrar esa condición y la validación de URL/markers. Sin errores funcionales detectados. Las tres advertencias de BlockingPortal/on_event son preexistentes.

## Compatibilidad y riesgos de despliegue

- Mantener APP_ENV=production explícito en EasyPanel y ambos procesos. No se examinó su configuración real. El arranque fallará intencionalmente si conserva placeholders, contraseña demo configurada, seed habilitado o secretos obligatorios ausentes.
- Conservar los password_hash actuales. S04 impide sobrescrituras futuras; no reconstruye contraseñas que versiones anteriores ya hubieran reemplazado. Revisar cuentas demo/privilegiadas heredadas de forma administrativa antes de publicar, sin borrado ni resets automáticos. No se certificó qué cuentas existen en EasyPanel.
- El bloqueo de login cubre la contraseña demo histórica conocida. Contraseñas de demostración personalizadas anteriores no pueden identificarse por el hash ni se eliminan automáticamente. Generar un secreto de sesión exclusivo de producción y rotarlo si antes se compartió con desarrollo; la rotación invalida cookies existentes. S04 no incorpora un sistema nuevo de revocación individual de sesiones.
- Se conserva el mínimo de contraseña de usuario existente y el cambio administrativo explícito: esta etapa no fuerza resets globales ni impone una nueva política a cuentas reales.
- Una contraseña DB de menos de 16 caracteres exigirá una intervención coordinada antes del despliegue. Cambiar solo POSTGRES_PASSWORD en Compose no rota la contraseña de un volumen PostgreSQL inicializado. No se realizó esta operación en datos persistentes.
- No sustituir PHONE_HASH_KEY sin un procedimiento compatible con identidades existentes. Conservar keyring/versiones históricas para descifrar datos pendientes. Si una clave histórica es insegura, el nuevo arranque falla; no se rota ni borra automáticamente. La recuperación/rotación operativa requiere revisión específica fuera de S04.
- Rotar el secreto de webhook requiere coordinación con el proveedor. La presencia/fortaleza local no demuestra validez de API keys o permisos del número; validación real sigue pendiente y no autorizada aquí.
- IA habilitada exige clave incluso si aún no hay tráfico. Un ambiente sin servicios reales debe deshabilitar explícitamente las tres funciones IA y WhatsApp, o utilizar fixtures en un entorno aislado.
- Menor detalle en logs de errores para no registrar secretos. El proceso canónico no imprime URLs. Proxies de EasyPanel, logging externo y arranques alternativos de Uvicorn no se verificaron: configurar redacción de tokens/query strings y no habilitar access logs crudos. No se promete redacción universal de logs de infraestructura ajena al proceso.
- Al deshabilitar el seed, un entorno nuevo de producción no crea ningún administrador. El alta operativa debe estar previamente autorizada y preparada con los mecanismos existentes; no se creó una cuenta real en esta etapa.
- El seed insert-only no repara perfiles incompletos ni eleva privilegios de cuentas ya existentes. No hay modificación de datos histórica implícita al arrancar.
- Las autorizaciones S02/S03 y el gate de asignaciones de coach heredadas se conservan; aprobar S04 no certifica esos datos ni autoriza publicación.

## Evidencia, integridad y cierre

JUnit local: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s04-validation-20261010/s04-full-final.xml` (564) y `s04-targeted-final.xml` (93). Se conserva también el resultado intermedio completo (563). Las capturas JavaScript se movieron exclusivamente desde el .impeccable creado por nuestras pruebas a `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s04-js-evidence-20261010/`; no se incorporaron al candidato.

Ambos contenedores S04 detenidos después de exportar evidencia. Datos tmpfs desechables; no borrado de imágenes, contenedores, volúmenes ni recursos existentes. Red interna S01 conservada.

Workspace original: 153 hashes coinciden, estado Git idéntico al snapshot S01; rama `codex/bitacora-entrenamiento`, HEAD `97583b5c191fd48d4282ad42d0b020d6cb1709a1` intactos. Candidato: once archivos funcionales/de pruebas en el commit indicado y únicamente este informe en el commit documental de cierre.

No push, merge, deploy, servicios reales ni migraciones persistentes. No cambios en el workspace original. No S05. Recomendación: aprobar el cierre técnico de S04 tras revisar la política de configuración y sus riesgos operativos. No hay FAIL/BLOCKED en las validaciones obligatorias locales. La validación de secretos, cuentas heredadas y logs de infraestructura de EasyPanel queda pendiente antes de publicar, dentro de sus etapas autorizadas. Trabajo detenido para revisión; no iniciar S05.
