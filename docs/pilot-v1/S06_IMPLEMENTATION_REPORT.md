# S06 — Límites compartidos y reservas de consumo

Fecha de revisión: 2026-10-10 (America/Santiago). Alcance exclusivo S06; S07 no iniciada.

Rama: `codex/pilot-v1-stabilization`.
Base aprobada: `98acac5a17fe000cb2a37d5c431f1ff41fd9c9ea`.
Implementación inicial: `a3c75a84902aaeaa4fd8e9bb2a4e57e2cf9850e8`.
Candidato funcional final: `35bd3c67b2e9d75f73c1d57a994acf31f66849a6`.
El commit documental final se obtiene con `git log -1 --format=%H -- docs/pilot-v1/S06_IMPLEMENTATION_REPORT.md` y se informa al entregar la etapa.

Estado: lista para revisión técnica final de S06. Todas las pruebas obligatorias locales del candidato final pasan. El E2E integrado heredado de S05 continúa BLOCKED y el release permanece NO-GO. No hay autorización de publicación ni consumo real.

## Arquitectura y alcance

Se extendieron PlanInteraction y WhatsAppUsage existentes; no se agregó un sistema comercial, suscripciones, pagos ni tablas de facturación. Antes, web descontaba una interacción mensual y chat registraba telemetría sin aplicar ese límite. Ahora ambos utilizan reservas durables compartidas antes del proveedor, con contadores diarios, límite mensual vigente del plan y presupuesto global común para IA y envíos.

La reserva usa una transacción PostgreSQL independiente de la operación web/chat. Un rollback del worker no borra el compromiso de consumo. Un advisory lock transaccional global serializa presupuestos y cuotas entre procesos; se libera antes del proveedor. El bloqueo User NO KEY UPDATE conserva la exclusión con la desactivación administrativa y permite insertar la FK de la reserva en otra conexión. Las regresiones S02 comprueban que la cuenta sigue bloqueada durante IA y envío.

Para video se reserva el costo de IA más los componentes configurados de cómputo, almacenamiento y otros cargos. Un cupo global permite un solo análisis pendiente/en ejecución. Los jobs heredados PROCESSING/PENDING sin reserva también ocupan capacidad de forma conservadora. La reserva se vincula al job antes de programarlo; STARTED se marca una sola vez. Un job duplicado no vuelve a ejecutar el analizador ni sobrescribe su estado. Una interrupción conserva la reserva y el cupo; no hay liberación automática por tiempo.

## Límites aprobados y configuración

| Concepto | Valor inicial aprobado |
|---|---|
| Interpretaciones por atleta/día, web + WhatsApp | 3 |
| Transcripciones por atleta/día, web + WhatsApp | 3 |
| Mensajes WhatsApp admitidos por atleta/día | 20 |
| Intentos físicos salientes por atleta/día | 20 |
| Rate WhatsApp por conversación y atleta | 5 por minuto |
| Análisis de video por atleta/día | 1 |
| Análisis de video concurrentes globales | 1 |
| Presupuesto global diario estimado | US$3 |
| Presupuesto estimado del piloto de 30 días | US$30 |
| Umbral de alerta | 80% |
| Reserva provisional por interpretación | US$0,05 |
| Reserva provisional por transcripción | US$0,03 |
| Reserva provisional por análisis con IA | US$0,20 + cómputo/almacenamiento/otros |
| Reserva provisional por intento físico WhatsApp | US$0,02 |

Los días contables y PILOT_START usan UTC; el rate utiliza una ventana móvil de 60 segundos. El presupuesto del piloto no se reinicia al cambiar de mes. PILOT_START identifica una ventana fija de 30 días y queda fijado en consumption_window tras la primera reserva; cambiarlo posteriormente falla cerrado. Una reserva pendiente se arrastra al presupuesto del nuevo día. STARTED vuelve a comprobar presupuesto/ventana vigentes antes de iniciar IA, incluido un límite reducido por el operador. Un último cupo ya reservado puede ejecutarse una vez al alcanzar exactamente el 100%; nuevas operaciones se bloquean.

