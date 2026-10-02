# Auditoría y modernización de interfaz

Fecha: 2026-10-02. Alcance: aplicación HTML/CSS/JS existente. Se mantienen flujos y lógica.

## Auditoría inicial

La identidad inicial no distinguía suficientemente navegación, contenido, controles y estados. La misma sombra, radio y acento azul se aplicaban a casi todos los contenedores y acciones.

| Before | After | Why |
| --- | --- | --- |
| Canvas azul con degradado y cards con sombra más borde | Canvas verde grisáceo, superficies blancas con borde | Jerarquía espacial en vez de decoración repetida |
| Barra horizontal sin ruta activa | Sidebar de 232px y aria-current | Ubicación clara para ambos roles |
| Títulos hasta 52px, tracking -0.055em y pesos 750–800 | Títulos de 28–40px, tracking -0.035em, pesos 400/600 | Lectura consistente y menos ruido |
| Controles de revisión de 32–35px | Controles de al menos 44px | Uso táctil |
| Hover en cards no accionables | Feedback en controles interactivos | Evitar falsas affordances |
| Hover que subía botones con sombra | Feedback de presión de 120ms y hover solo con puntero preciso | Respuesta breve, sin hover pegado en touch |
| Supresión global de transiciones | Reduced motion conserva feedback de color y elimina escala | Respeta preferencias sin borrar estados |
| CTA de acceso oculta bajo 960px | CTA visible también en móvil | Mantener el acceso público |

## Hallazgos prioritarios

- P1: acceso público oculto en móvil por selector de primer hijo de auth-actions. Corregido eliminando ese selector.
- P2: controles táctiles pequeños en filtros, video, repeticiones y anotaciones. Corregido mediante reglas comunes.
- P2: navegación sin ubicación activa y jerarquía visual uniforme. Corregido con rail, selección lima y superficies por tarea.
- P2: colores y efectos dispersos. Tokens globales coherentes; la landing hereda la paleta aprobada.
- P2: interacción hover global en dispositivos táctiles. Nuevos efectos limitados a hover:hover y pointer:fine.

Se mantienen etiquetas de formularios, navegación por rol, anuncios role=status, carga lazy de miniaturas y fuentes locales. No se ha realizado una certificación WCAG ni una evaluación de rendimiento instrumentada.

## Dirección seleccionada

El usuario confirmó prioridad equivalente para atletas y coaches y autorizó reemplazo de identidad. Seleccionó explícitamente verde profundo + lima. Referencia cultural: identidad gráfica de equipos deportivos; aplicada a paleta, densidad, tipografía y selección, con controles web convencionales.

## Implementación

Estilos base sustituidos en app/static/styles.css, composición de carga en dos columnas a partir de 1100px, sidebar de escritorio, navegación móvil desplazable, estados semánticos, métricas sin cards anidadas y reproductor del coach sobre superficie profunda. Landing y autenticación comparten identidad. JavaScript solo añade ubicación activa y clase visual de estados vacíos.

## Verificación

- node --check app/static/app.js: correcto.
- git diff --check para los archivos de interfaz: correcto.
- Comparación con HEAD: se mantienen 126 IDs y 18 campos con name originales.
- Navegador in-app: 1440px y 390px; sin overflow horizontal según DOM a 390px en carga, landing y revisión.
- Filtro de análisis pendiente sin resultados verificado con el JavaScript real y API GET de datos sintéticos. Navegación restringida al rol atleta/coach en fixtures.
- Detector Impeccable ejecutado una vez. Inter se conserva como fuente UI local; los avisos sobre reglas antiguas de landing se revisaron contra overrides. Contraste del botón deshabilitado mejorado.
- Backend PostgreSQL, mutaciones, análisis de video y hardware táctil no ejercitados. Las capturas son evidencia visual, no certificación de los flujos del servidor.

Capturas desktop.jpg y mobile.jpg son viewports válidos. Las capturas fullPage que presentaron render obsoleto o regiones vacías no sirven como evidencia y no se entregan al revisor.

## Revisión independiente

El revisor confirmó paleta, superficies, navegación y composición de carga. Solicitó retirar los rótulos sobre títulos: se eliminaron, conservando identidad en navegación y contexto necesario debajo del título. La pasada de veredicto calificó esa corrección como resuelta y emitió `ship` para el ajuste revisado. No extiende esa conclusión a vistas sin captura ni a operaciones del backend.
