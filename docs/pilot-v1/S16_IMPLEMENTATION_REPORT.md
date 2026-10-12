# S16 — Evaluación online, decisión pendiente

2026-10-12. [Comparación A/B/C fundamentada en código](S16_ONLINE_BACKUP_EVALUATION.md). Recomendada B con publicación atómica/inmutabilidad, fence contra GC y manifest de referencias del mismo snapshot SQL. No requiere receiver nuevo ni pausar webhook, pero hoy hay uploads referenciados antes de completarse/unlink concurrente; Runner offline no admite esta estrategia sin cambios aprobados. No retirar guardas sin invariantes probadas. Diseño de receiver/medios continúa no implementado, sin autorización nueva. Revisión PASS, suites SKIPPED, collector online/restore/ensayo NOT RUN. S16 BLOCKED / Pilot A NO-GO. Sin código/Runner/EasyPanel/servicios/proveedores/push/deploy modificados. Histórico conservado debajo.

---

# S16 — Diseño de continuidad de medios, ejecución pendiente

2026-10-12. [Contrato, pruebas e incrementos](S16_MEDIA_CONTINUITY_DESIGN.md). ACK estricto exige evento y medios completos cifrados/validados/vinculados durables y consentimiento; no200 para dependencia pendiente. Descarga temprana/replay privado/recibos procesamiento/limpieza opt-in diseñados, NO implementados. Latencia de8MiB/batches vs deadlineKapso y grants/revocación, costoescrow/recursos y RPO espejoexterno pendientes. Revisión documental PASS; pruebas NOT RUN, suites SKIPPED (sin código). S16 BLOCKED / Pilot A NO-GO. No servicios/EasyPanel/Kapso/OpenAI/mediosreales/push/deploy. Estado vigente; histórico conservado.

---

# S16 — Diseño receptor durable pendiente de revisión

2026-10-12. [Diseño y doce entregables](S16_DURABLE_RECEIVER_DESIGN.md). Estrategia B aprobada; implementación NO autorizada. SQLite con payload AES-GCM y volumen propio cifrado propuesto; confirmación durable antes de ACK, replay privado al inbox existente, pausa/recibos y retención72h desde incorporación. Medios reference_only no garantizan recuperación24h; spool bloqueado hasta política explícita. Durabilidad ante pérdidaVPS/RPO, capacidad/backupcola y privacidad pendientes. Diseño/revisión estática PASS; suites SKIPPED, implementación/operación NOT RUN. S16 BLOCKED / Pilot A NO-GO. Sin código funcional/servicios/proveedores/EasyPanel/push/deploy. Histórico debajo.

---

# S16 — Decisión de continuidad WhatsApp pendiente

2026-10-12. [Comparación A/B y recomendación](S16_WHATSAPP_CONTINUITY_DECISION.md). A no garantiza recuperar entradas durante la pausa; solo ensayo previo sin atletas bajo aceptación expresa. B propuesta como mínimo para continuidad con WhatsApp obligatorio, no implementada: decidir durabilidad/RPO, retención/claves y medios, y autorizar desarrollo local. Consulta de entregas fallidas documentada; reenvío manual API/dashboard no confirmado. Revisión documental PASS, suites SKIPPED, mantenimiento no autorizado. S16 BLOCKED / Pilot A NO-GO. Sin cambios funcionales/infraestructura/envíos/push/deploy. Histórico conservado debajo.

---

# S16 — Primera ventana preparada, ejecución pendiente

2026-10-12. [Procedimiento y autorizaciones](S16_FIRST_CONTROLLED_WINDOW.md). Revisión documental/estática PASS; S16 BLOCKED / Pilot A NO-GO. Kapso default agota tres intentos en ~50s: no garantiza recuperación tras mantenimiento prolongado. Drain del worker no implementado; requiere demostración o decisión adicional antes de detenerlo. Inventario real, recuperación de entradas, máximo propuesto 20min y pruebas representativas pendientes. No servicios detenidos, backups reales, envíos, automatización, despliegue ni push. Suites SKIPPED por documentación únicamente. Estado vigente; histórico conservado debajo.

---

# S16 — Preparación integración EasyPanel

2026-10-12. Base 3ce40466b21c99894715e6f9dc01f0ca6dd1eed0. Preparación documental PASS; S16 operativo BLOCKED / Pilot A NO-GO. [Procedimiento completo](S16_EASYPANEL_INTEGRATION_PLAN.md).

- [ ] Inventario real/versiones/roles/montajes/secretos/recursos confirmados por Gastón.
- [ ] Ventana de todos los escritores y drenaje demostrados; webhook no permanece activo en diseño actual. Retención/replay Kapso sin pérdidas pendiente de verificar.
- [ ] Reanudación sin upgrade implícito; no existe handshake capture-complete, esperar resultado final y proceso terminado.
- [ ] Backup representativo, restore aislado, alerta integrada y coordinador externo diario autorizados y probados.

Revisión estática PASS; suites SKIPPED por documentos únicamente, pruebas del runner ya PASS no repetidas. Sin infraestructura/datos reales/envíos/push/deploy/scheduler. Workflow existente conservado; S15 parcial y ausencia de gates automáticos aceptada temporalmente. Custodia KeePassXC y prueba Telegram anteriores conservan su evidencia; no sustituyen ensayo representativo. Esta cabecera es el estado vigente; se conserva histórico debajo. Commit documental: git log -1 -- docs/pilot-v1/S16_EASYPANEL_INTEGRATION_PLAN.md.

---

# S16 — Backup Runner implementado y validado localmente

Fecha: 2026-10-12, America/Santiago. Base 49e366203bcc9ce5e7bc0079ed4216eb3b4b84b3; rama codex/pilot-v1-stabilization. **Implementación local PASS; S16 operativo BLOCKED / Pilot A NO-GO.** No instalación/activación EasyPanel, datos reales, R2/Telegram reales, OpenAI/Kapso, push/merge/deploy ni cambios al workflow. Original sin escrituras del agente.

## Diseño y archivos

- backup-runner/Dockerfile, requirements.txt, compose.example.yml, environment.example, maintenance.example.json y README.md: imagen independiente, cliente PostgreSQL 17.6, crypto/psycopg existentes fijados, usuario 10001, sin puertos/Docker socket/credenciales EasyPanel ni VOLUME PGDATA heredado. Runner + watchdog separados, mounts/env mínimo y todos los flags false. Base/dep fijados; paquetes Debian se resolvieron durante build, por lo que digest construido es evidencia, no garantía de rebuild byte-a-byte futuro.
- scripts/pilot_backup_runner.py: pg_dump completo con snapshot readonly, captura filesystem, permisos/gates/espacio, AES streaming, R2 PUT/GET sin retries ni redirects, recibos atómicos y OS lock; schedule/pre-release, watchdog y plan de retención no destructivo.
- scripts/pilot_backup_bundle.py: FXS16GCM2 para streaming mayor de 128 MiB; key_id/metadata autenticados en AAD, manifiesto/hashes cifrados. No cambia la clave existente ni formato de objetos anteriores. Directorios/archivo seguros, sin links, traversal, dispositivos o sobrescritura de targets.
- scripts/pilot_backup_restore.py: descifrado/auth/hash antes de uso, v1/v2, restore solo opt-in a DB vacía movement_restore_* y storage nuevo; sin --clean/--create, migraciones/seed ni producción. Roles/clave/config se recuperan fuera del archivo por custodias independientes.
- tests scripts/test_pilot_backup_runner.py y scripts/test_pilot_backup_runner_integration.py. Reutiliza ops legacy y Telegram/ledger, no reescribe producto ni añade servicios facturables.

