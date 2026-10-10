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
