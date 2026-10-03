# Bitácora: auditoría y polish UX/UI

Fecha: 2026-10-02. Alcance: captura, interpretación, confirmación, guardado,
lista y edición de sesiones. Referencias: DESIGN.md, Impeccable,
emil-design-eng, mobile-native y review-animations.

No se modificaron modelos, reglas, endpoints, permisos, migraciones ni rutas.
Se conservaron los límites de archivos, audio, RPE, bloques y videos existentes.

## Auditoría antes de editar

Evidencia: código de training.js, training-voice.js y training.css; capturas
previas de interpretación y dictado; comparación con los formularios, listas,
feedback y navegación de análisis. No se identificaron Critical en ese alcance.

| Prioridad | Hallazgo | Impacto | Resolución |
| --- | --- | --- | --- |
| High | Captura y formulario completo visibles simultáneamente | No queda claro por dónde comenzar | Capturar → revisar → guardar |
| High | Interpretar y completar manualmente compiten en verde | Dos acciones parecen principales | Primaria verde y alternativa secundaria existente |
| High | Guardar al final de un formulario móvil largo | Siguiente acción difícil de encontrar | Guardado sticky sobre la navegación, sin fijarlo durante teclado |
| High | Texto del WOD y bloques duplicados | Confusión sobre cuál editar | Bloques visibles; texto libre por disclosure con explicación de su efecto |
| Medium | Adaptaciones, esfuerzo y videos mostrados demasiado pronto | Más decisiones antes de capturar | Secciones opcionales plegadas; abiertas si contienen datos |
| Medium | Estado de procesamiento distante del control | No se sabe si la acción comenzó | Texto inmediato, botón ocupado y aria-busy |
| Medium | Guardado redirige sin confirmación | Éxito poco claro | Flash compartido en la bitácora |
| Medium | Campos requeridos dentro de bloques cerrados | Validación difícil de localizar | Abrir ancestros details en invalid |
| Medium | Estado vacío sin acción contextual | No explica cómo iniciar | Invitación breve y enlace al primer registro |
| Medium | Errores de red y permisos poco orientativos | Recuperación ambigua | Explicar conexión/sesión/permisos y conservar borrador |
| Medium | Temporizador de voz en región viva cada 500 ms | Interrumpe al lector de pantalla | Mensaje estable; tiempo visual separado de aria-live |
| Polish | Bordes anidados, etiquetas largas y separación irregular | Ficha visualmente pesada | Fieldsets sin borde, whitespace y escala de DESIGN.md |
| Polish | Colores duplicados y campos con peso de etiqueta | Menor coherencia y jerarquía | Variables compartidas y valores de campos en peso 400 |
| Polish | Selector de archivo dependiente del idioma del navegador | Acción poco clara | Botón explícito en español, conserva selector nativo |

Se conservaron las fortalezas existentes: confirmación humana antes del guardado,
foto privada, audio revisable, texto editable, videos opcionales y navegación por rol.

## Recorrido final

| Pantalla/estado | Intención | Información necesaria | Acción principal | Después |
| --- | --- | --- | --- | --- |
| Lista | Consultar recuerdos | Fecha, nombre, resultado, esfuerzo | Abrir sesión o registrar | Edición o captura |
| Sin sesiones | Comenzar | Se puede usar texto, voz o foto | Registrar primer entrenamiento | Captura |
| Captura | Contar lo entrenado | Qué enviar y que la IA prepara un borrador | Interpretar WOD | Revisión |
| Captura manual | Registrar sin IA | Se mantiene la descripción | Completar manualmente | Revisión editable |
| Foto/audio en proceso | Esperar sin perder datos | Qué se está procesando | Esperar; controles ocupados | Preview o texto editable |
| Revisión | Confirmar lo entendido | Nombre, fecha, WOD y resultado; preguntas de IA | Guardar sesión | Lista con confirmación |
| Contexto opcional | Añadir detalles | Cargas, adaptaciones, RPE o videos existentes | Abrir sección pertinente | Volver al guardado |
| Corrección de captura | Aclarar el original | Reinterpretar reemplaza la ficha, como antes | Interpretar o volver manualmente | Revisión |
| Edición | Corregir una sesión | Datos ya guardados | Guardar cambios | Lista con confirmación |
| Error | Recuperarse | Qué ocurrió y qué se conserva | Reintentar/corregir/escribir | Continúa el mismo borrador |

