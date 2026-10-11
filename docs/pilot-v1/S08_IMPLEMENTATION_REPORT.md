# S08 — Operación segura del outbox Kapso

Fecha: 2026-10-11. Rama: `codex/pilot-v1-stabilization`. Base autorizada: `59bfcbea1745f6de8392fbea99075e6a6885bc3f`.

**S08 lista para revisión técnica final local.** Commit funcional: `dfe2f870ba6e2aad277de478838cbea78d95fc3d`. El commit documental de entrega se identifica con `git log -1 --format=%H -- docs/pilot-v1/S08_IMPLEMENTATION_REPORT.md`; incorpora este reporte y el checklist sin cambiar el código ensayado. Exclusivamente S08; S09 no iniciada. No autoriza publicación ni consumo real.

## Clasificación de errores y reintentos

| Evidencia | Estado / acción |
|---|---|
| HTTP 402 | `FAILED`, código `insufficient_credits`; circuito durable de crédito bloqueado; ningún retry automático |
| HTTP 429 | `RETRY` hasta cinco intentos físicos totales; quinto rechazo termina en `FAILED` |
| DNS o conexión rechazada antes de enviar | Reintento seguro, mismo máximo de cinco; no asumir que cualquier timeout prueba ausencia de envío |
| Timeout ambiguo, HTTP 408/409/5xx, redirección POST, respuesta ilegible/sin ID, excepción desconocida | `UNCERTAIN`; nunca reenviar automáticamente |
| Configuración/URL/acciones inválidas antes de llamar o rechazo inequívoco no recuperable | `FAILED`; sin retry automático |
| Cuenta desactivada o identidad revocada | `CANCELLED`; payload purgado; sin proveedor |
| Cupo/presupuesto agotado | `FAILED`, `consumption_rejected`; sin proveedor; bitácora manual e historial conservan acceso |

El adaptador usa el status HTTP y no lee ni registra el cuerpo de error. HTTP 402 se normaliza conservadoramente como bloqueo de crédito, aunque su cuerpo no incluya un código reconocible. No se hacen consultas nuevas al proveedor para confirmar saldo. Los códigos guardados pertenecen a una lista fija; errores no reconocidos se reducen a `provider_error` o `send_result_unknown`.

Backoff de 429 y fallos preenvío seguros: `min(300, 10 * 2**attempts)` segundos: 20, 40, 80 y 160 antes de los siguientes intentos. Se respeta un `Retry-After` entero de segundos, acotado a 0–86400, si es mayor. Valores ausentes, inválidos o con fecha HTTP usan el backoff local. No hay reintentos del transporte HTTP ocultos ni retry de 402/UNCERTAIN. Un administrador puede autorizar un intento individual posterior a un 402; no se reinicia el contador acumulado.

## Estados, persistencia y orden

`PENDING/RETRY → SENDING` se confirma en PostgreSQL antes de llamar al proveedor. La lease dura dos minutos. Resultado conocido: `SENT`; recibos autenticados pueden avanzar a `DELIVERED/READ`. Un recibo FAILED tardío no degrada entrega o lectura confirmadas. Una lease vencida o nula en SENDING se transforma en `UNCERTAIN`, con `send_interrupted`, sin envío. Una interrupción dentro de send conserva SENDING y la reserva durable para esta recuperación conservadora.

Un advisory lock de sesión PostgreSQL serializa globalmente el emisor durante claim, commit durable, llamada y cierre del resultado. El mismo identificador protege autorizaciones administrativas mediante lock transaccional. Así un segundo worker no envía mientras el primero conoce/persiste un 402. El proceso no depende de memoria local; los bloqueos se liberan al cerrar la conexión. El piloto tiene un solo envío físico simultáneo; usa una conexión adicional mientras envía.

Los fragmentos se ordenan por fecha y dedupe_key, incluyendo empates de reloj. No se envía un sucesor si falta éxito del predecesor de la misma respuesta. También se mantiene el orden entre respuestas aún vigentes del atleta o de la conversación identificada mediante hash, incluyendo destinatarios no vinculados. Un fallo mantiene los siguientes fragmentos en PENDING, cifrados y visibles en el outbox; no los descarta ni salta. Otros atletas pueden continuar ante UNCERTAIN/429; un 402 detiene globalmente el emisor.

La retención no se amplía: vencimiento original de 23 horas para respuestas. PENDING/RETRY vencidos pasan a EXPIRED y pierden el payload aunque esté cerrado el circuito. La limpieza existente del worker purga también payloads de fallos al vencer, conservando metadata. Los fragmentos de la misma respuesta no saltan un predecessor vencido; una conversación nueva puede continuar cuando la respuesta anterior ya venció. Recuperación de contenido vencido se deniega; debe resolverse con el atleta mediante el flujo legítimo, nunca regenerando/reenviando silenciosamente la respuesta original.

