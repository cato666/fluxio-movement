# Kapso Sandbox: registro de validación

Estado global: **PENDIENTE DE CONFIGURACIÓN Y TRÁFICO REAL**. Este documento no certifica Kapso Sandbox.
Fecha de preparación: 2026-10-03, America/Santiago. Revisión auditada: `f0b1acc`.
Alcance: validación de fases 2/3; sin nuevas funcionalidades, merge ni deploy.

## Configuración utilizada

Auditoría local y tests aislados, sin credenciales reales, sin teléfono de prueba ni origen HTTPS confirmados. No se leyeron ni exportaron secretos del entorno desplegado. Imagen de tests existente `fluxio-whatsapp-tests:phase2`; PostgreSQL de tests separado de producción. El canal real no fue habilitado.

Variables previstas: WHATSAPP_PROVIDER=kapso, WHATSAPP_ENABLED=true exclusivamente en Sandbox, KAPSO_API_KEY, KAPSO_WEBHOOK_SECRET, KAPSO_PHONE_NUMBER_ID, PUBLIC_BASE_URL, PHONE_ENCRYPTION_KEY y PHONE_HASH_KEY, con valores confidenciales omitidos. El runtime actual requiere **WHATSAPP_ENCRYPTION_KEY**; PHONE_ENCRYPTION_KEY y PUBLIC_BASE_URL no son leídos. Ver checklist para configuración efectiva y discrepancia.

## Auditoría del webhook

| Control | Evidencia local | Validación real |
|---|---|---|
| POST /webhooks/whatsapp/kapso | Ruta existente y test de contrato | Pendiente de origen HTTPS |
| Raw body | Stream de bytes; máximo 262144 bytes | Pendiente de proxy real |
| Firma | X-Webhook-Signature, HMAC SHA-256, compare_digest | Pendiente de entrega Kapso |
| Header de evento | Concordancia con dirección/status firmados; formatos directos/batch | Pendiente de payload real |
| Deduplicación | Unique(provider, provider_message_id), ON CONFLICT | Pendiente de retransmisión real |
| Inbox persistente | Commit antes del ACK; cifrado y expiración | Pendiente de consulta nueva en Sandbox |
| ACK rápido | Sin IA/envío en petición | No se midió latencia real |
| Procesamiento posterior | Worker independiente, leases y locks PostgreSQL | Worker Sandbox no confirmado |
| Outbox | Dedupe transaccional y UNCERTAIN sin retry ciego | Pendiente de respuesta real |

## Pruebas realizadas