## Consistencia y límites de responsabilidad

La coherencia DB/files requiere **pausa real externa de TODOS los escritores**, drenaje y cierre de conexiones por Gastón o controlador autorizado, y ventana fresca <=30 min. El runner sin admin/socket no puede parar servicios ni probar una declaración de pausa falsa. El marker controlado RO no sustituye esa comprobación. Si falta/venció/no corresponde a source_commit/source_path, aborta. Snapshot PostgreSQL exportado readonly a pg_dump y hash/inventario antes-copia-después protegen la captura bajo esa precondición; cualquier drift/cliente detectado falla, no se sube un set declarado coherente.

Esto permite programación **condicional a una ventana segura**, no backup diario desatendido completo sin integración externa de pausa. No ampliar roles ni capturar storage vivo para evitar un rechazo. Config/instalación, pausa automatizada externa y recepción del job real siguen pendientes. Imagen source volume RO y DB role solo SELECT; no PGDATA. API/worker/job de video y otros escritores deben estar incluidos, no basta pausar WhatsApp.

Staging privado tmpfs o disco cifrado aprobado, inicialmente ~5x set; check de espacio antes de crear archivos grandes. Default máximo 512 MiB configurable <=4 GiB, streaming probado >128 MiB, manifest hasta 8 MiB y 100k files. Compose propone recursos, no presupuesto/capacidad del VPS aprobado. Datos privados no se registran; solo ciphertext va a R2, claves/versiones del producto custodiadas separadamente. Scratch propio se limpia en ejecución normal; SIGKILL puede dejar tmpfs propio hasta reinicio/revisión, no borrar medios ni conjuntos existentes automáticamente.

## Pruebas ejecutadas y resultados

| Validación | Estado / alcance |
|---|---|
| Unit runner | **33 PASS, 0 FAIL/SKIPPED** en Linux sin red: completo/pre-release, falta de secretos, PostgreSQL simulado, cifrado/clave errónea, R2 timeout/corrupción y HTTP SigV4 streaming simulado, Telegram fallido, concurrencia, SIGKILL/liberación lock, retención sin borrado, scheduler catch-up/slot, staging y watchdog/crash/active-job. |
| Regresiones reutilizadas | **28 legacy +31 Telegram +16 Resend PASS**, cero FAIL/SKIPPED; 75 pruebas distintas, no sumar ejecuciones repetidas. Transporte siempre fake. |
| Streaming | PASS: 129 MiB cifrado/descifrado por chunks e igualdad SHA; supera límite v1 sin cambiar el módulo v1. |
| Integración nueva imagen | PASS: pg_dump y pg_restore REALES solo PostgreSQL 17.6 tmpfs/red interna nueva, DB vacía v2 y otra v1. 29 tablas, 3 usuarios sintéticos, sesión/nota/foto/análisis/review; hashes y referencias. |
| Medios | PASS de integridad: archivos restaurados iguales a cuatro fuentes sintéticas; PNG verificada y MP4 original/annotated decodificables con FFprobe. Son medios artificiales, no certificación biomecánica. |
| Controles efectivos | PASS rol source sin DML, rechazo de cliente DB extra y cambios filesystem durante pg_dump; guardas restore/new target. Mutación de JSON exclusivamente sobre fixture nueva para probar drift; medios originales del producto no leídos/tocados. |
| Build/config | PASS imagen local no privilegiada sin VOLUME/puertos heredados, código imagen coincide por SHA-256 con seis módulos; Compose config --quiet válido usando env/files/nombres sintéticos, no up. |
| Interrupción | PASS proceso de ensayo terminado libera OS lock, nuevo job entra y recibos incompletos permanecen detectables. No reenvío de objeto previo incierto ni purga. Watchdog no alarma por incomplete mientras lock activo dentro del umbral; al liberar/crash sí detecta. |
| R2/Telegram reales y producción | NOT RUN/BLOCKED por alcance; pruebas anteriores de canal/recuperación sintética se conservan pero no certifican este runner con datos reales. |
| Suites app Python/JS completas | NOT RUN en este incremento: sin cambios app/modelos/migraciones/contratos web. Tests específicos runner y regresiones son verificación de esta etapa; antes de push rige ejecutar obligatorios del SHA candidato y aprobación manual. |

Fallos durante desarrollo corregidos: nombre de usuario Debian backup ya existente, transferencia/ACL de fixture y transacción explícita ajustadas, incompatibilidad filter=data en Python Debian solucionada con extracción manual validada, fixture HTTP requería config normalizada, watchdog distinguía job en curso de incomplete. No degradación de guardas. Intentos previos registrados FAIL; resultados finales sustituyen esos intentos sin declararlos aprobados.

Evidencia final detallada en S16_BACKUP_RUNNER_VALIDATION.json: image ID/digest, fuentes/hashes, entornos nuevos detenidos y logs de suites. No contiene clave/token/chat IDs ni datos privados; hashes son de código/ciphertext, nunca secretos. Contenedores anteriores ajenos no se detuvieron, ni imágenes/volúmenes/R2 existentes se borraron. Código funcional app y .github/workflows/deploy.yml permanecen iguales; untracked QA/artefactos no se agregan.

## Operación, alertas y recuperación

Runner y watchdog requieren estado persistente protegido compartido; UUID por set y OS file lock evitan concurrentes, marker diario antes de ejecución impide duplicados tras reinicio. Incidente health mantiene request ID hasta resolución para no convertir UNKNOWN/UNCERTAIN en nuevo intento automático. Rate limit/429 bloquea y registra fallo de notificación; sender nunca propaga fallo al backup. ACCEPTED es ACK de API, no lectura humana. Watchdog independiente no depende de que job llegue a reportar error; si watchdog muere, monitoreo de plataforma/operador debe detectarlo, no se afirma autocuración.

R2 restricted bucket y solo HTTPS, sin DELETE/retry. Fallo durante upload puede dejar objeto incierto: preservar recibo, verificar SHA/presencia antes de recuperación autorizada, no sobrescribir/purgar. Retención solo planifica siete daily COMPLETE y pre-release durante piloto; incompletos requieren revisión manual, no expiración automática. Preservar versiones AES y WhatsApp/sharing por KeePassXC/copia externa sin guardarlas en Git ni junto al ciphertext.

Restaurar a instancia nueva aislada, profile reader y clave por key_id recuperada; v2 metadata autenticada, v1 usa asociación externa SHA/key_id. DB/storage nuevos, proveedores apagados; reponer app con mount/ruta lógica original de medios sin reescribir DB. Si target queda parcial tras error, no repetir sobre él ni limpiar automáticamente: pedir destino nuevo/decisión.

## Instalación manual y pendientes para cierre

Instrucciones completas y lista exacta de secretos en backup-runner/README.md. Gastón debe confirmar inventario DB/media/mounts, rol readonly/select completo, reader R2 separado, UID/ACL, capacidad/staging protegido, secret-file raw/version productiva y perfiles libpq, estado privado, ventanas y control externo de pausa. Ningún servicio requiere socket ni credenciales administrativas. Watchdog solo Telegram/estado, sin AES/DB/R2/media.

Solicitar autorización específica antes de: subir código/cualquier deploy, crear/montar servicios/volúmenes en EasyPanel, aplicar secrets, pausar escritores o tomar backup real, restore de ese set representativo aislado, envío de alerta integrada y activar daily/watchdog/pre-release. Mantener flags false. Prueba representativa con recuperación desde KeePassXC y alerta real del job, y funcionamiento programado observados, son requisito para S16 operativo PASS. Además resto de Pilot A sigue NO-GO (paridad/canales/video/costos/coaches/otros gates). S15/workflow sin modificar, riesgo CI/control manual aprobado conservado.

