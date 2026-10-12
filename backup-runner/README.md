# S16 online — implementación local, activación pendiente

Modo offline conserva las guardas y ventana anteriores. El nuevo modo `BACKUP_CAPTURE_MODE=online_v1` exige `BACKUP_MEDIA_PROTOCOL=immutable-v1`, `BACKUP_ONLINE_WRITERS_VERIFIED=true`, `BACKUP_APPLICATION_STORAGE_PATH` igual a la ruta lógica de la app y revisión SQL certificada `0024_training_save_requests`. No activar hasta comprobar que API/worker y todos los escritores ejecutan este candidato, sin scripts externos o DDL/deploy concurrentes.

Online toma un fence SQL compartido contra GC antes del snapshot READ ONLY, lee todas las referencias de TrainingImage/Analysis/WhatsAppMedia del mismo snapshot exportado a pg_dump, y copia/verifica solo esas generaciones inmutables. Crecimientos del storage e inbox posteriores son permitidos; faltantes, cambios, paths inseguros o schema desconocido abortan. Dump y referencias se comprueban de nuevo al restaurar en DB/storage nuevos. Cifrado/R2/key_id/Telegram/scheduler/retención permanecen iguales y desactivados hasta aprobación.

Publicación crea temporales privados, fsync y hard-link atómico sin overwrite; generaciones con permisos 0640. Configurar `BACKUP_MEDIA_READ_GID` al grupo real que permite lectura del volumen RO. No ampliar permisos a todo el sistema ni cambiar archivos persistentes sin autorización. Staging, secrets y state conservan límites/aislamiento existentes. Upload de video no publica referencia SQL hasta tener archivo completo; errores de commit conservan bytes privados para conciliación. GC se difiere sin bloquear webhook si hay captura; cleanup no borra originales compartidos.

Respaldo online no promete guardar archivos temporales no referenciados ni recuperar mensajes posteriores al snapshot tras pérdida del VPS. En restore, proveedores/worker quedan apagados hasta conciliar inbox/outbox y costos; UNCERTAIN sin auto-reenvío. Legacy con referencias faltantes bloquea captura y requiere resolución explícita, nunca se omite silenciosamente.

Evidencia y resultados: [reporte online](../docs/pilot-v1/S16_ONLINE_IMPLEMENTATION_REPORT.md). **S16 operativo BLOCKED / Pilot A NO-GO** hasta ensayo representativo autorizado, paridad/grupo/recursos y automatización real.

---

## Histórico offline (solo aplica al modo offline)

# Backup Runner S16 — instalación manual preparada

**No instalado ni activado.** Gastón administra EasyPanel. Codex no requiere SSH, socket Docker ni credenciales administrativas. Validación local usa únicamente PostgreSQL/media desechables, R2 y Telegram simulados. S16 operativo permanece BLOCKED hasta set representativo y automatización real autorizados.

## Componentes y seguridad

- Dockerfile independiente, PostgreSQL client 17.6 + Python/cryptography/psycopg; base y dependencias fijadas. Usuario 10001, sin puerto/socket/VOLUME PGDATA heredado; entrypoint Python nunca arranca PostgreSQL, seed o Alembic.
- pilot_backup_runner.py: run/daily/pre-release, schedule, health/watch y retention. Captura readonly, encriptación streaming, transporte R2 limitado a fluxio-movement-backups, recibos atómicos y bloqueo OS liberado al morir proceso. No DELETE de R2/media; nuevas generaciones siempre con ID distinto.
- pilot_backup_bundle.py: formato FXS16GCM2, key_id en header autenticado GCM y manifiesto cifrado; nonce 12 y tag 16 bytes. Hashes SHA-256 de dump y cada archivo. Compatibilidad de restore FXS16GCM1 comprobada, no recifrado de objetos previos.
- pilot_backup_restore.py: autorización explícita, ciphertext SHA esperado, key_id, base VACÍA con prefijo movement_restore_, storage NUEVO, sin --clean/--create/upgrade. No arranca aplicación automáticamente.
- Reutiliza required paths/receipt/health/retention de pilot_backup_ops y callback/ledger/rate-limit de Telegram. Resend solo aporta utilidades existentes, no envío o fallback.

