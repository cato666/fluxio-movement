# WhatsApp — cierre de Fases 2 y 3

Fecha: 3 de octubre de 2026. Estado: **Fase 3 completada, gates verdes y trabajo detenido**. Sólo commits locales en `codex/bitacora-entrenamiento`; sin merge, push, deploy, producción ni credenciales reales.

## 1. Baseline usada

Se tomó la baseline aprobada de F0/F1: Python 195/195, JavaScript 60/60, Bitácora, texto/foto/audio, Athlete UX y Coach UX aprobados; contratos OpenAPI preservados; Alembic `0018_training_ai_usage`. No se repitió F0/F1.

Se creó el checkpoint pendiente `cb6b797`, incluyendo exclusivamente los archivos propios de F0/F1. Los cambios preexistentes de UI, analizador, perfiles de ejercicios y skills permanecen separados. Se registraron status, patch y hashes en `results/whatsapp/preexisting-*`: **104 hashes verificados sin cambios** al finalizar.

Todas las pruebas usaron `movement_test` en PostgreSQL descartable con tmpfs, sin puerto PostgreSQL publicado y sin cargar `.env`. El proyecto Docker `fluxio-whatsapp-tests` y el servidor E2E se apagaron y eliminaron al terminar. La BD habitual no se utilizó.

## 2. Fase alcanzada y comportamiento

Fase 2: Kapso como único proveedor; webhook firmado, identidad verificada, códigos temporales, revocación, inbox/outbox durable, estados de conversación y help.

Fase 3: `register_workout` y `add_note`, con propuestas antes de cualquier modificación de Bitácora. Texto y foto usan la interpretación existente. Audio OGG/Opus pasa por FFprobe/FFmpeg y la transcripción existente. Video MP4 H.264/HEVC se valida y almacena en privado; solicita contexto por texto/audio y no invoca el analizador biomecánico.

Guardar, corregir y cancelar usan acciones opacas asociadas a una versión del estado. Guardar consume el borrador exacto del servidor; no toma contenido del botón. Los mensajes duplicados, botones antiguos, estados expirados y teléfonos de otros atletas no producen una segunda sesión. La corrección vuelve a proponer; la interpretación ambigua pregunta una sola aclaración.

Las notas apuntan a sesiones propias de la fecha reciente más nueva dentro de siete días. Si hay varias candidatas en esa fecha, se pide selección. Más de tres candidatas deriva a la Bitácora web, evitando elegir silenciosamente. Se conserva `adaptations` y se agrega una etiqueta visible, junto con JSONB `athlete_notes` que contiene `type=athlete_note`, `source=whatsapp` y texto. No se creó una tabla de notas.

No se implementaron Fases 4/5/6, resumen semanal, landing, tokens compartidos, campañas, mensajes proactivos, PR/RM, redes, otros proveedores, coach por WhatsApp ni nuevas capacidades IA.

## 3. Commits locales

| Commit | Contenido |
|---|---|
| `cb6b797` | Checkpoint aprobado de servicios compartidos F0/F1 |
| `fecefaa` | Identidad verificada, adapter Kapso, webhook, inbox/outbox y tests de Fase 2 |
| `6528110` | Captura confirmada, audio, media privada y notas tipadas de Fase 3 |
| `3e5c7fd` | Tests de fiabilidad, OpenAPI congelado y script de reproducción |

Este informe se guarda en un commit documental posterior. Los commits no incluyen los cambios locales preexistentes.

## 4. Migraciones

- `0019_whatsapp_foundation`, posterior a `0018_training_ai_usage`: agrega siete tablas; no modifica ni hace backfill de teléfonos existentes.
- `0020_whatsapp_capture`: agrega `training_sessions.athlete_notes` con default `[]` y `whatsapp_media`. La referencia a TrainingSession usa `ON DELETE SET NULL` para conservar la eliminación web existente.

