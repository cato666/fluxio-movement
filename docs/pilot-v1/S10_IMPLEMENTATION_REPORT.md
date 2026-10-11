# S10 — Integridad del registro de entrenamientos

Fecha: 2026-10-11. Rama `codex/pilot-v1-stabilization`. Base de reanudación `213fb793bfde0d4a9cb4d648fc28cf0d722ed8e1`; autorización expresa del usuario después de la parada de reproducción. **Estado: cierre técnico local PASS, no habilita publicación.**

## Defectos reproducidos y corrección

La ejecución anterior demostró tres FAIL/P1: campos omitidos se sobrescribían con defaults, notas desaparecían del registro visible y el replay de POST con una clave generaba dos sesiones. No se intervino sobre datos reales. Reproducción previa conservada en C:/Users/desarrollo/AppData/Local/Temp/fluxio-s10-validation-20261011/.

- Edición: _assign usa exclude_unset solo para update. Los campos opcionales omitidos se conservan; null, texto vacío y [] explícitos mantienen su semántica de limpieza. Campos obligatorios y propiedad de imagen/análisis conservan el contrato. Update y delete bloquean la fila y refrescan su estado; append de notas también refresca después de bloquear para evitar perder notas por una instancia stale.
- Web: envía los campos obligatorios y solamente los opcionales modificados. Una nota WhatsApp añadida mientras el atleta edita otro campo no se reemplaza por el valor viejo reenviado automáticamente.
- Creación web: Idempotency-Key UUID opcional; mismo atleta/clave/payload normalizado retorna la sesión actual sin insert/update. Otro payload devuelve 409; sesión eliminada devuelve 404, nunca se recrea por replay. UUID malformado lo rechaza el contrato HTTP. Usuarios distintos no comparten espacio de claves.
- Web genera una clave por formulario y la conserva ante respuesta perdida/error. Si un intento pudo haberse guardado, modificar el borrador no inventa una clave nueva; un conflicto indica revisar bitácora y mantiene el borrador. Una captura nueva tiene una clave nueva.
- WhatsApp: mantiene su confirmación atómica por identidad/estado/versión/token y la purga existente; no se reconstruye el flujo ni se cambian consentimiento, cuotas o outbox.

## Idempotencia y migración

Tabla aditiva training_save_requests: athlete_id y request_key como PK compuesta, session_id, payload_hash y created_at. No almacena texto, fotografías, audio, teléfono ni respuesta de proveedor. La huella SHA-256 incluye atleta/clave y JSON normalizado; no se imprime en logs. No convierte el registro manual en una operación facturable.

El bloqueo existente de cuenta activa FOR NO KEY UPDATE serializa guardados keyed del atleta. La sesión y la evidencia se guardan en una sola transacción; un fallo de commit/validación revierte ambas. La tabla conserva evidencia al eliminar: session_id carece deliberadamente de FK a la sesión para impedir resurrección. No hay TTL/limpieza automática del ledger; su retención no se decide eliminando protección de replay.

Migración `0024_training_save_requests`, padre `0023_consumption_reservations`. Únicamente crea una tabla; no reescribe usuarios, notas, sesiones ni medios históricos. Se probó desde cero y 0023 con una sesión histórica intacta, además del check de drift. Ninguna migración persistente.

Compatibilidad: POST sin clave conserva contrato legacy, cada petición constituye un nuevo registro; no es posible distinguir una repetición accidental de dos entrenamientos iguales sin identificador. WhatsApp usa su identidad de acción vigente. JSON de sesiones no agrega campos públicos. PUT sigue exigiendo trained_on/title/workout; su omisión opcional conserva datos. La edición explícita de un campo sigue reemplazándolo; los clientes externos que reenvíen todo el payload deben hacerlo deliberadamente.

El campo visible canónico de notas sigue siendo adaptations, empleado por detalle y semana; athlete_notes conserva la evidencia histórica previa y no se agrega al resumen público. Editar explícitamente adaptations actualiza la vista; no se borran notas históricas ni se modifica política S05.

## Archivos modificados

app/models.py; app/services/training_errors.py; app/services/training_service.py; app/training.py; app/static/training.js; migrations/versions/0024_training_save_requests.py; tests/test_training_integrity.py; tests/training-ux.test.cjs; tests/test_whatsapp_contracts.py.

## Pruebas y resultados

