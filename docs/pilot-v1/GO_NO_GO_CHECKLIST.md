# S16 — Telegram reemplaza Resend

2026-10-11. Adaptador saliente Telegram preparado con reutilización de recibos/validación, timeout, rate limit persistente y callback seguro para backup. **31 tests simulados PASS + 16 regresiones PASS**. Sin Telegram real ni webhooks. Resend desactivado como canal; intento previo Resend HTTP 403 conservado como histórico, no repetir.

Config/instrucciones Chat ID y mensaje de prueba en [S16_TELEGRAM_ALERTS.md](S16_TELEGRAM_ALERTS.md). TELEGRAM_BOT_TOKEN/CHAT_ID privados; TELEGRAM_ALERTS_ENABLED=false. No stdout de tokens, direcciones de API o datos de chats. Monitores y scheduler no instalados; permisos y recuperación real pendientes.

**S16 BLOCKED / Pilot A NO-GO:** recepción real Telegram no autorizada/ejecutada, KeePassXC y backup representativo EasyPanel aún pendientes. No modificar CI, push, deploy, EasyPanel o workspace original. Riesgo de gates CI aceptado temporalmente, S15 pendiente; aprobación manual antes del push conserva pruebas del SHA definitivo.

---

## Histórico — prevalece Telegram como canal actual

# Procedimiento vigente — autorización manual antes del push

Fecha: 2026-10-11. Decisión explícita de Gastón: mantener .github/workflows/deploy.yml existente, sin modificar S15 ni agregar gates automáticos en esta etapa. **Ausencia de gates CI: riesgo aceptado temporalmente**, con control manual. S15 NO se considera completamente implementada. Esta aceptación no autoriza pruebas fallidas/bloqueadas, publicación o push por sí sola.

1. Codex prepara un commit candidato concreto y selección exacta de cambios, excluyendo secretos, herramientas locales y artefactos privados.
2. Antes de cada push ejecuta las pruebas obligatorias sobre ese commit y registra PASS/FAIL/SKIPPED/BLOCKED, entorno/evidencia, SHA completo y cambios incluidos. No sustituir evidencia del candidato por suites de otro SHA. Para commit exclusivamente documental, justificar pruebas funcionales no aplicables y realizar controles documentales; aceptación de excepciones corresponde a Gastón. Si se modifica el candidato después de validar, identificar nuevo SHA y revalidar lo afectado antes de solicitar push.
3. Informar resultados, riesgos y omisiones. Una prueba obligatoria FAIL/BLOCKED impide push salvo aceptación **expresa y específica** de Gastón. SKIPPED obligatorio no equivale a PASS y requiere revisión/aceptación. Aceptación temporal del riesgo CI no cubre estas excepciones.
4. Solicitar aprobación del push indicando repo/ref/SHA y efecto. Si ref es main, advertir que el workflow existente dispara deploy automático a EasyPanel. Gastón revisa y autoriza explícitamente. No inferir permiso de merge o de otros refs; no push/merge sin confirmación.
5. Tras autorización, GitHub Actions conserva el despliegue automático existente cuando corresponda. Codex no invoca directamente el webhook; Gastón administra EasyPanel y entrega evidencia de versión/API-worker, migraciones, configuración y smoke. Autorización de push no reemplaza permisos específicos de backup, migración, datos reales o gasto.
6. Registrar run/github.sha y commit/digests publicados; confirmar API y worker mismo SHA aprobado. Gastón aplica variables y opera backup previo y rollback con autorizaciones correspondientes. Mantener backup/restore operativo, privacidad, canales, video/costos, coaches y resto de gates obligatorios; NO-GO mientras falten.

Ya no exigir implementar un pipeline nuevo ni un gate automático como condición de esta etapa. Las exigencias históricas que contradicen esta decisión quedan sustituidas por este procedimiento manual. S15 permanece pendiente/parcial con riesgo aceptado, no PASS de implementación. Sin push, merge, cambios YAML ni deploy ahora. Continuar S16 localmente: custodia KeePassXC, alertas Resend y evidencias aportadas por Gastón.