## Garantía de coherencia: ventana de pausa obligatoria

El runner **no puede comprobar/controlar toda actividad de filesystem ajena con privilegios readonly**. No afirmar coherencia de un storage vivo por un simple pg_dump o hash. Se exige que Gastón pause API/ingress, worker WhatsApp, video/jobs y TODOS los escritores, drene operaciones y cierre conexiones, antes de emitir maintenance.json en directorio controlado que el runner monta RO.

Ventana incluye writers_paused=true, scope all-db-and-storage-writers, source_commit, storage_path y issued_at/expires_at UTC; máximo 30 min. Configurar valores de maintenance.example.json solo después de comprobar pausa, no marcar true para saltar un rechazo. El archivo es una declaración del operador, no prueba criptográfica de pausa. A diario un controlador externo autorizado (o Gastón) debe crear la ventana vigente; el runner no dispone de privilegios para pausar/reanudar servicios. **No hay backup diario desatendido seguro sin integrar esa coordinación externa**; si falta/venció la ventana, falla y notifica, nunca captura insegura.

Dentro de ventana: snapshot REPEATABLE READ READ ONLY exportado a pg_dump, rol sin capacidad DML/privilegios altos, ausencia de otros clientes DB al inicio/final; copia de TODOS los archivos privados y comparación de inventario/hash antes/copias/después. Cambios o clientes nuevos detectados abortan. Empaquetado/cifrado/upload usan snapshot privado, pero no existe handshake operativo capture-complete. Para la integración actual mantener pausa hasta resultado final y proceso terminado; no reanudar por receipt INCOMPLETE o existencia del dump. Ver procedimiento docs/pilot-v1/S16_EASYPANEL_INTEGRATION_PLAN.md. Inspeccionar recibo COMPLETE antes de dar set por válido. Doble hash es defensa adicional, no sustituto de la pausa; cambios transitorios/actores no coordinados no se garantizan.

## Variables y secretos exactos

Contrato implementado en environment.example:

- Secretos writer: R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. R2_ENDPOINT HTTPS, R2_BUCKET=fluxio-movement-backups y R2_REGION=auto son configuración del destino. No otras cuentas/buckets ni redirects.
- BACKUP_AES_KEY_FILE: archivo binario raw 32 bytes, mount RO privado; BACKUP_AES_KEY_ID: versión existente autorizada en KeePassXC. No generar/reemplazar/reutilizar una clave de ensayo para producción sin decisión explícita. Debe recuperarse desde copia externa, ID exacto guardado en manifiesto.
- BACKUP_PG_SERVICE, PGSERVICEFILE y PGPASSFILE: perfiles libpq, credencial de lectura en archivo pgpass (no DATABASE_URL de SQLAlchemy como argumento). Secret files 0600 o 0400 y legibles solo por UID 10001; directorio privado 0700. Nunca passwords en argv/Compose/Git/logs.
- STORAGE_PATH=/source/storage, BACKUP_STATE_PATH=/state, BACKUP_WORK_PATH=/work, BACKUP_QUIESCENCE_FILE=/control/maintenance.json, BACKUP_SOURCE_COMMIT SHA completo aprobado.
- BACKUP_RUNNER_ENABLED=false, BACKUP_SCHEDULE_ENABLED=false, TELEGRAM_ALERTS_ENABLED=false inicialmente. Tras permisos/ensayo y autorización de activación, Gastón los configura para el servicio, nunca automáticamente en esta entrega.
- BACKUP_DAILY_TIME propuesta 03:00; BACKUP_SCHEDULE_TIMEZONE America/Santiago; hora requiere aprobación. Slot una vez por fecha local, catch-up tras reinicio, sin doble ejecución por horario repetido. Reserva previa persistida, intento incompleto no reintenta automáticamente ese día; operación manual posterior requiere revisar estado/ventana.
- BACKUP_MAX_SET_BYTES=536870912 (512 MiB inicial, hasta 4 GiB), BACKUP_COMMAND_TIMEOUT_SECONDS=600 (1–3600), BACKUP_STALE_HOURS=24, BACKUP_MAX_RUN_SECONDS=1800 (watchdog alerta si job supera umbral); Telegram timeout 10, intervalo 60s, 20 intentos/día UTC. No asumir capacidad de VPS o volumen real por estos defaults.

