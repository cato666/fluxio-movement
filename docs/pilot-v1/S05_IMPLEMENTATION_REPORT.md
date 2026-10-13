# Revalidación S05 del candidato Pilot A — 2026-10-12

Candidato funcional ee489be19c72aa0da51ff407a00d1354ecc6fa56. **PASS final: nueve casos integrados navegador/backend/PostgreSQL/storage desechables**, incluido modal de foto. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-_qb62b_q`. Primero FAIL por timeout al crear enlace: el harness carecía de WEEKLY_SHARE_ENCRYPTION_KEY requerido por recuperación de enlaces. Una repetición sin cambio confirmó el fallo. Corrección: clave efímera generada dentro del proceso aislado, sin usar/imprimir claves operativas. Tercer intento FAIL al esperar imagen lazy del header cerrado; actualizar ensayo para abrir sección, comprobar todas las fotos, abrir modal y cerrarlo. Cuarta ejecución completa PASS. No se relajaron assertions de privacidad/idempotencia; código funcional intacto. Evidencias anteriores en PILOT_A_PUBLICATION_VALIDATION.json. Contenedores propios detenidos; cero proveedores o datos persistentes. Certificación real del dominio y canales aún pendiente; Pilot NO-GO.

---

# Adenda vigente — cierre del E2E integrado S05 (Pilot A)

Fecha: 2026-10-11. Rama codex/pilot-v1-stabilization; candidato funcional base `8db554430687147208c4f63170072dcb7a534d3e`, S17 técnicamente validada. Único objetivo: nueve casos integrados de consentimiento/privacidad. Estado de ejecución definitiva: **PASS — nueve casos obligatorios, cero FAIL/SKIPPED; tres guards adicionales PASS. El bloqueo E2E integrado local S05 queda cerrado con evidencia verificable.** **Sin cambios funcionales** en app, modelos, contratos o migraciones.

## Entorno seguro y reproducción

- Red Docker nueva, Internal=true, sin conexión a redes preexistentes. Segmento RFC1918 /28 previamente comprobado contra IPAM Docker y rutas Windows/WSL; no se expande ni modifica una red existente.
- PostgreSQL 17.6 de imagen local cacheada, base exclusiva movement_e2e_s05, PGDATA tmpfs y ningún mount/puerto persistente. Migración desde cero a 0024 exclusivamente en esa base temporal. Dos cuentas sintéticas creadas explícitamente; seed demo deshabilitado.
- Runtime local cacheado de pruebas con root read-only, source bind read-only y `/tmp` tmpfs (DB/files sin volúmenes). 94 archivos app comparados por SHA-256 con el candidato dentro del runtime real; imagen de pruebas no se representa como digest de release productivo S14.
- Backend FastAPI/uvicorn real; sesión/cookies/Origin existentes, origen loopback explícito de prueba y proxies no confiables. IA/transcripción/WhatsApp deshabilitados, claves de proveedor vacías, worker no arrancado. Navegador Playwright nuevo, perfiles/contextos efímeros y zona America/Santiago, sin datos reales.
- Sin puertos Docker publicados. Un puente HTTP stdlib temporal en 127.0.0.1 transporta solicitudes/respuestas por Docker stdin/stdout hacia HTTP TCP real 127.0.0.1:8000 del contenedor. Preserva cookies/Origin/cuerpos/headers de seguridad; no fabrica respuestas ni altera rutas. Navegador, servidor, PostgreSQL y archivos participan conjuntamente; no se usa TestClient ni route.fulfill. Única intercepción del navegador: abortar solicitudes externas, continuar toda solicitud de origen local al servidor real.
- Access logs HTTP deshabilitados y puente sin log de paths; errores del ensayo redactados. Tokens no salen en informes/logs/JSON. Fotos y captura visual exclusivamente sintéticas.

Reproducción: disponer de Docker, las imágenes locales cacheadas postgres:17.6-bookworm y fluxio-whatsapp-tests:phase2, Node/Playwright/Chromium locales; configurar NODE_PATH según instalación local. Desde el worktree de estabilización, ejecutar `python scripts/test_s05_integrated.py --node <ruta-node-local> --subnet <segmento-RFC1918-libre-/24-a-/28>`. El script rechaza otra rama, solapamientos de red/rutas, mounts inesperados, DB persistente, source writable o red ajena. Nunca pull/build/apt/pip/descarga modelo, proveedores, cuentas reales o DB ajenas. El script no permite indicar una base existente. Su evidencia sale a un directorio temporal nuevo fuera del repo.

Los únicos contenedores creados por instancia se detienen al terminar mediante comprobación de label; tmpfs pierde sus datos. No se borran imágenes/contenedores/volúmenes existentes. Nuevos contenedores detenidos y redes internas se conservan para inspección; no guardan datos DB/storage persistentes. El puente y el navegador se cierran; no queda listener publicado.

## Casos obligatorios y evidencia

| Caso | Comprobación integrada | Estado definitivo |
|---|---|---|
| 1 Guardar sin publicar | Login web, carga de PNG, normalización, completar/guardar manual vía UI; DB una sesión/una imagen/file, cero shares | PASS |
| 2 Consentimiento previo | Abrir sin publicar, aviso alcance vivo, checkbox explícito, crear vía UI; recibo DB; HTML/foto anónimos reales y pixels cargados | PASS |
| 3 Rechazar | Checkbox desmarcado no POST/publicación; POST consent=false rechazado 422; marcar y cancelar mantiene cero shares | PASS |
| 4 Revocar enlace | Revocación UI; nueva navegación HTML anónima devuelve 404 | PASS |
| 5 Foto revocada | GET real de imagen mediante token revocado devuelve 404; archivo privado se conserva | PASS |
| 6 Vencimiento | Segunda publicación consentida; expiry modificado solo en fixture guardada DB temporal; HTML/foto devuelven 404 | PASS |
| 7 Cuenta desactivada | Tercera publicación consentida; desactivar solo cuenta sintética en DB temporal; HTML/foto 404 y cookie previa sin acceso privado 401 | PASS |
| 8 Información ajena | Segundo atleta: detalle/foto/revocación ajenos 404; listado/semana propios vacíos; body athlete_id rechazado 422; anónimo privado 401 | PASS |
| 9 Duplicados | Doble clic UI genera una fila; dos POST simultáneos reales con mismo request_id devuelven replay sin path nuevo y DB sigue una fila | PASS |

Los tres shares finales son intencionales y corresponden a tres consentimientos separados para revocar/vencer/desactivar; no son duplicados. Se verifica conservación de sesión/imagen/archivo y consumo cero PlanInteraction/inbox/outbox. Nueve escenarios de un ensayo integrado, no nueve pruebas añadidas a pytest ni a la suite JS unitaria.

Evidencia definitiva: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-3hghvp_c/` con environment.json (fuentes/digests de pruebas/aislamiento), results.json (escenarios/contadores), execution.log redactado y journal-private.png. Hashes archivados en harness-checksums.json y evidence-checksums.json. Runtime source matches candidate=true; 94 archivos comprobados; own_containers_stopped=true. No HAR, cookies exportadas o trazas con tokens.

