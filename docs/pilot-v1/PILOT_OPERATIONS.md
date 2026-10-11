# Actualización de responsabilidades — 2026-10-11

Gastón administra EasyPanel; Codex no necesita acceso SSH ni sesión del panel. GitHub es origen de la versión publicada y GitHub Actions dispara deploy **solo bajo autorización expresa**. Codex prepara código/pruebas/manifiesto y sube exclusivamente refs aprobadas. Gastón aplica variables, obtiene inventario y evidencia redactada API/worker/DB/volúmenes/proxy, realiza backups/restore/rollback autorizados y confirma SHA/digests. Falta de acceso directo de Codex no es bloqueo; falta de evidencia verificable sí.

Workflow existente push main llama al webhook sin checks/gates: S15 permanece pendiente, YAML sin cambios. No push a main, merge, POST ni deploy. S16 sigue BLOCKED por pruebas operativas reales pendientes; continuar localmente con KeePassXC/Resend. Plan vigente: PILOT_A_RELEASE_PLAN.md y DEPLOYMENT_RUNBOOK.md; no solicitar nuevamente SSH para esta etapa.

---

## Historial anterior — instrucciones de acceso directo sustituidas

## Actualización S16 — 2026-10-11

Gastón confirmado como operador. Ensayo R2 sintético **PASS**: AES-256-GCM cliente, upload/download autenticados, DB nueva y cuatro archivos restaurados con hashes/referencias iguales; 3 usuarios, 1 sesión/foto/análisis/review, head 0024. Contenedores propios detenidos. 5,31 s y 92.197 bytes corresponden a muestra pequeña, no RTO operativo. Primer intento falló por expectativa HTTP anónima (400); corrección del harness y repetición aislada documentadas. Privacidad por dominios/r2.dev, configuración de cifrado proveedor, permisos separados, custodia definitiva, restore representativo del producto, scheduler y alertas **pendientes**. S16 sigue parcial y **NO-GO**, sin habilitar limpieza S11. Ver [reporte S16](S16_IMPLEMENTATION_REPORT.md).

# Estado vigente — cierre final Pilot A

Validación local final del candidato `03cfd4387a75f70fae60ccd2108a83d24dc57f31`: Python **820 PASS, 1 SKIPPED, 0 FAIL** (257,41 s); JavaScript **77 PASS, 0 FAIL/SKIPPED**. La prueba omitida requiere WEEKLY_RELEASE_PUBLIC_BASE_URL real y queda **NOT RUN**, sin afirmar paridad de dominio. PostgreSQL nuevo tmpfs, red interna nueva, sin puertos Docker publicados ni credenciales de proveedores; migraciones desde cero y worker vacío PASS; contenedores propios detenidos. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-2e4m_dlq/offline-tests.log` y `environment.json`. Tres advertencias de deprecación no bloquean estas pruebas. Workspace original: 153 rutas verificadas sin cambios.

Fecha: 2026-10-11, America/Santiago. Rama: codex/pilot-v1-stabilization. Candidato auditado: `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. **Pilot A NO-GO**. Alcance obligatorio: bitácora + WhatsApp + video certificado + coach titular/suplente, 3–5 atletas, 30 días. Esta entrega no autoriza proveedores, infraestructura persistente ni publicación.

Estados: PASS = evidencia ejecutada y limitada a su entorno; FAIL = defecto/evaluación fallida demostrada; BLOCKED = falta autorización, acceso, responsable o dependencia; NOT RUN = sin ejecución. Resultados históricos no certifican el candidato final ni el destino.

## Operación vigente

Responsables nominales de backup, operación, release y coach titular/suplente pendientes. Bucket R2 indicado; alertas no entregadas/certificadas. Mantener manual/historial ante límite IA. Presupuesto piloto 3 USD/día, 30 USD/30 días; 80% alerta y 100% bloqueo. Reservas no son tarifas ni factura. Video exige componentes adicionales aprobados.

Ante 402: detener intentos; recuperar individualmente tras evidencia/autorización. Ante UNCERTAIN: no reenviar ni liberar costo desconocido. Ante incidente de privacidad: bloquear exposición/canal afectado y revisar; no borrar evidencia personal ni bases por automatismo. Fallo backup/restore o falta coach detiene nuevas altas.

R2: diario y predeploy, siete copias diarias + pre-release durante piloto; destino privado, TLS/AES-256 objetivo, custodia de claves separada. Configuración sigue inerte sin jobs. Incluir claves de enlaces semanales cifrados además de WhatsApp. Restore debe validar DB, archivos, reviews y cifrado con RPO/RTO medidos.

