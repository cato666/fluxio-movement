# S02 — Cuentas desactivadas en WhatsApp

Fecha: 2026-10-10. Rama: codex/pilot-v1-stabilization.
Estado: VALIDACIÓN FINAL EN CURSO; detenerse al cerrar S02 para revisión.

## Revisión Git y alcance

- Candidato S01 inicial: a4af305f4e8642f7e9ecaacc8e790eb724494098.
- Cierre documental S01: feadbd2; no añadió cambios funcionales.
- Commit funcional final S02: f92487a2ed9779df74235479a3293fe60814f0ba.
- El commit documental de cierre se identifica con: git log -1 --format=%H -- docs/pilot-v1/S02_IMPLEMENTATION_REPORT.md. Su SHA se entrega junto con este informe.
- Trabajo exclusivamente en el worktree independiente de estabilización. El original conserva su rama codex/bitacora-entrenamiento y HEAD 97583b5c191fd48d4282ad42d0b020d6cb1709a1.
- Integridad del original: 153 hashes coinciden; estado Git idéntico al snapshot S01.
- Sin cambios de modelos, contratos HTTP, dependencias, frontend ni migraciones. Head de Alembic: 0022_administration.

## Archivos modificados

| Archivo | Cambio S02 |
|---|---|
| app/administration.py | Desactivar un atleta revoca el canal dentro de la misma transacción administrativa. |
| app/whatsapp/identity.py | Resolver solo cuentas activas; bloquear emisión/verificación de códigos inactivos; bloqueo de User y revocación de identidades, desafíos, conversación e inbox/outbox pendientes. |
| app/whatsapp/runtime.py | Guard de cuenta antes de operaciones; silencio para teléfono asociado a cuenta inactiva; refrescar inbox para respetar cancelaciones concurrentes. |
| app/whatsapp/capture.py | Guard independiente antes de lectura/escritura/IA; mantener bloqueo durante interpretación y recuperación de errores esperados. |
| app/whatsapp/media.py | Descargar, almacenar y transcribir dentro de la transacción protegida del worker. |
| app/whatsapp/queue.py | Comprobar cuenta, identidad y estado actualizado después de reclamar el envío; cancelar y eliminar payload si ya no está autorizado. |
| app/whatsapp/worker.py | Conservar CANCELLED y evitar devolver eventos revocados a PENDING durante recuperación. |
| app/services/training_service.py | Propagar la opción existente commit=False a la contabilidad de interpretación/transcripción. |
| app/services/training_usage.py | Opción interna commit=True por defecto; WhatsApp usa flush para conservar el bloqueo; web mantiene commits existentes. |
| tests/test_whatsapp_account_status.py | 22 casos S02 con PostgreSQL y proveedores simulados. |
| docs/pilot-v1/S02_IMPLEMENTATION_REPORT.md | Decisiones, evidencia, límites y cierre para revisión. |

Los tres archivos de medios/servicio/contabilidad son dependencias necesarias del guard: sus commits internos liberaban el bloqueo entre la comprobación de cuenta y la llamada de IA. No se implementaron cuotas nuevas ni S06.

## Decisiones de seguridad y comportamiento