Preparación anterior conservada: vgwoxykd BLOCKED por pools Docker agotados; 5ctkwgpq BLOCKED porque red interna no asigna puerto publicado en Docker Desktop; a9wg_ra_ 8 PASS y 1 FAIL en harness, sin marcar cierre; qar5pwq4 9 PASS tras esperar respuesta de publicación nueva en lugar de reutilizar input previo; 00mc8gva BLOCKED por escape incorrecto del chequeo adicional de hashes, corregido y comandos embebidos parseados antes de ejecución final. No se relajaron controles ni se cambió código funcional para resolver problemas del ensayo.

## Pruebas adicionales, límites y decisión

Sintaxis Python de las tres herramientas y comandos embebidos PASS; Node --check PASS. Guards negativos PASS (sin opt-in, DB persistente y clave de proveedor): rechazo previo a import/conexión DB; guards.json. Fingerprint original PASS: 153 paths y estado/rama/HEAD intactos; diff --check PASS; ningún cambio en app/Compose/migraciones. Escaneo acotado de patrones de credenciales/artefactos locales sin coincidencias; no sustituye S14. Suites generales: SKIPPED en esta tarea porque no cambia código funcional; últimos resultados históricos S17 803 Python/75 JS PASS, no se presentan como reejecución de este E2E. Migraciones persistentes, destino EasyPanel y proveedores reales: NOT RUN.

