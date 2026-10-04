# Resumen semanal y compartir semana

La Bitácora consulta semanas completas de lunes a domingo. La semana actual usa
America/Santiago. Incluye cantidad de entrenamientos, días activos y esfuerzo
promedio con su cantidad de registros; no infiere progreso ni usa IA.

El atleta puede navegar semanas, crear un enlace, copiarlo y revocar todos los
enlaces vigentes de la semana seleccionada. Los enlaces contienen una copia del
texto guardado al crearlos: entrenamientos, resultados, notas/adaptaciones y RPE.
Incluyen las fotos asociadas, servidas con el mismo token y verificación de
pertenencia a la copia. Una foto eliminada del almacenamiento deja de estar
disponible. No incluyen videos, teléfonos ni texto original de interpretación.

Quien tenga el enlace puede abrirlo sin cuenta. Tokens aleatorios de 32 bytes,
solo hash en PostgreSQL, expiración y revocación. HTML y fotos usan no-store,
noindex y no-referrer. Una copia descargada por el destinatario no puede retirarse.

WhatsApp: `resumen semana`, `resumen semana pasada`, `compartir semana`,
`compartir semana pasada`, `revocar semana`, `revocar semana pasada`.
La creación requiere PUBLIC_BASE_URL con HTTPS. Enlaces y outbox se guardan en
la transacción del worker; el inbox existente deduplica retransmisiones.

Despliegue: migración 0021_weekly_shares; WEEKLY_SHARE_TOKEN_TTL_HOURS=168
(admite de 1 a 168), PUBLIC_BASE_URL con el dominio del entorno. Compose pasa
estas variables a app y worker. No se despliega automáticamente.

Pruebas: tests/test_weekly_summary.py y tests/e2e/weekly.cjs.

Validación local: regresión Python completa 442 aprobadas; JavaScript 62
aprobadas. Tras los ajustes finales, las 9 pruebas del módulo semanal y el E2E
HTTP con PostgreSQL volvieron a pasar. Navegación, lectura anónima con fotos y
revocación verificadas en 1440 y 390 px. Tres avisos de deprecación preexistentes.
No se probó tráfico real de WhatsApp ni se desplegó esta funcionalidad.