El paso de captura no obliga a escribir para entrar manualmente a la ficha.
La validación y los campos requeridos siguen definidos por la implementación existente.

## Estados y accesibilidad

- Inicial: pregunta concreta, campo de descripción, voz/foto y una primaria.
- Sin datos: invitación con CTA contextual; resultados ausentes mantienen su mensaje.
- Cargando: mensaje visible en la lista o sesión, sin aparentar una lista vacía.
- Procesando: estado inmediato, controles temporalmente deshabilitados y aria-busy.
- Éxito: foto lista, transcripción añadida y confirmación al guardar usando el flash compartido.
- Error: explicación y recuperación; se mantienen descripción, ficha y audio para retry.
- Conexión perdida: aviso específico y alternativa manual al interpretar.
- Permisos rechazados: micrófono permite escribir; API 403 explica la restricción;
  API 401 ofrece iniciar sesión en otra pestaña para conservar esta pantalla.
  No se amplían permisos.
- Contenido incompleto: preguntas de IA y validación nativa abriendo las secciones pertinentes.
- Focus visible, etiquetas, orden de tabulación, encabezado de revisión enfocado y regiones
  status atómicas. El temporizador visual no repite anuncios al lector de pantalla.

Los cambios respetan Inter, paleta evergreen, radio de 9/14 px, escala de espacio
y controles secundarios definidos en DESIGN.md. No se añadieron librerías ni modales.

## Móvil

Captura y revisión en una columna; inputs de 16 px y controles de 44 px mínimo.
Guardar se apoya en --mobile-nav-height, env(safe-area-inset-bottom) y el estado
mobile-keyboard-open existente. El selector de foto conserva el comportamiento
del sistema. Ninguna acción exige hover. Datos opcionales se consultan por demanda.

Verificado con Chromium a 320, 390, 430, 768 y 1440 px, usando estilos reales;
capturas de la aplicación completa a 390 y 1440 px. No se detectó overflow ni
errores JavaScript en esos recorridos. No equivale a probar hardware real.

## Review-animations

| Before | After | Why |
| --- | --- | --- |
| Press heredado con duración simétrica | training.css:57–58, press 120 ms / release 80 ms | Feedback deliberado y retorno rápido; usa --ease-out existente |
| Posible tentación de animar cada nuevo estado | Cambios de captura/revisión inmediatos en training.js:92 | Flujo frecuente: prioridad a la tarea y focus, sin entradas decorativas |
| Movimiento heredado de botones | training.css:73–75 elimina transform con reduced-motion | Conserva feedback estático de color y focus sin desplazamiento |
| Hover global existente | Se mantiene su media query hover:hover/pointer:fine en styles.css | No requiere hover en teléfonos ni introduce estados pegados |

**Approve.** El diff solo usa transición de transform, interruptible, debajo de
300 ms; no hay keyframes, scale(0), layout animado ni entradas al usar teclado.
Focus-visible evita scale al pulsar por teclado. No hay hallazgos pendientes en
el motion añadido. La revisión se limita a esta funcionalidad.

## Validación

- Antes: 23 pruebas Python específicas de bitácora y 41 JavaScript existentes pasan.
- Después: suite Python completa, 182 passed (3 warnings de deprecación preexistentes).
- Después: mismas 41 pruebas JavaScript pasan.
- Nuevas: 10 pruebas de navegador pasan: progresión, preservación, validación de bloques,
  fallo/reintento de guardado, offline, tamaños, keyboard/reduced-motion, vacío/permisos,
  procesamiento sin duplicados, voz, foto y edición por PUT.