---

## Histórico — prevalece la decisión manual vigente

# Go/No-Go — responsabilidades y gates vigentes

Fecha: 2026-10-11. GitHub origen de release; Actions mecanismo de deploy autorizado; Gastón aplica configuración y administra EasyPanel. Codex prepara/tests/manifiesto y sube solo refs aprobadas; no necesita SSH ni acceso directo al panel. **Pilot A NO-GO.**

- [ ] SHA GitHub definitivo aprobado; suites/checks obligatorios de ese SHA completos, evidencia y omisiones revisadas.
- [ ] Workflow con gate efectivo antes de POST y autorización de publicación: hoy push main -> POST sin pruebas; S15 pendiente. YAML no modificado.
- [ ] Gastón verifica/aplica variables de seguridad, presupuesto, storage, backup y alertas sin revelar valores.
- [ ] S16 operacional cerrado: claves KeePassXC/externo recuperables, entrega Resend real, collector/capacidad, backup representativo restaurado y automatización autorizada.
- [ ] Backup pre-release coherente identificado; rollback binario/config compatible ensayado y responsable confirmado.
- [ ] Autorización concreta para publicar SHA/ref y ventana; autorizar push main implica deploy automático. No autorización actual.
- [ ] Run Actions/github.sha y runtime API/worker mismo SHA aprobado, digests identificados, Alembic observado, smoke/persistencia destino PASS.
- [ ] Canales reales, costos/certificación video, coaches y resto de gates obligatorios cerrados antes de altas autorizadas.

E2E S05 integrado local histórico PASS conservado; no equivale a smoke destino. Ausencia de SSH para Codex no es bloqueo; ausencia de evidencia de Gastón sí. No borrar los pendientes previos. Plan detallado: PILOT_A_RELEASE_PLAN.md / DEPLOYMENT_RUNBOOK.md.

---

## Evidencia histórica — prevalece el modelo vigente

# S16 — decisiones confirmadas y acceso EasyPanel pendiente

Fecha: 2026-10-11. Base 7598e38. Custodia elegida KeePassXC Windows + copia externa cifrada; runtime secrets pendiente. Resend preferido, destinatario/remitente/dominio/API key privados pendientes. Ninguna clave generada/reemplazada y ningún correo enviado.

**S16 BLOCKED / Pilot A NO-GO.** Lectura EasyPanel autorizada, pero no sesión administrativa/SSH ni URL de panel disponibles. Host documentado responde GET /health 200 con TLS validado; no informa versión ni certifica DB/worker/volúmenes. Inspección parcial en [S16_EASYPANEL_INSPECTION.md](S16_EASYPANEL_INSPECTION.md).

No existe envío API/SMTP actual: solo callback notify_operator y plantilla. Config Resend API propuesta, no implementada/activa. Procedimientos, prueba de un correo, recuperación KeePassXC y backup/restore representativo con autorizaciones separadas en [S16_CUSTODY_RESEND_VALIDATION_PLAN.md](S16_CUSTODY_RESEND_VALIDATION_PLAN.md). Diario no listo para activar por falta de adaptador, claves runtime, capacidad y alertas reales.

Verificaciones de esta etapa: Git/base, búsqueda de mecanismos, presencia de variables sin valores, inventario de sesión disponible, dos lecturas públicas (HEAD / 405 y GET /health 200), consulta de documentación oficial Resend/KeePassXC y validación JSON/gates. No repetir suites sintéticas previas ni registrar como PASS custodia/envíos/restore real no ejecutados. Nuevos deliverables documentales y plantillas inertes solamente. Original leído, sin escrituras; sin nuevos objetos R2, OpenAI/Kapso, cron, migraciones, deploy ni infraestructura modificada.