| Ejecución final | PASS | FAIL | ERROR | SKIPPED |
|---|---:|---:|---:|---:|
| Python completa, 238,01 s | 787 | 0 | 0 | 0 |
| Dirigidas integridad/CRUD/migración/WhatsApp | 89 | 0 | 0 | 0 |
| Contratos/migración dirigidos | 2 | 0 | 0 | 0 |
| Nota web/chat y semana adicional | 1 | 0 | 0 | 0 |
| JavaScript completa final, 24,63 s | 72 | 0 | 0 | 0 |

Dirigidas incluidas en la completa: no sumar. Las tres reproducciones originales ahora PASS dentro de tests/test_training_integrity.py. Regresiones S02–S09 y biomecánica existente incluidas. La última corrección fue exclusivamente JS (copia inmutable para comparar arrays): no se modificaron fuentes Python después de su PASS; se repitió JavaScript completo sobre la versión final. Código JS final sincronizado al runner para la comparación de fuentes. E2E integrado navegador/servidor S05 permanece BLOCKED; proveedores y destino NOT RUN/PENDIENTE.

Casos nuevos: tres reproducciones originales; replay desde otro proceso; dos guardados concurrentes reales; conflicto/delete/tombstone; separación por atleta/legacy; validación y commit fallidos; foto/blocks/video_links omitidos y limpieza explícita; edición inválida conserva todo; instancia stale/notas concurrentes; inactividad/replay; evidencia sin contenido; manual sin presupuesto/proveedores; migration 0023→0024/legacy; delete conserva medio/foto; consistencia de notas web/chat/detalle/semana. UI: clave estable al fallar, conflicto de contenido conserva borrador, campos opcionales sin cambios no se reenvían y cambios explícitos en arrays anidados/video se comparan contra una copia inicial inmutable.

Entorno: PostgreSQL 17.6, movement_test tmpfs sin mounts persistentes, reset explícito solo de fixtures; storage temporal; runner propio y red interna existente sin puertos publicados/redes añadidas. Proveedores simulados y claves reales vacías. Evidencia final en C:/Users/desarrollo/AppData/Local/Temp/fluxio-s10-final-validation-20261011/; capturas JS fuera del candidato en fluxio-s10-js-evidence-20261011/ y fluxio-s10-js-final-evidence-20261011/. Fuente ejecutada/candidato: 188 hashes iguales. Sintaxis de 42 módulos PASS.

Incidencia de preparación resuelta: la prueba nueva de medios importaba una fixture con nombre inexistente; se corrigió al helper/modelo existente. La revisión de diff corrigió una recodificación local de cadenas y conservó exactamente los textos UTF-8 originales antes de probar; no se cambió copy de producto para esta fase. La primera suite completa tuvo un FAIL de contrato al detectar la nueva cabecera opcional; se añadió únicamente create a la allowlist existente y se exigió exactamente UUID/null opcional. El resto del OpenAPI sigue comparándose íntegramente, sin reemplazar la baseline. No se omitieron pruebas.

## Riesgos y gates

- La nueva aplicación exige la migración 0024 antes de utilizar guardados con clave; falta comprobar esquema/configuración/digest del destino. No se aplicó en EasyPanel.
- No ejecutar downgrade sobre producto: perdería evidencia de idempotencia. Rollback requiere un bundle de migraciones compatible con 0024; un binario anterior sin esa revisión puede fallar en el script de arranque. Ensayo y respaldo corresponden a S14/S16, pendientes.
- Formularios nuevos y clientes legacy sin clave pueden registrar contenido igual deliberadamente. No se deduplican datos existentes por texto/fecha, ni se cambia silenciosamente ese contrato.
- Claves/evidencia persistentes crecen con guardados keyed, incluidos tombstones; no se eliminan por un TTL arbitrario.
- Pruebas con API simulada no cierran E2E integrado S05.
- Costos adicionales reales de video, paridad EasyPanel, proveedores reales y backup/restore del destino permanecen pendientes, junto con E2E S05 BLOCKED. Pilot **NO-GO**.

Workspace original intacto: 153 huellas y estado Git sin diferencias. Selección/secretos sin hallazgos de patrones; no garantía absoluta. Sin push, merge, deploy, proveedores/cuentas reales ni acciones sobre bases/archivos persistentes.

Commit funcional: `09b4215f5b1aec1e44e77f67e42360ecedfd373c`. Commit documental identificable mediante git log de este reporte. Recomendación: aceptar cierre técnico S10 y continuar exclusivamente al análisis S11 conforme a la autorización secuencial; no implementar borrado/retención sin política del propietario y sin resolver dependencia S16.
