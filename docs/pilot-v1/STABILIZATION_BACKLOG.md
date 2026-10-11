# Actualización Pilot A — política de respaldo aprobada, ejecución deshabilitada

El propietario aprueba objetivo privado S3 compatible/Azure Blob independiente del VPS, AES-256/TLS, PostgreSQL+archivos privados, frecuencia diaria/predeploy, siete copias diarias y copia pre-release durante piloto, rol propietario técnico, restore aislado y credenciales mínimas/alertas. **Proveedor, bucket/contenedor y responsable operativo formal no confirmados.** Preparados [configuración inerte](BACKUP_CONFIGURATION.example.json), [procedimiento](BACKUP_RESTORE_RUNBOOK.md) y [reporte S16](S16_IMPLEMENTATION_REPORT.md). Sin job instalado, respaldo, restore, migración, deploy ni infraestructura persistente.

S16 preparación documental, cierre BLOCKED; S11 parcial, limpieza efectiva BLOCKED. El inventario/guard S11 sigue siendo código vigente. S12–S15/S17–S18 no iniciadas; S14/digest pendiente. Retención y objetivos están aprobados, no medidos. Pilot **NO-GO**: E2E S05, costos extra video, paridad EasyPanel, proveedores reales y backup/restore destino permanecen pendientes. La evidencia histórica siguiente no sustituye este estado vigente.

---

# Actualización vigente S11 — política aprobada, cierre bloqueado

Fecha: 2026-10-11. La respuesta «Si» aprueba la política S11/S16. S11 tiene una entrega **PARCIAL**: inventario read-only y bloqueo de eliminación de fotografías por el worker; no cuarentena ni borrado efectivo. Dependencia S16 **BLOCKED**: respaldo coherente/restore comprobado, destino y responsable pendientes. No usar una variable de configuración como sustituto de evidencia de recuperación. Sin migración nueva; head 0024 conservado. S12–S18 no iniciadas.

Entrega funcional parcial `a4aefd7726a5d6f5f9b5c454bca16192ce0fe62d`: 795 Python / 72 JavaScript PASS (44 dirigidas incluidas, no sumables). 0 FAIL / 0 ERROR / 0 SKIPPED en Python. Los resultados actuales y el commit funcional constan en [S11_IMPLEMENTATION_REPORT.md](S11_IMPLEMENTATION_REPORT.md). Conservados: E2E integrado S05 **BLOCKED**, costos adicionales reales de video **PENDIENTE**, paridad EasyPanel **PENDIENTE**, proveedores reales **PENDIENTE**, backup/restore del destino **PENDIENTE**. Pilot **NO-GO**. La política ya no está pendiente; la implementación efectiva y su dependencia sí.

El texto siguiente conserva evidencia histórica anterior a esta aprobación, no representa el estado vigente S11.

---

# Seguimiento vigente — S10 PASS / S11 BLOCKED

Fecha: 2026-10-11. **S10 cierre técnico local PASS; S11 auditada/BLOCKED por política de retención y dependencia S16. S12–S18 no iniciadas. Pilot NO-GO.** Código actual `09b4215f5b1aec1e44e77f67e42360ecedfd373c`, entrega S10 `023736b6429524f5d5cecbc2c8febe738157a9e1`. Los tres defectos P1 de S10 fueron corregidos y sus reproducciones ahora pasan; la parada anterior S10 fue superada mediante autorización expresa del usuario. El commit documental actual no implementa S11.

| Fase | Estado |
|---|---|
| S01–S08 | Cierres locales históricos documentados; S08 verificada antes de S09 |
| S09 | Implementada; 769 Python/69 JS PASS; 1d739a8/f7a7006 |
| S10 | Implementada; 787 Python/72 JS PASS; 09b4215/023736b |
| S11 | Auditada, sin código; falta aprobación de retención y dependencia S16 |
| S12–S18 | NOT STARTED; ninguna prueba/implementación propia certificada |

S10-D01/D02/D03 fueron P1 por pérdida/duplicación reproducida y están corregidos; las pruebas fallidas iniciales se conservan como evidencia histórica, no como estado final. La severidad P2 de la tabla original es planificación previa, no una excepción aceptada al P1.

La propuesta S11/S16 es no vinculante hasta aprobación: [política propuesta](S11_RETENTION_POLICY_PROPOSAL.md). Responsable/canal S13, destino de backup y clips/coach/capacidad S18 siguen por definir.

1. **BLOCKED:** E2E integrado navegador/servidor S05; no sustituido por API simulada/TestClient.
2. **PENDIENTE:** reserva/control de costos adicionales reales de video.
3. **PENDIENTE:** paridad de commit/digest/esquema/configuración/worker con EasyPanel.
4. **PENDIENTE:** validación de proveedores reales; gasto/envíos no autorizados.
5. **PENDIENTE:** backup y restauración del destino; prueba temporal no los certifica.

