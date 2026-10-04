---
name: Fluxio Movement — Libreta de rendimiento
status: recomposición aprobada e implementada en bitácora, registro y recap
date: 2026-10-04
scope: dirección visual del producto; presentación e interacción de capacidades existentes
supersedes: dirección previa en superficies implementadas; DESIGN.md registra el sistema real
---

# Fluxio Movement · Dirección visual V2

## Estado de implementación

El usuario aprobó la recomposición real de Bitácora, Resumen semanal y Registrar entrenamiento después de rechazar la primera V2 por demasiado similar. DESIGN.md y .impeccable/design.json registran el sistema final; las secciones siguientes conservan la propuesta histórica y no son tokens normativos.

La versión final conserva sidebar evergreen de 208 px y el logo existente, con lima/navy en Registrar/Guardar. Bottom navigation blanca opera hasta 600 px, barra compacta hasta 900 px y sidebar desde 901 px. Bitácora y registro ahora alcanzan 1080 px, con cabecera desktop de 44 px y subtítulo de 16 px, WhatsApp como feature row, weekly card horizontal con siete días factuales, badges de categoría, iconos de fecha/RPE y sombra discreta de sesión. Registro usa panel guiado, resultado protagonista, accordions opcionales con SVG y acción sticky; Registrar también queda fijo sobre la navegación móvil.

El recap de 1120 px combina hero, tarjetas de métricas y destacados factuales, timeline compacto y movimientos repetidos reconocidos únicamente en texto autorizado mediante ocho nombres conocidos. No inventa técnica, progreso ni logs. Los enlaces actuales muestran semanas LIVE autorizadas, conforme a la corrección funcional previa; se conservan enlaces ya creados, caducidad, revocación y seguridad. Las referencias a snapshot de las secciones siguientes son contexto histórico de la propuesta, no el comportamiento actual. Análisis, revisión, marketing y autenticación mantienen su composición incumbente.

El hero del recap apila hasta 900 px; etiquetas de métricas envuelven y las prescripciones se muestran completas. Las 15 capturas finales y aserciones de bounds/prescripciones pasaron E2E. La evidencia actual está en results/recomposition y su comparison.html; results/visual-v2 conserva la iteración anterior. El equipo reportó E2E funcional, 62 pruebas JavaScript y 454 Python verdes antes de las correcciones finales puramente CSS de wrapping de etiquetas y eliminación del line-clamp de prescripciones. Motion: journal 240 ms, cambio semanal/disclosure 180 ms y reduced-motion. Validación en teléfono físico sigue pendiente; la meta histórica de reducción de cajas 30–40% no se declara medida.
## 1. La idea

**Libreta de rendimiento.** Un espacio personal para registrar, entender y compartir el entrenamiento.
La energía deportiva viene de las fotografías, los resultados y el ritmo de lectura.
La precisión tecnológica aparece en los estados, las mediciones y el feedback inmediato.

La firma visual es una combinación de fondo neutro claro, texto casi negro, resultados tabulares,
imágenes completas y pequeños acentos evergreen/lima. El verde deja de pintar el entorno entero.
La unidad principal es la sesión de entrenamiento: el contenido organiza la pantalla.

Atletas y coaches conservan igual prioridad. Bitácora y recap reciben una composición editorial;
análisis y revisión mantienen densidad suficiente para trabajar con video y feedback.
Linear, Arc, Vercel y Notion son referencias de nivel de acabado del brief, no plantillas a copiar.

**Primera impresión prevista:** una foto reconocible, un resultado claro y la siguiente acción disponible.
**Recuerdo previsto:** “mi entrenamiento se ve cuidado y mi semana merece compartirse”.

## 2. Auditoría de la interfaz actual

Evidencia: DESIGN.md, index.html, estilos y comportamiento de training, renderer público weekly;
capturas locales de registro/edición, bitácora y recap de la fase anterior. Son fixtures sintéticas,
no investigación con usuarios ni una auditoría de todos los estados en dispositivos físicos.

