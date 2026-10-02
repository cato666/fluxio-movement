# Mobile UX — 2026-10-02

Identidad de DESIGN.md conservada. Cambios exclusivamente de presentación; APIs, rutas, permisos y reglas de negocio conservados.

## Auditoría previa

Navegación superior desplazable; contexto y requisitos antes del video; motivos/confianza IA y selector completo de momentos compiten con las acciones; métricas y repeticiones desplegadas en el resultado; carga opcional ocupa espacio del formulario. El resultado del atleta ya priorizaba resumen, siguiente paso y feedback humano: se conserva ese orden.

## Cambios

Navegación inferior por rol en móvil, encabezado compacto, padding de 12–14 px, video inline y ancho completo, selector contextual «Momento N de M», confianza/motivos/validación IA bajo «Ver detalles». Métricas, repeticiones, original y carga opcional plegados en móvil. Controles de subida y resumen sticky dentro de su formulario. Al superar 600 px se restauran los nodos originales conservando valores y handlers. Desktop conserva su composición y los detalles IA siguen visibles.

## Medición reproducible

Fixtures sintéticos, Chromium 375 × 800. Altura total del documento, no tiempo de tarea ni medición en teléfono. La reserva de navegación está incluida. Antes usa HTML actual con CSS/JS de HEAD, sin mobile-ux.js.

| Flujo | Altura antes | Altura después | Scroll aproximado antes/después (pantallas de 800 px) |
|---|---:|---:|---:|
| Crear análisis | 1648 px | 1602 px | 1.06 / 1.00 |
| Resultado atleta | 3223 px | 2446 px | 3.03 / 2.06 |
| Studio con momento seleccionado | 5517 px | 2898 px | 5.90 / 2.62 |

Distancia entre borde inferior del video y «Comentar»: 551 → 374 px en la captura medida. Revisar y avanzar conserva 2 taps; comentar y guardar conserva 2 taps más escribir. Guardar/completar conserva 1 tap cuando se cumplen los requisitos. Expandir un detalle requiere 1 tap adicional. No se afirma una reducción de taps de selección nativa de archivos ni teclado. El siguiente paso del atleta sigue al resumen inicial; los CTAs de subida/cierre permanecen disponibles durante el scroll del formulario, no globalmente desde cualquier sección.

## Evidencia

mobile-qa.json: nueve rutas a 320, 375, 430 y 1280 px sin overflow; revisar/avanzar y restaurar desktop aprobados. mobile-metrics.json: mediciones antes/después. Capturas mobile--analyses-new.png, mobile--analyses-1.png y mobile--coach-reviews-2.png. Fixtures de navegador son sintéticos; no equivalen a E2E completo contra backend real.

JavaScript: 41/41 tests aprobados.

## Validación física pendiente

No hay teléfono conectado. Fase móvil completa requiere iPhone Safari y Android Chrome: retrato/paisaje, teclado sobre comentarios/resumen, archivos y cámara, video inline/fullscreen, salto timestamp, navegación inferior y safe areas. Safari requiere comprobar el teclado y home indicator; Chrome Android debe comprobar resizes-content y navegación del sistema. No se introdujo un modal/sheet nuevo: la edición sigue inline. No se fuerza capture para conservar selección de videos existentes.

Flujos adicionales en navegador a 375 px aprobados: atleta expande repeticiones y salta al video; coach comenta el momento, guarda comentario y guarda/completa la revisión. Se ejecutan contra servidor de fixtures con escrituras en memoria, no producción.

Python: 145/145 tests aprobados en Docker con PostgreSQL aislado; tres warnings de deprecación existentes.
