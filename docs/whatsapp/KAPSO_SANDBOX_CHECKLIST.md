# Validación real de Kapso Sandbox

Estado: preparación; ningún mensaje real aprobado todavía. No Fase 4, merge ni deploy.
Código auditado: `f0b1acc`. Baseline declarada: Python 246, JavaScript 60, E2E 6, Alembic 0020.

## 1. Configuración y requisitos

Usar un entorno Sandbox ya accesible por HTTPS con esta revisión, una base PostgreSQL separada y storage privado. No ejecutar `pytest` sobre esa base: los fixtures limpian tablas. El worker y la API necesitan la misma base, storage y claves. No habilitar el canal de producción ni iniciar envíos hasta completar los requisitos.

| Variable | Obtener/configurar | Lectura actual |
|---|---|---|
| `WHATSAPP_PROVIDER=kapso` | Configuración del entorno | Sí, único adapter |
| `KAPSO_API_KEY` | API key del proyecto de pruebas en Kapso; no token de Meta | Sí, `X-API-Key` outbound/media |
| `KAPSO_WEBHOOK_SECRET` | Secret key del webhook de tipo Kapso; elegir/configurar el mismo valor en Kapso y Fluxio | Sí, HMAC SHA-256 |
| `KAPSO_PHONE_NUMBER_ID` | Identificador de la configuración Sandbox WhatsApp, no el número del destinatario | Sí, valida el número propietario del evento |
| `PUBLIC_BASE_URL` | Origen HTTPS público del entorno Sandbox, sin slash final | No se consume; inventario de URL |
| `PHONE_ENCRYPTION_KEY` | Clave Fernet generada localmente y almacenada en un gestor de secretos | **No se consume** |
| `PHONE_HASH_KEY` | Secreto independiente, base64 URL-safe que decodifica a por lo menos 32 bytes aleatorios | Sí, lookup HMAC |
| `WHATSAPP_ENABLED=true` | Solo en el entorno aislado | Sí; el ejemplo mantiene `false` seguro |
| `WHATSAPP_ENCRYPTION_KEY` | Nombre realmente leído para la clave Fernet de cifrado | **Obligatorio adicional con el código actual** |
| `WHATSAPP_KEY_VERSION=1` | Versión local de la clave | Sí |

No basta con las ocho variables solicitadas: configurar la clave bajo `WHATSAPP_ENCRYPTION_KEY` o resolver primero la discrepancia del nombre. No se implementó un alias silencioso. Generar claves en un gestor seguro; no pegarlas en chat, documentos, capturas, argumentos de comandos ni logs. No rotar `PHONE_HASH_KEY` entre mensajes de una misma validación. El keyring `WHATSAPP_ENCRYPTION_KEYS` solo es necesario para descifrar versiones anteriores.

Para texto/foto/audio con IA, también se requieren las variables existentes de interpretación/transcripción y `OPENAI_API_KEY` en el entorno y worker, además de FFmpeg/ffprobe. No se requieren para vinculación y ayuda. Mantener `WHATSAPP_OUTBOUND_UNIT_COST_USD` vacío cuando la tarifa se desconoce: no introducir cero como estimación.

## 2. Activar el teléfono y el webhook

