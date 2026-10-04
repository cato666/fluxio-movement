# Validación de publicación a main

Fecha: 2026-10-04.

Alcance: rediseño de Bitácora y registro, recap compartido, semana compartida actualizable, resumen expandido compacto e icono de WhatsApp. Incluye cuatro perfiles ya referenciados por el catálogo existente, ausentes en el checkout limpio: overhead squat y handstand push-up, vistas front y side.

La primera validación del candidato aislado detectó 25 fallos por esas referencias sin archivos. Después de incluir las dependencias, la versión preparada pasó:

- Python completo: 440/440, tres avisos de deprecación existentes.
- JavaScript completo: 64/64.
- E2E phase01: Bitácora texto/foto/audio, Athlete UX y Coach UX.
- E2E semanal: navegación, enlaces persistidos, fotos públicas autorizadas y revocación.
- Catálogo: 41/41 pruebas específicas.
- Diferencias Git: sin errores de whitespace.

Pruebas ejecutadas sobre una exportación del índice Git, sin depender de modificaciones locales excluidas. El baseline local de 454 pruebas incluye 14 pruebas adicionales de ampliaciones de ejercicios no incluidas en esta publicación. Herramientas de diseño, capturas, archivos temporales y ampliaciones independientes permanecen locales.

No se ejecutó un deploy manual a producción ni se realizó smoke real de Kapso en esta publicación. Persisten las limitaciones documentadas del sharing: la API no recupera URLs anteriores ni fechas de creación, y la verificación móvil usó navegador emulado, no teléfono físico.