## Circuito, consumo y alertas mínimas

Se reutilizan `AdminSetting` (`whatsapp_credit_block`) y `AdminAudit`; no hay tablas ni migración nuevas. El fallo 402 y el cierre del circuito se confirman juntos. Mientras esté bloqueado, el emisor no incrementa intentos ni crea reservas ni llama a send. El procesamiento de webhooks y las cuotas de entrada existentes siguen funcionando; este circuito bloquea el emisor, no sustituye la política de admisión ni deshabilita toda la aplicación.

S06 se conserva: cada intento físico utiliza `send-reservation:<outbox UUID>:<attempt>`. SENT confirma la reserva; un resultado fallido/ambiguo conserva UNCERTAIN y su costo/cuota. No se libera presupuesto suponiendo que rechazo de entrega implique ausencia de cargo. La recuperación no borra reservas, no reinicia intentos, no evita cupos diarios y no duplica el registro lógico `outbound:<UUID>`. La optimización de liberaciones pertenece a S09 y no se implementa aquí.

Se emiten señales constantes: `whatsapp_credit_blocked reason=insufficient_credits`, `whatsapp_outbox outcome=... reason=...`, `whatsapp_credit_clearance authorized=true`, `whatsapp_recovery authorized=true`. Sin teléfonos, texto, tokens, cookies, URLs privadas ni errores crudos. El estado durable y los conteos se consultan solo como administrador en `GET /api/admin/whatsapp/operations`. Retorna hasta 100 pendientes/fallos, UUID operacional, estado, razón fija, intentos, vencimiento y disponibilidad de payload; no devuelve contenido ni identidad del atleta. No se agrega dashboard, notificación externa ni infraestructura de observabilidad de S13. Conectar estas señales a alertas del destino queda pendiente de validación operacional autorizada.

## Recuperación manual individual

1. Un administrador activo consulta el endpoint de operaciones con sesión web legítima. Identifica FAILED/insufficient_credits, vencimiento y disponibilidad; no copia contenido privado a logs/reportes.
2. Verifica manualmente que el saldo del proveedor fue corregido y registra evidencia en el sistema operacional autorizado, fuera del payload del mensaje. No se ejecutó esta verificación real en S08. Su referencia es un UUID, sin URL, teléfono o texto libre.
3. Con Origin permitido, llama a `POST /api/admin/whatsapp/credit-clearances` con `request_id` UUID, `evidence_reference` UUID y `balance_verified: true`. Devuelve `clearance_id`; auditoría `WHATSAPP_CREDIT_CLEAR` registra actor, bloqueo y referencia. Falso, campos adicionales, rol inválido o administrador inactivo se rechazan. Repetir la misma autorización no reabre un bloqueo nuevo.
4. **Desbloquear el circuito permite continuar PENDING y RETRY seguros previamente admitidos; no reactiva FAILED ni UNCERTAIN.** Revisar la cola antes de esta autorización. No existe operación de reenvío masivo.
5. Para cada fallo 402 concreto, verifica evidencia del rechazo sin entrega y ausencia de ID de envío/recibos. Si el resultado es incierto, no autoriza: UNCERTAIN está excluido del mecanismo, incluso si un operador pretende forzarlo.
6. Llama individualmente a `POST /api/admin/whatsapp/outbox/{UUID}/recover` con `request_id`, `clearance_id` vigente, `evidence_reference` y `rejection_verified: true`. Se exigen FAILED/insufficient_credits, sin ID del proveedor, payload válido/no vencido, atleta activo e identidad vigente. El mensaje conserva UUID, dedupe_key, payload, vencimiento y contador; cambia a RETRY. La auditoría `WHATSAPP_RECOVERY` identifica al administrador y la evidencia mínima.
7. Repetir el mismo request devuelve already_authorized sin tocar la cola, incluso después del envío; usarlo con otra evidencia, actor, mensaje o clearance se rechaza. El worker vuelve a verificar identidad/estado/cuotas antes del proveedor. Revisar estado y recibos después; un nuevo 402 vuelve a bloquear globalmente y exige una autorización nueva. No modificar filas SQL ni resetear estados/reservas manualmente.

Estos endpoints heredan protección Origin/HTTPS y sesión/rol S07; no son webhooks ni se excluyen del middleware. Las verificaciones reales de saldo y entrega son responsabilidad del operador autorizado: los booleanos son su declaración auditada, no una comprobación automática del proveedor. La aplicación no garantiza idempotencia física del proveedor para resultados ambiguos; por eso impide su reenvío.

