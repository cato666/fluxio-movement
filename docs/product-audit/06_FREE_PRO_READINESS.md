# Preparación de Free y Pro

Fecha: 2026-10-09. Esta evaluación distingue **capacidad construida**, **validación local** y **preparación para cobrar**. Precios recibidos del usuario como hipótesis: Pro **$3.990 CLP/mes**, fundador **$2.990 CLP/mes**. No son precios implementados/validados, ni incluyen supuestos sobre impuestos, margen, demanda, ingreso o tarifa de proveedor.

## Estado real del sistema comercial

`User.plan` acepta FREE/PAID. `AdminSetting` define límites y operaciones; `PlanInteraction` cuenta cada intento reservado. Default actual: Free 10 interacciones/mes, PAID 200, con ANALYZE/INTERPRET/TRANSCRIBE **habilitados en ambos**. Son defaults del código, no oferta recomendada ni consumo económicamente sostenible demostrado.

`consume` usa lock del usuario para limitar concurrencia, reserva y commit antes del trabajo; un audio interpretado puede usar dos operaciones, una transcripción y una interpretación. Reinicia período mensual UTC. Cambiar de plan conserva consumo del mes. La captura WhatsApp no aplica este control; tener accounting no equivale a límites. Cuenta desactivada en web pierde acceso, pero la identidad WhatsApp requiere revisión del guard transversal.

Admin puede asignar PAID y cambiar cupos; no hay checkout, facturas, renovación, cancelación, estado de mora, prueba gratuita, descuento fundador ni conciliación. GET plan/admin no figura en OpenAPI remoto inspeccionado hoy. No se debe vender como suscripción operativa por existir la etiqueta PAID.

Fuentes: `app/administration.py`, `app/models.py`, `app/training.py`, `app/main.py`, `app/whatsapp/capture.py/media.py`; `tests/test_administration.py` pasó en base aislada; admin UI pasó con API fixture.

## Qué está listo como capacidad de cada plan

| Capacidad | Free candidato | Pro candidato | Preparación real |
| --- | --- | --- | --- |
| Cuenta/login | Sí, con alta asistida en piloto | Igual | Código y pruebas; falta autorregistro/recovery para apertura pública |
| Diario manual, edición/eliminación, RPE y notas | Sí | Incluido | PY/JS y E2E actual; contrato remoto visible; lifecycle de fotos/historia por mejorar |
| Estadísticas básicas | Sí | Incluido | Conteo semanal y promedio RPE factual; no trends/PR |
| Resumen semanal | Sí | Incluido | API/recap construido y E2E actual; no envío programado |
| Copiar/revocar enlace semanal | Opcional con consentimiento | Incluido | Código/test; enlace vivo implica fotos/notas nuevas; separar automático WhatsApp |
| Interpretación de texto/foto | No según hipótesis Free | Sí, con cuota | Construida; IA real histórica sandbox; gating remoto y presupuesto no cerrados |
| Dictado/audio | No según hipótesis Free | Sí, con cuota | Construido; transcripción + interpretación pueden consumir dos llamadas |
| Captura WhatsApp | Decisión por validar | Candidata bajo cupo | Canal construido y probado históricamente; cuotas/account-status/control costos pendientes |
| Historial inteligente (PR/trends/asistente) | No construido | No listo | Requiere datos/modelo/capacidades de 04/05; no anunciar como disponible |
| Análisis técnico mensual automático | No incluido inicialmente | Candidato limitado por perfil | Pipeline construido; precisión/capacidad/costo/operación mensual no certificados |
| Review humana mensual | No prometida | Solo si capacidad validada | Workflow existe; servicio humano/cupo/SLA/costo no definidos |
| Pago recurrente/fundador | No aplica | **No listo** | Sin integración de suscripción ni beneficio fundador implementado |

“Listo como capacidad” no significa producto remoto comercial listo. El siguiente MVP puede usar alto porcentaje de componentes existentes, pero todavía hay bloqueos de oferta/operación.

## Requisitos antes de comenzar a cobrar

### Bloqueos técnicos/comerciales

1. Definir oferta contractual real: qué consume cupo, límites de texto/foto/audio/WhatsApp/video, si coach humano está incluido y cuál es entrega. No llamar “análisis técnico” a un detector de repeticiones sin especificar soporte.
2. Unificar entitlements por usuario/canal en servicio compartido: web, WhatsApp y acciones coach a nombre del atleta. Validar cuenta activa/consentimiento y publicar API/administración versionada.
3. Diseñar ledger de reserva/consumo/resultado/reembolso idempotente. No ocultar consumo por error; medir intentos facturables y separar cuota de negocio de tokens/segundos reales.
4. Integrar pagos con proveedor elegido después de verificar requisitos/tarifas oficiales: alta, webhooks firmados/idempotentes, renovación, cancelación, fallos, downgrade, conciliación y derechos de acceso. No se selecciona proveedor ni se inventa comisión.
5. Cuenta/soporte: autorregistro y recuperación para autoservicio o piloto asistido claramente comunicado; credenciales demo seguras y seed de producción controlado.
6. Consentimiento de compartir y de relación coach-atleta; ciclo de export/borrado/retención. Validar requisitos regulatorios con fuentes/asesoría al implementarlos, no afirmar cumplimiento en esta auditoría.
7. Release y smoke autenticado del destino: commit/image/migración exactos, worker, storage, firma/proxy y health de esquema. Probar pagos en sandbox, nunca cobros reales durante auditoría.
8. Medir costo por sesión completada y por usuario activo incluyendo correcciones y soporte; verificar restauración y alertas de jobs/cola/gasto. Validar hardware móvil, no solo viewport.