Próximo paso requiere URL/sesión del panel, referencias KDBX/dispositivo y configuración privada Resend. Leer el reporte antes de autorizar cualquier operación externa de escritura.

---

## Evidencia histórica

# Actualización S16 — 2026-10-11

Privacidad del bucket y token writer exclusivo/Active confirmados por el propietario en Cloudflare; token actualizado validado con dos lecturas HTTP 200, sin objetos ni escrituras. Confirmación del propietario y comprobación técnica tienen alcance distinto. Ver S16_UPDATED_TOKEN_READ_EVIDENCE.json.

**S16 BLOCKED / NO-GO:** falta lector de restore/separación de medios, bóveda independiente y recuperación real de claves, correo configurado/autorizado/recibido, adaptador EasyPanel coherente/capacidad, backup y restore representativo autorizados. Daily/pre-release están preparados pero no listos para activar; ejecución y scheduler permanecen deshabilitados. No repetir ensayos locales ya PASS.

Contrato de correo inerte: BACKUP_EMAIL_CONFIGURATION.example.json. Decisiones y autorizaciones precisas en [reporte S16](S16_IMPLEMENTATION_REPORT.md): primero bóveda y datos SMTP/destinatario, luego acceso EasyPanel de lectura; backup/pausa/restore y activación requieren autorizaciones separadas sobre planes concretos.

---

## Estado histórico conservado

# S16 — actualización operativa 2026-10-11

**S16 BLOCKED / Pilot A NO-GO.** Preparación local y restore sintético PASS no cierran gate operacional. Evidencia: [reporte S16](S16_IMPLEMENTATION_REPORT.md), [JSON](S16_OPERATIONAL_EVIDENCE.json).

- [x] Gastón confirmado; retención manual de objetos sintéticos durante piloto aprobada.
- [x] Helper AES-256-GCM compatible, integridad y recibos/lock, health missing/stale/incomplete, plan siete daily + pre-release sin borrado. Config y cron inertes.
- [x] 28 tests Linux PASS; restore local con 29 tablas, PNG/MP4 y referencias PASS; contenedores propios detenidos. Receptor de alerta solo simulado.
- [ ] R2 r2.dev/custom domains/Workers públicos deshabilitados, alcance exclusivo y separación de credenciales de medios comprobados.
- [ ] Custodia independiente seleccionada, claves/versiones recuperables por Gastón desde fuera de EasyPanel.
- [ ] Canal de alertas elegido y autorizado; entrega real comprobada; horario/fechas y suplencia definidos.
- [ ] Adaptador de recolección coherente/transport/key-store/alerts aprobado, capacidad del conjunto real validada, automatización instalada bajo autorización.
- [ ] Autorización específica e inventario EasyPanel; respaldo real completo y restore representativo aislado aceptado, RTO/RPO reales medidos.

E2E S05 integrado local histórico PASS conservado; siguen pendientes paridad/destino, canales reales completos, video/costos, coaches, alertas/CI/artefacto/rollback. S11 sin limpieza efectiva. No GO ni nueva fase.

---

## Estados históricos conservados

## Actualización S16 — 2026-10-11

Gastón confirmado como operador. Ensayo R2 sintético **PASS**: AES-256-GCM cliente, upload/download autenticados, DB nueva y cuatro archivos restaurados con hashes/referencias iguales; 3 usuarios, 1 sesión/foto/análisis/review, head 0024. Contenedores propios detenidos. 5,31 s y 92.197 bytes corresponden a muestra pequeña, no RTO operativo. Primer intento falló por expectativa HTTP anónima (400); corrección del harness y repetición aislada documentadas. Privacidad por dominios/r2.dev, configuración de cifrado proveedor, permisos separados, custodia definitiva, restore representativo del producto, scheduler y alertas **pendientes**. S16 sigue parcial y **NO-GO**, sin habilitar limpieza S11. Ver [reporte S16](S16_IMPLEMENTATION_REPORT.md).

