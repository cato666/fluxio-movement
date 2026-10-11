# S16 — prueba real Telegram recibida

Fecha: 2026-10-11, America/Santiago. **PASS del canal en una prueba manual:** un sendMessage autorizado aceptado HTTP 200 y recepción confirmada expresamente por el responsable. Evidencia redactada en S16_TELEGRAM_REAL_TEST_EVIDENCE.json, sin token, Chat ID, teléfono ni contenido privado. Ningún segundo envío ni retry. Esta confirmación no autoriza mensajes futuros.

**S16 sigue BLOCKED; Pilot A NO-GO.** Pendientes: recuperación real KeePassXC y copia externa, secreto runtime, backup/restore representativo EasyPanel, collector coherente/capacidad y activación autorizada de alertas/health watchdog. No se probaron aún alertas automáticas de backup/restore/worker ni fallos reales del monitor; no confundir recepción de prueba con operación continua validada. Scheduler y configuración de envíos permanecen deshabilitados; no push/deploy/CI ni escrituras al workspace original. Solo evidencia local y documentación actualizadas.

---

## Histórico — reemplazado únicamente el pendiente de recepción del mensaje manual

# S16 — alertas operativas Telegram / preparación local

Fecha: 2026-10-11. Telegram reemplaza Resend por decisión del propietario. Solo envío HTTPS sendMessage, sin webhooks. S16 BLOCKED hasta recepción real y recuperación/backup representativo. Sin Telegram real, push, deploy, CI/EasyPanel o cambios al workspace original.

## Implementación y resultados

scripts/pilot_telegram_alerts.py reutiliza AlertError, NoRedirect y save del adaptador existente. Resend permanece como utilidad histórica, no canal activo; no fallback ni correo automático. Códigos permitidos: BACKUP_FAILED/MISSING/STALE/INCOMPLETE, RESTORE_FAILED/COMPLETE, WORKER_DOWN/STALE, CRITICAL_ERROR, ALERT_DELIVERY_FAILED y BACKUP_ALERT_TEST. Texto fijo: código, fecha UTC e ID opaco de respaldo; sin nombres, teléfonos, chat ID visible, claves, entrenamientos, links privados o excepciones. Plain text sin parse_mode, previews deshabilitadas y protect_content; esto no impide capturas humanas.

31 pruebas nuevas PASS / cero FAIL/SKIPPED y 16 regresiones Resend PASS, siempre transportes simulados. Cobertura: autorización/flags, chat/key formato, respuesta correcta/incorrecta, duplicados/payload conflictivo, timeout/5xx/403/429 y JSON error_code, cooldown/límite diario/concurrencia/reinicio del estado, privacidad, callback seguro y descubrimiento de Chat ID privado/ambiguo/grupo/error. Se ejecuta run_job con fallo de respaldo y fallo de transporte: retorna INCOMPLETE y alert_delivery=FAILED, sin propagar excepción de Telegram. Sin pruebas reales ni repetición del restore R2 previamente aprobado; full Python/JS pendiente cuando corresponda al candidato antes del push, no sustituida por estos tests dirigidos.

Timeout configurable 1–30 s (default 10), intervalo mínimo default 60 s, máximo default 20 intentos diarios UTC, límites de seguridad configurables validando rangos. Estado/lock persistentes compartidos por todos los emisores: reservar antes de transporte, incluso envío incierto cuenta. HTTP 429 bloquea globalmente por max(intervalo,retry_after), sin retry automático. 5xx/timeout/respuesta ambigua → UNCERTAIN, sin replay; HTTP 4xx demostrados → REJECTED, sin reenvío automático. Telegram no recibe un idempotency key propio de Resend: deduplicación local con request ID durable, payload/timestamp fijo y reserva exclusiva. ACCEPTED exige ok=true, message_id y chat coincidente; no demuestra lectura del responsable.

notifier adapta al hook notify_operator del backup, retorna False ante fallos y nunca lanza hacia job. Identidad de evento backup estable por código/backup_id; para health sin backup_id, productor debe aportar request_id durable. Rate-limit/busy devuelve False para registrar fallo, no descarta silenciosamente ni genera alerta recursiva. Estado UNCERTAIN/REJECTED no se elimina para forzar reenvío. Watchdog debe conservar eventos rechazados y definir escalado/recuperación manual; no se instaló daemon ni vigilancia S13 de worker/restauración. Catálogo listo para productores existentes; integración runtime aún pendiente de autorización.

