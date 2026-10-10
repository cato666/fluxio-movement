# Brechas y oportunidades de producto

Fecha: 2026-10-09. Hechos de base en [01](01_FUNCTIONAL_INVENTORY.md); arquitectura en [03](03_TECHNICAL_ARCHITECTURE.md). **Toda valoración de impacto, valor para el atleta, diferenciación y mercado es una hipótesis de producto**, no una conclusión demostrada por tests/código. Complejidad expresa tamaño relativo, no plazo ni presupuesto.

## Brechas de la propuesta de valor

“Registrar con mínimo esfuerzo” ya tiene manual/foto/voz/WhatsApp y confirmación, pero alta asistida, saltos de canal, correcciones/reinterpretaciones y fechas limitadas añaden fricción. “Transformar historial en información para mejorar” tiene una semana factual y feedback técnico puntual; carece de PR, tendencias, metas y comparaciones longitudinales. No duplicar OCR/transcripción, catálogo, entrenamiento ni review: evolucionar esos componentes.

| Brecha | Evidencia / impacto | Prioridad propuesta |
| --- | --- | --- |
| Activación sin autonomía | No autorregistro/recovery; alta coach/admin | P1 antes de apertura pública; piloto asistido aceptable si explicitado |
| Plan comercial no aplicado a todos los canales | consume en web, no servicio/WhatsApp; PAID sin billing | P1 antes de cobrar |
| Cuenta desactivada e identidad WhatsApp | resolve no consulta User.is_active | P1 validar y corregir control transversal |
| Consentimiento/alcance social | Chat crea enlace vivo después de guardar; comparte fotos/notas nuevas de semana | P1 separar guardado y compartición explícita |
| Ownership de relación coach-atleta | Coach lista todos los atletas y puede subir a athlete_id | P1 definir permiso/consentimiento para SaaS abierto |
| Conocimiento longitudinal | Carga/resultado textual; sin sport/exercise ID | P1 datos base antes de PR/asistente |
| Historia y lifecycle | 200 filas sin paginar; imágenes web sobreviven a eliminación | P2 antes de crecimiento |
| Calidad de captura | Parser fecha limitado, menú nota, caption ahora sí leído | P2 mejora localizada con medición de correcciones |
| Entrega/operación | Video en proceso, worker sin alertas y costos desconocidos | P1 capacidad/costos antes de prometer análisis mensual |

## Criterios de clasificación

Impacto 1–5: 1 mejora periférica, 3 valor recurrente en un subgrupo, 5 resuelve directamente captura/progreso para gran parte de atletas objetivo. Esfuerzo 1–5: 1 extensión local de contratos/UX, 3 dominio nuevo moderado y varias capas, 5 integración/validación compleja con datos nuevos. Dependencias y riesgo pueden cambiar orden, aunque Impacto/Esfuerzo sea alto.

Diferenciación baja/media/alta es hipótesis sobre singularidad percibida; no se investigó mercado/competidores ni se afirma ventaja competitiva. Valor potencial depende de frecuencia de uso y calidad de historial confirmada.

## Matriz impacto / esfuerzo

| Candidata | Qué existe hoy | Impacto (H) | Esfuerzo | Complejidad | Valor potencial (H) / diferenciación (H) | Orden condicionado |
| --- | --- | --- | --- | --- | --- | --- |
| 1. PR automáticos | No PR; carga puntual y resultados texto | 5 | 3 | Media-alta | Alto / media | Después de medidas/variantes comparables |
| 2. Evolución de cargas/resultados | Diario y semana factual | 5 | 3 | Media-alta | Alto / media | Primer núcleo de progreso |
| 3. Comparación WOD histórico | Bloques sin identidad canónica | 4 | 4 | Alta | Alto en CrossFit / media | Después de definiciones/versiones |
| 4. Objetivos deportivos | objective puntual de video | 4 | 2 | Media | Alto / baja-media | Metas de constancia primero; rendimiento después |
| 5. Resumen mensual inteligente | WeeklySummaryService | 4 | 2 | Media | Medio-alto / media | Factual primero, IA sobre evidencia |
| 6. Asistente del historial | Comandos semanales deterministas | 4 | 4 | Alta | Alto si historial suficiente / media-alta | Después de consultas y permisos robustos |
| 7. Preparación preentrenamiento | Catálogo, history y next_session coach | 3 | 4 | Alta | Medio / media | Validar necesidad/seguridad antes |
| 8. Recomendaciones del historial | IA técnica puntual y coach | 4 | 5 | Alta | Alto condicionado / alta | Requiere longitudinal y revisión experta |
| 9. Análisis técnico video | Ya implementado para perfiles cubiertos | 4 | 3 | Media-alta para endurecer | Alto en segmento técnico / media-alta | Reutilizar; no reconstruir; validar precisión/capacidad |
| 10. Dispositivos deportivos | Ninguna integración | 3 | 5 | Alta | Medio-alto en running / baja-media | Posterior a modelo running y demanda |
| 11. Registro rápido/confirmación automática | OCR/voz/chat y confirmación explícita | 5 | 2 | Media | Alto / media | Reducir pasos; auto-confirmar solo opt-in acotado |
| 12. Musculación y running | Registro libre sin métricas/deporte | 4 | 4 | Alta | Alto si expansión validada / media | Musculación antes; running mínimo después |

