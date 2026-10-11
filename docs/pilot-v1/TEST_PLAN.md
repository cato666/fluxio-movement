# Resultados vigentes y pruebas pendientes

Estado vigente al 2026-10-11: **NO-GO**. S09 código `1d739a86e73d9d1cc5e0c89d80eb809c699f03be` y entrega `f7a70067fc812d4c1248f2c2ccf5eccd6fee777e` aprobados por pruebas locales; **S10 FAIL/BLOCKED** por tres defectos P1 reproducidos. S11–S18 no iniciadas. Esta adenda prevalece para el estado actual; el contenido anterior se conserva como propuesta/evidencia histórica, sin alterar el alcance aprobado.

| Ejecución | PASS | FAIL | ERROR | SKIPPED | Límite de la evidencia |
|---|---:|---:|---:|---:|---|
| S09 Python completa final | 769 | 0 | 0 | 0 | PostgreSQL temporal, proveedores simulados, XML 233,52 s |
| S09/S08 dirigidas finales | 66 | 0 | 0 | 0 | Subconjunto de la completa; no sumar |
| JavaScript completa S09 | 69 | 0 | 0 | 0 | API simulada; fuentes JS sin cambios posteriores |
| S10 reproducciones nuevas | 0 | 3 | 0 | 0 | Fuera de la suite anterior; fallos funcionales verificables; XML 1,37 s |
| S11–S18 propias | — | — | — | — | NOT RUN; no contar como aprobadas/omitidas por el runner |

S10 pendientes: promoción de reproducciones al candidato tras corrección; valores explícitos null/[], campos omitidos/foto/blocks/video_links, rollback/restart, concurrencia real, replay tras borrado, notas y ownership, doble confirmación WhatsApp/botón vencido y legacy. Suites completas obligatorias antes de cierre.

Evidencia local: C:/Users/desarrollo/AppData/Local/Temp/fluxio-s09-validation-20261011/ y fluxio-s10-validation-20261011/. Fuente probada coincide en 186 hashes; los tres probes S10 se ejecutaron solo en el runner y se conservaron fuera del producto. No se añadieron casos fallidos al candidato ni se ocultaron como SKIPPED.

1. **BLOCKED:** E2E integrado navegador/servidor S05, no ejecutado ni sustituido por mocks.
2. **PENDIENTE:** control de costos adicionales reales de video.
3. **PENDIENTE:** paridad de commit/digest/esquema/configuración/worker con EasyPanel.
4. **PENDIENTE:** validación de proveedores reales, sin autorización de gasto/envíos.
5. **PENDIENTE:** backup y restauración del destino; prueba temporal no los acredita.

Histórico original a continuación; no atribuir sus E2E a este candidato.

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