La web tiene también un rate por atleta para operaciones IA de 5/minuto, reutilizando el umbral configurado del canal; los cupos diarios por operación siguen siendo independientes. Las reservas inciertas gastan cupo conservadoramente. Un envío de varios fragmentos cuenta cada fragmento físico; los reintentos seguros reservan otro intento. Esto puede agotar 20 intentos con menos de 20 mensajes entregados. Los contactos sin atleta resuelto comparten el límite saliente anónimo, además del rate de conversación y del presupuesto global.

En producción no se usan defaults para autorizar consumo. Se requieren valores válidos para todos los límites/reservas, porcentaje y fecha inicial; cada operación falla cerrada si faltan. La app puede conservar login, historial y registro manual mientras la operación facturable recibe 503/429. Video exige además VIDEO_COMPUTE_RESERVE_USD, VIDEO_STORAGE_RESERVE_USD y VIDEO_OTHER_RESERVE_USD explícitos; un valor vacío bloquea video. Cero debe representar un componente verificado como no facturable, no una suposición.

La configuración inicial puede provenir de USAGE_* en el entorno. Para ajustes controlados, el administrador usa PUT `/api/admin/consumption-limits`, con el conjunto completo de claves de DEFAULTS, los tres componentes de video y PILOT_START. Se validan valores finitos, precisión, rangos, claves y fecha. El endpoint usa el mismo bloqueo global y registra before/after mediante AdminAudit. GET `/api/admin/settings` permite consultar la configuración administrativa. Las claves persistidas tienen precedencia sobre el entorno, se leen en cada operación y son comunes a app/worker sin cambiar código. `.env.example` documenta las claves; no configura ni despliega EasyPanel.

## Contratos de consumo y privacidad

- Web: Idempotency-Key UUID opcional en interpretación, transcripción, análisis y reanálisis. Los clientes existentes siguen funcionando; deben enviar una clave estable para deduplicar reintentos de transporte. Los clientes actuales conservan la clave ante resultado incierto y generan otra al cambiar contenido/corrección o realizar una nueva operación tras éxito.
- WhatsApp: el inbox UUID es la clave de la operación; TRANSCRIBE e INTERPRET son operaciones distintas con la misma clave. Un webhook duplicado no crea inbox/reserva nuevos. El replay del worker puede repetir trabajo local después de rollback, pero una reserva IA previa impide volver a llamar al proveedor.
- Unicidad durable: user_id + operation + request_key. Cambiar de canal no evita la restricción. Una repetición devuelve 409, no otra llamada ni una respuesta privada almacenada como caché. No se persisten prompts para comparar reintentos.
- Foto/audio: se reserva antes de descargar el medio. Cuando no queda cuota/presupuesto no se descarga ni ejecuta IA. La misma reserva se entrega a TrainingService con comprobación de actor, operación, canal, clave y estado. Audio requiere además otra reserva para interpretar el texto.
- Rate/cuota de ingreso WhatsApp: rechazo silencioso, inbox finalizado y sin respuesta automática, evitando bucles. El rechazo de una operación IA puede encolar una sola respuesta genérica deduplicada; el envío sigue sujeto a sus propios límites.
- Estados: RESERVED mantiene el compromiso durable; STARTED es una marca temporal de inicio único, no otro cobro; CONFIRMED significa resultado/acuse exitoso; UNCERTAIN conserva costos de fallos y resultados desconocidos; RELEASED exige prueba de que no comenzó la llamada. Solo la comprobación inequívoca de proveedor nativo deshabilitado antes de cualquier llamada libera automáticamente. Si hubo descarga previa, el costo permanece incierto.
- Confirmado no significa factura monetaria conciliada. El presupuesto sigue contando la reserva conservadora cuando no se conoce el costo real. Ningún timeout/error/desactivación devuelve dinero automáticamente. No se agregó una herramienta de reintegro o recuperación S09/S12.
- Los consumos históricos permanecen: filas PlanInteraction anteriores quedan UNCERTAIN sin clave ni costo nuevo. Los costos desconocidos se estiman conservadoramente para la ventana vigente; salidas WhatsApp históricas también cuentan sin duplicar una reserva nueva correspondiente.
- La telemetría nueva registra operación, canal, estado, motivo y período/umbral. No imprime IDs de atletas, teléfono, tokens, claves, texto, fotografías, audio, entrenamiento ni respuesta del proveedor. Las FK/UUID durables mínimos sirven para aplicar cuotas e idempotencia y no se exponen públicamente.