Upgrade/downgrade y `alembic check` verificados en la BD descartable. Una prueba baja a 0018, vuelve a head y verifica que una sesión previa conserva atleta, workout y adaptaciones. Los upgrades son aditivos. Un downgrade elimina los datos de las estructuras nuevas, por lo que requiere respaldarlos antes de usarse fuera de tests.

Revisión final registrada: **`0020_whatsapp_capture (head)`**.

## 5. Modelos y persistencia

| Tabla | Propósito |
|---|---|
| `athlete_identity` | Teléfono cifrado, HMAC de lookup, clave versionada, verificación y revocación; unicidad activa por atleta/teléfono |
| `whatsapp_link_challenges` | Código aleatorio hasheado, expiración, intentos y consumo único |
| `whatsapp_peers` | Límite de intentos de vinculación por lookup protegido |
| `whatsapp_inbox` | Mensaje normalizado cifrado, unicidad proveedor/mensaje, lease, intentos y timestamps |
| `whatsapp_outbox` | Respuesta cifrada, deduplicación, envío, entrega/lectura, intentos y resultado incierto |
| `conversation_state` | Borrador pendiente cifrado, acción opaca, versión y expiración |
| `whatsapp_usage` | Eventos idempotentes de consumo; costo desconocido representado por null |
| `whatsapp_media` | Referencia privada propia del canal y asociación a la sesión confirmada |

El teléfono nunca es una foreign key de negocio. TrainingService recibe `athlete_id`; no recibe JSON Kapso, teléfono de transporte, cookies ni endpoints internos.

El worker toma un advisory lock por remitente sobre una conexión fijada, incluso cuando el accounting IA realiza commits. Inbound, borrador y outbox quedan en PostgreSQL. Leases expirados permiten recuperar procesamiento interrumpido. Guardar sesión/nota, consumir estado y generar respuesta pertenece a una única transacción; un savepoint evita creaciones parciales cuando falla el enlace de media.

Los payloads de inbox se limpian al terminar. Borradores e inbox pendientes expiran a las 24 horas; outbox a las 23 horas. El worker elimina medios pendientes expirados sin salir del storage privado ni borrar imágenes que una sesión web esté utilizando. Medios confirmados se conservan; al borrar su sesión se habilita limpieza posterior.

## 6. Endpoints agregados y contratos preservados

| Endpoint | Acceso / función |
|---|---|
| `POST /webhooks/whatsapp/kapso` | Firma sobre raw body; máximo 256 KiB; normaliza, deduplica y hace commit antes del ACK; no ejecuta IA |
| `POST /api/whatsapp/link-challenges` | Atleta autenticado; genera código con TTL de 10 minutos |
| `GET /api/whatsapp/identity` | Atleta autenticado; estado de vínculo sin revelar teléfono |
| `DELETE /api/whatsapp/identity` | Atleta autenticado; revoca vínculo, borrador y envíos pendientes |

Todos los paths y schemas HTTP anteriores se compararon contra el OpenAPI aprobado, ahora versionado en `tests/fixtures/whatsapp-baseline-openapi.json`. No se cambiaron. Tampoco se agregaron campos de notas a las respuestas existentes.

La vinculación está disponible por API; no se agregó UI de configuración del canal en esta fase.

## 7. Tests antes y después

| Gate | Baseline aprobada | Fase 2 | Fase 3 |
|---|---:|---:|---:|
| Python completo | 195/195 | 216/216, 120.87 s | **246/246, 142.30 s** |
| JavaScript completo | 60/60 | 60/60, 18.710 s | **60/60, 16.128 s** |
| Específicos WhatsApp | — | 21/21 | **49/49, 31.00 s** |
| Contratos y conservación de datos | Aprobados | Compatibles | **2/2, 3.04 s** |
| E2E web | Aprobados | 6 PASS | **6 PASS** |

Los 51 tests nuevos están incluidos en los 246. Python conserva tres warnings previos de deprecación de Starlette/FastAPI. JavaScript no tiene fallos ni tests omitidos. Las suites completas no presentaron regresiones.