| Antes | Dirección V2 | Por qué |
| --- | --- | --- |
| Rail evergreen de 232 px y canvas gris verdoso | Rail claro de 208 px; verde en selección, marca y acciones | Liberar superficie para el contenido |
| Una caja blanca bordeada envuelve todo el formulario | Grupos abiertos; superficies solo para unidades que necesitan separación | Reducir la sensación de formulario empresarial |
| Campos, instrucciones y controles con peso parecido | Resultado protagonista; datos opcionales y media bajo disclosure | Hacer evidente qué revisar y completar |
| Navegación de retorno como botones grandes repetidos | Retorno textual y una acción principal por área | Simplificar la jerarquía |
| Resumen semanal compacto, pero aún como panel bordeado | Snapshot abierto con datos y enlace “Ver resumen” | Dar continuidad a la libreta |
| Separadores en fecha, fila y sección | Espacio entre días; divisores solo cuando aclaran una relación | Evitar que la cronología parezca una tabla |
| Editar/Eliminar ocupan una fila en cada entrada | Trigger de opciones discreto y siempre accesible | Mantener acciones sin competir con el resultado |
| Hero compartido dominado por bloque oscuro | Cabecera clara y foto protagonista; contraste oscuro localizado | Dar identidad a la semana mediante su contenido |
| Muchas variaciones locales de tamaños, bordes e iconos | Escala tipográfica y familia de iconos únicas | Conseguir coherencia de producto |

El polish anterior resolvió legibilidad y compactación. V2 reemplaza la gramática visual:
navegación, superficies, jerarquía y composición. No se plantea como una colección de ajustes de padding.

## 3. Paleta y tokens de color

Estos son valores propuestos, no variables añadidas al código.

| Token | Valor | Uso |
| --- | --- | --- |
| `color.canvas` | `#F7F7F5` | Fondo general neutro |
| `color.surface` | `#FFFFFF` | Superficie principal |
| `color.surface-secondary` | `#F0F1EE` | Grupos secundarios, media sin cargar |
| `color.surface-hover` | `#E9ECE7` | Hover de superficies interactivas |
| `color.text-primary` | `#181C19` | Títulos, cuerpo y resultados |
| `color.text-secondary` | `#626861` | Metadata, contexto y ayuda |
| `color.text-inverse` | `#FFFFFF` | Texto sobre verde profundo |
| `color.brand` | `#235D43` | Acción primaria, selección, enlaces |
| `color.brand-hover` | `#194B34` | Hover de acción primaria |
| `color.brand-pressed` | `#123A29` | Pulsación primaria |
| `color.brand-deep` | `#102F24` | Player y contraste localizado |
| `color.brand-soft` | `#E8EFE9` | Selección discreta en navegación |
| `color.accent` | `#D5EF87` | Lima: selección, progreso o énfasis puntual |
| `color.border-subtle` | `#E3E6DF` | Separación decorativa excepcional |
| `color.border-control` | `#858B83` | Borde funcional de input cuando se necesita distinguirlo |
| `color.focus` | `#235D43` | Focus en superficies claras |
| `color.focus-inverse` | `#D5EF87` | Focus sobre verde profundo |
| `color.disabled-text` | `#7B8178` | Controles deshabilitados |
| `color.success` / `color.success-bg` | `#246044` / `#EDF5EF` | Guardado, completado; siempre con texto |
| `color.warning` / `color.warning-bg` | `#825317` / `#FBF3E5` | Atención o confirmación pendiente |
| `color.error` / `color.error-bg` | `#A3333D` / `#FBEDEF` | Error o acción destructiva |
| `color.processing` / `color.processing-bg` | `#305E83` / `#EDF3F8` | Procesamiento o revisión |

### Reglas de uso

- Como orientación compositiva: 80–90% de superficie visible neutra; el contenido fotográfico queda fuera de esa cuota.
- El verde profundo se reserva para acciones principales, texto activo, marca y zonas de video.
- La sidebar clara sigue siendo navegación de marca: icono/texto evergreen y selección tonal.
- Lima no es un color de texto sobre blanco. Usar texto oscuro sobre lima o lima sobre fondo oscuro.
- Lima no significa éxito. Los estados usan su token semántico y una etiqueta.
- No teñir todos los backgrounds, placeholders o metadata de verde.
- Contraste mínimo al implementar: 4.5:1 en texto normal, 3:1 en texto grande y límites/estados funcionales.
  Los bordes decorativos no sustituyen el contorno accesible de un control.
