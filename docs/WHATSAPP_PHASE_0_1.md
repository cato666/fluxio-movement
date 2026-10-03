# WhatsApp: entrega de Fases 0 y 1

Fecha: 2026-10-03. No se implementó Identity, Kapso ni ninguna parte de Fase 2.

## Baseline reproducible

- Commit inicial: `dc1a92395f0eba244ba41cf83e2acf46eee3f3ff`.
- Se conservaron los cambios locales existentes. Se registraron estado Git, diff binario y SHA256 de 104 archivos modificados/no versionados en `results/phase01/`. La comprobación final encontró cero alteraciones de esos archivos.
- PostgreSQL descartable: proyecto Docker `fluxio-phase01-tests`, servicio `db-test`, base `movement_test`, almacenamiento PostgreSQL en tmpfs. No se utilizó la base normal.
- Imagen de ejecución: `sha256:dd640b49d87662da8e7b05ac08522d8f2bfc0579613a792d193f9685dd069edc`, con el workspace montado para probar el código actual, no el código antiguo de la imagen.
- Python 3.11.14, Node 24.19.0, Playwright 1.62.1, FFmpeg 5.1.9. Dependencias Python completas registradas en `python-dependencies.txt`.
- Alembic antes y después: `0018_training_ai_usage (head)`, una sola cabeza; sin nuevas migraciones.

| Validación | Resultado |
| --- | --- |
| Python antes, sin cambios | 188 passed, 1 failed, 3 warnings; 109.35 s |
| JavaScript antes | 60 passed, 0 failed, 0 skipped; 19.681 s |
| Python baseline corregida, antes del refactor | 189 passed, 3 warnings; 100.61 s |
| Python específica tras refactor | 36 passed, 3 warnings; 22.03 s |
| Python completa tras refactor | 195 passed, 3 warnings; 108.11 s |
| JavaScript completa tras refactor | 60 passed, 0 failed, 0 skipped; 18.942 s |
| OpenAPI completo | Igualdad estructural exacta antes/después |
| E2E HTTP con Chromium | Todos los flujos aprobados, sin errores JavaScript |

El fallo inicial fue `test_internal_usage_aggregates_completed_runs`: la expectativa omitía `audio_seconds` y `transcription_runs`, campos que ya devolvía la API. Se actualizaron únicamente los valores esperados del test; no se cambió el endpoint ni se relajó la igualdad exacta.

Para repetir las validaciones desde el workspace:

```powershell
./scripts/test-phase01.ps1 -Stage after -PlaywrightModule 'RUTA/AL/MODULO/playwright'
```

El script inicia solo la base descartable, ejecuta Python y todos los `tests/*.test.cjs`, inicia el servidor E2E local con fixtures externos y elimina servidor/proyecto de tests al terminar. La imagen predeterminada es la imagen exacta registrada arriba. En otra máquina puede construirse el target `test` del Dockerfile y proporcionarse con `-TestImage`; la reconstrucción debe contrastarse con el inventario de dependencias registrado. Las etapas `before` y `baseline-green` ejecutan las suites sobre el árbol presente: no restauran automáticamente el estado inicial.

Evidencias locales: `results/phase01/python-before.log`, `python-baseline-green.log`, `python-targeted.log`, `python-after.log`, `javascript-before.log`, `javascript-after.log`, `e2e-after.log`, `openapi-before.json`, `openapi-after.json`, `alembic-before.txt`, `alembic-after.txt`, `preexisting-status.txt`, `preexisting.patch`, `preexisting-hashes.json`. Este directorio ya estaba ignorado por Git.

## Servicios extraídos y archivos

Arquitectura resultante: `Web → TrainingService → PostgreSQL / TrainingMediaStore / pipelines IA existentes`.

- `app/services/training_service.py`: creación, consulta, actualización, eliminación, comprobaciones de propiedad de sesión/imagen/análisis vinculado, persistencia, interpretación y transcripción con contabilidad existente. Recibe `athlete_id`, sin requests, cookies, teléfonos ni payloads del proveedor.
- `app/services/training_contracts.py`: `SessionPayload`, `InterpretPayload`, `VideoLink`; reutiliza los únicos `WorkoutBlock` y `WorkoutDraft` existentes. No se duplicaron esquemas ni prompts.
- `app/services/training_media.py`: pipeline existente de validación, reducción, conversión y almacenamiento de foto privada. La imagen se elimina si falla su persistencia.
- `app/services/training_errors.py`: errores independientes del canal.
- `app/training.py`: adapter HTTP delgado; conserva autorización, lectura acotada del multipart, rutas, respuestas y traducción de errores.
- `tests/test_training_service.py`: seis tests del uso directo del servicio, interoperabilidad con Web, aislamiento entre atletas, guardado explícito, validación y limpieza ante fallo.
- `tests/test_ai_reasoning.py`: corrección de expectativa preexistente de baseline.
- `tests/e2e/app.py`, `tests/e2e/phase01.cjs`: fixture aislado y recorrido de navegador con API/BD reales.
- `scripts/test-phase01.ps1`: ejecución reproducible y limpieza del entorno descartable.
- Este documento: baseline, alcance y propuesta de siguiente fase.

