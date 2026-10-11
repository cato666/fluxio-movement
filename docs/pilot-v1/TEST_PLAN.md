# Estado vigente — cierre final Pilot A

Validación local final del candidato `03cfd4387a75f70fae60ccd2108a83d24dc57f31`: Python **820 PASS, 1 SKIPPED, 0 FAIL** (257,41 s); JavaScript **77 PASS, 0 FAIL/SKIPPED**. La prueba omitida requiere WEEKLY_RELEASE_PUBLIC_BASE_URL real y queda **NOT RUN**, sin afirmar paridad de dominio. PostgreSQL nuevo tmpfs, red interna nueva, sin puertos Docker publicados ni credenciales de proveedores; migraciones desde cero y worker vacío PASS; contenedores propios detenidos. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-2e4m_dlq/offline-tests.log` y `environment.json`. Tres advertencias de deprecación no bloquean estas pruebas. Workspace original: 153 rutas verificadas sin cambios.

Fecha: 2026-10-11, America/Santiago. Rama: codex/pilot-v1-stabilization. Candidato auditado: `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. **Pilot A NO-GO**. Alcance obligatorio: bitácora + WhatsApp + video certificado + coach titular/suplente, 3–5 atletas, 30 días. Esta entrega no autoriza proveedores, infraestructura persistente ni publicación.

Estados: PASS = evidencia ejecutada y limitada a su entorno; FAIL = defecto/evaluación fallida demostrada; BLOCKED = falta autorización, acceso, responsable o dependencia; NOT RUN = sin ejecución. Resultados históricos no certifican el candidato final ni el destino.

## Validación vigente

Tres niveles separados: simulada/unitaria; navegador/API/PostgreSQL/storage sintéticos locales; pruebas reales de canales y destino autorizadas. No sumar suites superpuestas ni afirmar factura por reservas. Matrices específicas en PILOT_A_WHATSAPP_VALIDATION.md y PILOT_A_VIDEO_CERTIFICATION.md. Suites finales locales concluidas; resultados abajo.

Obligatorios: permisos dos atletas/dos coaches/admin; S02–S10 y 200 registros; consentimiento/replay/revoke/expiración y fotos; recuperación cifrada owner/claves/rotación; modal/foco/CSP; registro foto/audio real; video clips/abstención/costo/reinicio; revisión completa; restore/rollback; alertas; smoke EasyPanel. E2E S05 histórico PASS permanece; revalidación final/destino NOT RUN.

Consultar [readiness final](PILOT_A_FINAL_READINESS.md), [video](PILOT_A_VIDEO_CERTIFICATION.md), [WhatsApp](PILOT_A_WHATSAPP_VALIDATION.md) y [release](PILOT_A_RELEASE_PLAN.md).

---

## Evidencia histórica conservada — no sustituye estado vigente

# Actualización vigente — E2E integrado S05 / Pilot A

Fecha: 2026-10-11. Candidato funcional 8db5544. Validación definitiva integrada S05 **PASS: nueve casos, cero FAIL/SKIPPED; tres guards adicionales PASS** sobre navegador real, FastAPI/HTTP real, PostgreSQL tmpfs y storage tmpfs, con red Docker nueva interna y transporte loopback temporal sin puertos Docker publicados. Nueve casos obligatorios y evidencia reproducible en [adenda S05](S05_IMPLEMENTATION_REPORT.md). No se sustituyen por mocks o TestClient; no se cambió código funcional.

- [x] E2E integrado local S05: nueve casos PASS; runtime coincide por hash (94 fuentes); entorno propio detenido. Evidencia: results.json/environment.json/guards.json y hashes en C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-3hghvp_c/. No certifica destino productivo.
- [ ] Restauración real de respaldos: PENDIENTE.
- [ ] Costos adicionales de video: PENDIENTE.
- [ ] Paridad con EasyPanel: PENDIENTE.
- [ ] Pruebas reales de canales habilitados: PENDIENTE; sin autorización de proveedores/gasto.

**Pilot NO-GO**. S11 parcial y S16 preparación documental no se cierran por esta prueba. No se inicia otra tarea; detenerse para revisión. Los encabezados siguientes preservan estados históricos y resultados S17, no sustituyen esta decisión vigente.

---

# Estado vigente — S17 cierre técnico local PASS, pendiente de revisión

