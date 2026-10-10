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