Los tests específicos cubren firma y límites, payloads/lotes retransmitidos, identidad y revocación, retry seguro, envío incierto, restart, rollback después de guardar, dos workers concurrentes, confirmación doble, acciones viejas, expiración, mensajes desordenados, ownership, notas y edición web concurrente, propuestas largas, privacidad, imágenes inválidas/sobredimensionadas y OGG real válido/inválido/Vorbis/duración excedida/error de transcripción.

Evidencias locales: `results/whatsapp/phase2-*` y `phase3-{specific,contracts,python,javascript,e2e,e2e-server,alembic}.log`. Los resultados están excluidos de Git, conservados en el workspace.

Entorno final: Python 3.11.14, Node v22.23.3; imagen local `fluxio-whatsapp-tests:phase2`, ID `sha256:63f83c0226a451897ebd0d62483812f647f4f56535bf004385cefa70cf4d31eb`. Se registraron `pip freeze` e identificadores en `results/whatsapp/`. Se agregó y fijó `cryptography==50.0.2`.

Reproducción: `./scripts/test-whatsapp.ps1 -TestImage fluxio-whatsapp-tests:phase2 -PlaywrightModule <ruta-a-playwright>`. El script crea otro proyecto descartable y guarda evidencia en una carpeta nueva. Si la imagen local no existe: `docker build --target test -t fluxio-whatsapp-tests:phase2 .`. Ejecutar con Node y Playwright disponibles; el script se detiene ante cualquier gate fallido y limpia los contenedores.

## 8. E2E ejecutados

Con navegador real y HTTP, autenticación, servicios compartidos, PostgreSQL y FFmpeg reales:

1. Bitácora texto: propuesta sin guardar, confirmación, lectura y edición.
2. Bitácora foto: carga, interpretación, guardado y privacidad.
3. Bitácora audio: micrófono, FFmpeg, transcripción, propuesta y confirmación.
4. Athlete UX: análisis de video persistido, media y solicitud de revisión.
5. Coach UX: iniciar, comentar, guardar y completar revisión.
6. Athlete UX: feedback del coach visible y sin errores JavaScript.

La IA externa y pose inference se controlan con fixtures del E2E existente. Además, un test de integración WhatsApp recorre webhook firmado → worker → implementación real de `workout_interpretation.interpret()` con transporte IA mock → outbox → confirmación → lectura en la Bitácora web. Los tests de audio usan OGG/Opus generado y decodificado realmente; los videos de prueba son MP4 reales.

## 9. Qué funciona con mocks

Toda la vinculación y captura, deduplicación, botones, estados, entrega/lectura, storage, reintentos, interrupciones y rollback. FakeProvider modela envío y descarga; tests adicionales ejercitan el adapter HTTP Kapso con respuestas realistas. Sólo se usan claves efímeras y valores `fixture-*`.

