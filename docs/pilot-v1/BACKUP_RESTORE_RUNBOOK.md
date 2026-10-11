# S16 — decisiones confirmadas y acceso EasyPanel pendiente

Fecha: 2026-10-11. Base 7598e38. Custodia elegida KeePassXC Windows + copia externa cifrada; runtime secrets pendiente. Resend preferido, destinatario/remitente/dominio/API key privados pendientes. Ninguna clave generada/reemplazada y ningún correo enviado.

**S16 BLOCKED / Pilot A NO-GO.** Lectura EasyPanel autorizada, pero no sesión administrativa/SSH ni URL de panel disponibles. Host documentado responde GET /health 200 con TLS validado; no informa versión ni certifica DB/worker/volúmenes. Inspección parcial en [S16_EASYPANEL_INSPECTION.md](S16_EASYPANEL_INSPECTION.md).

No existe envío API/SMTP actual: solo callback notify_operator y plantilla. Config Resend API propuesta, no implementada/activa. Procedimientos, prueba de un correo, recuperación KeePassXC y backup/restore representativo con autorizaciones separadas en [S16_CUSTODY_RESEND_VALIDATION_PLAN.md](S16_CUSTODY_RESEND_VALIDATION_PLAN.md). Diario no listo para activar por falta de adaptador, claves runtime, capacidad y alertas reales.

Verificaciones de esta etapa: Git/base, búsqueda de mecanismos, presencia de variables sin valores, inventario de sesión disponible, dos lecturas públicas (HEAD / 405 y GET /health 200), consulta de documentación oficial Resend/KeePassXC y validación JSON/gates. No repetir suites sintéticas previas ni registrar como PASS custodia/envíos/restore real no ejecutados. Nuevos deliverables documentales y plantillas inertes solamente. Original leído, sin escrituras; sin nuevos objetos R2, OpenAI/Kapso, cron, migraciones, deploy ni infraestructura modificada.

Próximo paso requiere URL/sesión del panel, referencias KDBX/dispositivo y configuración privada Resend. Leer el reporte antes de autorizar cualquier operación externa de escritura.

---

## Evidencia histórica

# Actualización S16 — 2026-10-11

Privacidad del bucket y token writer exclusivo/Active confirmados por el propietario en Cloudflare; token actualizado validado con dos lecturas HTTP 200, sin objetos ni escrituras. Confirmación del propietario y comprobación técnica tienen alcance distinto. Ver S16_UPDATED_TOKEN_READ_EVIDENCE.json.

**S16 BLOCKED / NO-GO:** falta lector de restore/separación de medios, bóveda independiente y recuperación real de claves, correo configurado/autorizado/recibido, adaptador EasyPanel coherente/capacidad, backup y restore representativo autorizados. Daily/pre-release están preparados pero no listos para activar; ejecución y scheduler permanecen deshabilitados. No repetir ensayos locales ya PASS.

Contrato de correo inerte: BACKUP_EMAIL_CONFIGURATION.example.json. Decisiones y autorizaciones precisas en [reporte S16](S16_IMPLEMENTATION_REPORT.md): primero bóveda y datos SMTP/destinatario, luego acceso EasyPanel de lectura; backup/pausa/restore y activación requieren autorizaciones separadas sobre planes concretos.

---

## Estado histórico conservado

# S16 — operación preparada, todavía no activada

Fecha: 2026-10-11. Consultar [reporte vigente](S16_IMPLEMENTATION_REPORT.md). Gastón es operador confirmado. Bucket fluxio-movement-backups identificado y ensayo R2 AES-256-GCM PASS; cierre operativo BLOCKED.

## Privacidad y permisos: evidencias requeridas

En Cloudflare, R2 → fluxio-movement-backups → Settings: comprobar Public Development URL disabled, todos los Custom Domains ausentes o disabled, y ausencia de Workers públicos que expongan este bucket. Obtener evidencia redactada con fecha sin URLs privadas/token. En Manage R2 API Tokens revisar el token de backup: Object Read & Write, Apply to specific buckets only = fluxio-movement-backups. Crear/confirmar lector de restore Object Read only separado, scope mismo bucket. Revisar token/mount de medios deportivos de EasyPanel sin copiar secretos; comprobar independencia. No cambiar settings ni crear tokens automáticamente.

