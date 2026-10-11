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

