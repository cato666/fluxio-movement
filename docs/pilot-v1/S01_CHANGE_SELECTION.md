# S01 — Selección materializada

Fecha: 2026-10-10, America/Santiago.
Rama: codex/pilot-v1-stabilization.
Base: 97583b5c191fd48d4282ad42d0b020d6cb1709a1.
Commit de implementación: cb4d63c6d79d0983561560299658b7b1dbb3f13e.
S02 no iniciada. Workspace original intacto.

## Reglas de selección

6 cambios rastreados completos, 24 archivos nuevos y 6 parciales; 117 cambios locales restantes no transferidos. Adicionalmente se retiraron 79 archivos de herramientas/artefactos ya heredados de HEAD solo del candidato, según la instrucción explícita de excluir herramientas y .impeccable. No se borraron del original.

S01_SELECTION.json fija rutas exactas y hashes SHA256 del origen. Los documentos de auditoría y costos conservan evidencia del workspace histórico, no describen literalmente el candidato filtrado ni certifican este commit.

## Cambios completos
- README.md
- app/main.py
- app/models.py
- app/training.py
- tests/test_basic_auth.py
- tests/test_whatsapp_contracts.py

## Archivos nuevos seleccionados
- app/administration.py
- app/static/admin.js
- app/static/admin.css
- migrations/versions/0022_administration.py
- tests/test_administration.py
- tests/test_delete_analysis.py
- tests/admin-ui.test.cjs
- docs/ADMINISTRACION.md
- docs/WHATSAPP_INTERACTION_COST_ANALYSIS.md
- docs/product-audit/01_FUNCTIONAL_INVENTORY.md
- docs/product-audit/02_CURRENT_USER_JOURNEYS.md
- docs/product-audit/03_TECHNICAL_ARCHITECTURE.md
- docs/product-audit/04_MULTISPORT_READINESS.md
- docs/product-audit/05_PRODUCT_GAPS.md
- docs/product-audit/06_FREE_PRO_READINESS.md
- docs/product-audit/07_PRODUCT_ROADMAP_PROPOSAL.md
- docs/product-audit/08_EXECUTIVE_SUMMARY.md
- docs/pilot-v1/DEPLOYMENT_RUNBOOK.md
- docs/pilot-v1/GO_NO_GO_CHECKLIST.md
- docs/pilot-v1/PILOT_OPERATIONS.md
- docs/pilot-v1/PILOT_SCOPE.md
- docs/pilot-v1/RELEASE_READINESS.md
- docs/pilot-v1/STABILIZATION_BACKLOG.md
- docs/pilot-v1/TEST_PLAN.md

## Parches parciales

Cada patch se generó contra el archivo de HEAD, pasó git apply --check, se aplicó y pasó git apply --reverse --check. No se transfirió el archivo mixto completo.

| Archivo | Selección |
| --- | --- |
| app/services/analyzer.py | Rango 180°, _inverted_metrics, incorporación en _press_metrics y propagación press. Sin las tres incorporaciones split_knee_angle. |
| app/services/exercise_validation.py | Alias/evaluación inconclusa OHS/HSPU. Sin Lunge/Bulgarian. |
| app/static/app.js | Administración y eliminar análisis. Sin badge Free/Pago/cupo del atleta. |
| app/static/index.html | Assets/nav admin, versión app.js, OHS/HSPU en tres selectores. Sin estocadas. |
| tests/test_exercise_profiles.py | Ciclos OHS/HSPU y requisitos overhead/invertido. Sin filas estocadas. |
| tests/test_weekly_release_validation.py | Cierre de sesión y restore head después de roundtrip; aserción de revocación de HEAD. |

Parches:
- [Patch app/services/analyzer.py](patches/app__services__analyzer.py.patch)
- [Patch app/services/exercise_validation.py](patches/app__services__exercise_validation.py.patch)
- [Patch app/static/app.js](patches/app__static__app.js.patch)
- [Patch app/static/index.html](patches/app__static__index.html.patch)
- [Patch tests/test_exercise_profiles.py](patches/tests__test_exercise_profiles.py.patch)
- [Patch tests/test_weekly_release_validation.py](patches/tests__test_weekly_release_validation.py.patch)