Commit final: git log -1 -- scripts/pilot_backup_runner.py. Detenerse para revisión; no habilitar piloto ni nueva fase.

---

## Historial — los contratos propuestos anteriores del runner ahora están implementados localmente

# S16 — preparación operativa final 2026-10-12

Base 3f8a408da61c005ed4dc06cb1f480b76abccc9c8. Lista de variables exactas, aplicación privada por Gastón, mapa Compose vs inventario EasyPanel pendiente, backup/restore representativo, activación y permisos: [S16_FINAL_OPERATIONS_GUIDE.md](S16_FINAL_OPERATIONS_GUIDE.md).

**S16 BLOCKED / Pilot A NO-GO.** Telegram manual y recuperación KeePassXC sintética PASS conservados sin repetición. Restan secreto runtime/versiones productivas + adaptador/colector/capacidad, backup/restore representativo y automatización/alertas integradas autorizadas. Variables R2 de los ensayos no están conectadas automáticamente a app/Compose; AES no consume env actual, BACKUP_AES_KEY_FILE/ID son contrato propuesto aún sin implementación. Flags/gates permanecen deshabilitados.

No pruebas sintéticas repetidas, código funcional/CI cambiado, EasyPanel configurado, backup de producción, Telegram, OpenAI/Kapso, push/merge/deploy ni escrituras al workspace original. Validación documental de referencias/código y ausencia de diferencias fuera de docs; no afirmar pruebas pendientes PASS. Commit: git log -1 -- docs/pilot-v1/S16_FINAL_OPERATIONS_GUIDE.md.

---

## Evidencia histórica — prevalece este estado operativo

# S16 — recuperación independiente KeePassXC PASS (sintético)

Fecha: 2026-10-12, America/Santiago. Base b25d1f31cf83bb903dd9585a7b0c2d6bbd02f438. Usuario confirmó importación binaria en KeePassXC, verificación de copia cifrada y exportó un archivo para el ensayo. **PASS: copia recuperada descifra y restaura el conjunto sintético autorizado. S16 global sigue BLOCKED / Pilot A NO-GO.**

## Evidencia ejecutada

- Exclusivamente la clave raw recuperada de 32 bytes indicada por el usuario; no se abrió la clave original, no se generó/reemplazó clave de backup ni se registró contenido/hash del secreto. Procedencia KeePassXC/copia cifrada confirmada por usuario; el agente no abrió la bóveda ni recibió contraseña/keyfile de desbloqueo.
- GET HTTPS único del objeto sintético `synthetic-validation/eb25e70ccc31/backup.tar.aes256gcm`: 92.197 bytes, SHA-256 esperado y real iguales. Sin PUT, DELETE, enumeración ni datos productivos. Credenciales R2 tomadas de configuración local privada autorizada, sin imprimir valores; reader exclusivo de producción sigue pendiente.
- AES-256-GCM / formato FXS16GCM1 y AAD existente: tag autenticado e integridad del manifiesto DB/storage PASS. key_id externo `pilot-s16-synthetic-eb25e70ccc31-k1` queda asociado a ese conjunto, sin modificar ciphertext histórico.
- pg_restore con --exit-on-error en base NUEVA `movement_s16_recovered`, PostgreSQL 17.6 tmpfs, red nueva interna 10.253.10.0/28, sin puertos Docker publicados ni redes con usuarios. Head restaurado 0024_training_save_requests, sin migración del target después de restore. Esquema de 29 tablas; 3 usuarios, 1 entrenamiento con nota, 1 foto, 1 análisis y 1 review.
- Cuatro archivos restaurados en directorio NUEVO tmpfs: hashes y referencias DB/storage iguales; PNG verificada por PIL. Los videos del conjunto histórico son placeholders sintéticos: no declarar reproducción/biomecánica PASS.
- Independencia del servidor: no acceso/conexión a EasyPanel, ninguna credencial exclusiva del VPS utilizada; clave exportada Windows y configuración R2 local bastaron. No se simuló caída destruyendo o reiniciando el servidor. Esto valida recuperación del conjunto de ensayo, no disponibilidad del secret runtime de producción.
- 2,42 segundos dentro del ensayo (GET/descifrado/restore/verificación); excluye intervención humana, apertura de bóveda y creación del entorno. No RTO/RPO de producción. Contenedores propios detenidos tras validación; no contenedores/volúmenes/imágenes existentes eliminados ni claves/export/objetos R2 borrados.

Evidencia redactada: S16_KEY_RECOVERY_EVIDENCE.json y S16_KEY_RECOVERY_PLAN.json; originales locales `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-ys4hmzql/` (environment.json, key-recovery-results.json). Se registran hashes del harness/script y del ciphertext, nunca de la clave. No suites completas repetidas por esta entrega documental; la prueba de recuperación real solicitada sí se ejecutó, no es mock.

## Riesgos y pendientes

PASS de custodia/recuperación **para esta versión sintética**; flags de producción independientes permanecen false: aún falta secreto runtime seguro y versiones de claves WhatsApp/sharing recuperables, reader separado, inventario de tamaño/capacidad y conjunto representativo EasyPanel, automatización/monitorización autorizada. Prueba manual Telegram recibida sigue PASS; no se envió ninguna alerta adicional. Riesgo CI aceptado/control manual vigente, sin YAML/push/deploy.

El archivo exportado es una copia en claro: Gastón debe mantener ACL privada y decidir su tratamiento después del ensayo; agente no lo modifica ni elimina. Conservar clave k1 y bóveda/copia mientras permanezca cualquier respaldo que la requiera. La copia externa y factores de desbloqueo deben continuar separados del VPS; pérdida del computador/custodia sin segunda copia sigue siendo riesgo operacional. No reutilizar una clave de ensayo como secreto productivo sin decisión explícita.

Rotación: solicitar autorización de nueva clave y key_id distinto; nunca sobrescribir k1, conservar referencias de manifiestos/objetos y versiones antiguas hasta retiro autorizado de todos sus respaldos; ensayar cada versión con adjunto recuperado. No se ejecutó rotación. Para pérdida del VPS: recuperar bóveda/copia externa y versión por key_id, usar reader privado, verificar ciphertext/tag/hashes y restaurar a instancia nueva aislada; aprobación separada antes de cutover o copia de datos reales.

Entregables S16_IMPLEMENTATION_REPORT.md y BACKUP_RESTORE_RUNBOOK.md actualizados; metadatos de configuración/evidencia sin secretos. Detenerse para revisión. Commit de etapa: git log -1 -- docs/pilot-v1/S16_KEY_RECOVERY_EVIDENCE.json.

---

## Evidencia histórica — el bloqueo de recuperación sintética está superado

# S16 — recuperación de clave KeePassXC: preparación y punto de intervención

Fecha: 2026-10-12, America/Santiago. Base a5f61dfc8730d67afb3071be5a4545aa5443d3d0 confirmada. **Formato/mapeo preparado PASS; recuperación real desde KeePassXC BLOCKED; S16 BLOCKED / Pilot A NO-GO.** La prueba Telegram recibida mantiene PASS. No nueva generación/reemplazo/lectura de clave, red, respaldo real, restore, eliminación, EasyPanel, push ni deploy en esta etapa.

## Clave y versión existentes

