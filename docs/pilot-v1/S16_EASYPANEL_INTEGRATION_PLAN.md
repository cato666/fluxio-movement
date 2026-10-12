# S16 — Integración EasyPanel preparada para aprobación

Fecha: 2026-10-12. Base revisada: 3ce40466b21c99894715e6f9dc01f0ca6dd1eed0, codex/pilot-v1-stabilization. **Preparación PASS; operación BLOCKED; Pilot A NO-GO.** Ninguna operación externa ejecutada.

## Inventario y modelo de instalación

Compose local describe db (PostgreSQL 17.6, postgres_data), app (FastAPI puerto interno 8000, app_storage en /data/storage) y whatsapp-worker (misma aplicación/storage). Estos nombres NO acreditan nombres, redes, rutas, imágenes ni versión reales de EasyPanel. Gastón debe aportar inventario sin secretos: servicios/réplicas, commit y digest API/worker, revisión Alembic, DB/schema/extensiones, volúmenes y STORAGE_PATH, jobs de video/limpieza/otros escritores, proxy/HTTPS y política de reinicio. No acceder a filas o medios para esta inspección preparatoria.

Gastón agregará, solo tras autorización, servicio independiente construido desde backup-runner/Dockerfile del commit publicado autorizado. Sin dominio, puerto, PGDATA, Docker socket o acceso administrativo. UID 10001, filesystem raíz readonly, capabilities eliminadas, no-new-privileges. Fuente de medios REAL montada RO en /source/storage; estado exclusivo RW en /state; secretos RO en /run/secrets; control RO en /control; scratch /work privado tmpfs o disco cifrado aprobado. No montar un volumen vacío sustituyendo el del producto. Verificar permisos sin chmod global. Comprobar que EasyPanel permite estas restricciones y montajes; si no, instalación BLOCKED.

PostgreSQL continúa funcionando; rol exclusivo CONNECT/USAGE/SELECT en todas las tablas/secuencias necesarias, sin propiedad ni superuser/createdb/createrole/replication/bypassrls ni DML/TRUNCATE. Revisar membresías, funciones SECURITY DEFINER, schemas y RLS para completar mínimo privilegio: la guarda del runner sobre tablas no constituye auditoría completa del rol. No conceder bypass para hacer pasar un dump. Preparar default privileges por propietario bajo autorización separada.

Red privada DB y salida HTTPS a R2/Telegram, nunca PostgreSQL público. No asumir egress disponible en una red interna; Gastón confirma DNS/TLS/rutas sin abrir puertos. Watchdog separado: solo /state y Telegram, sin DB/media/AES/R2. Compose es referencia, no instalación ejecutada.

Runner no depende de app ni worker para arrancar ni usa su entrypoint; depende de DB disponible, montajes correctos, estado persistente, secretos y pausa externa. Mantener servicios independientes: detener API/worker no debe detener DB/runner/watchdog ni provocar su reinicio automático por supervisores. No actualizar API o worker durante el respaldo.

## Variables y archivos privados exactos

Contrato completo: [environment.example](../../backup-runner/environment.example). Gastón introduce valores privadamente, nunca copia .env.example del producto al runner.

| Grupo | Variables / valores preparados |
| --- | --- |
| Activación | BACKUP_RUNNER_ENABLED=false; BACKUP_SCHEDULE_ENABLED=false; TELEGRAM_ALERTS_ENABLED=false hasta aprobación |
| Destino | R2_ENDPOINT (HTTPS privado); R2_BUCKET=fluxio-movement-backups; R2_REGION=auto; R2_ACCESS_KEY_ID; R2_SECRET_ACCESS_KEY |
| Clave | BACKUP_AES_KEY_FILE=/run/secrets/aes256.key; BACKUP_AES_KEY_ID=versión existente aprobada en KeePassXC |
| PostgreSQL | BACKUP_PG_SERVICE=fluxio_backup; PGSERVICEFILE=/run/secrets/pg_service.conf; PGPASSFILE=/run/secrets/pgpass |
| Rutas | STORAGE_PATH=/source/storage; BACKUP_STATE_PATH=/state; BACKUP_WORK_PATH=/work; BACKUP_QUIESCENCE_FILE=/control/maintenance.json |
| Versión | BACKUP_SOURCE_COMMIT=SHA completo de la aplicación respaldada, no asumir que coincide con el runner |
| Agenda | BACKUP_DAILY_TIME=03:00 propuesto, no aprobado; BACKUP_SCHEDULE_TIMEZONE=America/Santiago |
| Capacidad | BACKUP_MAX_SET_BYTES=536870912; BACKUP_COMMAND_TIMEOUT_SECONDS=600; BACKUP_STALE_HOURS=24; BACKUP_MAX_RUN_SECONDS=1800 |
| Alertas | TELEGRAM_BOT_TOKEN; TELEGRAM_CHAT_ID autorizado; TELEGRAM_ALERT_TIMEOUT_SECONDS=10; TELEGRAM_ALERT_MIN_INTERVAL_SECONDS=60; TELEGRAM_ALERT_DAILY_LIMIT=20 |