# Estado vigente — cierre final Pilot A

Validación local final del candidato `03cfd4387a75f70fae60ccd2108a83d24dc57f31`: Python **820 PASS, 1 SKIPPED, 0 FAIL** (257,41 s); JavaScript **77 PASS, 0 FAIL/SKIPPED**. La prueba omitida requiere WEEKLY_RELEASE_PUBLIC_BASE_URL real y queda **NOT RUN**, sin afirmar paridad de dominio. PostgreSQL nuevo tmpfs, red interna nueva, sin puertos Docker publicados ni credenciales de proveedores; migraciones desde cero y worker vacío PASS; contenedores propios detenidos. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-2e4m_dlq/offline-tests.log` y `environment.json`. Tres advertencias de deprecación no bloquean estas pruebas. Workspace original: 153 rutas verificadas sin cambios.

Fecha: 2026-10-11, America/Santiago. Rama: codex/pilot-v1-stabilization. Candidato auditado: `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. **Pilot A NO-GO**. Alcance obligatorio: bitácora + WhatsApp + video certificado + coach titular/suplente, 3–5 atletas, 30 días. Esta entrega no autoriza proveedores, infraestructura persistente ni publicación.

Estados: PASS = evidencia ejecutada y limitada a su entorno; FAIL = defecto/evaluación fallida demostrada; BLOCKED = falta autorización, acceso, responsable o dependencia; NOT RUN = sin ejecución. Resultados históricos no certifican el candidato final ni el destino.

## Gates vigentes de Pilot A

- [x] S01–S10 y S17 implementados y validados localmente en cierres históricos.
- [x] E2E integrado S05 histórico: nueve casos + tres guards PASS; conservar evidencia, sin certificar cambios posteriores/destino.
- [ ] Seguridad/aislamiento y consentimiento comprobados en artefacto final y destino.
- [ ] S16: backup R2 y restore DB/storage/claves verificables.
- [ ] Texto, fotografía y audio web/WhatsApp reales aprobados, presupuesto conciliado.
- [ ] Video certificado por ejercicio/vista y costos adicionales medidos/controlados.
- [ ] Coach titular y suplente disponibles y flujo completo certificado.
- [ ] Alertas efectivamente recibidas, disco/storage y heartbeat verificados.
- [ ] Imagen final escaneada, API/worker mismo digest/head/config.
- [ ] Gate CI y aprobación manual antes de POST EasyPanel.
- [ ] EasyPanel versión/configuración/HTTPS/proxy/volúmenes identificados.
- [ ] Rollback y restauración ensayados en aislado.
- [ ] Suites finales del artefacto y smoke destino PASS.
- [ ] Autorizaciones de publicación y alta de tres atletas.

NO-GO. Una suite local aprobada no cierra gates externos.

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

# Decisión vigente — NO-GO por S11 y gates de release

Fecha: 2026-10-11. **S10 cierre técnico local PASS; S11 auditada/BLOCKED por política de retención y dependencia S16. S12–S18 no iniciadas. Pilot NO-GO.** Código actual `09b4215f5b1aec1e44e77f67e42360ecedfd373c`, entrega S10 `023736b6429524f5d5cecbc2c8febe738157a9e1`. Los tres defectos P1 de S10 fueron corregidos y sus reproducciones ahora pasan; la parada anterior S10 fue superada mediante autorización expresa del usuario. El commit documental actual no implementa S11.

