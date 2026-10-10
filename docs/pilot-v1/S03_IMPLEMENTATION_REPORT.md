# S03 — Autorización de coaches

Fecha: 2026-10-10. Rama: codex/pilot-v1-stabilization.
Base aprobada: b65ddfd66b7b8bdc2d9a6d12d498a94df7f0e0d6.
Commit funcional final: 393699b5dad3c86c89e71bac9a92bbcdb9092765.
Estado: IMPLEMENTADA Y VALIDADA; lista para revisión técnica. S04 no iniciada.
El commit documental final se identifica con git log -1 --format=%H -- docs/pilot-v1/S03_IMPLEMENTATION_REPORT.md y se entrega junto al reporte.

## Relación existente y política aplicada

No existe una relación general coach-atleta que autorice altas, nuevas cargas, historial completo o bitácora. El mecanismo reutilizable es CoachReview (tabla reviews): coach_id y la pareja analysis_id/athlete_id, con claves foráneas a coaches y al análisis del atleta. Cada asignación permite revisar ese análisis concreto; no se convierte en permiso para crear otros análisis del atleta.

- El actor se obtiene de la sesión autenticada, con User.is_active y rol COACH. coach_id sigue siendo un parámetro compatible, pero se compara con ese actor y las operaciones usan su identidad verificada.
- Listado de atletas: solo id/nombre de atletas activos con revisiones asignadas al coach. Parámetros de búsqueda o IDs extra no amplían el conjunto. No se ofrece un directorio general.
- Revisiones PENDING/IN_REVIEW/COMPLETED: lectura solo del coach asignado y de atletas activos. Se conservan las reglas existentes de cierre: una revisión completada no admite edición.
- Una asignación a un análisis no permite consultar otros análisis, fotos de bitácora, resúmenes privados ni historial del mismo atleta.
- Videos originales, anotados, miniaturas y JSON privados: propietario o coach con una revisión del análisis que referencia exactamente ese archivo y atleta activo. Se agrega Cache-Control: private, no-store.
- Reanálisis puede reutilizar una ruta original. El guard busca una referencia autorizada, en vez de elegir arbitrariamente la primera fila que comparte la ruta. Esto permite el video efectivamente asignado sin abrir el resultado de un análisis distinto.
- Alta de atletas y carga de análisis desde coach: denegadas con 403 antes de consumir cuota, guardar archivos, crear filas o programar IA. También se deniegan en el handler si no se usa el middleware.
- El administrador conserva /api/admin/users y demás operaciones existentes de cuentas. El flujo permitido sigue siendo alta administrativa, login/upload del atleta y solicitud al coach. No se agregó upload ni impersonación para administrador.
- Estadísticas internas globales requieren SYSTEM_ADMIN e is_internal; un coach con un flag interno histórico ya no obtiene datos globales de atletas.
- Los coaches inactivos no se listan para nuevas solicitudes y no pueden recibir asignaciones nuevas. Desactivar atleta oculta sus asignaciones y medios a coaches; desactivar coach invalida sus siguientes solicitudes autenticadas.

Los IDs ajenos y ausentes de review responden el mismo 404. Los archivos ajenos y ausentes responden el mismo 403. Cambiar coach_id, omitirlo o duplicarlo no concede acceso. Un 422 de validación contiene únicamente datos del request, sin consultar ni identificar recursos ajenos.

## Inventario auditado

