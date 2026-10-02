# Review Studio: implementación UX del coach

> Informe histórico de implementación. La validación técnica posterior está en [coach-baseline-validation.md](coach-baseline-validation.md): 143/143 tests Python, 23/23 JavaScript y E2E contra FastAPI/PostgreSQL reales aislados. Sus resultados sustituyen las limitaciones de validación que se enumeran abajo.

Baseline: DESIGN.md, identidad vigente, rutas y contratos existentes. Sin cambios en backend, permisos o reglas de negocio. Trabajo limitado al coach.

## Comportamiento

- Resumen local por campo: hydrate conserva campos editados y actualiza los intactos; acknowledge reconoce el snapshot enviado y mantiene ediciones posteriores como pendientes.
- Indicador Cambios sin guardar, aviso antes de abandonar/recargar la página y conservación de resumen/editor durante recargas de clasificación, IA, anotación y estado. El borrador vive en memoria mientras la página está abierta; no se añade almacenamiento de contenido del coach en el navegador.
- Guardar y completar: PATCH summary pendiente, validación de cuatro requisitos existentes y POST complete. Fallos conservan el contenido; completar bloquea edición y muestra el atleta real. Si guardar funciona y completar falla, el resumen queda guardado y permite reintentar.
- Se bloquean operaciones simultáneas durante peticiones y el cierre. El resumen puede seguir editándose durante un guardado normal; esos cambios posteriores permanecen pendientes.
- Momentos y observaciones unificados por ID, con timestamp válido; orden prioritario conservado. Selección conecta video, repetición, observación, motivo y confianza. Los tres conceptos se mantienen separados: lectura local, decisión IA persistida y anotación para el atleta.
- El progreso de momentos revisados es local a la sesión de página; no se reutiliza CONFIRMED para persistir ese progreso ni se cambia el contrato backend.
- Edición IA inline, limitada a 240/800 caracteres según API. Sin prompts del navegador. Confirmación nativa de eliminación conservada.
- Video sticky junto a momentos, editor y clasificación. Desplazamiento contextual inmediato, con márgenes para evitar que el video oculte controles. Sin nuevas animaciones.

## Tests y evidencia

- `node --test tests/review-state.test.cjs`: **11/11**. Cubre refresh, campos intactos, snapshot de guardado, edición concurrente, orden save/complete, fallos y reintento, requisitos y deduplicación de momentos.
- Suite existente completa en PostgreSQL desechable: **54 passed, 43 failed, 46 errors**. No se declara verde. Incluye tests antiguos sin sesión (401) y errores de esquema que afectaron pruebas posteriores.
- Reejecución desde PostgreSQL desechable limpio de complete_review, coach_annotations y review_moments: **9 passed / 9 failed**; anotaciones y prueba API de momentos fallan por llamadas no autenticadas.
- Reejecución de `test_complete_review.py` + `test_basic_auth.py`: **16 passed**.
- Backend, modelos y router/navegación por rol comprobados sin cambios. Sintaxis JS verificada.
- Navegador con fixtures mutables en memoria: borrador conservado tras clasificar, descartar IA y anotar; guardado reconocido; faltantes visibles; fallo de save y complete recuperables; cierre exitoso bloqueado; segundo comentario habilitado; Enter en Siguiente momento saltó a 3 s con transform none.
- Responsive: editor abierto a **320, 390, 900, 1100 y 1440 px**, sin overflow horizontal ni controles inspeccionados menores de 44 px. Evidencia en review/studio-final.json. Última comprobación móvil 390×844: textarea y acciones bajo el reproductor, sin oclusión del campo.
- Fixtures: .impeccable/studio-fixtures.cjs; no forman parte de la aplicación ni acceden a PostgreSQL. Capturas locales en review/studio-final-390.png y studio-final-1440.png.

## Impeccable / Emil / review-animations

| Before | After | Why |
| --- | --- | --- |
| Recarga sobrescribe resumen | Borrador por campo y snapshot reconocido, review-state.js:8 | Preserva trabajo y ediciones realizadas durante una petición. |
| Dos bloques IA y edición con prompts | Contexto de momento junto al video, app.js:663 | Reduce cambios de contexto y distingue lectura/decisión/feedback. |
| Campo enfocado detrás del video sticky | Desplazamiento inmediato del editor y scroll-margin, app.js:924 y styles.css:397 | Mantiene foco y acción visibles sin movimiento decorativo. |
| Cambio de momento | Salto inmediato y foco sin desplazamiento animado | Acción frecuente y de teclado: no debe animarse. |
| Feedback 120/150 ms, hover condicionado y reducción | Conservados desde baseline | Propiedades explícitas; sin ease-in, scale(0), transition all ni layout animado. |

Veredicto **review-animations: Approve**. No se detectaron regresiones de motion en las interacciones comprobadas. Reduced-motion revisado en CSS; sin emulación ni pruebas físicas de teléfono.

## Validación pendiente con backend real

E2E desde sesión coach real: clasificar/confirmar/anotar con resumen sucio; inicio de revisión pendiente; guardar y completar con normalización; 401/403/409/503; reconexión y fallos entre ambos endpoints; feedback del atleta y bloqueo persistente tras recargar. Probar teclado virtual y sticky video en Safari/iOS y Android. La suite de autenticación/cierre sí utilizó PostgreSQL real aislado; la interfaz interactiva se validó con fixtures.
