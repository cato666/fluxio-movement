# S16 — Primera ventana controlada: procedimiento para aprobación

2026-10-12. Base c2fb54ed26e26861a54653c806d3dfdc36a8de1f. Complementa [integración EasyPanel](S16_EASYPANEL_INTEGRATION_PLAN.md), no la sustituye. **S16 BLOCKED / Pilot A NO-GO.** Preparación autorizada; ejecución NO autorizada. No se detuvieron servicios, consultaron datos reales, enviaron mensajes, activaron jobs ni ejecutaron backups.

## Hallazgo documental Kapso

Fuente primaria consultada 2026-10-12: [Delivery](https://docs.kapso.ai/docs/platform/webhooks/advanced). Sin HTTP 200, política predeterminada: tres intentos contando inicial, esperas de 10 y 40 segundos, agotados aproximadamente a los 50 segundos. Tras agotarse, entrega fallida; el panel muestra fallos. Pausa automática puede desactivar webhook y marcar pendientes fallidos. No se documenta aquí replay universal de fallidos al reactivar. Orden por conversación tiene timeout de 30 segundos. Buffer de 1–60 segundos es batching, NO cola duradera de mantenimiento.

No extrapolar política Meta de siete días al webhook Kapso. [Overview](https://docs.kapso.ai/docs/platform/webhooks/overview) distingue tipos Kapso/Meta; Gastón debe confirmar tipo/configuración/max_attempts reales. No modificar estos valores ahora. Retención de datos o panel con historial no equivale a reentrega garantizada.

**Conclusión:** HTTP 503 por sí solo no evita pérdidas durante una pausa de varios minutos. No desactivar webhook como supuesto mecanismo de conservación. No prometer orden total o ausencia de pérdida basándose en retries.

## Inventario de escritores y evidencia exigida

| Proceso del candidato | Escrituras | Drenaje / comprobación |
| --- | --- | --- |
| API FastAPI, TODAS las réplicas | Bitácora, fotos/audio temporales, cuotas/reservas, login/administración, shares, revisiones y anotaciones | Cerrar ingress y accesos internos a nuevas peticiones; esperar requests activas cero, no solo HTTP 202 terminado |
| BackgroundTasks dentro de API | _process_analysis: original/annotated/analysis/temp, progreso, reservas, resultados y observaciones | analyses PENDING/PROCESSING=0; procesos FFmpeg/analyzer y tareas activas cero; requests cero no demuestra fin del trabajo |
| API webhook Kapso | Inbox cifrada/usage y link-challenges | ACK solo tras commit; aislar entradas mediante mecanismo probado antes de interrumpir API |
| Worker WhatsApp, TODAS las réplicas | Inbox/runtime, training, conversation, media, usage/reservas, outbox y cleanup | PROCESSING/SENDING cero y ausencia de trabajo activo; PENDING puede conservarse en backup |
| Arranque API | Alembic, seed opt-in, recuperación de análisis interrumpidos | Misma imagen/revisión; seed off; startup marca análisis pendientes/interrumpidos FAILED: nunca detener con trabajo activo |
| Operadores/scripts/jobs externos | Migraciones/seed/SQL/limpieza/subidas/procesos video adicionales | Gastón enumera y suspende todos; no deducibles del repositorio |
| PostgreSQL y runner | DB mantiene motor; runner SELECT/dump, nuevos archivos privados de staging y R2 | DB NO se detiene; runner sin DML, fuentes RO; no montar PGDATA |

Inventario real pendiente: rellenar servicio API ___, réplicas ___, worker ___, DB ___, jobs ___, volumen/ruta medios ___, proxy/reglas ___, SHA/digest API-worker ___, head SQL ___, política de stop/grace ___ y owner de cada escritor ___. Sin completar inventario, ABORTAR. Compose proporciona referencia, no identidad real.

No existe flag drain/no-new-claims ni handler de parada ordenada específico del worker. Su bucle toma nuevo trabajo tras cada ciclo. SIGTERM/Stop de EasyPanel no acredita finalización segura. Si existe backlog elegible o envío activo y no se puede demostrar pausa entre trabajos, NO forzar kill ni vaciar cola consumiendo proveedores. Se requiere decisión posterior sobre coordinación de drenaje; no se implementa aquí. PENDING de reviews humanos no significa tarea automática activa.

## Evitar pérdidas: alternativas y decisión previa

A. Primera ventana antes de incorporar atletas: recomendar periodo acordado sin mensajes de prueba, backlog elegible cero y cero operaciones activas, con conciliación de eventos incluidos estados de entrega. Reduce exposición pero NO garantiza cero eventos imprevistos. Solo autorizar ejecución si además hay recuperación probada para cualquier llegada inesperada.

B. Mantener recepción duradera independiente de DB/media respaldados: relay cifrado validando firma, conservando bytes/headers/IDs antes de ACK, replay idempotente/ordenado y retención controlada. Soluciona disponibilidad si diseñado y probado, pero es infraestructura/implementación nueva fuera de esta preparación. Requiere aprobación separada de privacidad/costo/seguridad y pruebas; no está disponible actualmente.

C. Soporte/configuración Kapso que garantice conservación y replay de TODOS los fallidos durante la ventana: obtener contrato específico y probar en canal autorizado con datos sintéticos, IDs estables y medios recuperables. No asumir que reactivar recupera entregas fallidas. Cambiar max_attempts o buffer sin esa evidencia no satisface el requisito.

Seleccionar B o C antes de la ventana con WhatsApp expuesto. Si no es posible, solicitar aceptación explícita de interrupción y conciliación manual para ensayo sin atletas; no etiquetar esa excepción como garantía loss-free ni habilitar piloto. No pedir al usuario reenviar mensajes indiscriminadamente: nuevas IDs pueden duplicar registros y cargos.

## Duración máxima propuesta y abortos

Propuesta pendiente de aprobación: **20 minutos máximo desde cerrar ingress hasta reabrirlo**, repartidos hasta 5 drenaje, 10 backup completo y 5 reactivación/comprobación. Restore aislado ocurre DESPUÉS y no prolonga mantenimiento. Marker válido solo durante captura, <=30 minutos; no basta para ampliar límite operacional. Medir tamaño/bandwidth y tiempo en rehearsal para acreditar margen. Defaults del runner (comando 600s, alerta job 1800s) no imponen timeout end-to-end de 10 minutos: vigilancia y cancelación externa son responsabilidad de Gastón.

A los 15 minutos sin backup finalizado, cancelar solo el job backup por mecanismo probado, esperar salida/cierre conexiones/lock; preservar INCOMPLETE y posible objeto incierto. Reservar cinco minutos para reactivar. No matar escritores para cumplir reloj. Si cancelación o arranque no terminan antes del máximo, incidente de mantenimiento excedido, informar responsable y restaurar disponibilidad por procedimiento seguro, nunca declarar éxito ni borrar evidencia. No iniciar si no existe procedimiento de cancelación validado.

Abortar ANTES de detener API/worker si: inventario incompleto, entrada WhatsApp sin recuperación probada/decisión, trabajo activo que no drena en cinco minutos, claims nuevos, permisos/montajes/roles/secretos/versiones insuficientes, espacio/memoria insuficientes, restore sin destino aprobado o modificación de revisión SQL prevista. Durante captura: cliente DB externo, cambio de archivos, marker inválido/vencido, error dump/cifrado/R2/hash o timeout. No retry automático de objetos inciertos. Fallo de notificación se registra aparte; backup COMPLETE no prueba entrega de alerta ni habilita GO.

## Acciones exactas de Gastón en EasyPanel (futuras)

Los controles concretos y nombres reales del panel no han sido verificados. No inventar botones ni comandos de servicios; completar campos del inventario y confirmar capacidades antes de autorizar.

1. Registrar versiones y exportar SOLO configuración no secreta pertinente. Verificar misma imagen API/worker y revisión SQL: start-app.sh ejecuta alembic upgrade head al reiniciar. Si habría migración, abortar; este ensayo no autoriza migraciones. Confirmar ENABLE_DEMO_SEED=false y no release concurrente.
2. Si runner no está instalado, solicitar autorización independiente para servicio/rol/volumen/montajes/secrets y publicación previa necesaria. Esta ventana no implica deploy ni push. Mantener schedule deshabilitado; preparar run único.
3. Aplicar regla temporal de mantenimiento aprobada en proxy para TODOS los accesos/API internos; conservar HTTPS/ruta/firma webhook y recuperación elegida. Guardar regla anterior privadamente para revertir. No devolver 200 a eventos no persistidos. No registrar cuerpos, cookies o tokens.
4. Observar drenaje y los agregados siguientes desde consola SQL privada del servicio DB; cerrar conexión de inspección antes de backup. Verificar tareas y procesos, detener escritores solo cuando el drenaje se demuestre; confirmar que supervisores no los reinician. No usar restart/deploy como sustituto de pausa.
5. Detener/pausar worker y API y otros escritores con la operación de parada previamente validada de EasyPanel. DB, runner y watchdog permanecen disponibles. Comprobar TODAS las réplicas apagadas y fuentes inmóviles; detener monitores con clientes SQL persistentes.
6. En directorio controlado configurar maintenance.json del template con writers_paused=true SOLO tras verificación, scope exacto, SHA real de app y UTC vigentes. No cambiar fuente de medios ni elevar privilegios para resolver rechazo.
7. Ejecutar una única orden dentro del runner: python /opt/fluxio-backup/pilot_backup_runner.py run --kind pre-release. Configurar únicamente habilitaciones aprobadas para run/alerta, nunca BACKUP_SCHEDULE_ENABLED. Registrar backup ID, código/exit, key_id y SHA del recibo, no contenido de datos.
8. Esperar COMPLETE y proceso finalizado, o fallo/cancelación finalizados y lock liberado. No existe handshake de captura para reanudación anticipada. Invalidar marker y reponer supervisión/servicios con MISMAS imágenes, primero API saludable, después worker conforme a autorización de proveedores. Abrir ingress cuando webhook y controles estén disponibles, conciliando eventos retenidos con el método probado. No regenerar links/identidades o liberar costos inciertos.
9. Verificar pendientes/fallos/duplicados y salud; solo luego cerrar ventana. Iniciar restore aislado autorizado, fuera del mantenimiento, según apartado siguiente. S16 permanece BLOCKED hasta terminar todas las verificaciones obligatorias.

Durante el ensayo que permita replay/worker habrá posibilidad de IA/envíos reales. Se necesita autorización específica de límites y destinatario; si no se concede, mantener worker detenido y ensayar solo persistencia sin IA/envío, registrar etapa de reactivación completa BLOCKED, no fingir prueba integral.

## Comprobaciones agregadas antes/después (solo preparación SQL)

Gastón ejecutará con autorización, en conexión readonly corta de la DB identificada; no se ejecutaron aquí. Consultas sin payload/phone/token ni IDs personales. Cerrar sesión antes del runner (su guarda rechaza todos los demás clientes, incluso readonly).

```sql
BEGIN READ ONLY;
SELECT state, count(*) FROM whatsapp_inbox GROUP BY state ORDER BY state;
SELECT state, count(*) FROM whatsapp_outbox GROUP BY state ORDER BY state;
SELECT count(*) AS active_analyses FROM analyses WHERE status IN ('PENDING','PROCESSING');
SELECT count(*) AS active_training_ai FROM training_ai_usage WHERE status='RUNNING';
SELECT count(*) AS active_reasoning FROM ai_reasoning_runs WHERE status='RUNNING';
SELECT count(*) AS duplicate_inbox_groups FROM
 (SELECT provider, provider_message_id FROM whatsapp_inbox
  GROUP BY provider, provider_message_id HAVING count(*)>1) q;
SELECT count(*) AS duplicate_outbox_groups FROM
 (SELECT dedupe_key FROM whatsapp_outbox GROUP BY dedupe_key HAVING count(*)>1) q;
SELECT count(*) AS other_clients FROM pg_stat_activity
 WHERE datname=current_database() AND pid<>pg_backend_pid()
 AND backend_type='client backend';
COMMIT;
```

Counts no sustituyen drenaje físico ni detectan duplicados semánticos con IDs diferentes. Diferencias legítimas por transiciones se concilian por evento estable en evidencia PRIVADA del operador: eventos Kapso del intervalo deben estar persistidos o justificados; uno por mensaje recibido, una acción outbox por dedupe_key. No publicar esos IDs en reportes. Revisar FAILED/EXPIRED/PROCESSING y SENDING/UNCERTAIN, reservas inciertas/402 y secuencia de fragmentos sin reenvío automático. Verificar propuestas/Guardar no duplican sesiones, manualmente con datos sintéticos autorizados; no consumir IA solo para vaciar backlog. No interpretar PENDING que permanece por presupuesto/TTL como pérdida sin análisis.

## Restore aislado y evidencia de cierre

Autorizar conjunto exacto, destino privado cifrado nuevo, recursos/RTO y retención de datos. Descargar con reader aprobado, SHA y key_id del recibo, recuperar clave desde KeePassXC, DB vacía movement_restore_*, storage nuevo y BACKUP_RESTORE_ISOLATED_CONFIRMED=true. Ejecutar comando de [plan existente](S16_EASYPANEL_INTEGRATION_PLAN.md). No producir seed/upgrade ni activar proveedores. Misma imagen app y rutas lógicas originales; preparar claves del producto aparte. Medir custodia/descarga/descifrado/DB/files/arranque y verificar fotos/videos/reviews/notas/usuarios/constraints/privacidad. No restore a producción, no cutover ni limpieza.

Evidencia: cronología sanitizada, duración por etapa, inventario real, pausa demostrada, receipt COMPLETE/SHA/key_id, integridad y app restaurada, conciliación cero faltantes/duplicados, alerta recibida. Fallos de canal, replay, drain o restore son BLOCKED/FAIL y no excepción tácita.

## Aprobaciones requeridas antes de ejecutar

- Gastón confirma inventario y mecanismo de parada/drenaje/proxy/cancelación; selecciona recuperación de entradas B/C o excepción explícita para ensayo sin atletas.
- Autorizar fecha/hora, máximo 20 minutos propuesto, servicios identificados, pausa/reanudación MISMA versión y regla temporal reversible.
- Autorizar run único de respaldo representativo a bucket aprobado y restauración en destino aislado especificado; no borrado, no scheduler.
- Autorizar, por separado, una alerta Telegram y cualquier prueba/replay con potencial IA/WhatsApp, teléfono sintético, máximos de mensajes/llamadas/USD. No hay autorización de consumo en esta entrega.

**Estado:** revisión estática y consulta documental PASS; inventario real, drenaje, reentrega efectiva, mantenimiento, backup/restore y conciliación reales BLOCKED/NOT RUN. Suites SKIPPED: solo documentación, sin cambio funcional ni necesidad de repetir sintéticos aprobados. NO-GO conservado. Commit de este procedimiento: git log -1 -- docs/pilot-v1/S16_FIRST_CONTROLLED_WINDOW.md.
