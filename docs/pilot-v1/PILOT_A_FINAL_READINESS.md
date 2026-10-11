## Actualización S16 — 2026-10-11

Gastón confirmado como operador. Ensayo R2 sintético **PASS**: AES-256-GCM cliente, upload/download autenticados, DB nueva y cuatro archivos restaurados con hashes/referencias iguales; 3 usuarios, 1 sesión/foto/análisis/review, head 0024. Contenedores propios detenidos. 5,31 s y 92.197 bytes corresponden a muestra pequeña, no RTO operativo. Primer intento falló por expectativa HTTP anónima (400); corrección del harness y repetición aislada documentadas. Privacidad por dominios/r2.dev, configuración de cifrado proveedor, permisos separados, custodia definitiva, restore representativo del producto, scheduler y alertas **pendientes**. S16 sigue parcial y **NO-GO**, sin habilitar limpieza S11. Ver [reporte S16](S16_IMPLEMENTATION_REPORT.md).

# Pilot A — readiness final

Validación local final del candidato `03cfd4387a75f70fae60ccd2108a83d24dc57f31`: Python **820 PASS, 1 SKIPPED, 0 FAIL** (257,41 s); JavaScript **77 PASS, 0 FAIL/SKIPPED**. La prueba omitida requiere WEEKLY_RELEASE_PUBLIC_BASE_URL real y queda **NOT RUN**, sin afirmar paridad de dominio. PostgreSQL nuevo tmpfs, red interna nueva, sin puertos Docker publicados ni credenciales de proveedores; migraciones desde cero y worker vacío PASS; contenedores propios detenidos. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-2e4m_dlq/offline-tests.log` y `environment.json`. Tres advertencias de deprecación no bloquean estas pruebas. Workspace original: 153 rutas verificadas sin cambios.

Fecha: 2026-10-11, America/Santiago. Rama: codex/pilot-v1-stabilization. Candidato auditado: `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. **Pilot A NO-GO**. Alcance obligatorio: bitácora + WhatsApp + video certificado + coach titular/suplente, 3–5 atletas, 30 días. Esta entrega no autoriza proveedores, infraestructura persistente ni publicación.

Estados: PASS = evidencia ejecutada y limitada a su entorno; FAIL = defecto/evaluación fallida demostrada; BLOCKED = falta autorización, acceso, responsable o dependencia; NOT RUN = sin ejecución. Resultados históricos no certifican el candidato final ni el destino.

## Resumen ejecutivo

Bitácora, seguridad S02–S10, historial S17 y UI reciente implementados; existe evidencia local e integrada histórica. No se certifica publicación por completar tests locales. Falta respaldo restaurable R2, canales completos reales conciliados, video/costos y coach certificados, alertas, identidad/scan del artefacto, gates de CI, paridad/smoke destino y rollback.

No hay nuevas funcionalidades en esta entrega. La prioridad operativa S16 requiere autorización/acceso específicos y responsables, por lo que se detiene su ejecución. Las suites locales concluyeron en recursos nuevos desechables sin proveedores.

## Estado S01–S18

| Tarea | Estado auditado | Evidencia y pendiente |
|---|---|---|
| S01 | PASS local histórico | Worktree reproducible, selección y PostgreSQL desechable; no certifica artefacto productivo. |
| S02 | PASS local histórico | Cuentas inactivas bloqueadas en identidad, capture y outbox. |
| S03 | PASS local histórico | Coach limitado a reviews asignadas; sin autorización general coach-atleta. |
| S04 | PASS local histórico | Secretos y seed seguros; comprobar valores del destino antes de arrancar. |
| S05 | PASS local histórico e integrado | Nueve casos integrados + tres guards en 8db5544; cambios posteriores requieren validación final. |
| S06 | PASS local histórico / BLOCKED video real | Reservas y costos adicionales ya implementados; valores reales de cómputo/storage/otros no certificados. |
| S07 | PASS local histórico | Login, Origin, cookies y proxies; destino HTTPS pendiente. |
| S08 | PASS local histórico | 402 sin retry, 429 máximo cinco, UNCERTAIN y recuperación individual auditada. |
| S09 | PASS local histórico | Fallos previos sin gasto, reutilización de audio parcial; no repite implementación. |
| S10 | PASS local histórico | Edición parcial, notas y Save idempotente; head Alembic 0024. |
| S11 | PASS inventario / BLOCKED cierre | Conservación e inventario; cuarentena/borrado efectivos dependen de restore. |
| S12 | BLOCKED / NOT RUN | Reinicio de video y recuperación completa no certificados; depende S16. |
| S13 | BLOCKED / NOT RUN | Operador y canal de alertas no confirmados; recepción no probada. |
| S14 | NOT RUN cierre | Sin build/digest/scan final; hash de fuentes disponible, no equivale a imagen. |
| S15 | FAIL control actual / NOT RUN corrección | deploy.yml dispara POST por push main sin pruebas ni aprobación protegida. No disparar workflow. |
| S16 | PASS documentación / BLOCKED operativo | R2 elegido y bucket identificado; permisos, backup, claves, restore y alertas no comprobados. |
| S17 | PASS local histórico | Mitigación explícita 200 registros; conserva datos y consulta por semana. |
| S18 | BLOCKED / NOT RUN | Sin clips revisados, combinaciones certificadas ni coach titular/suplente confirmado. |