Clave del conjunto sintético exitoso: archivo binario raw de **32 bytes (256 bits)**, no password, hexadecimal, Base64 ni keyfile de desbloqueo de KeePassXC. Existencia/tamaño comprobados mediante stat, sin abrir contenido. Ubicación actual:

`C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-90w55bof/recovery-key-private/aes256.key`

El conjunto autorizado es `synthetic-validation/eb25e70ccc31/backup.tar.aes256gcm`, 92.197 bytes, SHA-256 de ciphertext `028beb7fba7412ec1e8c27c5e1a71023f772f411ed3e3090475fe231821c863f`. Este checksum corresponde al objeto cifrado, **no a la clave**. Existe otro ensayo con otra clave: no mezclar ni sustituir versiones.

Código vigente: MAGIC FXS16GCM1 (9 bytes) + nonce 12 bytes + ciphertext con tag GCM 16 bytes; AAD exacta `fluxio-s16-synthetic-v1`. Cambiar AAD o interpretar clave como texto impediría descifrado. Biblioteca AESGCM exige la clave raw de 32 bytes para este esquema. No identificar automáticamente la versión por un hash del secreto ni imprimir material criptográfico.

Identificador no secreto asignado a la clave existente: **pilot-s16-synthetic-eb25e70ccc31-k1**. Mapeo versionado en S16_KEY_RECOVERY_PLAN.json. El ciphertext histórico y manifiesto interno no incluyen key_id; esta referencia externa evita modificar/re-subir el objeto. Para nuevos manifiestos se propone cipher/key_id/key_encoding/key_length_bytes/format_version y referencia del objeto/sha256, siempre sin key bytes. Inserción automática de key_id en producción aún pendiente; no se cambió formato ni colección activa para afirmarla implementada.

## Intervención manual requerida ahora — detenerse antes de ella

1. Gastón abre su KeePassXC/KDBX privado en Windows. No se encontró ejecutable en las dos rutas estándar Program Files consultadas; esto no descarta instalación portable. Indicar si ya dispone de KeePassXC; el agente no lo instala ni abre credenciales.
2. Crear una entrada titulada `Fluxio / Backup AES / pilot-s16-synthetic-eb25e70ccc31-k1`. En adjuntos de la entrada añadir el archivo existente aes256.key desde la ruta anterior. **Adjuntar el binario**, sin copiar contenido al password de la entrada, terminal, clipboard, chat o informe; no usar generador de contraseñas para sustituirlo. Registrar solo versión, algoritmo y backup-set asociado.
3. Guardar KDBX cifrada bajo la custodia ya elegida y conservar una copia protegida en el dispositivo externo cifrado, con factores de desbloqueo recuperables por separado. No exportar la bóveda en texto/CSV ni guardar todo únicamente en VPS o repo.
4. Para la prueba independiente, abrir la copia externa de KDBX desde entorno controlado que no dependa de EasyPanel; recuperar **el adjunto** de esa versión hacia una carpeta nueva privada fuera de repositorios, con ACL solo del usuario Windows. No sobrescribir el archivo original ni exportar a la misma ruta Temp del ensayo. El export transitorio sigue siendo una clave en claro aunque la bóveda esté cifrada: proteger acceso y acordar su tratamiento posterior; no borrarlo implícitamente.
5. Entregar al agente **solo la ruta absoluta del adjunto recuperado** y confirmar que proviene de la copia KeePassXC, preferentemente la copia externa. No enviar el adjunto ni la clave por chat. No dar contraseña maestra/keyfile de desbloqueo. Sin esto no puede afirmarse recuperación desde la custodia.

## Ensayo autorizado que se ejecutará después de esa intervención

- Usar exclusivamente la clave exportada, sin leer la clave original ni secretos de EasyPanel; bloquear proveedores IA/chat y no contactar el VPS. Credenciales R2 de lectura independientes y vigentes por referencia privada: actualmente usuario señaló .env.example local para configuración, nunca se imprime ni incorpora a Git. Reader dedicado aún pendiente para operación definitiva; writer con GET no demuestra separación de roles.
- Descargar solo el objeto sintético señalado por HTTPS, comprobar tamaño/SHA-256 antes de descifrar. No listar/copiar contenido productivo ni alterar/borrar R2. Recuperar con clave por key_id y AAD/format existentes; GCM tag + hashes internos prueban integridad y correspondencia, sin comparar/imprimir el secreto original.
- Restaurar pg_dump completo y storage en PostgreSQL/paths **nuevos y desechables**, red nueva interna sin puertos publicados ni redes con usuarios, usando imágenes locales existentes. No restaurar sobre producción ni ejecutar upgrade después del restore. Fuente backup 0024_training_save_requests, datos esperados 3 usuarios, 1 sesión/foto/análisis/review y cuatro archivos.
- Comprobar schema/referencias/hash y fotografía. Este conjunto histórico contiene videos placeholder, no clips reproducibles: documentar ese límite, no certificar video por esta prueba de claves. Ya existe otra prueba local con MP4 válidos, no confundir conjuntos.
- Registrar PASS/FAIL/BLOCKED, tiempos, evidencia y custodia efectivamente utilizada. Parar contenedores propios; conservar objeto R2. No simular caída destruyendo/reiniciando EasyPanel: ausencia de conexión/acceso al servidor demuestra independencia del ensayo, sin probar disponibilidad automática del secret runtime aún no definido.

La autorización del usuario cubre restore de este respaldo **sintético**; no requerir nueva aprobación genérica para esa misma acción después de obtener la copia recuperada. Si destino, conjunto o datos cambian, preparar acción y solicitar autorización específica.

## Pérdida del servidor y rotación sin perder respaldos

Ante pérdida del VPS: recuperar KDBX/copia externa y factores independientes; localizar key_id por manifiesto/registro; obtener esa versión de adjunto y credenciales reader desde custodia independiente; reconstruir solo a destino nuevo aislado y comprobar integridad antes de solicitar cutover. No depender del único password/keyfile o clave AES almacenado en el servidor. Aún falta prueba de recuperación externa y diseño de entrega segura al runtime; esta preparación no los marca PASS.

Rotación futura requiere autorización explícita para nueva clave. Nunca sobrescribir k1 ni modificar claves existentes: asignar k2 a una nueva clave autorizada, custodiar ambas, respaldar nuevos conjuntos con key_id correcto, restaurar una generación de cada versión y comprobar selección. Conservar claves anteriores mientras exista un backup que dependa de ellas; versiones de WhatsApp/sharing también deben mantenerse por separado. No re-cifrar ni borrar backups viejos para rotar sin autorización. No ejecutar generación, reemplazo, invalidación o subida nueva ahora.

## Evidencia y pendientes

PASS: rama/commit base, formato fuente, mapeo de objeto y metadatos, archivo fuente existente de 32 bytes, ausencia de lectura de clave y generación. BLOCKED: importación/recuperación real KeePassXC y copia externa, descifrado/restore usando esa copia, reader separado, runtime secret mechanism, automatización y restore representativo EasyPanel. Tests sintéticos existentes no se repiten ni certifican esta recuperación. Entregables documentales y JSON válidos; no código funcional cambiado. Detenerse para pasos manuales de Gastón.

---

## Evidencia histórica conservada

# S16 — prueba real Telegram recibida

Fecha: 2026-10-11, America/Santiago. **PASS del canal en una prueba manual:** un sendMessage autorizado aceptado HTTP 200 y recepción confirmada expresamente por el responsable. Evidencia redactada en S16_TELEGRAM_REAL_TEST_EVIDENCE.json, sin token, Chat ID, teléfono ni contenido privado. Ningún segundo envío ni retry. Esta confirmación no autoriza mensajes futuros.

