# Arquitectura técnica y evidencia de validación

Fecha: 2026-10-09, America/Santiago. HEAD `97583b5c191fd48d4282ad42d0b020d6cb1709a1`, rama `codex/bitacora-entrenamiento`. Se auditó el workspace con modificaciones previas; administración, migración 0022, tests de administración y algunos perfiles no estaban rastreados. La auditoría no alteró esos archivos. Las ocho entregas son documentación nueva.

## Arquitectura actual: hechos

Monolito FastAPI con routers separados para bitácora, resumen, WhatsApp, administración y catálogo. Frontend HTML/CSS/JavaScript sin framework; rutas de app sirven `index.html`, y JS compone vistas. SQLAlchemy/PostgreSQL, Alembic y archivos en volumen compartido. No se halló servicio de pagos, motor de PR, objetivos, dispositivo deportivo ni asistente longitudinal.

```mermaid
flowchart TD
    UI[HTML y JS web] --> API[FastAPI y guards de sesión/rol]
    API --> TRAIN[TrainingService]
    API --> WEEK[WeeklySummaryService]
    API --> ADMIN[Administración y cuotas]
    API --> VIDEO[BackgroundTasks de video]
    API --> CAT[Catálogo JSON y perfiles]
    K[Kapso webhook firmado] --> IN[Inbox PostgreSQL]
    IN --> WORK[Worker independiente]
    WORK --> STATE[Identidad y máquina de estados]
    STATE --> TRAIN
    STATE --> WEEK
    WORK --> OUT[Outbox PostgreSQL]
    OUT --> K
    TRAIN --> AI[Interpretación/transcripción externa]
    VIDEO --> POSE[MediaPipe/OpenCV/FFmpeg]
    VIDEO --> REASON[IA sobre métricas, opcional]
    TRAIN --> DB[PostgreSQL]
    WEEK --> DB
    ADMIN --> DB
    VIDEO --> DB
    TRAIN --> DISK[Storage privado]
    VIDEO --> DISK
    WORK --> DISK
```

### Componentes y contratos

| Componente | Archivos | Responsabilidad y límite |
| --- | --- | --- |
| Aplicación/seguridad/reviews/video | `app/main.py` | Middleware de ruta, rol/ownership, upload, trabajos, review; archivo concentra gran parte del producto |
| Autenticación | `app/services/auth.py`, `app/seed.py` | scrypt, comparación constante, cookie firmada Starlette; cuentas demo y altas asistidas |
| Bitácora | `app/training.py`, `services/training_service.py`, `training_contracts.py` | CRUD de propietario y pipeline compartido; adaptador HTTP agrega consume, servicio no lo hace |
| Media | `services/training_media.py`, `training_transcription.py` | Imagen validada/normalizada; audio temporal normalizado; sin archivo de audio durable |
| Interpretación | `services/workout_interpretation.py` | JSON schema estricto; bloques y resultados como texto; borrador requiere confirmación |
| Video | `services/analyzer.py`, `biomechanics.py`, `exercise_profiles.py`, `exercise_validation.py` | Pose, segmentación y métricas por perfil/vista; control conservador de calidad |
| Feedback IA | `services/ai_reasoning.py`, `review_moments.py` | Input de métricas/evidencia; abstención por calidad; IA asistente del coach |
| Catálogo | `services/exercise_library.py`, `exercise_library/*.json`, `app/exercises.py` | 20 ejercicios: 7 supported, 13 reference_only; metadata no amplía automáticamente detector |
| Resumen/sharing | `app/weekly.py`, `services/weekly_summary.py` | Estadística factual y semana pública viva; hash de token, expiración y revocación |
| Administración/cuotas | `app/administration.py`, `static/admin.js/css` | Alta/edición, planes, organización, auditoría; no billing |
| WhatsApp | `app/whatsapp/{routes,kapso,identity,security,capture,runtime,queue,worker,media,models}.py` | Firma, identidad cifrada, inbox/outbox, leases, locks, estados y retención |
| UI | `static/app.js`, `training.js`, `training-voice.js`, `whatsapp-link.js`, `athlete-state.js`, `review-state.js`, `mobile-ux.js` | Recuperación de errores, prevenir duplicados y navegación responsive |

