# S16 — configuración operativa final preparada, no activada

Fecha: 2026-10-12, America/Santiago. Base 3f8a408da61c005ed4dc06cb1f480b76abccc9c8. Gastón administra EasyPanel; Codex prepara/testea y no aplica infraestructura. **S16 BLOCKED / Pilot A NO-GO.** Recuperación KeePassXC sintética y Telegram manual recibido conservan PASS; no se repiten.

## 1. Variables exactas y estado del contrato

| Variable | Uso / valor sin secretos | Estado real |
|---|---|---|
| R2_ENDPOINT | Endpoint HTTPS privado S3 del account autorizado | Contrato de ensayos R2 validado; transporte del adaptador desplegable aún pendiente. |
| R2_BUCKET | fluxio-movement-backups | Mismo contrato; no lo usa app.main ni Compose automáticamente. |
| R2_ACCESS_KEY_ID | Referencia privada de identidad writer limitada al bucket | Secreto; no imprimir ni guardar en Git. |
| R2_SECRET_ACCESS_KEY | Secreto privado de esa identidad | Secreto; reader de restore separado debe usar otro perfil con estos mismos nombres. |
| R2_REGION | auto | Firma S3 del transporte pendiente de integrar. |
| TELEGRAM_BOT_TOKEN | Bot privado autorizado | Consumida por pilot_telegram_alerts.py. |
| TELEGRAM_CHAT_ID | Chat privado confirmado del responsable | Consumida; no imprimir en informes. |
| TELEGRAM_ALERTS_ENABLED | false hasta activación autorizada | Consumida; habilitar flag no reemplaza autorización requerida por el callback. |
| TELEGRAM_ALERT_TIMEOUT_SECONDS | 10, rango 1–30 | Consumida. |
| TELEGRAM_ALERT_MIN_INTERVAL_SECONDS | 60, rango 1–86400 | Consumida; estado persistente compartido. |
| TELEGRAM_ALERT_DAILY_LIMIT | 20, rango 1–100 | Consumida; cuenta intentos físicos, incluidos inciertos, por día UTC. |
| DATABASE_URL | SQLAlchemy de API/worker existente, privado | Consumida por app.database; no pasar directamente dialecto postgresql+psycopg a pg_dump. Collector usará conexión libpq privada compatible y rol autorizado. |
| STORAGE_PATH | /data/storage en Compose; verificar mount real | Consumida por API/worker; origen del inventario, no snapshot coherente por sí solo. |

**AES actual no tiene variable de entorno implementada.** configured_run llama adapter.recover_backup_key(), que devuelve bytes raw de longitud 32. No hay BACKUP_AES_KEY, KEY_VERSION ni loader de Base64 activos para el respaldo. Propuesta de contrato para implementar en el adaptador, **todavía no consumida**:

- BACKUP_AES_KEY_FILE: path absoluto de secret-file binario protegido, fuera del repo/logs/recibos y separado del destino R2.
- BACKUP_AES_KEY_ID: versión no secreta fijada al manifiesto. Versión sintética recuperada: pilot-s16-synthetic-eb25e70ccc31-k1; no asumir que está autorizada para datos productivos.

No pegar bytes o representación textual de la clave en Environment. Secret-file/runtime debe conservar exactamente los 32 bytes del adjunto recuperable en KeePassXC. No generar/reemplazar clave ni cambiar AAD/format: FXS16GCM1, nonce 12 y AAD fluxio-s16-synthetic-v1 para los objetos existentes. Registrar key_id en manifest externo; históricos no lo llevan embebido. Nuevos manifiestos con key_id automático son integración pendiente, no capacidad demostrada.

Configuración operacional es JSON privada vía --config, no variables mágicas: operational_adapter.path + sha256 aprobado, state_directory absoluto protegido, execution_enabled, scheduler_enabled, aprobación infraestructura, privacidad/least privilege y recuperación independiente. Todos los gates finales siguen sin aprobar. Cambiar bool no demuestra quiescencia, permiso o custodia. BACKUP_CONFIGURATION.example.json es plantilla, no runtime activo.

## 2. Guía de aplicación en EasyPanel por Gastón — no ejecutar ahora