Este ensayo local no certifica HTTPS/cookie Secure/proxy reales de EasyPanel ni OpenAI/Kapso, video/costos o restore de backups. Cierra el gate integrado local S05 tras nueve resultados finales PASS; no cierra S11/S16 ni otras fases.

Commit único de validación: obtener SHA con `git log -1 --format=%H -- docs/pilot-v1/S05_IMPLEMENTATION_REPORT.md`; se comunica al entregar. **Pilot NO-GO**: restauración real de respaldos, costos adicionales de video, paridad EasyPanel y pruebas reales de canales habilitados siguen pendientes. No se inicia automáticamente la siguiente tarea. Workspace original conservado, sin push/merge/deploy ni gasto.

El reporte siguiente conserva evidencia histórica S05; su bloqueo ambiental anterior no sustituye la decisión de esta adenda vigente.

---

# S05 — Consentimiento explícito para compartir semanas

Fecha: 2026-10-10. Alcance: exclusivamente S05; S06 no iniciada.

Rama: `codex/pilot-v1-stabilization`.
Base aprobada: `4ba63a441016c95cb55d61f8b4288b42078d98ef`.
Commit funcional probado: `6ff45479192e7f404134da54e941ddae8467d1b8`.
El commit documental final se obtiene mediante `git log -1 --format=%H -- docs/pilot-v1/S05_IMPLEMENTATION_REPORT.md`; se comunica al entregar la etapa y no modifica el código probado.

Estado: lista para revisión técnica de S05. Las suites completas y las verificaciones obligatorias de consentimiento pasan. El E2E combinado navegador/servidor real permanece bloqueado por el entorno; se validaron separadamente la interfaz en navegador y el flujo HTTP real dentro del contenedor. No se autoriza publicación con este cierre.

## Decisión sobre enlaces históricos

El usuario aprobó expresamente: «Bloquear históricos y crear enlaces nuevos con consentimiento».

Los enlaces sin evidencia de consentimiento quedan inaccesibles públicamente. Se conservan filas, hashes, vencimientos y snapshots históricos; pueden consultarse en el listado privado y revocarse. Aceptar el aviso crea un enlace nuevo y nunca habilita el token anterior. Los entrenamientos existentes permanecen intactos.

## Comportamiento anterior y nuevo

Guardar entrenamientos y notas ya era privado en la base aprobada; las pruebas fijan esta propiedad. La publicación previa permitía crear enlaces sin consentimiento verificable: WhatsApp publicaba directamente al recibir el comando y la tarjeta web disparaba automáticamente la creación al abrir el panel.

Ahora Guardar confirma solamente el registro. Compartir presenta un aviso sobre la semana completa, entrenamientos, resultados, notas, RPE y fotografías, incluidos cambios y registros añadidos posteriormente. La publicación requiere una aceptación explícita y admite como máximo 168 horas; conserva la revocación.

WhatsApp guarda una solicitud pendiente cifrada con semana, versión y nonce, usando el estado existente y su vencimiento de 24 horas. Solo el botón vigente «Aceptar y compartir» crea el enlace. Cancelar, acciones antiguas, solicitudes vencidas y cuentas desactivadas no publican ni ejecutan IA. «Guardar» no significa aceptar; «revocar semana» sigue disponible y elimina la solicitud pendiente. La creación, consumo del estado y respuesta utilizan la transacción existente del worker.