### Persistencia

- `users/athletes/coaches`: identidad, rol, hash de contraseña, plan; Athlete no tiene perfil deportivo.
- `training_sessions/training_images`: entrenamiento textual y JSONB, foto propia; asociación a video en JSONB.
- `analyses/repetitions`: estado/progreso, carga kg, resultados/artefactos, tiempos y métricas de reps, correcciones.
- `reviews/coach_annotations/annotations/ai_observation_decisions`: review asignada, anotaciones, resumen, selección/corrección de reps y juicio sobre IA.
- `ai_observations/ai_review_moments/ai_reasoning_runs/training_ai_usage`: observaciones y trazabilidad de modelo/tokens/segundos/error; no libro contable monetario.
- `weekly_shares`: snapshot histórico persistido, pero lector usa consulta **actual** de la semana; token se almacena como hash.
- WhatsApp: identity/challenges/peers/inbox/outbox/conversation_state/usage/media. Teléfono y payload sensibles cifrados; lookup mediante HMAC; claves versionadas.
- Admin: `admin_settings/admin_audit/plan_interactions`; plan válido FREE/PAID, operations ANALYZE/INTERPRET/TRANSCRIBE.
- Migraciones 0001–0022; último head del código: `0022_administration`. Existencia de migración no demuestra aplicación remota.

Storage: original, annotated, analysis, temp; además training-images y original/whatsapp. Guards privados de video validan owner o coach asignado. Imágenes privadas validan propietario; imágenes públicas validan token y pertenencia actual a esa semana. Audio se borra al cerrar temporales. Eliminar sesión web no borra imagen/archivo; worker limpia media WhatsApp no vinculada con TTL, no toda la media web.

### Trabajos y operación

Video moderno devuelve 202 y usa BackgroundTasks dentro del proceso API, sin broker/cola durable. Al iniciar, pendientes pasan a FAILED con error de reinicio: recupera estado visible, no reanuda procesamiento. Ruta legacy `/api/analyze` permanece síncrona.

WhatsApp usa worker separado, inbox durable antes de ACK, deduplicación por proveedor/message_id, locks advisory por peer y locks de filas. Outbox considera envío ambiguo UNCERTAIN y evita retry ciego; retry seguro con backoff. Limpieza comparte worker: si deja de correr, tampoco se ejecuta su retención periódica. No se observó panel/alerta de cola atascada.

Compose define PostgreSQL sin puerto público, volumen DB/storage, app y worker. Arranque espera DB, migra a head, ejecuta seed e inicia Uvicorn. `Dockerfile` incluye FFmpeg y modelo pose con checksum. `ensure_model` puede descargar modelo si falta fuera de imagen; en pruebas se usó modelo ya incluido, red interna sin internet.

## Pruebas actuales y límites

Se reutilizó `fluxio-whatsapp-tests:phase2`; código/tests del workspace copiados a `/tmp/audit` dentro de contenedor, origen montado `:ro`. PostgreSQL **nuevo** `movement_test` en tmpfs; red Docker interna sin salida externa. No se usaron .env reales, credenciales de proveedores ni DB del producto. La suite existente migra/trunca y hace roundtrips únicamente sobre esa base desechable. No se ejecutaron migraciones ni escrituras contra bases del producto.

