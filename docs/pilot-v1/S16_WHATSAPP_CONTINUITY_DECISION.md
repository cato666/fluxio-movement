# S16 — Decisión técnica de continuidad WhatsApp (para aprobación)

Fecha 2026-10-12. Base d2b62071fc7bbbad74bbd8572a33ae738782090f. **Propuesta, no implementación. S16 BLOCKED / Pilot A NO-GO.** Ventana no autorizada. Solo lectura de código y documentación pública, sin llamadas API autenticadas, datos reales ni infraestructura.

## Recomendación

A es el mínimo para ensayar manualmente un respaldo antes de incorporar atletas, aceptando expresamente que conciliación no garantiza recuperar cada evento. A no satisface continuidad durante respaldos diarios con WhatsApp obligatorio. Recomiendo B acotada: un único receptor HTTPS permanente con cola cifrada durable propia, pausa del consumidor y replay al inbox actual. Mantener URL estable evita un cambio de ruta en cada mantenimiento. No reescribir runtime, outbox o Backup Runner ni añadir Redis/Kafka/organizaciones. Aprobar diseño/retención/capacidad y pruebas antes de implementar. Independiente de PostgreSQL/volúmenes respaldados no significa independiente del VPS.

## Evidencia de Kapso y límites documentados

Consulta pública 2026-10-12, no inspección de cuenta:

