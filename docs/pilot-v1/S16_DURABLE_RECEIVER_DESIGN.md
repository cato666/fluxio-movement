# Actualización normativa — medios antes del ACK

2026-10-12. Decisiones base aprobadas condicionadamente; implementación NO autorizada. [Contrato vigente de medios](S16_MEDIA_CONTINUITY_DESIGN.md) sustituye reference_only, fetch posterior al ACK y todas las garantías relacionadas del texto anterior. Para foto/audio admitidos, ningún HTTP 200 hasta bytes completos validados/cifrados, asociación durable y consentimiento aplicable. SQLite/10 GiB/72h/pendientes conservados; spool4GiB, grants y mitigación externa son propuestas pendientes. S16 BLOCKED / Pilot A NO-GO. El resto del diseño se conserva como base y no habilita construcción.

---

# S16 — Diseño mínimo de receptor durable Kapso

2026-10-12. Referencia 113e39a02de740efe845bf2b10a0dc10b4125df5. **Diseño para revisión, implementación NO autorizada. S16 BLOCKED / Pilot A NO-GO.** Sin cambios de código funcional, servicios, infraestructura, datos reales o proveedores modificados/ejecutados.

## 1. Arquitectura y garantías

Propuesta: un servicio receiver independiente y permanente, una réplica, un proceso dueño de SQLite y volumen privado exclusivo /var/lib/fluxio-ingress. Tres componentes lógicos: entrada HTTPS, dispatcher privado pausable y monitor. No Redis/RabbitMQ. Dispatcher puede ser tarea del mismo proceso con estado durable; su crash no convierte la cola en volátil. Separar módulos/privilegios; receiver nunca usa DATABASE_URL, OpenAI ni credencial de envío Kapso.

Flujo: Kapso -> proxy HTTPS estable -> firma/límites -> evento cifrado + commit durable -> HTTP200. Dispatcher -> ruta privada autenticada de API -> validación original -> inbox actual + commit -> recibo -> estado INGESTED. Worker principal procesa posteriormente bajo S02–S08. Durante backup: receiver activo, dispatcher PAUSED sin requests/conexiones a API, API/worker/video/otros escritores drenados y detenidos. DB principal permanece activa. Backup Runner conserva rol/mounts/guardas; no captura volumen vivo de receiver.

Garantía objetivo: ningún evento válido confirmado se pierde en reinicios controlados del receiver si volumen y fsync funcionan; replay at-least-once y efectos idempotentes por IDs originales. NO exactly-once global, NO garantía ante pérdida del disco/VPS/proxy/proveedor ni de medios que solo se referencian. Fallos anteriores al commit no reciben200. El receptor añade latencia y nuevos datos sensibles; no es un simple cambio de URL.

Para no perder durante cambio inicial, activar/verificar receiver antes de cambiar proxy, mantener destino viejo hasta comprobar nueva ruta efectiva, deduplicar ambos; no detener app en esa transición. URL pública /webhooks/whatsapp/kapso estable; acceso público directo al webhook original bloqueado al finalizar transición. No toggles de URL por cada backup.

## 2. Almacenamiento: comparación y elección propuesta

| Criterio | A SQLite cifrado/volumen propio | B PostgreSQL independiente | C objetos R2 u otra cola existente |
| --- | --- | --- | --- |
| Operación/despliegue | Un servicio y volumen, mínimo | DB nueva, servicio receiver, roles/TLS/monitor/migraciones/backup adicionales | R2 ya existe para backups, NO cola autorizada; requerir bucket/credencial/política propios |
| Integridad/concurrencia | Transacciones, índices únicos, un escritor serial; suficiente piloto | Transacciones/locks/concurrencia superior, innecesaria para 15 atletas | PUT durable por objeto, pero evento/estado/leases/orden no son transacción multiclave; implementar ledger/claims |
| Cifrado | AES-GCM por evento + volumen cifrado; SQLite normal NO cifra páginas automáticamente | AES-GCM por payload + volumen/TLS; motor no sustituye cifrado aplicación | AES-GCM antes PUT + TLS; claves/índices opacos |
| Reinicios | Volumen local persistente, fsync/commit y leases | WAL/fsync/recovery DB propia | Objetos sobreviven proceso; reconstruir estado/cursor, controlar writes ambiguos |
| Backups | Snapshot online consistente SQLite separado, cifrado y restore probado | Dump/snapshot propio separado del principal | Durabilidad remota no sustituye versión/retención/backup; borrado/clave puede perder datos |
| Pérdida VPS | Pierde eventos posteriores a última copia externa | Igual si mismo VPS; DB externa cambia costo/operación | Objetos externos sobreviven VPS si ACK solo después de confirmación remota; receptor sigue necesitando estar disponible |
| Esfuerzo relativo | Bajo-medio, recomendado para continuidad de mantenimiento | Medio-alto; no justificado por tráfico | Medio-alto para orden/idempotencia/claims; posible si se exige RPO0 ante pérdida VPS |

