# S09 — Consumo correcto y liberación de reservas

Fecha: 2026-10-11. Rama: `codex/pilot-v1-stabilization`. Base: `f1a8bf47c92dbdb7079470a2f42b0d92f2d18e55` (S08 verificada). Estado: cierre técnico local PASS; no habilita el piloto.

## Comportamiento anterior y cambio mínimo

La preparación nativa de audio y ciertos errores locales ocurrían después de reservar y marcar STARTED. Un fallo de interpretación posterior a una transcripción exitosa tampoco reutilizaba el texto en el siguiente evento. S09 separa preparación y llamada sin reconstruir S06.

- Texto/foto: validar payload y propiedad antes de reservar; comprobar cuenta activa, habilitación, cuota mensual y disponibilidad nativa. Construir el request y marcar STARTED inmediatamente antes del adaptador externo.
- Audio: comprobar formato, tamaño, duración y decodificación local antes de reservar. Preparar una sola vez; transcripción e interpretación mantienen reservas independientes. El callback previo al transporte permite distinguir preparación local fallida de una llamada iniciada.
- WhatsApp: comprobar habilitación antes de reservar/descargar. Una descarga iniciada constituye costo desconocido y nunca acredita un reembolso. El resultado exitoso de audio se reutiliza únicamente para la misma referencia dentro del estado cifrado existente; TTL y purga anteriores no se amplían.
- Kapso: preparación pura del envío (configuración, URL, payload/acciones) antes de reservar. El transporte y su clasificación 402/429/UNCERTAIN de S08 no cambian.
- Video: validar extensión/tamaño y metadatos antes de consumir. Una falla posterior a comenzar almacenamiento/cómputo no demuestra ausencia de costo; sus reservas conservadoras permanecen. No certifica costos reales adicionales.

## Contrato y concurrencia

Estados persistentes existentes: RESERVED, CONFIRMED, RELEASED, UNCERTAIN; STARTED se registra en started_at. RELEASED exige prueba explícita de ausencia de llamada y started_at vacío. Repetir esa liberación es idempotente; no reabre una request_key liberada. Una operación nueva usa una nueva clave y respeta cuotas/presupuesto. Las reservas ya iniciadas, confirmadas o inciertas no se liberan por clase de excepción.

Se conserva el advisory lock global y los bloqueos de usuario de S06. Los proveedores inyectados no ofrecen evidencia interna de preparación: se consideran iniciados antes de invocarlos. Timeouts, resultados inválidos posteriores y descargas de costo desconocido mantienen UNCERTAIN. No se cambian límites, políticas de 402/429, privacidad, shares ni recuperación de S08. Los errores genéricos de interpretación ya no trasladan mensajes privados del proveedor al atleta.

El cache de audio utiliza únicamente ConversationState cifrado y su ciclo de vida vigente. No archiva audio ni crea un almacenamiento paralelo de transcripciones. No promete recuperar un resultado si el proceso termina antes de guardar el contexto: el contrato idempotente evita volver a llamar automáticamente con la misma reserva.

## Archivos

`app/main.py`; `app/services/consumption_limits.py`; `app/services/training_service.py`; `app/services/training_transcription.py`; `app/services/workout_interpretation.py`; `app/whatsapp/capture.py`; `app/whatsapp/media.py`; `app/whatsapp/kapso.py`; `app/whatsapp/queue.py`; `tests/test_consumption_limits.py`; `tests/test_consumption_preflight.py`.

Sin migraciones nuevas ni dependencias añadidas. Head Alembic permanece `0023_consumption_reservations`. Contratos públicos y firmas previas compatibles; los callbacks/preflight son opcionales internos.

## Validación

Resultado final: **769 Python PASS / 0 FAIL / 0 ERROR / 0 SKIPPED**, 233,52 s; **66 dirigidas S09/S08 PASS**, 20,05 s; **69 JavaScript PASS / 0 FAIL / 0 SKIPPED** (suite completa ejecutada durante S09; ningún cambio JS posterior). Las pruebas dirigidas se incluyen en la completa, no se suman. Sintaxis de 42 módulos y head único Alembic PASS. XML final y resumen analizado conservados; ejecuciones intermedias no certifican el código final. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s09-validation-20261011/`. Fuente comparada por SHA-256: 186 archivos, cero discrepancias entre candidato y runner.

Entorno: PostgreSQL 17.6 en tmpfs, base exclusivamente movement_test y reset habilitado; almacenamiento /tmp/s05-storage. Runner aislado en la red interna existente, sin puertos publicados ni redes añadidas. OpenAI/Kapso simulados; cero consumos reales. Las suites completas incluyen regresiones S02–S08, contratos, migraciones y biomecánica soportada.

Incidencias resueltas durante validación: fixtures antiguas esperaban una reserva para proveedor deshabilitado; se actualizó al contrato preflight sin reserva. Un WAV parametrizado generó un nombre pytest demasiado largo; se asignaron IDs cortos. Se mantuvo la prioridad de rechazo de cuota mensual sobre proveedor deshabilitado tras detectar una regresión en administración. No se omitieron casos para obtener PASS. Un comando dirigido inicial usó un nombre de archivo inexistente y no ejecutó casos; se corrigió a test_whatsapp_delivery_operations.py.

## Gates y riesgos

- BLOCKED: E2E integrado navegador/servidor S05; pruebas simuladas de UI y TestClient no lo certifican.
- PENDIENTE: control real de costos adicionales de video.
- PENDIENTE: paridad y validaciones EasyPanel.
- PENDIENTE: validaciones de proveedores reales.
- PENDIENTE: respaldo/restauración del destino.
- Decodificar audio inválido consume CPU local, aunque no cuota IA; no equivale a certificación de costos de infraestructura.
- Cache condicionado a referencia y contexto vigente; sin garantía de recuperación de resultado no persistido ante terminación abrupta.

Workspace original: huellas de 153 archivos y estado/HEAD sin diferencias. Escaneo de selección sin patrones de credenciales ni archivos locales; no constituye garantía absoluta. Artefactos JS movidos y conservados fuera del candidato. Sin push/merge/deploy, migraciones persistentes, cuentas reales, limpieza de datos ni proveedores reales.

Commit funcional: `1d739a86e73d9d1cc5e0c89d80eb809c699f03be`. El commit documental de entrega se identifica con git log para este reporte. Recomiendo cierre técnico local S09; cumple pruebas obligatorias ejecutables y permite continuar S10 conforme a la autorización secuencial. Pilot permanece NO-GO.
