# S16 — Evaluación de respaldo online sin interrumpir WhatsApp

2026-10-12. Código revisado: 5dde1487cd7fe47cad8018837a97f23a3d70c39b. **Solo evaluación; sin implementación ni autorización de ventana. S16 BLOCKED / Pilot A NO-GO.** Los diseños de receptor y medios permanecen propuestas no construidas.

## Recomendación concreta

Recomiendo **B mediante archivos publicados atómicamente, inmutables y protegidos contra borrado, con manifest de referencias leído del MISMO snapshot SQL usado por pg_dump**. Mantener API, worker y webhook actuales vivos. No incorporar receiver, nueva base de datos, broker, bucket de medios ni snapshots de infraestructura para esta opción mínima. Reutilizar cifrado, R2, manifiesto/verificación, alertas y restore del Runner; modificar únicamente en una etapa posterior aprobada su collector y las reglas de publicación/eliminación del producto.

No es compatible con el código actual sin cambios: hoy existen referencias a uploads parciales, unlink concurrentes y el collector rechaza cualquier cliente DB. No basta retirar esa guarda o ejecutar rsync mientras pg_dump corre. Esta evaluación cambia la recomendación de arquitectura según el objetivo de evitar interrupciones: B evita la causa que obligaba a construir el receiver, siempre que se prueben sus invariantes. A/C quedan alternativas si no se puede cubrir todos los escritores.

La garantía es restaurar coherentemente el estado SQL del snapshot T y los bytes exactos referenciados en T. No garantiza recuperar mensajes posteriores a T ante pérdida del VPS ni revertir entregas ya efectuadas por Kapso; eso es RPO/conciliación de desastre, diferente de pérdida causada por interrumpir el webhook durante un backup.

## 1. PostgreSQL online: qué garantiza y qué no