- Esta fase propone un sistema claro. No introduce un selector de tema ni una nueva versión oscura.

## 4. Tipografía

Inter local, con los archivos 400 y 600 ya disponibles. Usar pesos reales y evitar simular 700/800.
Una sola familia une libreta, números y herramientas de revisión. No agregar serif ni monospace decorativa.

| Rol | Móvil / desktop | Peso | Interlineado | Tracking |
| --- | --- | --- | --- | --- |
| Display público | 36 / 48 px | 600 | 1.08 | -0.035em |
| H1 de pantalla | 28 / 32 px | 600 | 1.15 | -0.025em |
| H2 | 22 / 24 px | 600 | 1.25 | -0.02em |
| H3 / nombre de sesión | 16 / 18 px | 600 | 1.35 | -0.01em |
| Resultado principal | 24 / 28 px | 600 | 1.2 | -0.025em |
| Body | 16 / 16 px | 400 | 1.55 | 0 |
| Small | 14 / 14 px | 400 | 1.45 | 0 |
| Caption | 12 / 12 px | 400 | 1.4 | 0 |
| Label | 13 / 13 px | 600 | 1.4 | 0 |
| Texto de input | 16 / 16 px | 400 | 1.45 | 0 |

Caption se reserva para contexto complementario: nunca instrucciones necesarias ni errores.
Los valores tabulares usan `tabular-nums`; el resultado textual puede ocupar varias líneas.
No forzar un resultado largo a caber en una única línea. Metadata no debe competir con el resultado.
Títulos públicos con un máximo aproximado de 16–20ch; cuerpo de lectura de 60–72ch.
No colocar kickers decorativos encima de los títulos ni usar mayúsculas sostenidas como jerarquía habitual.

## 5. Espacio, grid, radios y profundidad

| Familia | Tokens propuestos |
| --- | --- |
| Spacing | `4, 8, 12, 16, 20, 24, 32, 40, 48, 64 px` |
| Gap dentro de un grupo | 8–12 px |
| Separación entre grupos | 24–32 px |
| Separación entre días de bitácora | 32–40 px |
| Margen horizontal móvil | 16 px a 320–430 px; 24 px en tablet |
| Padding de superficies excepcionales | 16–20 px móvil; 24 px desktop |
| Radio de input / botón | 12 px |
| Radio de selección / fila interactiva | 10 px |
| Radio de media / unidad de contenido | 16 px |
| Radio de sheet | 20 px en esquinas superiores |
| Radio de estado | 6 px; no hereda forma de botón |
| Elevación base | ninguna |
| Elevación de menú | `0 8px 24px rgba(24,28,25,.08)` |
| Elevación de sheet | `0 -8px 32px rgba(24,28,25,.10)` |

No aplicar sombra y borde decorativo a la misma tarjeta. No sombras pesadas, halos ni efectos glass.
No decorar el fondo con líneas de cuaderno, texturas artificiales ni gradientes.
La sensación de libreta viene del contenido y de su ritmo, no de imitar papel físicamente.

### Layout

- 320–767 px: composición móvil de una columna y bottom navigation.
- 768–1023 px: una columna principal más amplia; navegación de rutas en barra compacta.
- Desde 1024 px: sidebar de 208 px; contenido flexible con padding de 32–48 px.
- Ancho máximo del workspace: 1120 px. Bitácora/lectura: 760 px. Registro: 720 px.
- Recap: 960 px para foto/composición; cuerpo de lectura hasta 720 px.
- Revisión del coach: video + feedback en columnas solo cuando ambos conservan ancho útil;
  en teléfono el video precede al feedback y los momentos siguen siendo encontrables.
- El orden móvil define el orden semántico; desktop amplía la composición sin reorganizar el significado.

### Reducir contenedores entre 30 y 40%

Antes de implementar se cuenta por pantalla: cajas de agrupación, cards y wrappers que tienen borde,
fondo contrastante o elevación. Inputs, botones, players y fotos no cuentan como cajas de agrupación.
En una misma ruta y estado, el objetivo V2 es conservar entre el 60 y el 70% de esas cajas.

