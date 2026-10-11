# Modal de foto de entrenamiento

El clic sobre la fotografía en el detalle de un entrenamiento abría una pestaña nueva. Ahora abre un dialog modal en la misma página, conserva la imagen completa y permite cerrar con Cerrar, Escape o clic fuera. El foco permanece en el modal y vuelve a la miniatura al cerrar. Se muestra un error recuperable cuando la foto no carga; una miniatura ausente queda deshabilitada. La miniatura del listado conserva su navegación al entrenamiento.

## Archivos

- app/static/training.js: botón de apertura, dialog y gestión de cierre/foco/error.
- app/static/training.css: tamaño adaptado al viewport, fondo, imagen sin recorte y bloqueo de scroll del fondo.
- tests/training-ux.test.cjs: extensión de regresión de miniaturas con navegación, foco, cierres, viewport y fallo de imagen.

## Verificación

- PASS: prueba dirigida del modal después de corregir contención de foco con Tab.
- PASS: 31/31 pruebas JavaScript aplicables (training UX, WhatsApp link, usage integration).
- PASS: navegador real contra backend local, login de cuenta sintética, fotografía privada y modal en 390x844 y 1440x1000; captura, límites de viewport y cierre Escape verificados. Inspección visual realizada en ambos tamaños.
- PASS: git diff --check; workspace original intacto (153 rutas).
- Detector Impeccable ejecutado una vez: avisos de radios/tipografía en CSS preexistente; sin hallazgos sobre líneas nuevas del modal. No se amplió el ajuste a esos estilos.
- SKIPPED: Python en esta corrección exclusivamente frontend; la ejecución previa de 343 pruebas pertenece al cambio de preview WhatsApp, no se atribuye a este commit.

La copia de training.js y training.css fue actualizada únicamente en tmpfs del entorno QA. No se cambian APIs, autenticación, permisos, cuotas ni URLs privadas; no se publican fotografías. Sin consumo de OpenAI/Kapso, migraciones persistentes, push, merge o deploy. Prueba física de dispositivo sigue pendiente; los tamaños móviles se comprobaron en Chromium.

Evidencias locales fuera de Git: C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-5vgudpqr/photo-modal/mobile.png y desktop.png. Herramientas QA y artefactos .impeccable excluidos del commit. Los bloqueos de Go/No-Go del piloto continúan pendientes; este ajuste no declara GO.

Commit independiente: hash informado en la entrega final.