### Definición verificable de listo

Un usuario piloto obtiene cuenta, registra manualmente sin usar IA de pago, puede consultar/editar/borrar y revocar enlaces. Un Pro de prueba tiene acceso coherente web/chat, cobro sandbox reflejado una vez, cancelación/downgrade sin perder historial y cupos aplicados en todos los canales. Una operación fallida tiene estado/cargo explicado. Ninguna promesa de análisis o coach excede evidencia/capacidad. Estos son criterios propuestos, no casos aprobados hoy.

## Costos que deben medirse

| Rubro | Datos existentes | Falta para unit economics |
| --- | --- | --- |
| Interpretación texto/foto | TrainingAIUsage: modelo, tokens reportados, latencia/status | Tarifa efectiva por modelo/fecha, detalle de foto, correcciones/reintentos y atribución a sesión |
| Transcripción | Segundos, modelo, tokens nullable, status | Conciliar factura/tarifa; sin tokens no asumir consumo cero |
| Razonamiento video | AIReasoningRun tokens/reasoning/latencia | Costo monetario por ejecución y elegibilidad; fallos/calls repetidas |
| WhatsApp | Inbound/outbound/media/bytes, cost nullable y rate env opcional | Precio/proveedor/categoría real y facturación por entrega/país/plan; no convertir UNKNOWN en cero |
| Cómputo/video | Duración y estados; artefactos | CPU/tiempo de cola/memoria por video/ejercicio, demanda pico y fallos |
| Storage/transferencia | Archivos e imágenes persistentes | Bytes por atleta/mes, retención, backups y egress real |
| Coach humano | Workflow de review | Minutos por solicitud, tasa de revisión, disponibilidad, remuneración real |
| Cobro/operación | Sin integración | Comisiones/impuestos aplicables, soporte, fraude/reembolsos y cambio USD/CLP comprobados |

Fórmula propuesta sin números inventados:
`contribución mensual = precio neto realmente cobrado - pagos - IA - WhatsApp - cómputo/storage - soporte/coach imputable`.
Evaluar precio fundador por separado. No afirmar margen positivo con conteos de tokens ni precio nominal.

## Límites por plan propuestos, pendientes de medición

- **Free:** diario manual y semana factual; no interpretar/transcribir/analizar por defecto bajo hipótesis inicial. Límites de abuso/storage se definen con medición, no cupo comercial artificial por sesión manual.
- **Pro:** presupuesto mensual explícito de capturas asistidas; distinguir foto/texto/audio (audio tiene transcribe + interpret) y correcciones. Medir primero y traducir a unidades comprensibles para el atleta.
- **WhatsApp:** rate limit por peer y budget por atleta independientes de dedupe; no confundir tres challenges por hora con límite de captura/IA.
- **Video:** límite por archivo y duración/perfil soportado, concurrencia/job budget y almacenamiento; un cupo mensual no basta si un usuario sube videos largos.
- **Review humana:** cuota/cupo explícito separado de análisis automático y con capacidad real; no incluir “mensual” ilimitado por valor nominal.
- Mantener fallback manual y acceso al historial al agotarse cupo o vencer Pro; comunicar estado/reintento y período con zona horaria acordada.

No se recomiendan los defaults 10/200 como oferta hasta medir costos y comportamiento. No se inventa una nueva cuota numérica.

## Validación con usuarios

Hipótesis a verificar: disposición a pagar ambos precios, preferencia WhatsApp/web, confianza en borradores y necesidad de confirmar, uso de resumen, valor de PR/trends frente a coach, tolerancia a límites y a fallos, entendimiento de enlaces vivos, necesidad de musculación/running. Medir uso/retención real, entrevistas y pago piloto efectivo; intención verbal no es demanda comprobada.

## Recomendación comercial

**Piloto Free asistido + Pro de captura con cuota transparente** sobre bitácora y resumen existentes, después de cerrar controles/pago/consentimiento y smoke del destino. No anunciar asistente de historial ni recomendaciones como disponibles. Analítica básica de progreso tipado es la siguiente capa de valor. Ofrecer video/review inicialmente como capacidad de piloto separada si se valida entrega, no como promesa mensual universal.