Archivos secretos: aes256.key binario existente de 32 bytes; pg_service.conf con DNS privado/puerto/DB/rol/TLS; pgpass con contraseña y escapes libpq. Permisos POSIX 0400/0600 y directorio 0700 legibles por UID 10001. No generar ni reemplazar claves. Comparar recuperación y descifrado por key_id sin mostrar bytes. Custodiar además todas las versiones de claves del producto y configuración necesaria fuera de EasyPanel; la clave AES del backup no sustituye claves WhatsApp/sharing.

Referencia de recursos: tmpfs 3 GiB/RAM 4 GiB/CPU 1, NO capacidad aprobada. Medir set y staging (~5 veces set), memoria total VPS y tiempo antes de instalar. Mantener retención siete diarios y pre-release durante piloto; retention solo propone, sin borrado automático. R2 Object Read & Write puede permitir DELETE: el código no elimina, pero no afirmar que el token impide eliminación. Verificar reader independiente para recuperación.

## Pausa segura y WhatsApp: bloqueo obligatorio

El webhook POST /webhooks/whatsapp/kapso vive dentro de API: firma verificada, accept y commit antes del ACK. Inbox tiene unicidad provider/provider_message_id; outbox dedupe_key. Esto protege reentregas con ID estable, no mensajes que nunca llegaron. El runner exige ausencia de otros clientes PostgreSQL y pausa de todos los escritores; API viva con webhook escribiendo NO es compatible con este diseño.

No hay modo de mantenimiento/drain coordinado implementado ni controlador de pausa en runner. El worker tiene bucle continuo sin handshake específico de drenaje. **Requiere ventana explícita; continuidad del webhook sin interrupción no está soportada.** No crear ahora relay, cola externa o nueva arquitectura.

Antes de autorizar ventana, Gastón debe verificar contrato Kapso de conservación/reintento ante indisponibilidad/503: horizonte máximo, IDs estables, recuperación/replay, descarga de medios y orden. Esa garantía no está acreditada por el código. Si no se verifica, respaldo diario loss-free WhatsApp BLOCKED: solicitar decisión explícita de mantenimiento y conciliación, sin afirmar ausencia de pérdidas. Un proxy jamás debe responder 200 sin persistencia; propuesta 503 debe aprobarse/configurarse por Gastón y probarse con autorización de canal real. No deshabilitar ni cambiar webhook sin evaluar qué ocurre con eventos pendientes.

Procedimiento futuro, ejecutado exclusivamente por Gastón:

1. Autorizar ventana/duración y método de retención de entradas, inventario de escritores y rollback de configuración. Avisar mantenimiento. Registrar estados operativos agregados sin teléfonos/contenido.
2. Bloquear NUEVAS operaciones de escritura en ingress; permitir terminar las ya iniciadas según capacidades reales del proxy. Incluye todos los hosts/réplicas/rutas administrativas, jobs programados y accesos internos. No dar falsos ACK al webhook. No inventar un flag de aplicación inexistente.
3. Drenar solicitudes/IA/video/envíos ya iniciados mediante evidencia de procesos y estados agregados. La cola PENDING puede permanecer: será respaldada. No exigir vaciarla consumiendo proveedores. Evitar nuevos claims del worker requiere coordinación operativa todavía no implementada: si no se demuestra drenaje, abortar, no matar un envío para simularlo.
4. Pausar/detener todos los escritores con mecanismo aprobado, impedir autorestart y verificar réplicas/procesos detenidos, transacciones y clientes DB cerrados. Monitores que conectan a DB también deben cesar: guarda actual rechaza cualquier otro cliente, incluso readonly.
5. Solo entonces emitir maintenance.json vigente, scope all-db-and-storage-writers, writers_paused=true, SHA de aplicación, storage_path=/source/storage, issued_at/expires_at UTC <=30 min. Es declaración humana, no prueba de pausa. Registrar evidencia sanitizada fuera del archivo.
6. Ejecutar run --kind daily o pre-release; snapshot READ ONLY exportado, inventario/copia/hashes y comprobación final sin clientes. Si ventana expira o drift aparece, aborta. No extender marker sin verificar de nuevo.
7. Mantener pausa hasta resultado COMPLETE y proceso terminado. El código permite separar conceptualmente captura/upload, pero **no expone handshake fiable capture-complete para reanudación temprana**. No usar existencia de dump o receipt INCOMPLETE como permiso para reanudar. Si ejecución falla/interrumpe, verificar que no queda captura activa y lock liberado antes de reactivar; conservar recibo/objeto incierto y no repetir automáticamente. Duración total debe medirse y aprobarse.
8. Invalidar marker, restaurar supervisión y levantar misma versión API/worker; verificar seguridad/DB/health antes de abrir ingress. start-app.sh ejecuta alembic upgrade head al arrancar: comprobar de antemano coincidencia de revisión y misma imagen; cualquier upgrade efectivo requiere autorización de migración separada. Seed deshabilitado. No combinar con release.
9. Recuperar entradas retenidas solo por mecanismo probado, con mismos IDs. Mantener S02–S08, cuotas, TTL y orden de fragmentos; leases SENDING vencidas quedan UNCERTAIN, no reenviar automáticamente. Inbox PROCESSING puede recuperarse por lease, pero comprobar reservas inciertas y no forzar retry. Revisar FAILED/402 y caducados individualmente. Conciliar IDs y conteos antes/durante/después sin contenidos. Cualquier pérdida/duplicación bloquea aceptación.