Quick wins propuestos: 11, 4 orientado a constancia, 5 factual. Inversiones de núcleo: 1/2 tras datos tipados. Posteriores: 3/6/12. Experimentos primero: 7/8/10. La candidata 9 es una capacidad construida que necesita validación, operación y límites; no “feature totalmente faltante”.

## Desarrollo, reutilización, dependencias y riesgos por candidata

### 1. Detección de récords personales

**Reutilizar:** TrainingSession, Analysis.load_kg, catálogo/alias, fechas, ownership, revision de datos. **Desarrollar:** medidas ejecutadas normalizadas, variante, score/Rx, reglas PR versionadas, eventos con evidencia, recalcular ante corrección/eliminación, UI de marca posible/confirmada. **Dependencias:** identidad de ejercicio y equivalencia/unidades (04), no LLM obligatorio. **Riesgos:** confundir programación con resultado; kg/lb, rep max frente a serie, WOD distinto, error OCR, backfill inventado. **Valor/diferenciación (H):** progreso visible con confianza puede elevar retorno recurrente; PR genérico por sí solo no demuestra ventaja.

### 2. Evolución de cargas y resultados

**Reutilizar:** misma bitácora/fechas y cuota de datos autorizados, UI semanal como punto de entrada. **Desarrollar:** consultas por ejercicio/score, unidades, volumen por sets, gráficos con muestra y filtros, no extrapolación de faltantes. **Dependencias:** contratos tipados e historia paginada; métricas deterministas. **Riesgos:** cargas de pizarra ≠ carga usada; variantes/Rx mezclados; registros escasos. **Valor (H):** relación directa con visión de evolución; validar comprensión, no solo atractivo visual.

### 3. Comparación de WODs históricos

**Reutilizar:** bloques y prescripción textual, source_text/imagen para evidencia. **Desarrollar:** WorkoutDefinition/version/hash, identificación con revisión, contexto/carga/adaptación, motor de comparación de resultados, UI lado a lado. **Dependencias:** score tipado y programación explícita. **Riesgos:** mismo nombre con esquemas distintos, benchmarks inferidos, time caps e incompletos. **Diferenciación (H):** puede ser útil si ahorra comparación manual y reconoce condiciones reales.

### 4. Objetivos deportivos

**Reutilizar:** conteo de días/sesiones y RPE factual. **Desarrollar:** Goal, plazo/meta/baseline/status, editor y progreso, recordatorios solo con opt-in. Empezar por constancia semanal medible con datos existentes. **Dependencias:** para fuerza/running, medidas de 04; no requiere IA. **Riesgos:** confundir constancia de registro con entrenamiento real, metas poco realistas, fatiga de recordatorios. **Valor (H):** claridad y hábito; verificar retención y ajuste de metas.

### 5. Resumen mensual inteligente

**Reutilizar:** WeeklySummaryService, ownership, componentes recap, uso de IA/modelo/tokens. **Desarrollar:** agregado por mes, comparación con mes anterior y muestra, narrativa trazable/optativa, límites/cache por versión de datos, share específico si se valida. **Dependencias:** basta fechas/RPE para primera versión factual; progreso exige métricas. **Riesgos:** presentar frecuencia como mejora deportiva, narrativa inventada, costos repetidos al abrir. **Valor (H):** reflexión de baja fricción; probar demanda de mensual frente a semanal.

### 6. Asistente conversacional del historial

**Reutilizar:** identidad y servicio compartido, comandos semana, políticas prompt, auditoría de tokens. **Desarrollar:** consultas autorizadas por atleta, herramientas de lectura, filtros, respuestas con fechas/sesiones de evidencia, límites de conversación, evaluación de fidelidad y aislamiento. No es necesario vectorizar todo para preguntas estructuradas iniciales. **Dependencias:** historia completa/paginación y semántica de resultados. **Riesgos:** filtración multiusuario, prompt injection desde notas, alucinación, costos largos. **Valor/diferenciación (H):** alto si responde preguntas repetidas que hoy exigen búsqueda; validar con preguntas reales.

