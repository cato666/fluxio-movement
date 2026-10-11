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

# Modelo vigente de release — GitHub Actions / EasyPanel administrado por Gastón

Fecha: 2026-10-11, America/Santiago. Base documental `df4f3ce3a5b9b194116f4363cd76d72e5c441fdb`, rama codex/pilot-v1-stabilization. Esta sección sustituye las instrucciones históricas de acceso/operación directa por Codex. **Pilot A NO-GO; S16 BLOCKED.** No push, merge, webhook, deploy, migración persistente ni envío externo autorizado en esta etapa.

## Responsabilidades y autoridad

| Actividad | Codex | Gastón / GitHub Actions |
|---|---|---|
| Desarrollo/pruebas/documentación | Implementa incrementos aprobados en worktree; prepara candidato y evidencia. | Gastón revisa y aprueba cada etapa. |
| GitHub como origen de release | Prepara commit/branch/manifiesto. Solo sube refs explícitamente autorizadas. | Gastón autoriza ref/SHA y publicación. Subir rama de revisión no autoriza main ni release. |
| Despliegue | No administra EasyPanel ni necesita SSH. No llama al webhook directamente. | Workflow existente de GitHub Actions dispara EasyPanel bajo autorización de Gastón. |
| Variables, servicios y volúmenes | Prepara inventario, requisitos y checklist sin valores secretos. | Gastón aplica configuración y entrega evidencia redactada. Ninguna modificación de infraestructura implícita. |
| Backups/restore y rollback | Prepara/verifica procedimientos y pruebas locales aisladas autorizadas. | Gastón ejecuta operación real autorizada y entrega resultados; Actions solo orquesta lo previamente aprobado. |
| Paridad y smoke | Compara evidencia fuente/artefacto/pruebas y señala faltantes. | Gastón confirma SHA/digest real de API/worker, revisión DB, configuración y smoke del destino. |

## Secuencia de release autorizada futura

1. Congelar un SHA completo del candidato GitHub y revisar alcance, migraciones/compatibilidad, secretos excluidos y diff. Evidencias antiguas no certifican un SHA nuevo. Registrar commit de pruebas, fecha/comandos/resultados y todas las omisiones justificadas.
2. Verificar suites obligatorias del candidato: Python con PostgreSQL desechable, JavaScript, E2E privacidad/seguridad/canales y regresiones pertinentes; distinguir pruebas locales simuladas de reales autorizadas. Checks fallidos, ausentes o pendientes obligatorios bloquean publicación.
3. Gastón revisa variables y configuración a aplicar: APP_ENV producción, SESSION_SECRET, demo seed deshabilitado, orígenes HTTPS y proxies confiables, DATABASE_URL/STORAGE_PATH privados, firmas/claves WhatsApp y weekly sharing compatibles API/worker, cuotas/reservas y costos video, R2, claves backup por secret store y Resend. Confirmar nombres exactos contra candidato; reportar solo presencia/validación y referencias privadas. Codex no aplica cambios.
4. Completar S16: custodia KeePassXC + copia externa cifrada recuperable, canal Resend real probado, adaptador/capacidad/coherencia y respaldo representativo restaurado. Antes de cada release, Gastón coordina pausa de escritores y backup coherente DB + todos los medios + versiones de claves/config; conserva copia previa con hashes y evidencia. Backup sintético o upload sin restore no cierra este gate. Migraciones persistentes requieren autorización específica y procedimiento de una sola ejecución, no arranque accidental.
5. Preparar manifiesto anterior y rollback probado. Gastón autoriza expresamente publicación de SHA/ref concreto y ventana. **El workflow actual se activa por push a main**: la autorización de ese push tiene consecuencia de deploy inmediato y debe explicitarla. No push/merge a main mientras falten gates; ningún disparo manual del webhook por Codex.
6. GitHub Actions es el único disparador previsto. Registrar URL/run ID, evento, github.sha, ref, checks y resultado de trigger; éxito del POST no equivale a deploy terminado. Gastón confirma que EasyPanel tomó ese SHA y que main no cambió durante la selección/build. Release serializada, sin carreras entre publicaciones; no inferir SHA del runtime por el último commit local.
7. Gastón registra SHA completo y digest de API y worker. Ambos ejecutan **la misma versión fuente aprobada** y dependencias/config compatibles. Si comparten imagen, registrar el mismo digest probado; imágenes distintas solo si aprobadas y trazadas al mismo SHA. Confirmar alembic_version real y smoke/health/heartbeat/privacidad/persistencia. Evidencia sin secretos. Diferencia de SHA, fallo de smoke o ausencia de identidad verificable bloquea GO.
8. Revisar gates finales y autorización de altas separada. Continuar con tres atletas solo tras GO explícito; no se autoriza crear cuentas reales por aprobar este modelo.