**S16 sigue BLOCKED; Pilot A NO-GO.** Pendientes: recuperación real KeePassXC y copia externa, secreto runtime, backup/restore representativo EasyPanel, collector coherente/capacidad y activación autorizada de alertas/health watchdog. No se probaron aún alertas automáticas de backup/restore/worker ni fallos reales del monitor; no confundir recepción de prueba con operación continua validada. Scheduler y configuración de envíos permanecen deshabilitados; no push/deploy/CI ni escrituras al workspace original. Solo evidencia local y documentación actualizadas.

---

## Histórico — reemplazado únicamente el pendiente de recepción del mensaje manual

# S16 — Telegram reemplaza Resend

2026-10-11. Adaptador saliente Telegram preparado con reutilización de recibos/validación, timeout, rate limit persistente y callback seguro para backup. **31 tests simulados PASS + 16 regresiones PASS**. Sin Telegram real ni webhooks. Resend desactivado como canal; intento previo Resend HTTP 403 conservado como histórico, no repetir.

Config/instrucciones Chat ID y mensaje de prueba en [S16_TELEGRAM_ALERTS.md](S16_TELEGRAM_ALERTS.md). TELEGRAM_BOT_TOKEN/CHAT_ID privados; TELEGRAM_ALERTS_ENABLED=false. No stdout de tokens, direcciones de API o datos de chats. Monitores y scheduler no instalados; permisos y recuperación real pendientes.

**S16 BLOCKED / Pilot A NO-GO:** recepción real Telegram no autorizada/ejecutada, KeePassXC y backup representativo EasyPanel aún pendientes. No modificar CI, push, deploy, EasyPanel o workspace original. Riesgo de gates CI aceptado temporalmente, S15 pendiente; aprobación manual antes del push conserva pruebas del SHA definitivo.

---

## Histórico — prevalece Telegram como canal actual

# S16 — adaptador Resend preparado, validación offline

Fecha: 2026-10-11. Política de release vigente: control manual de tests/resultados/SHA y aprobación explícita antes de push; riesgo de ausencia de gates CI aceptado temporalmente, S15 no completada. Workflow sin cambios.

Implementación acotada: scripts/pilot_resend_alerts.py, scripts/test_pilot_resend_alerts.py y plantilla de correo. No modifica app ni autenticación, backup collector, CI, infraestructura o claves. El módulo no envía al importar ni tiene CLI de envío. Requiere autorización explícita en llamada, BACKUP_ALERTS_ENABLED=true, BACKUP_ALERT_DOMAIN_VERIFIED=true, RESEND_API_KEY y FROM/TO privados. Ningún envío real autorizado/ejecutado.

Validación offline: **16 PASS, 0 FAIL/SKIPPED**, transportes falsos siempre. Casos: autorización/flags/config, dominio, aceptación distinta de recepción, duplicados, payload distinto con misma ID, timeout/5xx/429 sin retry, crash incierto, contenido/headers rechazados, privacidad de recibos y redirects bloqueados. Estados ACCEPTED/REJECTED/UNCERTAIN; receipt_confirmed siempre false hasta evidencia real separada del operador. Intento durable previo al proveedor, ID y payload estables; replay no vuelve a enviar aun con resultado ambiguo. No redirecciones de Authorization a otros destinos. Excepciones/respuestas privadas no se imprimen ni persisten; recibos sin direcciones ni API key. Estado local debe protegerse y persistir entre reinicios; no borrar ledger para recuperar un envío sin decisión individual.

El adaptador standalone todavía no está conectado al job de servidor; debe completar callback de entrega y política de deduplicación/recordatorios antes de activar. No convierte ACK API en correo recibido. No se habilitó scheduler, Resend o DNS. Antes de un eventual push se deben ejecutar las pruebas obligatorias sobre el SHA definitivo y presentar resultados/omisiones para aprobación; estos tests dirigidos no sustituyen ese gate manual.

**S16 BLOCKED / Pilot A NO-GO:** pendiente configuración privada Resend (remitente/destinatario/dominio/API key) y autorización individual para correo real, recuperación desde KeePassXC/dispositivo externo y secreto runtime, evidencia EasyPanel por Gastón, collector/capacidad y backup/restore representativo autorizado. No pedir SSH a Codex ni modificar S15. No se repiten ensayos sintéticos previos.

Commit: consultar git log -1 -- scripts/pilot_resend_alerts.py. Detenerse para revisión del incremento antes de continuar o subir código.

---

## Histórico

# Actualización de responsabilidades — 2026-10-11

Gastón administra EasyPanel; Codex no necesita acceso SSH ni sesión del panel. GitHub es origen de la versión publicada y GitHub Actions dispara deploy **solo bajo autorización expresa**. Codex prepara código/pruebas/manifiesto y sube exclusivamente refs aprobadas. Gastón aplica variables, obtiene inventario y evidencia redactada API/worker/DB/volúmenes/proxy, realiza backups/restore/rollback autorizados y confirma SHA/digests. Falta de acceso directo de Codex no es bloqueo; falta de evidencia verificable sí.

Workflow existente push main llama al webhook sin checks/gates: S15 permanece pendiente, YAML sin cambios. No push a main, merge, POST ni deploy. S16 sigue BLOCKED por pruebas operativas reales pendientes; continuar localmente con KeePassXC/Resend. Plan vigente: PILOT_A_RELEASE_PLAN.md y DEPLOYMENT_RUNBOOK.md; no solicitar nuevamente SSH para esta etapa.

---

## Historial anterior — instrucciones de acceso directo sustituidas

# S16 — decisiones confirmadas y acceso EasyPanel pendiente

Fecha: 2026-10-11. Base 7598e38. Custodia elegida KeePassXC Windows + copia externa cifrada; runtime secrets pendiente. Resend preferido, destinatario/remitente/dominio/API key privados pendientes. Ninguna clave generada/reemplazada y ningún correo enviado.

**S16 BLOCKED / Pilot A NO-GO.** Lectura EasyPanel autorizada, pero no sesión administrativa/SSH ni URL de panel disponibles. Host documentado responde GET /health 200 con TLS validado; no informa versión ni certifica DB/worker/volúmenes. Inspección parcial en [S16_EASYPANEL_INSPECTION.md](S16_EASYPANEL_INSPECTION.md).

No existe envío API/SMTP actual: solo callback notify_operator y plantilla. Config Resend API propuesta, no implementada/activa. Procedimientos, prueba de un correo, recuperación KeePassXC y backup/restore representativo con autorizaciones separadas en [S16_CUSTODY_RESEND_VALIDATION_PLAN.md](S16_CUSTODY_RESEND_VALIDATION_PLAN.md). Diario no listo para activar por falta de adaptador, claves runtime, capacidad y alertas reales.

Verificaciones de esta etapa: Git/base, búsqueda de mecanismos, presencia de variables sin valores, inventario de sesión disponible, dos lecturas públicas (HEAD / 405 y GET /health 200), consulta de documentación oficial Resend/KeePassXC y validación JSON/gates. No repetir suites sintéticas previas ni registrar como PASS custodia/envíos/restore real no ejecutados. Nuevos deliverables documentales y plantillas inertes solamente. Original leído, sin escrituras; sin nuevos objetos R2, OpenAI/Kapso, cron, migraciones, deploy ni infraestructura modificada.

Próximo paso requiere URL/sesión del panel, referencias KDBX/dispositivo y configuración privada Resend. Leer el reporte antes de autorizar cualquier operación externa de escritura.

---

## Evidencia histórica