## Contratos preservados y límites de la validación

No cambiaron rutas HTTP, schemas OpenAPI, estados, mensajes de error, límites de carga, propiedad, permisos atleta/coach, modelos SQL, UI ni DESIGN.md. La lista sigue limitada a 200 registros. Los pipelines existentes de interpretación y transcripción son únicos y no guardan un entrenamiento por sí mismos. El audio sigue temporal y no se persiste. El pipeline de video técnico existente quedó intacto; la Bitácora conserva enlaces a análisis propios.

El E2E recorre texto con propuesta/confirmación/edición, foto con almacenamiento y acceso privado, audio real del navegador normalizado por FFmpeg, análisis persistido, solicitud de revisión, comentarios/completado del coach y feedback leído por atleta. Las respuestas externas de IA y la inferencia de pose son deterministas. No acredita una llamada real a OpenAI ni precisión biomecánica sobre un video de atleta. La suite Python sí incluye decodificación real de MP4 y rechazo por pose insuficiente, además de las pruebas del analizador y de persistencia/revisión existentes.

## Deuda técnica y riesgos para Fase 2

- Los recorders de consumo hacen commits internos. Se preservó esa semántica; una futura confirmación idempotente con inbox/outbox deberá coordinar transacciones sin envolver las llamadas IA en la transacción del guardado final.
- Procesamiento de video en BackgroundTasks y recuperación que marca trabajos interrumpidos como fallidos; todavía no hay worker durable para WhatsApp.
- Media actual usa rutas estables protegidas por autenticación; faltan URLs temporales firmadas para usos futuros.
- OGG/Opus no está soportado todavía por el validador de audio existente.
- Falta gateway central de sanitización; texto, voz y fotos pueden incluir datos personales.
- README tiene afirmaciones desactualizadas sobre autenticación y procesamiento síncrono.
- Tres warnings de deprecación: portal AnyIO y startup `on_event` de FastAPI.
- TrainingService supone que el caller ya autenticó/verificó al atleta. Identity deberá resolver exclusivamente asociaciones verificadas; nunca tomar `athlete_id` de texto del remitente.

## Propuesta exacta para iniciar Identity + Kapso

1. Migración aditiva para `athlete_identity` y desafíos de vinculación, con teléfono normalizado cifrado y HMAC único de identidades activas; vinculación mediante usuario autenticado y código de un solo uso enviado desde WhatsApp. Desvinculación y expiración incluidas.
2. Contratos internos de mensajes/media/estados y `WhatsAppProvider`; una sola implementación concreta, `KapsoWhatsAppProvider`.
3. Variables Kapso, flag desactivado por defecto y endpoint firmado `POST /webhooks/whatsapp/kapso`, con aceptación durable, deduplicación por mensaje, procesamiento recuperable y logs minimizados.
4. Inbox/outbox, estado mínimo con TTL y serialización por atleta; empezar con identidad y `help`, validar sandbox antes de habilitar registro.
5. Registrar consumo de mensajes y fallos; conectar flujos posteriores exclusivamente con TrainingService. Sin HTTP interno ni simulación de cookies.

Los ajustes aprobados quedan como requisitos posteriores, sin cambiar contratos en Fase 1:

- Notas personales: `adaptations` es Text y no admite metadatos tipados. Para distinguir `type=athlete_note` y `source=web|whatsapp|ai` sin mezclar adaptaciones, proponer una colección JSONB aditiva en `training_sessions`, sin tabla nueva; conservar `adaptations` y no reclasificar texto antiguo automáticamente. Su migración/contrato se concretará cuando se autorice implementar notas.
- Video WhatsApp: recibir y almacenar privado; pedir texto/audio cuando falte descripción. No inferir WOD desde biomecánica.
- Token semanal: `WEEKLY_SHARE_TOKEN_TTL_HOURS=168` inicialmente, hash, revocación, no-store, noindex y Referrer-Policy no-referrer. No implementado todavía.