## Riesgo del workflow existente — pendiente real

Inspección .github/workflows/deploy.yml: push main -> un job que POSTea secrets.EASYPANEL_DEPLOY_URL. **No ejecuta pruebas ni fija/verifica SHA de artefactos ni exige aprobación protegida dentro del workflow.** En esta etapa no se modifica el YAML. El cambio de responsabilidades no subsana S15. Antes de publicar, preparar bajo tarea aprobada checks/gate del mismo SHA y un control de autorización efectivo (protección de main/environment según esquema que Gastón apruebe). Probar localmente que fallos no permiten trigger; no invocar EasyPanel como test. Mientras tanto main no se toca y los controles faltantes permanecen BLOCKED.

## Respaldo previo y rollback por el administrador

Gastón conserva set pre-release identificado, revisión DB y manifiesto anterior API/worker/config/claves. Primer recurso: volver a versión binaria anterior compatible, mediante GitHub Actions y configuración controlada por Gastón, con autorización explícita; registrar commit de rollback o artefacto fijado, ejecución y resultado. No force-push ni downgrade automático. Si se usa git revert, se prepara/revisa en rama y su publicación requiere permiso porque vuelve a disparar deploy. No suponer que revert elimina migraciones aplicadas.

Si binario anterior no es compatible, mantener mantenimiento y preparar corrección o restauración coherente **a nueva instancia aislada**; medir pérdida potencial desde snapshot, reconciliar escrituras y pedir permiso de cutover. Nunca restaurar encima de producción ni mezclar DB vieja con storage/claves nuevos. No borrar volúmenes/objetos como rollback. Gastón ejecuta cambios de infraestructura, Codex prepara y valida evidencia.

## Trabajo actual y evidencias necesarias

Continuar únicamente pruebas locales, custodia KeePassXC y alertas Resend. No se requiere SSH ni sesión administrativa para Codex: Gastón proporcionará inventario redactado de servicios, volumes/storage, TLS/proxy, presencia de variables, revisión migraciones y SHA/digest API/worker. Ya no tratar acceso directo de Codex a EasyPanel como requisito de GO; **sí** exigir evidencia verificable del destino.

Bloqueos conservados: S16 operacional; paridad EasyPanel y evidencia de deploy; checks/gates S15; canales reales completos; costos/certificación video y coaches; alertas reales y rollback. E2E S05 integrado local histórico PASS se conserva, sin convertirlo en smoke del destino. No repetir suites por este cambio documental ni marcar como ejecutada ninguna prueba real pendiente.

---

## Evidencia y planes históricos — prevalece el modelo vigente anterior

# Pilot A — plan de release

Validación local final del candidato `03cfd4387a75f70fae60ccd2108a83d24dc57f31`: Python **820 PASS, 1 SKIPPED, 0 FAIL** (257,41 s); JavaScript **77 PASS, 0 FAIL/SKIPPED**. La prueba omitida requiere WEEKLY_RELEASE_PUBLIC_BASE_URL real y queda **NOT RUN**, sin afirmar paridad de dominio. PostgreSQL nuevo tmpfs, red interna nueva, sin puertos Docker publicados ni credenciales de proveedores; migraciones desde cero y worker vacío PASS; contenedores propios detenidos. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-2e4m_dlq/offline-tests.log` y `environment.json`. Tres advertencias de deprecación no bloquean estas pruebas. Workspace original: 153 rutas verificadas sin cambios.

Fecha: 2026-10-11, America/Santiago. Rama: codex/pilot-v1-stabilization. Candidato auditado: `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. **Pilot A NO-GO**. Alcance obligatorio: bitácora + WhatsApp + video certificado + coach titular/suplente, 3–5 atletas, 30 días. Esta entrega no autoriza proveedores, infraestructura persistente ni publicación.

