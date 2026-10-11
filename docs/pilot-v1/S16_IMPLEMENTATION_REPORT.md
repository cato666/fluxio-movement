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