1. Cada operación de un atleta toma un bloqueo de fila User y vuelve a leer is_active. La desactivación administrativa utiliza esa misma fila. La comprobación y la operación quedan serializadas con el commit de desactivación.
2. Una cuenta activa con identidad verificada conserva el flujo de registro, consulta, propuestas y confirmaciones.
3. Desactivar revoca identidades, consume desafíos pendientes, elimina borradores y tokens de conversación, cancela inbox PENDING/PROCESSING y outbox PENDING/RETRY/SENDING y elimina sus payloads cifrados. Los identificadores y códigos de estado permiten deduplicación y trazabilidad sin conservar el contenido pendiente.
4. Webhooks nuevos de un teléfono asociado a una cuenta inactiva no descargan medios, no ejecutan IA, no guardan entrenamientos ni generan respuestas. Se conserva recepción/dedupe y motivo técnico; el contenido se elimina al procesar o cancelar.
5. El dispatcher verifica autorización después del commit SENDING y refresca la fila antes de descifrar/enviar. Una desactivación seguida de reactivación durante esa ventana no recupera el mensaje antiguo. Detectar una cuenta inactiva también revoca sus acciones si la desactivación se realizó fuera de la API.
6. Reactivar mediante administración habilita la cuenta, pero conserva identidades revocadas, desafíos consumidos y acciones canceladas. Se requiere un nuevo código válido, vigente y de un solo uso. Se mantienen los límites actuales de vinculación.
7. Una identidad activa válida prevalece sobre asociaciones históricas de ese teléfono a cuentas inactivas. Los teléfonos sin identidad válida no acceden a información personal; las instrucciones genéricas existentes no contienen datos del atleta.
8. Las identidades conservan los campos cifrados/hash del contrato actual; el cambio no imprime teléfonos, códigos, prompts ni contenido en logs. No es una eliminación de la cuenta ni de su historial de entrenamiento.
9. Los errores esperados de contenido/proveedor conservan fotos y contabilidad dentro de la transacción del worker, permitiendo aclarar/reintentar sin perder la referencia. Los errores de base de datos siguen la recuperación existente del worker.

## Límite de simultaneidad

La desactivación es efectiva al confirmar su transacción. Si una operación o envío ya empezó, la administración espera el bloqueo hasta que termine. No se inicia una operación autorizada después de confirmar la desactivación. Un mensaje que el proveedor ya aceptó puede entregarse después: no se puede retirar desde este cambio. El guard impide nuevos envíos del candidato, sin prometer revocar entregas externas ya aceptadas.

## Entorno y pruebas

- Docker Engine 28.3.2 disponible; imagen local existente fluxio-whatsapp-tests:phase2, sin rebuild.
- Red Docker interna fluxio-s01-validation-20261010, sin salida a servicios externos.
- PostgreSQL nuevo fluxio-s02-db-20261010, base movement_test; datos en tmpfs /var/lib/postgresql/data. Ninguna base persistente utilizada.
- Ejecutor fluxio-s02-tests-20261010; candidato montado /candidate en lectura. Código copiado a /tmp/s02 para ejecución y caches.
- TEST_DATABASE_RESET=1 únicamente en ese ejecutor; llaves OpenAI/Kapso vacías. FakeProvider y funciones IA simuladas.
- Migraciones desde cero mediante fixture Alembic, hasta 0022_administration. Sin nueva migración S02.
- WEEKLY_RELEASE_PUBLIC_BASE_URL=https://fluxio-s02.invalid habilita el caso de contrato de URL configurada con FakeProvider; ese dominio no se contacta.

| Verificación | Resultado |
|---|---|
| Dirigidas WhatsApp + administración, segunda iteración | PASS: 91 casos, 43.16 s. |
| S02 final: cuenta activa/inactiva, texto/foto/audio, lectura semanal, linking, pendientes, duplicados, reactivación, otros atletas y carreras | PASS: 22 casos, 11.14 s. |
| Suite Python inicial de cierre | PASS: 493 casos, 215.08 s; sin FAIL/SKIPPED. |
| Suite Python sobre commit funcional final | PASS: 495 casos, 210.85 s; 22 S02 incluidos; cero FAIL/ERROR/SKIPPED. |
| JavaScript: nueve archivos .test.cjs | PASS: 65 casos, 18.50 s; sin FAIL/SKIPPED. |
| Sintaxis/imports, migraciones y diff revisable | PASS: compileall y carga pytest; Alembic head único 0022; diff --check limpio. |
| Original sin modificaciones | PASS: 153 hashes y estado Git coincidentes. |
| Proveedores reales, EasyPanel, envíos facturables, cuentas reales | SKIPPED: fuera de la autorización. |

Comandos reproducibles dentro del ejecutor aislado:

    pytest -q tests/test_whatsapp_account_status.py --junitxml=/tmp/s02-targeted.xml
    WEEKLY_RELEASE_PUBLIC_BASE_URL=https://fluxio-s02.invalid pytest -q --junitxml=/tmp/s02-final-full.xml