Elegir A como mínimo para reinicios/mantenimiento; riesgo VPS debe aceptarse expresamente o elegir C con persistencia remota pre-ACK antes de implementar. No reutilizar token ni bucket fluxio-movement-backups para ingress. No hay otra cola durable instalada acreditada.

SQLite WAL requiere filesystem LOCAL compatible, un host y un escritor; WAL synchronous=FULL, foreign_keys=ON, busy timeout limitado a2 s, checkpoint bajo coordinación del mismo dueño. No usar NFS/SMB ni copiar solo .db mientras WAL está vivo. Usar backup API online con snapshot consistente y verificar. Fijar SQLite >=3.51.3 o backport corregido acreditado: documentación advierte WAL-reset bug en versiones anteriores. Verificar versión real de librería runtime, no solo Python. [WAL](https://www.sqlite.org/wal.html), [synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous). SQLCipher no se incorpora por defecto: requerirlo cambiaría dependencias/build/pruebas. Cifrado por registros no permite afirmar archivo SQLite íntegramente cifrado; volumen cifrado obligatorio para metadatos/artefactos.

R2 tiene lectura/listado consistentes tras escritura, pero no da por sí mismo transacciones entre objetos o orden de conversaciones. [Consistencia R2](https://developers.cloudflare.com/r2/reference/consistency/). Si se elige C, especificar CAS/leases/ledger y costos antes de implementar.

## 3. Contratos API/eventos

PROPUESTOS, no endpoints implementados nuevos:

- Público POST /webhooks/whatsapp/kapso: TLS, Content-Type JSON, body<=262144 bytes (contrato existente), X-Webhook-Signature y X-Webhook-Event; conservar X-Idempotency-Key y datos batch/sequence si existen. No transformar bytes firmados. Firma HMAC verificada antes de parse/store, normalización existente y destino/número/eventos permitidos. No logs de body, URL media, firma, headers completos o teléfono. POST sin cookies: misma excepción de sesión webhook, sin crear bypass a endpoints web.
- GET /health/live: vida del proceso; GET /health/ready: capacidad de verificar/encriptar/commit, no necesita API activa. Solo estado genérico al público; profundidad/control privados.
- Control privado POST /internal/ingress/pause y /resume con autenticación de operador exclusiva, TLS/mTLS, audit actor opaco/reason/window/version. Nunca accesible por dominio público. Pause persiste estado/no-new-claims, espera inflight=0, devuelve paused=true, generación y watermark; NO pausar entrada HTTPS. Resume exige API verificada, inventario/coherencia y decisión sobre consumo; no reintenta salidas UNCERTAIN.
- Replay usa destino interno /webhooks/whatsapp/kapso de la API existente sobre HTTPS, bytes/header originales, mTLS o autenticación adicional dedicada validada antes de ingestión. Proxies preservan scheme y confianza S07. No inventar firmas nuevas. Se propone recibo verificable añadido al contrato interno: ingress_receipt_id, hash del cuerpo/evento, todos los IDs normalizados persistidos o duplicados, commit confirmado. Compatibilidad: respuesta pública existente se conserva; receipt interno es ampliación de seguridad a implementar/pruebar, no ya disponible.
- HTTP200 solo tras incorporación transaccional de TODO envelope al inbox. accepted=0 puede ser duplicado legítimo; no inferir entrega correcta por cualquier200 de proxy. Timeout del ACK interno es ambiguo: conservar evento y repetir ingestión con mismos IDs; esto no es reenvío WhatsApp ni nueva IA. 401/403/400/413/hash conflicto: cuarentena/alerta, no bucle. 503 durante mantenimiento: dispatcher pausado, sin sondeo agresivo.

Dedupe de entrega: HMAC secreto sobre namespace provider/número + X-Idempotency-Key si presente. Fallback a fingerprint de envelope firmado/normalizado sin generar ID de mensaje nuevo. Además índice único de mensaje normalizado (provider, destino, evento, provider_message_id), compatible con received vs status del inbox. Batch mantiene envelope cifrado y membership de mensajes; nuevos mensajes y duplicados se concilian por item. Un ID ya visto con cuerpo/semántica distinta se pone en cuarentena, no se sobrescribe. No usar delivery ID como único dedupe de mensajes entre batches diferentes.

## 4. Modelo de persistencia y estados

Schema PRIVADO receiver, independiente de Alembic/DB del producto:

| Entidad | Campos mínimos |
| --- | --- |
| envelopes | local_uuid, delivery_hmac UNIQUE, ciphertext, nonce/tag/key_id, schema_version, body_hmac, accepted_at, state, bytes, last_error_code |
| items | local_uuid, envelope_uuid, item_index, message_hmac UNIQUE, conversation_hmac, event_type, sequence nullable, local_order, original_time cifrado, state, lease_owner/generation/until, attempts, next_attempt_at, inbox_receipt cifrado, ingested_at |
| envelope_members | envelope_uuid/item_index UNIQUE -> item_uuid; permite que un mismo mensaje figure como duplicado en diferentes entregas/batches sin nueva ejecución |
| control | singleton mode RUNNING/PAUSING/PAUSED, generation, window_id, paused_at, heartbeat |
| media_spool (solo si aprobada) | opaque_uuid, item_uuid, encrypted_blob_reference, key_id/hash cifrado, bytes, mime, status, processor_receipt, confirmed_at |
| notification ledger | incident_uuid/código, counters, estado/tiempos; reutilizar política Telegram sin payload |

ACTIVE RECEIVED -> LEASED -> INGESTED, o RETRY_WAIT/QUARANTINED. Lease tras crash vencida vuelve a replay seguro de ingestión; nunca cambian IDs. INGESTED significa inbox durable, NO DONE ni envío WhatsApp. PENDING incluye RECEIVED/LEASED/RETRY_WAIT/QUARANTINED hasta resolver; no eliminar por edad. Tombstone de message/delivery HMAC para dedupe: propuesto8 días, separado de payload 72 h y sujeto a aprobación; coincide con ventana de mensajes de7 días actual. Tras retirar tombstone, inbox mantiene unicidad histórica, pero recuperación vieja puede no estar disponible. Índices sin texto/phone/IDs privados en claro.

AES-256-GCM por envelope/media, nonce único por clave, AAD con schema/local_uuid/key_id y namespace; HMAC de índices con clave separada, sin hash de teléfono sin secreto. Claves raw32 en archivos RO, keyring de versiones previo, no generar ahora. Metadata de estado no equivale a anonimización absoluta. Cifrar identificadores recibos y campos de negocio; solo opacos/contadores al monitor.

## 5. Orden, pausa y replay

Un dispatcher con claims transaccionales; una operación por conversación, se permite intercalar otras. Reproducir orden durable local y usar sequence Kapso cuando esté presente; no ordenar ciegamente por timestamp de segundos. Un envelope/batch atomiza ingestión y mantiene orden interno. Retries no dejan adelantar Guardar/Corregir al evento precedente de la misma conversación. Gaps/errores de una conversación -> cuarentena de esa secuencia, alerta; otras siguen. Kapso puede entregar originalmente fuera de orden; no prometer reconstrucción global ni causalidad que no se recibió.

API viva debe persistir todo backlog de una conversación antes de habilitar procesamiento de esa conversación: diseño mínimo propuesto durante catch-up es worker PAUSADO hasta ingresar corte inicial y nuevas entradas ordenadas, luego reactivar bajo límites. Con llegada continua definir watermark por conversación; pruebas deben impedir que worker procese Guardar antes de propuesta todavía en relay. No convertir mantenimiento en vaciado facturable de cola.

Handshake pause del dispatcher no drena worker/video/API: se requiere control no-new-claims del worker y finalización de tareas actual; aún pendientes de implementación/coordinación aprobada. Tras pause y verificaciones, API/worker/jobs detenidos, runner captura fuentes inmóviles. Reanudar API con misma imagen/head, sin migración/seed involuntarios; probar health, habilitar ingestión privada, catch-up, luego worker solo con autorización de consumo. No liberar reservas inciertas ni cambiar política402/429/UNCERTAIN.

## 6. Capacidad de24 h y retención

Base piloto15 atletas:20 entradas/día =300;20 salidas/día =300 y supuesto conservador tres estados por salida=900. Total1200 mensajes/eventos diarios esperados. Retries, control/batches/estados extra no están acotados por esas cuotas: diseñar5000 items únicos/día, hasta20000 intentos/día; duplicados no duplican payload. Mantener límite body 256 KiB, incluso al batchear; lotes mayores fallan413, configuración proveedor debe respetarlo. No ampliar contrato actual en silencio.

Dimensionamiento extremo eventos:5000 envelopes/día *256KiB =1.22GiB/día;24 h pendientes +72 h procesados=4.88GiB, overhead/WAL/copias/backup => volumen inicial propuesto10GiB; debe validarse con stress y overhead real. <=5000 items no limita bytes por sí solo: capacidad bytes es guarda independiente. Alerta70%, crítica85%, nuevas admisiones bloqueadas95% o reserva mínima512MiB; no ACK falso ni eliminación de pendientes para hacer espacio. Capacidad24 h no promete conservación infinita: pendientes>24 h alerta y ampliación/intervención, no borrado. Tráfico firmado abusivo puede exceder supuestos; controles de rate/backpressure no garantizan recuperación Kapso si rechazan.

Retener envelope procesado72 h DESDE que TODOS sus items tengan recibo durable del inbox; nunca desde llegada. Pendientes se conservan hasta ingreso confirmado o decisión explícita de descarte por privacidad/inválido, auditada, sin aplicar TTL72 h. Inbox actual rechaza mensajes>7 días, tiene payload24 h y outbox23h: alerta replay30min objetivo en operación normal, inmediata por edad>1h fuera de mantenimiento; al24 h incidente, al7 días cuarentena/decisión; no reescribir timestamp para eludir controles. Mantenimiento esperado20 min aprobado por separado. Tombstones8 días, ledger operativo7 días propuestos requieren aprobación.

Backup propio de receiver con SQLite online backup a staging cifrado, sin copiar db/WAL a ciegas, verificación key_id/hash y restore aislado. Frecuencia/horizonte/destino propio pendientes; una copia posterior al ACK deja RPO>0 ante pérdida VPS. No incluir cola viva en Backup Runner principal ni pausar receiver para respaldar producto. Pérdida VPS exige copiar/restaurar cola y conciliar inbox/outbox reales antes de replay; no ejecutar automáticamente todo histórico contra DB antigua porque pudo haberse enviado respuesta antes de la pérdida.

## 7. Fotografías y audio: decisión de privacidad pendiente

Contrato observado: media_reference=media_id; app ya resuelve URL al descargar, 8MiB para imagen/audio y16MiB video. [Kapso media](https://docs.kapso.ai/api/meta/whatsapp/media/get-media-url) distingue URL Meta5 min y download_url Kapso4 min con expires_at. No almacenar tokens/URL como referencia permanente. Duración de media_id entrante recuperable por24 h NO acreditada aquí; página Meta no accesible durante consulta. No afirmar30d/7 días sin contrato aplicable. Probar renovación y recuperación real con autorización posteriormente.

**Default de diseño MEDIA_MODE=reference_only.** No descarga/spool sin política explícita. Conservar referencia cifrada y resolver URL fresca al replay, respetando MIME/límites/rutas anti-SSRF existentes, sin redirects a URLs arbitrarias. Esto NO cierra garantía de conservación de fotos/audio24 h: gate BLOCKED hasta prueba/garantía proveedor o aprobación de spool.

Opción propuesta si no se garantiza media_id: servicio auxiliar lógico media-fetcher sin IA/envío, solo referencia de evento firmado, credencial lectura de medios y egress allowlist, almacenamiento cifrado propio sin fuente del backup. Descarga temprana fuera del request ACK (<10 s): tras persistencia de evento; archivo temporal cifrado streaming -> fsync -> rename atómico + fsync directorio -> commit vínculo; crash conserva evento y permite reconciliar blobs huérfanos. Si ACK precede captura, existe riesgo explícito de media expirada/fetcher detenido; no afirmar que ACK garantiza bytes aún no descargados.

Para garantía completa de medios exigir disponibilidad proveedor durante tiempo máximo de fetch/retry medido o no certificar flujo; descargar antes de ACK no garantiza cumplir deadline con archivos grandes. No esconder ese compromiso. Fetch solo tras política de privacidad aprobada: propósito continuidad, tipos foto/audio, retención, destinatarios/operador y tratamiento de cuentas inactivas. Receptor sin DB durante pausa NO puede verificar is_active actual: descargar basándose en cache puede contrariar privacidad; aprobar mecanismo/alcance explícito o aplazar captura hasta validación de cuenta. Bloqueo IA/envíos S02 siempre en backend actual.

Spool propuesto<=300medios/24 h *8MiB =~2.35GiB; volumen cifrado4GiB con guardas70/85/95% y límites de bytes reales, no confianza en Content-Length. MIME+magic validados, no descompresión/transcripción ni fetch video ampliado automáticamente. No credencial de envío al fetcher; si Kapso no ofrece alcance lectura, reconocer permiso excesivo y aprobar mitigación antes de instalar.

Replay de media preserva payload firmado; adapter interno download_media consulta spool por referencia/recibo autorizado y valida hash/tamaño, sin alterar firma/media_id ni nuevo acceso público. Esto es cambio futuro necesario en provider/media y endpoint interno, NO disponible hoy. El worker sigue verificando cuenta/reserva antes de consumir. Eliminar bytes SOLO tras recibo explícito de procesamiento: imagen persisted en almacenamiento principal y transaction committed; audio transcripción committed/estado confirmado; INGESTED no basta. Audio no se copia a registros públicos. Propuesta borrado lógico spool tras confirmación (sin72 h extra de binarios), pendientes nunca eliminados automáticamente; parametrizar límite y revisar excepción por cuenta desactivada, error terminal o privacidad. Política debe aprobarse antes de habilitar descarga.

No garantizar borrado físico seguro en SSD/SQLite/WAL/snapshots: cifrado y ACL, retención de copias y destrucción de claves según dependencias. Retirar refs/borrar archivo evita acceso normal, no prueba irrecuperabilidad. No borrar objetos R2 ni claves compartidas para limpiar un solo mensaje. Eliminaciones y jobs deshabilitados inicialmente, ensayo sintético requerido.

## 8. Errores y alertas

Firma inválida401; payload inválido400/413; identidad de evento en conflicto409/quarantine; disco/key/commit no disponible503 sin200. Rate-limit429 previo a persistencia solo si capacidad/abuso lo exige, con alerta riesgo de pérdida por retries finitos. Duplicado confirmado200 sin nuevo consumo. SQLite busy reintento local acotado dentro de ACK objetivo<=5 s/deadline<10 s, luego503; no drop.

Replay timeout/5xx -> estado RETRY_WAIT con backoff1/5/15/60s y máximo20 intentos activos antes de cuarentena notificada, conserva pending y manualresume; pause no incrementa attempts.401/403/config y400/413 terminal -> quarantine, no retry-loop.402 en cualquier operación potencialmente facturable -> sin retry automático, controlesS06/S08; replay interno no genera402 de proveedor ni modifica sender. Fallo de Telegram no interrumpe entrada/commit; guardar notificación fallida durable, sin tokens/contenido. Reutilizar rate/timeout/ledger Telegram.

Alertas propuestas: INGRESS_STORAGE_WARN/CRITICAL/FULL, INGRESS_COMMIT_FAILED, INGRESS_KEY_UNAVAILABLE, INGRESS_REPLAY_DELAY/FAILED, INGRESS_PAUSE_STUCK, INGRESS_MEDIA_PENDING/FAILED, INGRESS_BACKUP_STALE. Incidente estable, dedupe60s/máx20diarias existente, no bucle por mensaje. Durante mantenimiento aprobado evitar falsa alarma breve, pero no suprimir full/key/fallo captura; monitor externo del proceso caído necesario (no puede alertarse a sí mismo estando muerto). Solo códigos/contadores/IDopaco/tiempos, sin phone/WAMID/body/token. Retrasos acumulados y notificación fallida aparecen en control privado.

## 9. Variables/secretos propuestos (no implementados)

| Grupo | Nombres / defaults propuestos |
| --- | --- |
| Entrada | INGRESS_ENABLED=false; INGRESS_ALLOWED_PHONE_NUMBER_IDS; INGRESS_ALLOWED_EVENTS; INGRESS_MAX_BODY_BYTES=262144; INGRESS_ACK_TIMEOUT_SECONDS=5 |
| Persistencia | INGRESS_DB_PATH=/var/lib/fluxio-ingress/inbox.sqlite; INGRESS_MAX_BYTES=10737418240; INGRESS_MIN_FREE_BYTES=536870912; INGRESS_CAPACITY_ITEMS_24H=5000; INGRESS_BUSY_TIMEOUT_MS=2000 |
| Cifrado | INGRESS_AES_KEY_FILE; INGRESS_AES_KEY_ID; INGRESS_AES_KEYRING_FILE; INGRESS_INDEX_HMAC_KEY_FILE; KAPSO_WEBHOOK_SECRET_FILE (reutilizar versión original privadamente) |
| Replay/control | INGRESS_REPLAY_ENABLED=false; INGRESS_BACKEND_URL=HTTPS interno exacto; INGRESS_REPLAY_AUTH_FILE; INGRESS_CONTROL_AUTH_FILE; INGRESS_TLS_CA_FILE; INGRESS_TLS_CLIENT_CERT_FILE; INGRESS_TLS_CLIENT_KEY_FILE; INGRESS_REPLAY_TIMEOUT_SECONDS=5; INGRESS_REPLAY_MAX_ATTEMPTS=20; INGRESS_LEASE_SECONDS=30 |
| Retención/monitor | INGRESS_PROCESSED_RETENTION_HOURS=72; INGRESS_TOMBSTONE_RETENTION_DAYS=8; INGRESS_PENDING_ALERT_HOURS=1; INGRESS_REPLAY_DELAY_SECONDS=1800; INGRESS_STORAGE_WARN_PERCENT=70; INGRESS_STORAGE_CRITICAL_PERCENT=85; INGRESS_STORAGE_STOP_PERCENT=95; INGRESS_CLEANUP_ENABLED=false |
| Media opcional | INGRESS_MEDIA_MODE=reference_only; INGRESS_MEDIA_PRIVACY_APPROVED=false; INGRESS_MEDIA_PATH; INGRESS_MEDIA_KEY_FILE/ID; INGRESS_MEDIA_MAX_FILE_BYTES=8388608; INGRESS_MEDIA_MAX_BYTES=4294967296; KAPSO_MEDIA_READ_KEY_FILE; KAPSO_PHONE_NUMBER_ID |
| Backup cola | INGRESS_QUEUE_BACKUP_ENABLED=false; INGRESS_QUEUE_BACKUP_INTERVAL_MINUTES (por aprobar); INGRESS_QUEUE_BACKUP_DESTINATION (por aprobar, diferente set principal); credenciales/retención propias por definir |
| Telegram | TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ALERTS_ENABLED=false, TELEGRAM_ALERT_TIMEOUT_SECONDS=10, TELEGRAM_ALERT_MIN_INTERVAL_SECONDS=60, TELEGRAM_ALERT_DAILY_LIMIT=20 |

La autenticación API del replay no sustituye los chequeos de identidad/actividad del worker: durante la pausa el receiver no consulta usuarios. Mantener la captura cifrada como dato mínimo temporal, nunca interpretar su ACK como autorización del atleta. Cuotas de admisión del receiver son operativas, adicionales a S06; replay al inbox no debe cargar inbound usage más de una vez por mensaje.

Los nombres nuevos no son configuración actual; implementar validación fail-closed/no fallback secretos. Exclusivas key/secret files RO UIDprivado0400/0600; valores no Git/.env.example/logs. Key de ingress/media/control no sustituye backup/WhatsApp; custodiar versiones en KeePassXC/copia externa. No generar claves sin permiso. Flags privados control no exponen secretos ni replay público.

## 10. Configuración EasyPanel propuesta

Gastón instala tras autorización de publicación/infraestructura: imagen del commit aprobado, una réplica, UIDno-root, capdrop/no-new-privileges/rootRO, puerto interno HTTPS únicamente a proxy, sin acceso administrativo/Docker socket/PGDATA. Proxy TLS público termina o re-encripta a receiver; replay HTTPS privado/mTLS a API, allowlist de hostname/ruta/IP y confianzaforwardedS07. Volumen propio10GiB cifrado LOCAL que sobreviva stop/recreate, permisos0700; SQLite/db/WAL bajo él, no temp. RAM propuesta256–512MiB/CPU0.5–1 pendiente de benchmark. Spool separado4GiB solo si aprobado. Sin DB principal/medios fuente en receiver; sin depends_on app/worker que detenga receiver. Confirmar cifrado de disco real: etiqueta volumen no prueba cifrado.

Receiver comparte runtime con monitor/dispatcher lógico, no requiere otro DBserver. Durante PAUSED dispatcher no mantiene pools a DB principal ni solicita backend; estas conexiones causarían rechazo del runner. Readiness de receiver no depende de salud app. Restart controlado cierre transacciones/leases y recuperación de WAL sin limpiarvolumen; falla de readiness nunca genera nuevos200. No disponer despliegue simultáneo de réplicas que compartanSQLite; actualización rolling incompatible con una réplica debe probar continuidad y riesgo retries, no confundir independencia de mantenimiento principal con alta disponibilidad del propio receiver.

Workflow GitHub existente intacto; cambios de routing/secrets/roles/montajes los aplica Gastón tras permiso, no SSH de Codex. No scheduler de backup real hasta ensayo y coordinación de escritores. API startup Alembic/seed y recuperación de análisis siguen requiriendo versión/head y drenaje, independientemente del receiver.

## 11. Pruebas/gates necesarios

- Firma exacta/headers/eventos/batches/body límites, dedupe entrega y mensaje, colisión ID, timestamps; logs/DB/WAL/temp sin datos sensibles en claro.
- Crash antes/tras commit/ACK; filesystem fsync real, reinicio controlado, WALcheckpoint concurrente/runtimecorregido, disco lleno/key ausente; ningún200 sinpersistencia.
- HTTP privado/receipt spoof/proxy200 rechazados; commit inbox seguido timeout; replaydup sin nuevo usage/IA/outbox; cuentas inactivas/revocadas y consentimientoS02–S08.
- Orden Guardar/Corregir, batches mezclados/duplicados, cola continua durante catch-up, leases expiradas y pause/no-new-claims; UNCERTAIN nunca reenviado.
- Capacity5000 únicos/20000 intentos/24 h y peor body; retención72 h desde confirmación, no borrar pending, tombstones8 días, backupSQLite/restore independiente; bloqueo de eliminación inicial.
- Media con proveedor simulado: URL4/5 min, renovación,404/429/402, tamaño/mime/SSRF, spoolcrash/fsync/hash, cuenta desactivada, recibo ingestiónvsprocesamiento, borrado lógico/retención/keyring.
- PostgreSQL/media desechables: API/worker apagados mientrasreceiverpersiste; dump consistente sin otrosclientes; restoreproducto+colaconciliada y recibos; no duplicar salidas tras restoreanterior.
- EasyPanel futuro autorizado: cifrado/volumen/red/versiones, transición inicial/recepciónfirma, alertaentregada, foto/audioavailabilityreal, ventana/dropnetwork/restart sin pérdidas confirmadas. Sin pruebas reales no certificar continuidad.

## 12. Estimación y decisiones pendientes

Diseño base metadata+SQLite+replay+pause+receipts/seguridad+monitor+tests:6–9 días técnicos (incluye controles de drenaje acotados); integración/validación autorizada1–2 días adicionales. Spoolmedios+adapter/reciboprocesamiento añade3–5d. Persistenciaexterna pre-ACK o nuevaDB añade alcance/costo, reestimar. No compromiso de plazo ni autorización de trabajo.

Decisiones para revisión: aprobarSQLite en volumen cifrado/RPO ante pérdida del VPS o exigir remoto pre-ACK; capacidad10GiB(+4GiBopcional) y recursos; tombstones8 días/política respaldocola propia; modalidadmedios/privacidad de cuentas desactivadas/borrados; identidadservicios/roles/custodia de secretos y recibo interno. 72 hprocesados y conservaciónpending según condiciones del usuario ya incorporados. No pedir confirmar nuevamente esos requisitos.

Riesgos residuales: caídaVPS/proxy, filesystem que ignore sync, secreto comprometido, exceso tráfico/retries finitos, cola atrasada fuera de TTL, orden original incompleto, media no descargable, falta de alcance de lectura en Kapso, snapshot del producto antiguo con salidas ya entregadas, cifrado del volumen no disponible, monitor caído. Ninguno se marcaPASS por diseño. Recomendación: aprobar selección/privacidad y luego autorizar implementación LOCAL; mantener S16 BLOCKED hasta evidencia operacional. Consulta/documento/revisión estática PASS; suites SKIPPED(sin código) , controlesyensayos NOT RUN. No implementación/servicios/EasyPanel/push/deploy/proveedores.