Restore en instancia aislada usa además RESTORE_PG_SERVICE, BACKUP_RESTORE_ISOLATED_CONFIRMED=true, el reader R2 separado si descarga y la clave recuperada; no necesita writer/Telegram activos ni conexiones al VPS original para descifrar. Conservar por separado versiones WhatsApp/sharing/PHONE_HASH_KEY y config/roles necesarios del producto: **no se meten claves en el archivo cifrado junto al objeto** ni se reconstruyen desde Git.

## Rol PostgreSQL mínimo — lo aplica Gastón bajo permiso

Crear identidad exclusiva, sin superuser/createdb/createrole/replication/bypassrls, sin INSERT/UPDATE/DELETE/TRUNCATE. CONNECT a DB del producto, USAGE en schemas requeridos, SELECT en todas las tablas/secuencias que pg_dump necesita; default privileges por cada propietario para tablas futuras. Rol no debe ser dueño de tablas; runner lo verifica. default_transaction_read_only=on y PGOPTIONS readonly en pg_dump. Si RLS/permisos impiden dump completo, abortar; no habilitar bypass automáticamente. Roles/extensiones/ACL de recuperación se provisionan por el operador aparte: --no-owner/--no-acl no exporta identidades admin ni garantiza reconstrucción de permisos.

PGSERVICEFILE ejemplo privado (sin contraseña):

```ini
[fluxio_backup]
host=<DNS interno real>
port=5432
dbname=<base aprobada>
user=<rol de backup readonly>
# Usar verify-full/certificados si TLS DB está configurado; nunca conexión pública.
```

PGPASSFILE: formato host:port:database:user:password, introducido privadamente por Gastón. Confirmar rutas/escape libpq y permisos sin mostrar contenido. API/worker mantienen sus credenciales normales; no cambiar sus roles aquí.

## Instalación EasyPanel manual — no ejecutar ahora

1. Publicación/instalación requieren autorizaciones futuras. Código actual solo local; no push ni CI modificado. Usar mismo repositorio/candidato autorizado, Dockerfile backup-runner/Dockerfile y registrar SHA/digest de esta imagen. No usar entrypoint de app ni tag mutable sin identificación.
2. Gastón identifica DB, red privada y volumen REAL de medios. Añade runner sin dominio ni puertos: volumen privado en /source/storage **RO**; UID/grupo/ACL debe permitir lectura sin chmod global. No monta PGDATA ni socket Docker. Crear estado dedicado solo con autorización de volumen (existe/externo en template, no se crea silenciosamente).
3. Secrets dir RO, control dir RO y estado persistente /state RW; /work tmpfs privado. Ejemplo Compose propone tmpfs 3 GiB, RAM 4 GiB, CPU 1: **dimensionamiento no aprobado**, ajustar con tamaño/CPU/RAM reales antes de instalar. Staging puede requerir ~5 veces el set para dump/copia/tar/cipher/download/verificación; check de espacio previo aborta. En caso de más capacidad, aprobar scratch cifrado o tmpfs/mem adecuados, no fallback silencioso a disco plano. Máximo configurable no garantiza caber en RAM del VPS.
4. Instalar watchdog separado con command watch, solo estado/Telegram y red egress para api.telegram.org:443, sin DB/media/AES/R2. Ejecutor comparte estado con watchdog; permisos 0700/0600. Modo read_only, cap_drop ALL, no-new-privileges, sin daemon Docker ni creds EasyPanel.
5. Dejar todos los flags false; validar presencia/formato y montajes sin exportar env/inspect Config.Env. Crear/aprobar mecanismo externo de pausa y ventana diaria; no se proporcionan credenciales administrativas a runner.
6. Autorizar primero prueba representativa, backup/restore y notificación controlada. Después aprobar flags/horario, watchdog y daily. Before release: run --kind pre-release manual por Gastón, éxito/backup restaurable como condición de aprobación del push/publicación. Mantener workflow actual, no nuevos gates CI.

compose.example.yml es referencia parametrizada, no servicio instalado. Volúmenes/redes external=true evitan creación de storage vacío por error; campos deben corresponder al inventario real. environment.example tiene valores no secretos y flags false. No cargar .env.example original con todos los proveedores/credenciales de app en el runner.

