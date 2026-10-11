# Estado vigente — S17 cierre técnico local PASS, pendiente de revisión

Fecha: 2026-10-11. Base c5d1764 verificada, original intacto. S08–S10 cerradas localmente; S11 parcial; S16 preparación documental completada, validación operativa pendiente. S12/S13/S15/S18 conservan dependencias abiertas; S14 necesita build/identidad/scan local verificables. Se completó **solo S17** con mitigación explícita y recursos desechables existentes: **803 Python / 75 JavaScript PASS**; 57 dirigidas son subconjunto, no sumables; sin FAIL/ERROR/SKIPPED en la suite Python. El commit único se identifica mediante git log del reporte S17; no se repiten cierres anteriores. Auditoría completa, cambios y resultados en [reporte S17](S17_IMPLEMENTATION_REPORT.md).

Mitigación S17: límite de listado 200 conservado e informado, desempate estable; filas anteriores conservadas y consultables en resumen semanal/detalle privado. Registro manual permite superar 200, sin consumo IA. Sin paginación/exportador nuevo ni garantía de que toda cohorte permanecerá debajo de 200. No borrar para liberar historial; aviso operativo a 150 es propuesta, no automatismo certificado.

**NO-GO**: E2E integrado S05 BLOCKED; restauración real de respaldos PENDIENTE; costos adicionales de video PENDIENTE; paridad EasyPanel PENDIENTE; pruebas reales de canales habilitados PENDIENTE. S11/S16 no se cierran por resultados locales. Tras S17 se detiene para revisión, sin avanzar automáticamente. El texto siguiente conserva historia, no reemplaza este estado vigente.

---

# Actualización Pilot A — política de respaldo aprobada, ejecución deshabilitada

El propietario aprueba objetivo privado S3 compatible/Azure Blob independiente del VPS, AES-256/TLS, PostgreSQL+archivos privados, frecuencia diaria/predeploy, siete copias diarias y copia pre-release durante piloto, rol propietario técnico, restore aislado y credenciales mínimas/alertas. **Proveedor, bucket/contenedor y responsable operativo formal no confirmados.** Preparados [configuración inerte](BACKUP_CONFIGURATION.example.json), [procedimiento](BACKUP_RESTORE_RUNBOOK.md) y [reporte S16](S16_IMPLEMENTATION_REPORT.md). Sin job instalado, respaldo, restore, migración, deploy ni infraestructura persistente.

S16 preparación documental, cierre BLOCKED; S11 parcial, limpieza efectiva BLOCKED. El inventario/guard S11 sigue siendo código vigente. S12–S15/S17–S18 no iniciadas; S14/digest pendiente. Retención y objetivos están aprobados, no medidos. Pilot **NO-GO**: E2E S05, costos extra video, paridad EasyPanel, proveedores reales y backup/restore destino permanecen pendientes. La evidencia histórica siguiente no sustituye este estado vigente.

---

# Actualización vigente S11 — política aprobada, cierre bloqueado

Fecha: 2026-10-11. La respuesta «Si» aprueba la política S11/S16. S11 tiene una entrega **PARCIAL**: inventario read-only y bloqueo de eliminación de fotografías por el worker; no cuarentena ni borrado efectivo. Dependencia S16 **BLOCKED**: respaldo coherente/restore comprobado, destino y responsable pendientes. No usar una variable de configuración como sustituto de evidencia de recuperación. Sin migración nueva; head 0024 conservado. S12–S18 no iniciadas.

Entrega funcional parcial `a4aefd7726a5d6f5f9b5c454bca16192ce0fe62d`: 795 Python / 72 JavaScript PASS (44 dirigidas incluidas, no sumables). 0 FAIL / 0 ERROR / 0 SKIPPED en Python. Los resultados actuales y el commit funcional constan en [S11_IMPLEMENTATION_REPORT.md](S11_IMPLEMENTATION_REPORT.md). Conservados: E2E integrado S05 **BLOCKED**, costos adicionales reales de video **PENDIENTE**, paridad EasyPanel **PENDIENTE**, proveedores reales **PENDIENTE**, backup/restore del destino **PENDIENTE**. Pilot **NO-GO**. La política ya no está pendiente; la implementación efectiva y su dependencia sí.