Consultar [readiness final](PILOT_A_FINAL_READINESS.md), [video](PILOT_A_VIDEO_CERTIFICATION.md), [WhatsApp](PILOT_A_WHATSAPP_VALIDATION.md) y [release](PILOT_A_RELEASE_PLAN.md).

---

## Evidencia histórica conservada — no sustituye estado vigente

# Estado vigente — S17 cierre técnico local PASS, pendiente de revisión

Fecha: 2026-10-11. Base c5d1764 verificada, original intacto. S08–S10 cerradas localmente; S11 parcial; S16 preparación documental completada, validación operativa pendiente. S12/S13/S15/S18 conservan dependencias abiertas; S14 necesita build/identidad/scan local verificables. Se completó **solo S17** con mitigación explícita y recursos desechables existentes: **803 Python / 75 JavaScript PASS**; 57 dirigidas son subconjunto, no sumables; sin FAIL/ERROR/SKIPPED en la suite Python. El commit único se identifica mediante git log del reporte S17; no se repiten cierres anteriores. Auditoría completa, cambios y resultados en [reporte S17](S17_IMPLEMENTATION_REPORT.md).

Mitigación S17: límite de listado 200 conservado e informado, desempate estable; filas anteriores conservadas y consultables en resumen semanal/detalle privado. Registro manual permite superar 200, sin consumo IA. Sin paginación/exportador nuevo ni garantía de que toda cohorte permanecerá debajo de 200. No borrar para liberar historial; aviso operativo a 150 es propuesta, no automatismo certificado.

**NO-GO**: E2E integrado S05 BLOCKED; restauración real de respaldos PENDIENTE; costos adicionales de video PENDIENTE; paridad EasyPanel PENDIENTE; pruebas reales de canales habilitados PENDIENTE. S11/S16 no se cierran por resultados locales. Tras S17 se detiene para revisión, sin avanzar automáticamente. El texto siguiente conserva historia, no reemplaza este estado vigente.

---

# Operación del piloto de 30 días

Propuesta: inicia día 1 con autorización y primer grupo; no hay fecha de inicio fijada. Release owner, operador EasyPanel/DB, QA, responsable de privacidad/costos y coach titular/suplente deben tener nombre y horario antes de activar. Una persona puede cubrir varios roles, pero ninguna alerta queda sin dueño.

## Activación gradual

- Antes del día 1: gates completos, respaldo/restore, límites escritos, consentimiento de datos/medios y sharing separado, formación breve y coach disponible. No invitar ni crear cuentas en esta etapa.
- Días 1–3: 3 atletas asistidos; observar 72 h y al menos una captura completada por cada uno. Foto/audio/chat/video requieren evidencia real previa del candidato; no prometer canal no validado.
- Días 4–7: ampliar primero a 10 y luego hasta 15, máximo 5 altas por tanda. Antes de cada tanda: cero P0/P1 abiertos, sin incidente de datos/privacidad, gastos bajo límites, cola operativa y capacidad coach. Si falta evidencia conservar 3, sin ampliar.
- Días 8–29: revisión diaria operativa, revisión semanal días 7/14/21/28; soporte y ajustes de estabilización mediante release pequeña validada. No expandir alcance.
- Día 30: cerrar reporte, revisar incidentes/costos/uso/confianza, revocar enlaces según elección/política y acordar conservación/export de datos. No borrar cuentas/datos automáticamente ni extender el piloto sin acuerdo.

## Política de límites propuesta para aprobación

Son valores conservadores propuestos, no controles existentes ni costos validados. Verificarlos en S06 y medir con 3 atletas antes de ampliar. No convertir defaults FREE10/PAID200 en oferta comercial.

| Recurso | Propuesta inicial | Acción al límite |
| --- | --- | --- |
| IA interpretación | 3 intentos/atleta/día, web+chat combinados, incluye correcciones con nueva llamada | Rechazo antes de proveedor, fallback manual. |
| Transcripción | 3 intentos/atleta/día y 180 s/8 MB por archivo | Rechazo previo; interpretar audio consume también cupo interpretación. |
| WhatsApp | 20 eventos de usuario/atleta/día, 5/min por peer; duplicados no cuentan como trabajo nuevo; mensajes operativos también bajo presupuesto | No generar respuestas en bucle; detener trabajo facturable, indicar límite una vez cuando presupuesto permite. |
| Video | 1 nuevo análisis/atleta/día, 1 job concurrente global durante cohorte 3 | Acceso asistido; límite bytes actual 250 MB exige validar duración/CPU y acordar máximo menor antes de activar. |
| Coach | 1 solicitud abierta/atleta y cupo diario declarado por coach | No ofrecer nuevos turnos sin disponibilidad; propuesta de respuesta <=48 h hábiles solo si coach la acepta. |
| Historial | Aviso interno a 150 sesiones y no exceder 200 antes de mitigar S17 | Operador revisa; nunca borrar para liberar listado. |
| Gasto | Tope diario y total de 30 días en USD/CLP, por proveedor y global: pendiente de importe aprobado | A 80% alerta; a 100% suspender nuevas llamadas/envíos facturables. Costos desconocidos requieren revisión, no se tratan como cero. |

