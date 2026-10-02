# Coach UX: baseline técnica validada

Fecha: 2026-10-02. Contexto: coach-ux-review.md. DESIGN.md e identidad aprobada conservados. Sin nuevas funcionalidades, rutas, permisos ni trabajo de producto sobre atleta. Las modificaciones en tests del atleta son mantenimiento de la suite existente solicitado en esta fase.

## Suite antes y después

| Ejecución | Passed | Failed | Errors |
| --- | ---: | ---: | ---: |
| Inicial, PostgreSQL limpio | 54 | 43 | 46 |
| Aislamiento y sesiones explícitas | 108 | 35 | 0 |
| Correcciones y contrato vigente | 137 | 6 | 0 |
| Final, PostgreSQL limpio | 143 | 0 | 0 |

JavaScript: 11 tests originales de review-state siguen pasando; 12 tests nuevos ejecutan handlers/API helper de app.js: total **23/23**. No skips ni xfails. Los 16 tests de cierre/autenticación están incluidos en los 143 aprobados. Evidencia: review/suite-before.xml, suite-isolation.xml, suite-corrections.xml, suite-final.xml y studio-final-tests.log.

## Clasificación individual y causas

Los 89 fallos/errores originales están enumerados individualmente en **coach-suite-classification.csv**, con grupo, causa primaria, causa secundaria revelada posteriormente, archivo, impacto, acción y resultado final. El conteo clasifica el primer fallo observado de cada caso: no suma otra vez sus defectos secundarios.

| Grupo | Cantidad inicial | Causa raíz | Archivos | Impacto / acción |
| --- | ---: | --- | --- | --- |
| A: regresión Coach UX | 0 demostradas | No se reprodujo pérdida de borradores ni cierre indebido | app/static/app.js, review-state.js | Guardas adicionales contra invocaciones encoladas; pruebas de handlers |
| B: tests desactualizados | 21 | 20 llamadas sin autenticación; un seed esperaba cuatro usuarios en vez de cinco | test_api, test_async_analysis, test_athlete_flow, test_persistence | Sesiones reales por rol y len(DEMOS); no desactivar autenticación |
| C: fixture/configuración | 67 | Health test restauraba una revisión antigua; pruebas posteriores bajaban migraciones desde un esquema desfasado y dejaban columnas faltantes | test_api, test_athlete_flow, test_persistence; 46 errores posteriores en otros módulos | Restaurar revision original; preparar fixtures legacy sin SYSTEM_ADMIN; reejecutar desde base limpia |
| D: entorno/dependencia | 0 | Sin bloqueo externo en la ejecución final | — | Docker/PostgreSQL/FFmpeg/MediaPipe disponibles |
| E: fallo previo sin defecto identificado | 0 | Los casos previos se identificaron concretamente como B/C/F | — | Sin casos sin explicar |
| F: defecto real visible inicialmente | 1 | /api/health comparaba hardcoded 0012 contra un esquema más reciente | app/main.py | Resolver head con Alembic; ahora responde ready en head |

La tabla inicial provisional agrupaba health con la contaminación (C=68). La ejecución aislada demostró que health era un defecto independiente; clasificación final de casos originales C=67/F=1.

Al eliminar la contaminación se revelaron otras causas, antes ocultas:

- **F, default de revisión**: SQL conservaba REQUESTED mientras el modelo y la restricción admitían PENDING. Afectaba 18 casos de gráficos inválidos antes de alcanzar la aserción pretendida. Migración 0015 alinea el default; no cambia estados de negocio ni filas existentes.
- **F, drift**: ai_reasoning_runs usaba unique constraint en migraciones y unique index en el modelo. Dos command.check fallaban. 0015 alinea la representación conservando unicidad; roundtrip y command.check pasan.
- **F, seed**: el upsert sobrescribía nombres editados. Se conserva el nombre existente y se mantienen las operaciones de credenciales existentes. El test de preservación se conserva, no se debilita.
- **F, persistencia indisponible**: error de conexión durante autenticación/guard podía escapar sin una respuesta recuperable. Manejo SQLAlchemyError devuelve 503; probado también desconectando PostgreSQL real.
- **F previo, cliente 204**: apiJson intentaba parsear JSON ausente tras DELETE exitoso. Ahora acepta 204; test específico añadido. El mismo problema está en HEAD, por lo que no es regresión Coach UX.
- **B, aislamiento por rol**: operar con coach_id ajeno como Carlos recibe 403 del guard, no 404. Se mantienen pruebas de propiedad y prohibición; se actualiza el código esperado al contrato autenticado vigente.
- **B/C, procesamiento**: /api/analyses responde 202 y el resultado final se consulta por GET. Los stubs ahora aceptan view/progress_callback y escriben los artefactos que el worker exige. Preflight se aísla explícitamente solo en tests unitarios con bytes falsos.
- **B, video negro real**: ya no es un caso de análisis exitoso. Preflight lo rechaza por falta de pose; los tests reales verifican FAILED, error persistido y ausencia de resultados, sin simular éxito ni desactivar validación.
- **B, landing**: se retiran expectativas de textos eliminados de la baseline aprobada; se conservan las aserciones de propuesta comercial y CTA vigente.
- **C, legacy**: SYSTEM_ADMIN no existe en esquemas anteriores a 0012. Los tests de migración preparan datos representables en ese esquema y restablecen seed/login tras upgrade. No se cambia el downgrade para borrar usuarios reales.
- Tres problemas de codificación introducidos durante esta fase al editar tests se corrigieron antes de la ejecución final. No quedan expectativas con mojibake.