| Superficie | Revisión y resultado |
|---|---|
| GET /api/coach/athletes | Filtrado por reviews del actor y User.is_active; forma de respuesta conservada. |
| POST /api/coach/athletes | Denegado; alta asistida queda en /api/admin/users. |
| POST /api/coach/analyses | Denegado incluso si el coach ya tiene otra review del atleta; no relación para nuevas cargas. |
| GET /api/coach/reviews | Actor autenticado, coach_id propio y atletas activos; filtros de estado existentes. |
| GET /api/coach/reviews/{review_id} | _get_coach_review verifica review + coach; no lectura por ID ajeno. |
| PATCH .../start | Mismo guard; idempotencia y revisión completada conservadas. |
| GET/POST .../annotations; PATCH/DELETE .../annotations/{annotation_id} | Review propia; anotaciones acotadas a review y coach; sin cruce de IDs hijos. |
| GET .../ai-observations; PATCH .../ai-observations/{observation_id} | Review propia y observación del análisis correspondiente. |
| PATCH .../repetitions/{repetition_id}; POST .../repetitions | Review propia y repetición del análisis; no mutación de IDs ajenos. |
| PATCH .../summary; POST .../complete | _editable_review, asignación propia, requisitos de cierre y bloqueo de completadas. |
| /uploads/*, /results/*, /analysis/* | Guard de ruta exacta por análisis autorizado, cuenta activa y no-store; sin bypass por nombre de archivo. |
| /api/analyses, /api/analyze y detalle/delete/reanalyze | require_athlete y propiedad existente; coach no accede por IDs ni crea análisis aquí. |
| GET /api/coaches; POST /api/analyses/{id}/request-review | Solo atleta autenticado/propietario; solicitud a coach activo. Tras S03 es el único productor HTTP de CoachReview. |
| /api/training-sessions/*, /api/training-week*, /api/whatsapp/* | require_athlete y servicios con athlete_id derivado de sesión; no heredan permisos de review. S02 conservada. |
| /api/admin/*, /api/internal/ai-usage | Administración por rol; flag interno de coach no concede acceso global. |
| /coach/reviews*, /coach/athletes/new, /coach/analyses/new | Shell con guard de rol; formularios legacy no otorgan permiso de operación. Sus POST están bloqueados. |
| /shared/week/{token} e imágenes compartidas | Capacidad pública mediante token del mecanismo existente; independiente del rol coach. Consentimiento/retención siguen pendientes de S05, sin cambios aquí. |
| /api/exercises, /api/exercise-categories, /exercises, /static/*, docs/OpenAPI | Catálogo y assets de producto, sin listado de datos privados de atletas. |

Servicios y helpers revisados: _authenticated_user, _guard_user, require_coach, require_internal, protect_application_routes, _coach_context, _get_coach_review, _editable_review, _get_analysis, _prepare_async_analysis, _process_analysis, TrainingService, WeeklySummaryService, routers de administración/entrenamiento/semana/WhatsApp e IdentityResolver S02. Los servicios de análisis ya no reciben un athlete_id arbitrario desde una operación de coach habilitada.

## Cambios seleccionados

1. app/main.py: guards de actor/roles, listados acotados, denegación de alta/upload, permisos de medios, cuentas activas y filtro de coaches disponibles por actividad.
2. tests/test_basic_auth.py: expectativas inseguras anteriores reemplazadas por denegación; alta y fixture de segundo atleta por API administrativa; propiedad del atleta conservada.
3. tests/test_coach_authorization.py: 29 casos de aislamiento con dos atletas, Carlos/Annais como dos coaches y administrador en PostgreSQL desechable; flujo completo request/start/annotation/summary/complete y lectura del atleta.
4. docs/pilot-v1/S03_IMPLEMENTATION_REPORT.md: evidencia y límites del cierre.

Sin cambios de modelos, migraciones, frontend, dependencias, catálogo ni arquitectura. Head Alembic único: 0022_administration. Las operaciones/esquemas OpenAPI se comparan exactamente con el baseline; se conserva incluso el orden de parámetros.

## Pruebas y resultados

Entorno: Docker Engine 28.3.2, imagen local existente fluxio-whatsapp-tests:phase2; PostgreSQL nuevo fluxio-s03-db-20261010 con movement_test y datos tmpfs. Ejecutor fluxio-s03-tests-20261010, candidato montado en lectura, ejecución en /tmp/s03. Red interna heredada de S01 sin salida a proveedores. OPENAI_API_KEY/KAPSO_API_KEY vacías; mocks/FakeProvider. Las migraciones y TRUNCATE de fixtures se ejecutan únicamente en esta base nueva.

| Verificación | Resultado |
|---|---|
| Dirigidas: autorización nueva + auth + solicitudes/inbox/anotaciones/cierre + contratos + S02 | PASS: 90 casos, 44.98 s; incluye los 29 nuevos y los 22 S02. |
| Suite Python completa sobre commit funcional final | PASS: 524 casos, 225.00 s; 29 S03 incluidos; cero FAIL/ERROR/SKIPPED. |
| JavaScript, nueve archivos .test.cjs | PASS: 65 casos, 18.89 s; cero FAIL/SKIPPED. |
| Contrato OpenAPI íntegro | PASS: test_all_baseline_http_operations_and_schemas_are_preserved. |
| Migraciones aisladas/compatibilidad | PASS dirigido: roundtrip de bitácora y Alembic check; head 0022 sin cambios. |
| Copia ejecutada vs candidato | PASS: SHA-256 de los tres archivos funcionales/de pruebas coincide. |
| Workspace original | PASS: 153 hashes y estado Git coinciden con snapshot S01; rama y HEAD originales intactos. |
| EasyPanel, servicios reales, datos/cuentas persistentes | SKIPPED por restricción; no se conectó ni desplegó. |

Comandos de validación:

    pytest -q tests/test_coach_authorization.py tests/test_basic_auth.py tests/test_coach_requests.py tests/test_coach_inbox.py tests/test_coach_annotations.py tests/test_complete_review.py tests/test_whatsapp_contracts.py tests/test_whatsapp_account_status.py --junitxml=/tmp/s03-targeted.xml
    WEEKLY_RELEASE_PUBLIC_BASE_URL=https://fluxio-s03.invalid pytest -q --junitxml=/tmp/s03-full.xml

La URL .invalid habilita un caso de contrato con FakeProvider; no se contacta. JavaScript usa NODE_PATH del runtime bundled y Playwright existente.

Se detectaron y corrigieron dos problemas antes del cierre: codificación Windows de seis bytes en los mensajes nuevos (fallo de import, corregido a UTF-8) y cambio de orden OpenAPI en el listado de reviews (primera ejecución: 88 PASS/1 FAIL; corregido sin cambiar fixture ni relajar el test). La ejecución dirigida final quedó en 90 PASS. Las tres advertencias Python de BlockingPortal/on_event ya existían.

## Criterios obligatorios

- Coach autorizado: detalle y archivos del análisis asignado, anotación/resumen/cierre legítimos.
- Coach sin autorización: atletas ajenos fuera de listas; nueva carga denegada para atleta propio/ajeno/inexistente; análisis, archivos y bitácora ajenos inaccesibles.
- IDs directos: matriz de doce operaciones de review, comparación contra recurso inexistente, suplantación/duplicación de coach_id y cruce de annotation/repetition/observation de otro análisis.
- Administrador: alta de fixture y acceso operativo a usuarios/estadísticas. Atleta: lectura propia de análisis, video, bitácora y review cerrada; acceso ajeno denegado.
- Desactivación: atleta no aparece ni permite review/media al coach; cookie de coach desactivado queda inválida; regresiones WhatsApp S02 conservadas.
- Reviews: solicitud del propietario, asignación, inicio, anotación, resumen, cierre y devolución al atleta comprobados sin proveedores reales.

## Riesgos y restricciones temporales

- Reviews preexistentes no guardan la procedencia de la asignación. Versiones anteriores permitían al coach crear una review al subir un video. S03 impide ese nuevo camino, pero no reconstruye ni certifica autorización histórica de esas filas. Antes de activar el piloto, un operador debe confirmar las asignaciones heredadas con atletas/administración; ninguna fila persistente se modificó en esta etapa. No se utilizaron timestamps ni inferencias como prueba de consentimiento.
- Una review conservada es el grant existente de ese análisis, incluidas las completadas para consulta. No existe una acción pública nueva de revocación/asignación: la política de conservación y revocación operativa debe mantenerse bajo control administrativo. Se oculta durante la desactivación del atleta; reactivarlo vuelve a permitir la asignación existente, sin reactivar la identidad WhatsApp revocada por S02.
- Las pantallas legacy de alta/upload de coach permanecen en el shell por compatibilidad, pero sus operaciones responden 403 con instrucciones. El piloto debe utilizar alta administrativa y carga/solicitud del atleta; no hay un módulo nuevo de vinculación coach-atleta.
- Un archivo ya descargado o una respuesta/stream autorizado ya iniciado no se puede retirar; no-store evita nueva persistencia normal en caché. No se prometen revocaciones de copias que ya existían.
- Tokens públicos de sharing y consentimiento siguen fuera de S03. La seguridad de roles no equivale a cierre de todos los riesgos de publicación.
- Pruebas locales/simuladas; no certificación de la versión actualmente desplegada en EasyPanel. No publicación, cuentas reales, consumos externos ni tareas S04 y posteriores.

Recomendación de cierre: aprobar el cierre técnico S03 tras revisar la política aplicada. Todos los criterios obligatorios pasan en PostgreSQL desechable; la publicación sigue condicionada a verificar las asignaciones heredadas y los demás gates del piloto. El código no certifica procedencia histórica que el esquema no conserva. Trabajo detenido para revisión; no iniciar S04.

## Evidencia y entorno al cierre

JUnit local: C:/Users/desarrollo/AppData/Local/Temp/fluxio-s03-validation-20261010/s03-full.xml (524 casos) y s03-targeted.xml (90 casos). Capturas JavaScript conservadas fuera del candidato en C:/Users/desarrollo/AppData/Local/Temp/fluxio-s03-js-evidence-20261010/. No se incluyeron logs, secretos ni artefactos .impeccable en los commits.

Los contenedores creados solamente para S03 se detienen al conservar la evidencia; PostgreSQL tmpfs es desechable. No se borraron imágenes, contenedores ni volúmenes existentes. Se conserva la red interna S01. Original: 153 hashes y estado Git verificados de nuevo; rama codex/bitacora-entrenamiento y HEAD 97583b5c191fd48d4282ad42d0b020d6cb1709a1 sin cambios.
