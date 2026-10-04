# Fluxio Movement — composición de referencia V2

## Overview

**Creative North Star: "Libreta de rendimiento"**

La imagen proporcionada guía la composición. Bitácora y registro usan Operate; semana pública usa Read/editorial. DESIGN.md conserva la referencia funcional y .impeccable/design.json no se regenera en esta entrega. Backend, rutas, permisos y contratos permanecen como autoridad funcional.

## Colors

Canvas #f5f6f6; surface #fff; soft #eef1f1; texto #101819; secundario #626b6f; borde #e3e7e8; brand #07392b; rail/hero #08251e; accent #c9f274. WhatsApp usa #183e32, blanco y marca oficial lima. Las categorías mantienen colores y etiquetas explícitas.

## Typography

Inter local con fallback de sistema. Heading de bitácora 28px escritorio y 24px móvil; subtítulo 13/12px. Sesión 18/14px, resultado 13/11px, categorías 10/9px. Campos de 16px y cifras tabulares. Resumen semanal: métricas 30px/26px móvil, fecha 25px/23px móvil. Hero público en mayúsculas: clamp(32px,4.2vw,48px), interlínea 1.02 y tracking -.035em; 36px en móvil. Métricas públicas 28/24px.

## Layout

Rail de 184px sobre 900px; libreta de 960px centrada y registro de 640px. Solo la tarjeta de resumen se amplía a 1180px; las demás secciones conservan 960px. Grid explícito con mínimos 260/320/240px, gap y padding de 24px. Altura medida de 266px a 1440px, aproximadamente el objetivo de 260px; sin altura fija ni remate deportivo. Thumbnail de 108 × 80px, o 58 × 58px móvil. Sesión de al menos 110px, o 80px móvil.

A 600px: navegación inferior de 68px más safe area y + circular de 44px junto al título. Guardar permanece sobre la navegación y pasa a flujo normal al abrir el teclado. Resumen: tres columnas sobre 1180px; dos entre 768 y 1180px, con compartir debajo; una hasta 767px. El intervalo adicional 1025–1180px evita comprimir los mínimos por el rail de 184px y los 64px de padding. Compartir mantiene el dialog existente. Semana pública de 1000px, hero de dos columnas y una a 600px.

Orden workspace: styles.css → training.css → visual-v2.css → weekly-expanded.css → reference-ui.css → weekly-summary.css; admin.css conserva su carga existente. La página pública carga sus estilos base y weekly.css; el bloque editorial final determina su composición.

## Elevation & Depth

Sombra ambiental de sesión/resumen: 0 2px 10px rgba(16,24,25,.025). El resumen es inline; el dialog existente de compartir mantiene su backdrop. Campos y opcionales se separan mediante bordes y espacio.

## Shapes

Radios: categoría 4px; thumbnail 6px (5px móvil); campo y guardar 8px; WhatsApp/bloques 10px; sesión 12px (10px móvil); resumen semanal 20px y sus thumbnails 10px; hero 16px (14px móvil). Objetivos táctiles de al menos 44px. Ritmo de espacios: 8, 12, 16, 20, 24 y 32px.

## Components

Header compacto con + móvil; fila WhatsApp verde; resumen inline con cifras y siete barras; sesiones con categoría y menú Editar/Eliminar. Registro de una columna con foto integrada, resultado compacto, bloques editables y opcionales plegables; guardar verde profundo. No truncar prescripciones largas.

Resumen inline: overview → entrenamientos → compartir. Lista central con tres filas visibles de 56px y scroll para la cuarta; thumbnails de 56px, categoría y fecha. Títulos en una línea con ellipsis y min-width:0; sin corte carácter por carácter. Divisores verticales escritorio y horizontales móvil. Crear enlace reutiliza el handler existente; fila de enlaces activos abre su dialog. Hero público oscuro con foto únicamente autorizada. Ausencias de foto o datos mantienen estados explícitos.

Lucide 0.468.0 local (ISC), adaptador fluxio-icons.js y SVG decorativos ocultos a lectores de pantalla; WhatsApp conserva su marca oficial. Foco visible y restauración de foco al cerrar según contexto.

Bitácora sin entrada animada. Resumen inline sin entrada animada; compartir: 200ms y 12px; easing cubic-bezier(.16,1,.3,1). Solo activación por puntero con movimiento permitido. Teclado y movimiento reducido abren instantáneamente. Cancelar animaciones al cerrar/desmontar. Hover condicionado a hover:hover y pointer:fine.

## Do's and Don'ts

- **Do** conservar interpretación, carga, confirmación manual, edición, eliminación, video, vencimiento y revocación.
- **Do** usar datos reales y media dentro del alcance autorizado.
- **Do** mantener campos de 16px, safe areas y objetivos de 44px.
- **Don't** reconstruir URLs de tokens anteriores ni inventar fechas de creación ausentes.
- **Don't** inferir nuevos entrenamientos o evaluación técnica desde movimientos reconocidos.
- **Don't** declarar validación de teléfono físico a partir de emulación.

Evidencia de la composición inicial: results/visual-reference/DELIVERY.md. Reconstrucción exclusivamente del resumen semanal: results/weekly-card/DELIVERY.md.