- Revisión de routes, adapter Kapso, seguridad, identidad, runtime, captura, media, worker, modelos y accounting.
- Contraste con [Sandbox oficial](https://docs.kapso.ai/docs/how-to/whatsapp/use-sandbox-for-testing), [webhooks](https://docs.kapso.ai/docs/platform/webhooks/overview) y [firmas](https://docs.kapso.ai/docs/platform/webhooks/security).
- Tests específicos: **51/51**, incluyendo firma/límite, duplicados, identidad, outbox, media, confirmación y preservación de contratos OpenAPI/migraciones. Usan proveedores/IA controlados; no prueban credenciales reales.
- JavaScript: **60/60** en esta preparación.
- Python completo: **246/246** en esta preparación, 150.48 s; tres avisos de deprecación existentes. Coincide con la baseline aprobada.
- E2E web: **6 flujos aprobados** en la baseline; se verificó `results/whatsapp/phase3-e2e.log` (texto, foto, audio, solicitud de revisión, revisión coach y feedback atleta). No reejecutados aquí. **E2E real Kapso: 0**, pendiente.
- No se agregaron tests nuevos: no se cambió implementación. Se reejecutaron los controles existentes relevantes.

Incidencia de entorno: el primer intento con la imagen antigua de bitácora no tenía `cryptography` y no pudo importar conftest. Se corrigió usando la imagen WhatsApp existente, sin instalar dependencias ni reconstruir Docker.

## Discrepancias y correcciones necesarias

1. **Variables:** la lista solicitada no configura por sí sola Vault. Debe usarse el nombre vigente WHATSAPP_ENCRYPTION_KEY; documentado en .env.example con placeholders. Cambiar/añadir alias sería una corrección de código pendiente, no realizada en esta fase de preparación.
2. **Ayuda inicial:** sin vincular devuelve instrucciones de vinculación, no el menú solicitado. ConversationState pertenece a un athlete_id y no existe para anónimos. Después de vincular, la ayuda disponible ofrece registro, nota y Bitácora web; no promete “ver tu semana”. Debe acordarse el criterio antes de marcar aprobado. No implementar consulta semanal ni anunciarla como disponible.
3. **Accepted:** el adapter entiende received/sent/delivered/read/failed. Una aceptación de send devuelve ID y estado SENT; un evento `accepted` no está normalizado. Comprobar qué entrega realmente Sandbox antes de decidir una corrección.
4. **Identidad:** los contratos recientes de Kapso pueden entregar identidad sin teléfono; el adapter actual necesita phone para resolver al atleta. BSUID-only debe registrarse como incompatibilidad si se observa, sin inventar phone.
5. **MIME/audio:** la validación usa el MIME descargado y decodificación existente. MIME parametrizado o URLs de descarga distintas deben contrastarse con bytes reales. No se relajan allowlists ni límites por anticipación.
6. **Texto breve:** “Hoy hice 4 rondas en 12 minutos” puede requerir aclaraciones de ejercicios en el flujo existente. No inferir información no suministrada para forzar la prueba.

## Matriz de pruebas reales

Todos los casos siguientes están **NO EJECUTADOS**. No hay evidencia real de persistencia o idempotencia todavía.

| Caso | Evidencia pendiente |
|---|---|
| Alcance/firma inválida | HTTP 401, cero inbox, esquema HTTPS real |
| Ayuda sin IA | Recepción Kapso, inbox DONE, respuesta WhatsApp, cero IA |
| Vinculación | API autenticada, código consumido, cifrado/hash/verified_at |
| Ayuda con identidad | IdentityResolver, conversation_state IDLE, outbox SENT |
| REGISTER_WORKOUT texto | Propuesta, cero sesiones antes de confirmar |
| Guardar | Una sesión por SQL nuevo y Bitácora web |
| Replay/doble confirmación/botón antiguo | Deltas cero, un inbox y respuesta por mensaje lógico |
| Foto | MIME/bytes/límites/storage privado, propuesta y sesión confirmada |
| Voz | Container/codec reales, FFmpeg, transcripción, propuesta y confirmación |
| Media inválida/inexistente/transcripción fallida | Respuesta segura y ausencia de persistencia parcial |
| No vinculado/código expirado | Ninguna reasignación ni sesión |
| Timeout outbound | UNCERTAIN, no retransmisión ciega |
| Delivery/read/failed | Estados normalizados; cero lógica de conversación |
| Costos | Inbound/outbound/IA/tokens/media; costo ausente UNKNOWN |

## Payloads normalizados y fixture frente a real

No se recibieron payloads de Kapso Sandbox; no hay muestras reales normalizadas ni diferencias observadas. La forma local esperada es InboundWhatsAppMessage: provider_message_id, phone, message_type, timestamp, text, media_reference, media_mime, action_id, event. En el reporte final redactar phone, texto personal, IDs externos, referencia y acciones; registrar solo tipo/evento/forma/estado y IDs internos necesarios para correlación. No almacenar originales ni firmas en Git.

OGG/Opus generado por fixture no certifica la nota de voz real. Fotos/IA mock no certifican MIME ni calidad de extracción de una pizarra WhatsApp. Idempotencia bajo fixture no demuestra que el replay real use el mismo ID.

## Evidencia a completar tras configurar

Por caso: hora, commit/entorno, evento redactado, HTTP y latencia, inbox/outbox internos, connection SQL nueva, conteos antes/después, fila de estado, sesión en Bitácora y consumo. Usar las consultas de KAPSO_SANDBOX_CHECKLIST.md; nunca seleccionar phone, payloads cifrados, códigos o secretos para anexarlos.

Persistencia: pendiente. Idempotencia: pendiente. Logs reales sin teléfonos: pendiente. Costos reales: UNKNOWN/no medidos. `results/whatsapp/phase3-alembic.log` confirma la baseline `0020_whatsapp_capture (head)`; contrato OpenAPI preservado por tests locales, sin cambios a API. Esto no acredita la versión del entorno Sandbox aún desconocido.

## Riesgos restantes y siguiente paso

Faltan dominio HTTPS, configuración de secretos en el entorno, worker activo, sesión Sandbox activada y teléfono autorizado. La activación Sandbox y la vinculación Fluxio son pasos diferentes. Confirmar proxy TLS y discrepancias de ayuda/variables antes de aprobar. No dar por cerrada esta fase con resultados locales; completarla únicamente tras tráfico real y evidencia PostgreSQL nueva. No se hizo merge, deploy ni envío de mensajes.


## Arranque local autorizado, 2026-10-03

Se levantó `fluxio-kapso-local` con imagen existente, código montado, PostgreSQL y storage exclusivos. API en http://localhost:8001; worker independiente activo; health 200; Alembic 0020_whatsapp_capture; Vault válido. No se hizo merge ni deploy. La aplicación anterior en localhost:8000 permanece independiente.

Se generó PHONE_HASH_KEY faltante sin mostrar su valor. La clave de cifrado proporcionada no era válida; se creó una Fernet exclusiva en `.env.kapso-local` (ignorado por Git), sin sustituir la clave de otros entornos. No borrar ni regenerar estas claves mientras existan identidades del Sandbox.

Webhook temporal: https://b369-186-104-25-125.ngrok-free.app/webhooks/whatsapp/kapso. ngrok apunta a localhost:8002, un proxy limitado al POST del webhook; las demás rutas se rechazan. Inspección de requests de ngrok desactivada y proxy sin logging de payloads. No se expone la API completa. La revisión automática rechazó el primer planteamiento de túnel directo; se aplicó la alternativa restringida antes de iniciar el túnel.

Pruebas locales: login por proxy 404; firma inválida 401; inbox permanece en 0. API/worker listos para recibir después de configurar el webhook en Kapso. No hay todavía mensaje real, vinculación ni E2E Kapso aprobado. URL temporal puede cambiar al reiniciar ngrok.


## Primer inbound real: 2026-10-03 13:11:35 America/Santiago

Consulta nueva a PostgreSQL confirmó un inbox received/text, DONE, attempts=1, sin error de procesamiento. Un outbox reply quedó FAILED, attempts=1, error_code=provider_http_error y sin provider_message_id. Accounting: inbound=1; IA=0; identidades activas=0. No hay todavía éxito de entrega a WhatsApp ni E2E completo.

La consulta no mutante de configuración del número a Kapso devolvió HTTP 200. Esto acredita acceso de lectura con las credenciales, no permiso/saldo/capacidad de envío. El adapter actual descarta detalles/status HTTP de send; no se conservó el motivo exacto del rechazo. No se reenvió automáticamente ni se expusieron teléfono, texto, secretos o respuesta cruda del proveedor. Pendiente consultar el diagnóstico de envío en Kapso para distinguir autorización, saldo o restricciones Sandbox.


## Foto real rechazada: 2026-10-03 16:15:21 UTC

El delivery aportado desde Kapso muestra HTTP 400, Webhook inválido, para whatsapp.message.received con message.type=image, MIME declarado image/jpeg, caption y media ID. Diferencia respecto al fixture: message.kapso.direction=inbound, pero message.kapso.status=delivered. El adapter exigía received también en ese campo. No se conserva el payload original, teléfono, identificadores externos ni URLs firmadas.

Corrección acotada en app/whatsapp/kapso.py: admitir received o delivered para eventos received con direction inbound. El evento normalizado continúa siendo received; no se trata como recibo outbound. Se preservan HMAC sobre raw body, comparación constant-time, dirección, número configurado y deduplicación.

Cinco casos agregados en tests/test_whatsapp_foundation.py: reproducción anonimizada de imagen aceptada y deduplicada, rechazo de firma inválida y relabeling del evento; cuatro estados no observados rechazados. Suite dirigida foundation + contracts: 28/28, tres warnings de deprecación existentes. Suite Python completa no ejecutada tras esta corrección; baseline previa 246/246. JavaScript sin cambios: resultado previo 60/60. E2E real pendiente.

API y worker locales reiniciados; health HTTP 200. Falta retransmitir desde Kapso o enviar otra foto y consultar nuevamente PostgreSQL. No se acredita todavía descarga de foto, MIME real, interpretación, confirmación ni persistencia en Bitácora. El fallo outbound del primer texto sigue pendiente e independiente del rechazo 400. Sin merge ni deploy.


## Reenvío real confirmado: 2026-10-03 16:22:41 UTC

Consulta nueva a PostgreSQL: received/image persistido y DONE, attempts=1, error_code NULL; procesamiento terminado a las 16:22:41.418 UTC (aproximadamente 202 ms desde created_at, no equivalente a latencia HTTP). Outbox reply con provider_message_id presente y estado READ, attempts=1, error_code NULL. Receipts sent y read persistidos y DONE. La respuesta de este nuevo mensaje sí fue aceptada por Kapso y reportada leída; el outbox FAILED del texto anterior permanece como evidencia histórica.

Identidades verificadas=0, media_rows=0, training_sessions=0, training_ai_usage=0. Se acredita recepción de imagen y respuesta de vinculación, no descarga/interpretación ni registro de la imagen: el remitente aún no está vinculado. Próximo paso: autenticación en el Sandbox localhost:8001, generar challenge y enviar su código desde WhatsApp. No se observó evento delivered en esta consulta; no se inventa ni se considera validado. Replay/idempotencia real aún pendientes.


## Vinculación real: 2026-10-03 16:26:26 UTC

El usuario confirmó la respuesta WhatsApp vinculado a Fluxio. Consulta nueva a PostgreSQL confirmó identidad activa con verified_at persistido, phone_encrypted no vacío y phone_hash de 64 caracteres; los valores privados no fueron seleccionados. Esta comprobación de presencia no sustituye una revisión criptográfica ni una auditoría completa de logs.

Inbox received/text y receipts sent/delivered/read: DONE sin error. Outbox más reciente: READ, provider_message_id presente, sin error. TrainingSession=0; training_ai_usage=0. Vinculación y respuesta reales confirmadas; siguiente prueba ayuda y captura de texto con propuesta antes de Guardar. Confirmación/idempotencia de entrenamiento aún pendientes.


## Propuesta de texto real recibida, 2026-10-03 16:31 UTC

El usuario confirma recepción de propuesta. Consulta nueva a PostgreSQL: TrainingSession=0 antes de confirmar; inbound texto DONE sin error y respuesta interactive READ sin error. Se acredita que recibir la propuesta no guarda automáticamente. training_ai_usage contiene 10 filas; este conteo de registros no demuestra 10 llamadas IA y requiere desglose antes de concluir consumo. Confirmación Guardar y conteo posterior pendientes.


## Confirmación real Guardar: 2026-10-03 16:32:55 UTC

Consulta nueva a PostgreSQL tras confirmación del usuario: TrainingSession pasó de 0 a exactamente 1, creada a las 16:32:55.091847 UTC. Conversation_state=IDLE, pending_action NULL. Inbound interactive DONE sin error; respuesta con provider_message_id presente, READ, sin error. Se acredita propuesta sin guardado y creación única tras la primera confirmación real. No equivale a validar retransmisión de webhook ni doble confirmación: ambos siguen pendientes.

Detalle web para comprobación manual en el Sandbox: http://localhost:8001/training/10087c47-0b24-4ba9-b2f6-ad7d4dfab866. Visualización autenticada por usuario aún pendiente. Foto/audio reales interpretados, consumo desglosado y casos de error siguen pendientes. Sin merge ni deploy.


## Diagnóstico de descarga de foto real, 2026-10-03

Inbound image DONE con respuesta de error READ; media=0, entrenamientos=1. El error genérico no acreditaba fallo de interpretación IA. Consulta de media real anonimizada en outputs: sin phone_number_id produjo provider_http_error; con phone_number_id devolvió metadata con download_url en api.kapso.ai/meta/whatsapp/media_download. Descarga real completada: 157845 bytes, Content-Type image/jpeg. No se almacenaron bytes ni URLs firmadas en documentación/logs.

Corrección del adapter: añadir el phone_number_id configurado a la consulta de metadata y rechazar ausencia de configuración. Se conserva la allowlist de host/path y el límite de descarga; no se utilizan URLs externas del webhook. Fixture actualizado para exigir phone_number_id. Documentación primaria: https://docs.kapso.ai/docs/whatsapp/typescript-sdk/media. Descarga real comprobada; decodificación, storage privado, interpretación, propuesta y confirmación de foto todavía pendientes de nuevo mensaje. El primer entrenamiento permanece intacto. Sin merge ni deploy.


## Foto confirmada y persistida: 2026-10-03 16:46:22 UTC

El usuario confirmó la propuesta y recibió Entrenamiento guardado. Consulta nueva a PostgreSQL: sesiones=2 (antes 1), última sesión con source_image_id presente; WhatsAppMedia image vinculada a TrainingSession; conversation_state IDLE sin pending_action; respuesta READ sin error. Detalle para comprobación web manual: http://localhost:8001/training/dfd8b834-c5ce-4d59-af3d-aef7d52bae09. Visualización web autenticada aún pendiente.

Foto real completó descarga, interpretación, propuesta, confirmación y persistencia con imagen. No acredita replay/idempotencia real. Fricción reportada durante aclaraciones: repetición de la pregunta sobre 8 minutos de activación y varias preguntas de detalle antes de la propuesta; posible pérdida de contexto por investigar, no causa demostrada. No se modificó esa lógica. Audio, errores restantes y costos/tokens desglosados siguen pendientes. Sin merge ni deploy.


## Ajuste de aclaraciones autorizado por el usuario

capture.py se alinea con la revisión web: cuando workout tiene contenido se propone el borrador aunque el intérprete devuelva questions. Las dudas se muestran como Por confirmar (opcional), con Guardar/Corregir/Cancelar. Si workout está vacío se mantiene CLARIFY. No se inventan respuestas, no cambia el intérprete compartido ni contratos/API; persistencia continúa exigiendo confirmación. No se implementó clasificación nueva de contradicciones: el criterio es el mismo contenido de workout que permite revisión web.

Tests: fixture de aclaración actualizado a workout vacío; nueva regresión prueba dudas opcionales, ausencia de guardado automático, corrección con source acumulado y guardado único. Suite WhatsApp capture/foundation/contracts: 57/57, tres warnings existentes. Suite completa y E2E real del nuevo comportamiento aún no repetidos. API y worker locales reiniciados para aplicarlo. Sin merge ni deploy.


## Nota de voz real: 2026-10-03 17:03 UTC

Inbox received/audio DONE sin error. Descarga diagnóstica real desde Kapso: Content-Type audio/ogg, 33376 bytes. FFprobe sobre archivo temporal privado: format ogg, codec opus, duración 13.866500 s, exit 0. Archivo temporal eliminado; no se registra contenido ni URL firmada. Diferencia fixture vs real: formato real ahora observado, no inferido del fixture.

TRANSCRIBE COMPLETED sin error, duración contabilizada 14.0 s, tokens entrada/salida NULL (desconocidos, no cero). INTERPRET COMPLETED sin error: 574 tokens entrada, 141 salida. Propuesta interactive READ; conversation_state CONFIRM. Sesiones=3; la última fue creada a las 16:54:55 UTC, antes de este audio. No hay entrenamiento nuevo del audio antes de confirmar. Guardado de audio pendiente.

Costos whatsapp_usage consultados: inbound 27 unidades, outbound 26, media 3, media_bytes 349066; todos los costos NULL/UNKNOWN. Son acumulados del Sandbox, no costos exclusivos del audio ni prueba de facturación del proveedor. Suite completa aún pendiente; sin merge ni deploy.


## Audio confirmado y persistido: 2026-10-03 17:04:46 UTC

El usuario confirmó Guardar. Consulta nueva a PostgreSQL: TrainingSession pasó de 3 a exactamente 4; última creada a las 17:04:46.858276 UTC. Conversation_state IDLE, pending_action NULL; inbound interactive DONE sin error; respuesta aceptada y READ, sin error. Audio real completó descarga OGG/Opus, transcripción, interpretación, propuesta, confirmación y persistencia. Comprobación visual web pendiente: http://localhost:8001/training/fa8e21df-ebb0-421e-8824-c8b3a4d2274a.

Esto acredita una primera confirmación, no retransmisión real ni doble confirmación. Las validaciones restantes del informe siguen pendientes. Sin merge ni deploy.


## Corrección de fecha reportada en audio

El usuario indicó que dijo 2 de octubre, pero la sesión del audio quedó el 3. Causa en código: fecha asignada antes de transcribir; solo ayer detectado inicialmente; contrato del intérprete no incluye fecha. Se añadió extracción acotada de fechas españolas con mes escrito (año explícito o año actual de Santiago), hoy/ayer después de transcribir y también al corregir. Fechas inválidas no se sustituyen silenciosamente; no se infieren fechas de duraciones/repeticiones. Fecha visible en propuesta. No se cambiaron APIs ni prompt compartido.

Suite capture + contracts 38/38: audio con fecha explícita, corrección, hoy/ayer, duración no confundida e inválida. Suite completa pendiente. Última sesión de audio corregida mediante TrainingService al 2026-10-02 según indicación del atleta, conservando demás campos. API/worker Sandbox reiniciados. Prueba real de nueva fecha pendiente; formatos numéricos y fechas en palabras no cubiertos por este parser. Sin merge ni deploy.


## Prueba combinada imagen + audios + confirmación, 2026-10-03 17:09–17:12 UTC

Consultas nuevas: secuencia received/image, interactive, audio, interactive, audio, interactive; todos DONE sin error. Una sola sesión creada durante ese flujo; total acumulado 5. Última sesión trained_on=2026-09-30, source_image_id presente, resultado 10 rondas. WhatsAppMedia imagen vinculada; conversation_state IDLE; respuesta READ sin error. Se acredita conservación de imagen al corregir por audio y fecha explícita en registro real. No acredita retransmisión idéntica ni doble Guardar.

Bloque WOD persistido AMRAP 10 minutos con 15 STOH (43/29 kg) y 10 burpees target. Carga personal no asignada arbitrariamente: adaptación conserva que el atleta dijo peso del WOD sin especificar cuál. RPE NULL. Persisten textos de lectura incierta en bloques secundarios y título con borrador: oportunidades de calidad, sin cambios de código en este análisis. No se cotejó la pizarra original visualmente; exactitud OCR de esos detalles no aprobada.

Dos últimas interpretaciones COMPLETED: 2587/824 y 2611/650 tokens entrada/salida; transcripciones COMPLETED con 5 y 8 segundos contabilizados y tokens desconocidos. Estas son las últimas dos llamadas, no el consumo completo de la sesión. Detalle web para validar manualmente: http://localhost:8001/training/4273d3bb-8d9b-469c-8699-253ea0aa7317. Sin merge ni deploy.


## Doble confirmación textual real: 2026-10-03 17:21:45 UTC

El usuario envió Guardar nuevamente después de finalizar el entrenamiento y recibió No hay una propuesta vigente para guardar. Consulta nueva a PostgreSQL: sesiones permanecen en 5; conversation_state IDLE, pending_action NULL; último inbound text DONE sin error; respuesta aceptada y READ sin error. Validado rechazo de segunda confirmación textual sin crear otra sesión. Es un mensaje nuevo con respuesta legítima, no replay del mismo webhook ni prueba de ausencia de respuesta duplicada en replay. Reutilización de botón antiguo y retransmisión real de Kapso siguen pendientes. El usuario no encontró opción de replay en dashboard; no se da por validada esa capacidad.


## Validación visual manual confirmada por el usuario — 2026-10-03

El atleta confirmó explícitamente los cinco puntos de revisión visual del Sandbox:

- Aparecen los cinco entrenamientos.
- Las fotos se ven en listado y detalle.
- Resultados y bloques corresponden al contenido enviado.
- El primer registro de audio tiene fecha 2 de octubre y el último registro fecha 30 de septiembre.
- La experiencia se ve correctamente desde el teléfono.

Fuente: confirmación manual del usuario en esta conversación. Estos puntos quedan aprobados como revisión visual humana, no como ejecución E2E automatizada ni inspección adicional del agente. No se adjuntaron nuevas capturas ni datos privados. Esta confirmación cubre la correspondencia visual de los bloques que previamente estaba pendiente.

Pendientes para cierre: suite automática completa sobre los últimos cambios, revisión de privacidad/logs y consumo consolidado, casos de error controlados restantes, botón antiguo real y retransmisión real del mismo webhook Kapso. Doble confirmación textual ya validada por consulta nueva. No se hizo merge ni deploy ni se amplió el alcance de funcionalidades.


## Regresión final y auditoría local — 2026-10-03

Resultados sobre el workspace actual, sin merge/deploy:

- Python completo: 259/259, 151.61 s, tres warnings de deprecación existentes.
- JavaScript completo: 60/60, 15.716 s, sin fallos ni skipped.
- E2E UI/HTTP/PostgreSQL: seis flujos PASS (texto, foto, audio, análisis/solicitud atleta, revisión coach, feedback atleta), sin errores JavaScript. Servidor temporal localhost:8768, base movement_test, IA/pose fixtures. Servidor detenido al terminar; Sandbox no utilizado para tests.
- Tests OpenAPI exacto y roundtrip Alembic incluidos en Python completo y aprobados. Sandbox Alembic confirmado por SQL: 0020_whatsapp_capture.
- Casos controlados aprobados dentro de la suite: firma/límite, batch/replay/deduplicación, doble acción, código vencido/reutilizado, botón antiguo, aislamiento de atleta, media inválida/límites/errores del proveedor, audio inválido, send incierto y retry seguro. Son pruebas aisladas, no errores reales inducidos en Kapso. No se enviaron mensajes adicionales para esta regresión.

Privacidad: una identidad descifrada solo en memoria; cifrado no contiene el teléfono plaintext y el hash HMAC corresponde al número normalizado. Solo se imprimió resultado booleano. Esquema training_sessions: cero columnas phone. Logs completos disponibles de API y worker consultados en memoria: cero coincidencias de patrón de teléfono chileno y de patrones phone_encrypted/phone_hash/código VINCULAR/X-API-Key/data:image. Revisión acotada a esos patrones y esos dos contenedores; no acredita ausencia de toda forma de PII ni inspección de logs del proveedor.

Consumo acumulado Sandbox al consultar: INTERPRET COMPLETED=20, input_tokens=31061, output_tokens=8791; TRANSCRIBE COMPLETED=3, audio_seconds=27, tokens NULL para las tres llamadas. Inbound=35, outbound=34, media=6, media_bytes=493260. Categorías con todos sus costos NULL: UNKNOWN, nunca cero. Conteos son accounting local, no factura del proveedor ni atribución exclusiva a un entrenamiento. Interpretaciones incluyen intentos y correcciones del flujo anterior. La primera respuesta FAILED sigue como evidencia histórica; outbound accounting no prueba que todos los envíos hayan sido entregados.

Estado de cierre: regresión automática y validación visual humana aprobadas; texto/foto/audio/combinado y doble Guardar textual reales aprobados. Pendientes explícitos: replay del mismo webhook desde Kapso (sin opción localizada), botón antiguo real y casos de error reales no provocados; accepted no observado como evento de webhook. No declarar esos pendientes aprobados por los tests simulados. La vinculación por UI continúa documentada, no implementada. Parser de fecha acotado a meses españoles escritos y hoy/ayer; otros formatos y ambigüedades siguen siendo limitación. No hay nuevas funcionalidades de Fase 4.


## Confirmación manual de vinculación UI — 2026-10-03

El usuario indicó que probó la nueva interfaz de vinculación y funciona. Se registra aprobación manual del recorrido probado. No especificó si utilizó QR o enlace por clic: no se acredita cada alternativa por separado con esta confirmación. Generación/consulta/desvinculación y QR permanecen cubiertos por las pruebas dirigidas previas; regresión completa posterior a interfaz y QR sigue pendiente. Sin merge ni deploy.


## Preparación final del candidato de publicación — 2026-10-03

Sin commit/push/merge/deploy. Base f0b1acc; rama codex/bitacora-entrenamiento. Parche local .tools/whatsapp-release.patch con 15 archivos, validado mediante git apply --cached --check sin modificar índice. Candidato en .tools/whatsapp-release-candidate contiene HEAD más únicamente los cambios seleccionados. index.html incluye metadata y scripts de vinculación/QR, conservando el body de HEAD para excluir opciones de ejercicios ajenas. Excluidos skills, adjuntos, capturas, analyzer/perfiles, env privados, compose Sandbox y datos.

Regresión del candidato exacto: Python 246/246 (137.60 s, tres deprecaciones existentes); JavaScript 62/62 (14.888 s); seis flujos E2E PASS, sin errores JavaScript, IA/pose fixtures y PostgreSQL aislado. Contratos OpenAPI y roundtrip Alembic aprobados dentro de Python. No equivale a seis flujos reales Kapso nuevos. Servidor E2E temporal detenido.

Workspace completo: Python 260/260 (148.40 s) y JS 62/62. Diferencia de 14 tests Python corresponde a cambios locales de ejercicios excluidos de la candidata. Los resultados previos del workspace no deben confundirse con esta selección. La nueva baseline para publicar únicamente WhatsApp es 246/62/6, con vinculación/QR incluidos.

Configuración para publicación: WHATSAPP_PUBLIC_NUMBER además de credenciales de provider, webhook, ID y claves persistentes; número público no es provider ID. Entorno destino debe tener su propio webhook HTTPS y worker con misma DB/storage/claves; no reutilizar ngrok temporal como URL productiva. No se incluyen valores secretos del Sandbox. QR licencia MIT preservada y servido localmente.

Pendientes reales siguen explícitos: replay Kapso, botón antiguo real y fallos reales no inducidos. Usuario aprobó revisión visual de registros y recorrido de vinculación; no especificó cada alternativa QR/clic por separado. Costos permanecen UNKNOWN. Limitación de fechas acotadas y título borrador documentadas. Preparado para revisión y autorización de publicación; no se avanzó a Fase 4.
