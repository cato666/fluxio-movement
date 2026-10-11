## Actualización S16 — 2026-10-11

Gastón confirmado como operador. Ensayo R2 sintético **PASS**: AES-256-GCM cliente, upload/download autenticados, DB nueva y cuatro archivos restaurados con hashes/referencias iguales; 3 usuarios, 1 sesión/foto/análisis/review, head 0024. Contenedores propios detenidos. 5,31 s y 92.197 bytes corresponden a muestra pequeña, no RTO operativo. Primer intento falló por expectativa HTTP anónima (400); corrección del harness y repetición aislada documentadas. Privacidad por dominios/r2.dev, configuración de cifrado proveedor, permisos separados, custodia definitiva, restore representativo del producto, scheduler y alertas **pendientes**. S16 sigue parcial y **NO-GO**, sin habilitar limpieza S11. Ver [reporte S16](S16_IMPLEMENTATION_REPORT.md).

# Estado vigente — cierre final Pilot A

Validación local final del candidato `03cfd4387a75f70fae60ccd2108a83d24dc57f31`: Python **820 PASS, 1 SKIPPED, 0 FAIL** (257,41 s); JavaScript **77 PASS, 0 FAIL/SKIPPED**. La prueba omitida requiere WEEKLY_RELEASE_PUBLIC_BASE_URL real y queda **NOT RUN**, sin afirmar paridad de dominio. PostgreSQL nuevo tmpfs, red interna nueva, sin puertos Docker publicados ni credenciales de proveedores; migraciones desde cero y worker vacío PASS; contenedores propios detenidos. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-2e4m_dlq/offline-tests.log` y `environment.json`. Tres advertencias de deprecación no bloquean estas pruebas. Workspace original: 153 rutas verificadas sin cambios.

Fecha: 2026-10-11, America/Santiago. Rama: codex/pilot-v1-stabilization. Candidato auditado: `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. **Pilot A NO-GO**. Alcance obligatorio: bitácora + WhatsApp + video certificado + coach titular/suplente, 3–5 atletas, 30 días. Esta entrega no autoriza proveedores, infraestructura persistente ni publicación.

Estados: PASS = evidencia ejecutada y limitada a su entorno; FAIL = defecto/evaluación fallida demostrada; BLOCKED = falta autorización, acceso, responsable o dependencia; NOT RUN = sin ejecución. Resultados históricos no certifican el candidato final ni el destino.

## Identidad vigente

Fuente auditada: 03cfd4387a75f70fae60ccd2108a83d24dc57f31. Rama codex/pilot-v1-stabilization; worktree independiente. Inventario SHA-256: PILOT_A_SOURCE_HASHES.json (141 archivos rastreados de app/migraciones/scripts y construcción). No incluye herramientas QA no rastreadas ni credenciales. Head Alembic: 0024_training_save_requests, padre 0023_consumption_reservations. Migración persistente NOT RUN.

Imagen final/digest/SBOM/scan/API-worker parity: NOT RUN. EasyPanel commit/digest/schema/config: BLOCKED. Metadatos del QA anterior contienen hash antiguo y worker_running=false; no certifican candidato 03cfd43. Cambios posteriores a S17 incluyen token semanal cifrado, script modal same-origin CSP, manifest/iconos y ajustes de resumen; claves de recuperación deberán ser iguales API/worker.

Archivos locales fuera de release: .impeccable/, docs/pilot-v1/WHATSAPP_SANDBOX_LOCAL_CHECKLIST.md, scripts/pilot_whatsapp_gateway.py, scripts/pilot_whatsapp_worker.py, scripts/test_whatsapp_pilot_preflight.py. No se eliminan ni se incorporan.

Consultar [readiness final](PILOT_A_FINAL_READINESS.md), [video](PILOT_A_VIDEO_CERTIFICATION.md), [WhatsApp](PILOT_A_WHATSAPP_VALIDATION.md) y [release](PILOT_A_RELEASE_PLAN.md).

---

## Evidencia histórica conservada — no sustituye estado vigente

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

# Manifiesto actual — candidato S10 / bloqueo S11

Fecha: 2026-10-11. **S10 cierre técnico local PASS; S11 auditada/BLOCKED por política de retención y dependencia S16. S12–S18 no iniciadas. Pilot NO-GO.** Código actual `09b4215f5b1aec1e44e77f67e42360ecedfd373c`, entrega S10 `023736b6429524f5d5cecbc2c8febe738157a9e1`. Los tres defectos P1 de S10 fueron corregidos y sus reproducciones ahora pasan; la parada anterior S10 fue superada mediante autorización expresa del usuario. El commit documental actual no implementa S11.