[pg_dump PostgreSQL17](https://www.postgresql.org/docs/17/app-pgdump.html) permite respaldo consistente con lectores/escritores concurrentes. No requiere pausar sesiones normales. Usa snapshot y locks de lectura; DDL concurrente puede interferir. Prohibir despliegues/migraciones/DDL durante captura, limitar duración/carga y considerar retención MVCC/vacuum y locks. No afirmar que cualquier carga carece de impacto.

El Runner ya exporta snapshot REPEATABLE READ READ ONLY y usa pg_dump --snapshot. Lo reutilizable es ese snapshot. [Sincronización de snapshots](https://www.postgresql.org/docs/17/functions-admin.html#FUNCTIONS-SNAPSHOT-SYNCHRONIZATION): mantener transacción exportadora abierta para lectura de referencias y dump del mismo conjunto visible. Roles/extensiones/ACL/config/secrets requieren recuperación aparte, como en runbook existente.

pg_dump NO captura filesystem, operaciones externas ni byte contents de rutas guardadas como texto. Dos snapshots SQL/FS tomados a horas diferentes no se vuelven consistentes por guardar timestamps cercanos.

## 2. Evidencia de ciclo de vida del código actual

| Flujo/archivo | Comportamiento revisado | Riesgo de backup online / ajuste necesario |
| --- | --- | --- |
| app/services/training_media.py: save_image | UUID nuevo, JPEG normalizado escrito directamente al path final | Normalmente precede fila TrainingImage; falta publicación temp/fsync/no-overwrite formal para durabilidad/crash |
| app/services/training_service.py: store_image/delete | Fila tras guardar; error elimina path; borrar sesión no borra fotografía | Proteger cleanup de archivo que pudo quedar referenciado en snapshot anterior; fotos orphan no son permiso de borrado |
| app/main.py: _prepare_async_analysis y flujo legacy | Analysis PENDING/video_path se commit antes de terminar open(wb) upload; oversized puede unlink tras registrar FAILED | Un snapshot puede contener path ausente/parcial; publicar original completo antes de primera referencia durable |
| app/main.py: _process_analysis | Resultados desde temp a annotated/analysis y thumbnail; referencias se commit después | Buen orden lógico, pero shutil.move no acredita rename atómico si cambia filesystem, fsync o no-overwrite. Formalizar publicación |
| app/main.py: reanalyze | Nuevo job/derivados, comparte video_path original | Modelo ya se aproxima a versiones, conservar original hasta que ningún snapshot activo lo necesite |
| app/main.py: delete_analysis | Borra DB/commit y luego revisa referencias actuales/unlink | Verifica DB presente, no referencias del snapshot antiguo: puede destruir archivo necesario al dump |
| app/whatsapp/media.py | Imágenes por pipeline común; MP4 en original/whatsapp con UUID antes de fila WhatsAppMedia | Formalizar publicación; incluir referencias WhatsAppMedia en manifest y guardas de eliminación |
| app/whatsapp/worker.py: cleanup | Fotos conservadas por S11; otros medios no asociados vencidos pueden unlink ANTES de borrar fila/commit | Carrera SQL/FS; no unlink durante captura y cambiar orden lógico/eliminación física controlada |
| app/services/training_transcription.py | Audio temporal en TemporaryDirectory, transcripción; no persistencia de grabación | No ampliar privacidad para incluir audio original. Respaldar resultados durables existentes; no prometer recuperar audio en curso solo por dump |
| app/services/photo_retention.py | Inventario dry-run, sin unlink/DB write | Conservar ese modo; no activar limpieza S11 para habilitar backups |
| scripts/pilot_backup_runner.py: capture/snapshot | Ventana obligatoria, rechaza otros clientes, copia TODO root antes de dump, exige inventario estable | Designed offline; necesita collector online distinto, no eliminar protecciones sin sustituto demostrado |

STORAGE_PATH usa original, annotated, analysis, training-images y temp. Rutas DB pueden tener aliases uploads/results y relativas/absolutas; resolver mediante mapeo explícito actual, no join ingenuo ni reescribir registros históricos. Paths peligrosos/externos/symlinks bloquean set, nunca traversal. video_links remotos no implican que se pueda descargar contenido externo en backup.

## 3. Comparación A/B/C

| Criterio | A: mantenimiento + receiver | B: snapshot SQL + archivos inmutables | C: pausa mínima de escritores con webhook vivo |
| --- | --- | --- | --- |
| Consistencia | Coherente cuando pausa/drain verdaderos y collector actual | Coherente por mismas referencias/snapshot y bytes inmutables retenidos | Coherente si pausa/drain cubre todos los escritores de archivos y referencias relevantes |
| WhatsApp | Nueva recepción durable + consentimiento/spool/ACK deadline | Recepción e inbox actuales continúan; no routing/replay nuevos | Webhook actual puede seguir escribiendo inbox mientras se pausa worker/medios; no necesita receiver nuevo si no se detiene API |
| Cambios | Nuevos servicio/SQLite/grants/spool/replay/recibos/operación | Publicación/GC/ref-manifest/collector, sin nuevo servicio | Gates de rutas, no-new-claims/drain para worker/video, permisos y collector online de SQL |
| Runner | Menor cambio al collector offline, mayor entorno | Collector cambia; bundle/crypto/R2/restore aprovechables | También cambia: guarda sin clientes actual incompatible con webhook vivo |
| Infraestructura | Volúmenes/secretos/routing/backup de cola nuevo | Montajes y R2 existentes; no snapshot host indispensable | Puede necesitar snapshot filesystem real para que pausa sea breve; capacidades EasyPanel desconocidas |
| Operación | Compleja, receiver es nuevo componente crítico | Baja-media; backup sin ventana visible, GC temporalmente diferido | Media-alta; demostrar bloqueo de TODOS los flujos sin cortar ingreso |
| Estimación orientativa | Diseño de medios anterior15–23 días | 5–8 días locales +1–2 ensayo autorizado; legacy irregular puede ampliar | 4–7 días +ensayo; snapshot/drain específico puede ampliar |
| Riesgo principal | ACK de medios y consentimiento durante pausa, nueva cola privada | Escritor o unlink no cubierto, referencias antiguas inválidas, inmutabilidad incumplida | Escritor sin gate, tareas que no drenan, pausa deja de ser mínima, expiraciones |

Ninguna opción es lista hoy. Estimaciones incluyen pruebas locales, no certificación real ni autorización de infraestructura/consumo.

## 4. B mínima: invariantes que hacen suficiente el manifest

1. Todo archivo referenciado durablemente existe completo, cerrado y publicado antes del commit que hace visible su referencia. Temp de upload no es referencia publicada. En video cambiar preparación/legacy para no commit path de original parcial: conservar contrato HTTP y job, pero publicar antes de primera referencia durable. No fabricar copia válida de un upload fallido.
2. Un path publicado nunca se sobrescribe ni muta. UUID/generación nueva para originales/derivados/reanálisis y update transaccional de referencias. Resultados y notas/reviews que viven en DB quedan en snapshot; si el JSON archivo no se modifica al editar review, no regenerarlo silenciosamente. Toda futura regeneración publica versión nueva.
3. Ningún archivo que existía en T puede ser eliminado hasta que termine la captura de su set. Implementar fence de GC compartido entre Runner y TODAS las rutas físicas de eliminación. Propuesta: lock advisory PostgreSQL compartido de backup adquirido ANTES de snapshot y liberado tras copia/verificación; GC toma lock exclusivo mediante try-lock, no espera bloqueando el worker. Si busy, difiere eliminación física con registro durable o conciliación de huérfanos existente/manual aprobada. No introducir job efímero ni retención fija que venza a mitad de backup.
4. Borrado lógico del recurso puede seguir y preservar autorización: un archivo físicamente retenido no se vuelve accesible públicamente. Cleanup no puede unlink antes de commit del retiro lógico. La eliminación futura debe respetar referencias actuales, originales compartidos y snapshots activos; resolver crash tras commit sin liberar bytes necesarios.
5. Fsync archivo/directorio y publicación atómica/no-overwrite sobre mismo filesystem, incluyendo entrenamiento, originals, annotated, thumbnail y JSON. Rollbacks solo retiran artefactos nunca publicados; si pudieron ser visibles, entran al fence. No confiar solo en UUID para acreditar inmutabilidad de rutas legacy.
6. Todos los actores conocen el protocolo: no shell manual/rsync/cron/directwriter fuera del fence; precondición verificada por Gastón. Collector falla cerrado ante referencia requerida ausente, hash cambiante o cliente DDL incompatible. No marcar conjunto COMPLETE incompleto.

Con estas reglas: cualquier fila visible en T referencia bytes publicados antes de T; cambios posteriores usan otras versiones y borrados no pueden quitar esos bytes mientras se copian. Por ello no se necesita snapshot FS simultáneo ni pausa de API. Archivos creados después de T no pertenecen al set y no provocan drift por el simple crecimiento del directorio.

El fence es coordinación contra destrucción, NO pausa global de escrituras ni bloqueo de webhook/inbox. Advisory lock no exige privilegio administrador, pero verificar rol/funciones/locks/réplicas y funcionamiento; no escribir en tablas desde rol de backup. Si proceso muere se libera lock, pero set queda INCOMPLETE; no certificar captura después del crash. Timeouts liberan fence y alertan, pendientes de GC nunca desaparecen.

## 5. Captura online propuesta

1. Validar versión, secretos/RO/espacio, ausencia de DDL/deploy y protocolo de inmutabilidad/GC habilitado; no habilitar modo online por defecto antes de certificar escritores.
2. Tomar fence compartido con timeout y abrir/exportar snapshot READ ONLY. Leer head y referencias en esa misma transacción: todas las TrainingImage (incluso no asociadas a sesión), WhatsAppMedia, Analysis original/annotated/json/thumbnail, derivados y cualquier otro path durable descubierto. Mantener schemas completos y no filtrar filas del dump por conveniencia.
3. Manifest interno cifrado clasifica cada path canónico requerido con origen/modelo opaco, versión y hash/tamaño; dedupe originales compartidos. Enumerar mediante lectura consistente, no inventario del filesystem vivo como fuente autoritativa. Hash/comparación no sustituyen inmutabilidad ni fence.
4. pg_dump --snapshot y copia de paths exactos del manifest a staging protegido, en cualquier orden mientras exportador/fence estén vivos. Verificar tamaño/hash/no symlink de cada copia y source; no exigir root antes=después ni cero clientes normales. Nuevas sesiones/inbox y archivos posteriores quedan para siguiente backup.
5. Cerrar snapshot/fence solo después de capture completa/verificada. Bundle/AES/key_id/R2/GET-verificación/receipt existentes continúan sobre staging; app nunca se detuvo. Stamp corresponde al snapshot identificado, no solo hora de finalización.
6. Referencia ausente o mutable inesperada -> FAIL, no omitir. Legacy histórico que ya apunta a archivo perdido necesita clasificación/remediación autorizada individual; no declarar backup válido ocultando la pérdida. Metadata FAILED sin archivo requiere contrato explícito de artefacto no disponible, no excepción automática para todo FAILED.

Temp/scratch sin referencia durable no se prometen restaurables: excluir explícitamente del set final conforme aprobación del cambio de contrato. Si el requerimiento exige cada archivo huérfano/temp del filesystem, documentar que no tiene estado transaccional SQL; capturarlo suplementariamente no permite reclamar instante global idéntico. No activar borrado para simplificar inventario. Nuevo manifest versionado compatible con bundle/restore; no asumir que actuales REQUIRED dirs/inventory y format aceptan sin ajuste sets selectivos.

## 6. Estados en curso y restore coherente

Un snapshot online puede guardar inbox PENDING, outbox SENDING, análisis PROCESSING y reservas STARTED. Eso es un estado válido en T, no autorización para repetir proveedores tras restore. Mantener originales publicados y dependencias persistentes; API actual marca análisis pendientes/interrumpidos FAILED al arrancar. Documentar/certificar recuperación de trabajos no terminados sin nuevas llamadas automáticas. No prometer recuperar audio temporal o imagen todavía no committed en T.

Restore aislado: dump completo + archivos del mismo manifest, hashes/key_id, same logical paths, app/worker con proveedores y scheduler deshabilitados. Revisar relaciones, fotos, videos reproducibles, resultados, revisiones, permisos/links; conservar claves externas del producto. No migrations/seed silenciosos.

Desastre real: detener automatismos hasta conciliar delivery-provider/outbox/S06, especialmente SENDING o SENT posterior a T perdido del SQL restaurado. Mantener UNCERTAIN sin reenvío automático. Los webhooks ACK posteriores a T pueden perderse si el VPS desaparece antes del siguiente backup; ni pg_dump online ni un filesystem snapshot eliminan ese RPO. Si se exige cero pérdida ante ese desastre, hace falta persistencia externa pre-ACK/PITR u otro alcance, no incluido. Durante backup normal sin caída, mantener endpoint/inbox actuales evita introducir pérdida por indisponibilidad.

## 7. Snapshots FS y alternativa C

Snapshot de volumen solo congela bytes del filesystem; sin coordinación con snapshot SQL puede contener archivo nuevo con fila antigua, ausencia de borrado posterior o upload parcial. Requiere FS/capacidades reales (LVM/ZFS/etc.), orden temporal/retención y protocolo de referencias; no se acreditan desde Compose ni EasyPanel. Evitar diseñar infraestructura nueva para B mínima.

C posible: dejar webhook autenticado/inbox API vivos y pausar solo publicación/destrucción de archivos y worker/video, con gate/drain verificable; SQL dump online acepta nuevas filas inbox sin medios descargados aún. No confundir recepción con archivo: manifest T puede contener referencia media de proveedor y su recuperación posterior no garantizada. Gates deben incluir web manual/foto/audio, coach/admin, análisis asíncrono, cleanup/reanalyze y escrituras internas. No existe no-new-claims fiable hoy.

Sin snapshot FS, copiar todos los archivos puede durar minutos: C no es automáticamente pausa breve. Con snapshot FS atómico coordinado tras drain, acortar pausa y copiar después, pero capacidad externa desconocida. No parar API porque alberga webhook. La guarda actual del Runner igual debe cambiar; C no es una solución sin modificaciones.

## 8. Cambios mínimos futuros y pruebas

Archivos candidatos, no editados: app/main.py (publicación original/derivados, borrado), app/services/training_media.py, training_service.py, app/whatsapp/media.py, worker.py; helper acotado para publicación/fence; scripts/pilot_backup_runner.py (collector online/ref-manifest), pilot_backup_bundle.py/restore/ops solo si cambia contrato de manifest y REQUIRED. Tests/runbooks correspondientes. Puede requerir pequeño journal/migración de GC si se opta por defer durable automático; alternativamente conservar huérfanos bajo inventario/manual ya previsto, sin construir cleanup nuevo ahora. Resolver en diseño aprobado antes de modificar. No cambiar runtime de interpretación/sharing ni sender.

Pruebas de recuperación necesarias con PostgreSQL/storage desechables y proveedores simulados:

- Imagen/nota/sesión/WhatsApp comprometidos antes, durante y después de T: dump y manifest coinciden en T; ACK de webhook continúa y no duplica.
- Upload parcial antes de publicar y crash antes/después fsync/commit: ningún path visible apunta a parcial; snapshot de operación en curso tiene política clara.
- Borrar original/review/video o cleanup WhatsApp mientras captura: unlink diferido/no faltantes; logical delete no vuelve público el archivo retenido.
- Reanálisis comparte original y cambia derivados, updates/versiones concurrentes: hash antiguo intacto y restore de T reproducible.
- File-mutation fuera de protocolo, path ausente/symlink/legacy inválido: FAIL explícito; no COMPLETE ni bypass.
- Fence tomado antes de snapshot, varias réplicas/backup concurrente, GC try-lock, crash/timeouts, nueva referencia mientras copia: sin deadlock ni suspensión del webhook.
- DDL/deploy concurrente rechazados/lock timeout; SQL exportado idéntico para manifest/dump; carga y duración aceptables.
- Restore exacto con PNG/MP4/reviews/notas/consentimiento/usuarios, claves/paths/versiones y estado outbox/reservas; salientes inciertos no reenviados.
- R2/cifrado/alertas fallidos: capture lock liberado, set incompleto conservado, fuentes nunca borradas; privacidad logs/regresiones S02–S08.

Después, ensayo representativo autorizado, API/worker/webhook realmente activos, fuentes de prueba consentidas y RPO/RTO/latencia/capacidad medidos. Sin ese ensayo no certificar S16 operativo. No repetir sintéticos previos sin necesidad, pero nuevo collector requiere nuevas pruebas concurrentes/restore.

## Decisión para revisión

Aprobar B como siguiente diseño acotado de inmutabilidad/publicación/GC y captura por referencias, manteniendo receiver/spool en pausa. Condición: demostrar cobertura total de caminos de publicación/destrucción y resolver legacy antes de declarar viable para producción. Si no se puede, presentar C con gate probado y capacidades reales; no volver automáticamente a implementar A.

Revisión de código/documentación PASS; suites SKIPPED (solo evaluación), concurrencia/restore nuevo NOT RUN, infraestructura NOT VERIFIED. No se modificaron Runner/código funcional, crearon servicios, consultaron EasyPanel/datos reales ni consumieron proveedores/push/deploy. S16 BLOCKED / Pilot A NO-GO. Estimación B 5–8 días +ensayo autorizado, pendiente de inventario/cobertura/legacy. Commit local: git log -1 -- docs/pilot-v1/S16_ONLINE_BACKUP_EVALUATION.md.
