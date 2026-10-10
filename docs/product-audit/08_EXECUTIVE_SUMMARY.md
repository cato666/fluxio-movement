# Resumen ejecutivo — Fluxio Movement

Auditoría al **9 de octubre de 2026**, America/Santiago. Alcance: workspace actual de `codex/bitacora-entrenamiento`, HEAD `97583b5c191fd48d4282ad42d0b020d6cb1709a1`, incluyendo cambios previos sin commit. Solo se crearon los ocho documentos de auditoría; no se modificó código funcional, ni se migraron bases del producto, ni se usó IA de pago o envió WhatsApp real.

## Estado general

Fluxio ya es una **bitácora asistida con revisión técnica de video y coaches**. Está construida buena parte de “registrar con mínimo esfuerzo”: manual, foto, audio y WhatsApp, revisión/confirmación, historial editable y recap semanal compartible. La parte de “transformar historial en información para mejorar” está mucho menos desarrollada: hay estadísticas semanales y feedback técnico puntual, pero no PR, tendencias de cargas/resultados, objetivos ni asistente general del historial.

Inventario: **57 funcionalidades**, 29 Implementadas, 16 Parciales y 12 No existe según alcance revisado; ninguna categoría global Solo documentada. Hay contratos/planes futuros dentro de módulos parciales, identificados como tales. Estas categorías describen código, no porcentaje comercial terminado ni certificación de producción.

## Funcionalidades listas como capacidad técnica

- Login/logout por contraseña, roles y ownership; alta asistida por coach/admin.
- Diario manual con fecha, resultado, RPE, notas/adaptaciones, editar/eliminar y fotos privadas.
- Interpretación de texto/pizarra y dictado; borrador editable con guardado explícito.
- WhatsApp con vinculación, captura texto/foto/audio, corrección/confirmación, notas y comandos de semana.
- Resumen factual por semana, días activos/esfuerzo, enlaces vivos con vencimiento/revocación y fotos autorizadas.
- Análisis de video por ejercicio/vista soportados, repeticiones/métricas y sugerencias IA; solicitud/review de coach y feedback temporal.
- Biblioteca de 20 ejercicios: **7 supported, 13 reference_only**; presencia de referencia no significa detector completo.
- Administración y políticas de consumo **locales**, con auditoría; esto no equivale a facturación/subscripción.

“Lista” se limita a implementación y validación indicada en el inventario. IA real actual, canal WhatsApp de producción y precisión universal de video **No verificado**.

## Funcionalidades parciales y ausentes

Parciales: calendario limitado a semanas, constancia sin tendencia, multimedia sin archivo durable de audio, preguntas al historial solo mediante comandos semanales, comunicación coach sin chat/alertas, Free/PAID sin billing, quotas no uniformes por canal, accounting sin costos reconciliados y lifecycle/monitoreo incompletos. Faltas biomecánicas experimentales no entran al pipeline productivo.

Ausentes: autorregistro/recovery como autoservicio, perfil/preferencias deportivas, PR, evolución de carga/score, comparación WOD, metas, asistente longitudinal, recomendaciones del historial, landing personal permanente, desafíos/red social, suscripción/pagos e integraciones con dispositivos. Musculación/running aceptan texto libre, pero no tienen mediciones/dashboards específicos.

## Evidencia de funcionamiento y despliegue

| Evidencia actual | Resultado / alcance |
| --- | --- |
| Python dirigido | **85 aprobadas**, PostgreSQL desechable y providers fixture |
| Python completo | **479 aprobadas, 1 omitida**, 3 avisos de deprecación; omitida exige dominio público explícito |
| JavaScript | **65/65 aprobadas**, APIs simuladas y pruebas de UI/estado |
| E2E web actual | **6 recorridos PASS**: texto/foto/audio, análisis y solicitud, review coach, feedback atleta; HTTP/DB/FFmpeg reales, IA/pose fixture |
| E2E semanal actual | **PASS**: navegación, sharing, fotos anónimas autorizadas, desktop/mobile emulados y revocación |
| Health/API schema Easypanel | **200 / ready**; no identifica commit ni migración SQL exacta |
| OpenAPI remoto | **59 rutas**; bitácora/semanal/WhatsApp/catálogo presentes; **admin, account plan y DELETE de análisis ausentes** |
| OpenAPI local 8000 y 8001 | **67 rutas**, con administración/plan presentes |
| WhatsApp real | Evidencia histórica sandbox del 03-10: texto/foto/audio/combinado, persistencia, doble Guardar textual y revisión humana móvil; no repetida en auditoría |

