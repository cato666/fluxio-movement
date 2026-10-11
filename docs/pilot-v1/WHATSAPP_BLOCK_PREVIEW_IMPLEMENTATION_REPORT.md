# Corrección acotada: vista previa de bloques en WhatsApp

## Problema y cambio

Una fotografía real produjo tres bloques estructurados, pero `propose` mostraba únicamente `workout`, un aviso genérico de legibilidad. El atleta no podía revisar la programación extraída antes de Guardar.

La propuesta conserva su resumen e incluye, en orden, títulos de bloques, prescripciones y movimientos con sus dosis. Conserva literalmente incertidumbres y preguntas, resultados, adaptaciones, RPE y acciones de confirmación. Sin bloques, la respuesta mantiene su formato anterior. El cambio no realiza nuevas llamadas IA ni modifica la extracción, cuotas, permisos, consentimiento o persistencia.

Archivos funcionales: `app/whatsapp/capture.py` (10 líneas añadidas), `tests/test_whatsapp_capture.py` (dos regresiones nuevas).

## Validación

- Python: PASS, 343/343 en diez archivos de pruebas WhatsApp/seguridad, incluyendo las dos nuevas regresiones; 136,07 segundos y tres advertencias de deprecación existentes. No representa una ejecución de la suite Python completa.
- JavaScript aplicable: PASS, 31/31 (vinculación, cuotas y UX de registro).
- Nuevas regresiones: fotografía simulada con resumen genérico y bloques legibles, revisión antes de guardar y persistencia exacta de bloques/foto; propuesta larga sin pérdida de detalles, preguntas y botones solo en el fragmento final.
- Migraciones: PASS en preparación desde cero de PostgreSQL desechable (alembic upgrade head); entorno y worker vacío PASS. Recursos propios de esta ejecución detenidos al finalizar, sin borrar imágenes, redes ni volúmenes.
- Diff/formato: PASS, solo la corrección y sus pruebas; sin cambios de finales de línea.
- Workspace original: PASS, 153 rutas verificadas, ninguna alterada.
- Repetición del canal real con candidato actualizado: SKIPPED en esta etapa; cero llamadas reales OpenAI/Kapso durante la corrección. Worker real pausado; su copia funcional anterior no fue actualizada automáticamente.

Entorno offline exclusivo: red nueva interna `fluxio-s05-e2e-net-cff595851298`, subnet `10.254.247.0/28`; PostgreSQL y almacenamiento tmpfs, sin puertos publicados ni conexiones a redes del producto. Base de pruebas `movement_test`, distinta de la base de la sesión WhatsApp. Evidencias: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-tpmb_lk3/`.

Recomendación: corrección técnica lista para revisión. Repetir fotografía y Guardar en el canal real requiere actualizar explícitamente la copia QA y comprobar cuotas antes de habilitar el worker; no se declara validación real del cambio.

## Riesgos y estado

La vista previa muestra lo que extrajo la IA; no certifica su exactitud. Permanecen ambigüedades de la foto y la clasificación del bloque B. La corrección no cambia prompts ni inventa movimientos/cargas/tiempos. Propuestas largas se fragmentan mediante el outbox existente; cada fragmento físico consume cuota y reserva. Se conserva orden y deduplicación existente.

No se incluyeron herramientas QA locales ni su checklist previo en este commit. No hubo push, merge, deploy, migraciones persistentes ni ampliación de alcance a otra fase.

Pilot permanece NO-GO: destino y restauración externa de respaldo, costos adicionales de video, paridad EasyPanel y validaciones completas de canales reales pendientes. El E2E integrado S05 ya validado permanece PASS; sharing por WhatsApp en el túnel exclusivo está BLOCKED por falta deliberada de PUBLIC_BASE_URL, no debe confundirse con ese E2E.

Commit: el commit independiente que incorpora este informe, la corrección y sus dos regresiones; hash informado en la entrega final.