# S16 — verificación del token actualizado y decisiones operativas pendientes

Fecha: 2026-10-11, America/Santiago. Base `3fa022956e6e5fc2315aa67e24499c7ff4ae4086`. **S16 BLOCKED operativamente; Pilot A NO-GO.** No repetición de ensayos sintéticos, nuevas cargas R2, instalación de jobs, correos, EasyPanel ni proveedores IA.

| Control | Estado vigente |
|---|---|
| Bucket privado, sin dominio ni r2.dev | PASS de confirmación del propietario en Cloudflare; no inspección independiente de la API/panel por el agente. |
| Writer Active, Object Read & Write, exclusivo al bucket | Confirmado por propietario: fluxio-movement-backup-writer. Nombre/policy no introspectados con credencial S3. |
| Token actualizado operativo | PASS técnico: HEAD bucket HTTP 200, ListObjectsV2 max-keys=0 HTTP 200; cero objetos consultados, cero escrituras. Evidencia S16_UPDATED_TOKEN_READ_EVIDENCE.json. |
| Identidad de restore y separación de medios | BLOCKED: lector separado no identificado; medios EasyPanel no inventariados. least_privilege_verified permanece false. |
| Claves | Ambas claves sintéticas anteriores siguen disponibles localmente en Temp/recovery-key-private/aes256.key; fuera de EasyPanel/R2/Git, sin imprimir contenido. No hay clave de producción configurada ni almacén independiente aprobado. |
| Alertas por correo | Preparado contrato/mensaje redactado BACKUP_EMAIL_CONFIGURATION.example.json. BLOCKED destinatario, remitente, proveedor SMTP TLS, credencial y autorización de un envío de prueba. Cero correos enviados; no adaptador SMTP implementado sin configuración elegida. |
| Diario / pre-release | Helper y cron preparados, probados previamente; NO listos para activar: adaptador path/hash, collector/quiescencia, transporte, clave, correo, estado y horario faltan. execution_enabled/scheduler_enabled siguen false. |
| Restore EasyPanel representativo | Preparado procedimiento y permisos requeridos, NOT RUN. Falta acceso read-only para inventario y autorización separada del backup real/pausa/restore. Ensayo previo no representa volumen/costos/RTO de destino. |

## Decisiones exactas y autorización por etapa

1. **Custodia:** confirmar una bóveda/gestor de secretos fuera del VPS y distinto del bucket, su referencia privada y acceso de recuperación de Gastón. Propuesta: bóveda cifrada con MFA y copia de recuperación offline protegida, suplente por designar. No usar Temp ni el único servidor como almacén permanente. Con elección aprobada, autorizar crear/custodiar una clave nueva de producción y recuperar una clave sintética desde esa bóveda en máquina aislada; no copiar claves por chat.
2. **Correo:** entregar dirección de Gastón, remitente autorizado, proveedor/host/puerto SMTP y modo TLS, ubicación privada de credenciales. Luego autorización concreta: “Autorizar un correo de prueba de alerta S16 al destinatario indicado desde el remitente indicado”. Antes del envío mostrar mensaje concreto sin datos personales del producto; confirmar recepción por Gastón, no solo aceptación SMTP. Solicitar separadamente activación de alertas automáticas y pauta de deduplicación/escalado.
3. **EasyPanel lectura:** indicar proyecto/servicios API, worker, PostgreSQL y storage, y acceso SSH/panel privado por referencia. Autorización requerida: “Autorizar inspección read-only de esos servicios para inventario S16, sin cambios ni copia de datos”. Inventariar versión, 29 tablas del candidato y posibles schemas adicionales, mounts privados, tamaño, escritores, roles, claves/versiones y capacidad. No imprimir conexiones ni contenido de usuarios.
4. **Backup real:** después del inventario presentar ventana exacta y servicios a pausar/reanudar, set/prefijo, tamaño/costo estimado, destino aislado y acceso/retención de la copia. Pedir autorización específica para esa pausa y dump completo + storage cifrado hacia R2. PostgreSQL lógico no modifica filas, pero la coordinación de servicios cambia infraestructura y exige aprobación. No ejecutarlo solo por aprobar inspección.
5. **Restore:** autorizar restaurar únicamente ese set identificado en instancia nueva aislada con proveedores apagados, acceso restringido, validación de imágenes/videos/usuarios/analyses/reviews y claves/permisos, tiempo extremo a extremo. Aprobar manejo posterior de la copia; nunca restore en producción ni eliminación implícita.
6. **Programación:** aprobar horario/zona, operador/suplente, directorio de estado protegido, adaptador fijado por hash, alerts watchdog y ventanas coherentes. Solo tras gates y restore aceptados solicitar autorización de instalar/activar diario y pre-release; no publicar aplicación. Mantener borrado manual de siete daily + pre-release hasta prueba/aprobación separada de cualquier automatización destructiva.

Las decisiones 1 y 2 se requieren ahora para continuar implementación del adaptador; no se inventan proveedor ni direcciones. Mantener evidencia previa 28 tests Linux y restore sintético, sin declararlos reejecutados. Ningún cambio funcional en esta etapa; JSON/docs solamente. Original solo leído; configuración con secretos sigue sin incorporarse al candidato.

Commit de esta etapa: git log -1 -- docs/pilot-v1/S16_UPDATED_TOKEN_READ_EVIDENCE.json. Detenerse para decisiones de custodia/correo/acceso; no cierre falso de S16 ni siguiente fase.

---

## Evidencia histórica

# S16 — preparación operativa y validación local vigente

Fecha: 2026-10-11, America/Santiago. Base `84ad8a992a6f78d36ba8844abf24777308202c24`, rama codex/pilot-v1-stabilization. **Preparación local PASS; cierre operativo S16 BLOCKED; Pilot A NO-GO.** Esta etapa no repitió el upload/restore R2 validado previamente: cero operaciones nuevas R2, cero Kapso/OpenAI, cero EasyPanel, ningún job instalado, ningún objeto borrado.

## Matriz de aceptación