El texto siguiente conserva evidencia histórica anterior a esta aprobación, no representa el estado vigente S11.

---

# Preparación vigente — S10 cerrada, política S11 pendiente

Fecha: 2026-10-11. **S10 cierre técnico local PASS; S11 auditada/BLOCKED por política de retención y dependencia S16. S12–S18 no iniciadas. Pilot NO-GO.** Código actual `09b4215f5b1aec1e44e77f67e42360ecedfd373c`, entrega S10 `023736b6429524f5d5cecbc2c8febe738157a9e1`. Los tres defectos P1 de S10 fueron corregidos y sus reproducciones ahora pasan; la parada anterior S10 fue superada mediante autorización expresa del usuario. El commit documental actual no implementa S11.

Listo para revisión técnica local: preservación de campos/notas, idempotencia durable por atleta, respuesta a replay sin duplicación y migración aditiva 0024; 787 Python/72 JS PASS, 188 fuentes verificadas, original intacto. No se deduplicaron ni repararon datos reales.

Bloqueo inmediato: falta política aprobada para fotos web huérfanas/cuarentena/legacy y dependencia S16. Riesgos de cleanup por contexto vigente y unlink antes del commit requieren ensayos/corrección S11; no se declara daño real. [Propuesta para decisión](S11_RETENTION_POLICY_PROPOSAL.md).

Orden: aprobar/ajustar retención y respaldo → preparar pruebas de dependencia S16 en entorno aislado → implementar/validar S11 sin borrado real → continuar secuencia si gates pasan. S12–S18 permanecen sin iniciar, no se eluden dependencias.

## Cinco gates heredados

1. **BLOCKED:** E2E integrado navegador/servidor S05; no sustituido por API simulada/TestClient.
2. **PENDIENTE:** reserva/control de costos adicionales reales de video.
3. **PENDIENTE:** paridad de commit/digest/esquema/configuración/worker con EasyPanel.
4. **PENDIENTE:** validación de proveedores reales; gasto/envíos no autorizados.
5. **PENDIENTE:** backup y restauración del destino; prueba temporal no los certifica.

[Consolidado parcial](FINAL_STABILIZATION_REPORT.md). A continuación se conserva la propuesta histórica del 10-10; no representa ejecución actual.

---

# Preparación de release y resumen ejecutivo

Fecha: 2026-10-10, America/Santiago. **NO-GO: plan completo sujeto a revisión; ninguna capacidad certificada hoy para publicación.**

## Qué está construido y qué evidencia existe

Manual, CRUD/historial, interpretación texto/foto, audio, WhatsApp, semanal/sharing y video/review humana tienen implementación. La auditoría del 09-10 reporta 85 tests Python dirigidos, 479 aprobados/1 omitido en suite completa, 65 JS aprobados, seis recorridos E2E y E2E semanal aprobados. Python utilizó PostgreSQL desechable; E2E web utilizó IA/pose fixture y FFmpeg/HTTP/DB reales. JS usa API simulada. WhatsApp con proveedores reales tiene evidencia histórica del 03-10, no certificación actual.

No se reejecutaron estas suites en esta fase documental. `tests/conftest.py` migra y TRUNCATE: exige `movement_test` y TEST_DATABASE_RESET=1; por eso nunca se debe ejecutar sobre una base persistente. Tests de persistencia prueban conexiones/roundtrips, no acreditan reinicios ni restore del destino.