El manejo Kapso 402/429/UNCERTAIN conserva su clasificación existente. 402 no admite retry automático; 429 conserva backoff y máximo de cinco intentos, sujetos al presupuesto disponible en cada intento. Una respuesta incierta o un SENDING interrumpido conserva el costo y no se reenvía a ciegas. No se implementó recuperación operativa S08.

## Archivos y migración

| Grupo | Archivos |
|---|---|
| Reserva, presupuesto y administración | app/services/consumption_limits.py; app/administration.py; .env.example |
| Modelos y migración aditiva | app/models.py; app/whatsapp/models.py; migrations/versions/0023_consumption_reservations.py |
| Adaptadores y ciclo de IA/video | app/services/training_service.py; app/training.py; app/main.py |
| WhatsApp | app/whatsapp/identity.py; runtime.py; capture.py; media.py; queue.py |
| Reintentos de clientes | app/static/app.js; training.js; training-voice.js |
| Pruebas | tests/test_consumption_limits.py; conftest.py; test_whatsapp_contracts.py; training-ux.test.cjs; athlete-integration.test.cjs |
| Documentación | docs/pilot-v1/S06_IMPLEMENTATION_REPORT.md; GO_NO_GO_CHECKLIST.md |

Cadena: 0022_administration → 0023_consumption_reservations. Agrega clave, canal, presupuesto provisional, estado, started_at y resource_id a PlanInteraction, unicidad de reservas/recurso y estado nullable a WhatsAppUsage. No altera entrenamientos, notas, imágenes ni enlaces. Se probaron migración desde cero, upgrade/downgrade en base desechable, preservación de una interacción histórica y alembic check. No se aplicó a bases persistentes.

La excepción de contrato HTTP está acotada a cinco headers opcionales Idempotency-Key; se conserva además la excepción SharePayload aprobada en S05. El baseline original no fue reescrito. El endpoint administrativo nuevo es exclusivamente configuración de estos controles.

## Pruebas y resultados

| Verificación | Estado | Evidencia |
|---|---|---|
| Casos S06 finales | PASS | 47 aprobados, cero fallos; 14,55 s. |
| Selección de seguridad y regresiones inicial | PASS | 217 aprobadas; 78,88 s. |
| S06/WhatsApp/S02/video/regresión dirigida previa al ajuste de día | PASS | 119 aprobadas; 40,35 s. |
| Python completa antes del ajuste de día | PASS | 641 aprobadas; 188,05 s. No sustituye la ejecución final. |
| Python completa del candidato final | PASS | 643 aprobadas; cero fallos, errores u omitidas; 187,29 s. Tres advertencias preexistentes de deprecación. |
| JavaScript completa | PASS | 69 aprobadas, cero FAIL/SKIPPED; 21,836 s. Las últimas correcciones solo afectan Python. |
| Código ejecutado versus candidato | PASS | 180 archivos comparados SHA256, ninguna diferencia con el código final ejecutado. |
| Workspace original | PASS | 153 rutas conservadas; estado Git y HEAD originales intactos, verificados al cierre. |
| E2E integrado navegador/servidor heredado S05 | BLOCKED | No se ejecutó ni se marcó PASS. Conservado explícitamente en GO_NO_GO_CHECKLIST.md. |
| EasyPanel, OpenAI/Kapso reales y facturación | SKIPPED | No autorizados; no conexiones ni llamadas reales. |