Quitar primero: wrapper de formulario, cajas dentro de cajas, marcos de métricas y divisores redundantes.
Conservar: unidades de media, estados que necesitan recuperación y menús flotantes.
Una reducción no se aprueba si borra la relación entre contenido, formulario y acciones.
La cuota es una meta verificable de implementación, no un resultado logrado en este documento.

## 6. Componentes y estados

### Botones

| Variante | Apariencia | Uso |
| --- | --- | --- |
| Primary | Evergreen, texto blanco, sin borde decorativo | Guardar, confirmar, iniciar acción principal |
| Secondary | Fill neutro suave, texto principal, sin marco permanente | Alternativa necesaria de peso medio |
| Ghost | Sin fill; texto evergreen o secondary | Volver, ver detalle, acciones secundarias |
| Destructive | Ghost rojo dentro del menú; rojo sólido en confirmación existente | Eliminar o revocar sin protagonismo permanente |
| Icon button | 44×44 px, icono 20 px, nombre accesible | Abrir opciones o acción contextual |

Altura mínima: 44 px; primary y CTA de registro: 48 px. Padding horizontal: 16–20 px.
Una acción primaria por área. No llenar la pantalla con botones secundarios del mismo tamaño.
El icono acompaña o representa una acción conocida; no reemplaza un label ambiguo.

| Estado | Especificación |
| --- | --- |
| Default | Contraste y tamaño del token de componente |
| Hover | Fill o texto cambia solo con pointer fine + hover disponible |
| Pressed | Transform leve en acciones de toque; respuesta desde pointer-down; sin rebote |
| Focus-visible | Outline de 2 px, offset 3 px; contraste inverso cuando corresponda |
| Disabled | Fill neutral, label deshabilitado; sigue siendo legible y no depende solo de opacidad |
| Loading | Label específico de la operación; ancho estable; acción duplicada bloqueada como hoy |
| Success | Confirmación contextual cerca del resultado de la operación |
| Error | Mensaje legible y recuperación existente; conservar los datos introducidos |

### Inputs

Label arriba, compacto y persistente. Texto a 16 px. Altura de campo simple: 48 px.
Fill neutro suave y contorno funcional fino; focus evergreen, sin glow.
El placeholder es ejemplo, nunca la única etiqueta. Ayuda debajo solo cuando aporta una decisión.
Textarea de resultado con 3 líneas iniciales y crecimiento según el contenido.
Mantener selector de fecha nativo y reglas actuales de validación; presentarlo donde corresponde.
Inputmode decimal para carga/esfuerzo; teclado de email o teléfono solo en sus campos existentes.
Errores junto al campo y resumen contextual cuando procede; no recortar mensajes largos.

### Iconografía

Una familia lineal: geometría de 24×24, stroke 1.75, extremos redondeados, sin relleno habitual.
Tamaño de 20 px en controles; 24 px en navegación móvil. Una sola gramática para los SVG actuales.
Símbolos de overflow, editar, eliminar, media y navegación deben compartir familia y peso.
No introducir una dependencia para obtener iconos si los SVG locales pueden normalizarse.
Ningún emoji o carácter Unicode funciona como sustituto de un icono.

## 7. Navegación

### Desktop

Sidebar clara, compacta, de 208 px. Logo existente en su proporción original.
Filas de 44 px; icono y nombre; activo con fill brand-soft y texto evergreen, sin bloque oscuro grande.
Cuenta y salir al pie, sin una segunda tarjeta. Los destinos y su visibilidad por rol permanecen iguales.
No sumar entradas nuevas ni volver a mostrar Exercise Library.

### Mobile

Bottom navigation con destinos ya permitidos para el rol; icono y label persistentes.
Superficie casi blanca, activo evergreen con señal lima puntual y texto inequívoco.
Los tabs llevan área táctil de al menos 44×44 px; el label puede envolver antes de truncar.
El contenido reserva altura real de la barra más safe-area. No sustituir etiquetas necesarias por iconos solos.
Mantener el comportamiento actual de navegación y validación de sesión.

## 8. Bitácora: composición propuesta

### Primer viewport móvil de 390×844 px