- node --check para los dos scripts y git diff --check pasan.
- Los proveedores de IA y el micrófono se simulan en estas pruebas de UI; no se consumen
  tokens ni se certifica nuevamente la precisión de interpretación/transcripción.

Ejecutar las pruebas de navegador con Playwright disponible:

```powershell
$env:PLAYWRIGHT_MODULE = 'ruta al módulo playwright' # opcional si está instalado localmente
node --test tests/training-ux.test.cjs
```

## Archivos y límites

Interfaz: app/static/training.js, training-voice.js, training.css y referencias
de caché de index.html. Verificación: tests/training-ux.test.cjs. Documento: este archivo.
Los cambios ajenos ya presentes en index.html y otros archivos se conservaron.

Validación manual pendiente: iPhone/Android real (teclado, scroll, safe areas,
selector de cámara/galería y permisos), VoiceOver/TalkBack y dictado real.
El borrador sigue viviendo en esta pantalla: no se añadió persistencia offline.
Se actualizaron los tres assets del contenedor en localhost:8000 y únicamente sus
referencias de caché en el HTML, sin rebuild ni copiar cambios ajenos del HTML local.
Se verificó que los archivos servidos coinciden con el código final del workspace.
Un despliegue remoto posterior debe incluir esos assets y referencias de caché.

## Entrenamientos guardados: resumen primero

Al abrir una sesión guardada, se muestra una anotación de lectura con fecha,
nombre, resultado, WOD, adaptaciones y esfuerzo cuando existen. Videos vinculados
se indican sin cargar anticipadamente la interfaz de vinculación. Textos extensos
ofrecen lectura completa mediante details nativo. No se genera texto con IA.

“Ver detalle y editar” abre la ficha existente en la misma ruta. “Volver al resumen”
conserva las ediciones pendientes; la nota mantiene los datos guardados y muestra
un aviso si hay cambios sin guardar. Registrar una sesión nueva conserva su flujo.

| Before | After | Why |
| --- | --- | --- |
| Abrir sesión presenta el formulario | Nota legible; detalle por acción explícita | Consultar antes de editar |
| Cambiar de vista puede confundirse con guardar | Aviso de cambios pendientes; misma ficha en memoria | Evita presentar un borrador como guardado |
| Transición entre vistas | Inmediata, con focus al encabezado pertinente | Frecuente, accesible, sin animación decorativa |

Review-animations: **Approve**. No se añadieron transiciones ni keyframes;
los botones reutilizan el feedback y reduced-motion existentes. Verificación:
11 pruebas de navegador y 41 JavaScript existentes pasan; sin overflow en
320/390/430/768/1440 px. Capturas con el shell real a 390 y 1440 px.
Pendiente la comprobación física en teléfono. Backend y DESIGN.md sin cambios.

## Captura con experiencia de chat

Referencia: imagen del usuario. Mensaje inicial, composer único y barra integrada
con foto (+), dictado (micrófono) e Interpretar WOD. Audio, transcripción, foto,
revisión y guardado conservan sus operaciones existentes. Completar manualmente
sigue como acción secundaria. Iconos SVG con nombres accesibles y targets de 44 px.

| Before | After | Why |
| --- | --- | --- |
| Acciones separadas del campo | Foto, micrófono e interpretación dentro del composer | Una zona clara para capturar y actuar |
| Controles móviles apilados | Barra en una fila a 320–430 px | Mantiene la relación entre mensaje y acciones |
| Feedback de presión existente | Se reutiliza sin motion adicional | Review-animations: **Approve**, sin animaciones decorativas |

Verificación: 12 pruebas de navegador y 41 JavaScript existentes pasan; captura
desktop/móvil con shell real y comprobación sin overflow. Pendiente hardware real.