La web abre el panel sin publicar, muestra una casilla inicialmente desmarcada y exige su aceptación. Cancelar antes de enviar no realiza POST. Mientras se procesa, bloquea cierres y acciones duplicadas; después de enviar, la acción se denomina Cerrar. Un identificador de solicitud por semana se conserva en sessionStorage ante respuestas inciertas, sin guardar tokens. Volver al panel exige marcar nuevamente la aceptación. Los enlaces históricos se identifican como bloqueados y pueden revocarse.

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `app/services/weekly_summary.py` | Validación de consentimiento, cuenta activa, TTL, recibo mínimo, idempotencia y autorización pública común. |
| `app/weekly.py` | Contrato estricto del POST de publicación y vinculación al atleta autenticado. |
| `app/whatsapp/capture.py` | Solicitud, aceptación y cancelación del consentimiento; validación de URL pública y nonce. |
| `app/static/training.js` | Separación Guardar/Compartir, casilla, reintentos y estado de enlaces históricos. |
| `app/static/weekly-expanded.css` | Presentación del aviso y objetivo táctil de la casilla dentro del diseño existente. |
| `tests/share_helpers.py` | Datos de consentimiento para pruebas existentes. |
| `tests/test_sharing_consent.py` | 32 pruebas específicas de privacidad, idempotencia, autorización y TTL. |
| `tests/test_weekly_summary.py` | Regresiones adaptadas al consentimiento explícito. |
| `tests/test_weekly_release_validation.py` | Migraciones históricas y flujo semanal actualizado. |
| `tests/test_whatsapp_contracts.py` | Única excepción intencional de esquema: SharePayload. |
| `tests/training-ux.test.cjs` | Consentimiento en navegador, cancelación, duplicados y recuperación de solicitud incierta. |
| `tests/e2e/weekly.cjs` | Flujo combinado actualizado para consentimiento. |
| `docs/pilot-v1/S05_IMPLEMENTATION_REPORT.md` | Evidencia y límites de la etapa. |

No se modificaron modelos, migraciones, dependencias ni configuración de seguridad de S04. No se incorporaron artefactos locales, capturas, logs ni archivos .impeccable. Se utilizó Impeccable únicamente para la claridad y verificación visual del panel existente.

## Contrato y evidencia mínima

POST `/api/training-week/shares` conserva la ruta y el día opcional. Exige `consent` booleano estricto igual a true, `consent_version` igual a `weekly-live-v1` y `request_id` UUID. Rechaza campos extra, versiones incorrectas y publicaciones sin aceptación con 422. El atleta se obtiene de la sesión; no puede elegirse mediante el cuerpo.

La fila utiliza el JSONB snapshot existente como recibo mínimo: version, accepted, channel, request_id y accepted_at UTC del servidor; WhatsApp añade event_id del inbox. La propiedad del recurso sigue en athlete_id. No se guarda IP, teléfono, email, texto del mensaje, copia del entrenamiento ni token público en el recibo. Los snapshots anteriores se preservan; las nuevas filas guardan únicamente este recibo.

La creación bloquea la fila User y vuelve a comprobar su estado activo, coordinándose con la desactivación de S02. Repetir el mismo request_id para la misma semana devuelve la misma fila, path nulo y already_created; no crea otra publicación, prolonga vencimientos ni revive enlaces revocados. Usar el identificador para otra semana se rechaza. Se probó concurrencia con dos sesiones independientes.

Se almacena únicamente el hash del token. HTML y fotografías comparten la comprobación de token, vigencia, revocación, consentimiento y atleta activo, con respuesta genérica 404 para acceso público inválido. La lista privada incluye consent_required sin revelar URLs. Los mecanismos de S02/S03 continúan aplicándose.

## Validación y entorno

PostgreSQL 17.6 desechable sobre tmpfs, sin volúmenes persistentes. La suite utilizó movement_test con el guard de reset; el servidor HTTP utilizó otra base y otro rol, movement_e2e_s05, en el mismo clúster temporal. Cuentas exclusivamente sintéticas. Se reutilizó la imagen local existente y una red Docker interna; no se conectó EasyPanel ni proveedores reales. OpenAI/Kapso quedaron deshabilitados o simulados.

| Verificación | Estado | Resultado |
|---|---|---|
| Python completa, código final | PASS | 596 aprobadas, 0 fallos/errores/omitidas; 173,22 s. |
| JavaScript completa | PASS | 67 aprobadas, 0 fallos/omitidas; 21,743 s. |
| Selección S05/S02/S03/S04/WhatsApp/semanas/contratos | PASS | 178 aprobadas; 66,88 s. |
| Consentimiento final, incluidos límites TTL | PASS | 32 aprobadas; 9,73 s. |
| Migraciones desde cero y recorrido histórico | PASS | Suite completa sobre base desechable; head 0022_administration, sin nueva migración. |
| Contratos existentes | PASS | Operaciones y esquemas iguales a la base salvo SharePayload, cambio de seguridad explícito; fixture baseline conservado. |
| Regresiones biomecánicas y flujos previos | PASS | Incluidas en Python completa; OHS, HSPU y ejercicios soportados. |
| HTTP real dentro del contenedor | PASS | Guardado privado con foto, rechazo 422, aceptación única, repetición, nota posterior, HTML/foto, revocación, expiración y desactivación. |
| Interfaz en navegador con respuestas simuladas | PASS | Aceptación, cancelación, duplicados y nonce tras respuesta incierta; inspección desktop/mobile. |
| Navegador y servidor HTTP real combinados | BLOCKED | Puerto no publicado hacia host en red interna; conexión rechazada antes de login. No se presenta como aprobado. |
| Integridad del código ejecutado | PASS | 177 archivos app/tests/scripts/migrations y configuración comparados por SHA256, ninguna diferencia. |
| Workspace original | PASS | 153 rutas conservan hashes y estado Git; rama y HEAD originales intactos. |
| Logs del servidor de prueba | PASS | Sin rutas con tokens públicos; solo mensajes de arranque, acceso Uvicorn deshabilitado. |
| EasyPanel y servicios facturables | SKIPPED | Fuera de autorización; ningún despliegue ni consumo. |