1. Identificar servicio/candidato fijado de API, worker WhatsApp, PostgreSQL y futuro ejecutor de backups. No poner writer R2/AES/Telegram en API o worker deportivo si solo los necesita el job operacional. Montaje de storage de ese job con acceso mínimo de lectura; escritura solo en staging/recibos privados. Restore reader en perfil de recuperación separado.
2. Gastón configura los secretos mediante controles privados del runtime. Para AES, elegir mecanismo de secret-file/gestor que permita recuperabilidad independiente: soporte de mount/secret exacto de EasyPanel aún debe confirmarse, no prometer opción de panel no inspeccionada. Si requiere escribir/crear archivo o volumen, preparar acción y solicitar autorización. No aplicar una alternativa de clave en texto/env por conveniencia.
3. Aplicar variables Telegram con ENABLED=false y R2 en servicio correcto, y path/ID de clave propuestos solo cuando el adaptador esté implementado/probado. No colocar valores en Compose, .env.example, stdout, docker inspect Config.Env, capturas o GitHub. Mantener copia KeePassXC/external independiente.
4. Confirmar presencia/formato mediante reporte booleano sin valores; key length 32 y versión/manifest por ID. Verificar lectura del secret-file por usuario mínimo y SHA de código adaptador; no registrar hash del secreto. Gastón entrega evidencia redactada; la configuración no debe reiniciar servicios hasta autorización de aplicación/ventana.
5. Mantener scheduler/envíos deshabilitados. No cambiar pipeline GitHub Actions: control manual/autorizar push vigente, ausencia de gates CI riesgo aceptado temporalmente, S15 sin modificar.

## 3. Servicios y volúmenes que deben inventariarse

**Compose local es referencia, no evidencia de nombres EasyPanel.**

| Referencia del candidato | Servicio/mount previsto | Datos necesarios y evidencia real pendiente |
|---|---|---|
| db | PostgreSQL 17.6; postgres_data:/var/lib/postgresql/data | Gastón identifica nombre/versión/database/schemas/roles/head. Backup lógico pg_dump completo, nunca tar en caliente de PGDATA. |
| app | API; app_storage:/data/storage | training-images, original (incluye original/whatsapp), annotated, analysis y otros paths persistentes identificados; tamaño/referencias. |
| whatsapp-worker | Mismo volumen app_storage y configuración DB/storage | Escritor de medios/outbox/capture; confirmar activo, heartbeat, trabajos en vuelo y cómo pausar sin retry UNCERTAIN/402. |
| Procesamiento video/jobs | Ejecutores reales, aún no inventariados | Pueden escribir archivos/DB; hay que incluirlos en pausa y drenaje. No asumir que parar worker WhatsApp pausa toda actividad. |
| Ejecutor backup/watchdog | Operación aún no instalada | Acceso de lectura DB/storage, staging con capacidad/cifrado, estado persistente privado, acceso limitado R2/clave/Telegram. Watchdog independiente del proceso que vigila. |

PGDATA completo lógico incluye las 29 tablas del candidato y otros schemas/datos reales que aparezcan en inventario, sin filtros accidentales. Roles/extensiones/config y versiones de claves necesarias deben registrarse por referencia privada. Inventariar temp antes de excluir; symlinks/rutas fuera del root abortan para revisión. No modificar/borrar archivos para reducir tamaño. Límites actuales de helper: 128 MiB en memoria; falta medir el tamaño representativo antes de confiar el piloto al job.

## 4. Plan representativo de respaldo/restauración

A. Gastón entrega inventario y manifest de versión API/worker, DB/head, rutas/tamaño y permisos. Codex verifica coherencia/capacidad y prepara adaptador concreto: collect_quiesced_snapshot, put_encrypted/get_encrypted, recover_backup_key y notify_operator Telegram. No se consideran implementados por esta documentación.

B. Aprobar conjunto individual, pausa de escritores/ingress/jobs y ventana, prefijo R2, custodio, presupuesto/retención, instancia aislada y manejo de datos de copia. Recolectar dump custom completo bajo quiescencia comprobada y snapshot de todos los archivos; no pasar storage vivo al seal_snapshot. Reanudar de forma controlada sin perder mensajes/orden ni mandar proveedores reales. No migrations como parte del backup.

C. Asociar clave autorizada/key_id recuperable en KeePassXC a manifiesto, cifrar AES-256-GCM, cargar por TLS y verificar download/hash/tag/manifiesto. Conjunto incompleto no actualiza last_success y no borra previos. Writer no sustituye reader separado; permisos del token limitados al bucket confirmados previamente por propietario.

D. Con permiso separado de datos/restore, abrir instancia nueva aislada, sin origen VPS disponible como dependencia de claves; recuperar adjunto/versiones desde KeePassXC/copia externa, descargar ese objeto concreto, restaurar DB/storage sin entrypoint de seed ni upgrade. Validar cada tabla/conteo/FK, imágenes/videos decodificables, usuarios activos/inactivos, notas, analyses/reviews/anotaciones, medios privados/sharing revoked/expired/consent y claves WhatsApp/sharing. Providers apagados; no OpenAI/Kapso.