| Verificación 09-10 | Resultado | Qué prueba / qué no prueba |
| --- | --- | --- |
| Dirigidas: administración, sesiones, servicio, semanal, captura WhatsApp y auth | **85 passed**, 3 warnings, 43.60 s | API/DB y contratos con proveedores fixture; no WhatsApp real |
| Suite Python completa | **479 passed, 1 skipped**, 3 warnings, 238.29 s | CRUD, ownership, cuotas concurrentes, persistencia/migraciones, detección con fixtures y validaciones; no precisión universal ni proveedor real |
| Suite JS completa, 9 archivos `tests/*.test.cjs` | **65 passed**, 0 failed/skipped, 16.52 s | UI/estado y navegador con API simulada; admin usa servidor estático local |
| E2E actual | Ver adenda al final | No equiparar suite JS con E2E HTTP/DB |
| Conteo catálogo | **20: 7 supported, 13 reference_only** | Datos JSON actuales; no todos los perfiles/tipos de falta productivos |
| Health/OpenAPI local y remoto | Ver tabla siguiente | Contrato publicado y respuesta pública; no funcionalidad autenticada completa |

La prueba omitida es `test_weekly_release_validation.py::test_whatsapp_exact_commands_use_configured_real_public_base`: requiere WEEKLY_RELEASE_PUBLIC_BASE_URL explícito. No se suministró para no representar una validación de dominio/canal real. El resto de comandos semanales está cubierto por fixtures. Warnings existentes: Starlette/AnyIO BlockingPortal y FastAPI on_event deprecado.

Incidentes de harness, resueltos sin tocar producto: primer intento JS no encontraba browser bajo usuario sandbox; usar PLAYWRIGHT_BROWSERS_PATH existente lo resolvió. El intento sandbox luego dio 64/65 por ERR_NETWORK_ACCESS_DENIED de admin localhost; ejecución autorizada fuera del sandbox pasó 65/65. Primer backend dio 82/85 porque esta auditoría deshabilitó TRAINING_AI_ENABLED/TRAINING_VOICE_ENABLED, contradiciendo fixtures que habilitan una clave ficticia; repetir con flags por defecto y red bloqueada pasó 85/85. No se atribuyen esos fallos al producto.

Comandos reproducibles esenciales (usar solo base desechable, nunca .env/base real):

```text
NODE_PATH=<runtime>/dependencies/node/node_modules
PLAYWRIGHT_BROWSERS_PATH=C:/Users/desarrollo/AppData/Local/ms-playwright
node --test <lista explícita de tests/*.test.cjs>
DATABASE_URL=postgresql+psycopg://movement:movement@audit-db:5432/movement_test
TEST_DATABASE_RESET=1
STORAGE_PATH=/tmp/audit-storage
OPENAI_API_KEY=
pytest -q -p no:cacheprovider tests/test_administration.py tests/test_training_sessions.py tests/test_training_service.py tests/test_weekly_summary.py tests/test_whatsapp_capture.py tests/test_basic_auth.py
pytest -q -p no:cacheprovider
```

No modificar flags de IA de los fixtures; ausencia de clave real y red interna bloqueada previenen consumo externo. Scripts `scripts/test-phase01.ps1` y `test-weekly-release.ps1` contienen runners históricos; no ejecutarlos contra entornos persistentes. Herramientas y archivos temporales de auditoría se limitan a contenedores desechables/temporales, no al código funcional.

### Evidencia histórica

`results/releases/main-publish-python.log`: 440 passed, 3 warnings, 230.38 s para candidato publicado entonces, no mismo workspace que 479 actual. `main-candidate-phase01.log`: seis PASS de texto/foto/audio/solicitud/review/feedback con IA/pose fixture. `main-candidate-weekly.log`: navegación/sharing/fotos/revocación. `docs/whatsapp/KAPSO_SANDBOX_VALIDATION.md`: pruebas reales del 03-10 con texto/foto/audio/combinado y doble Guardar textual, más comprobación humana de teléfono; replay webhook, botón viejo real y algunas fallas de proveedor no certificados. Es evidencia histórica reportada, no un nuevo envío.

## Despliegue observado hoy, sin mutación

GET anónimos con validación TLS normal al dominio documentado `https://proyectos-fluxio-movement.sgnetm.easypanel.host`. Sin login ni consulta de datos privados. “schema ready” se evalúa contra el head de la **versión que corre allí**, no contra el head del checkout.