Fecha: 2026-10-11. Base c5d1764 verificada, original intacto. S08–S10 cerradas localmente; S11 parcial; S16 preparación documental completada, validación operativa pendiente. S12/S13/S15/S18 conservan dependencias abiertas; S14 necesita build/identidad/scan local verificables. Se completó **solo S17** con mitigación explícita y recursos desechables existentes: **803 Python / 75 JavaScript PASS**; 57 dirigidas son subconjunto, no sumables; sin FAIL/ERROR/SKIPPED en la suite Python. El commit único se identifica mediante git log del reporte S17; no se repiten cierres anteriores. Auditoría completa, cambios y resultados en [reporte S17](S17_IMPLEMENTATION_REPORT.md).

Mitigación S17: límite de listado 200 conservado e informado, desempate estable; filas anteriores conservadas y consultables en resumen semanal/detalle privado. Registro manual permite superar 200, sin consumo IA. Sin paginación/exportador nuevo ni garantía de que toda cohorte permanecerá debajo de 200. No borrar para liberar historial; aviso operativo a 150 es propuesta, no automatismo certificado.

**NO-GO**: E2E integrado S05 BLOCKED; restauración real de respaldos PENDIENTE; costos adicionales de video PENDIENTE; paridad EasyPanel PENDIENTE; pruebas reales de canales habilitados PENDIENTE. S11/S16 no se cierran por resultados locales. Tras S17 se detiene para revisión, sin avanzar automáticamente. El texto siguiente conserva historia, no reemplaza este estado vigente.

---

# Actualización Pilot A — política de respaldo aprobada, ejecución deshabilitada

El propietario aprueba objetivo privado S3 compatible/Azure Blob independiente del VPS, AES-256/TLS, PostgreSQL+archivos privados, frecuencia diaria/predeploy, siete copias diarias y copia pre-release durante piloto, rol propietario técnico, restore aislado y credenciales mínimas/alertas. **Proveedor, bucket/contenedor y responsable operativo formal no confirmados.** Preparados [configuración inerte](BACKUP_CONFIGURATION.example.json), [procedimiento](BACKUP_RESTORE_RUNBOOK.md) y [reporte S16](S16_IMPLEMENTATION_REPORT.md). Sin job instalado, respaldo, restore, migración, deploy ni infraestructura persistente.

S16 preparación documental, cierre BLOCKED; S11 parcial, limpieza efectiva BLOCKED. El inventario/guard S11 sigue siendo código vigente. S12–S15/S17–S18 no iniciadas; S14/digest pendiente. Retención y objetivos están aprobados, no medidos. Pilot **NO-GO**: E2E S05, costos extra video, paridad EasyPanel, proveedores reales y backup/restore destino permanecen pendientes. La evidencia histórica siguiente no sustituye este estado vigente.

---

# Actualización vigente S11 — política aprobada, cierre bloqueado

Fecha: 2026-10-11. La respuesta «Si» aprueba la política S11/S16. S11 tiene una entrega **PARCIAL**: inventario read-only y bloqueo de eliminación de fotografías por el worker; no cuarentena ni borrado efectivo. Dependencia S16 **BLOCKED**: respaldo coherente/restore comprobado, destino y responsable pendientes. No usar una variable de configuración como sustituto de evidencia de recuperación. Sin migración nueva; head 0024 conservado. S12–S18 no iniciadas.

Entrega funcional parcial `a4aefd7726a5d6f5f9b5c454bca16192ce0fe62d`: 795 Python / 72 JavaScript PASS (44 dirigidas incluidas, no sumables). 0 FAIL / 0 ERROR / 0 SKIPPED en Python. Los resultados actuales y el commit funcional constan en [S11_IMPLEMENTATION_REPORT.md](S11_IMPLEMENTATION_REPORT.md). Conservados: E2E integrado S05 **BLOCKED**, costos adicionales reales de video **PENDIENTE**, paridad EasyPanel **PENDIENTE**, proveedores reales **PENDIENTE**, backup/restore del destino **PENDIENTE**. Pilot **NO-GO**. La política ya no está pendiente; la implementación efectiva y su dependencia sí.

El texto siguiente conserva evidencia histórica anterior a esta aprobación, no representa el estado vigente S11.

---

# Evidencia vigente S10 y validaciones pendientes