Cabecera compacta: “Mi bitácora” y acción de registrar, sin bloque introductorio largo.
Debajo, weekly snapshot de aproximadamente 110–150 px, sin marco de card.
Siguen fecha agrupadora y primera sesión. Objetivo: título y resultado de la primera sesión visibles
antes de la bottom bar, con contenido normal y disclosure cerrado.
El bloque de WhatsApp conserva acceso y comportamiento; permanece secundario y colapsado.

### Weekly snapshot

Semana seleccionada + entrenamientos/días activos + esfuerzo cuando existe, con tamaño muestral.
“Ver resumen” revela controles de semana, fecha, detalle y gestión de enlaces existentes.
El número de enlaces activos permanece localizable en el snapshot cuando exista.
La advertencia de lo que se comparte se presenta junto a crear enlace, antes de confirmar esa acción.
Estados de carga, error, creación, copia y revocación siguen claros y accesibles.

No agregar una gráfica RPE como decoración. Solo se justificaría con datos por sesión ya autorizados,
sin inferir progreso ni conectar muestras ausentes; no es parte de esta propuesta.

### Entradas

Fecha agrupadora de 14 px. Thumbnail de 72–80 px con imagen completa y fondo neutro.
Nombre de 16 px; resultado de 24 px; nota breve de 14 px; metadata y esfuerzo secundarios.
Evitar repetir la misma fecha en agrupador y thumbnail salvo necesidad real de lectura.
Separar días con espacio. Dentro de un día, usar continuidad de alineación y 20–24 px de separación.
Una línea solo se usa si hay ambigüedad entre sesiones largas.

Trigger de opciones siempre presente, de 44 px, con nombre “Opciones del entrenamiento”.
Desktop: popover anclado. Móvil: menú o sheet breve accesible desde toque, nunca solo por long-press.
Contiene únicamente Editar/Eliminar existentes; conserva confirmación y permisos actuales.
Escape cierra; foco vuelve al trigger. No exigir hover para encontrar operaciones.

## 9. Registrar y editar entrenamiento

Una composición abierta, no un formulario dentro de una gran caja.

1. Título y contexto breve: “Revisa lo que detectamos y completa lo que falta” solo en propuesta de IA.
   En edición manual se usa contexto de edición; no afirmar que hubo detección.
2. Estado contextual de IA, únicamente cuando existe propuesta o falta información real.
   “Falta confirmar resultado” solo si ese es el estado actual, sin nueva inferencia del backend.
3. Información principal: fecha y nombre juntos; apilados en móvil.
4. Bloques: accordion compacto, resumen legible y controles de edición existentes al abrir.
5. Resultado: sección protagonista; label y textarea visibles, sin adornos.
6. Opcionales: cargas, adaptaciones y esfuerzo bajo disclosure, con indicación de datos presentes.
7. Media: foto/video existentes bajo disclosure; no nuevos uploads ni herramientas.
8. CTA sticky de guardado con el label de la operación actual; no duplicar una acción de guardado global.

Las confirmaciones por bloque y los retornos a descripción/resumen se preservan donde hacen falta,
pero pasan a ghost/contextuales. Guardado, validación, draft y confirmación conservan su semántica.

## 10. Recap compartido

Modo editorial de lectura. La identidad de la semana la aporta una foto autorizada, no un gran panel verde.

### Composición

- Cabecera clara: título de 36/48 px y rango de fechas legible, sin kicker decorativo.
- Métricas juntas, sin tres tarjetas: entrenamientos, días activos y esfuerzo con su tamaño muestral.
- Foto destacada de la sesión más reciente con foto, siguiendo el criterio factual ya usado.
- Momentos: jerarquía visual de sesiones/resultados existentes; sin nuevos rankings ni evaluaciones.
- Timeline: fecha, nombre, entrenamiento, resultado, notas/adaptaciones y esfuerzo actuales.
- Cierre: Fluxio discreto y aviso de snapshot; sin una nueva promesa o CTA comercial.

En móvil, métricas y foto aparecen antes de la lista larga. En desktop, cabecera y foto pueden compartir
un layout asimétrico si la imagen conserva proporción y legibilidad. La lectura mantiene una columna útil.