| Destino | /health | /api/health | OpenAPI | Auth / Bitácora / Semana / WhatsApp / Catálogo | Admin / Account plan |
| --- | --- | --- | --- | --- | --- |
| localhost:8000 | 200 ok | 200 database ready | 67 paths | Presentes | Presentes |
| localhost:8001 | 200 ok | 200 database ready | 67 paths | Presentes | Presentes |
| Easypanel HTTPS | 200 ok | 200 database ready | 59 paths | Presentes | **Ausentes** |

Los dos contenedores locales app/api y el worker WhatsApp estaban Up; app/api healthy. Esto solo acredita proceso, no cola o proveedor funcional. No se leyó ambiente/secretos de contenedores del producto. No se verificó commit/image digest remoto, revisión SQL remota, entrega WhatsApp actual, modelo IA real, billing ni restore de backups. El informe de smoke del 04-10 decía que Weekly no estaba remoto; **el probe actual reemplaza ese dato**: hoy existe su contrato. Admin/plan siguen diferentes del workspace.

La lectura completa de paths/métodos remoto también confirmó **DELETE /api/analyses/{analysis_id} ausente**: allí el recurso solo expone GET. El checkout sí implementa eliminación de análisis y archivos asociados en `app/main.py:delete_analysis`, cubierta por `tests/test_delete_analysis.py` en la suite actual. PUT/DELETE de sesiones de bitácora sí figuran remotos. No confundir eliminación de TrainingSession con eliminación de Analysis.

## Riesgos y brechas técnicas

| Severidad | Hecho verificable | Implicación / propuesta |
| --- | --- | --- |
| P1 | `consume` está en adaptadores web; `capture.interpret`/`media.receive` llaman TrainingService directo | Cuotas comerciales eludibles por WhatsApp; centralizar entitlements y reservas idempotentes |
| P1 | `identity.resolve` busca identidad activa sin verificar User.is_active; captura valida identidad, no cuenta | Inferencia: cuenta desactivada podría seguir registrando por WhatsApp; añadir guard compartido y prueba de regresión antes de cobrar |
| P1 | Coach lista todos Athlete/User y sube para athlete_id sin relación de asignación/consentimiento | Definir contrato multiusuario/organización y limitar acceso antes de ofrecer SaaS abierto |
| P1 | Seed actualiza password_hash de cuentas demo en cada arranque; Compose tiene DEMO_PASSWORD default demo1234 | Riesgo de credenciales demo previsibles/reestablecidas si deployment usa defaults; config remota no verificada |
| P1 | `saved_week_link` crea enlace tras Guardar entrenamiento o nota si base válida | Compartición automática con alcance vivo; revisar consentimiento y UI antes de beta abierta |
| P1 | Login sin limitador explícito y sin recuperación; SESSION_SECRET tiene fallback en código | Fortalecer login/config de producción; Compose exige variable pero no prueba entropía real |
| P2 | BackgroundTasks y recuperación que marca FAILED | Pérdida de jobs al reiniciar; cola durable para volumen/SLA, no rehacer todo el backend |
| P2 | list_sessions limit(200); referencias JSONB | Historia truncada y relaciones sin FK; paginar y evitar dependencia del listado para vincular detalle |
| P2 | consumo reserva y commit antes de validar/proveedor | Fallos/deshabilitación técnica pueden gastar cuota; definir reserva/cargo/reembolso idempotente |
| P2 | Nota se copia en adaptations y athlete_notes; fields omite athlete_notes | Edición web puede divergir de notas estructuradas; separar semántica y serializar |
| P2 | No lifecycle completo de fotos web/cuentas; retención ligada a worker | Diseñar borrado/export y limpieza por referencias; probar restore |
| P2 | Workflow GitHub solo POST al deploy en push main | Incorporar gates de validación antes de release; no existe resultado de CI vigente en auditoría |
| P3 | on_event deprecado | Migrar a lifespan en fase de mantenimiento, sin cambiar comportamiento |