Fecha: 2026-10-11. **S10 cierre técnico local PASS; S11 auditada/BLOCKED por política de retención y dependencia S16. S12–S18 no iniciadas. Pilot NO-GO.** Código actual `09b4215f5b1aec1e44e77f67e42360ecedfd373c`, entrega S10 `023736b6429524f5d5cecbc2c8febe738157a9e1`. Los tres defectos P1 de S10 fueron corregidos y sus reproducciones ahora pasan; la parada anterior S10 fue superada mediante autorización expresa del usuario. El commit documental actual no implementa S11.

| Ejecución final | PASS | FAIL | ERROR | SKIPPED | Alcance |
|---|---:|---:|---:|---:|---|
| S10 Python completa | 787 | 0 | 0 | 0 | PostgreSQL tmpfs; proveedores simulados; 238,01 s |
| S10 dirigidas CRUD/integridad/migración/WhatsApp | 89 | 0 | 0 | 0 | Subconjunto de completa |
| S10 contratos/migración | 2 | 0 | 0 | 0 | Subconjunto de completa |
| Nota web/chat/semana adicional | 1 | 0 | 0 | 0 | Subconjunto de completa |
| S10 JS completa final | 72 | 0 | 0 | 0 | API simulada, incluye copia inmutable/arrays; 24,63 s |
| S11–S18 propias | — | — | — | — | NOT RUN; auditoría S11 de fuentes no es prueba ejecutada |

No sumar dirigidas a completa. Los tres nuevos casos originalmente FAIL ahora forman parte de los 787 PASS. La primera suite S10 tuvo 786 PASS/1 FAIL por cabecera OpenAPI no incluida en allowlist; se corrigió exclusivamente la extensión opcional y se volvió a ejecutar completa. JavaScript final se repitió tras corregir la comparación de arrays; Python no tuvo cambios posteriores a su último PASS.

Migraciones: desde cero→0024, roundtrip/check sin drift y 0023→0024 con sesión histórica intacta, únicamente DB movement_test con reset explícito. Replay desde otro proceso, concurrencia, rollback, nota visible, ownership, manual sin presupuesto y conservación de foto/medio probados.

Evidencia: C:/Users/desarrollo/AppData/Local/Temp/fluxio-s10-final-validation-20261011/ (XML, resumen, log JS y 188 SHA-256). Reproducción fallida inicial permanece en fluxio-s10-validation-20261011/. No se ocultan incidentes anteriores como SKIPPED.

1. **BLOCKED:** E2E integrado navegador/servidor S05; no sustituido por API simulada/TestClient.
2. **PENDIENTE:** reserva/control de costos adicionales reales de video.
3. **PENDIENTE:** paridad de commit/digest/esquema/configuración/worker con EasyPanel.
4. **PENDIENTE:** validación de proveedores reales; gasto/envíos no autorizados.
5. **PENDIENTE:** backup y restauración del destino; prueba temporal no los certifica.

Plan histórico a continuación; sus E2E no certifican el candidato actual.

---

# Plan de validación del piloto

Estado: propuesto, no ejecutado el 10-10. QA owner registra fecha, commit/digest, revisión SQL, ambiente, fixture, expected/actual, capturas redactadas y PASS/FAIL/BLOCKED. Un caso sin evidencia permanece BLOCKED; no cuenta como PASS. Resultados históricos en RELEASE_READINESS son baseline, no certificación del candidato.

## Entornos y autorización

- **S — Simulado:** API/DB PostgreSQL real desechable movement_test, storage temporal; Kapso/OpenAI y pose cuando corresponda fixtures, red saliente bloqueada y sin credenciales reales. Migraciones/truncados solo en este entorno efímero.
- **L — Local con servicios reales:** app/worker/DB/storage aislados, FFmpeg/pose reales y clips autorizados. OpenAI/Kapso reales solo después de autorización explícita de llamadas, destinatarios, número de pruebas y presupuesto; hasta entonces simular proveedor. Sin .env del producto ni DB persistente.
- **E — EasyPanel controlado:** primero read-only público/panel redactado; escrituras, cuentas de QA/piloto, migración y reinicios solo autorizados expresamente para el destino. Pruebas con IA/chat exigen además permiso de gasto/envío. No ejecutar pytest ni E2E fixture/reset sobre producción. Preferir staging aislado; smoke productivo usa datos identificados y minimiza mutaciones.

## Matriz E2E