- [Delivery](https://docs.kapso.ai/docs/platform/webhooks/advanced): default tres intentos incluido inicial, esperas 10/40s y agotamiento ~50s; pausa automática marca pendientes fallidos. Batching 1–60s no es cola de mantenimiento; orden puede ceder tras 30s. Reactivación no acredita replay de todos los fallidos.
- [List webhook deliveries](https://docs.kapso.ai/api/platform/v1/webhook-deliveries/list-webhook-deliveries): GET /platform/v1/webhook_deliveries, filtros status/webhook_id/errors_only/period (24h,7d,30d); páginas default20/max100 con cursores. Respuesta contiene metadatos de intento, no cuerpo firmado. No POST retry/replay documentado en esta referencia ni índice revisado. No usar period30d como garantía de retención.
- Dashboard: Delivery documenta consulta de fallos y reactivación. **Reenvío manual no confirmado** por fuentes revisadas: no afirmar que existe ni que sea imposible; pedir confirmación de soporte o evidencia sanitizada del panel y probar después de autorización. Tampoco se verificó acceso por plan.
- [List messages](https://docs.kapso.ai/api/platform/v1/messages/list-messages) permite consultar mensajes/contenido con cursores (20/max100), y [Get message](https://docs.kapso.ai/api/platform/v1/messages/get-message) consulta por WAMID. Facilitan conciliación, no recuperan automáticamente cuerpo/headers/firma original ni secuencia de acciones. Estado failed de mensaje no es estado failed de entrega webhook. Hay diferencia con la tabla de [WhatsApp data](https://docs.kapso.ai/docs/platform/whatsapp-data); verificar versión/plan antes de depender de contenido API.
- WhatsApp data documenta retención indefinida por defecto, configurable en proyectos pagos; log de mensajes 30 días o menor retención. Eliminaciones por política no recuperables. Confirmar política real, no extrapolar defaults.
- [Rate limits](https://docs.kapso.ai/api/rate-limits): ventana fija por minuto, Free/Legacy100, Pro1000, Platform2000, Enterprise4000 solicitudes por clave; 429/Retry-After. No son cuotas S06 ni autorización de gasto.
- [Get media URL](https://docs.kapso.ai/api/meta/whatsapp/media/get-media-url): URL vence en cinco minutos. Esto no define duración de disponibilidad del media_id. Conservar referencia y resolver URL nueva al consumir; probar disponibilidad durante ventana. Sin ella, no certificar cero pérdida de fotografía/audio por preservar solo JSON.

Conclusión documental PASS: default retries insuficientes; inspección de fallos e historial existen. Recuperación manual de entregas originales por API/dashboard **NOT VERIFIED/BLOCKED**. No invocar endpoints supuestos ni enviar un mensaje nuevo como si fuera replay del anterior.

## Comparación

| Criterio | A: manual sin atletas | B: receptor durable independiente |
| --- | --- | --- |
| No pérdida | Solo para datos ya persistidos y capturados con pausa real. No garantiza eventos durante caída; ausencia de atletas reduce riesgo | Para eventos válidos confirmados, conservación condicionada a commit durable y almacenamiento sano. No exactamente una vez ni cero pérdida ante caída del VPS/fallo proveedor |
| Backup Runner | Sin cambio: API/worker/otros escritores pausados, sin otros clientes SQL, medios inmóviles | Sin cambio de collector/guardas: receptor sigue vivo sin tocar DB/media fuente; consumidor detenido y sin conexiones SQL. Su volumen no integra el set coherente |
| Cambios | Procedimiento/inventario/conciliación; resolver drenaje existente. No introducir recuperación adhoc insegura | Receptor+cola cifrada, consumidor, control de pausa/drain, health/capacidad, replay y pruebas; reutilizar firma/normalización/inbox actuales |
| Complejidad/plazo | Baja documental, 0.5–1 día técnico tras inventario; drenaje puede añadir 1–2 días. No incluye esperas/operación autorizada | Media: 4–7 días técnicos para versión acotada local probada +1–2 de integración y ensayo autorizados; si media/RPO exigen almacenamiento externo, reestimar |
| Recuperación | Conciliar fallos y mensajes con IDs originales; soporte/replay no confirmado. Importar historial requeriría herramienta autenticada nueva aprobada | Entrega at-least-once a inbox; borrar/retirar solo tras ACK durable y política aprobada; timeout después del commit produce replay idempotente |
| Idempotencia/orden | Restricciones inbox/outbox ayudan con IDs iguales; reenvío humano con ID nuevo puede duplicar | Dedupe de entrega y mensaje/evento, HMAC índice; mismo ID con contenido distinto se pone en cuarentena. Cola por conversación y consumidor serial por conversación; no orden total de eventos aún no recibidos |
| Seguridad | Mantener datos y claves existentes; conciliación privada sin payloads en reportes | TLS, firma sobre bytes exactos antes de almacenar, AES-GCM clave propia/key_id/nonce único, secretos privados, solo ruta necesaria y replay autenticado |
| EasyPanel | Gastón pausa/reanuda todos los escritores, DB/runner activos; no asegura recepción WA | Servicio permanente independiente, volumen propio cifrado, proxy HTTPS estable; sin PGDATA/socket/admin/medios fuente; consumidor privado, pausa verificada |
| Riesgos | Llegadas imprevistas, orden alterado, medios expirados, claims durante drain, startup falla análisis, recuperación incompleta | Disco lleno/corrupto, key perdida, replay fuera de TTL, nueva superficie sensible, caída VPS/proxy, backlog y cuotas, transición inicial de ruta |

Estimaciones relativas, no compromiso calendario ni autorización de implementación/infraestructura. B requiere resolver también drenaje de API/video/worker; receptor no lo sustituye.

## A — uso limitado y aceptación

Solo antes de atletas activos y con teléfonos de ensayo informados. Confirmar todos los escritores/inventario, backlog elegible cero y tareas activas cero; cerrar nuevas escrituras, drenar y verificar parada. Mantener límite propuesto 20min y backup/restore del procedimiento existente. Nunca responder 200 para descartar eventos. No desactivar webhook esperando que actúe como buffer.

Registrar intervalo UTC y conciliar, privadamente, todas las páginas de entregas/mensajes del número autorizado frente a inbox/outbox; no consultar producción ahora. Si existen fallos no recuperados, abortar cierre y registrar incidente. No reconstruir firma o reutilizar credencial webhook para simular Kapso; recuperación desde historial necesitaría import autenticado con procedencia auditada, controles activos/cuotas y IDs originales. No está implementado. No reenviar UNCERTAIN ni liberar reservas de costo desconocido.

A puede validar coherencia del respaldo existente. No prueba continuidad durante ventana ni respalda datos que nunca entraron; aceptación de ensayo sin atletas no autoriza riesgo diario para atletas.

## B — contrato mínimo propuesto

1. Receptor siempre en la ruta pública estable. Verificar firma exacta y límites antes de aceptar; conservar bytes y headers indispensables cifrados (no Authorization/cookies). Metadatos mínimos opacos/hashes de conversación; no teléfonos en índices/logs. Validez de firma no autoriza IA, publicación o envío.
2. Cola local propuesta SQLite en volumen exclusivo, una réplica escritora, transacción y fsync/synchronous FULL sobre filesystem compatible. ACK200 solamente tras commit durable; confirmar duplicado existente sin crear otro. Si key/disco/firma falla, no ACK. Comprobar recuperación tras crash y saturación; fsync y volumen se deben verificar en destino, no prometer durabilidad absoluta. Nunca cola en tmpfs ni disco efímero.
3. Clave del receptor separada de clave de backup, custodia independiente y versión; requiere aprobación para generarla. Cifrado de payload no cifra WAL/índices automáticamente: no almacenar allí datos privados en claro; volumen cifrado para metadatos y artefactos. Retención/backlog máximo pendiente de aprobación; no borrado masivo automático.
4. Consumidor privado con pausa persistente/no-new-claims y handshake de trabajos terminados. En mantenimiento continúa receptor, consumidor sin SQL ni escrituras a storage fuente; worker y API drenados/parados; runner no monta ni respalda cola viva. Receptor sin credenciales DB o medios fuente.
5. Replay conserva cuerpo/firma/IDs originales por vía privada autenticada restringida (no nuevo acceso público ni bypass de S07); backend valida firma e identidad/actividad y hace commit-before-ACK. No fabricar webhook con firma nueva ni exponer secreto al operador. Timestamp actual del receptor no reemplaza timestamp original: inbox admite edad <=7d, payload dura24h/outbox23h tras ingreso. Definir ventana de replay aprobada que respete privacidad/conversación/medios; cuarentena si excedida, nunca override silencioso.
6. Consumidor envía solo a inbox y no a Kapso/OpenAI; worker actual controla interpretación/transcripción/envío, cuotas/idempotencia S02–S08. Preservar acciones/batches y orden por conversación de lo recibido; durante catch-up no adelantar nuevos mensajes sobre backlog de esa conversación. Eventos originalmente fuera de orden siguen necesitando análisis, no prometer corregirlos todos por timestamp.
7. Fotos/audio: conservar media_id, no URL temporal. Antes de certificar B validar renovación/descarga y disponibilidad real del media para ventana máxima. Si no garantizable, ampliar diseño con spool cifrado de medios independiente y recuperación interna aprobada: exige lecturas proveedor/permisos/costos/privacidad y reestimación, nunca montar fuente respaldada para almacenar durante pausa.
8. Cola contiene eventos posteriores al snapshot y no pertenece al backup DB/media; requiere estrategia propia de recuperación/retención. Si mismo VPS se pierde después del ACK, volumen local puede perderse: para cubrir ese riesgo se necesita réplica durable externa ANTES del ACK o RPO explícito aceptado. No usar token/bucket backups como cola automáticamente. Restore de DB antigua puede haber perdido outbox SENT mientras Kapso ya entregó: no replay masivo histórico; reconciliar entregas/costos antes de reactivar. Backup Runner no puede resolver ese problema por sí solo.
9. Transición inicial de routing bajo aprobación: verificar receptor antes de cambiar, mantener ingress original durante propagación y persistir/deduplicar ambos caminos; no pausar fuente hasta confirmar ruta efectiva y backlog. No cambiar URL por cada backup. Fuera de ventana mantiene solo latencia de cola, no intervención del atleta.

## Pruebas/gates antes de habilitar B

Locales aisladas sin proveedores: firma inválida/cuerpo límite; crash antes/después commit y antes ACK; fsync/restart/key ausente/disco lleno; duplicados/batches/colisión de ID; pausa y drain concurrentes; dump mientras receptor escribe volumen independiente; timeout backend tras commit; orden/backlog; inactive/revoked/consentimiento; TTL y presupuesto; log sin secretos; restauración cola y conciliación con outbox UNCERTAIN. No debilitar guarda other_database_clients para permitir un consumidor activo.

Destino autorizado: permisos/volumen/cifrado/egress/health/capacidad/alertas; texto/foto/audio y replay realmente conservados, límites de costos, transición proxy sin hueco, pausa y snapshot coherentes, restore aislado con conciliación. Independencia de ciclo de vida demostrada: detener API/worker/runner no detiene receptor. No activar scheduler antes de probar coordinación completa.

## Decisión solicitada

Recomiendo aprobar B como incremento de seguridad/operación acotado para WhatsApp obligatorio, manteniendo A como ensayo opcional previo sin atletas y con sus riesgos expresamente aceptados. Primero decidir destino durable/RPO (volumen separado vs persistencia externa), custodia/retención/capacidad de cola y alcance de conservación de medios; luego autorizar implementación local y pruebas. No autorizar mantenimiento real hasta gates. Confirmación de soporte Kapso sobre replay puede simplificar conciliación, no elimina necesidad de continuidad y drain con evidencia.

Esta entrega: revisión documental/estática PASS; suites SKIPPED porque ningún código modificado; API/dashboard de cuenta, receptor, failover, mantenimiento y pruebas operativas NOT RUN/BLOCKED. S16 y Pilot A NO-GO. Ningún servicio creado, deploy/push/migración/envío/llamada facturable o scheduler. Commit local documental: git log -1 -- docs/pilot-v1/S16_WHATSAPP_CONTINUITY_DECISION.md.