- [x] Rama/worktree independiente y S08 verificados antes de continuar.
- [x] S09 implementada, pruebas ejecutables PASS y commits limpios.
- [x] S10-D01: campos omitidos preservados; reproducción PASS.
- [x] S10-D02: notas visibles consistentes; reproducción PASS.
- [x] S10-D03: guardado keyed una vez; replay/concurrencia/reinicio/delete PASS.
- [x] S10 suites finales: 787 Python y 72 JS PASS; commit independiente y worktree limpio antes del análisis S11.
- [ ] S11 política de retención aprobada y dependencia S16 resuelta; **BLOCKED**.
- [ ] S11 limpieza segura/refs/legacy/fallos implementada y probada; actualmente sin código.
- [ ] S12–S18 implementadas y validadas; **NOT STARTED**.
- [ ] E2E integrado S05: **BLOCKED**.
- [ ] Control real de costos adicionales de video: **PENDIENTE**.
- [ ] Paridad EasyPanel, incluido head 0024: **PENDIENTE**.
- [ ] Proveedores reales: **PENDIENTE**, sin autorización de consumo.
- [ ] Backup/restore del destino y rollback compatible con 0024: **PENDIENTE**.
- [ ] Responsables, alertas entregadas y clips/coach/capacidad certificados.

[Propuesta S11/S16 para aprobación](S11_RETENTION_POLICY_PROPOSAL.md) · [Consolidado parcial](FINAL_STABILIZATION_REPORT.md). Ningún PASS local cierra un gate real ni autoriza deploy.

Checklist histórico a continuación; gates pendientes siguen abiertos.

---

# Go / No-Go — Pilot v1.0

Estado al 2026-10-11: **NO-GO**. S01–S07 aprobadas técnicamente (S05 conserva aprobación condicionada); S08 validada localmente y pendiente de revisión; 749 pruebas Python y 69 JavaScript aprobadas. Release y destino aún sin certificar. Cada casilla exige evidencia fechada del candidato/destino y firma del responsable; desconocido equivale a pendiente. No usar resultados 09-10 para marcar candidato futuro PASS.

## Aprobación del plan

- [ ] Usuario revisó alcance, backlog S01–S18, TEST_PLAN, runbook y operación.
- [ ] Responsables nominales, horario de soporte y coaches titular/suplente definidos.
- [ ] Políticas coach/atleta, cuenta desactivada, enlaces vivos/consentimiento y retención aprobadas.
- [ ] Límites numéricos y presupuesto monetario por día/30 días definidos.
- [ ] Se autoriza una fase posterior de correcciones pequeñas; ninguna funcionalidad nueva.

Esta aprobación no autoriza llamadas OpenAI, mensajes Kapso, operaciones destructivas, altas reales, migraciones persistentes ni deploy. Solicitar permisos específicos sobre resultados concretos cuando corresponda.

## Pendiente heredado S05

- [ ] **BLOCKED**: E2E integrado navegador/servidor HTTP real. Las pruebas de interfaz simulada y HTTP dentro del contenedor pasaron separadamente; no sustituyen este gate. No ampliar redes Docker para resolverlo sin autorización.

## Otros pendientes heredados de S06

- [ ] **PENDIENTE**: reserva y control verificables de costos adicionales del procesamiento de video (cómputo, almacenamiento y otras operaciones facturables). La configuración/fail-closed simulados no certifican el costo real ni autorizan proveedores.
- [ ] **PENDIENTE**: paridad con EasyPanel y validaciones reales del candidato, incluyendo dominio HTTPS, Origin, proxy confiable, digest, esquema, app y worker. No ejecutadas; no marcar PASS sin evidencia del destino y autorización.

## Gate de candidato — QA + seguridad + release owner