La tabla siguiente conserva tareas/dependencias y estimaciones originales.

---

# Backlog de estabilización

Propuesta; ninguna tarea implementada. P1 bloquea release; P2 exige cierre o mitigación firmada con prueba. Esfuerzo relativo S=un cambio acotado, M=varios puntos y regresión, L=contrato/concurrencia/operación; no estimación de días. QA verifica aceptación y release owner registra evidencia por commit/digest. Dependencias por ID; el orden ejecutivo está en RELEASE_READINESS.

| ID / severidad / esfuerzo | Descripción y archivos afectados | Riesgo / dependencias | Pruebas necesarias | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| S01 / P1 / S | Inventariar y seleccionar cambios; candidato limpio y comparación remota. docs/pilot-v1, Git, app/models.py, migrations/versions/0022_administration.py | Alto: incluir trabajo ajeno/omitir schema. Dep: aprobación de alcance | Diff seleccionado, cadena migration, export remoto read-only | Manifiesto lista cada cambio incluido/excluido, commit/digest/rutas/revisión destino o bloquea release; sin git add masivo. |
| S02 / P1 / S | Guard activo antes de resolver/vincular/procesar chat y antes de envío pendiente sensible. app/whatsapp/identity.py, runtime.py, capture.py, queue.py | Alto: sesión/cola antigua. Dep: S01 | Cuenta desactivada con cookie, identidad, challenge y eventos pendientes; reactivar explícitamente | No lectura/escritura/IA/respuesta sensible para cuenta inactiva; sin duplicado al recuperar. |
| S03 / P1 / M | Acotar listado/upload/review/media de coach al permiso ya disponible; si no hay relación representable, retirar acceso global de coach y usar alta admin asistida. app/main.py, administration.py, tests/test_basic_auth.py, test_coach_*.py | Alto: romper flujo legítimo. Dep: política y S01 | Dos atletas/dos coaches, ID directo, listados, archivos, POST upload, review asignada | Coach no enumera ni opera atletas sin autorización; flujo permitido sigue funcionando. No crear módulo de relaciones nuevo. |
| S04 / P1 / S | Evitar seed demo automático productivo y fallbacks inseguros; validar secretos presentes sin imprimirlos. scripts/start-app.sh, app/seed.py, main.py, docker-compose.yml | Alto: login/arranque. Dep: S01 | Arranque sin secreto, seed dev explícito, reinicio y hash de cuenta existente | Producción falla cerrada sin configuración; no restaura contraseña demo ni crea demo al reiniciar. |
| S05 / P1 / M | Separar guardar/compartir y exigir opt-in previo web/chat sobre alcance vivo; registrar evidencia mínima reutilizando contrato/persistencia existente o extensión aditiva acotada. app/whatsapp/capture.py, weekly.py, services/weekly_summary.py, static/training.js | Alto: exposición pública. Dep: consentimiento aprobado, S01 | Guardar/nota no crea share; negar/aceptar opt-in, TTL, revoke, fotos, nuevas notas; contratos legacy | Cero enlaces automáticos; aviso antes de creación y prueba de elección; revocar bloquea HTML/foto anónimos. Sin consentimiento verificable no habilitar sharing. |
| S06 / P1 / L | Aplicar límite común a IA web/chat con reserva idempotente en mecanismos existentes; rate por peer y presupuesto global/canal. app/administration.py, training.py, whatsapp/capture.py, media.py, runtime.py | Alto: costo y doble cargo. Dep: límites aprobados, S02 | Concurrencia web/chat, cuota límite, replay, corrección, audio dos etapas, bloqueo global | Ninguna llamada externa fuera de cupo; replay no cobra; manual/historial disponibles; operador puede detener canal. Sin billing ni ledger comercial nuevo. |
| S07 / P1 / M | Limitar intentos login y verificar CSRF/Origin en mutaciones con sesión sin romper webhook firmado. app/main.py, services/auth.py, weekly.py, training.py | Medio: proxy/clients. Dep: S01 | Login fallido/rate, Origin hostil/permitido, cookie HTTPS, webhook firma inválida | Ataques de sesión/origen ensayados bloqueados; secretos/cookies fuera de logs; login legítimo y webhook funcionan. |
| S08 / P1 / S | Distinguir 402 operativo de Kapso y ensayo de reintentos. app/whatsapp/kapso.py, provider.py, queue.py, worker.py | Alto: duplicar mensajes o quedar bloqueado. Dep: S06 | HTTPError 402/429/5xx, DNS/timeout, SENDING lease vencida, chunks bloqueados | 402 detiene intento y alerta sin retry automático; 429 máximo 5 intentos/backoff; ambiguo UNCERTAIN no replay ciego; recuperación por operador comprobada. |
| S09 / P2 / M | Validar antes de reserva y liberar solo fallos inequívocamente sin llamada; explicar cuota al fallar. app/administration.py, training.py, main.py | Medio: reembolso doble. Dep: S06 | Archivo inválido, provider disabled, error previo/post llamada, transcripción exitosa/interpretación fallida | Fallos locales no gastan; consumo externo incierto se conserva y reporta; audio parcial no repite transcripción exitosa injustificadamente. |
| S10 / P2 / M | Verificar guardar/editar/notas y replay sin pérdida ni divergencia; corregir solo defecto reproducido. services/training_service.py, training_contracts.py, whatsapp/capture.py, static/training.js | Alto si pérdida reproducida: elevar P1. Dep: S01,S05 | CRUD, doble Guardar, botón vencido, nota/edit, links analysis borrado, payload legacy | Un evento guarda una sesión; contenido visible coincide tras edición/recarga; fallo no pierde borrador ni sobrescribe silenciosamente. |
| S11 / P2 / M | Política de retención y limpieza segura de fotos sin referencias; inactiva y shares activos. services/training_media.py, training_service.py, weekly_summary.py, whatsapp/worker.py | Alto: borrar medio vigente. Dep: S05,S16 | Imagen compartida/referenciada, orphan, worker detenido, desactivar usuario con enlace | Plazo aprobado y comunicado; nunca borra medio referenciado; enlaces de cuenta desactivada dejan de exponer datos según política propuesta; limpieza/export manual ensayada. Privacidad sin política bloquea altas. |
| S12 / P2 / S | Runbook de video interrumpido y recuperación asistida existente. app/main.py, tests/test_async_analysis.py, docs/pilot-v1 | Medio: reanálisis/consumo. Dep: S09,S16 | Reinicio durante job en entorno desechable; luego reanalyze existente | Pendiente pasa a FAILED visible, originales/resultados completos sobreviven; una recuperación autorizada conserva ownership y no duplica review. No agregar broker. |
| S13 / P1 / M | Alertas y consultas operativas mínimas redactadas. app/whatsapp/worker.py, queue.py, docs/pilot-v1/PILOT_OPERATIONS.md, health actual | Medio: falsa salud y PII. Dep: S08,S12 | Worker dormido/caído, cola vieja, 402, disk bajo, IA fallida, alerta recibida | Heartbeat efectivo y cola medidos; cada alerta llega a responsable; ningún teléfono/token/workout en logs. No usar solo proceso Up. |
| S14 / P1 / S | Identidad app/worker, tag y manifiesto; escaneo del digest/dependencias. Dockerfile, constraints.txt, requirements.txt, docs/pilot-v1 | Medio: builds distintos. Dep: S01 | Build candidato, catálogo/modelo checksum, scan y compatibilidad | SHA/digest/head/assets/perfiles fijados; app y worker misma release; vulnerabilidad crítica aplicable resuelta; evidencia de scan archivada. |
| S15 / P1 / M | Gate de pruebas antes de disparar deploy y aprobación manual para producción. .github/workflows, scripts/test-*.ps1, compose.test.yml | Alto: push main despliega ahora. Dep: S14 | Job fallido bloquea POST; candidato aprobado en base temporal, contratos y E2E | No deploy sin checks del commit y aprobación; nunca pytest contra DB producto. No disparar workflow durante preparación. |
| S16 / P1 / M | Backup coherente DB/storage y claves, restore aislado y compatibilidad rollback. scripts/start-app.sh, migrations/versions, docker-compose.yml, docs/pilot-v1 | Alto: pérdida/clave faltante. Dep: S01,S14 | Restaurar copia temporal, descifrar fixture, medias/rows, viejo binario contra schema nuevo | Restore medido cumple RPO/RTO acordados; backup verificable; ruta de rollback ensayada sin downgrade destructivo. |
| S17 / P2 / S | Verificar límite 200 y límites de uso piloto; no ocultar registros. services/training_service.py, tests/test_training_sessions.py, PILOT_OPERATIONS | Bajo/medio. Dep: límites | 199/200/201 registros, detalle directo/resumen/export | Se informa límite actual; cohorte no lo excede o corrección acotada compatible antes de activar; nunca afirmar historia completa truncada. |
| S18 / P1 / M | Certificar combinaciones video y coaches activos/capacidad. services/exercise_library.py, exercise_profiles.py, exercise_validation.py, main.py, TEST_PLAN | Alto: feedback erróneo/servicio humano inexistente. Dep: S03,S12 | Clips representativos, vistas/calidad mala, reference_only, coach inactivo/no disponible, cierre review | Lista exacta de ejercicio/vista validada por coach; unsupported bloqueado; revisión solo con capacidad y permisos, cierre visible al atleta. |

No aceptar P2 de pérdida/exposición confirmada como excepción: reclasificar P1/P0 por impacto. Las tareas pueden subdividirse en PR pequeños conservando su aceptación; cualquier cambio de esquema exige análisis y validación aislada antes de una autorización posterior de migración.
