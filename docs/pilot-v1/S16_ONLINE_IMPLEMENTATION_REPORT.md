# S16 — Implementación online para revisión

2026-10-12. Rama codex/pilot-v1-stabilization; HEAD inicial 30d735b7e2e7118a5ebfeb5adcd86ba6f27187e0. Commit final: consultar git log -1 -- docs/pilot-v1/S16_ONLINE_IMPLEMENTATION_REPORT.md.

## Cambio

Publicación atómica sin overwrite de fotos, originales/derivados de video y thumbnails; fsync y archivos privados. Referencias de upload no se commit antes de finalizar el archivo. Tras rollback, una consulta independiente y fence permiten limpiar solo fotos sin referencia comprometida; commit incierto o captura activa conserva bytes para conciliación. GC usa fence SQL no bloqueante y revisa todos los propietarios de referencias; originales compartidos se conservan.

Collector online opt-in: fence antes de snapshot exportado, referencias del mismo snapshot usado por pg_dump, copia y hash de todas las generaciones requeridas; faltantes/mutación/path inseguro/schema no certificado abortan. Offline conserva sus controles. Restore valida referencias SQL restauradas frente al manifest y archivos. R2, AES-256-GCM/key_id/KeePassXC, Telegram y scheduler reutilizados; sin receptor SQLite, cambios deportivos o migraciones nuevas.

## Validación

- PASS: 117 pruebas backup/alertas (33 existentes, nueve online y 75 regresiones); sin red/proveedores.
- PASS: 77 JavaScript, incluidos fixtures UI locales; cero skipped.
- PASS: ejecución daily, pg_dump y pg_restore PostgreSQL real desechable con R2/Telegram simulados, mismo snapshot y cero referencias faltantes. Restore: 29 tablas, tres usuarios sintéticos, entrenamiento/foto/análisis/review, cuatro archivos con hashes idénticos y decodificación PNG/MP4. Carga foto/video y borrado concurrentes; tres webhooks texto/foto/audio firmados y sus duplicados aceptados sin duplicación en fuente.
- PASS: 32 regresiones finales publicación/GC/uploads/async en otra DB desechable, incluidas 14 pruebas nuevas de inmutabilidad, rollback incierto y originales compartidos.
- PASS: suite Python completa, 951 passed / 0 failed / 1 SKIPPED (PUBLIC_BASE_URL real no configurado; dominio no certificado).

Evidencia final de restore: S16_ONLINE_VALIDATION.json y directorio temporal fluxio-s16-runner-integration-ljf2ttjf. Iteraciones anteriores detectaron fixtures inválidas, diferencias de hashes/entorno y regresiones de error SQL/rollback de imagen; estas últimas se corrigieron manteniendo sus tests originales. Se conservaron constraints y guardas. No se utilizaron fallos de entorno para marcar resultados PASS. Workspace original: 153 fingerprints iguales; status previo difiere por configuración del usuario, no escrituras de esta entrega.

## Límites y activación

Config inicial sigue offline y flags false. Online solo después de verificar versión idéntica API/worker, todos los escritores bajo protocolo, ruta lógica STORAGE_PATH, rol SELECT, grupo privado de lectura, capacidad y ausencia de DDL/deploy simultáneo. Archivos huérfanos/temporales no son el set de referencias; datos legacy faltantes bloquean captura. GC diferido y errores inciertos pueden retener bytes privados: conciliación S11 y límites de disco se mantienen.

S16 operativo BLOCKED / Pilot A NO-GO: faltan ensayo representativo real, alerta integrada/automatización autorizadas, configuración/paridad EasyPanel y gates del piloto. Backup periódico conserva RPO: no elimina pérdida de eventos posteriores al snapshot ante desastre ni justifica reenviar outbox incierto. Sin push/merge/deploy/proveedores reales/infraestructura persistente/scheduler.