| Condición | Resultado y evidencia | Responsable / siguiente acción |
|---|---|---|
| Bucket privado, dominios y r2.dev | BLOCKED: .env.example solo contiene R2_ENDPOINT/BUCKET/ACCESS_KEY_ID/SECRET_ACCESS_KEY/REGION, sin API token Cloudflare de administración. HTTP anónimo 400 previo no prueba privacidad. | Gastón: proporcionar lectura del panel o API Workers R2 Storage Read; confirmar r2.dev disabled y cero dominios públicos habilitados. |
| Alcance exclusivo de credenciales, separación de medios | BLOCKED: S3 funciona pero no prueba scope/token policy ni configuración del almacenamiento deportivo de EasyPanel. | Gastón: evidencia token limitado exclusivamente fluxio-movement-backups; writer/reader separados; token de medios distinto o medios en filesystem sin ese token. No probar acceso a buckets ajenos por enumeración. |
| Secretos actuales en candidato/HEAD | PASS limitado: 311 archivos rastreados y HEAD sin coincidencias con ID/secret R2 actuales; nuevos scripts/docs/evidencia y logs sintéticos revisados. No es auditoría de todo historial, tokens revocados o infraestructura. | Gastón: retirar secretos del .env.example original mediante acción autorizada independiente; agente no lo modifica. |
| Retención de objetos sintéticos | PASS de aprobación: usuario confirmó conservar ambos durante el piloto y eliminación manual posterior. No lifecycle ni DELETE. Fechas finales pendientes. | Gastón: aprobar eliminación individual posterior; mantener claves sintéticas mientras se conserven los objetos. |
| Custodia independiente | BLOCKED: claves anteriores en recovery-key-private local con ACL, fuera de R2/Git/EasyPanel; solo ensayo. Recuperación sintética con clave correcta PASS, incorrecta rechazada. No demuestra acceso de otro operador ni pérdida real del host. | Gastón: confirmar almacén externo de claves y acceso de recuperación; propuesta en runbook. |
| Diario / pre-release | PASS del helper offline; BLOCKED instalación/adapter destino. run_job conserva formato AES-256-GCM validado, lock contra solapamiento, recibos atómicos y verificación local/remota. Daily/pre-release separados. Configuración inerte impide ejecución; adaptador aprobado por SHA-256 obligatorio. | Gastón: collector coherente de EasyPanel, transporte y key-store/alert adapter, horario y autorización de instalación. |
| Integridad y retención | PASS: corrupción, clave incorrecta, membresía y hashes, symlinks y traversal rechazados; directorios tar del ensayo anterior compatibles. Plan siete diarios completos y todos los pre-release, sin función de borrado. | Operador: revisar plan manualmente; límite conservador 128 MiB requiere capacidad representativa antes de activar. |
| Alertas | PASS sintético: fallo alcanza receptor local inyectado con ACK; entrega fallida queda registrada. Missing/stale/incomplete detectados; watcher independiente preparado, no instalado. **BLOCKED entrega a Gastón**, canal sin confirmar y no autorizado para envío. | Gastón: elegir canal y autorizar prueba individual; verificar recepción real y respuesta. |
| Restauración local con medios válidos | PASS: esquema completo 29 tablas, 3 usuarios, sesión con nota/foto, análisis y review; cuatro archivos, PNG verificado por PIL, MP4 original/annotated leídos por FFprobe, hashes/referencias iguales, nueva DB vacía, head 0024 conservado sin migrar después de restore. | QA: medios artificiales y análisis/review precargados; no certifica semántica biomecánica ni flujo web/coach restaurado. |
| Recuperación representativa de EasyPanel | BLOCKED/NOT RUN: no acceso/inventario ni autorización del conjunto real. 7,58 s de ensayo sintético incluye tests del helper y transferencia local, no un RTO/RPO real. | Gastón: inspección autorizada de destino, ventana coherente, backup real autorizado y restore aislado; aprobación separada previa a cualquier acción real. |

## Implementación y pruebas

Archivos nuevos: scripts/pilot_backup_ops.py; scripts/test_pilot_backup_ops.py; docs/pilot-v1/BACKUP_AUTOMATION.cron.example; S16_OPERATIONAL_EVIDENCE.json. Actualizados los tres entregables pedidos y BACKUP_CONFIGURATION.example.json. Sin cambios en app, modelos, migraciones, Compose, workflow o contratos del producto. No dependencias nuevas: cryptography existente y stdlib.

- Windows: 27 PASS / 1 SKIPPED (permiso symlink). Linux: **28 PASS, cero FAIL/SKIPPED** con el helper definitivo. Son las mismas pruebas, no sumar totales.
- Integrado: PostgreSQL 17.6 y storage tmpfs nuevos, red interna exclusiva 10.253.9.0/28, sin publicar puertos Docker ni incorporar redes existentes. Fuente copiada a tmpfs; proveedores apagados. Estado restaurado validado y contenedores propios detenidos.
- Evidencia final: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-qybhgju9/` (environment.json, ops-tests.log, operational-results.json), hashes públicos en S16_OPERATIONAL_EVIDENCE.json. Suites completas históricas 820 Python + 77 JS corresponden a fuentes app previas; no se afirman reejecutadas aquí. Cambios acotados ops tienen suite propia y restore integrado, no cierre final del piloto.
- Intentos previos del harness: fallo de docker cp con ruta Windows y fallo transitorio al inspeccionar una red Docker. Corregida transferencia por stdin, sin debilitar guardas; nuevo entorno para la repetición. Sin errores del producto. Una prueba integrada anterior con 26 tests pasó antes de añadir dos regresiones tar; sustituida por evidencia final de 28.
- Comprobación del original: 153 rutas fingerprint sin cambios; Git original muestra .env.example modificado por configuración del usuario. No hubo escrituras del agente allí.
- La revisión automática bloqueó la primera búsqueda por riesgo de imprimir secretos; se sustituyó por lectura de nombres/presencia y escaneo sin valores. No permanece bloqueo de esa operación segura.

## Riesgos y cierre

No considerar preparado un cron como instalado ni un receptor simulado como notificación recibida por Gastón. El adaptador está pendiente: debe recoger pg_dump completo y todos los archivos bajo mantenimiento real comprobado, recuperar clave desde custodia aprobada, ejecutar TLS/S3 y notificar al canal confirmado. Flags JSON no demuestran quiescencia ni privacidad. El helper limita tamaño en memoria a 128 MiB y no sirve como evidencia de capacidad de un piloto con videos grandes; excederlo bloquea y genera fallo, sin truncar datos. No reintenta uploads inciertos ni borra conjuntos parciales.

No habilitar S11 ni GO. Pendientes nominales: Gastón para privacidad/scope/separación, custodia, canal/horario/fechas y autorización EasyPanel; QA para restauración representativa y controles del sistema restaurado; release para identidad/paridad del artefacto. Detenerse para revisión. Commit final de esta etapa: git log -1 -- scripts/pilot_backup_ops.py.

---

## Evidencia histórica conservada

# S16 — ensayo sintético R2 / estado vigente

Fecha: 2026-10-11, America/Santiago. Responsable operativo confirmado por el usuario: Gastón. Base documental `1f250ddc82e7dd9292c656d856c89073493f379d`; fuentes funcionales `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. Usuario autorizó lectura y luego upload/restore sintético a `fluxio-movement-backups`; no autorizó copias del producto, scheduler, borrado, deploy ni proveedores IA. **PASS del ensayo sintético; S16 continúa PARCIAL/BLOCKED y Pilot A NO-GO.**

## Evidencia y resultados

- PASS: esquema completo migrado desde cero únicamente en PostgreSQL 17.6 tmpfs nuevo, revisión `0024_training_save_requests`; red interna nueva, sin puertos publicados, proveedores deshabilitados y sin claves OpenAI/Kapso.
- PASS: conjunto coherente sin productores/worker ni escrituras concurrentes: PostgreSQL custom dump y cuatro archivos sintéticos (foto PNG válida, original/annotated con bytes de prueba, JSON de análisis). Los archivos de video son placeholders; este ensayo no certifica reproducción, biomecánica ni flujo de coach por API/navegador.
- PASS: cifrado cliente AES-256-GCM, clave aleatoria 256 bits, nonce 96 bits y AAD; clave separada del objeto R2, directorio local de recuperación restringido mediante ACL al usuario actual. TLS validado por cliente HTTPS. Clave incorrecta rechazada mediante InvalidTag.
- PASS: PUT y GET autenticados 200; igualdad del ciphertext y SHA-256 de DB/storage. Carga final 92.197 bytes, conservada en `synthetic-validation/eb25e70ccc31/backup.tar.aes256gcm`.
- PASS: pg_restore --exit-on-error en base nueva vacía `movement_s16_restore`, sin upgrade posterior; conteos iguales: 3 usuarios, 1 entrenamiento con nota, 1 foto, 1 análisis, 1 revisión completada. Archivos restaurados en directorio nuevo; referencias DB/storage verificadas, esquema conservado.
- PASS limitado: 5,31 s de ensayo interno (preparación de datos hasta comprobación), 3,62 s desde snapshot coherente hasta verificación. No incluye creación del entorno, recuperación por otro operador ni un incidente real; no constituye RTO/RPO operativo ni benchmark de datos reales.
- NOT VERIFIED: petición anónima al endpoint S3 devuelve 400 sin contenido; esto no demuestra ausencia de dominio público o r2.dev. Configuración de política respondió 501 NotImplemented y lectura de cifrado 403 AccessDenied en inspección previa. Cifrado cliente demostrado; configuración de cifrado del proveedor no verificada.
- FAIL del primer harness: esperaba únicamente 401/403 para la solicitud anónima y R2 devolvió 400. Corregida solo la expectativa del script temporal; no se relajó el requisito de privacidad ni se cambió código del producto. Segundo ensayo ejecutado en recursos nuevos. Primer objeto cifrado y clave sintética conservados, sin borrado; no fue marcado PASS de restauración.
- PASS: ambos grupos propios de contenedores detenidos; tmpfs no contiene datos persistentes al finalizar. Ninguna imagen, volumen, contenedor existente ni objeto R2 eliminado. Dos uploads pequeños conservados; cargos reales no conciliados ni estimados como tarifa.