JavaScript usa el Node bundled con NODE_PATH apuntando al node_modules bundled. La primera ejecución omitió NODE_PATH y falló al localizar Playwright en tres archivos (43 PASS, tres archivos FAIL); se corrigió exclusivamente el entorno y los 65 casos pasaron. No se instalaron dependencias ni se cambió código para esa corrección.

Las tres advertencias Python son deprecaciones existentes de BlockingPortal y on_event. No indican fallos S02.

## Cobertura obligatoria y regresiones

| Criterio | Evidencia |
|---|---|
| Activa registra normalmente | test_active_registers; pruebas de texto/foto/audio y confirmación existentes. |
| Inactiva no registra ni lee información | test_inactive_inbound_no_ai_or_reply y test_inactive_cannot_confirm_old_proposal. |
| Inactiva no vincula nuevamente | test_inactive_link_challenges_blocked. |
| Webhook tras desactivar no ejecuta IA | Parametrización texto/image/audio/resumen; fallo inmediato si se intenta transcribir o descargar. |
| Respuesta pendiente no se envía | PENDING/RETRY/SENDING; guard ante cambio externo; carrera claim/desactivar/reactivar. |
| Duplicados no añaden respuestas | Mismo provider_message_id aceptado cero veces tras primer procesamiento; regresiones de confirmación duplicada. |
| Reactivación exige autorización válida | Nuevo código, identidad previa revocada, botón anterior inválido, desafío cacheado consumido. |
| Otras cuentas funcionan | test_other_active_identity_unaffected. |
| Protección durante IA y envío | NOWAIT desde una segunda sesión comprueba bloqueo de User, incluso tras report_usage, descarga, foto y audio. |
| Recuperación sin perder foto tras error IA | test_photo_ai_failure_retains_media_and_minimal_accounting. |
| Contratos, auth, coaches y biomecánica | Suite Python completa: contratos WhatsApp/bitácora, análisis, revisiones, perfiles/validación de ejercicios incluidos Overhead Squat y HSPU. |

## Riesgos pendientes y recomendación

- La transacción protegida puede durar lo que dure la descarga/IA/envío; la desactivación administrativa puede esperar. No se cambiaron timeouts ni la política de reintentos.
- En WhatsApp, la contabilidad de IA/medios se confirma con la operación del worker. Una terminación abrupta antes del commit puede perder ese detalle de uso o dejar un archivo sin fila confirmada; el intento de inbox previamente confirmado y la política SENDING/UNCERTAIN permanecen. La conciliación de costos y recuperación operativa corresponden a S06/S12, pendientes; no se ejecutaron aquí.
- El guard no sustituye la administración autorizada: desactivar y reactivar por SQL directo, sin que ningún worker observe el estado inactivo, evade la revocación del ciclo de vida. El procedimiento soportado es la API administrativa.
- Ningún test real en EasyPanel ni certificación con proveedores externos; las diferencias de versión desplegada no se han vuelto a verificar. No se autoriza publicación.
- No se cambiaron permisos de coach, consentimiento de sharing, cuotas, demos ni tareas S03 y posteriores.

Recomendación final: PENDIENTE del resultado de la suite del commit funcional final. Al cerrar la validación, detenerse para revisión explícita antes de S03.

## Evidencia conservada y entorno al cierre

Los JUnit de 495 y 22 casos est�n guardados en C:/Users/desarrollo/AppData/Local/Temp/fluxio-s02-validation-20261010/ (s02-final-full.xml y s02-targeted.xml). Las ocho capturas de las pruebas JavaScript est�n en C:/Users/desarrollo/AppData/Local/Temp/fluxio-s02-js-evidence-20261010/. No se incorporaron logs ni artefactos .impeccable al candidato.

La copia ejecutada coincide por SHA-256 con los diez archivos funcionales/de pruebas del commit f92487a. Los contenedores creados �nicamente para S02 se detienen tras conservar la evidencia; su base tmpfs es desechable. No se borraron im�genes, contenedores ni vol�menes existentes, ni se alter� la red interna heredada de S01.