## Archivos y compatibilidad

- `app/whatsapp/provider.py`: evidencia preenvío y demora de retry opcionales, compatibles con constructores existentes.
- `app/whatsapp/kapso.py`: clasificación HTTP y resultados ambiguos sin cuerpo privado.
- `app/whatsapp/queue.py`: circuito, exclusión concurrente, orden, lease, payload y reserva S06.
- `app/whatsapp/operations.py`: tres endpoints administrativos y autorizaciones individuales auditadas.
- `app/whatsapp/runtime.py`: recibos monotónicos frente a fallos tardíos.
- `app/main.py`: registro del router administrativo.
- `tests/test_whatsapp_delivery_operations.py`: pruebas S08 con proveedor simulado y PostgreSQL real desechable.
- Este reporte y `GO_NO_GO_CHECKLIST.md`: evidencia y pendientes visibles.

Worker/cleanup, capture, identidad y servicios de cuotas fueron revisados y reutilizados, sin cambios funcionales en esos archivos. Contratos previos de web/chat, consentimiento S05 y cuotas S06 se mantienen; las rutas administrativas son aditivas. Head SQL permanece `0023_consumption_reservations`. No dependencias, servicios, red, puertos ni configuración comercial nuevos.

## Pruebas y resultados

| Verificación | Resultado y evidencia |
|---|---|
| Python completa del código final | **PASS: 749**, 231,27 s; cero fallos/errores/skipped, `s08-full-final.xml` |
| Casos dirigidos S08 del código final | **PASS: 46**, 14,41 s; `s08-targeted-final.xml` |
| Regresiones dirigidas WhatsApp/S02/S06 durante implementación | **PASS: 96**, 31,41 s; `s08-regression.xml`; la suite completa verifica además los cambios finales |
| JavaScript completa: nueve archivos tests/*.test.cjs | **PASS: 69**, 25,472 s; cero fallos/skipped; transportes y backend simulados |
| HTTP 402: sin retry, circuito durable, mensaje retenido y señal sin contenido | **PASS**, bloqueo detiene nuevos intentos/reservas/send |
| 429: backoff/Retry-After y máximo cinco intentos | **PASS**, cinco reservas conservadas y ninguna sexta llamada automática |
| Timeout preenvío demostrado, timeout ambiguo, 408/5xx y respuesta sin ID | **PASS**, no confundir timeout sin evidencia con ausencia de entrega |
| Reinicio durante send y lease vencida/nula | **PASS**, excepción de terminación simulada dentro del proveedor, SENDING/reserva durable y posterior UNCERTAIN sin replay |
| Workers concurrentes | **PASS**, dos conexiones/threads, un proveedor bloqueado y un solo envío físico simulado |
| Fragmentos: empate de fecha, fallo intermedio y recuperación ordenada | **PASS**, sucesores retenidos hasta recuperar el fragmento y secuencia ABCDE; UNCERTAIN/RETRY/FAILED no se saltan |
| Otras cuentas y conversación anónima | **PASS**, aislamiento y bloqueo de predecesor sin nuevas reservas; respuesta vencida no bloquea una conversación nueva |
| Webhook duplicado y recibos tardíos | **PASS**, sin outbox/consumo/envío adicional; READ no se degrada por FAILED/DELIVERED tardíos |
| Pendiente de cuenta desactivada | **PASS**, cancelación/purga y cero llamadas/reservas |
| Presupuesto agotado después de reautorización | **PASS**, consumo rechazado y cero llamadas al proveedor |
| Recuperación individual: saldo, evidencia, actor activo e idempotencia | **PASS**, servicio y despacho integrado con proveedor falso; ACL/Origin del API operacional y clearance probados por HTTP local |
| Rechazos de recuperación | **PASS**, UNCERTAIN, ID de proveedor, vencimiento, payload purgado, cuenta inactiva, revocación, anonimato, clearance inválido, evidencia falsa y request_id conflictivo |
| S02–S07, bitácora/IA texto/foto/audio/chat, coach y biomecánica soportada | **PASS**, regresiones incluidas en la suite completa; proveedores simulados, no certificado de calidad de IA real |
| Migraciones y contratos existentes | **PASS**, PostgreSQL tmpfs inicialmente vacío y cadena hasta head único `0023_consumption_reservations`; suite incluye roundtrip/check y contratos previos; sin migración S08 |
| Fuente ejecutada versus candidato | **PASS**, SHA-256 de 185 archivos, cero diferencias; `source-verification.json` |
| Selección, diff y patrones de secretos/artefactos locales | **PASS**, siete archivos funcionales/pruebas y dos documentales; diff --check limpio, scanner sin hallazgos; no garantía absoluta de detección de secretos |
| Workspace original | **PASS**, 153 huellas intactas y estado Git idéntico al baseline S01 |
| E2E integrado navegador/servidor de S05 | **BLOCKED**, no ejecutado; el gate continúa abierto |
| Proveedores reales, EasyPanel, costos externos de video y deploy | **SKIPPED / PENDIENTE**, sin autorización ni ejecución; no PASS |

Entorno: PostgreSQL 17.6, contenedor `fluxio-s05-db-20261010`, PGDATA tmpfs sin mounts persistentes; runner `fluxio-s05-tests-20261010`, imagen existente `fluxio-whatsapp-tests:phase2`. Red interna existente `fluxio-s01-validation-20261010`; ningún puerto publicado en runner ni red ampliada. Candidato montado read-only y copiado a `/tmp/s05`; fixtures exigen `TEST_DATABASE_RESET=1` y base exactamente `movement_test`. No se borraron contenedores, imágenes, volúmenes ni bases existentes. Se detienen únicamente estos dos contenedores de pruebas al terminar.

Comandos principales: `docker exec -w /tmp/s05 -e WEEKLY_RELEASE_PUBLIC_BASE_URL=https://fluxio-s08.invalid fluxio-s05-tests-20261010 pytest -q --tb=short --junitxml=/tmp/s08-full-final.xml`; dirigido: mismo runner con `tests/test_whatsapp_delivery_operations.py`; JavaScript: Node local incluido en runtime, `--test` sobre tests/*.test.cjs con NODE_PATH a las dependencias ya instaladas. `.invalid` es un origen sintético de fixtures.

Evidencia XML, resumen y comparación de fuente: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s08-validation-20261011/`. Capturas JavaScript simuladas: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s08-js-evidence-20261011/`, movidas fuera del candidato y conservadas. No se incorporan artefactos .impeccable.

Tres advertencias preexistentes: alias anyio BlockingPortal y on_event/lifespan; no se omitieron pruebas. En la primera ejecución dirigida hubo seis FAIL: cuatro assertions usaban un atributo inexistente de la reserva, una fixture usaba un atributo inexistente de usuario y una repetición de autorización conservaba el advisory lock. Se corrigieron fixtures/assertions y liberación transaccional del replay; las 46 pruebas finales y las 749 completas pasaron sin excluir casos. También se corrigió en revisión la clasificación conservadora de errores sin evidencia, la validación de ID/payload y el bloqueo permanente de conversaciones nuevas después del TTL. No se modificó código del workspace original ni se ajustaron cuotas/privacidad para lograr los resultados.

## Riesgos y cierre

- **BLOCKED: E2E integrado navegador/servidor S05**, no sustituido por TestClient ni interfaz con backend simulado.
- **PENDIENTE: reserva/control real de cómputo, almacenamiento y otros costos de video.**
- **PENDIENTE: paridad EasyPanel y validaciones reales del candidato**, TLS/Origin/proxy, commit/digest, esquema, worker y comportamiento actual del proveedor.
- Serializar el emisor es adecuado al piloto de 10–15 atletas; limita throughput y exige disponibilidad/pool de PostgreSQL. Validar operación en destino antes de publicar.
- Los fallos detienen fragmentos y respuestas vigentes de la conversación hasta recuperación o vencimiento; el TTL aprobado puede hacer imposible recuperar una respuesta antigua. El contenido no se retiene indefinidamente por razones operativas.
- El endpoint de operaciones tiene una ventana de 100 filas; conteos globales permiten detectar acumulación, pero no reemplaza auditoría/monitoreo de S13. No se acredita una alerta entregada a una persona.
- El circuito de crédito bloquea send; no impide que un atleta haga nuevas solicitudes legítimas dentro de S06. No se cambian cuotas ni privacidad para resolver el bloqueo.
- No se habilita recuperación de UNCERTAIN, fallos no 402, destinatarios anónimos/inactivos/desvinculados o mensajes vencidos. El saldo/evidencia requiere comprobación humana; no se ha certificado idempotencia externa ni costo real.

Recomiendo aceptar el cierre técnico local de S08 después de revisar el diff, estas pruebas y las restricciones de recuperación. El candidato contiene exclusivamente los siete archivos funcionales/pruebas enumerados; el commit de entrega añade este reporte y actualiza el checklist. Pilot v1.0 continúa **NO-GO** por los pendientes heredados y los demás gates sin certificar. No hubo push, merge, deploy, migración persistente, altas reales ni consumo OpenAI/Kapso real. Se detiene la etapa para revisión; **S09 no iniciada**.
