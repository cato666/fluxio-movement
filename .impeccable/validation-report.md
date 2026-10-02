# Validación del baseline aprobado

Fuente de verdad: DESIGN.md. Auditoría Impeccable y review-animations con criterios de Emil Kowalski. Datos sintéticos locales, endpoints de escritura bloqueados.

## Auditoría inicial

| Prioridad | Problema | Corrección prevista |
| --- | --- | --- |
| Crítico | Saltos al video en tarjetas IA, repetición y comentario dependen del clic en contenedores no accesibles por teclado. | Botones nativos para el mismo salto existente. |
| Crítico | Foco verde sobre el reproductor verde oscuro con contraste insuficiente. | Anillo lima como en el rail. |
| Medio | Logo público, regresos y botón 1x tienen dimensiones inferiores a 44 px. | Ampliar área táctil sin cambiar jerarquía. |
| Medio | Hover borra la apariencia seleccionada de filtros, clasificación y tabs. | Mantener selección durante hover. |
| Medio | Scroll suave al video ignora movimiento reducido; presión con teclado anima controles. | Salto inmediato y feedback de foco sin escala por teclado. |
| Medio | Selección de coach vacía no comunica ausencia de resultados. | Mensaje de estado vacío. |
| Medio | Una revisión que falla al cargar deja controles vacíos y el error al final. | Ocultar únicamente la presentación de datos sin cargar; mantener título, regreso y error. |
| Polish | Fondo y overlay del video público conservan el azul anterior; declaraciones de color antiguas duplicadas. | Aplicar los tokens aprobados y retirar la variante oscura obsoleta. |
| Polish | Etiquetas públicas de 11 px, filas largas y métricas con bordes sobrantes al envolver. | Legibilidad y wrapping controlados. |

## Revisión de motion

| Before | After | Why |
| --- | --- | --- |
| Presión .97 también con teclado | Escala solo fuera de focus-visible | El teclado necesita feedback de foco inmediato. |
| scrollIntoView smooth incondicional | Salto inmediato al video | Acción frecuente; evita movimiento de cámara y respeta reducción. |
| Transiciones explícitas 120/150 ms y hover condicionado | Conservar | Propiedades acotadas, sin entradas decorativas ni animación de layout. |

Veredicto inicial: **Block**, limitado a teclado y salto al video. No se propone una nueva animación ni un nuevo lenguaje visual.

## Cobertura inicial

14 rutas inspeccionadas: landing general, atletas, coaches, demo, login, nuevo análisis, listado, detalle, selección de coach, subida por coach, registro de atleta, revisiones, detalle de revisión y uso interno. Capturas desktop 1440 y móvil 390, inspección DOM de overflow y objetivos táctiles. Sin desbordamiento horizontal a 390 px. Las tres páginas públicas comparten plantilla con copy contextual. No existen tablas HTML ni modales propios: uso interno presenta filas y las confirmaciones/edición IA usan diálogos nativos. No se sustituyen estos flujos.

## Resultado y validación final

Corregidos los críticos, después los medios y el polish de este informe. DESIGN.md y la identidad verde profundo + lima permanecen intactos. No se modificaron backend, rutas, llamadas API, permisos, contratos ni condiciones de edición. El cambio de JavaScript se limita a controles accesibles y presentación de estados.

- Matriz inicial final: **70 combinaciones**, 14 rutas × 320, 390, 900, 1100 y 1440 px, sin overflow. Los enlaces públicos de navegación medían 22 px en desktop/tablet y se ampliaron después a 44 px; medición confirmada a 1100 px.
- Segunda confirmación: **62 combinaciones completadas**, sin overflow ni objetivos interactivos menores de 44 × 44 px. El navegador dejó de responder durante las últimas ocho combinaciones; no se presentan como verificadas. Ya estaban cubiertas por la primera matriz. Evidencia JSON en `review/confirmation.json` y `review/final-checks.json`.
- Estados comprobados en navegador: listado vacío, coaches vacíos, error de listado, carga de listado, procesamiento 64 %, análisis fallido, revisión pendiente, en revisión, completada y sin anotaciones. Editor de comentario abierto en móvil: sin overflow y foco visible. Enter en «Ver repetición 2» posicionó el video en 2 s, sin transform en el control enfocado.
- El ajuste posterior que simplifica la pantalla de error de revisión se verificó en código; la captura posterior quedó bloqueada por el timeout del navegador.
- Contraste calculado desde tokens: texto 14,74:1; secundario sobre canvas 5,22:1 y soft 4,90:1; placeholder 4,87:1; botón primario 7,73:1; estados semánticos 5,07–5,81:1. Foco lima sobre verde oscuro **11,36:1**, antes 1,87:1.
- Sin restos de la paleta azul comercial anterior. Los aliases `--lp-blue` apuntan al verde aprobado; el azul semántico de «Procesando» permanece porque pertenece a DESIGN.md.
- `node --check` correcto para frontend y servidor de fixtures. IDs HTML, nombres de campos y líneas de llamadas API idénticos al inicio de esta fase. Router y navegación por rol idénticos a HEAD.
- Hover/selección y reducción de movimiento revisados en CSS. No se añadieron animaciones. No hay `transition: all`, ease-in ni transiciones de layout; presión 120 ms con curva aprobada, color/borde 150 ms, reducción 100 ms sin transform y teclado sin transición. Confirmaciones y prompts nativos revisados en código, sin ejecutar operaciones de escritura.

Veredicto final de **review-animations: Approve**, para las interacciones revisadas. Sin regresiones de movimiento detectadas; la comprobación de prefers-reduced-motion es de código, no una emulación en navegador.

Limitaciones: QA con fixtures sintéticas y viewport de navegador; no valida datos de producción, backend, dispositivos físicos ni teclado virtual móvil. Los archivos en `review/` contienen evidencia local ignorada por Git. No se desplegó la aplicación.