Las pruebas específicas cubren guardado y notas sin enlaces, rechazo sin publicación, aceptación única, webhook duplicado, HTML y fotografías vencidos/revocados/inactivos, bloqueo histórico, datos históricos intactos, autorización del atleta, nonce antiguo, cancelación y expiración del consentimiento, cuentas desactivadas, ausencia de IA y concurrencia. La suite completa incluye las regresiones de S02, S03 y S04.

Durante la validación inicial, el fixture de migración consultaba el modelo User moderno en el esquema 0021 y dejaba errores posteriores de preparación. Se corrigió el fixture para insertar el enlace histórico con el esquema correspondiente y completar/restaurar la cadena; no se alteró el control de cuentas activas. También se actualizó una expectativa antigua de copia del entrenamiento en snapshot y se corrigió la ubicación inicial de la validación event_id antes de cerrar el código. Resultado inicial: 1 fallo, 12 aprobadas y 45 errores derivados; resultados finales: cero fallos y errores. Las tres advertencias de deprecación de la suite completa son preexistentes.

La revisión automática rechazó conectar la app de prueba a bridge porque ampliaba la superficie de red y podía exponer sesiones y datos de prueba. Ese cambio no se ejecutó. Se completó la verificación HTTP mediante loopback dentro del contenedor existente, sin ampliar conectividad. Queda pendiente únicamente la comprobación combinada de navegador contra servidor real en un entorno que publique localhost de forma autorizada.

Evidencia local no incluida en Git: XML JUnit y verificador HTTP en `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-validation-20261010/`; capturas de interfaz en `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-js-evidence-20261010/`. Los tres contenedores propios de S05 quedaron detenidos; no se borraron imágenes, contenedores ni volúmenes existentes.

## Compatibilidad, riesgos y revisión

- Clientes anteriores que publicaban sin consentimiento reciben 422 y requieren la interfaz actualizada. La semana sigue siendo dinámica; cambiar el aviso exige actualizar coherentemente cliente, servidor y versión.
- Los enlaces históricos quedan bloqueados deliberadamente. No se borran ni convierten sus datos; cada publicación nueva exige aceptación nueva.
- Una respuesta perdida no permite recuperar el token a partir del hash. El usuario puede revocar y crear otro enlace con nuevo consentimiento; el reintento no duplica filas.
- Desactivar bloquea el acceso público. Reactivar puede devolver acceso a enlaces con consentimiento vigente que no estén revocados ni expirados; las identidades WhatsApp mantienen las restricciones de S02.
- Revocar impide nuevas consultas, pero no elimina copias ya descargadas ni interrumpe una descarga previamente autorizada. Cachés y logs del proxy de EasyPanel siguen sin verificar; requieren revisión antes del despliegue.
- Volver a S04 restablecería la política anterior de enlaces históricos. Antes de un rollback operativo debe bloquearse el acceso público o aplicarse una revocación autorizada; no se realizaron acciones sobre datos reales.
- El recibo registra la acción de una sesión/identidad autenticada; no constituye una firma criptográfica ni prueba legal de identidad. No se amplió la recopilación de datos personales.

Recomendación: cerrar técnicamente S05 sujeto a revisión de estos cambios y del límite del E2E combinado. La publicación y la siguiente etapa requieren autorización independiente. No se inició S06, no hubo push, merge, deploy ni migraciones persistentes.