### 7. Preparación personalizada antes del entrenamiento

**Reutilizar:** programación registrada, referencias de ejercicio y recomendación humana next_session. **Desarrollar:** intención preentrenamiento, contexto del día, rutina/recomendación aprobada por especialista, restricciones y evidencia. **Dependencias:** distinguir plan futuro de sesión ejecutada, perfil/metas y validación experta. **Riesgos:** prescripción inadecuada con historia insuficiente, lesión/fatiga no observadas, promesas técnicas. **Valor (H):** validar si el atleta busca preparación en Fluxio o ya la recibe en su box.

### 8. Recomendaciones basadas en historial

**Reutilizar:** feedback de coach, datos/servicios/usage; mantener autoridad humana. **Desarrollar:** baseline longitudinal, reglas/guardrails, explicaciones con evidencia, aceptación/seguimiento, evaluación experta. **Dependencias:** métricas/metas, contexto recuperativo y permiso del usuario, calidad del dataset. **Riesgos:** confundir correlación con causalidad, consejo inseguro, recomendaciones repetitivas. **Diferenciación (H):** potencial alto, pero no listo para ofrecer “coach IA” autónomo.

### 9. Análisis técnico de ejercicios mediante video

**Existe:** pipeline pose/reps/métricas, preflight, razonamiento opcional, momentos priorizados y review humana. **Reutilizar todo ese módulo.** **Desarrollar:** dataset/validación por ejercicio/vista, soporte explícito y experimental separado, capacidad/cola durable, fallos/retry, SLA de coach y cupo mensual ligado al plan. **Dependencias:** cámara/pose, FFmpeg/modelos, recursos CPU/storage, disponibilidad coach. **Riesgos:** tests sintéticos no validan precisión deportiva; referencia de catálogo ≠ detector; video WhatsApp no entra al pipeline. **Valor (H):** alta utilidad para segmento que pide feedback; medir satisfacción y tiempo de coach.

### 10. Integraciones con dispositivos deportivos

**Reutilizar:** auth, futura TrainingSession con sport/mediciones, adaptadores de servicios. **Desarrollar:** OAuth/scopes por proveedor, revocación, import idempotente, sincronización/reconciliación, procedencia y duplicados, export/privacidad. **Dependencias:** APIs/permisos y modelo running/ciclismo; verificar documentación oficial al elegir proveedor. No se recomiendan APIs concretas sin investigar. **Riesgos:** términos/límites cambiantes, doble registro manual-importado, zona horaria, costo de soporte. **Valor (H):** ahorrar captura; validar proveedor realmente usado por segmento objetivo.

### 11. Registro rápido con confirmación automática

**Existe:** captura compacta, título por fecha, foto/voz/chat y propuesta confirmada. **Reutilizar:** compositor/payload/estados, validación y dedupe. **Desarrollar:** medir tiempo/turnos, preservar intención de nota, mejoras de fecha, confirmación de un toque, modo auto opt-in con umbral, reversión y prevención de publicación automática. **Dependencias:** score de completitud definido, idempotencia y medición de error; no confiar en confidence LLM sin evaluación. **Riesgos:** persistir resultados incorrectos, fechas equivocadas, cuota excesiva por corrección. **Propuesta:** primero reducir esfuerzo sin quitar confirmación; auto-confirmación futura solo para casos explícitos de bajo riesgo.

### 12. Soporte para musculación y running

**Reutilizar:** auth, bitácora, captura, semanas, catálogo, algunas capacidades de video. **Desarrollar:** AthleteSport, sport/session type, sets/mediciones/unidades, catálogo fuerza, entrada rápida por series; running distance/duration/pace y contexto; dashboards por deporte. **Dependencias:** arquitectura compatible 04 y validación de nuevas rutinas. **Riesgos:** expandir demasiado antes de resolver CrossFit; interpretación WOD/regex rechaza vocabulario de otros deportes; métricas vacías. **Valor (H):** ampliar utilidad a atletas mixtos, demanda de cada deporte aún no demostrada.

## Validación de hipótesis

Pilotear captura y progreso con atletas y coaches reales: tiempo hasta primer registro, turnos/reinterpretaciones por sesión, porcentaje de propuestas corregidas, error de fecha/carga, sesiones por semana, retorno a 7/30 días, uso de recap, PR comprendidos y confianza. Medir intención/pago efectivo, abandono, disposición a compartir y costo de soporte. No fijar un tamaño de muestra ni tasas de éxito inventadas: acordarlos antes del experimento con baseline observado.

