# S11 — Entrega parcial segura; cierre BLOCKED por S16

Fecha: 2026-10-11. Rama `codex/pilot-v1-stabilization`. Base `ee94abb9038d38e4b3c8eb179250e27d49945eb8`. Política S11/S16 aprobada expresamente por «Si». **No se declara S11 completada. Pilot NO-GO.**

## Comportamiento anterior y cambio mínimo

El worker eliminaba una foto WhatsApp al vencer media.expires_at si no encontraba TrainingSession.source_image_id. No comprobaba todos los contextos activos y ejecutaba unlink antes del commit. La antigüedad del medio no prueba 24 horas de orfandad. La aprobación exige ejecución inicial dry-run y respaldo/restore antes de limpieza efectiva.

Ahora cleanup conserva todas las filas y archivos clasificados como imagen o ubicados en training-images/, incluso vencidos o cancelados. No elimina TrainingImage ni WhatsAppMedia de fotografías. La expiración existente de contexto/inbox/outbox sigue funcionando; el flujo de video previo queda fuera de este cambio. El resguardo es incondicional: ninguna variable puede activar borrado sin implementar y validar la dependencia.

Nuevo `app/services/photo_retention.py`: inventario interno read-only de TrainingImage; identificadores internos y códigos/conteos, sin rutas, contenido, teléfonos, tokens o atleta. Comprueba referencias de sesiones, WhatsAppMedia y contextos vigentes. Conserva de forma conservadora todas las fotos del atleta si existe contexto vigente, incluso indescifrable; no descifra payloads. Las semanas compartidas vivas derivan fotos de sesiones ya protegidas; no crea ni amplía acceso público. S02/S05 conservan denegación pública de cuentas inactivas/enlaces revocados/expirados.

Solo nombres normalizados UUID.jpg coincidentes con TrainingImage son conocidos; paths legacy, faltantes y symlinks se clasifican para revisión. No enumera ni elimina archivos sin fila DB. Una observación sin referencias **no equivale a archivo elegible**: no persiste reloj de orfandad ni decisiones de cuarentena. Sin autoflush ni commit. Resultado snapshot no autoriza una limpieza concurrente posterior. No se añade endpoint público, dependencia, migración ni arquitectura nueva.

## Archivos

- app/whatsapp/worker.py: bloqueo de eliminación de fotos y retirada de rama destructiva anterior.
- app/services/photo_retention.py: inventario conservador interno sin efectos de escritura.
- tests/test_photo_retention.py: ocho casos sintéticos de conservación, contexto, ambigüedad, lectura pura y fallo de commit.
- tests/test_whatsapp_capture.py: dos expectativas de limpieza actualizadas a conservación dry-run aprobada; no se eliminan las verificaciones de captura/guardar/privacidad.
- Documentos de política, manifiesto, readiness, backlog, test plan, Go/No-Go, matriz y consolidado: aprobación registrada y cierre pendiente explícito. Historia anterior identificada como tal.

## Pruebas y evidencia

Entorno: PostgreSQL 17.6 movement_test, PGDATA tmpfs sin mounts persistentes; runner existente con red Internal=true y ningún puerto publicado. Solo contenedores de prueba propios arrancados. Alembic desde cero hasta 0024 ejecutado por fixture exclusivamente en base desechable. Proveedores simulados, sin OpenAI/Kapso reales.

| Verificación | Resultado |
|---|---|
| S11 + captura WhatsApp | PASS: 44 pruebas; 0 FAIL / 0 ERROR / 0 SKIPPED |
| Python completa, regresiones previas y biomecánica | PASS: 795; 0 FAIL / 0 ERROR / 0 SKIPPED; 249.13 s |
| JavaScript completa | PASS: 72; 0 FAIL / 0 SKIPPED / 0 CANCELLED; 26.843 s |
| Workspace original | PASS: 153 paths sin cambio, estado Git/HEAD/rama conservados |
| Cuarentena/recovery 7 días, reloj durable 24 h y limpieza configurable | BLOCKED: no implementados ni ejecutados; requieren S16 |
| Backup/restore coherente y evidencia destino | BLOCKED; política aprobada no sustituye prueba |
| E2E integrado S05 | BLOCKED; ninguna ejecución nueva integrada navegador/servidor |

44 dirigidas son un subconjunto de la suite completa; no sumar. Tres warnings históricos de deprecación FastAPI/Starlette. Evidencia externa: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s11-validation-20261011/targeted.xml`; `full.xml` y `summary.json` conservados. Artefactos JS sintéticos conservados fuera del candidato.

## Riesgos, compatibilidad y parada

Sin cambios de modelos, contratos HTTP ni revisión de migración: head 0024. No elimina cuentas ni enlaces históricos ni archivos reales. Fotos huérfanas permanecerán mientras el modo efectivo esté bloqueado: crecimiento de almacenamiento pendiente de observabilidad/S12 y operación. El inventario protege por exceso y no puede demostrar elegibilidad tras carreras; antes de cuarentena se necesitan locks, revalidación y journal durable recuperable, no una bandera «backup verified». Limpieza previa de video permanece fuera de S11 y no queda certificada con este cambio.

Pendientes S11: parametrización validada de política, primera observación durable, cuarentena reversible, restore de DB+archivos+claves y pruebas de referencias múltiples/carreras/reanudación/recuperación. No se declara PASS de esos escenarios por preservar todos los archivos.

Para resolver S16 hace falta definir destino privado cifrado y responsable de respaldo/restauración, preparar ensayo coherente aislado DB+storage+claves, hashes/compatibilidad y medir recuperación. S16 además depende de S14; su preparación no es su cierre. No se inventan destino, responsable o evidencia. Conforme a la regla del encargo «Detente inmediatamente cuando exista ... Una dependencia bloqueada», no se inicia S12 ni otra fase.

Gates heredados: E2E S05 BLOCKED; costos adicionales reales video PENDIENTE; paridad EasyPanel PENDIENTE; proveedores reales PENDIENTE; backup/restore del destino PENDIENTE. Ningún resultado local autoriza publicación.

Commit funcional: `a4aefd7726a5d6f5f9b5c454bca16192ce0fe62d`. AST de cuatro fuentes PASS; hashes del runner coincidentes; diff --check PASS. Scanner limitado de patrones sobre 284 archivos rastreados sin coincidencias de credenciales/artefactos; no sustituye auditoría integral de secretos. Contenedores de prueba propios detenidos al finalizar. Commit documental: consultar git log -1 -- docs/pilot-v1/S11_IMPLEMENTATION_REPORT.md. Recomendación: revisar esta entrega parcial y resolver evidencia/dependencia S16 antes de cerrar S11. Sin push, merge, deploy, migraciones persistentes o modificaciones del workspace original.