- [ ] S01: cambios locales seleccionados sin herramientas/artefactos ajenos, commit limpio y manifiesto.
- [ ] S02–04,07: cuentas inactivas bloqueadas web/chat/colas; coaches aislados; seed/secretos/cookies/login/origen seguros.
- [ ] S05: Guardar nunca crea share; opt-in previo verificable; lector/fotos revocados o vencidos bloqueados y política de desactivación probada.
- [ ] S06,08,09: límites efectivos web/chat concurrentes, audio dos etapas, replay idempotente; 402/429/UNCERTAIN y recuperación comprobados, sin retries ciegos.
- [ ] S10,11,17: CRUD/notas/legacy íntegros, fotos/retención y listado sin pérdida oculta dentro del contrato.
- [ ] S12,18: ejercicios/vistas explícitos validados con clips reales y coach; restart/FAILED/reanalyze comprobados; coach disponible y acceso acotado.
- [ ] S13: alertas operativas probadas, heartbeat y cola/costos/disco/backup visibles sin PII.
- [ ] S14,15: app/worker mismo digest, esquema/modelo/assets fijados y scan revisado; tests bloquean deploy no aprobado.
- [ ] S16: DB/storage/claves restaurados en aislado, compatibilidad rollback probada; RPO/RTO aprobados y medidos.
- [ ] Tests específicos y suite completa + JS/E2E del candidato: cero fallos críticos; skipped explicados; T01–T16 con evidencia.
- [ ] Cero P0/P1 abiertos. P2 solo con mitigación probada, dueño/plazo y aceptación expresa; pérdida/exposición no se acepta como P2.

## Gate de validación real y publicación

- [ ] Autorización de pruebas reales: ambientes, proveedor, destinatarios/medios consentidos, máximo de llamadas/mensajes y costo.
- [ ] Foto/audio/texto/video y WhatsApp reales actuales validados dentro del alcance; evidencia histórica/fixtures no sustituyen este gate.
- [ ] Comparación EasyPanel actual: commit/digest app-worker, OpenAPI, revisión SQL, TLS/proxy, DB/storage/keys y worker efectivo; DNS/reachability verificados desde destino/cliente.
- [ ] Backup pre-release verificado y restaurable, plan de migración incremental desde revisión real y ventana sin escrituras.
- [ ] Usuario autorizó específicamente deploy y migración persistente de commit/digest/revisión/destino indicados; rollback listo.
- [ ] Usuario autorizó altas de atletas y las operaciones reales/destructivas o facturables del smoke que correspondan.
- [ ] Deploy autorizado y smoke posterior del destino exacto aprobado; datos QA aislados y links QA revocados; no reset/truncate de producto.

## Gate de activación

- [ ] Cohorte inicial de 3 con consentimiento y soporte; presupuesto/cupos/coach confirmados.
- [ ] 72 h estables, al menos un registro completado por atleta, cero duplicados/pérdidas/incidentes de privacidad y cero P0/P1.
- [ ] Backup <24 h, cola saludable, alertas recibidas, gasto bajo límite y reviews dentro de capacidad.
- [ ] Release owner/QA/operador aprueban ampliar primero a 10 y después hasta 15; cualquier fallo suspende ampliación.
- [ ] Fecha día 1/día 30 y evaluación semanal registradas; cierre no implica pago ni expansión funcional.

## Registro de decisión

| Campo | Valor actual |
| --- | --- |
| Decisión | NO-GO; E2E integrado S05 BLOCKED y gates de release pendientes |
| Candidato / digest | Rama codex/pilot-v1-stabilization; código S08 dfe2f870ba6e2aad277de478838cbea78d95fc3d / digest no construido |
| SQL destino / head candidato | Destino desconocido / candidato 0023_consumption_reservations; migración persistente no autorizada |
| QA / seguridad / operador / coach / release owner | Por asignar |
| Evidencia / excepciones P2 | Baseline histórica documentada; sin excepciones aprobadas |
| Permisos de pruebas reales / deploy / migración / altas | No otorgados en esta etapa |
| Próximo paso | Revisión final S08 ([reporte](S08_IMPLEMENTATION_REPORT.md)); conservar los tres pendientes heredados; S09 no iniciada, sin deploy ni gasto |

Una firma Go debe enlazar resultados actuales y autorización final. Si falta un gate obligatorio, registrar No-Go y tarea concreta; no declarar listo por health ready ni por cobertura histórica.