| Función | Estado para piloto | Evidencia y pendiente |
| --- | --- | --- |
| Alta/login/manual/CRUD | Candidata con correcciones de seguridad | tests basic_auth, administration, training_sessions/service; E2E phase01 histórico; falta smoke de candidato y destino. |
| Texto/foto/audio | Candidata condicionada | training_interpretation/transcription/usage y E2E fixtures; falta calidad y fallos reales actuales, con autorización de gasto. |
| WhatsApp | Bloqueada | foundation/capture/contracts y sandbox histórico; cuenta activa, cuotas y sharing pendientes. |
| Semanal | Candidata | weekly_summary/release_validation y weekly E2E; validar fechas/muestra y destino exacto. |
| Sharing | Bloqueado por consentimiento | Token hasheado, TTL/revocación y fotos autorizadas construidos; creación automática en chat y alcance vivo. |
| Video | Candidata restringida | api/async_analysis/exercise_profiles/validation; precisión real y recuperación operativa no certificadas. |
| Coach | Condicionada | inbox/requests/annotations/complete_review; relación/permisos y capacidad humana pendientes. |

## Git y migraciones actuales

Rama `codex/bitacora-entrenamiento`, HEAD `97583b5c191fd48d4282ad42d0b020d6cb1709a1`. Árbol sucio: 39 archivos tracked modificados según diff --stat, incluyendo app/main.py, models.py, training.py, analyzer/exercise_validation/weekly_summary, UI y WhatsApp; además cambios en herramientas/skills y artefactos. Administración, tests de administración, migración 0022 y cuatro perfiles lunge/bulgarian_split_squat están sin seguimiento. Los ocho documentos product-audit también están sin seguimiento. No se hicieron commits, cambios de rama, staging ni limpieza.

Cadena estática 0001–0022 con head local `0022_administration`, descendiente de `0021_weekly_shares`; agrega is_active/plan/email/last_login y tablas administrativas. Head de archivos no equivale a revisión aplicada. `scripts/start-app.sh` ejecuta upgrade head y seed en cada arranque; iniciar candidato sobre datos persistentes ya implica migración. No se inició aquí.

## Local frente a EasyPanel

| Dimensión | Workspace actual | Destino |
| --- | --- | --- |
| Identidad | HEAD conocido + cambios sin commit | Commit, digest y rama no verificados. |
| Contrato | Auditoría 09-10: 67 paths en local 8000/8001; código admin y DELETE analysis presentes hoy | Histórico 09-10: 59 paths, admin/account-plan y DELETE analysis ausentes; semanal presente. |
| DB/storage/worker | Compose define volúmenes DB/storage compartido con worker | Revisión SQL, montaje real, claves y worker efectivo no verificados. |
| Estado vivo 10-10 | Inspección estática solamente | GET /health, /api/health y /openapi.json fallaron con “Host desconocido” desde este entorno. |

URL histórica: https://proyectos-fluxio-movement.sgnetm.easypanel.host. Fallo DNS local no demuestra caída del servicio. No hubo acceso al panel, login ni lectura privada. La comparación actual queda pendiente de export read-only del operador: commit/digest de app y worker, revisión Alembic aplicada, configuración redactada, rutas y mounts. Health ready compara con la versión instalada, no con este workspace.

## Defectos y riesgos

P0: exposición no autorizada o pérdida de datos activa/confirmada, secretos comprometidos o corrupción persistente: detiene activación y operación inmediatamente. **Ningún P0 confirmado en esta inspección.** P1: bloqueo de seguridad, privacidad, integridad o control operativo previo a publicación. P2: degradación acotada con mitigación verificada; no significa aceptación automática.