No recortar contenido importante de pizarras. Usar contain para documentos y fotografías cuyo contenido
no puede perderse; si no hay clasificación fiable, contain es el default. Cover exige verificar que el
recorte no oculte la información. El enlace a foto completa sigue usando la ruta segura existente.
Sin fotos, la cabecera y el primer resultado ocupan el lugar visual; no se agregan imágenes de stock.
Sin esfuerzo, omitir esa métrica; sin sesiones, mostrar el estado vacío actual, sin cifras o mensajes inventados.

Solo se presenta el snapshot autorizado. No añadir identidad del atleta, teléfono, ubicación,
notas internas, source_text ni URLs privadas. Mantener noindex, no-store, no-referrer, CSP, TTL y revocación.
No agregar Open Graph con información privada ni fuentes/analytics externos.

## 11. Motion e interacción

Una gramática breve, funcional e interrumpible. Curva principal: `cubic-bezier(.23,1,.32,1)`.
Transform y opacity son los únicos candidatos a animación de geometría/visibilidad en esta propuesta.
No transicionar height, margin, padding o posiciones de layout; no `transition: all`.

| Evento | Propuesta | Presupuesto |
| --- | --- | --- |
| Tap de botón | Scale 0.98 en pressed, retorno inmediato y sin rebote | 120 ms press / 80 ms release |
| Menú contextual | Scale 0.97 + opacity desde el trigger; transición interrumpible | 160 ms entrada / 100 ms salida |
| Sheet móvil | Translate corto desde el borde inferior; conserva foco y scroll | 220 ms entrada / 160 ms salida |
| Expandir sección | Disclosure inmediato; sin animar altura | Sin retraso de layout |
| Cambio de semana | Datos anteriores legibles mientras carga; feedback inline | 120–160 ms solo si aclara el reemplazo |
| Recap compartido | Aparición única opcional, desplazamiento máximo 4 px con opacity | 180 ms, sin delays escalonados |
| Navegación móvil | Estado activo responde al toque; ruta carga sin slides decorativos | Feedback inmediato |

Contenido visible por defecto y usable aunque motion no ejecute. No animar toda la libreta al cargar.
Acciones de teclado sin desplazamientos ni espera. Reduced-motion elimina transform y mantiene,
cuando sirve, color/opacity de hasta 100 ms. Hover se limita a dispositivos con hover y pointer fine.
Un cambio semanal no mezcla datos de dos semanas ni bloquea la interacción por una transición.
La animación de entrada del recap es opcional: si no mejora comprensión, se omite.

### Revisión de motion propuesta — emil-design-eng / review-animations

| Antes | Después propuesto | Motivo |
| --- | --- | --- |
| Motion de pulsación breve | Mantener y unificar por token | Feedback consistente |
| Ninguna transición de altura | Mantener respuesta inmediata en disclosure | Rendimiento y teclado |
| Contenido aparece como documento completo | Un solo momento opcional en recap | Presupuesto de atención limitado |
| Acciones secundarias persistentes | Menú anclado con origen correcto | Relación espacial entre control y contenido |

**Approve de la especificación**, sujeto a validar la implementación. No equivale a aprobar
animaciones renderizadas: aún no existen. Será Block si aparecen layout animations, focus perdido,
scale(0), ease-in, interacción retrasada, hover sin gate o ausencia de reduced-motion.

## 12. Reglas mobile-native

- Baseline: 320–430 px, luego tablet y desktop; no comprimir un layout desktop.
- Targets ≥44 px y campos a 16 px. Zoom del usuario siempre permitido.
- `viewport-fit=cover`; safe areas en cabecera, bottom navigation, sheets y CTA.
- CTA sticky sobre la bottom bar, sin tapar el último campo; reservar espacio equivalente.
- Con teclado abierto: mantener campo y guardado accesibles; evitar barras que compitan por altura.
  Usar el comportamiento de teclado existente antes de añadir listeners.
- `dvh` solo para shells/sheets que requieren altura de viewport; páginas de lectura en flujo normal.
- Scroll de documentos natural. Overscroll containment solo en superficies internas donde evita encadenamiento.
- Feedback en pressed; hover por capacidades, sin user-agent sniffing.
- Selección de texto disponible en entrenamiento, resultados, notas y enlaces.
- No bloquear gestos de scroll ni añadir navegación por swipe como nueva capacidad.
- Media fullscreen utiliza controles nativos de video y apertura segura de foto existentes.
- Loading, error, vacío y permiso limitado deben caber a 320 px; no asumir contenido de una línea.
- iOS/Android físicos validarán safe areas, teclado, input zoom, overscroll y sensación de tap.
  La emulación no prueba esos comportamientos.