Falta importe monetario: **gate obligatorio**, no autorización implícita de gasto. Medir costo por sesión completada incluyendo correcciones, audio dos etapas, outbox dividido, video y tiempo humano. Mantener manual/lectura disponibles al pausar IA/chat. Interruptor de WhatsApp/IA mediante configuración existente requiere proceso operativo ensayado; no afirmar aplicación instantánea sin reinicio/control verificado.

## Monitoreo y alertas propuestas

| Señal / umbral inicial | Responsable / reacción |
| --- | --- |
| Pérdida/exposición, permiso ajeno o share sin elección: 1 evento | Privacidad + release owner: incidente inmediato, pausar superficie, preservar evidencia y revocar enlaces afectados con autorización operativa. |
| /api/health falla dos veces a 1 min; login general falla | Operador: inspección inmediata DB/schema/proxy, sin restart ciego. /health solo no basta. |
| Heartbeat worker ausente >2 min o pendiente más viejo >5 min | Operador: revisar leases/locks, backlog y expiración; worker Up no acredita trabajo. |
| 402 o UNCERTAIN: 1 evento | Costos/operador: pausar nuevos envíos si financiero, reconciliar; nunca retry automático ambiguo. |
| FAILED inbox/outbox >=3 en 15 min o errores IA >=3 en 15 min | Operador/QA: revisar códigos/latencia sin contenido privado; activar fallback. |
| Video activo >10 min o FAILED por reinicio | Operador/coach: revisar recursos y comunicar estado; umbral ajustar al baseline real, no SLA de procesamiento. |
| Disco >=80%, >=90% crítico; backup >24 h o restore no comprobado | Operador: frenar uploads si crítico, backup/verificación; no borrar medios referenciados. |
| Presupuesto 80%/100% o medición incompleta | Costos: alerta/bloqueo de llamadas; reconciliar factura y uso antes de reabrir. |
| Review sin atención >24 h hábiles; cierre >48 h acordadas | Coach titular/suplente: redistribuir con permisos y capacidad; suspender oferta si no hay coach. |

S13 debe demostrar recepción de alertas con fallos simulados; no hay sistema certificado hoy. Revisión diaria: health/schema, API-worker digest, cola/leases, FAILED/UNCERTAIN, costos, disco, backup y reviews. Log operacional guarda IDs internos mínimos, estados y tiempos; no teléfonos, tokens públicos, passwords, cookies, keys, audio/fotos o texto de entrenamiento. No exportar DB para analítica informal.

## Métricas y soporte

Medir participantes activos, sesiones guardadas por canal, tiempo hasta primer registro, correcciones por propuesta, abandono antes de guardar, duplicados/pérdidas, errores de fecha/resultados, uso de resumen, shares opt-in/revocados, clips abstención vs completados, minutos coach y costo observado por atleta/sesión. Separar fixtures de uso real; frecuencia de registro no prueba mejora deportiva. Reporte semanal agregado sin contenido personal.

Alta asistida: verificar identidad/consentimiento, contraseña individual por canal acordado, explicar fallback manual, fotos sin terceros identificables, edición/borrado y enlaces vivos. Soporte por responsable/canal acordado; no recuperación automatizada prometida. Atleta conserva control de compartir y puede solicitar pausar canal/review o exportación/borrado con procedimiento autorizado.

## Incidentes y criterios de continuidad

P0: pausar inmediatamente activación y superficie afectada; P1: no ampliar y contener antes de reanudar. Objetivo propuesto de acuse operativo <=30 min en horario cubierto; horario y suplencia pendientes. P2: ticket con responsable/mitigación/fecha y seguimiento diario. Registrar impacto, timestamps Santiago, digest/schema, pasos sin PII, recuperación y evidencia. No enviar avisos externos desde herramientas sin autorización.

Ampliar solo tras 72 h estables, 3 atletas con registro persistente, cada canal ofertado validado, backup reciente, alertas recibidas, presupuesto conocido y reviews atendibles. Si proveedor/capacidad no alcanza, pausar ese canal y conservar bitácora; esto es operación temporal, no aprobación de una release con alcance requerido sin validar. Día 30 recomendar continuidad/repetición/cierre por evidencia, sin lanzar automáticamente producto comercial.