Referencias oficiales: [public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/) y [tokens R2](https://developers.cloudflare.com/r2/api/tokens/). S3 object credentials no son credenciales REST para consultar el panel; rechazos anónimos del endpoint S3 no prueban privacidad de dominios.

## Custodia propuesta — requiere elección de Gastón

Guardar cada clave AES-256 y su versión/ID en un gestor de secretos o bóveda cifrada independiente de EasyPanel y del bucket de respaldo. Acceso MFA para Gastón y suplente aún por confirmar; clave de desbloqueo/códigos de recuperación bajo custodia independiente, copia offline protegida con procedimiento aprobado. No almacenar el único ejemplar en VPS, repo, logs, objetos R2 o archivo de plantilla. El job recupera temporalmente solo la versión de clave necesaria; no registra valores. Separar el inventario de versiones WhatsApp/sharing y PHONE_HASH_KEY del ciphertext y verificar recuperación histórica.

Ensayo de custodia: desde máquina aislada sin acceso al VPS, Gastón obtiene por ID una clave de la bóveda, descarga un objeto autorizado con identidad reader distinta y verifica descifrado/hashes. Clave errónea debe fallar; quitar acceso al VPS durante la prueba sin destruir servidor ni borrar claves. Registrar ID/versiones y resultado, nunca valores. El ensayo local actual simula esta recuperación, no sustituye este procedimiento ni demuestra disponibilidad de la bóveda.

## Automatización y comandos preparados

Dependencias ya existentes. Verificar rutas privadas, permisos y capacidad antes de ejecutar. No instalar BACKUP_AUTOMATION.cron.example hasta aprobar horario/zona, gates e integración del adaptador. En un entorno autorizado:

```text
python scripts/pilot_backup_ops.py run --config <config-privada> --kind daily
python scripts/pilot_backup_ops.py run --config <config-privada> --kind pre-release
python scripts/pilot_backup_ops.py health --state <directorio-privado-recibos>
python scripts/pilot_backup_ops.py retention --state <directorio-privado-recibos>
```

Los paths relativos de ejemplo se resuelven dentro del release fijado; el scheduler usa paths absolutos. Config plantilla actual execution_enabled=false/scheduler_enabled=false: run devuelve código 2 sin recoger datos ni llamar a proveedores. Código 0 exige recibo COMPLETE y lectura remota verificada; 1 indica incomplete/busy o alerta de health; 2 indica configuración/invocación fallida. Release no continúa si backup falla.

El adaptador operacional aún **no existe para EasyPanel**. Interfaz requerida, fijada por path absoluto y SHA-256 aprobado: collect_quiesced_snapshot() → dump custom completo + snapshot de storage inmóvil; put_encrypted()/get_encrypted() → transporte TLS a prefijo autorizado; recover_backup_key() → clave desde bóveda; notify_operator() → True solo tras ACK real. No pasar una carpeta de storage activa a seal_snapshot. Falta validar productor/API/worker/jobs pausados y cero escrituras en vuelo. No ejecutar entrypoint que seed/migre al restaurar.

Recepción saludable: scheduler/health watchdog independiente del proceso de backup, examina recibos COMPLETE por snapshot_at y alerta >=24 h, primer backup ausente o intento más reciente INCOMPLETE. Errores tienen códigos fijos sin excepciones privadas. Recibo publicado atómicamente; crash previo conserva INCOMPLETE/lock, no last_success ficticio. Lock residual se revisa por operador y nunca se elimina automáticamente ni se toma como permiso para solapar jobs. Alert channel sin confirmar: cron stdout/journal no equivale a entrega.

Retención: retention devuelve keep/proposed_manual_review, conserva siete daily COMPLETE y todos los pre-release; no contiene operación DELETE. Conjuntos incompletos se investigan y nunca se purgan automáticamente. Objetos sintéticos previos: aprobación explícita de conservar durante el piloto y eliminar solo tras aprobación manual posterior; fechas aún por definir. No hay lifecycle instalado.

## Validación representativa real: pendiente de autorización específica

Preparar inventario read-only de DB/version/head, todos los 29 nombres de tablas del candidato y otros schemas si existen, roles, montajes privados y versiones de claves. Dump no filtra tablas: pg_dump custom completo; capturar training-images/original (incluye whatsapp)/annotated/analysis y otros paths persistentes encontrados. La cuenta de DB necesita permisos de lectura completos y backup no incluye claves/contraseñas de proveedor. Confirmar que no faltan medios cifrados o rutas fuera del root; symlinks abortan para revisión.

Gastón debe autorizar ventana coherente, copia real, destino/prefijo, costos y acceso a datos de la copia. Solo entonces tomar backup completo e íntegro, restaurar en instancia NUEVA aislada y recuperar claves desde custodia real. Verificar conteos por tabla, hashes, vínculos, imágenes/video decodificables, usuarios/analyses/reviews, API/medios privados, permisos y sharing consentido/revocado/expirado, worker sin envío ni proveedores reales. Medir desde incidente simulado incluyendo transferencia, clave, pg_restore, filesystem y arranque, no solo paso interno del helper. No extrapolar 7,58 s / muestra sintética a RTO/RPO reales. Límite actual 128 MiB requiere medir y resolver capacidad antes de producción; no activar job que no pueda empaquetar el conjunto real.

---

## Procedimiento histórico y política objetivo

## Actualización S16 — 2026-10-11

Gastón confirmado como operador. Ensayo R2 sintético **PASS**: AES-256-GCM cliente, upload/download autenticados, DB nueva y cuatro archivos restaurados con hashes/referencias iguales; 3 usuarios, 1 sesión/foto/análisis/review, head 0024. Contenedores propios detenidos. 5,31 s y 92.197 bytes corresponden a muestra pequeña, no RTO operativo. Primer intento falló por expectativa HTTP anónima (400); corrección del harness y repetición aislada documentadas. Privacidad por dominios/r2.dev, configuración de cifrado proveedor, permisos separados, custodia definitiva, restore representativo del producto, scheduler y alertas **pendientes**. S16 sigue parcial y **NO-GO**, sin habilitar limpieza S11. Ver [reporte S16](S16_IMPLEMENTATION_REPORT.md).

# Pilot A — Configuración y procedimiento de respaldo/restauración

Estado: preparación documental, sin ejecución. Política aprobada por el propietario; proveedor, bucket/contenedor y responsable operativo no confirmados. La aprobación de esta política no autoriza infraestructura persistente, respaldo real, migración o despliegue. Plantilla: [BACKUP_CONFIGURATION.example.json](BACKUP_CONFIGURATION.example.json). Ningún componente de la aplicación consume esta plantilla; no es un job instalado ni una validación runtime.

## Objetivo y condiciones previas

Destino privado cifrado S3 compatible **o** Azure Blob, independiente del VPS EasyPanel; no se elige proveedor. AES-256 en reposo y TLS en tránsito obligatorios y verificables, sin inferirlos de una etiqueta o del nombre comercial. Acceso público denegado; confirmar ubicación, permisos efectivos, custodia de claves, costos, capacidad y política de eliminación. No habilitar scheduler ni limpieza de fotos antes de evidencia aceptada.

Responsable principal por rol: propietario técnico del proyecto. Falta persona operativa confirmada, suplente, aprobador de restore y canal probado de alertas. No inventar sus nombres ni enviar notificaciones en esta etapa.

La plantilla deja ejecución, scheduler y limpieza efectiva deshabilitados. Campos null requieren decisión/evidencia, no valores demo. No guardar passwords, tokens, connection strings, SAS, claves AWS/Azure o claves de cifrado en Git/manifiestos/logs. Registrar únicamente referencias al gestor privado de secretos. Antes de habilitación futura un operador revisará **todas** las condiciones; cambiar un booleano no constituye autorización ni comprobación de restore.

## Mapeo y permisos por confirmar

- PostgreSQL real: identificar instancia/base/revisión sin exponer conexión; PostgreSQL 17 es la referencia local, no evidencia del destino. Preparar herramienta pg_dump compatible con la versión real. Dump lógico custom, no copia en caliente de PGDATA. Registrar roles/permisos necesarios para reconstrucción sin archivar passwords en el manifiesto.
- Storage privado compartido por API/worker: verificar mount y valor real de STORAGE_PATH. Incluir training-images, original (incluye original/whatsapp), annotated y analysis, además de otros paths persistentes encontrados. No asumir que Compose prueba mounts EasyPanel. Excluir temp únicamente tras comprobar que no contiene archivos vigentes; no borrar nada para preparar respaldo. Symlinks o referencias fuera del root requieren revisión, no seguirlos silenciosamente.
- Recuperación cifrada: custodiar separadamente todas las versiones vigentes/históricas de WHATSAPP_ENCRYPTION_KEYS o WHATSAPP_ENCRYPTION_KEY, WHATSAPP_KEY_VERSION y PHONE_HASH_KEY; inventariar otras claves necesarias y configuración privada. Sus referencias/versiones se registran sin valores. Claves de cifrado del respaldo independientes de las claves de aplicación, acceso mínimo y recuperación comprobada. SESSION_SECRET y secretos de proveedor son configuración sensible; restore de pruebas usa valores aislados y proveedores deshabilitados, sin reutilizar sesiones o conectar servicios reales.
- Identidad exclusiva de backup: lectura mínima necesaria en DB/storage y escritura en prefijo privado autorizado; no credenciales administrativas generales. Identidad de restore separada, lectura/descifrado mínima. Eliminación de generaciones reservada a identidad operativa distinta y autorización explícita; escritor no debe poder destruir todo el historial. Adaptar permisos exactos al proveedor seleccionado y ensayarlos antes de aprobación.

## Procedimiento futuro de respaldo coherente — no ejecutar ahora

1. Autorizar conjunto concreto: proveedor/destino, responsable, candidato/digest, revisión DB, ventana, paths, credenciales por referencia y eventual costo. Confirmar acceso privado, TLS y AES-256 efectivos. Directorio de staging privado cifrado fuera del repositorio, con capacidad/acceso controlados y política de limpieza aprobada; VPS por sí solo no es destino final.
2. Abrir ventana de mantenimiento aprobada para copia diaria y predeploy. Impedir nuevas escrituras en todos los canales; drenar operaciones en vuelo y suspender productores/worker/jobs sin forzar envíos UNCERTAIN ni reintentos 402. Verificar realmente cero escritores/operaciones activas; si no puede garantizarse, abortar o diseñar snapshot coherente ensayado antes. Un pg_dump consistente solo garantiza consistencia DB, no DB+archivos.
3. Bajo esa ventana, obtener pg_dump custom y copia de todos los paths privados asociados. No guardar archivos de fotos/audio en logs. Conservar originales en su ubicación; copia, no movimiento. Coordinar referencias de claves/config desde el almacén de recuperación independiente. No migrar ni cambiar cuentas como parte del backup.
4. Crear conjunto con ID opaco, UTC, duración, commit/digests API+worker, versión PostgreSQL, alembic_version, tamaño, conteos agregados y hashes SHA-256 de cada componente. Índice por archivo privado y rutas vive **dentro del respaldo protegido**, nunca en informe público. Confirmar relación DB↔fotos/análisis y registro de excepciones antes de aceptarlo. Hash detecta integridad, no sustituye autenticidad: proteger manifiesto y su acceso junto al conjunto.
5. Transferir por TLS al destino privado cifrado ya aprobado. Verificar totalidad, integridad, cifrado aplicado, metadatos/versiones y lectura controlada. Una carga parcial queda INCOMPLETE, no adelanta last_success. No eliminar copias anteriores para reparar una falla. Guardar las referencias de secretos por separado; no poner claves junto a objetos que cifran.
6. Reabrir escrituras según procedimiento ensayado; documentar cualquier interrupción/fallo sin datos privados. Un backup recién creado requiere validación; una copia predeploy no habilita despliegue si no fue restaurada y aceptada.

## Frecuencia, retención y alertas

Diaria y antes de **cada** despliegue; definir hora/zona y ventana con operador. Conservar siete generaciones diarias completas y copia(s) pre-release durante el piloto; fechas del piloto pendientes (política S11/S16 previa: 30 días). No purgar pre-release por rotación diaria. No configurar lifecycle destructivo hasta resolver fechas, excepciones, recuperabilidad y aprobación. Eliminar después del piloto requiere decisión explícita; no prolongar retención de datos privados silenciosamente.

Alertar fallo/incompleto de job, ausencia de primera copia válida, integridad/descifrado fallidos y última copia completa antigua. Umbral propuesto 24 h, alineado con objetivo RPO aprobado; confirmar horario/tolerancia y canal operativo antes de activación. Un scheduler corriendo no prueba respaldo vigente. Métricas mínimas: resultado, edad last_complete_verified, duración, tamaño total, ID opaco y código de error sin rutas privadas, teléfonos, tokens o contenido. Canal y entrega de alerta deben ensayarse; no se implementa ni envía aviso ahora. RPO ≤24 h/RTO ≤4 h son objetivos aprobados, no garantías medidas.

## Ensayo futuro de restauración aislada — obligatorio antes de atletas

1. Autorizar destino de ensayo **nuevo y desechable**, selección individual del conjunto y responsable; nunca restore sobre DB/volumen activo. Primero ensayo con datos sintéticos; restore con datos reales requiere autorización, acceso restringido y política de destrucción de la copia. No abrir puertos públicos ni ampliar redes Docker existentes para facilitarlo.
2. Aislar ingress, scheduler y worker; OpenAI/Kapso deshabilitados y sin credenciales reales. No ejecutar entrypoint automático que migra o seed al iniciar. Descargar/verificar manifiesto y hashes; restaurar DB a instancia vacía compatible y storage a directorio privado vacío. Recuperar versiones de claves necesarias por canal restringido sin imprimirlas.
3. Comprobar alembic_version y compatibilidad con commit/digests antes de arrancar API/worker. Primero validar esquema restaurado tal cual, sin upgrade automático ni downgrade. Un ensayo de migración incremental es una prueba distinta, autorizada sobre copia desechable, no parte implícita de este encargo.
4. Validar conteos y referencias DB/archivos, lectura privada de fotos/análisis, notas/historial, controles coach/atleta, cuenta inactiva y sharing consentido/revocado/expirado. Probar descifrado necesario sin exponer payloads; identidad válida no autoriza envío. Mantener replay de outbox/UNCERTAIN bloqueado y reconciliar evidencia antes de cualquier recuperación individual.
5. Medir RTO desde inicio de recuperación hasta validación funcional y RPO desde instante coherente del conjunto hasta incidente simulado; incluir transferencia, recuperación de claves y arranque, no solo pg_restore. Registrar PASS/FAIL/BLOCKED por escenario y aceptación del responsable. Una prueba local no certifica destino/proveedor real.
6. Conservar evidencia redactada y gestionar copia desechable conforme a autorización específica. No automatizar destrucción ni reconectar al destino productivo. No habilitar atletas hasta restore aceptado y restantes gates cerrados.

## Rollback y relación con S11

Preferir rollback de binario/config API y worker como conjunto únicamente si se ensayó compatibilidad con esquema actual 0024 y claves. S14 (digest/manifiesto) permanece pendiente; no asumir que binario viejo arranca tras revisión nueva. Si no es compatible, mantener mantenimiento y preparar corrección o restore a instancia nueva. Restaurar un conjunto anterior puede perder escrituras posteriores: requiere reconciliación, decisión y autorización de cutover; nunca downgrade/reset/truncate sobre datos persistentes.

S11 conserva todas las fotografías. Antes de habilitar cuarentena de siete días o eliminación, implementar primera observación durable de orfandad (24 h), referencias/locks/journal recuperable y ensayar recuperación DB+archivo; la copia anterior debe contener los archivos afectados y ser restaurable. Política aprobada y plantilla no cierran S16 ni S11.

## Evidencia pendiente y Go/No-Go

Proveedor, endpoint, bucket/contenedor privado, cifrado/TLS efectivos, credenciales exclusivas/permisos, operador formal, hora de ejecución, canal de alerta probado, fechas de retención, backup coherente e integridad, restore medido/aceptado y rollback compatible: **PENDIENTES**. Además siguen abiertos E2E integrado S05, costos adicionales de video, paridad EasyPanel y validaciones reales de proveedores. Pilot **NO-GO**. Ningún respaldo, restore, migración, despliegue o operación persistente fue ejecutado al preparar estos documentos.