## 13. Ejemplos conceptuales

Los siguientes datos son ilustrativos y no proponen nuevos campos ni un nuevo resumen funcional.

### Bitácora, lectura móvil

```text
Mi bitácora                         Registrar

28 sep — 4 oct
4 entrenamientos · 4 días activos
Esfuerzo 7.5/10 · 4 registros      Ver resumen

Hoy · 4 de octubre
┌ foto ┐  AMRAP 12                         ⋯
│      │  5 rondas + 8 reps
└──────┘  30 kg · Esfuerzo 8/10
          Bajé la carga en la última ronda.

3 de octubre
┌ foto ┐  Fuerza · Sentadilla              ⋯
│      │  5 × 5 · 60 kg
└──────┘  Esfuerzo 7/10

        [navegación existente del rol]
```

Los marcos del esquema representan fotos; no son tarjetas para cada entrenamiento.

### Registrar, revisión de propuesta

```text
Registrar entrenamiento
Revisa lo que detectamos y completa lo que falta.

Falta confirmar resultado.       [solo si aplica]

Fecha                  Nombre
4 de octubre           AMRAP 12

Bloques
Metcon · 12 minutos                   Abrir

Tu resultado
5 rondas + 8 reps

Cargas, adaptaciones y esfuerzo       Abrir
Foto y videos                        Abrir

             Guardar entrenamiento
```

### Recap público

```text
Semana de entrenamiento
28 de septiembre — 4 de octubre

4 entrenamientos   4 días activos   7.5/10
                                   4 registros

[Foto autorizada de la semana, completa]
La sesión más reciente con foto · AMRAP 12

4 de octubre
AMRAP 12
5 rondas + 8 reps
Entrenamiento y notas del snapshot…

3 de octubre
Fuerza · Sentadilla
5 × 5 · 60 kg
Entrenamiento y notas del snapshot…

Fluxio Movement
Copia de la semana al crear el enlace.
```

## 14. Alcance, decisiones y aceptación futura

La propuesta fue aprobada e implementada en el alcance indicado al comienzo. Los criterios históricos siguientes orientan comprobaciones futuras, sin certificar hardware ni mediciones pendientes.

### Criterios de aceptación de la implementación futura

1. El resultado y la siguiente acción son reconocibles en los primeros segundos.
2. A 390×844, con contenido normal, snapshot cerrado y teclado oculto, la primera sesión queda visible.
3. La reducción de cajas se mide en la misma ruta/estado; objetivo 30–40% sin pérdida de agrupación.
4. Se conservan campos, operaciones, confirmaciones, permisos y destinos de navegación.
5. Las acciones contextuales funcionan con touch, mouse y teclado; foco y cierre son correctos.
6. 320, 390, 430, 768, 1024 y 1440 px, además de zoom 200%, sin overflow ni contenido oculto.
7. Fotos completas, textos largos, semana sin foto, sin esfuerzo, vacía y enlaces no disponibles.
8. Tokens con contraste comprobado; targets, labels, focus y reduced-motion verificables.
9. Python, JavaScript, suites UX y E2E existentes verdes; seguridad del sharing intacta.
10. Revisión de motion sobre el diff real y validación en teléfono físico antes de declarar acabado móvil.

### Riesgos de diseño a resolver en la ejecución

- Un menú secundario mejora la composición pero exige discoverability y buen foco.
- El aspecto del recap depende de fotografías reales; una pizarra requiere composición distinta a una foto deportiva.
- Menos bordes necesita spacing disciplinado: no convertir densidad menor en pérdida de claridad.
- Una CTA sticky necesita comprobar teclado y safe areas en hardware.
- La nueva dirección tendrá que demostrarse con capturas y recorridos; esta propuesta no certifica el resultado visual final.

**Decisión realizada:** dirección e implementación aprobadas; resta comprobación en teléfono físico.
