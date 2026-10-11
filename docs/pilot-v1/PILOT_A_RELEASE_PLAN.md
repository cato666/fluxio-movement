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