## Primer respaldo representativo y restauración

Checklist pendiente, todos los puntos necesitan evidencia real autorizada:

- [ ] Inventario/versiones/migraciones/rutas y escritores verificados por Gastón; permisos/RO/egress/capacidad confirmados.
- [ ] Claves existentes, key_id y recuperación independiente; writer/reader separados; destinos privados confirmados.
- [ ] Plan WhatsApp y drenaje probado, ventana y reanudación autorizadas; sin upgrade implícito.
- [ ] Ejecución única pre-release o daily; exit 0, receipt COMPLETE, SHA remoto, GCM y manifiesto verificados, sin datos privados en logs.
- [ ] Restore aislado independiente, tiempo total medido, Telegram del job recibido; reporte sin registros personales.

Restaurar en entorno NUEVO privado y cifrado, sin red/rutas hacia producción, OpenAI/Kapso y scheduler deshabilitados. Usar reader para descargar objeto aprobado, SHA del recibo, clave recuperada desde KeePassXC y key_id. PostgreSQL compatible, perfil RESTORE_PG_SERVICE, BACKUP_RESTORE_ISOLATED_CONFIRMED=true, DB vacía movement_restore_*, storage destino inexistente. Comando preparado:

```text
python /opt/fluxio-backup/pilot_backup_restore.py --source <archivo-cifrado-aprobado> --storage-destination <directorio-nuevo> --expected-sha256 <sha-del-recibo> --key-id <version-custodiada>
```

Sin clean/create/seed/migraciones. Provisionar roles/extensiones/permisos aparte bajo aprobación: dump omite owner/ACL. Aplicación aislada del mismo commit, storage montado en ruta lógica original (p. ej. /data/storage), no en ruta de staging /source/storage si las referencias son absolutas. Verificar tablas/schemas reales, constraints, usuarios, fotografías, videos reproducibles, análisis, reviews, notas, consentimiento y permisos S02–S08, sin enviar mensajes. Medir RPO/RTO desde descarga/custodia hasta aplicación utilizable. Fallo deja target parcial: no reutilizar ni limpiar sin autorización. Retención/eliminación del restore con datos reales requiere decisión privada explícita.

## Automatización y alertas

Primero ensayo manual representativo. Después aprobar horario y coordinador externo de pausa/drenaje/reanudación: schedule NO lo implementa y no debe recibir credenciales administrativas. Sin coordinador probado, diaria desatendida BLOCKED; no programar marker estático. Slot persistente por fecha local, catch-up y lock evitan duplicados; fallos no reintentan ese día. Conservar estado entre reinicios. Pre-release manual debe terminar antes de aprobar publicación; mantener GitHub Actions existente, sin nuevos gates ni webhook invocado por Codex.

Watchdog independiente detecta faltantes, antiguos e incompletos; Telegram fallido no rompe respaldo, pero entrega debe revisarse. Prueba real futura: fallo controlado en instancia aislada, mismo chat autorizado, una notificación sin datos privados, confirmación humana y evidencia de fallo de notificación si canal falla. No romper PostgreSQL/R2 de producción para probar. Confirmar también alerta cuando runner esté caído; watchdog caído necesita supervisión de Gastón/plataforma. Umbral 24h puede alertar alrededor de la siguiente ejecución: ajustar tolerancia y horario con aprobación.

## Autorizaciones y estado

| Acción | Responsable / autorización pendiente |
| --- | --- |
| Inventario sanitizado EasyPanel | Gastón; no acceso a datos reales de Codex |
| Publicar commit probado | Codex solo después de autorización específica de push; workflow existente |
| Crear servicio/estado/rol/montajes/secretos/egress | Gastón, aprobación infraestructura específica |
| Ventana, proxy y retención/replay WhatsApp | Gastón, contrato proveedor probado y aprobación de interrupción/prueba real |
| Backup representativo y acceso a datos cifrados | Autorización específica set/fecha/destino/operador |
| Restore con datos reales aislado | Autorización separada destino/retención/controles/RTO |
| Telegram de fallo integrado | Un envío al chat aprobado, autorización específica |
| Automatización diaria/watchdog | Solo después de prueba representativa y coordinador de pausa probado |

Validación de esta entrega: revisión estática PASS de webhook commit-before-ACK, unicidad inbox/outbox, leases/UNCERTAIN, guardas de backup, configuración y arranque. Suites y ensayo sintético SKIPPED: documentos únicamente, sin repetir 33 tests +75 regresiones e integración PostgreSQL ya PASS en commit base. Instalación, pausa real, contrato replay Kapso, backup/restore representativo, alerta integrada y scheduler real BLOCKED/NOT RUN. No inferir versión de EasyPanel desde Compose ni cerrar S16 por evidencias sintéticas. Restantes gates Pilot A conservados.
