# S16 — Continuidad de fotografías y audio: contrato para aprobación

2026-10-12. Referencia: 9847d2f4554189e6629666d0d5d0dc41fb4138ff. Decisiones aprobadas: receptor independiente, SQLite separado, eventos cifrados, ACK durable, replay privado, idempotencia, 10 GiB sujeto a validación, retención de eventos incorporados de 72 horas, pendientes hasta conciliación y sin HA completa. **Solo diseño; implementación NO autorizada. S16 BLOCKED / Pilot A NO-GO.** Este documento sustituye el ACK anticipado y reference_only como solución final de medios del diseño anterior.

## 1. Contrato de ACK y límite de viabilidad

Texto: HTTP 200 después del commit del evento cifrado. Foto/audio admitidos: HTTP 200 únicamente cuando TODOS los eventos y medios requeridos del envelope tengan consentimiento aplicable, bytes completos validados, cifrado autenticado y vínculo durable en estado READY. Una referencia, reserva de espacio, archivo parcial o promesa de retry no permite ACK exitoso. Un duplicado pendiente tampoco recibe 200; un duplicado READY sí, sin repetir descarga.

[Kapso overview](https://docs.kapso.ai/docs/platform/webhooks/overview) exige 200 dentro de 10 segundos. [Delivery](https://docs.kapso.ai/docs/platform/webhooks/advanced) documenta tres intentos por defecto y agotamiento aproximado a los 50 segundos. [Media API](https://docs.kapso.ai/api/meta/whatsapp/media/get-media-url) distingue URL Meta válida cinco minutos y download_url Kapso válida cuatro minutos, con expires_at. No se acreditó duración recuperable del media_id entrante.

Propuesta: deadline total de ocho segundos por request, con dos segundos de margen para proxy/commit; metadata y descarga comparten ese límite. Si no queda READY, responder 503 y conservar evento/job durable. La descarga puede continuar con reintentos acotados; un retry posterior obtiene 200 solo si todo quedó READY. Si Kapso agotó sus intentos, el receptor conserva lo adquirido y permite replay autorizado, pero no puede convertir retrospectivamente un fallo del proveedor en ACK exitoso.

Garantía: medios confirmados no se pierden en reinicios controlados con almacenamiento sano; dependencias fallidas nunca desaparecen silenciosamente. No garantiza adquirir un archivo que el proveedor dejó de ofrecer, cumplir deadline con cualquier batch o sobrevivir pérdida física del VPS. Un medio nunca adquirido queda DEPENDENCY_UNRECOVERABLE y genera alerta/conciliación, nunca éxito. Si 8 MiB o batches no cumplen el plazo, el piloto sigue bloqueado hasta una decisión explícita de límites/configuración/contrato; no debilitar ACK.

## 2. Arquitectura y consentimiento

Receiver permanente con tareas de entrada, fetch, monitor y dispatcher; estados y leases en SQLite, no en RAM. Durante mantenimiento receiver/fetch continúan; dispatcher PAUSED, API/worker y demás escritores drenados y detenidos. SQLite y spool propios, fuera de PostgreSQL y almacenamiento respaldados. Backup Runner sin cambios.

No existe evidencia específica de consentimiento para spool en el código revisado. Vinculación de WhatsApp y consentimiento S05 para compartir no equivalen a esa autorización. Política propuesta: registro privado y continuidad, exclusivamente fotos/audio, cifrado, acceso técnico mínimo, retención hasta procesamiento/conciliación, eliminación posterior y tratamiento de revocación. Debe aprobarse y registrarse para cada atleta antes de capturar bytes.

Proponer ledger independiente de grants, firmado por autoridad privada: sujeto/vínculo mediante HMAC propio, grant_id, policy_version, tipos permitidos, revisión de identidad/actividad, issued_at/valid_until y revocaciones durables. No compartir PHONE_HASH_KEY ni claves con frontend. Un flag global de privacidad no sustituye el grant individual.

Una cache de actividad sin sincronizar desactivaciones es insuficiente. Desactivación, desvinculación y retiro de consentimiento deben revocar durablemente el grant antes de confirmar el cambio; si esa coordinación falla, bloquear admisiones del sujeto o la ventana. Claims y revocaciones se serializan; revalidar grant al commit READY. Durante pausa, cambios de autorización externos deben usar ese control o quedar suspendidos. No suponer que API apagada elimina todos los escritores.

Sin grant vigente: no descargar ni almacenar bytes; evento mínimo cifrado en CONSENT_BLOCKED, sin ACK de éxito de registro. Su disposición requiere conciliación, no descarte silencioso. Revocación posterior bloquea captura/replay/uso; la resolución de bytes retenidos por privacidad será individual y auditada. Backend mantiene controles is_active, reservas y consentimiento S02–S08 antes de IA, uso o publicación. Este mecanismo de grants es un cambio futuro necesario, no implementado.

## 3. Descarga temprana y validación

Foto: JPEG/PNG/WebP. Audio: OGG/application-ogg, WebM, MP4, WAV/x-wav; reutilizar MIME admitidos del worker. Máximo 8 MiB (8388608 bytes) por archivo, medidos realmente. MIME, magic/estructura y tamaño deben concordar; limitar CPU/memoria si la validación requiere decodificar. No transcribir ni analizar en receiver. Video queda fuera de este incremento de spool; su límite existente no autoriza captura temprana.

Resolver exclusivamente media_id del evento firmado y destino permitido. Reutilizar allowlist HTTPS api.kapso.ai y path de descarga existente; sin redirects o URLs arbitrarias del usuario. URL/token solo en memoria de la operación, nunca en logs/DB. Validar hash SHA-256 del proveedor cuando esté disponible y longitud real frente a metadata; URL expirada requiere resolver una nueva por ID. Un 404 de URL no acredita media_id inexistente.

Reservar espacio durable antes del fetch, inicialmente hasta 8 MiB más overhead si se desconoce tamaño; dedupe por evento/referencia impide downloads paralelos. Propuesta: dos fetch concurrentes, configurable solo tras benchmark. No mantener una transacción SQLite abierta durante la red. Un batch requiere todos sus medios READY antes del ACK; concurrency=2 puede superar deadline, debe probarse. Contrato de webhook conserva body máximo de 256 KiB. No cambiar batching Kapso aquí.

## 4. Persistencia y recuperación

| Entidad propuesta | Datos mínimos |
| --- | --- |
| media_dependencies | item_uuid, reference_hmac, media_uuid, grant_id/revision, estado, attempts, lease, retry_at, error_code |
| blobs | UUID/path opacos, key_id, bytes, metadata/hash cifrados, recibos READY/procesamiento y tiempos |
| event_media_members | Vinculación durable con evento/item; índices únicos por namespace, mensaje y referencia |

Media_id, MIME y datos de negocio quedan cifrados; índices HMAC, no teléfonos o nombres originales. Formato propuesto FXINGMEDIA1: AES-256-GCM streaming, nonce único de 12 bytes, tag de 16, header limitado y AAD que liga schema/key_id/blob/evento/grant. SHA/longitud privados autenticados. Claves propias versionadas en archivos RO y KeePassXC; no generar ni sustituir claves en esta etapa.

Secuencia requerida:

1. Commit de evento, dependencia y reserva.
2. Claim/lease FETCHING y obtención de URL nueva.
3. Streaming cifrado hacia .part del job, sin plaintext temporal en disco.
4. Finalizar GCM, validar tamaño/tipo/hash, fsync del archivo.
5. Rename atómico al blob opaco y fsync del directorio.
6. Commit SQLite del vínculo, READY, recibo y ajuste de reserva.
7. HTTP 200 únicamente si todas las dependencias del envelope están READY.

No hay atomicidad ficticia entre filesystem y SQLite. Crash antes del vínculo: reconciliar blob completo mediante manifest privado/autenticación, o continuar job pendiente; no borrar un blob válido sin conciliación. Archivo parcial nunca se sirve. READY con archivo ausente/tag inválido es CORRUPT: bloquear ACK/replay y alertar. Verificar autenticación completa antes de liberar plaintext al backend. .part propio irrecuperable puede limpiarse solo después de confirmar ausencia de job activo y autorización de la política; jamás equivale a borrar un medio pendiente válido.

## 5. Estados y fallos

| Estado | Regla |
| --- | --- |
| CONSENT_BLOCKED | Sin bytes/fetch ni ACK exitoso |
| FETCH_PENDING / FETCHING / FETCH_RETRY_WAIT | Evento y reserva conservados; sin 200 hasta READY |
| READY | Bytes completos cifrados, validados y vinculados; habilita ACK del envelope completo |
| INBOX_CONFIRMED | Inbox/mapping comprometidos; no autoriza limpiar medio |
| PROCESSING | Backend tiene lease; no borrar |
| PROCESSING_CONFIRMED | Resultado o referencia privada comprometidos; elegible para limpieza aprobada |
| CLEANUP_PENDING / CLEANED | Limpieza lógica idempotente con recibo y sin lease activo |
| QUARANTINED / CORRUPT / DEPENDENCY_UNRECOVERABLE | Conservar evidencia, alertar y conciliar; no éxito ni retry ilimitado |

Propuesta: cinco ciclos automáticos máximos de metadata/descarga por medio, backoff 1/5/15/60 segundos con jitter. 429 respeta Retry-After; 402 bloquea retry; 401/403 de configuración y media_id definitivamente no disponible pasan a cuarentena. Timeout/5xx de GET conserva job y reserva; no representa un envío WhatsApp incierto. URL expirada se renueva dentro del presupuesto de intentos. Costos desconocidos no se liberan.

Al agotar intentos, conservar pending y generar incidente estable. Recuperación manual individual autenticada/auditada revalida grant, identidad y presupuesto; mismos IDs. Nunca reenviar salientes UNCERTAIN o repetir IA para recuperar spool. Alertas y conteos distinguen recibido, ACK, READY, inbox y procesado; cada diferencia queda explicada. Si contenido se perdió antes de adquirirlo, la conciliación puede solicitar un nuevo archivo solo con autorización y revisión de registros previos, evitando duplicados.

## 6. Replay y procesamiento confirmado

Preservar cuerpo/firma/media_id originales. Replay privado con sidecar autenticado que liga evento, blobs, hashes y grants; backend confirma incorporación transaccional de todos los mensajes y mapping en inbox. accepted=0 no acredita por sí solo la disponibilidad de medios. Endpoints/mapping/recibos son cambios futuros compatibles con contratos públicos, no implementados hoy.

Provider wrapper interno consulta spool por media_reference y recibo autorizado. Acceso HTTPS privado con mTLS/credencial dedicada y lease por inbox; no URL pública, frontend key o presigned link. Devuelve DownloadedMedia al pipeline actual tras comprobar GCM/hash/tamaño y cuenta activa. Si receipt exige spool y falta/corrompe el blob, no fallback silencioso al proveedor. Buffer máximo 8 MiB en RAM, sin archivo claro persistente. Foto se guarda por flujo usual; audio transcribe bajo S06.

PROCESSING_CONFIRMED requiere commit del worker y recibo durable autenticado: inbox/mensaje/blob/hash, resultado PERSISTED_PRIVATE_IMAGE o TRANSCRIPT_COMMITTED, referencia opaca/versionada. Download 200 o inbox commit no bastan. Si callback falla, consultar estado privado y reemitir el mismo recibo, sin nueva IA; proponer ledger de notificación transaccional independiente del outbox WhatsApp. Una transcripción solo en RAM no es confirmación: ensayar error posterior de interpretación y recuperación.

FAILED/EXPIRED/CANCELLED/inactive no autoriza borrar automáticamente. Conciliar privacidad y resultado. Orden por conversación y no-new-claims/leases se mantienen; drain del worker/API/video es independiente del pause del dispatcher. Reanudar con misma imagen/head y sin migración/seed involuntaria, luego catch-up y worker según permiso de consumo.

## 7. Retención y limpieza

Eventos incorporados conservan 72 horas desde INGESTED, conforme decisión aprobada. Medios pendientes se conservan hasta procesamiento/conciliación aunque superen 72 horas. Default cleanup deshabilitado; tras PROCESSING_CONFIRMED y sin lease, unlink solo del blob opaco propio, fsync directorio y commit CLEANED. Crash después de unlink se resuelve idempotentemente con ENOENT; no afectar fotos/audio del storage principal ni borrar R2 o claves compartidas.

Tombstones mínimos HMAC/recibo: propuesta ocho días, pendiente de aprobación. Consentimiento retirado requiere disposición individual según política de privacidad. Borrado lógico no acredita borrado físico en SSD/WAL/copias; volumen cifrado, claves y retención de snapshots deben cubrir residuales. Cryptoerase por archivo requeriría DEK por blob y gestión de wraps/copies adicional; no prometerlo por borrar path. Mirrors no usan lifecycle que elimine medios pendientes por edad.

## 8. Capacidad, recursos y costos

15 atletas × 20 entradas/día = hasta 300 medios si todas las entradas son archivos. 300 × 8 MiB = 2,34375 GiB/24 h. Proponer spool cifrado propio de 4 GiB, adicional a 10 GiB de eventos; validar overhead, .part, WAL y reservas. Alertas 70%, crítica 85%; bloquear nuevas reservas al 95% o margen libre menor a 512 MiB. No ACK falso ni purga para hacer espacio. Más de 24 horas pendientes requiere alerta/ampliación autorizada; no se promete capacidad infinita.

Propuesta 0,5–1 CPU y 512 MiB–1 GiB RAM, dos fetch concurrentes; benchmark requerido para deadline, streaming/decoders/IO. No usar tmpfs como almacenamiento durable.

Costos por fórmula, no tarifas: normalmente dos GET por medio, hasta 600 GET/día; cinco ciclos conservadores implican hasta 3000 GET/día. Verificar si lecturas, storage, egress y cómputo son facturables. Mirror cada cinco minutos tiene 288 slots/día: no copiar 4 GiB completos cada vez (~1,125 TiB/día). Usar blobs inmutables incrementales y snapshots/manifiestos pequeños; medir PUT/GET/bytes/retención antes de estimar USD.

Presupuesto S06 US$3/día y US$30/piloto no se amplía. Si hay cargos, definir reserva conservadora y escrow durable reservado desde el presupuesto global ANTES de pausar: ledger de ingress consume esa asignación idempotentemente sin DB principal; no crear segundo presupuesto paralelo. Parámetros faltantes/costos no verificados bloquean operaciones facturables. Costos desconocidos quedan reservados. Este escrow es trabajo futuro, no capacidad actual. No IA ni envíos físicos por ACK/fetch.

## 9. Mitigación mínima ante pérdida del VPS

SQLite/spool locales sobreviven reinicios con volumen sano, no pérdida del VPS/disco. Proponer copia cifrada externa independiente cada cinco minutos y antes de ventana/release, sin HA: SQLite online backup y blobs inmutables referenciados, manifiesto/hashes/key_id, lease que impida cleanup durante copia y restore desde KeePassXC. Destino/credenciales separados de backups principales, pendientes de aprobación; nada creado.

RPO objetivo cinco minutos, no garantizado si copia falla/se atrasa; alertar y conservar última copia completa. RTO propuesto una hora para receptor, por medir. Se pueden perder eventos ACK posteriores a la última copia. Si ese riesgo no se acepta, persistir evento y medios fuera del VPS ANTES del ACK; incrementa costo/latencia, pero no requiere construir HA completa. La decisión de excluir HA no autoriza automáticamente perder ACK.

Restaurar exclusivamente en entorno aislado: DB de cola, blobs/keyring, hashes, READY y leases. Conciliar con inbox/outbox del producto antes de replay, especialmente si DB principal volvió a snapshot anterior y algunas respuestas ya se enviaron. No reenviar histórico masivamente. Política de retención de mirrors/procesados pendiente; no borrar objetos ni claves por esta preparación.

## 10. Configuración EasyPanel propuesta

Gastón instalará tras autorización: receiver independiente una réplica, root readonly/UID privado/capabilities eliminadas/no-new-privileges; volúmenes locales cifrados exclusivos de eventos y medios, secretos RO. Ruta TLS pública estable solo para webhook; blobs/replay/grants/receipts/control privados HTTPS/mTLS. Sin PGDATA, storage principal, Docker socket o admin credentials. No depends_on que detenga receiver con API/worker.

Fetcher tiene egress solo api.kapso.ai:443 y credencial de lectura si el proveedor admite ese alcance. Si token también permite enviar, reconocer privilegio excesivo y aprobar mitigación de rutas/credenciales; no llamarlo read-only comprobado. Nada de secretos en frontend/Git/.env.example/logs. Keeper de claves independiente/versionado; no generarlas ahora.

Variables nuevas PROPUESTAS, no implementadas:

| Grupo | Nombres y defaults |
| --- | --- |
| Activación/privacidad | INGRESS_MEDIA_ENABLED=false; INGRESS_MEDIA_MODE=durable_before_ack; INGRESS_MEDIA_PRIVACY_POLICY_VERSION; INGRESS_MEDIA_GRANTS_PATH; INGRESS_MEDIA_GRANT_VERIFY_KEY_FILE |
| Fuente | KAPSO_MEDIA_READ_KEY_FILE; KAPSO_PHONE_NUMBER_ID; firma original según diseño base |
| Spool/crypto | INGRESS_MEDIA_PATH=/var/lib/fluxio-ingress-media; INGRESS_MEDIA_AES_KEY_FILE; INGRESS_MEDIA_AES_KEY_ID; INGRESS_MEDIA_AES_KEYRING_FILE |
| Límites | INGRESS_MEDIA_MAX_FILE_BYTES=8388608; INGRESS_MEDIA_MAX_BYTES=4294967296; INGRESS_MEDIA_MAX_CONCURRENT_FETCHES=2; INGRESS_MEDIA_FETCH_MAX_ATTEMPTS=5; INGRESS_ACK_TIMEOUT_SECONDS=8 |
| Confirmación/limpieza | INGRESS_MEDIA_PROCESSING_RECEIPT_AUTH_FILE; INGRESS_MEDIA_CLEANUP_ENABLED=false; umbrales 70/85/95 y margen 512 MiB |
| Costos | INGRESS_MEDIA_COST_RESERVATION_USD; INGRESS_MEDIA_COST_ESCROW_FILE; fail-closed si no se acreditan costos/asignación |
| Copia externa | INGRESS_QUEUE_MIRROR_ENABLED=false; INGRESS_QUEUE_MIRROR_INTERVAL_SECONDS=300; INGRESS_QUEUE_MIRROR_DESTINATION y secret files propios por aprobar |

Telegram conserva variables/rate/timeout/ledger existentes. Alertas: MEDIA_FETCH_DELAY/FAILED, DEPENDENCY_UNRECOVERABLE, CONSENT_BLOCKED, STORAGE_WARN/CRITICAL/FULL, INTEGRITY_FAILED, REPLAY_FAILED, PROCESSING_RECEIPT_MISSING, CLEANUP_FAILED y MIRROR_STALE/FAILED. Solo código/contador/edad/UUID opaco, sin URLs/tokens/phone/contenido. Fallo Telegram se registra sin romper commit; receiver caído necesita supervisión externa. Scheduler/pipeline actual no se modifican ni activan.

## 11. Implementación incremental futura

| Etapa | Alcance | Aceptación dirigida |
| --- | --- | --- |
| M0 | Grants/revocación, privacidad, secretos y escrow | Sin consentimiento no bytes; revocación bloquea captura; costos desconocidos bloquean |
| M1 | Evento/dependencias/reservas/leases y ACK gate | Ningún 200 sin READY; dedupe por IDs originales; batches completos |
| M2 | Descarga, cifrado y fsync/recovery | Parciales/corruptos nunca READY; crash conserva eventos/reservas |
| M3 | Replay privado, adapter y recibos comprometidos | Spool READY no llama Kapso; rollback/callback perdido no borra medio ni repite IA |
| M4 | Limpieza opt-in, capacidad y alertas | Nunca borrar pending; full rechaza sin ACK; logs/DB sin secretos privados en claro |
| M5 | Copia externa/restore propio | Manifiesto coherente, claves recuperables, RPO medido y conciliación sin doble envío |
| M6 | E2E desechable, pausa y rendimiento | Foto/audio/texto durante pausa, URL renovada y deadline/picos medidos |

Cada etapa: autorización posterior, commit propio, pruebas dirigidas, reporte y revisión antes de avanzar. PostgreSQL/storage desechables y proveedores simulados. Reales/destino/infraestructura/alertas requieren autorizaciones específicas; no habilitar scheduler implícitamente.

## 12. Pruebas preparadas y criterio de cierre

Matriz necesaria, NO ejecutada en esta entrega:

- URL expiradas de cuatro/cinco minutos, refresh por ID, 404 de URL frente a ID; 401/402/429/5xx/timeout.
- Tamaño anunciado falso, chunks oversized, MIME/magic conflictivos, SSRF/redirects, hash/tag incorrectos.
- Consentimiento ausente/expirado/revocado, desactivación concurrente antes de commit READY y durante replay.
- Crash antes/después de fsync, rename, commit SQLite, ACK, inbox commit, recibo y unlink; recuperación de leases y blobs huérfanos.
- Duplicados concurrentes y batches superpuestos, mismo ID/hash distinto, orden Guardar/Corregir y archivos múltiples.
- Full de WAL/spool, reservas colgadas, backlog de 24 h, cleanup nunca elimina pending; mensajes sin ACK visibles.
- Receipt perdido, transcripción comprometida con interpretación fallida, rollback antes de confirmación; no IA repetida ni salientes UNCERTAIN.
- Medio READY usado con URL proveedor ya vencida, sin GET Kapso; acceso público privado denegado, claves nunca frontend.
- Restore de producto anterior y mirror posterior: conciliación de inbox/outbox/costos; no replay masivo inseguro.
- Backup principal mientras receiver/fetch persisten en su volumen independiente, cero clientes del dispatcher en DB principal.

Aceptación: todos los ACK de medios admitidos tienen dependencias completas durables; cero pérdidas en restart controlado, cero borrado pending, idempotencia/costo y privacidad demostrados, capacidad/aprobaciones/restore verificados. Un archivo nunca adquirido es fallo visible/conciliable, no PASS de continuidad. Plazo máximo y batching deben probarse con evidencia; tests mock no certifican red real.

## 13. Estimación y decisiones pendientes

Estimación revisada: core 6–9 días técnicos; medios/grants/revocación/recibos/escrow otros 6–9; espejo/restore 2–3; integración autorizada 1–2. Total orientativo 15–23 días, sujeto a contratos/capacidad y sin compromiso calendario. HA completa excluida; no eliminar consentimiento o ACK seguro para reducir esfuerzo.

Para aprobación: política y evidencia de consentimiento individual, revocación independiente; spool 4 GiB/recursos; tombstones/copies y limpieza lógica; RPO de espejo propuesto o persistencia remota pre-ACK; límites/costos y escrow; viabilidad de latencia/download/batches. Decisiones base de 10 GiB/72 horas/pendientes ya aprobadas se conservan.

**Revisión documental/estática PASS; pruebas planificadas NOT RUN; suites SKIPPED, sin cambio funcional. S16 BLOCKED / Pilot A NO-GO.** No captura de medios, servicios, datos reales, EasyPanel, proveedores, push o deploy. Detener para revisión antes de construir.