| Campo | Valor verificable |
|---|---|
| Rama | codex/pilot-v1-stabilization |
| Worktree | C:/Users/desarrollo/.codex/worktrees/pilot-v1-stabilization/fluxio-movement-mvp |
| Código final S10 | 09b4215f5b1aec1e44e77f67e42360ecedfd373c |
| Entrega S10 | 023736b6429524f5d5cecbc2c8febe738157a9e1 |
| Documentación de bloqueo S11 | Resolver git log -1 -- docs/pilot-v1/FINAL_STABILIZATION_REPORT.md; sin implementación funcional S11 |
| Alembic candidato | 0024_training_save_requests, padre 0023_consumption_reservations, head único |
| SQL destino | Desconocido; migración persistente no ejecutada |
| Imagen/digest final app y worker | PENDIENTE S14; imagen de tests no es artefacto de release certificado |
| Dependencias/modelo | Sin cambios S10; scan/identidad/precisión final pendientes S14/S18 |
| Fuente y validación | 188 hashes comparados; 787 Python/72 JS PASS |
| Reproducciones P1 S10 | Corregidas y PASS; registros reales sin intervención |
| Policy / backup | S11/S16 pendientes de aprobación y ensayo; nada de la propuesta está activo |
| Original | 153 huellas/status/HEAD intactos; artefactos JS preservados fuera del candidato |
| Operaciones reales | Sin push/merge/deploy, migraciones persistentes, proveedores, altas, redes/puertos nuevos |

## Checksums del delta funcional S10

| Archivo | SHA-256 |
|---|---|
| app/models.py | 012fe7463f6f475647db6cc7b28ebfd6db3d5b7c38f262b267abb08119ae1d1b |
| app/services/training_errors.py | 293abd68fb9ea0046e5a90c154086c37661fa196e27a02702565eb25720c5827 |
| app/services/training_service.py | f79cc2312b508623953042531f15c3f1394bb0fb693362ce80ee4c1f51ecd05f |
| app/static/training.js | af3c19d74018452dc0dabc3b15df554959ad706291504471cc819dd463413c56 |
| app/training.py | e6e4daf55b315d401c072c3d6dba94cb4dc427335a6e4c08d8adb11be14cfc4e |
| migrations/versions/0024_training_save_requests.py | a4ebe542b0fb6dbc6b09fe60807b0511afdf071a3f3c027961ee4ac36c24b894 |
| tests/test_training_integrity.py | 081491f29e5ec206a1145b4cf3bb951b8251e30cf877df8af70c9779e362356f |
| tests/test_whatsapp_contracts.py | 552f6859cc74b624e80868fcd41f7accbc09790919f576c72bd9ded1f91cb057 |
| tests/training-ux.test.cjs | 983953bc2aa91e6f7f7986aa1594408094edf219143e034f6a7c43c0d5c9c987 |

## Gates heredados

1. **BLOCKED:** E2E integrado navegador/servidor S05; no sustituido por API simulada/TestClient.
2. **PENDIENTE:** reserva/control de costos adicionales reales de video.
3. **PENDIENTE:** paridad de commit/digest/esquema/configuración/worker con EasyPanel.
4. **PENDIENTE:** validación de proveedores reales; gasto/envíos no autorizados.
5. **PENDIENTE:** backup y restauración del destino; prueba temporal no los certifica.

---

## Manifiesto S01 histórico (sin reemplazar evidencia)

# Manifiesto de candidato S01

Fecha: 2026-10-10, America/Santiago.
**MATERIALIZADO / VALIDACIÓN OBLIGATORIA BLOQUEADA / NO-GO**.