El contrato Kapso se contrastó con documentación oficial: [seguridad de webhook](https://docs.kapso.ai/docs/platform/webhooks/security), [eventos de mensaje](https://docs.kapso.ai/docs/platform/webhooks/message-events), [referencia de media](https://docs.kapso.ai/api/meta/whatsapp/media/get-media-url) y [descarga protegida](https://docs.kapso.ai/api/meta/whatsapp/media/download-media-file). El adapter accede exclusivamente a `api.kapso.ai`, rechaza redirects y URLs externas, y no manda API key a la URL de descarga firmada. La ruta Kapso `/meta/whatsapp/...` pertenece a Kapso; no se integró Meta directamente.

## 10. Qué requiere Kapso Sandbox real

Verificar configuración de webhook v2 y firma; payloads reales de texto/foto/voz/video y batches; `phone_number_id`; descarga y disponibilidad de media; botones y títulos; delivery/read/failed; ventana de respuesta; límites/rate limits y costos. Nada de esto se presenta como una prueba contra Kapso real.

También falta un piloto con IA real, autorizado y presupuestado, para valorar calidad de interpretación/transcripción. El pipeline actual se reutiliza; los resultados reales no pueden inferirse de las fixtures.

## 11. Variables de entorno y operación

En `.env.example`, el canal queda **deshabilitado** por defecto.

| Variable | Uso |
|---|---|
| `WHATSAPP_ENABLED` | `false` por defecto; `true` sólo al habilitar sandbox |
| `WHATSAPP_PROVIDER` | `kapso`; no hay otro adapter |
| `KAPSO_API_KEY` | Key del sandbox para enviar y obtener referencia de media |
| `KAPSO_WEBHOOK_SECRET` | Secreto HMAC de webhook |
| `KAPSO_PHONE_NUMBER_ID` | Identificador sandbox validado en cada evento |
| `WHATSAPP_ENCRYPTION_KEY` | Clave Fernet para payloads y teléfono |
| `WHATSAPP_KEY_VERSION` | Versión activa, default `1` |
| `WHATSAPP_ENCRYPTION_KEYS` | JSON keyring opcional de versiones anteriores |
| `PHONE_HASH_KEY` | Secreto base64 de al menos 32 bytes para lookup HMAC |
| `WHATSAPP_OUTBOUND_UNIT_COST_USD` | Tarifa opcional; vacío significa costo desconocido |

Se reutilizan `DATABASE_URL`, `STORAGE_PATH`, `OPENAI_API_KEY`, `TRAINING_AI_ENABLED`, `TRAINING_AI_MODEL`, `TRAINING_VOICE_ENABLED` y `TRAINING_TRANSCRIPTION_MODEL`. Se respetan los defaults actuales de IA. `APP_ENV=production` exige HTTPS en el webhook, pero no se configuró ni utilizó producción.

Worker separado: `python -m app.whatsapp.worker`; un ciclo: `python -m app.whatsapp.worker --once`. Necesita la misma BD, storage y claves que la API. No usa BackgroundTasks del request. No se agregó ni desplegó un supervisor.

## 12. Riesgos y deuda técnica

- Confirmación/persistencia tiene tests de concurrencia, pero el piloto debe verificar comportamiento y límites reales de Kapso. El canal permanece deshabilitado hasta esa validación.
- `UNCERTAIN` no se reenvía automáticamente. Se necesita revisar/reconciliar en el proveedor; las partes posteriores de esa propuesta quedan retenidas. No existe una consola operativa para esto.
- Una revocación cancela pendientes, pero no puede retirar un envío que ya está en tránsito hacia el proveedor.
- Las claves deben custodiarse y respaldarse. Para rotar cifrado, mantener el keyring antiguo mientras existan datos cifrados con él. La clave HMAC de lookup requiere un procedimiento distinto; cambiarla sin migración pierde la resolución de identidades.
- Falta supervisor/alertas para FAILED, UNCERTAIN, leases y limpieza, y definir cuotas de uso antes de abrir el piloto ampliamente. Los límites de contenido ya son acotados: imagen/audio 8 MiB; audio 180 s; video 16 MiB y 180 s; imagen hasta 24 megapíxeles.
- El video confirmado tiene referencia privada interna, sin vista nueva ni enlace de descarga en WhatsApp. El análisis técnico sigue en la app web.
- La conversación tiene alcance acotado: fecha por defecto Santiago, con reconocimiento de «ayer»; notas según el criterio reciente descrito arriba. No es un asistente abierto.
- El teléfono de transporte y contact_name no llegan a TrainingService ni a logs. La limpieza de texto elimina patrones de contacto, pero no constituye anonimización exhaustiva de contenido libre o de fotos del atleta.
- La semántica de notas se conserva internamente y se etiqueta en `adaptations`; el editor web previo no expone los metadatos tipados. No se reescribió ese contrato ni su UX.
- Permanecen las deprecaciones anteriores de FastAPI/Starlette y los cambios locales preexistentes sin commit. No se modificó el pipeline web de análisis de video ni su mecanismo de ejecución previo.

El único ajuste transaccional de TrainingService respondió a un defecto concreto: su commit obligatorio impedía guardar sesión, consumo de confirmación y outbox atómicamente. Se agregó `commit=False` para el canal durable; el default web conserva el comportamiento anterior. Se sumó la operación de notas propias y el soporte OGG/Opus; no se duplicó la lógica de interpretación, validación ni persistencia.

## 13. Bloqueos

No quedan bloqueos para cerrar las Fases 2 y 3 con mocks. No hay regresiones ni riesgo identificado sin mitigación que obligue a activar una STOP CONDITION. La conexión real a sandbox queda pendiente de credenciales y autorización operativa; no se solicitó ni utilizó ninguna credencial real esta noche.

El primer health de E2E no pudo acceder a localhost desde el entorno restringido. Se repitió con permiso de acceso al puerto local, sin cambiar código, y el E2E pasó. Las iteraciones fallidas previas de pruebas nuevas fueron ajustes de fixtures/expectativas antes del gate completo; ninguna suite completa falló.

## 14. Costos instrumentados

`whatsapp_usage` contabiliza inbound aceptado una sola vez, incluso antes de procesar; se asocia al atleta al resolverlo. Registra outbound aceptado por Kapso/FakeProvider, llamadas de media interpretada y bytes de descargas completadas por intento. Una retransmisión no duplica inbound. Las propuestas extensas pueden generar varios mensajes outbound, todos contabilizados.

La tarifa opcional outbound produce un estimado USD. Sin tarifa válida, `cost=null`: **no significa gratis**. Envíos inciertos pueden haber sido facturados y no se incluyen como aceptados hasta reconciliarlos. El ledger no pretende sustituir la factura Kapso.

Se reutiliza `TrainingAIUsage` para intentos, modelo, tokens reportados, duración de audio, latencia y estado de interpretación/transcripción, visibles en las estadísticas existentes. No se guarda prompt ni media allí. Es accounting compartido con la web: no hay atribución exclusiva al canal WhatsApp ni cálculo monetario por modelo. La transcripción fixture sin tokens conserva consumo desconocido; el test de interpretación verifica tokens reportados. No se estimaron precios reales ni se hicieron llamadas pagadas.

## 15. Siguiente fase propuesta

Primero validar el sandbox real y su operación con esta implementación, sin ampliar alcance. Después solicitar aprobación explícita para Fase 4. Si se aprueba compartir semana, mantener token opaco, hash, revocación, `no-store`, `noindex` y `Referrer-Policy: no-referrer`; agregar entonces `WEEKLY_SHARE_TOKEN_TTL_HOURS=168` para piloto. Esa variable y esos componentes **no fueron implementados** ahora.

## PARA GASTÓN MAÑANA

1. Revisar este informe y los commits locales `fecefaa`, `6528110` y `3e5c7fd`.
2. Mantener separados los 104 archivos preexistentes; no hacer merge/deploy todavía.
3. Crear credenciales y número **sandbox Kapso**, con webhook v2 y eventos received/sent/delivered/read/failed.
4. Generar/custodiar claves de cifrado y lookup; configurar sólo un entorno aislado y habilitar allí WhatsApp.
5. Aplicar migraciones hasta 0020 en la BD sandbox y arrancar API más worker con las mismas claves/storage.
6. Desde una cuenta atleta autenticada, generar código por `POST /api/whatsapp/link-challenges`, enviarlo por WhatsApp y verificar GET identity; probar también revocación.
7. Probar texto, foto, OGG/Opus y video reales, siempre con propuesta y confirmación antes de guardar.
8. Validar botones, doble confirmación, corrección/cancelación, restart, entrega/lectura y descarga de media con Kapso real.
9. Definir presupuesto/cuotas, tarifa outbound y procedimiento de revisión de FAILED/UNCERTAIN antes del piloto.
10. Autorizar explícitamente la siguiente fase cuando el sandbox esté aprobado; Fases 4/5/6 siguen pendientes.