Los casos cubren los cupos compartidos web/chat, último cupo concurrente, presupuesto concurrente entre atletas, audio con dos etapas, correcciones, replay web/webhook, transacción rollback, cuenta inactiva, bloqueo antes de descarga/proveedor, registro manual, alertas al 80%, ventana de 30 días, presupuesto al cambiar de día/reducirse, configuración inválida/productiva, cambios administrativos auditados, video global único y estimación adicional, 20 ingresos/salidas, rechazo sin bucle, 402/429 y envío incierto. JavaScript verifica claves estables para interpretación/audio/video y claves nuevas para correcciones.

En la primera regresión, la admisión idempotente omitía todo el replay del worker y perdía el Guardar local tras rollback. Se corrigió para permitir trabajo local y mantener la deduplicación en las reservas de proveedor; la regresión original pasó. Un fixture nuevo de video omitía video_path obligatorio; se corrigió el fixture, conservando el contrato del modelo. La revisión posterior añadió revalidación del presupuesto de reservas pendientes entre días. No se declaró PASS de esas versiones como resultado del candidato final.

PostgreSQL 17.6 tmpfs, sin mounts/volúmenes persistentes, en la red interna existente fluxio-s01-validation-20261010. Se reutilizaron exclusivamente los contenedores desechables S05 DB/tests, con movement_test y guard TEST_DATABASE_RESET=1. No se publicaron puertos, ampliaron redes ni reconstruyeron imágenes. Proveedores simulados y claves reales ausentes. Las regresiones ajenas a cuotas usan límites sintéticos generosos explícitos en fixture; test_consumption_limits usa los valores aprobados y casos extremos controlados.

## Riesgos y recomendación

1. Los importes son estimaciones conservadoras provisionales. Bloquear al 100% del presupuesto reservado no garantiza el máximo de una factura real si el proveedor/infraestructura no ofrece un cap o si las estimaciones son insuficientes. Validar tarifas, límites externos, cómputo, retención/almacenamiento y demás costos antes de autorizar consumo; video productivo permanece bloqueado con parámetros faltantes.
2. Las cuotas mensuales actuales FREE=10/PAID=200 y operaciones habilitadas se conservan. Pueden restringir antes que los cupos diarios del piloto; revisar la configuración existente de planes mediante el administrador antes de altas/activación, sin introducir suscripciones.
3. Un resultado perdido conserva presupuesto y bloquea repetir la misma clave; puede requerir registro manual. Audio con transcripción exitosa e interpretación rechazada conserva el consumo de transcripción. Recuperación/refunds/retención más amplios corresponden a S09/S11/S12 y no se iniciaron.
4. Un proceso interrumpido deja capacidad de video ocupada de forma segura. El operador debe verificar que no sigue ejecutándose y resolverlo mediante una actuación aprobada; no hay expiración automática que autorice otro job potencialmente concurrente.
5. La alerta del 80% se emite como evento de log redactado. Enrutamiento a responsables, deduplicación operativa y alertas recibidas deben certificarse en S13; no se enviaron notificaciones externas.
6. El E2E integrado S05 continúa BLOCKED y mantiene No-Go. Navegador con respuestas simuladas y suites locales no certifican EasyPanel ni proveedores reales.
7. App/worker deben usar la misma base, configuración y versión. La configuración persistida y auditada prevalece sobre variables locales; no editar el inicio de ventana para restituir cupos. Cambios iniciales de entorno requieren control de release, no están desplegados por este trabajo.
8. Un rollback al binario anterior omitiría estos controles financieros. La compatibilidad aditiva de datos no equivale a rollback seguro: deshabilitar proveedores y validar el procedimiento antes de cualquier publicación/rollback autorizado.

Recomendación final: cerrar técnicamente S06 sujeto a revisión de este candidato, sus reservas provisionales y los pendientes registrados. Este cierre no autoriza release ni consumo real. S07 no iniciada. No hubo push, merge, deploy, migraciones persistentes, usuarios reales ni consumo externo.

Evidencia local fuera de Git: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s06-validation-20261010/` contiene XML JUnit de la suite completa final, los 47 casos S06 y las regresiones dirigidas. Capturas JavaScript se conservan en `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s06-js-evidence-20261010/`. Los contenedores DB/tests reutilizados se detuvieron después de exportar evidencia; no se eliminaron contenedores, imágenes ni volúmenes existentes.
