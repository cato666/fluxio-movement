# Corrección de nombres guardados desde WhatsApp

Los títulos vacíos o genéricos «Borrador de entrenamiento» y «Borrador de programación de pizarra» se reemplazan en la propuesta por «Entrenamiento · DD/MM/AAAA», usando la fecha interpretada del entrenamiento. Se conservan títulos específicos y el mismo nombre al confirmar Guardar. Sin llamadas IA adicionales.

La bitácora presenta los registros históricos con título genérico usando el mismo nombre con fecha, sin modificar su almacenamiento. Los formularios de edición conservan el valor almacenado. No se migran datos.

Archivos: app/whatsapp/capture.py, app/static/training.js, tests/test_whatsapp_capture.py, tests/training-ux.test.cjs.

PASS: 348 pruebas Python dirigidas de WhatsApp, contratos, consumo y seguridad S02–S08, en PostgreSQL nuevo desechable, con proveedores simulados. Incluye cinco casos de normalización/preservación y guardado. PASS: 32 pruebas JavaScript aplicables, incluyendo presentación histórica sin escrituras. PASS: detector de interfaz sin hallazgos y workspace original intacto (153 rutas). Suite Python completa SKIPPED: ajuste acotado, sin cierre de fase.

Evidencia Python: C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-0j_f0ilc/offline-tests.log. Contenedores propios de regresión detenidos, sin alterar otros contenedores.

Archivos de código actualizados en tmpfs del QA local anterior. Worker no observado en ejecución: prueba real posterior de WhatsApp pendiente de revisar/reanudar sesión controlada y límites, sin afirmar PASS. Las pruebas de títulos de navegador usan backend simulado; integración real del ajuste SKIPPED.

Riesgos: nombres genéricos diferentes de los enumerados se conservan; no se inventa un nombre de WOD a partir del contenido. Tres avisos de deprecación preexistentes en pytest. Bloqueos obligatorios del piloto continúan pendientes; no se declara GO. Sin proveedores reales invocados, cambios del workspace original, push, merge, deploy ni migraciones persistentes.

Commit independiente informado en la entrega final.