## Configuración privada

Crear fuera de Git, con permisos/ACL del usuario y después secrets del runtime:

```ini
TELEGRAM_BOT_TOKEN=<privado>
TELEGRAM_CHAT_ID=<chat privado autorizado>
TELEGRAM_ALERTS_ENABLED=false
TELEGRAM_ALERT_TIMEOUT_SECONDS=10
TELEGRAM_ALERT_MIN_INTERVAL_SECONDS=60
TELEGRAM_ALERT_DAILY_LIMIT=20
```

El adaptador lee variables del proceso, no carga dotenv automáticamente. No imprimir variables/env, URLs Telegram ni bodies de respuesta. El token forma parte del path de Bot API: no pegar URL completa en navegador/curl/logs. No usar .env.example con secretos ni incorporarlos a commits. Estado operativo privado persistente fuera del repo, compartido por alertadores, no Temp en producción; referencia aún pendiente. Authorized=false por defecto; flag true no reemplaza aprobación humana.

## Obtener Chat ID sin exponer token

Gastón crea/usa bot dedicado mediante BotFather si hace falta y abre chat privado con ese bot, pulsando Start o escribiendo /start. No terceros o grupos para el piloto de alertas personales. Preparar carpeta de secretos fuera del repo con ACL restringida.

Ejecutar MANUALMENTE scripts/pilot_telegram_chat_id.py --output <ruta-absoluta-a-archivo-nuevo-privado>. Pide token por getpass (entrada oculta) si no existe en variables del proceso; no escribir token como argumento. Hace una única consulta getUpdates timeout=0 sin offset ni configuración de webhooks, nunca sendMessage/deleteWebhook. Guarda TELEGRAM_CHAT_ID en archivo privado nuevo sin imprimir ID/token/nombre/mensaje. Si hay cero/múltiples chats o solo grupos, aborta sin escoger arbitrariamente. Confirmar que el chat seleccionado corresponde a Gastón; si bot compartido, resolver ambigüedad manualmente con evidencia privada. Si existe webhook previo, no eliminarlo ni cambiarlo para facilitar descubrimiento; usar bot dedicado y autorización separada. Método y límites oficiales: [Bot API](https://core.telegram.org/bots/api#getupdates), [sendMessage](https://core.telegram.org/bots/api#sendmessage), [FAQ](https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this).

No se ejecutó este helper contra Telegram; pruebas simulan su HTTP y validan redacción. os.chmod no sustituye ACL de Windows: usuario debe aplicar permisos privados al directorio/archivo.

## Prueba real pendiente y autorización

Mensaje propuesto:

```text
Fluxio Pilot A — BACKUP_ALERT_TEST
Prueba controlada; no es un fallo real.
Fecha UTC: <fecha fijada para la prueba>
ID operativo: no aplica
Revisar el estado operativo. Sin datos de atletas.
```

Entregar solo ruta privada de configuración y confirmar chat privado del responsable técnico. Verificar presencia/formato sin mostrar valores; preparar ID/timestamp durables y ledger con ACL. Solicitar autorización explícita: “Autorizar un único mensaje de prueba S16 al chat privado configurado y confirmado, sin retries ni activación periódica”. Habilitar flags solo en memoria para esa solicitud, no editar archivo ni activar jobs. Guardar respuesta operativa redactada; responsable confirma recepción. Fallo/UNCERTAIN detiene y no reutiliza la aceptación Resend anterior para Telegram.

## Pendientes conservados

Recepción Telegram real, custodia KeePassXC/copia externa y secret runtime, inventario EasyPanel por Gastón, collector y capacidad de medios, respaldo representativo/restauración y alertas automatizadas bajo autorización. Riesgo CI aceptado temporalmente/control manual vigente, S15 no implementada. Pilot NO-GO. Commit local de etapa: git log -1 -- scripts/pilot_telegram_alerts.py.
