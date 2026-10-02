# Athlete UX — implementación y validación

Fecha: 2026-10-02. Baseline: DESIGN.md y Coach UX aprobados. Alcance exclusivo del atleta. No se cambiaron identidad, paleta, rutas, permisos, requisitos de cierre ni reglas de análisis/revisión. No se añadieron capacidades IA.

## Hallazgos y correcciones

| Before | After | Why |
| --- | --- | --- |
| Crear se deshabilitaba sin explicar requisitos pendientes | Lista de requisitos y estado «Listo para subir y analizar»; objetivo obligatorio con ejemplos | Explicar el bloqueo sin alterar validación de backend |
| La entrada aceptaba cualquier MIME de video, aunque el backend admite cuatro extensiones | Requisito de MP4/MOV/M4V/AVI visible; validación local refleja la existente | Evitar una subida que sabemos que el backend rechazará |
| Preview dentro de un label de archivo | Preview independiente con controles y playsinline; selección/reemplazo explícitos | Controlar el video no debe volver a abrir el selector |
| Doble envío posible y progreso solo en texto | Guard de subida, campos congelados y progress accesible; errores conservan el formulario | Evitar operaciones repetidas y explicar envío/confirmación |
| Polling sin manejo de fallos | Lecturas seriales, recuperación automática y consulta manual; errores de acceso detienen reintentos automáticos | Una desconexión no equivale a un análisis FAILED |
| Resultado abría con original y detalles técnicos | Qué mirar primero, siguiente paso, feedback humano, video anotado, momentos automáticos, métricas/reps y original secundario | Orientar la decisión sin eliminar datos |
| CTA de solicitud siempre igual y al final | CTA contextual al inicio: solicitar / esperando / ver revisión | Hacer visible el siguiente paso |
| Listado solo conocía el estado técnico | Metadatos de revisiones mediante consulta agrupada y badge «Revisión disponible» | Separar procesamiento y disponibilidad de feedback humano |
| Selección no mostraba solicitudes existentes | Solicitudes visibles antes de coaches; bloquea solicitudes activas al mismo coach | Evitar duplicados sin prohibir otros coaches ni nuevas revisiones tras completar |
| Error de POST podía permitir reintentar una escritura ya confirmada en servidor | Reconsulta solicitudes; si tampoco puede leer, bloquea hasta recargar; conserva error original | No simular éxito ni repetir escrituras ambiguas |
| Feedback abría con clasificaciones y detalles | Punto principal → comentarios con salto al timestamp → próxima sesión → detalles adicionales | Priorizar qué trabajar y conectar comentario/video |
| Refresh podía reconstruir repeticiones y reiniciar el video | Limpieza de filas y asignación de src solo si cambia; render completo solo cuando cambian datos | Preservar reproducción y evitar duplicación visual |
| Navegador conservaba JavaScript antiguo después de recargar | Assets versionados en HTML | Asegurar carga de la implementación actual |

## Archivos de esta fase

- `app/static/app.js`: formulario/subida, listado, resultado, polling, feedback y selección del coach. Los handlers de Review Studio no se modificaron.
- `app/static/athlete-state.js`: estado contextual, requisitos y polling serial recuperable.
- `app/static/index.html`: jerarquía del atleta, recomendaciones, progreso, estados y assets versionados.
- `app/static/styles.css`: reglas limitadas a superficies del atleta; tokens existentes, 44 px y responsive.
- `app/main.py`: solo metadatos aditivos `coach_reviews` del listado del atleta, agrupados y limitados a sus análisis. Reutiliza `_review_fields`; ninguna ruta o regla de negocio nueva.
- `tests/athlete-state.test.cjs`, `tests/athlete-integration.test.cjs`: 18 tests nuevos.
- `tests/test_athlete_review_metadata.py`: 2 tests nuevos de metadatos/persistencia/aislamiento.
- `tests/test_athlete_flow.py`, `tests/test_coach_requests.py`: dos aserciones de copy estático actualizadas; preservan todas las aserciones de negocio existentes.
- Este informe. Los scripts y evidencias de QA están en `.impeccable/review/` (ignorado por Git).

## Tests antes/después

| Suite | Baseline aprobada | Final |
| --- | ---: | ---: |
| Python completa | 143/143 | 145/145 |
| JavaScript completa | 23/23 | 41/41 |

Python: `docker compose -p movement-athlete-test -f compose.test.yml run --rm` con código y tests actuales montados, `pytest -q`: 145 passed, 3 warnings de deprecación, 72.51 s. Base PostgreSQL `movement_test`, exclusiva de pruebas. JavaScript: `node --test tests/*.test.cjs`: 41 pass, 0 fail/skip. `git diff --check` y `node --check` sin errores.

Primera ejecución Python: 143 pasan, 2 fallan. Causas: una segunda aserción de copy antiguo y la nueva fixture completada sin `main_focus`, `next_session`, `completed_at`. Se corrigieron test/fixture; no se relajó ninguna restricción de producto. No hay tests excluidos o expectativas de negocio debilitadas.