La prueba omitida no valida comandos contra dominio real; el E2E web no valida OpenAI/Kapso reales. La historia documental del 04-10 decía que Weekly no estaba publicado: hoy **sí aparece su contrato remoto**. No se puede inferir paridad de workspace/producción por health saludable.

## Problemas críticos

1. **No hay suscripción/cobro** y los planes locales no aparecen en el contrato remoto; defaults permiten IA en ambos planes.
2. **WhatsApp evita las cuotas del adaptador web**. También falta verificar User.is_active en la resolución de identidad; riesgo inferido de cuenta desactivada operando por chat.
3. **Compartición automática tras Guardar en chat** crea enlace público vivo si hay base válida; futuras fotos/notas de la semana entran bajo ese permiso. Se debe revisar elección/consentimiento antes de abrir comercialmente.
4. **Alta/seguridad/relaciones aún de MVP**: sin autorregistro/recovery/rate limit login visible, seed recrea contraseñas demo y coach puede listar todos los atletas/subir a sus IDs sin relación explícita. Configuración productiva de secretos no verificada.
5. **Historial no comparable**: programación/ejecución/cargas/score principalmente texto, sin disciplina ni ejercicio canónico. PR/asistente sobre esto podrían dar conclusiones erróneas.
6. Operación: video en BackgroundTasks no durable, cuota reservada antes de fallos, historia limitada a 200, lifecycle de fotos web y costos/backup/alertas sin cierre.

Los riesgos inferidos se distinguen de fallas reproducidas; no se realizaron ataques, cobros, mensajes ni modificaciones remotas.

## Cinco mejoras de mayor impacto propuesto

1. Activación/recuperación y permisos/cuenta activa consistentes.
2. Captura más corta con intención de nota/fechas claras, confirmación y compartir explícito.
3. Datos ejecutados tipados, PR y evolución verificables.
4. Pro con entitlement transversal, pagos/conciliación y costos/limites observados.
5. Metas de constancia y resumen mensual factual que motiven volver al historial.

Impacto y diferenciación son **hipótesis**, no demanda demostrada; dependencias y evaluación por candidata en [05](05_PRODUCT_GAPS.md).

## Próximo MVP comercial recomendado

**Free:** bitácora manual, estadísticas básicas y resumen semanal. **Pro de captura:** interpretación de texto/fotos y dictado, con cupo transparente definido tras medir costos; WhatsApp bajo el mismo entitlement. Usar como hipótesis los precios solicitados: **$3.990 CLP/mes**, fundador **$2.990 CLP/mes**. No se inventan margen, conversión o disposición a pagar.

Antes de cobrar: cerrar pagos/cancelación, gating web/chat, consentimiento/share, cuenta/seguridad, medición de costos y smoke de la release exacta. No anunciar todavía “historial inteligente” ni recomendaciones. Video/coach pueden pilotearse como capacidad separada hasta validar precisión, límites y entrega humana; no prometer revisión mensual universal por existir el workflow.

Después de estabilizar captura/comercialización, desarrollar progreso tipado CrossFit/fuerza y luego musculación/running. Reutilizar servicios y módulos actuales; no reconstruir OCR, voz, bitácora, recap, coaches ni catálogo.

## Riesgos principales y decisiones pendientes

Calidad/atribución IA, falsos PR por textos/unidades/variantes, acceso multiusuario/consentimiento, gasto por correcciones y canal WhatsApp, costo/tiempo de coach, pérdida de trabajos al reiniciar y diferencia de versiones desplegadas. La disposición a pagar, valor de análisis mensual, preferencia de canal y demanda multidisciplina requieren validación con usuarios. No hubo investigación comercial externa ni estimación de costos no observados.

## Documentos de soporte

1. [Inventario funcional y evidencia por feature](01_FUNCTIONAL_INVENTORY.md)
2. [Diez recorridos reales y fricciones](02_CURRENT_USER_JOURNEYS.md)
3. [Arquitectura, pruebas y despliegue observado](03_TECHNICAL_ARCHITECTURE.md)
4. [Preparación multidisciplina y transición compatible](04_MULTISPORT_READINESS.md)
5. [Brechas y doce candidatas impacto/esfuerzo](05_PRODUCT_GAPS.md)
6. [Preparación Free/Pro, costos y gates](06_FREE_PRO_READINESS.md)
7. [Roadmap propuesto por fases](07_PRODUCT_ROADMAP_PROPOSAL.md)