Estados: PASS = evidencia ejecutada y limitada a su entorno; FAIL = defecto/evaluación fallida demostrada; BLOCKED = falta autorización, acceso, responsable o dependencia; NOT RUN = sin ejecución. Resultados históricos no certifican el candidato final ni el destino.

## Artefacto y predeploy

Congelar candidato fuente, conservar worktree original, excluir herramientas QA no rastreadas, .impeccable, logs, temporales, secretos y clips privados. Revisar diffs desde S17: consentimiento cifrado, CSP script self para modal público, iconos/manifest y UI. No confundir pruebas dirigidas posteriores con suite completa del artefacto.

Build local reproducible con dependencias/modelos/perfiles fijados; registrar digest, SBOM/scan y excepciones aplicables. API y worker deben usar el mismo digest, head 0024_training_save_requests y configuración equivalente. Compatibilidad de claves WhatsApp y WEEKLY_SHARE_ENCRYPTION_* en ambos procesos; guardar versiones antiguas para enlaces vigentes. Sin clave de enlaces, creación falla con 503.

S15: .github/workflows/deploy.yml actual publica por push main sin gates. Antes de cualquier push/merge, corregir gate por checks del commit y aprobación manual protegida; probar fallo de checks sin POST. Esta etapa no modifica/dispara workflow ni hace push.

## EasyPanel y respaldo

Acceso read-only explícitamente autorizado: registrar commit/digest/API/worker, revisión SQL, volúmenes y rutas privadas, TLS, hostname/orígenes permitidos, proxies confiables, SESSION_SECRET seguro, demo seed deshabilitado, firmas Kapso, claves de cifrado y USAGE_* válidos. No imprimir valores.

B01/B02: R2 privado independiente, backup DB/storage/claves consistente con escritores pausados en ventana aprobada. Validar restauración aislada y conservación de reviews/medios. No ejecutar Alembic ni pg_dump en producto por autorización implícita. Solicitar operación concreta y origen/destino después de preparar runbook revisable.

## Publicación futura autorizada

Solo con autorización explícita: backup pre-release, mantenimiento/pausa writers, aplicar migraciones revisadas, desplegar digest fijado API/worker y ejecutar smoke. No ordenar borrar volúmenes, downgrade SQL ni rollback destructivo.

Smoke destino: login/cookies/Origin, manual CRUD, upload privado, resumen/share/consent/revoke/foto, WhatsApp real autorizado dentro del saldo, video combinación certificada con coach, health/heartbeat/alertas, persistencia tras reinicio autorizado. Una prueba que necesita proveedor requiere autorización de gasto independiente.

## Rollback y activación

Registrar digest anterior compatible y DB head antes/después. Ensayar binario anterior contra schema aditivo en copia aislada; si incompatibilidad, restauración coordinada DB+storage+claves con aprobación específica, documentando pérdida posible según RPO. No revertir solo DB dejando archivos inconsistentes. Evidencia de ensayo obligatorio, no prometer tiempo sin medición.

Tras smoke destino, reunión Go/No-Go: doce condiciones completas. Autorizar tres cuentas de atletas explícitamente, alta asistida, consentimiento/uso/cupos y coach titular/suplente; observar antes de aumentar a cinco. Fallo de privacidad, pérdida de datos, saldo incierto o backup inválido detiene nuevas altas y operaciones afectadas. No ampliar a 10–15 en Pilot A sin decisión posterior.

## Autorizaciones pendientes

R2 inspección/backup/restore y responsables; credenciales/acceso EasyPanel/GitHub; teléfono/clips/cuentas sintéticas y gasto proveedores; parámetros de costo y criterios coach; operador/canal alertas; operación persistente concreta; deploy y altas reales. Ninguna está implícita en el cierre documental.