## Cambios locales excluidos — inventario exhaustivo
- .agents/skills/impeccable/SKILL.md
- .agents/skills/impeccable/agents/impeccable_asset_producer.toml
- .agents/skills/impeccable/agents/impeccable_finish_reviewer.toml
- .agents/skills/impeccable/reference/adapt.md
- .agents/skills/impeccable/reference/audit.md
- .agents/skills/impeccable/reference/degraded/asset-producer.md
- .agents/skills/impeccable/reference/degraded/finish-reviewer.md
- .agents/skills/impeccable/reference/harden.md
- .agents/skills/impeccable/reference/hooks.md
- .agents/skills/impeccable/reference/new-work.md
- .agents/skills/impeccable/reference/routing.md
- .agents/skills/impeccable/reference/visualize.md
- .agents/skills/impeccable/scripts/VERSION
- .agents/skills/impeccable/scripts/bin/windows-x64/impeccable.exe
- .agents/skills/impeccable/scripts/command-metadata.json
- .agents/skills/impeccable/scripts/impeccable.cmd
- .agents/skills/impeccable/scripts/live-browser-session.js
- .agents/skills/impeccable/scripts/live-browser.js
- .impeccable/design.json
- .impeccable/mobile--analyses-1.png
- .impeccable/mobile--analyses-new.png
- .impeccable/mobile--coach-reviews-2.png
- app/services/weekly_summary.py
- app/static/weekly-expanded.css
- app/whatsapp/capture.py
- app/whatsapp/runtime.py
- tests/test_whatsapp_capture.py
- .agents/skills/animate-expo/RECIPES.md
- .agents/skills/animate-expo/SKILL.md
- .agents/skills/animate/RECIPES.md
- .agents/skills/animate/SKILL.md
- .agents/skills/animation-vocabulary/SKILL.md
- .agents/skills/apple-design/SKILL.md
- .agents/skills/ask-sonner/API.md
- .agents/skills/ask-sonner/SKILL.md
- .agents/skills/emil-design-eng/SKILL.md
- .agents/skills/find-animation-opportunities/SKILL.md
- .agents/skills/impeccable/reference/component-review.md
- .agents/skills/impeccable/reference/generate.md
- .agents/skills/impeccable/reference/mode-operate.md
- .agents/skills/impeccable/reference/mode-persuade.md
- .agents/skills/impeccable/reference/mode-read.md
- .agents/skills/impeccable/reference/region-map.md
- .agents/skills/improve-animations/AUDIT.md
- .agents/skills/improve-animations/PLAN-TEMPLATE.md
- .agents/skills/improve-animations/SKILL.md
- .agents/skills/mobile-native/SKILL.md
- .agents/skills/pick-ui-library/SKILL.md
- .agents/skills/prototype/PICKER.md
- .agents/skills/prototype/SKILL.md
- .agents/skills/review-animations/SKILL.md
- .agents/skills/review-animations/STANDARDS.md
- .agents/skills/write-swift/SKILL.md
- .codex-remote-attachments/01a0feda-5128-7592-a4d3-1029560531e9/12346a44-779a-485a-9e25-3c1a3ac930d7/1-1000084801.jpg
- .codex-remote-attachments/01a0feda-5128-7592-a4d3-1029560531e9/4109fffb-b190-4505-ae41-55ae88b22ffc/1-1000084802.jpg
- .impeccable/admin-desktop.png
- .impeccable/admin-mobile.png
- .impeccable/admin-plans-mobile.png
- .impeccable/admin-regression.log
- .impeccable/admin-suite.log
- .impeccable/bitacora-desktop.png
- .impeccable/bitacora-mobile.png
- .impeccable/bitacora-qa.cjs
- .impeccable/bitacora-test.yml
- .impeccable/coach-suite-classification.csv
- .impeccable/install-training-usage.py
- .impeccable/mobile-flows.cjs
- .impeccable/mobile-metrics.cjs
- .impeccable/mobile-navigation-index.patch
- .impeccable/mobile-qa.cjs
- .impeccable/native-interactions.cjs
- .impeccable/native-mobile-qa.cjs
- .impeccable/native-nav.png
- .impeccable/preview-server.cjs
- .impeccable/reference-capture.cjs
- .impeccable/reference-targeted.log
- .impeccable/reference-tests.log
- .impeccable/stage-training-index.py
- .impeccable/studio-fixtures.cjs
- .impeccable/training-board-fixture.jpg
- .impeccable/training-evolution-detail-mobile.png
- .impeccable/training-evolution-edit-mobile.png
- .impeccable/training-evolution-list-desktop.png
- .impeccable/training-evolution-list-mobile.png
- .impeccable/training-interpretation-desktop.png
- .impeccable/training-interpretation-mobile.png
- .impeccable/training-interpretation-qa.cjs
- .impeccable/training-live-smoke.py
- .impeccable/training-main-index.patch
- .impeccable/training-note-desktop.png
- .impeccable/training-note-mobile.png
- .impeccable/training-note-qa.cjs
- .impeccable/training-polish-capture-desktop.png
- .impeccable/training-polish-capture-mobile.png
- .impeccable/training-polish-local-check.cjs
- .impeccable/training-polish-qa.cjs
- .impeccable/training-polish-review-desktop.png
- .impeccable/training-polish-review-mobile.png
- .impeccable/training-publish-index.patch
- .impeccable/training-voice-desktop.png
- .impeccable/training-voice-mobile.png
- .impeccable/training-voice-qa.cjs
- .impeccable/validation-baseline.json
- .impeccable/validation-server.cjs
- .impeccable/weekly-card-capture.cjs
- .impeccable/weekly-dense-function.js
- .impeccable/weekly-dense-tests.cjs
- .impeccable/weekly-direction.md
- .impeccable/whatsapp-link-desktop.png
- .impeccable/whatsapp-link-mobile.png
- .impeccable/whatsapp-link-qr.png
- app/services/exercise_profiles/bulgarian_split_squat_front.json
- app/services/exercise_profiles/bulgarian_split_squat_side.json
- app/services/exercise_profiles/lunge_front.json
- app/services/exercise_profiles/lunge_side.json
- debug.log
- docker-compose.kapso-local.yml