Evidencia local final: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-90w55bof/` (environment.json y r2-trial-results.json). Primer intento: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-_m3i4zcv/`. Claves sintéticas fuera de Git y R2, en recovery-key-private de cada evidencia; custodia solo de ensayo, no producción. Los scripts temporales se conservan fuera del producto; sus hashes figuran en S16_SYNTHETIC_R2_EVIDENCE.json. No se copia ningún .env ni valores secretos.

## Cambios, regresiones y límites

Solo documentación y plantilla JSON inerte. Ejecución, scheduler, retención destructiva y limpieza de fotos continúan deshabilitados. No cambios funcionales, modelos o migraciones. Suites completas previas del mismo código: Python 820 PASS / 1 SKIPPED (dominio real faltante), JS 77 PASS. No se repiten por un cambio documental; restore no sustituye pruebas de sesión/coach/links del sistema restaurado.

No se escribió en el workspace original. Fingerprint de 153 rutas sin cambios; estado Git original difiere del histórico porque .env.example está modificado por configuración del usuario. Credenciales renovadas según confirmación del usuario; lectura únicamente, sin imprimir ni incorporar a Git. Riesgo pendiente: credenciales reales en un archivo plantilla habitualmente rastreado; no incluirlas en ningún commit.

## Pendientes para cierre

1. Verificar R2 private/r2.dev/domains, AES-256 del proveedor y permisos mínimos; identidades writer/reader separadas y autorización del conjunto definitivo.
2. Custodia duradera y separada de claves backup y todas las versiones WhatsApp/sharing; recuperación por Gastón desde ese almacén. No usar clave sintética local para datos del piloto.
3. Inventario y coherencia reales de DB/storage/configuración, candidato y artefactos; ensayo de aplicación restaurada con medios reproducibles, análisis/reviews, claves y controles S02–S08, no solo hashes/conteos.
4. Aprobación específica antes de respaldar/restaurar datos del producto. Medir tamaño representativo, transferencia/arranque/recuperación de claves e integridad y aceptar RTO/RPO.
5. Scheduler diario/predeploy, siete diarios y pre-release; horario/fechas, entrega real de alertas y retención revisada. No borrar los objetos de ensayo sin autorización individual.
6. Restantes gates: canales reales completos, video/costos, coaches nominales y certificación, alertas, CI con gates, artefacto/digest, paridad EasyPanel y rollback.

Recomendación: aceptar solo el ensayo sintético y revisar los pendientes; no cerrar S16, activar S11 ni declarar GO. Commit de esta entrega: consultar git log -1 -- docs/pilot-v1/S16_IMPLEMENTATION_REPORT.md.

---

## Evidencia histórica anterior — sustituida donde corresponda

# S16 — Preparación de configuración y procedimiento, sin ejecución

Fecha: 2026-10-11. Política objetivo Pilot A aprobada expresamente por el propietario: destino privado cifrado S3 compatible o Azure Blob independiente de VPS EasyPanel; AES-256/TLS; DB y archivos privados; diario/predeploy; siete diarios y pre-release durante piloto; propietario técnico como rol principal; restore aislado obligatorio; credenciales exclusivas mínimas; alertas de fallo/antigüedad.

Estado: **PREPARACIÓN DOCUMENTAL / BLOCKED para ejecución y cierre**. No hay proveedor, bucket ni responsable operativo formal confirmado. No se iniciaron operaciones persistentes ni implementación de job. Dependencias S01/S14 conservadas; S14 no certificada. S11 parcial sigue bloqueada para cuarentena/eliminación. Política/RPO/RTO aprobados no son evidencia de backup ni medición de restore.

## Archivos y contratos

- BACKUP_CONFIGURATION.example.json: plantilla JSON inerte, sin credenciales/destino real; ejecución/scheduler/limpieza deshabilitados. Null indica pendiente. No está conectada al runtime y no valida infraestructura.
- BACKUP_RESTORE_RUNBOOK.md: precondiciones, mapeo DB/storage/claves, permisos por roles, coherencia con escritores pausados, manifiesto protegido, retención, alertas, restore desechable, compatibilidad y rollback.
- DEPLOYMENT_RUNBOOK.md y documentos de seguimiento: referencias y estado vigente; información anterior conserva carácter histórico.

Código funcional, Compose, scripts de arranque, modelos y migraciones: **sin cambios**. No se instala cron ni integración S3/Azure, no se eligen servicios, no se crean recursos/cuentas/credenciales. Valores secretos excluidos.

## Validaciones de esta preparación

| Verificación | Estado |
|---|---|
| Parse JSON y comprobación de campos de seguridad/pendientes | PASS: JSON válido; ejecución/scheduler/limpieza deshabilitados; destinos y credenciales pendientes; política/retención/objetivos comprobados |
| git diff --check | PASS; enlaces locales nuevos comprobados |
| Fingerprint original | PASS: 153 paths sin cambios, estado/rama/HEAD originales conservados |
| Suites Python/JavaScript | SKIPPED: solo documentación/plantilla inerte; referencia S11 795 Python/72 JS PASS, no resultados nuevos |
| Respaldo real, upload proveedor y alertas entregadas | BLOCKED / NOT RUN |
| Restore sintético o real, RPO/RTO medidos | NOT RUN; preparación no equivale a ensayo |
| Permisos/cifrado/TLS del destino, paridad EasyPanel | BLOCKED / NOT VERIFIED |

## Riesgos y recomendación

Sin copia restaurable certificada no habilitar piloto ni limpieza efectiva. Crecimiento de fotos huérfanas sigue pendiente. La pausa coherente diaria tiene impacto de disponibilidad y exige ventana/operador; no fue ensayada. La retención no activa eliminación automática. Custodia de claves y acceso de restore deben verificarse separadamente del bucket. S11 y S16 no se declaran cerradas, otras fases no iniciadas por esta preparación.

Próximo paso: seleccionar y aprobar proveedor/destino y operador formal; revisar configuración concreta/permisos/canales, preparar ensayo aislado autorizado y registrar evidencia antes de activación. Este encargo no autoriza gasto ni acciones persistentes. Pilot **NO-GO** con cinco gates heredados conservados.

Commit documental de entrega: consultar git log -1 -- docs/pilot-v1/S16_IMPLEMENTATION_REPORT.md. Commit funcional continúa a4aefd7726a5d6f5f9b5c454bca16192ce0fe62d (S11 parcial); no commit funcional S16.
