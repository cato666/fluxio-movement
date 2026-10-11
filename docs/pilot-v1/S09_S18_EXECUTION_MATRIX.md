# Matriz de ejecución controlada S09–S18

Fecha: 2026-10-11. Base verificada: f1a8bf47c92dbdb7079470a2f42b0d92f2d18e55, rama codex/pilot-v1-stabilization, worktree independiente limpio. S08 implementada (dfe2f870ba6e2aad277de478838cbea78d95fc3d), reporte presente y XML: 749 Python / 46 dirigidas / 69 JS PASS, cero fallos/omisiones. Esta verificación cumple la condición previa del nuevo encargo; no aprueba publicación ni proveedores.

| Fase | Dependencias del backlog | Ejecución y gate |
|---|---|---|
| S09 | S06 | Ejecutable local: preflight, release probado/idempotente, audio por etapas; preservar UNCERTAIN y cuotas. Primero pruebas dirigidas, luego regresiones y cierre con commit limpio. |
| S10 | S01, S05 | Después de S09: reproducir defectos antes de corregir; integridad/ownership y contratos legacy. E2E integrado S05 sigue abierto como gate transversal de release. |
| S11 | S05, S16 | No autoriza borrado efectivo sin política de retención del propietario y evidencia de respaldo/restauración. S16 depende de S14; preparar documentación/pruebas de dependencia si está autorizado, sin darla por cerrada. Detenerse si falta política o restore obligatorio. |
| S12 | S09, S16 | Recuperación asistida BackgroundTasks; cierre depende de conservación/restore verificados. No broker. |
| S13 | S08, S12 | Heartbeat y eventos simulados; requiere responsable nominal y canal autorizado con recepción verificable. Logs solos no cierran aceptación. |
| S14 | S01 | Identidad/checksums/build y scan local; digest definitivo o bloqueo explícito. Sin publicación de imagen. |
| S15 | S14 | CI con DB desechable, gates y aprobación; protección del entorno de producción debe verificarse, no basta YAML. No workflow real/deploy. |
| S16 | S01, S14 | Restore solo desechable; política de backups y objetivos RPO 24 h/RTO 4 h son propuestas sin aprobación localizada. No restore/downgrade del producto. |
| S17 | Límites | 199/200/201, corrección compatible o mitigación explícita; nunca borrar para liberar historial. |
| S18 | S03, S12 | Clips autorizados y validación de coach/capacidad; combinaciones sin evidencia humana permanecen pendientes e inhabilitadas para piloto. |

Orden de ejecución autorizado: S09→S10→S11→S12→S13→S14→S15→S16→S17→S18. Las dependencias adelantadas S16/S14 no se ignoran: se preparan únicamente documentación/pruebas cuando permita cerrar la fase, o se detiene ante bloqueo. No se implementan fases posteriores solo para aparentar cierre secuencial.

## Pendientes transversales conservados

1. **BLOCKED:** E2E integrado navegador/servidor S05; UI simulada y TestClient separados no lo sustituyen. No ampliar redes existentes ni publicar puertos.
2. **PENDIENTE:** reserva/control verificables de costos adicionales reales de video.
3. **PENDIENTE:** paridad commit/digest/esquema/configuración/worker EasyPanel.
4. **PENDIENTE:** calidad/contratos de proveedores reales; sin autorización de gasto/envíos.
5. **PENDIENTE:** backup y restauración del destino; ensayo local no los certifica.

## Discrepancias históricas

PILOT_SCOPE, RELEASE_READINESS, TEST_PLAN, PILOT_OPERATIONS y el encabezado de STABILIZATION_BACKLOG conservan la propuesta del 10-10 y cifras/defectos anteriores a S01–S08. Se usan como contrato e historia, no como estado actual. Los informes y código actual prevalecen. S01 conserva una adenda posterior que reemplaza su bloqueo Docker. Un informe histórico presenta mezcla UTF-8/cp1252; fue leído con fallback, sin modificarlo. El límite monetario fue autorizado posteriormente (US$3 diario, US$30/30 días), y ya se implementó S06; el texto histórico de importe pendiente no revoca esa autorización ni autoriza gastar.

Estado de release: **NO-GO**. Restricciones: original intacto, no datos/volúmenes persistentes, proveedores reales, altas reales, push/merge/deploy ni webhook EasyPanel. Cada fase registra commit, evidencia, PASS/FAIL/SKIPPED/BLOCKED y worktree limpio antes de avanzar. Una decisión de privacidad pendiente detiene el flujo.
