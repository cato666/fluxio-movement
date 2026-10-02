# Mobile Native Feel — 2026-10-02

Implementación móvil aplicada. Fase pendiente de aceptación en hardware real.
Sin cambios en backend, APIs, rutas, permisos, lógica de negocio o DESIGN.md.

## Auditoría y resultado

| Antes | Después | Motivo |
| --- | --- | --- |
| Bottom navigation solo con texto y altura implícita | SVG + labels originales; altura mínima compartida con CTAs | Reconocimiento y separación estable |
| Página móvil con min-height 100vh | Override móvil 100svh | Altura estable con barras del navegador |
| Cabecera con margen negativo fijo y safe areas laterales incompletas | Contenido y navegación con insets simétricos | Evitar controles bajo recortes en landscape |
| Scroll raíz sin política de overscroll | Overscroll deshabilitado en workspace móvil; contenido secundario contenido | Evitar recargas accidentales y scroll chaining |
| Feedback incompleto en enlaces/disclosures | Presión inmediata; liberación de 100 ms con curva existente | Responder antes del click; acciones siguen en release |
| Selección accidental de labels | user-select/callout deshabilitados solo en controles táctiles | Texto de contenido sigue copiable |
| Navegación inferior competía con teclado | VisualViewport adapta navegación y CTAs; campo fuera del área visible se desplaza lo necesario | Proteger edición sin scroll global forzado |
| Username sin política explícita de autocapitalización | Sin autocapitalizar/corregir; hints de tecla en formularios | Teclado adecuado para credenciales |

Ya existían hover condicionado, inputs 16 px, viewport-fit=cover, interactive-widget=resizes-content, video playsinline, controles nativos, seek contextual, aria-current y reducción de movimiento. Se conservan.

No existen modales centrados propios que ameriten convertir a bottom sheet. Se conserva el editor contextual junto al video, los selectores nativos y confirmación destructiva del navegador. No se añaden gestos que puedan cerrar y perder un borrador. Navegación atrás conserva el historial y la advertencia existente por cambios sin guardar. No se fuerza orientación ni se intercepta fullscreen: controles del sistema conservan la sesión de reproducción.

## Revisión de motion

Approve para el cambio móvil: feedback de presión inmediato, release 100 ms, cubic-bezier(.23,1,.32,1); solo transform/opacity. Transiciones interrumpibles, sin rebotes, animación de layout, entradas de página o espera antes de ejecutar acciones. Movimiento eliminado también durante transición al activar prefers-reduced-motion. Referencias: app/static/styles.css, bloque Native mobile platform layer; app/static/mobile-ux.js, bloque VisualViewport.

## iOS y Android

iOS: se mantiene playsinline, fullscreen nativo, safe areas y zoom accesible; VisualViewport atiende la reducción del área visual por teclado. Android: se conserva interactive-widget=resizes-content; la detección compara también la altura previa al teclado porque puede reducirse el layout viewport completo. No hay detección por user agent ni cambios al gesto/botón atrás.

## PWA — recomendación, sin implementación

Recomiendo evaluar una fase separada de instalación para usuarios recurrentes: launcher y ventana standalone reducirían el contexto de navegador. Actualmente hay theme-color, pero no manifest, iconos de instalación/apple-touch-icon, service worker ni fallback offline. El favicon SVG no es un juego de iconos de instalación.

Preparar manifest con nombre, start_url, scope, display standalone, theme_color acorde a la cabecera y background_color acorde al canvas; iconos PNG 192/512, maskable y Apple; comprobar splash generado en ambos sistemas. Offline mínimo: mensaje explícito y recursos estáticos; nunca presentar análisis, uploads o guardados como completados sin servidor. Definir actualización e invalidación y no cachear automáticamente datos autenticados ni videos. Instalación y offline son decisiones distintas.

Fuentes: https://web.dev/learn/pwa/web-app-manifest ; https://web.dev/learn/pwa/installation ; https://web.dev/learn/pwa/service-workers ; https://webkit.org/blog/6784/new-video-policies-for-ios/

Una app nativa merece evaluarse si se requiere mayor control de captura, tareas/cargas en segundo plano e integración profunda con el sistema; esta fase no promete esas capacidades.

## Verificación

- Python completa: 145 passed, 3 warnings de deprecación. Código actual montado read-only en imagen existente; PostgreSQL nuevo y desechable movement-native-test, retirado al terminar. Intentos previos con imagen/base antiguas fallaron por desalineación de esquema (DuplicateColumn bio); no se modificó producto para acomodarlos.
- JavaScript completa: 41 passed; node --check y git diff --check correctos.
- E2E Chromium con fixtures HTTP sintéticas: atleta expande repeticiones y seek; coach comenta/guarda/completa. No certifican persistencia en backend real.
- Nueve rutas a 320/375/430/1280: sin overflow ni tarjetas de error; cambio de momento y restauración de disclosures a desktop correctos.
- native-interactions.cjs: iconos por rol, presión/release, reduced motion, teclado sintetizado, exclusión de pinch zoom. Capturas desktop 1280x800 idénticas a HEAD para listado, upload y Studio; video enmascarado para evitar variación de fotogramas.
- No hay dispositivos físicos accesibles en esta sesión. No se afirma validación real ni se cierra la fase.

## Aceptación pendiente en hardware

En iPhone Safari y Android Chrome, registrar modelo/OS/browser y probar: navegación y selección activa, tap/long press, scroll y encadenamiento, campos con teclado y cierre, upload desde archivos y cámara, video inline/seek/timestamp, entrada/salida de fullscreen, orientación horizontal y vertical, notch/home indicator, CTAs sticky y atrás con borrador. Confirmar que ningún campo o acción se oculte y que los valores se conserven. Probar con fuente ampliada y reduced motion.

Si se autoriza e implementa PWA, repetir instalada desde Home Screen en ambos sistemas, incluyendo arranque, splash, offline y actualización.