## Herramientas/artefactos heredados retirados solo del candidato
- .agents/skills/impeccable/SKILL.md
- .agents/skills/impeccable/agents/impeccable_asset_producer.toml
- .agents/skills/impeccable/agents/impeccable_documenter.toml
- .agents/skills/impeccable/agents/impeccable_finish_reviewer.toml
- .agents/skills/impeccable/agents/impeccable_manual_edit_applier.toml
- .agents/skills/impeccable/agents/openai.yaml
- .agents/skills/impeccable/reference/adapt.md
- .agents/skills/impeccable/reference/adapt.native.md
- .agents/skills/impeccable/reference/android.md
- .agents/skills/impeccable/reference/animate.md
- .agents/skills/impeccable/reference/audit.md
- .agents/skills/impeccable/reference/audit.native.md
- .agents/skills/impeccable/reference/bolder.md
- .agents/skills/impeccable/reference/clarify.md
- .agents/skills/impeccable/reference/colorize.md
- .agents/skills/impeccable/reference/craft-floor.md
- .agents/skills/impeccable/reference/craft.md
- .agents/skills/impeccable/reference/critique.md
- .agents/skills/impeccable/reference/degraded/asset-producer.md
- .agents/skills/impeccable/reference/degraded/documenter.md
- .agents/skills/impeccable/reference/degraded/finish-reviewer.md
- .agents/skills/impeccable/reference/degraded/manual-edit-applier.md
- .agents/skills/impeccable/reference/delight.md
- .agents/skills/impeccable/reference/distill.md
- .agents/skills/impeccable/reference/doctor.md
- .agents/skills/impeccable/reference/document.md
- .agents/skills/impeccable/reference/extract.md
- .agents/skills/impeccable/reference/harden.md
- .agents/skills/impeccable/reference/hooks.md
- .agents/skills/impeccable/reference/init.md
- .agents/skills/impeccable/reference/ios.md
- .agents/skills/impeccable/reference/layout.md
- .agents/skills/impeccable/reference/live-setup.md
- .agents/skills/impeccable/reference/live.md
- .agents/skills/impeccable/reference/new-work.md
- .agents/skills/impeccable/reference/onboard.md
- .agents/skills/impeccable/reference/operate.md
- .agents/skills/impeccable/reference/optimize.md
- .agents/skills/impeccable/reference/overdrive.md
- .agents/skills/impeccable/reference/polish.md
- .agents/skills/impeccable/reference/quieter.md
- .agents/skills/impeccable/reference/routing.md
- .agents/skills/impeccable/reference/shape.md
- .agents/skills/impeccable/reference/typeset.md
- .agents/skills/impeccable/reference/visualize.md
- .agents/skills/impeccable/scripts/VERSION
- .agents/skills/impeccable/scripts/bin/windows-x64/impeccable.exe
- .agents/skills/impeccable/scripts/command-metadata.json
- .agents/skills/impeccable/scripts/data/font-index-failures.json
- .agents/skills/impeccable/scripts/data/font-index.json
- .agents/skills/impeccable/scripts/impeccable
- .agents/skills/impeccable/scripts/impeccable.cmd
- .agents/skills/impeccable/scripts/live-browser-dom.js
- .agents/skills/impeccable/scripts/live-browser-ignores.js
- .agents/skills/impeccable/scripts/live-browser-session.js
- .agents/skills/impeccable/scripts/live-browser.js
- .agents/skills/impeccable/scripts/modern-screenshot.umd.js
- .codex/hooks.json
- .impeccable/athlete-ux-validation.md
- .impeccable/audit.md
- .impeccable/coach-baseline-validation.md
- .impeccable/coach-ux-review.md
- .impeccable/design.json
- .impeccable/exercise-quality/frozen-environment.json
- .impeccable/exercise-quality/measure-public.py
- .impeccable/exercise-quality/measure.py
- .impeccable/exercise-quality/metrics-by-exercise.json
- .impeccable/exercise-quality/protocol.md
- .impeccable/exercise-quality/report.md
- .impeccable/exercise-quality/video-results.csv
- .impeccable/mobile--analyses-1.png
- .impeccable/mobile--analyses-new.png
- .impeccable/mobile--coach-reviews-2.png
- .impeccable/mobile-metrics.json
- .impeccable/mobile-qa.json
- .impeccable/mobile-ux-report.md
- .impeccable/native-feel-validation.md
- .impeccable/surface-workspace.md
- .impeccable/validation-report.md

## Dependencias y riesgos

Administración requiere models + 0022 + administration + adaptadores main/training + UI/pruebas. DELETE analysis requiere endpoint/imports SQL, botón y pruebas; sin nueva migración. Perfiles OHS/HSPU ya versionados requieren las señales y alias seleccionados; el rango 180° afecta también otros ejercicios, con regresión pendiente.

Cadena estática 0001–0022, head 0022_administration. No se ejecutó Alembic. Restore head del test semanal evita dejar DB temporal en 0021 con ORM0022. El test JS admin tiene import absoluto de Playwright y produce screenshots; no se versionaron, se retiraron solo del candidato al terminar.

El contrato de sharing explícito aún necesita S05. No incluir saved_week_link evita transferir la publicación automática local, sin cerrar consentimiento. Demo/seed, cuotas chat, permisos y retención permanecen pendientes de otras etapas.

Estado: selección materializada, validación backend obligatoria bloqueada. Ver S01_IMPLEMENTATION_REPORT.md y S01_VALIDATION.json.