Cada fila se ejecuta en S; L/E añaden evidencia donde se indica. La ausencia de autorización bloquea L/E dependientes y se informa. Borrados y fallos inducidos en E se limitan a staging/casos autorizados.

| ID / backlog | Flujo y pasos | Resultado verificable | S / L / E y cobertura existente |
| --- | --- | --- | --- |
| T01 / S02–04,07 | Alta asistida, login correcto/incorrecto, logout, duplicado, rol, cookie previa al logout/desactivar | Cuenta individual; login sin filtraciones, rol correcto y rate; sesión inactiva rechazada | S: basic_auth/administration, phase01 parcial. L: TLS/proxy. E: alta de QA autorizada y login. |
| T02 / S10 | Manual con fecha/título/workout/resultado/RPE; validar error; guardar y recargar | No sesión antes de guardar; una sesión exacta, owner correcto; error conserva entrada | S: training_sessions/service, training-ux, phase01. L/E: HTTP/DB real sin IA. |
| T03 / S06,09,10 | Foto válida/ilegible/grande/HEIC; interpretar; corregir resultado/fecha; guardar | Rechazo seguro de inválida; no inventa resultados ajenos; foto privada, borrador revisable y persistencia | S: training_interpretation/usage, phase01. L: imagen consentida/OpenAI autorizado. E: mismo caso acotado. |
| T04 / S06,09 | Permiso micrófono denegado/concedido; audio válido, silencio, 8 MB+, 180 s+, fallo transcribe/interpret | Error comprensible/fallback manual; no doble consumo al retry; texto editable y sin audio durable | S: training_transcription, training-ux, phase01. L: teléfono físico/FFmpeg y proveedor autorizado. E: HTTPS/móvil. |
| T05 / S02,05,06,08,10 | Vincular challenge; texto/foto/audio; corregir/cancelar/Guardar; replay webhook y doble Guardar/botón viejo; desvincular | Firma/challenge válidos; un registro por confirmación vigente; cuota antes de IA; no share automático; identidad revocada bloqueada | S: whatsapp_foundation/capture/contracts, whatsapp-link JS. L/E: sandbox y teléfonos explícitamente autorizados; replay real adicional controlado. |
| T06 / S10,11 | Guardar/editar/eliminar registro propio; ID ajeno; nota WhatsApp editada web; vínculo analysis eliminado | Datos consistentes, denegación ajena, confirmación de borrado; orphan con política; nada de otro atleta borrado | S: training_sessions/service/delete_analysis. L: DB/storage aislados. E: solo registros QA autorizados. |
| T07 / S10,17 | Semana actual/anterior/vacía; domingo/lunes Santiago, RPE faltante; 201 sesiones | Conteos/fechas exactos, muestra de RPE, no ceros inventados; límite listado explícito no afecta resumen | S: weekly_summary/release_validation, weekly E2E. L/E: HTTP real sin proveedores. |
| T08 / S05,11 | Guardar sin compartir; rechazar aviso; aceptar share; lector anónimo/foto; editar/agregar semana; revocar/TTL; token inválido/imagen ajena/cuenta desactivada | Opt-in previo trazable; semana viva comunicada; token hasheado; revocación/expiry y política de desactivación bloquean HTML/media; no-store/noindex | S: weekly tests y E2E más regresiones faltantes. L/E: URL/TLS/cache reales; token QA no divulgado y revocado con autorización. |
| T09 / S12,18 | Video por cada ejercicio/vista habilitada, reference_only, pose mala, tamaño inválido; analizar/vincular; reinicio intermedio | Solo soporte certificado; abstención/error por calidad; métricas/reps contrastadas por coach; progreso termina COMPLETED/FAILED | S: api/async_analysis/exercise_profiles/validation, phase01 pose fixture. L: pose/FFmpeg reales y clips consentidos; IA razonamiento si autorizada. E: pequeño clip autorizado y recursos medidos. |
| T10 / S03,18 | Solicitar coach disponible; no disponible/inactivo; request duplicada; coach ajeno; iniciar/anotar/guardar/completar; consultar atleta | Permisos y cupo; sin solicitud si no disponible; única review activa; feedback persiste y completado no se edita indebidamente | S: coach_requests/inbox/annotations/complete_review, phase01. L/E: coach QA autorizado y capacidad humana registrada. |
| T11 / S02,03,07,11 | Atletas A/B, coaches C/D/admin; IDs de sesión/imagen/analysis/review; cuenta desactivada con cookie/WhatsApp/cola/share previo | Ninguna lectura/escritura/IA indebida; todos los canales aplican activo/permiso, enlaces conforme política | S: basic_auth/administration/athlete_flow y nuevas regresiones transversales. L/E: datos QA autorizados, sin explorar cuentas reales. |
| T12 / S08,13 | Inyectar HTTP 402 Kapso; comprobar outbox/alarma; corregir condición simulada; autorización de recuperación; 429/5xx/timeout y lease vencida | 402 FAILED identificable sin auto retry; alerta; no duplica sesión/envío; 429 backoff máx 5; incierto UNCERTAIN sin replay ciego; chunks posteriores no quedan invisibles | S: foundation retry/uncertain, falta caso específico 402 y recuperación. L: stub HTTP primero; 402 real solo si sandbox permite y autorizado. E: no provocar deuda/cobro; fault injection staging. |
| T13 / S12,16 | Guardar sesión/foto/review/share; detener app/worker/DB, reiniciar con mismos volúmenes; job interrumpido y inbox pendiente; reconstruir app sin borrar mounts | Conteos/hashes/contenidos idénticos; cookie/permisos coherentes; claves descifran; inbox durable y outbox sin duplicación; job FAILED recuperable | S: persistence/foundation/async tests complementados con restart real desechable. L: contenedores y mounts reales aislados. E: staging/reinicio solo autorizado; nunca down -v. |
| T14 / S16 | Backup coordinado y restauración en DB/storage nuevos; correr candidato y binario anterior compatible | Rows/referencias/medias descifrables; RPO/RTO medidos; schema compatible; no pérdida silenciosa | S/L: copia de fixture sin datos reales. E: restore aislado de backup real solo autorizado; no restore encima del producto. |
| T15 / S06,09,13 | Último cupo concurrente web/chat, presupuesto global alcanzado, canal apagado, proveedor ausente | No se supera límite; no calls fuera de cuota; manual/consulta siguen; consumo desconocido no equivale a cero | S: administration/training_usage y regresiones chat. L/E: límites y apagado sin llamadas facturables para probar denegación. |
| T16 / S14,15 | Comparar commit/digest/schema/rutas/assets app-worker, gates CI fallidos y dependencia ausente | Candidato reproducible y deploy bloqueado al fallar; health no filtra credenciales | S/L: deployment_readiness y build/scan. E: panel read-only y smoke de imagen exacta. |