Cobertura nueva: los tres CTA; disponibilidad independiente del estado técnico; objetivo con espacios y extensiones permitidas; polling offline/503 y recuperación; 401/403/404 sin retry automático; serialización y respuestas tardías; FAILED terminal; espera de coach; listado real; orden y conservación del feedback; timestamp real del handler; diferenciación automático/humano; solicitud existente; doble clic/409 sin falso éxito; escritura de resultado incierto; refresh sin recargar videos ni duplicar reps. Los 23 tests existentes de Coach UX siguen verdes.

## E2E contra backend real

Entorno aislado `movement-athlete-e2e`, PostgreSQL real con migraciones al head y seed **solo de usuarios**. Uvicorn en `127.0.0.1:8771`. Sin stubs de análisis, endpoints ni escrituras. Capa opcional del proveedor IA deshabilitada (`ai_reasoning.status=DISABLED`); no se llama a servicios externos.

Recorrido ejecutado en navegador:

1. Login `gaston` → formulario con requisitos → archivo seleccionado y preview → subir y procesar.
2. Primera captura `landing-analysis-example.mp4`: FAILED real por resolución insuficiente. Se conserva registro `9f8b762eae6b`, muestra detalle real y reanálisis; no se simula éxito.
3. Segunda captura `landing-demo.mp4` de 1280×720: subida con progreso y procesamiento real → COMPLETED `ca8cdbb9216b`, métricas y video anotado. Detecta **cero repeticiones**; la interfaz comunica ese dato.
4. Solicitar a Carlos → «Esperando revisión del coach». Volver a selección → solicitud existente visible y botón de Carlos bloqueado.
5. Detener solo el backend aislado: «Conexión interrumpida», conserva resultado y solicitud. Restaurar backend: recuperación automática de la misma solicitud.
6. Logout atleta → login `carlos` → bandeja → Review Studio existente → iniciar revisión → mover video a 2 s → crear comentario → escribir punto principal y próxima sesión → «Guardar y completar revisión».
7. Logout coach → login atleta → listado «Revisión disponible» → abrir feedback → comentario lleva a **2.00 s** del video y lo deja pausado → próxima sesión visible.
8. Nueva sesión HTTP independiente: reconsultar listado y detalle, verificar una única revisión COMPLETED, una anotación a 2 s, textos exactos y video anotado accesible. Evidencia `athlete-persistence.json`. La comprobación no usa el estado del navegador ni siembra resultados.

## Responsive y revisión de interacción

Cinco pantallas revisadas a 320, 390, 768 y 1440 px: creación, listado, resultado/feedback, selección de coach y error de procesamiento. Sin desbordamiento horizontal. Controles personalizados medidos ≥44 px. CTA principal medido 44 px en los cuatro anchos. Inputs de texto/objetivo 16 px; selector nativo de archivo conserva tipografía propia de la baseline. Video cabe en todos los anchos y el salto a 2 s se verificó a los cuatro tamaños. Evidencias: `athlete-responsive.json`, `athlete-responsive-final.json` y PNG por pantalla/tamaño.

Impeccable: conserva DESIGN.md, jerarquía orientada a tarea, error real separado de conexión, estados accesibles y datos técnicos secundarios. No se añadieron modales ni prompts de edición.

### review-animations / Emil

| Before | After | Why |
| --- | --- | --- |
| Salto al timestamp con scroll automático y feedback de contorno existente | Se conserva, sin transición decorativa | Respuesta inmediata y ubicación del momento |
| Feedback de controles de la baseline, focus-visible y reduced-motion existentes | Se conserva; no se añadieron animaciones de entrada o layout | Mantener interacción frecuente breve y accesible |

Veredicto: **Approve para el diff Athlete UX**. Sin motion añadido ni regresiones detectadas. Referencias: `app/static/app.js` (`seekAthleteVideo`), `app/static/styles.css` (focus-visible y prefers-reduced-motion). Esta revisión no reabre el diseño aprobado ni la animación de pantallas ajenas al atleta.

## Límites y pendientes

- El E2E usó una muestra con cero repeticiones. Varias reps, varios comentarios y observaciones automáticas existentes tienen cobertura de tests; falta ampliar el recorrido real con una captura larga del ejercicio correcto y varios momentos. No se atribuye la segmentación al cambio UX ni se cambia el algoritmo para forzar datos.
- El proveedor IA externo estuvo deshabilitado en QA. No se afirma una validación E2E de ese proveedor; no se añadieron capacidades IA.
- Pendiente dispositivo físico: teclado virtual y scroll al objetivo/carga, selector/cámara y reemplazo de archivo, formatos HEVC/MOV según dispositivo, controles y seeking de video en Safari iOS/Chrome Android, subida lenta y cambios Wi-Fi/datos/background. La emulación de viewport no sustituye estas pruebas.
- Sin read receipts ni notificaciones nuevas: «Revisión disponible» indica disponibilidad persistida, no una afirmación de que el atleta nunca la vio. La espera se reconsulta mientras el detalle está abierto y al volver al listado.
- Tres warnings de deprecación de dependencias existentes; suite verde. Ninguna regresión atribuible a esta fase detectada.

Solo los contenedores temporales creados para esta fase se retiran después de guardar la evidencia. Los entornos y datos anteriores de la aplicación se conservan.
