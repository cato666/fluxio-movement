# S11 — Privacidad y ciclo de vida de fotografías: auditoría y bloqueo

Fecha: 2026-10-11. Base de análisis: código S10 09b4215f5b1aec1e44e77f67e42360ecedfd373c, entrega 023736b6429524f5d5cecbc2c8febe738157a9e1, worktree limpio antes de comenzar. **AUDITADA / BLOCKED: política de retención y dependencia S16 no aprobadas/resueltas.** Sin implementación funcional S11.

## Componentes revisados en lectura

app/services/training_media.py; training_service.py; weekly_summary.py; app/weekly.py; app/whatsapp/media.py, worker.py, capture.py y models.py; TrainingImage/TrainingSession/WeeklyShare; docs/pilot-v1/DEPLOYMENT_RUNBOOK.md/PILOT_OPERATIONS.md y auditoría de producto.

| Área | Comportamiento observado / límite |
|---|---|
| Web | Guarda TrainingImage y archivo privado; no hay TTL global/inventario de huérfanos para uploads web. Deleting sesión conserva fila/archivo; prueba S10 PASS, no política integral S11. |
| WhatsApp | Media sin guardar nace con expires_at +24 h. Guardar vincula training_session_id y deja expiración nula. Delete SET NULL; cleanup asigna +24 h a medio desvinculado sin expiración. |
| Referencias compartidas | Cleanup de imagen verifica TrainingSession.source_image_id y conserva si otra sesión la utiliza. No basta para probar todas las referencias de contexto/legacy. |
| Contexto activo | ConversationState actualiza expiración a +24 h en cada transición; expires_at del medio puede conservar fecha anterior. Cleanup no verifica explícitamente payload del contexto vigente antes de eliminar ese medio. Riesgo pendiente de reproducción y protección, no se declara pérdida real confirmada. |
| Falla de cleanup | target.unlink precede al commit de borrado en DB. Si el commit falla, hay riesgo de fila/archivo divergentes. Lectura de código, no ensayo ejecutado ni afirmación de daño real. |
| Shares | HTML y foto validan cuenta activa, consentimiento, revocación y expiración; foto debe seguir referenciada por una sesión de esa semana. Revocar/expirar un share no autoriza borrar una foto vigente. Controles S05 cubiertos por suite S10; no E2E integrado. |
| Worker detenido | La limpieza depende de run_once; detener worker impide progreso de retención. S13 observabilidad sigue sin implementar. |
| Legacy/inactividad | No hay una decisión aprobada para eliminación/exportación de fotos legacy o de cuentas desactivadas; proteger lectura no equivale a permiso de borrar. |

## Parada y propuesta revisable

El encargo exige detenerse cuando falte una decisión de privacidad y antes de implementar borrado efectivo sin política del propietario. S11 depende de S16, cuyo destino/retención/RPO/RTO y restore no están aprobados/verificados. Se detuvo tras la lectura: ningún cleanup nuevo, unlink, cuarentena, migración o cambio de TTL ejecutado.

[S11_RETENTION_POLICY_PROPOSAL.md](S11_RETENTION_POLICY_PROPOSAL.md) propone protección de referencias, 24 h desde detección verificable de orfandad, cuarentena reversible de 7 días, preservación legacy, modo dry-run inicial, backups 7 diarios + snapshot pre-release durante 30 días y objetivos RPO 24 h/RTO 4 h. **Nada aprobado o activo**; requiere decisión del propietario y dependencia de respaldo antes de modo efectivo.

## Resultados y estado

Pruebas propias S11: **NOT RUN**, no PASS; solo auditoría de fuentes. No se ejecutó cleanup contra datos reales ni sintéticos en esta fase. Suite completa S10: 787 Python/72 JS PASS; contiene regresiones de privacidad previas, no certifica la implementación S11 inexistente. Commit de implementación S11: ninguno. Commit documental: identificar por git log del reporte.

Cinco gates conservados: E2E S05 BLOCKED; costos adicionales reales de video; paridad EasyPanel; proveedores reales; backup/restore del destino. S12–S18 no iniciadas. Pilot **NO-GO**.

Próximo paso: aprobación o ajuste de la propuesta de política; luego preparar dependencias/test de restore aislado y corrección mínima segura S11. No presentar estas decisiones como aprobación de borrado en el producto.