## Ejecución segura y cobertura

Después de correcciones aprobadas: primero tests específicos del ID (regla docs/AGENTS.md), luego suite completa al cierre de estabilización, nueve JS *.test.cjs y E2E tests/e2e/phase01.cjs + weekly.cjs. Estos E2E usan tests.e2e.app y flags fixture/reset: solo entorno temporal. Publicar salidas, número de skipped y causas; no ocultar pruebas omitidas. La omitida histórica weekly exige PUBLIC_BASE_URL real explícita y no acredita envío Kapso.

Antes de pytest: verificar URL resuelta solo a movement_test del contenedor nuevo, TEST_DATABASE_RESET=1, storage temporal, ausencia de claves reales y red sin egress. Usar compose.test.yml como referencia tras revisar su configuración; no asumir que un nombre de DB vuelve seguro un servidor productivo. Nunca ejecutar scripts históricos sin inspeccionar sus destinos/reset.

La suite existente no demuestra consentimiento nuevo, desactivación chat, cuotas chat, 402 específico, aislamiento coach acotado, restore EasyPanel ni exactitud video universal. Estos casos son requisitos de regresión pendientes. En hardware probar al menos Android Chrome e iPhone Safari disponibles: permisos, dictado, foto, teclado y reproducción, sin declarar hardware probado por viewport emulado.

## Salida

Cero fallos en casos de seguridad/integridad y rutas incluidas. Todos los P1 cerrados; P2 aceptados solo con mitigación probada. Para proveedores reales: corpus pequeño consentido, expected confirmado por atleta/coach y errores corregibles; cualquier atribución ajena, publicación sin consentimiento o pérdida bloquea release. QA y release owner firman evidencia del candidato exacto. Autorización de pruebas reales debe especificar proveedor, llamadas/mensajes máximos, destinatarios, ambiente, presupuesto y responsable; aprobación del plan no la sustituye.