| Campo | Valor |
| --- | --- |
| Rama | codex/pilot-v1-stabilization |
| Base | 97583b5c191fd48d4282ad42d0b020d6cb1709a1 |
| Commit de código y selección | cb4d63c6d79d0983561560299658b7b1dbb3f13e |
| Commit final documental | Resolver git rev-parse HEAD; agrega los tres entregables, sin modificar el código del commit anterior. |
| Worktree | C:/Users/desarrollo/.codex/worktrees/pilot-v1-stabilization/fluxio-movement-mvp |
| Tag propuesto | v1.0.0-pilot.1-rc.1; no creado |
| Digest app/worker | No construido |
| Head de archivos migration | 0022_administration |
| Revisión SQL destino | Desconocida |
| JavaScript | 65 PASS / 0 FAIL / 0 SKIPPED; backend simulado |
| Python/PostgreSQL y biomecánica | BLOCKED / NOT RUN |
| Push/merge/deploy/altas reales | No realizados |
| OpenAI/Kapso reales | No utilizados |
| S02 | No iniciada |

## Hashes del candidato

SHA256 de bytes actuales. Hashes de origen en S01_SELECTION.json; seis parches fijan selección parcial.

| Archivo | SHA256 |
| --- | --- |
| README.md | e9b703dfded1820d76de4a2fc2de0bf0984ea628dc3bdbdae170b133f8c30777 |
| app/main.py | 85131c0183cbec94fff59bc3918b4b6ff172c44d04389a75f1cd193b32bdbfb1 |
| app/models.py | a1f4adefd6225f2952961e3bd920f08215197353b4159afbb9de11bb95e278ce |
| app/training.py | 791d39cd26e85bb19d66dfeecaf724dbba1bd7def4ff0b624928558f82b6858b |
| tests/test_basic_auth.py | dcb702bc7ab428618aa28117f23199274c618b3ca679cb62aacb81c1fce70350 |
| tests/test_whatsapp_contracts.py | d68ec033d4a0c1cc4b9139a46ae8ed99cbae908a1ac8d9a95c05f7989976f796 |
| app/administration.py | 094542024bd126c7e521f69366a82ed54b27abc91a0139ec145d1f040c022a33 |
| app/static/admin.js | e86f5772fe3a6e41b14197d2e874876daf407d489206f7b1db4406f1710d5b76 |
| app/static/admin.css | 53881d26ebf49a18fb6448508344126e5cd4b30f269ad3c30c2d4ef2849cd7ac |
| migrations/versions/0022_administration.py | 74c68f6292c1142ee44ed2fa0d98894cf9fd2eb13c13a89332b0e48ed26fe580 |
| tests/test_administration.py | 8fa07494a63567843795a893a322bc220cdbdf5c157d42d8447a9e256b54e079 |
| tests/test_delete_analysis.py | ab85e6a4e887623b9a35f975778dbcc8442fae04780cbb0396b3ce8841ac752c |
| tests/admin-ui.test.cjs | 720e2101ea448862f6bdbd299664df82cc704e08ae669151e836c1264d108485 |
| app/services/analyzer.py | 233f2abfa606d7837a9a67a3e9c3f2397c10fb5e34dc03ec8d6f8b0c881d68d6 |
| app/services/exercise_validation.py | 72b9f1e0e187c2db3aed1bf644804c79305f323d7936bb46dd531c4b11ad407c |
| app/static/app.js | 0668f8e0de00d186c846c665d8fb074a75346fccec96755214203ec08c770f64 |
| app/static/index.html | 80145b0eacb9d60c849fd1090f76584acaaa66e16a31ad2b330f6710c454b3d9 |
| tests/test_exercise_profiles.py | ad0ff077259f80477d7700853c3a92292e6409d960de863fefb5682614c1293a |
| tests/test_weekly_release_validation.py | 309f55a8db6d2249da0ae53fe21b9746c1def59acd0bea694c3516f835827f54 |

## Procedencia y límites

Sin nuevas dependencias ni migraciones adicionales a 0022. Alembic no ejecutado. start-app.sh migra y seed al arrancar: no usar contra datos existentes para validar. No se inició imagen de test por fallo Docker. No se sustituyó PostgreSQL por SQLite.

Sin .env reales, adjuntos, debug.log, Compose Kapso local, perfiles Lunge/Bulgarian ni herramientas/artefactos heredados en candidato. .env.example y defaults demo son plantillas/configuración insegura conocida para S04, no secretos productivos certificados. Escaneo por patrones sin matches no es garantía exhaustiva de ausencia de secretos.

Paridad EasyPanel pendiente: histórico 09-10 local67/remoto59, admin/account plan/DELETE analysis ausentes remoto entonces. DNS falló desde este entorno en inspección S01 previa. SHA/digest/schema/mounts/worker actuales no verificados. Sin acceso a datos privados.

Este manifiesto identifica un candidato local reproducible, no una release publicable.