## Bloqueos verificables

| ID / dependencia | Evidencia actual y trabajo mínimo | Pruebas / criterio de cierre | Riesgo | Responsable pendiente |
|---|---|---|---|---|
| B01 S16 ← S14 | Bucket R2 fluxio-movement-backups identificado por propietario, no inspeccionado. Confirmar credenciales y permisos privados, TLS/cifrado, custodia claves. Preparación JSON inerte. | Inventario autorizado de configuración; datos no públicos, acceso mínimo y clave recuperable. | Copia accesible o irrecuperable. | Propietario técnico: nombre y suplencia sin confirmar. |
| B02 S16/S11 ← B01 | Crear backup coherente DB/storage/claves; restaurar primero datos sintéticos y luego copia real solo autorizada; medir tiempos e integridad. | DB, medios, análisis, reviews, tokens cifrados y claves funcionan; alertas de fallo/antigüedad recibidas. | Pérdida de datos; borrado de medios sin retorno. | Operador de backup y aprobador de restore. |
| B03 canales ← S14 | Texto/foto Sandbox con evidencia parcial, audio/consentimiento WhatsApp real sin completar. Worker de QA no certificado activo actualmente. | Firma HTTPS, texto/foto/audio, Save/Corregir/Cancelar/resumen/share/revoke, entrega, persistencia, sin duplicados y conciliación de proveedor. | Gasto, duplicados, exposición accidental. | QA + propietario que autoriza teléfono/gasto. |
| B04 S12/S18 ← S16 | Siete ejercicios declarados supported; cero combinaciones certificadas para Pilot A. Reservas adicionales existen, cifras no medidas. | Clips consentidos por vista, abstención, CPU/RAM/tiempo/bytes, costo IA, reinicio y reanálisis; revisión técnica humana documentada. | Feedback incorrecto o costos no controlados. | Coach técnico + operador infraestructura. |
| B05 coach ← S03/B04 | Permisos por asignación existentes; titular/suplente y capacidad sin confirmar. | Solicitud, asignación, anotaciones temporales, aceptar/descartar IA, feedback/próxima sesión, cierre y lectura atleta; dos atletas/dos coaches/admin; negativos cross-ID. | Acceso excesivo o promesa de servicio sin cobertura. | Coach titular y suplente nominales. |
| B06 S13 ← S12/S08 | Métricas y señales parciales existentes; no entrega real de alertas. | Worker muerto/cola vieja/402/IA/job video/disco/backup; 80% alerta, 100% bloqueo; operador recibe y responde. | Fallos invisibles, falsa salud por proceso Up. | Responsable operativo y canal autorizado. |
| B07 S14/S15 | Candidato hash identificado; workflow main carece de gate. | Build fijado, scan, digest API=worker, migraciones/head, checks del commit y aprobación manual antes de POST. | Publicación automática no autorizada o artefactos distintos. | Release owner / administrador GitHub-EasyPanel. |
| B08 destino/rollback ← B01–B07 | Sin acceso/paridad EasyPanel ni rollback ensayado; suites locales finales aprobadas con una prueba de dominio omitida. | Commit/digest/Alembic/config/TLS/proxy/storage y smoke destino aprobados; restauración/rollback compatible; aprobación publicación y altas. | Entorno distinto al probado. | Release owner y operador EasyPanel. |

## Costos y mediciones

No hay factura conciliada ni medición certificada de video. Evidencia QA anterior: 17 intentos físicos, cinco reservas IA, US$0,59 asignados; no es gasto real ni tarifa. Máximo autorizado de aquella sesión: 20 respuestas y US$2, sin ampliación ni reinicio del acumulado. Reservas configurables: texto/foto 0,05; transcripción 0,03; IA video 0,20; envío sandbox 0,02 USD. Piloto: 3 USD/día y 30 USD/30 días, alerta 80%, bloqueo 100%. No garantizar máximo de factura si proveedor no ofrece límite duro.

## Orden exacto de cierre

1. Confirmar operador, bucket R2, custodia claves y autorización específica de inspección/ensayo.
2. S16: backup/restore coherente y medido, automatización y alerta; después habilitar limpieza S11 aprobada.
3. Identificar candidato y app/worker de prueba; completar canales reales con autorización renovada y conciliación.
4. S12/S18: medir video, aprobar reservas reales, certificar combinaciones y revisión completa con titular/suplente.
5. S13: comprobar alertas recibidas y respuesta operacional.
6. S14/S15: build/digest/scan, gate de CI y aprobación protegida, sin push ni deploy en esta etapa.
7. Identificar destino EasyPanel read-only autorizado, ensayar rollback aislado, validar suites finales del artefacto.
8. Solicitar autorización de deploy; ejecutar smoke autorizado del destino, revisar doce gates y recién solicitar/autorizar altas de tres atletas.

Para incorporar tres atletas se deben cerrar B01–B08: video y coach son obligatorios y no pueden excluirse para obtener GO. Detenerse para revisión antes de publicación.