No se halló protección CSRF explícita ni validación de Origin para todas las mutaciones; cookie SameSite=lax aporta un control parcial. La explotabilidad no fue probada y no se afirma una vulnerabilidad confirmada. No se hace evaluación legal de cumplimiento: privacidad técnica documentada no equivale a cumplimiento regulatorio certificado.

## Propuesta evolutiva

Conservar monolito, TrainingService, adapters HTTP/WhatsApp, reglas de ownership, catálogo y contratos. Agregar servicio de entitlement/usage transversal, score/mediciones tipadas y ledger de eventos con idempotencia. Mantener video como capacidad especializada y review humana. Introducir job durable cuando carga/entrega lo justifiquen; no se necesitan microservicios para el próximo MVP. Detalle multidisciplina en [04](04_MULTISPORT_READINESS.md).

## Adenda: E2E actuales del 09-10 y cierre

Después de la suite Python se inició un servidor **temporal** `tests.e2e.app` con PHASE01_E2E=1 y TEST_DATABASE_RESET=1, la misma DB desechable movement_test, código copiado a /tmp y puerto host **127.0.0.1:18779**. El fixture sustituye solicitudes de interpretación/transcripción y pose por respuestas deterministas; FFmpeg/media, autenticación, API y PostgreSQL son reales. El servidor nunca importó .env del producto ni usó credenciales reales.

`tests/e2e/phase01.cjs` produjo:
- PASS Bitácora texto: propuesta no guardada, confirmación, lectura y edición.
- PASS Bitácora foto: carga, interpretación, guardado y privacidad.
- PASS Bitácora audio: micrófono, FFmpeg, transcripción, propuesta y confirmación.
- PASS Athlete UX: análisis persistido, media y solicitud de revisión.
- PASS Coach UX: iniciar, comentar, guardar y completar revisión.
- PASS Athlete UX: feedback del coach visible; sin errores JavaScript.

Tras reset exclusivo del fixture, `tests/e2e/weekly.cjs` produjo **Weekly E2E passed: navigation, sharing, anonymous photos, desktop/mobile, revocation**. Los screenshots/fixtures se escribieron en TEMP, sin sobrescribir results ni datos del repositorio. Vista móvil emulada, no dispositivo físico. No hay evidencia nueva de calidad de IA real o tráfico WhatsApp real.

Incidentes de harness E2E resueltos: Docker no publicó puerto en red exclusivamente interna; se agregó bridge al servidor temporal y se reinició para aplicar puerto loopback. Esto habilitó conectividad local; el servidor continuó con providers/pose fixture y clave ficticia. El primer arranque semanal se intentó antes de readiness y falló socket hang up; después del health interno aprobado, el mismo runner pasó. No se confunden esos intentos con fallas del producto. La suite Python anterior mantuvo red interna sin salida; el E2E tuvo bridge y sustituciones explícitas de proveedores.

No se ejecutaron E2E contra localhost:8000/8001 ni contra Easypanel. Todas sus escrituras fueron sobre fixture/DB/storage temporales. No se crearon tokens ni se enviaron mensajes en sistemas persistentes. Se eliminaron únicamente los contenedores/red nombrados para la auditoría; no se reconstruyeron imágenes ni se reiniciaron servicios del producto.

E2E reproducible: levantar `tests.e2e.app:app` solo con DB movement_test, flags de fixture y modelo de imagen existente; esperar /health; ejecutar phase01.cjs con PHASE01_E2E_URL loopback, reiniciar **fixture** para limpiar datos, esperar health y ejecutar weekly.cjs con WEEKLY_E2E_URL, WEEKLY_E2E_PHOTO y WEEKLY_CAPTURE_DIR en TEMP. Mantener errores/salida del proceso y no presentar IA fixture como validación de proveedor.