En [Kapso Sandbox](https://docs.kapso.ai/docs/how-to/whatsapp/use-sandbox-for-testing), dentro del proyecto de pruebas:

1. WhatsApp → Sandbox → Add Test Number; registrar el teléfono desde el que se probará.
2. Crear sesión, abrir WhatsApp desde el enlace mostrado y enviar el código de activación de Kapso. Es distinto del código de vinculación de Fluxio. Debe llegar la confirmación y la sesión quedar `active`; si vence, generar otra sesión.
3. WhatsApp → Configurations → Sandbox WhatsApp → Manage Webhooks. Obtener el identificador de esa configuración. No confundirlo con un número telefónico ni usar una configuración de producción.
4. Crear webhook **WhatsApp de tipo `kapso`, versión v2**, no Platform/project ni tipo Meta. Configurar secret key y copiarlo mediante el gestor de secretos al entorno Fluxio.
5. Seleccionar `whatsapp.message.received`; para la segunda ronda también `whatsapp.message.sent`, `whatsapp.message.delivered`, `whatsapp.message.read`, `whatsapp.message.failed`. Si un evento no está disponible en Sandbox, registrarlo como no disponible, no aprobado. Desactivar buffering para la primera prueba; probar batches después.
6. La URL exacta es el valor de `PUBLIC_BASE_URL` seguido de `/webhooks/whatsapp/kapso`. El dominio aún debe ser proporcionado: no se ha identificado una URL real verificable en esta fase. Ejemplo de formato solamente: `https://sandbox.example.invalid/webhooks/whatsapp/kapso`.
7. Desactivar otros agentes/flows que respondan al mismo teléfono durante esta prueba. No publicar un workflow nuevo.

Origen de la API key: proyecto Kapso, sección de API keys/credenciales disponible para ese proyecto; si la UI no muestra esa sección, confirmar con Kapso en vez de sustituirla por otra credencial. Para verificar el identificador, el API oficial ofrece `GET https://api.kapso.ai/platform/v1/whatsapp/phone_numbers` con la key del proyecto; ejecutarlo privadamente sin guardar el cuerpo completo ni datos de teléfonos.

Fuentes: [webhooks](https://docs.kapso.ai/docs/platform/webhooks/overview), [firmas](https://docs.kapso.ai/docs/platform/webhooks/security). No se ha confirmado el diseño exacto de la UI de tu cuenta.

## 3. Preflight de Fluxio

- [ ] En el entorno correcto, `alembic current` devuelve `0020`; no ejecutar downgrade.
- [ ] `/openapi.json` contiene `POST /webhooks/whatsapp/kapso` y los endpoints de vinculación existentes.
- [ ] Variables presentes, sin listar sus valores. API y worker pueden crear `Vault()` sin error.
- [ ] PostgreSQL y storage compartidos entre API y worker, separados de producción.
- [ ] Certificado HTTPS válido, ruta sin login, captcha o redirección. El proxy conserva raw body y headers.
- [ ] En `APP_ENV=production`, Fluxio ve esquema HTTPS. Si el proxy termina TLS, revisar trusted forwarded headers; no confiar en cualquier origen indiscriminadamente. Un `400 HTTPS requerido` no indica firma inválida.
- [ ] Worker independiente activo: `python -m app.whatsapp.worker`. Para una ronda controlada existe `python -m app.whatsapp.worker --once`; procesa como máximo un inbound y un outbound por llamada, repetir hasta drenar. No procesar en el webhook.
- [ ] No imprimir payloads originales, teléfonos, códigos, claves, firmas ni URL firmada de media.

El endpoint tiene límite de **262144 bytes**, lectura por stream de bytes originales, HMAC SHA-256 y `hmac.compare_digest`. La firma debe ser hexadecimal minúscula de 64 caracteres en `X-Webhook-Signature`, sin prefijo `sha256=`. `X-Webhook-Event` determina el tipo y debe concordar con los campos firmados. Persiste inbox antes del ACK; no llama a IA ni a Kapso durante esa petición.

Probar alcance antes de mensajes: enviar `{}` con `X-Webhook-Signature` de 64 ceros y `X-Webhook-Event: whatsapp.message.received` al endpoint habilitado. Esperar **401 Firma inválida** y cero filas nuevas; esto prueba alcance y rechazo, no integración completa. 404: ruta/canal incorrecto; 503: claves de cifrado no configuradas; 413: tamaño; 400: esquema/payload. No reenviar un payload real con firma inválida fuera del entorno de pruebas.

La entrega válida debe responder HTTP 200, `{"ok":true,"accepted":1}` para un mensaje nuevo (0 en duplicado), antes de procesamiento posterior. Medir latencia desde Kapso: objetivo menos de 10 s; no se ha medido realmente aún.

## 4. Primer E2E sin IA y vinculación

**Discrepancia del criterio solicitado:** enviar `ayuda` sin vincular devuelve instrucciones para generar un código. No crea `conversation_state` de atleta. Después de vincular, la ayuda real es: “Puedes registrar un entrenamiento por texto, foto o audio, agregar una nota y abrir tu bitácora en Fluxio.” No ofrece resumen semanal. No aprobar el texto esperado que promete “ver tu semana” sin resolver este criterio; no implementar Fase 4.

1. Registrar timestamp inicial y conteos de inbox/outbox/sesiones/IA. Enviar `ayuda` desde WhatsApp; comprobar entrega en Kapso, inbox persistente, worker `DONE`, outbox `SENT` y respuesta de vinculación. No deben aparecer llamadas IA ni sesiones.
2. Iniciar sesión como atleta de prueba en Fluxio. En su navegador autenticado ejecutar `fetch('/api/whatsapp/link-challenges',{method:'POST'}).then(r=>r.json())`; tratar el código devuelto como secreto temporal y no guardarlo en evidencia.
3. Enviar por WhatsApp el valor completo `VINCULAR ...`, dentro de 10 minutos. No enviar el código de activación de Kapso aquí.
4. Esperar confirmación. Consultar `GET /api/whatsapp/identity` desde la sesión autenticada: `linked:true`, `verified_at` presente, sin teléfono.
5. Verificar por SQL `phone_encrypted IS NOT NULL`, hash de 64 caracteres, fecha y vínculo al atleta; no seleccionar valores cifrados ni hashes completos en los reportes.
6. Enviar `ayuda` otra vez; comprobar IdentityResolver → conversation_state IDLE → outbox → WhatsApp, sin IA. Registrar la respuesta real, no reemplazarla por la deseada.

## 5. Texto y confirmación

Enviar `Hoy hice 4 rondas en 12 minutos`. Debe producir interpretación existente y propuesta; contar sesiones antes y después: **delta 0 antes de confirmar**. El texto puede ser insuficiente para especificar ejercicios; si hay preguntas, responderlas, y registrar la desviación respecto al caso ideal, sin inventar ejercicios.

Responder `Guardar` o pulsar el botón vigente. Consultar PostgreSQL mediante una conexión/transacción nueva: **delta 1**. Abrir `/training` y `/training/<id>` como ese atleta y comprobar la misma sesión, resultado y fecha. No validar únicamente objetos de ORM ya cargados ni una respuesta HTTP. Repetir `Guardar` y el botón anterior: delta posterior 0.

## 6. Duplicados

Preferir retransmitir la misma entrega mediante la función de replay/retry que Kapso exponga; si no existe, operador autorizado puede reenviar privadamente los mismos bytes firmados durante la ventana admitida. No copiar payloads sensibles a este repo. La deduplicación se basa en `(provider, provider_message_id)`, no en el identificador del request HTTP. Repetir antes y después de procesar; repetir también batch e individual con el mismo ID.

Esperar accepted 0 para el mismo mensaje, un inbox lógico, una respuesta de negocio y una única TrainingSession. Hay que comprobarlo con consultas nuevas; las notificaciones de estado tienen su propia clave `event:message_id` y no son mensajes de negocio duplicados.

## 7. Foto y audio reales

- Foto: enviar una pizarra real. Registrar tipo de evento, MIME declarado y MIME de descarga, bytes descargados y validación del contenido; nunca URL firmada. Verificar ≤8 MiB, decoder de imagen, storage privado, propuesta, delta 0 sin confirmar; Guardar, delta 1 y foto en Bitácora. El adapter solo descarga referencias permitidas desde `api.kapso.ai` y rechaza redirects. Acceso a foto como otro atleta/guest debe fallar.
- Audio: grabar una **nota de voz en WhatsApp**, no subir el fixture. Registrar container/codec observados con ffprobe privadamente; reportar únicamente formato, codec, duración y tamaño. Confirmar OGG/Opus si realmente llega así; MIME puede incluir parámetros, y el MIME descargado puede diferir del declarado. No se da por aprobado por el test OGG generado. Validar FFmpeg, ≤8 MiB/180 s, transcripción, interpretación, propuesta, Guardar y Bitácora. Audio es transitorio y no debe quedar persistido como grabación.
- No incluir video conversacional, nuevas métricas ni resumen semanal.

## 8. Errores y delivery/read

| Caso | Resultado a observar |
|---|---|
| Firma ausente/incorrecta; bytes modificados | 401, sin persistencia ni IA |
| Payload superior al límite | 413, sin persistencia |
| Mensaje duplicado/doble Guardar | Delta de sesión 0 después del primer guardado |
| Media inválida/inexistente | Error recuperable, sin sesión parcial ni secretos en respuesta |
| Transcripción fallida | Sin confirmación automática; consumo real reportado o desconocido |
| Atleta no vinculado | Instrucción de vincular, sin entrenamiento |
| Código expirado/reutilizado | No reasigna identidad; generar otro código |
| Botón antiguo | No confirma otra propuesta ni crea una sesión extra |
| Timeout outbound | Estado UNCERTAIN; no reenviar ciegamente ni prometer exactly-once de red |

Simular errores solo si Sandbox permite hacerlo; marcar “no ejecutado” si no es posible. Sin inyectar fallos en producción.

Accepted de la API outbound se representa por respuesta con ID y estado local SENT; los eventos suscritos son sent/delivered/read/failed. **No hay normalización de un evento denominado accepted** en este adapter. Si Kapso lo entrega, conservar evidencia anonimizada y registrar incompatibilidad, no marcarlo aprobado. Los estados no deben activar conversación, IA, reply ni registro de sesión. Revisar no regresión READ → DELIVERED y duplicados de receipts.

## 9. Evidencia por PostgreSQL

Abrir psql contra la base Sandbox en una conexión nueva en cada comprobación. Sustituir parámetros solo por IDs/tiempos de prueba. No ejecutar SELECT de payloads ni teléfonos.

```sql
SELECT version_num FROM alembic_version;
SELECT id,event,message_type,state,attempts,error_code,processed_at,
       payload_encrypted IS NOT NULL AS protected_pending
FROM whatsapp_inbox WHERE created_at >= :'started_at' ORDER BY created_at;
SELECT id,action,state,attempts,error_code,provider_message_id IS NOT NULL AS has_provider_id
FROM whatsapp_outbox WHERE created_at >= :'started_at' ORDER BY created_at;
SELECT athlete_id,channel,state,version,pending_action IS NOT NULL AS has_pending_action
FROM conversation_state WHERE athlete_id = :'athlete_id';
SELECT athlete_id,phone_encrypted IS NOT NULL AS encrypted,
       length(phone_hash)=64 AS hash_shape,verified_at,revoked_at
FROM athlete_identity WHERE athlete_id = :'athlete_id';
SELECT count(*) FROM training_sessions
WHERE athlete_id = :'athlete_id' AND created_at >= :'started_at';
SELECT column_name FROM information_schema.columns
WHERE table_name='training_sessions' AND column_name ILIKE '%phone%';
SELECT provider,event,provider_message_id,count(*) FROM whatsapp_inbox
WHERE created_at >= :'started_at' GROUP BY provider,event,provider_message_id HAVING count(*)>1;
SELECT dedupe_key,count(*) FROM whatsapp_outbox
WHERE created_at >= :'started_at' GROUP BY dedupe_key HAVING count(*)>1;
SELECT category,count(*) AS records,sum(units) AS units,
       CASE WHEN count(cost)<count(*) THEN 'UNKNOWN' ELSE 'KNOWN' END AS cost_state,
       sum(cost) AS known_partial_cost
FROM whatsapp_usage WHERE created_at >= :'started_at' GROUP BY category;
SELECT operation,model,status,input_tokens,output_tokens,duration_seconds
FROM training_ai_usage WHERE athlete_id=:'athlete_id' AND created_at>=:'started_at';
SELECT media_type,training_session_id IS NOT NULL AS linked,count(*)
FROM whatsapp_media WHERE created_at>=:'started_at' GROUP BY media_type,linked;
```

No interpretar un parcial conocido como costo total. NULL sigue siendo UNKNOWN; no usar COALESCE(cost,0). Ayuda/vinculación no deben aumentar llamadas IA. Contar media_bytes incluso si hubo validación fallida posterior. Revisar logs privadamente por filtración de números/códigos; no exportar las coincidencias al reporte.

## 10. Cierre

Registrar cada prueba con hora, ambiente/commit, evento anonimizado, HTTP/latencia, IDs internos, estados antes/después y conteos obtenidos mediante consulta nueva. Guardar solo muestras normalizadas redactadas: teléfono, texto personal, IDs externos, reference de media y acciones como `[REDACTADO]`. Los originales, si son indispensables para replay, quedan fuera de Git en un almacenamiento privado temporal.

Completar `KAPSO_SANDBOX_VALIDATION.md` únicamente con hechos observados. Hasta que haya credenciales, dominio, worker y mensajes reales, el resultado global es **PENDIENTE**, nunca “Sandbox aprobado”.