## Review Studio: las 13 condiciones

| Condición | Verificación |
| --- | --- |
| 1. Refresh interno conserva borrador | Node state + handlers; navegador real al iniciar revisión |
| 2. Guardar anotación conserva resumen | Handler + POST real, resumen dirty conservado |
| 3. Confirmar/rechazar IA conserva resumen | Ambas decisiones PATCH reales; handler y state |
| 4. Clasificación conserva resumen | PATCH real NEEDS_WORK + handler |
| 5. Advertencia al salir | Test del listener beforeunload para resumen/editor; navegación real con dirty quedó bloqueada. El IAB no expuso un diálogo nativo inspeccionable |
| 6. Guardar limpia dirty | Handler + PATCH real, indicador Sin cambios pendientes |
| 7. Guardar antes de completar | Orden PATCH summary → POST complete en log real + tests |
| 8. Error de save impide close | 503 real de summary; no POST complete; dirty conservado |
| 9. Error de close conserva datos | 503 real de complete tras guardar; datos permanecen; recuperación exitosa |
| 10. 409 no duplica | Repetir complete devuelve 409; conflicto real con cierre desde otro cliente retiene borrador y rechaza PATCH; no segundo POST |
| 11. 401/403 seguros | Logout en otra pestaña / login con otro rol produce errores reales; nada se guarda, borrador permanece |
| 12. Conexión recuperable | Red Docker del servidor desconectada: Failed to fetch; reconectar permite guardar/completar el contenido conservado |
| 13. Doble clic | Tests encolados para comentario/resumen/cierre; navegador dblclick anotación/cierre: una operación persistida |

## E2E con backend real

FastAPI/Uvicorn y PostgreSQL 17, proyecto Docker desechable movement-coach-e2e. Video MP4 reproducible generado con FFmpeg. Análisis, repeticiones y sugerencias sembrados expresamente para QA; **no se afirma haber generado IA real ni validado el proveedor OpenAI**. No se usa el servidor anterior de fixtures HTTP ni se intercepta éxito.

Recorrido completado: login Carlos → bandeja → revisión PENDING → borrador → iniciar → primer momento → seek 3 s y reproducción → comentar → guardar → clasificar → descartar y confirmar IA inline → guardar resumen → editar resumen adicional → doble clic Guardar y completar → bandeja → reabrir COMPLETED y campos bloqueados.

Persistencia reconsultada mediante nuevas peticiones autenticadas y SQL: revisión COMPLETED, foco/próxima sesión/resumen iguales a los escritos, una anotación y una decisión por revisión principal. Dos revisiones completas del recorrido/recuperación tuvieron dos anotaciones en total, sin duplicados. Una tercera revisión aislada sirve exclusivamente para el conflicto 409.

Errores reales: 401 sin sesión, 403 por rol incorrecto, 409 por revisión ya completada, 503 por desconectar la red de PostgreSQL, desconexión HTTP al cortar la red del servidor. Ningún error se trató como éxito. Evidencia en review/backend-http.log, backend-persistence.json, backend-recovery-persistence.json, backend-sql.txt, backend-conflict-completion.json y capturas backend-*.png.

Responsive real: 320, 390, 1440 px; sin overflow horizontal y sin botones visibles del Studio menores de 44 px. Evidencia backend-responsive.json. No cambios CSS en esta fase.

## Archivos modificados en esta fase

- Producto: app/main.py (health y 503), app/seed.py (preservación de nombres), app/static/app.js (guardas y 204).
- Migración nueva: migrations/versions/0015_review_status_default.py (default e índice).
- Fixtures/helpers: tests/conftest.py, tests/analysis_helpers.py.
- Tests existentes actualizados: test_api, test_async_analysis, test_athlete_flow, test_coach_annotations, test_coach_inbox, test_coach_requests, test_demo_page, test_deployment_readiness, test_persistence, test_press_segmentation, test_reanalysis, test_review_moments.
- Nuevo: tests/studio-integration.test.cjs. tests/review-state.test.cjs se conserva.
- Diagnóstico: este informe y coach-suite-classification.csv. Evidencia y scripts de backend desechable permanecen en review/ ignorado.

## Riesgos y aplicación

- Ejecutar **alembic upgrade head** antes de usar esta baseline en el backend habitual. No se migró ni se tocó su base normal.
- Los borradores son locales en memoria: cerrar voluntariamente la página después de la advertencia pierde el contenido no guardado. Es el alcance aprobado, sin almacenamiento nuevo.
- Ante un 409 por cierre concurrente, el borrador local se conserva; el servidor mantiene el bloqueo. La vista local debe reabrirse para reflejar el estado canónico. No se introdujo sincronización ni resolución nueva de conflictos.
- Validación pendiente física: beforeunload y teclado/video sticky en Safari iOS y Android. Responsive de escritorio emulado sí probado.
- Rollback a revisiones anteriores a SYSTEM_ADMIN requiere una estrategia de datos; la suite legacy no convierte ni elimina usuarios de producción.
- Tres warnings existentes de FastAPI on_event deprecado. Tests verdes; no se migró el lifecycle fuera del alcance.

**Resultado: suite completa verde, sin tests excluidos. Coach validado contra backend real aislado; identidad intacta y flujo del atleta sin desarrollo nuevo.**