E. Medir descarga, recuperación de claves, DB/storage, arranque/verificación y pérdidas posibles desde snapshot. RPO objetivo 24 h/RTO 4 h no son medición certificada. Ensayo sintético 2,42 s no sustituye el real. Gastón acepta evidencia y política de acceso/conservación de copia; no borrar objetos/volúmenes ni cutover automáticamente.

## 5. Activación controlada diario y pre-release

Preparado, **no listo para activar** mientras falten adaptador, capacidad, secretos runtime, recovery real de versiones de producto, restore representativo y alertas por job. Cron ejemplo comentado permanece inerte.

- Elegir hora diaria y America/Santiago; validar comportamiento ante cambio horario y evitar ejecuciones duplicadas mediante IDs/locks. Definir ventana de mantenimiento real diaria si el esquema de coherencia la necesita.
- Activar primero una ejecución manual autorizada con el adaptador final; aceptar backup/restore/alertas. Posteriormente pedir instalación del job diario y watchdog bajo autorización concreta, con state_directory persistente compartido. Ningún job aquí se instala.
- Antes de cada release: Gastón ejecuta pre-release del candidato fijado, conserva set/clave/manifiesto y valida completitud; fallo bloquea publicación bajo control manual. No modificar workflow para automatizar esta acción en esta etapa.
- Retención planifica siete daily completos + todos los pre-release del piloto; fecha inicio/fin pendiente. No DELETE/lifecycle automático; revisión y eliminación por aprobación individual.

Comandos preparados para entorno aprobado (sin destinos productivos inventados):

```text
python <release>/scripts/pilot_backup_ops.py run --config <json-privado-aprobado> --kind daily
python <release>/scripts/pilot_backup_ops.py run --config <json-privado-aprobado> --kind pre-release
python <release>/scripts/pilot_backup_ops.py health --state <recibos-privados>
python <release>/scripts/pilot_backup_ops.py retention --state <recibos-privados>
```

## 6. Cómo verificar alerta real de fallo

Telegram sendMessage manual ya recibido: PASS del canal, no garantía del job integrado. Probar fallo **controlado**, sin dañar DB/medios reales: collector de ensayo devuelve fallo fijo o objeto de prueba se marca incomplete por inyección, con evento BACKUP_FAILED y request ID durable. Callback retorna ACK de transporte/False, ledger conserva resultado redactado y backup falla por la causa simulada, nunca por excepción de Telegram.

Solicitar autorización de un único aviso operativo de fallo simulado al chat ya confirmado; mostrar texto fijo sin datos de atletas, tokens o excepciones. Gastón confirma recepción; registrar evento/request ID, resultado y confirmación humana. Después, pruebas separadas autorizadas de stale/missing/incomplete, worker/restore y proceso backup detenido **solo en entorno de ensayo**; watchdog independiente debe detectar falla aunque job no arranque. No crear alertas recursivas por fallo de Telegram. Rate-limited/busy/uncertain conserva fallo/evento para recuperación/escalado aprobados, sin pérdida silenciosa ni retries ciegos. No forzar reenvío borrando ledger.

## 7. Pruebas pendientes y permisos específicos

| Pendiente | Autorización/evidencia requerida |
|---|---|
| Identidad/mount/tamaño/runtime | Inventario redactado por Gastón, sin exigir SSH a Codex. |
| Adaptador runtime/clave/versión | Elegir mecanismo de secret-file, versión autorizada para datos reales y aprobar aplicación concreta. No nueva clave sin autorización. |
| Alerta integrada | Autorizar un mensaje de fallo simulado al chat confirmado, sin envío periódico; luego pauta/activación de alertas por separado. |
| Backup real | Aprobar servicios/ventana/conjunto/prefijo/costo y datos de copia definidos tras inventario, sin migrations. |
| Restore representativo | Aprobar ese set a DB/storage nuevos aislados, acceso y retención de copia; nunca sobre producción. |
| Diario/watchdog/pre-release | Autorizar instalación/activación final, hora/zona/ventana, operator/suplente y alarmas, solo después de aceptación. |
| Destrucción/rotación | Permisos separados; no borrar R2/volúmenes ni generar/reemplazar claves ahora. |

Compatibilidad PASS limitada: key_id k1 raw 32 bytes recuperado desde KeePassXC descifró conjunto histórico con tag y hashes correctos. Compatibilidad productiva sigue pendiente por versión/secret runtime, reader, claves de aplicación y set representativo; no dar PASS solo por nombres iguales de variables. S16 sigue BLOCKED y Pilot A NO-GO. Detenerse para revisión; sin operaciones reales.