| ID | Severidad | Evidencia estática y efecto |
| --- | --- | --- |
| S02 | P1 | identity.resolve consulta identidad no revocada sin User.is_active; bypass de desactivación por chat inferido, no explotado. |
| S03 | P1 | GET coach/athletes lista todos; POST coach/analyses acepta atleta sin relación previa explícita. Riesgo de alcance excesivo; otras reviews/media sí tienen guards. |
| S04 | P1 | seed sobrescribe password_hash demo; Compose default demo1234 y fallback SESSION_SECRET en código. Configuración remota desconocida. |
| S05 | P1 | saved_week_link llamado después de Guardar crea enlace vivo; SharePayload web solo contiene day. Opt-in previo y evidencia deben cerrarse. |
| S06 | P1 | consume en adaptadores HTTP; captura/media WhatsApp llama servicio directo. No hay cuota transversal efectiva demostrada. |
| S07 | P1 | Login sin limitador explícito localizado; SameSite=lax sin protección CSRF/Origin uniforme demostrada. Explotabilidad no evaluada. |
| S08 | P1 | Kapso transforma 402 en provider_http_error genérico, no retry seguro; outbox FAILED. Falta señal operativa específica y ensayo de recuperación. No incidente real observado hoy. |
| S09 | P2 | Cuota web reservada antes de validación/proveedor; fallos consumen presupuesto. |
| S10 | P2 | Notas duplicadas en adaptations/athlete_notes; edición puede divergir. Guardado/replay debe verificarse antes de aceptación. |
| S11 | P2 | Fotos web no se eliminan al borrar sesión; limpieza WhatsApp depende del worker. Política/privacidad de retención debe aprobarse antes de altas. |
| S12 | P2 | Video BackgroundTasks no durable; inicio marca pendientes FAILED. No reanuda; requiere recuperación asistida sin perder originales. |
| S13–S16 | P1 | Sin evidencia actual de alertas, backup/restore, identidad de release ni gates CI. Workflow hace POST deploy en push main. |
| S17 | P2 | Historial limitado a 200; no paginado. Mitigación piloto debe demostrar que no oculta datos dentro de límites acordados. |
| S18 | P1 | Soporte video y disponibilidad coach requieren validación humana/capacidad; fixtures no certifican precisión. |

## Dependencias externas

PostgreSQL/volúmenes, EasyPanel/proxy/TLS/DNS, Kapso/webhook/red, OpenAI interpretación/transcripción/razonamiento, FFmpeg, MediaPipe/OpenCV/modelo pose y disponibilidad humana. requirements y constraints fijan versiones; Docker fija imagen base/Postgres y checksum pose. Build usa apt/pip y descarga modelo; reproducción exacta y vulnerabilidades de imagen no verificadas. No se consultaron tarifas ni se afirma ausencia de CVE. Predeploy requiere escaneo del digest elegido y comprobación de dependencias, sin actualización masiva.

## Qué corregir rápido y qué postergar

Cambios potencialmente pequeños: separar Guardar/Compartir, guard is_active por canal, fail-closed de secretos/seed demo, señal 402, gates de despliegue y manifiesto de release. No asumir esfuerzo trivial de permisos/cuotas: requieren definir contrato y probar concurrencia/replays. Postergar PR, progreso, deportes, pagos, red social, catálogo nuevo, cola durable/refactor grande y pulido visual no necesario.

## Orden exacto recomendado

1. Aprobar alcance, política de acceso/consentimiento, límites y responsables; esta aprobación permite preparar correcciones, no desplegar ni gastar.
2. S01: aislar candidato reproducible de cambios locales y comparar destino en lectura.
3. S04, S02, S03, S05, S07: cerrar seguridad y privacidad con pruebas dirigidas.
4. S06, S08, S09: límites/costos, 402 y reservas/reintentos.
5. S10, S11, S12, S17: integridad, retención y recuperación acotada.
6. S18 y S13: soporte video/coaches, observabilidad y operación.
7. S14, S15, S16: imagen/versiones, CI, backup y restore desechable; cerrar suite completa y E2E simulados.
8. Solicitar autorización concreta para pruebas reales acotadas con costo máximo; ejecutarlas y adjuntar evidencia.
9. Aprobar release exacta y autorización separada de deploy/migración/altas; ejecutar runbook y smoke del destino.
10. Activar 3 atletas; evaluar 72 h y ampliar a 10–15 solo si gates se cumplen; operar hasta día 30.