## Ejecución y recuperación

```text
python pilot_backup_runner.py run --kind daily
python pilot_backup_runner.py run --kind pre-release
python pilot_backup_runner.py schedule
python pilot_backup_runner.py watch
python pilot_backup_runner.py health
python pilot_backup_runner.py retention
```

Dentro de imagen Python es /opt/backup-venv/bin/python y scripts /opt/fluxio-backup/. run devuelve 0 solo COMPLETE; fallo/disabled/busy !=0. schedule/watch son procesos largos pero flags false impiden acciones reales. Leer recibos/ledger no exige APIs de administrador. OS lock se libera al morir proceso; archivo vacío queda, no eliminarlo para forzar concurrencia. Crash conserva INCOMPLETE, posible objeto R2 incierto, y marcador diario evita repetición; comprobar evidencia antes de recuperación manual. IDs de incidente health permanecen estables hasta resolución, evitando reenvío UNCERTAIN con ID nuevo cada hora. Telegram aceptado no prueba lectura.

No borra fotos/videos ni objetos R2. Solo limpia staging **creado por esa ejecución** mediante TemporaryDirectory; interrupción abrupta puede dejar scratch propio hasta reinicio/tmpfs o revisión manual. No limpiar directorios existentes para arrancar. Retention solo propone siete daily COMPLETE y todos los pre-release; incompletos se investigan, sin DELETE. Mantener key_id/versión de claves mientras exista un backup dependiente.

## Restore representativo aislado — requiere autorización separada

Descargar únicamente set aprobado con reader y SHA/key_id del recibo/manifiesto, recuperar clave desde KeePassXC/copia externa, crear NUEVA DB vacía con prefijo movement_restore_ y storage destino inexistente. Proveedores apagados, no entrypoint seed/migrate. Perfil restore libpq privado, clave binaria RO, staging protegido:

```text
python /opt/fluxio-backup/pilot_backup_restore.py --source <cipher-local> --storage-destination <path-nuevo> --expected-sha256 <sha-del-recibo> --key-id <version-custodiada>
```

La confirmación BACKUP_RESTORE_ISOLATED_CONFIRMED=true es permiso operacional opt-in, no prueba de que la instancia sea desechable; Gastón debe verificar aislamiento e identidad. Guardas exigen DB vacía/prefijo y storage nuevo, sin clean/create/downgrade ni overwrite. Si falla tras pg_restore, el target nuevo puede quedar parcial: no repetir sobre él ni limpiar automáticamente; investigar y autorizar otro destino.

Validar 29 tablas del candidato y schemas reales adicionales, conteos/constraints y foto/video/reviews/anotaciones, notas/usuarios/consentimiento/medios privados en app aislada. Al reponer app, montar los archivos en **la misma ruta lógica STORAGE_PATH original**: DB puede guardar rutas absolutas; no reescribirlas ni confundir el path de staging del runner con /data/storage. R2/header-hash/tag y archivos verificados no sustituyen smoke de aplicación, versiones de claves cifradas de app ni RPO/RTO real. Registrar tiempo total incluyendo download/bóveda/DB/storage/arranque. No cutover, borrar originales o activar proveedores implícitamente.

## Evidencia local y límites

33 tests runner PASS (R2 HTTP simulado, fallos/cifrado/secrets, concurrencia, SIGKILL/lock, scheduler/health y >128 MiB). 28 legacy +31 Telegram +16 utilidades reutilizadas PASS. Integración real PostgreSQL desechable: pg_dump con rol readonly, DB vacías restauradas v2/v1, 29 tablas, notas/reviews y cuatro archivos equivalentes a PNG/MP4 decodificables; client extra y drift filesystem rechazados. Imagen final por hash coincide con código, user 10001 y ningún VOLUME PGDATA heredado, puertos o Docker socket. Sin R2/Telegram reales.

No certifica que la pausa real funcione, ni capacidad/permisos/TLS/red del VPS, secret runtime recuperable, recepción de alerta del job real, backup/restore representativo, uso de claves productivas y operación diaria. S16 operativo sigue BLOCKED hasta esas pruebas autorizadas. No implementar nueva arquitectura empresarial ni módulos de producto.
