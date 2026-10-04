# P1 — Preparación del pipeline para detección futura

Fecha: 2026-10-03, America/Santiago. Análisis y diseño, sin implementación.
Alcance: los cinco faults priorizados en la [validación experimental](P1_FAULT_DETECTION_VALIDATION.md).
Se conservan sus estados NOT_FEASIBLE_CURRENT_PIPELINE y detectable:false.
No se ajustan thresholds, no se modifica biblioteca, UI, feedback ni modelos.

## 1. Evidencia y gaps actuales

Fuentes inspeccionadas: [analyzer.py](../../app/services/analyzer.py),
[biomechanics.py](../../app/services/biomechanics.py),
[RepDetector](../../app/services/exercise_profiles.py), perfiles laterales
[deadlift](../../app/services/exercise_profiles/deadlift.json),
[squat](../../app/services/exercise_profiles/squat_side.json),
[thruster](../../app/services/exercise_profiles/thruster_side.json),
[HSPU](../../app/services/exercise_profiles/handstand_push_up_side.json),
[OHS](../../app/services/exercise_profiles/overhead_squat_side.json) y
[experimentos](../../app/services/experimental_faults.py).
Los perfiles HSPU/OHS existen en el checkout inspeccionado aunque contienen trabajo
local previo; este documento no los modifica ni presupone que estén publicados.

REQUIRED: sin resolverlo no se puede evaluar con suficiente sustento el fault.
IMPORTANT: mejora robustez/cobertura; su ausencia exige restringir el alcance.
NICE_TO_HAVE: ampliación posterior que no bloquea un primer piloto acotado.
La clasificación expresa dependencia técnica, no evidencia de eficacia.

### Contrato actual común

- Se calcula pose aproximadamente a 15 Hz mediante stride redondeado; a 24 fps
  resulta 12 Hz. El tiempo es índice/fps, no PTS verificado del frame.
- Timeline contiene solo samples aceptados; no registra cada intento de tracking
  fallido. Falta denominador para medir cobertura/oclusión real por ventana.
- Se conservan métricas inferiores por lado en left/right y una selección/media
  en active_side. No se conserva visibilidad articular ni coordenadas originales
  en timeline. Los brazos se promedian entre lados válidos sin indicar contribuyentes.
  active_side describe selección inferior, o 'arms' si no hay selección inferior;
  no demuestra calidad de ambos codos.
- _pose_quality toma el máximo entre izquierda/derecha para cada grupo y luego
  promedia grupos. Puede aceptar hombro de un lado y cadera del otro. No equivale
  a probabilidad calibrada de tracking ni a calidad de una cadena completa.
- Los ángulos 2D usan x/y normalizados sin corregir ancho/alto. wrist_lift es
  diferencia de y del encuadre; cambia con zoom/crop. trunk_from_vertical usa la
  vertical de imagen. Ninguna de esas señales corrige perspectiva de cámara.
- RepDetector usa thresholds de conteo, confirma dos samples y admite gaps de
  0.5 s en estos perfiles. Devuelve rep start/bottom/end y extremos de métricas;
  no expone intervalos de fases ni intentos fallidos. Confianza ausente cae a 1.0
  en consume: ese comportamiento no sirve para gates de faults.
- Estados iniciales como lockout son inicialización del contador, no prueba de
  que el atleta esté en esa fase al inicio de un clip.

### Gaps comunes clasificados

| ID | Gap y efecto | Clase | Evidencia de cierre requerida |
|---|---|---|---|
| G1 | No existen intentos y ventanas finales independientes del éxito del conteo | REQUIRED | Intentos completos, incompletos y fallidos etiquetados; segmentación sin exigir extensión correcta |
| G2 | Falta calidad por landmark/cadena y registro de samples inválidos | REQUIRED | Coordenadas, visibilidad, validez, lado y razón de rechazo por sample; cobertura calculable |
| G3 | Geometría angular y desplazamientos dependen del encuadre | REQUIRED | Espacio isotrópico versionado, escala corporal estable, registro de rotación/crop y revisión de vista |
| G4 | No hay baseline de extensión individual revisado | REQUIRED | Calibración separada del intento evaluado, calidad y variabilidad registradas |
| G5 | Ejercicio/vista/variante declarados no están verificados | REQUIRED | Revisión humana inicial; desconocido implica abstención |
| G6 | Tiempo/cadencia/duplicados y pérdida de tracking no tienen contrato completo | REQUIRED | Tiempo fuente trazable, samples únicos, gaps y cadencia efectiva por ventana |
| G7 | Sin dataset etiquetado ni evaluación independiente | REQUIRED | Dataset del apartado 5 y protocolo cerrado antes de evaluar |
| G8 | Media de codos oculta unilateralidad y cambia de contribuyentes | REQUIRED para los tres faults de codo | Métrica y calidad por brazo, sin sustituir un brazo por otro; alcance explícito |
| G9 | Falta estimación de jitter y longitud aparente de segmentos | IMPORTANT | Informe temporal por cadena y prueba de estabilidad sin borrar déficits |
| G10 | Sin monitor de cambio de cámara/encuadre | IMPORTANT | Invalidar calibración o abstenerse ante cambio; revisión manual viable inicialmente |
| G11 | Sin contraste entre vistas simultáneas | NICE_TO_HAVE | Auditoría posterior de proyección, sin exigir nuevos modelos |
| G12 | Sin visualizador interno de anotaciones/fases | NICE_TO_HAVE | Puede sustituirse inicialmente por archivos y revisión externa; no se propone UI ahora |

### Análisis por ejercicio

Índices: hombro 11/12, codo 13/14, muñeca 15/16, cadera 23/24,
rodilla 25/26, tobillo 27/28. Cada tripleta debe pertenecer al mismo lado.
Los riesgos de oclusión siguientes son hipótesis de captura que deben anotarse,
no estadísticas medidas en los cinco videos locales.

| Ejercicio / fases actuales | Landmarks y métricas disponibles | Vista, tracking y estabilidad | Gaps específicos y señal que impide evaluar |
|---|---|---|---|
| Deadlift: lockout → setup → ascent → lockout; hip 115/145/160° | Cadera 11–23–25 o 12–24–26; rodilla 23–25–27 o 24–26–28 como apoyo de fase; hip_angle, knee_angle, trunk_from_vertical, left/right | Lateral conventional revisada; lado estable. Brazos/carga pueden tapar cadera/rodilla; pérdida de lado altera la media. Baseline y geometría faltantes | REQUIRED: final del intento aunque hip <160°, descenso y ventana terminal; G1–G7. IMPORTANT: distinguir subida de cadera y desplazamiento corporal; NICE_TO_HAVE: separar first_pull anatómico con evidencia externa |
| Air squat: perfil squat lockout → descent → bottom → ascent → lockout; knee 145/115/135/155° | Rodilla 23–25–27 o 24–26–28; hombro/cadera para posición global; knee_angle, hip_angle, trunk_from_vertical, left/right | Lateral sin carga confirmada, no basta alias squat que también incluye back/front squat. Pierna lejana puede quedar oculta; transición both/left/right cambia señal | REQUIRED: identidad air squat, standing y final sin exigir knee ≥155°, baseline, G1–G7. IMPORTANT: descenso/ascenso por tendencia temporal y altura de cadera normalizada; NICE_TO_HAVE: segunda vista |
| HSPU: lockout → descent → bottom → ascent → lockout; codo 145/100/130/160° e inversión ≥0.5 | Brazos 11–13–15 y 12–14–16; inversión 11–23–27 y 12–24–28; elbow_angle, inverted_body_ratio | Lateral strict revisada; posición invertida y pared pueden ocultar brazo/torso. Requerir ambos brazos reduce cobertura; no rellenar brazo oculto | REQUIRED: final de empuje independiente de ≥160°, métricas por brazo G8, strict confirmado, G1–G7. IMPORTANT: confirmar ciclo por desplazamiento del hombro con muñeca estable; NICE_TO_HAVE: anotación de contacto de cabeza, no necesaria para el fault de codo |
| Thruster: ready → dip → drive → lockout → ready; rodilla 130/145/155°, muñeca 0.08/0.04 | Brazos y piernas completos: 11–13–15/12–14–16, 23–25–27/24–26–28; knee_angle, hip_angle, wrist_lift, elbow_angle | Lateral barbell revisada; barra/front rack pueden ocultar muñeca/codo; transición rápida y media bilateral. wrist_lift cambia con escala | REQUIRED: front_rack, squat_descent, bottom, press y final independientes; G1–G8. El conteo final no exige ángulo de codo: puede incluir un fault, pero no proporciona su ventana. IMPORTANT: resolver solapamiento drive/press; NICE_TO_HAVE: trayectoria de carga verificada |
| OHS: lockout → descent → bottom → ascent → lockout; rodilla 145/115/135/155°, muñeca ≥0.08 y codo ≥155° en todas las transiciones | Mismos brazos/piernas que thruster; knee_angle, hip_angle, wrist_lift, elbow_angle | Lateral barbell, overhead confirmado; agarre ancho y brazo lejano producen proyección/oclusión. Rachas cortas pueden perderse a 12 Hz | REQUIRED: segmentar squat sin exigir codo ≥155°; G1–G8; distinguir salida voluntaria de overhead. IMPORTANT: jitter y duración continua de fase; NICE_TO_HAVE: revisión multivista del agarre |

La escala/cámara, el baseline individual y la resolución/FPS aplican a los cinco;
no se resuelven usando thresholds del perfil como calibración del atleta.

## 2. Diseño de una capa explícita de fases

Capa adicional futura, compatible con el contador: no sustituye sus estados ni
usa repetitions_detected como universo de intentos. Consume muestras trazables,
calibración y contexto revisado; produce intervalos incluso si no se cuenta rep.
Estados auxiliares comunes: unknown, partial_attempt, tracking_lost y ambiguous.
No forzar una fase al principio/final del clip ni cruzar pérdidas de tracking.

Contrato propuesto por intervalo: attempt_id, exercise_id, variant, phase,
start_s/end_s, boundary_uncertainty_s, evidence, valid_sample_ids,
phase_confidence_kind, phase_review_status y rejection_reasons.
Por intento: observed_start, observed_end, complete_observation y outcome_unknown.
Completo significa que se observa el intento y su terminación/retorno, no que
alcance un ángulo correcto. lockout es una etiqueta revisada de posición; para
evaluar extensión incompleta se usa terminal_extension/terminal_press, incluyendo
intentos que nunca llegan a lockout. Esa distinción evita selección circular.

Tendencias de ángulos y posiciones deben calcularse en tiempo real de muestras,
con histéresis y persistencia temporal a validar. Derivadas y alturas normalizadas
son señales propuestas, no métricas de fase ya implementadas. Smoothing debe
guardar señal original y latencia; no interpolar para fabricar evidencia.

| Ejercicio | Fases objetivo | Evidencia candidata y límites de separabilidad actual |
|---|---|---|
| Deadlift | setup → first_pull → extension → terminal_extension/lockout → descent | Flexión estable, apertura hip/knee y su tendencia sugieren inicio/extensión; máximo seguido de retorno delimita final retrospectivamente. first_pull no se separa fiablemente de extension solo por thresholds actuales ni se prueba despegue de barra: mantener ascent agregado/unknown hasta evidencia etiquetada. Descent falta como intervalo |
| Air squat | standing → descent → bottom → ascent → terminal_extension/lockout | knee decreciente/creciente y extremo local son candidatos; standing requiere contexto y estabilidad. Altura de cadera sería corroboración futura. Bottom puede ser instante con incertidumbre, no pausa inventada; final por fin de ascenso/retorno, sin exigir rodilla extendida |
| HSPU strict | inverted_ready → descent → bottom → ascent → terminal_press/lockout → descent/exit | Inversión y codo orientan ciclo; hombro respecto a muñeca aportaría evidencia adicional del empuje. Media de codos actual no resuelve lados; no demuestra strict ni contacto. Final/exit requiere revisión si no hay reversión clara |
| Thruster | front_rack → squat_descent → bottom → drive → press → terminal_press/overhead_lockout → return | Rodilla y muñeca permiten hipótesis de squat/overhead; no prueban rack de barra. Drive y press pueden solaparse: permitir intervalos etiquetados por componente, no imponer corte único. Separación fina bloqueada sin alturas normalizadas por lado y anotaciones |
| OHS | overhead_ready → descent → bottom → ascent → standing_overhead → exit | Rodilla guía squat, muñeca/contexto revisado sostienen overhead. No gatear fases con elbow_angle: es la variable evaluada. Exit/regrip anotados para excluir bajada voluntaria; wrist_lift sola no demuestra control de barra |

Con señales actuales se pueden formular candidatos de tendencia y extremos;
no se autoriza implementar segmentación automática fina. MVP viable primero:
intervalos manuales revisados con incertidumbre y ciclos completos, luego validar
segmentación gruesa en modo offline. La fase desconocida siempre impide evaluar.

## 3. Quality gates previos a todo fault

Contrato futuro: gate pass/fail/unknown con evidencia por ventana y motivo.
fail y unknown implican abstención, nunca 'técnica correcta'. No convertir scores
de MediaPipe o del segmentador en probabilidades de acierto sin validación.
Los números siguientes conservan las restricciones experimentales como punto de
partida de evaluación; no son estándares validados ni modificaciones del código.

| Gate | Regla mínima propuesta | Clase y razón de abstención |
|---|---|---|
| Identidad/vista/variante | Revisión humana: lateral compatible y variante exacta; cámara estable y calibración vigente | REQUIRED; incompatible_or_unverified_context |
| Landmark confidence | Visibilidad ≥0.75 en cada landmark requerido del mismo lado; score global ≥0.8 solo adicional. Ausencia nunca vale 1 | REQUIRED; missing_or_low_joint_quality |
| Cadena/métrica | Coordenadas finitas, segmento no degenerado; hip/knee por lado fijo; brazos por lado con contribuyente explícito | REQUIRED; invalid_chain_or_metric |
| Frames y duración | ≥3 samples válidos únicos y ≥0.25 s de evidencia continua; ambas condiciones. Un frame duplicado no incrementa evidencia | REQUIRED; insufficient_evidence |
| Cadencia y cobertura | Tiempos monotónicos; gap ≤0.12 s y margen de bordes ≤0.12 s. Medir FPS efectivo; nominal no basta | REQUIRED; temporal_gap_or_uncovered_boundary |
| Oclusión máxima | 0 samples inválidos dentro de la racha usada y de la ventana final evaluada; no rellenar. Fuera de esa ventana, toda oclusión que cruce inicio/bottom/final vuelve intento desconocido | REQUIRED; occluded_evaluation_or_phase |
| Estabilidad temporal | Mismo lado/persona y encuadre; conservar jitter y cambios de longitud. Si la incertidumbre angular alcanza la banda de decisión, abstenerse | REQUIRED para estabilidad de identidad; IMPORTANT para cuantificar jitter; unstable_or_uncertain_signal |
| Movimiento completo observado | Inicio, recorrido y terminación/retorno revisados; no exigir rep exitosa. Clip truncado o abandono ambiguo se abstiene | REQUIRED; incomplete_observation |
| Fase fiable | Ventana revisada por humano al inicio. Automatización posterior solo con score/boundaries validados en atletas separados; no fijar arbitrariamente '0.8 = fiable' | REQUIRED; phase_unknown_or_ambiguous |
| Calibración | Baseline independiente, misma geometría/lado/variante, calidad suficiente y variabilidad compatible con decisión | REQUIRED; invalid_or_missing_calibration |

Para HSPU añadir inversión revisada; para thruster/OHS contexto overhead revisado.
Los gates existentes inverted_body_ratio ≥0.5 y wrist_lift ≥0.08 son evidencia
auxiliar experimental, no verificación suficiente de ejercicio/fase. Los tres
faults de codo conservan inicialmente alcance bilateral con ambos brazos visibles;
una futura evaluación unilateral requeriría contrato y validación específicos.
Una vista lateral que oculta sistemáticamente el brazo lejano debe abstenerse:
no relajar gate ni cambiar de vista sin validar sus ángulos.

La racha OHS puede estar dentro de un intento observado completo; debe conservarse
continuidad y no concatenarse a través de ruido. Los finales de los otros cuatro
requieren toda la ventana terminal válida y considerar una extensión correcta tardía.
La incertidumbre de límites no debe mezclar empuje normal o retorno con el final.

## 4. Calibración mínima viable propuesta

| Factor | Necesidad y estrategia | Clase |
|---|---|---|
| Geometría/resolución | Convertir x/y a coordenadas isotrópicas del frame fuente (x·width, y·height) antes de ángulos; registrar resize, crop y rotación. No reutilizar thresholds calibrados en la escala antigua sin nueva validación | REQUIRED |
| Escala corporal | Mediana robusta de longitud de torso/segmentos visibles en captura revisada; normalizar desplazamientos por esa escala, guardar dispersión y lado. No usar altura del encuadre | REQUIRED para fase con desplazamientos/overhead |
| Orientación cámara | Captura lateral fija con cuerpo/cadenas completos; revisor confirma plano compatible. La pose 2D sola no certifica yaw ni perspectiva | REQUIRED |
| Inclinación/plano | Registrar roll de cámara y vertical de referencia del entorno revisada para posiciones/torso. Un ángulo entre segmentos es invariante a roll en espacio isotrópico, pero wrist_lift/inversión no lo son. Rotar no corrige perspectiva fuera del plano | REQUIRED para señales direccionales; IMPORTANT cuantificar residual |
| Ángulos base/atleta | Referencia independiente de extensión cómoda y prevista para esa variante, por lado; guardar mediana, dispersión y revisión. Nunca calibrar sobre el máximo del mismo intento defectuoso | REQUIRED |
| FPS/tiempo | Guardar FPS nominal/efectivo, timestamps fuente y política CFR/VFR; rechazar cadencia insuficiente. Verificar PTS antes de usar VFR; no inventar precisión subframe | REQUIRED |
| Diversidad corporal | Baseline individual, rango prescrito/adaptado explícito; fuera de alcance abstenerse. Medir desempeño por atleta y captura sin interpretar anatomía clínica | REQUIRED para contexto; IMPORTANT para cobertura |
| Geometría multivista/3D | Auditoría opcional posterior de perspectiva con recursos existentes; no asumir que z de pose es calibración métrica | NICE_TO_HAVE |

Secuencia MVP de adquisición futura: comprobar cámara/encuadre/variante; grabar
2–3 s de referencia estable con ≥20 muestras únicas válidas y repetirla en tres
capturas breves del mismo contexto. Para HSPU, referencia invertida solo si es
práctica y segura; si no puede obtenerse, no sustituir por extensión de pie sin
validación de transferencia. Revisar postura de referencia y ROM prescrito;
calcular calidad/variabilidad por lado; versionar y ligar al video/atleta.
Estos tiempos/cantidades son un protocolo candidato de captura, no thresholds
del detector. No pedir al atleta que provoque un fallo ni fijar objetivos clínicos.

Invalidar ante zoom, crop, rotación, cambio de cámara, vista, variante o tracking
de persona; al principio la revisión manual puede hacerlo. Evaluar repetibilidad
antes de construir un baseline automático. No cambiar 10° ±5° ni 0.25 s para
compensar una calibración mala; incertidumbre alta obliga a abstención.

## 5. Dataset mínimo etiquetado

No se construye ni descarga aquí. Objetivo de adquisición con material autorizado:
**25 intentos por fault = 125 unidades fault/intento**. Un clip puede aportar
varios intentos, pero no cuentan duplicados como evidencia independiente.

| Fault | Correctos | Claramente incorrectos | Limítrofes | Ventana anotada |
|---|---:|---:|---:|---|
| Deadlift / incomplete_hip_extension | 10 | 10 | 5 | Ciclo y terminal_extension |
| Air squat / incomplete_knee_extension | 10 | 10 | 5 | Ciclo y terminal_extension |
| HSPU strict / incomplete_elbow_lockout | 10 | 10 | 5 | Ciclo invertido y terminal_press |
| Thruster / incomplete_elbow_lockout | 10 | 10 | 5 | Squat/drive/press y terminal_press |
| OHS / sustained_elbow_flexion | 10 | 10 | 5 | Squat overhead y racha de flexión |

Correcto/incorrecto son etiquetas de coach sobre el movimiento visible en el
alcance definido; no se asignan por comparación con el threshold experimental.
Limítrofe incluye duración/amplitud dudosa o desacuerdo técnico, con motivo; mala
calidad se registra aparte y no sustituye los 5 casos limítrofes técnicos.
Añadir un conjunto de exclusiones/abstenciones (oclusión, parcial, vista incorrecta,
wrong exercise, duplicados, ruido) separado de estos 125 casos evaluables.

Esquema mínimo por unidad:

| Grupo | Campos requeridos |
|---|---|
| Identidad | case_id, fault_id, exercise_id, variant, athlete_id seudónimo, session_id, source_id/hash, autorización de uso |
| Captura | view y revisión, width/height, fps nominal/efectivo, duración, timestamps fuente, cámara/rotación/crop, calidad blur/iluminación/oclusión |
| Anotación temporal | attempt_start/end_s, fase y phase_start/end_s, fault_start/end_s o null si ausente, incertidumbre de cada borde |
| Etiqueta | correct/clearly_incorrect/borderline, razón observable, evaluable true/false y razón de exclusión, annotator_ids, desacuerdo y adjudicación |
| Pose | modelo/versión/hash, sample_ids/timestamps, landmarks disponibles por lado, coordenadas/visibilidad/validez, gaps, métricas y versión geométrica |
| Calibración | calibration_id, captura separada, revisión, baseline por lado, variabilidad, ámbito de validez |
| Evaluación | split, detector/version congelados, expected, observed, evidence, confidence_kind, abstention_reason |

No deducir fault_start del inicio del clip. En ausentes timestamp de fault es null;
en limítrofes la incertidumbre y el desacuerdo quedan visibles. Dos coaches anotan
independientemente, sin ver salida/threshold del detector; adjudicar diferencias
y conservar ambas etiquetas. El contexto de fase también necesita revisión.

Muestreo mínimo sugerido por fault: ≥5 atletas, ≥2 sesiones/capturas cuando sea
posible; ningún atleta aporta más de 5 de los 25 casos. Cada clase debe repartirse
entre atletas, sin asociar una cámara a una sola etiqueta. Si no se consigue
diversidad suficiente, registrar el sesgo y no generalizar resultados.
Partición por atleta, nunca por frame/rep del mismo atleta: desarrollo y evaluación
retenida; al menos dos atletas solo para evaluación y representación de las tres
clases en ambos conjuntos. Baseline personal de esos atletas es entrada de captura,
no material para ajustar el algoritmo. Congelar selección y protocolo antes de
reproducir detectores; no cambiar split para mejorar resultados.

125 casos es un mínimo exploratorio, no prueba de seguridad ni suficiencia
estadística para piloto. Registrar FP/FN, abstenciones y cobertura por clase,
fault, atleta/vista; no contar abstención como TN ni ocultarla excluyendo videos.
Medir también error de límites de fase y sensibilidad a calibración independiente.
Con pocos negativos, cero FP observados no demuestra riesgo cero. Criterios de
piloto deben acordarse antes de evaluación; ampliar datos si incertidumbre persiste.
Los 5 videos únicos previos están UNLABELED y no cumplen automáticamente cupos.
Las 25 abstenciones previas no validan desempeño de detección.

## 6. Orden recomendado de implementación futura

Cada paso requiere una fase posterior autorizada; el presente documento no lo ejecuta.

1. **Cerrar contrato de datos (G2/G6/G8).** Persistencia trazable de samples válidos
   e inválidos, calidad por cadena, métricas por lado y tiempo fuente; versiones.
   Verificar que no altera conteo/feedback actual con tests de compatibilidad.
2. **Preparar protocolo y comenzar dataset (G5/G7).** Revisión de vistas/variantes,
   anotación manual de intentos/fases/faults y split por atleta antes de automatizar.
3. **Corregir geometría y capturar calibración (G3/G4).** Primero modo offline y
   comparación de escalas; no migrar thresholds existentes de forma implícita.
4. **Validar quality gates.** Ensayar pérdidas, lados, duplicados y cambios de
   cámara; auditar abstenciones sobre datos reales sin seleccionar solo buenos clips.
5. **Fases gruesas independientes (G1).** Empezar air squat y deadlift: ciclos,
   reversión y ventana terminal. Mantener first_pull agregado si no separable.
   Comparar intervalos con anotaciones, incluidos intentos que el contador omite.
6. **Fases de brazos.** OHS sin gate de extensión, thruster con drive/press
   potencialmente solapados y HSPU strict/inversión revisados. Validar bilateralidad
   y cobertura real antes de automatizar contexto.
7. **Reevaluar los cinco kernels congelados.** Sin ajustes para forzar positivos;
   medir cobertura, FP/FN y error temporal en evaluación retenida. Cambios de
   algoritmo requieren hipótesis documentada y nueva evaluación independiente.
8. **Decidir readiness.** Solo después de resolver contratos puede pasar a
   NEEDS_MORE_DATA; READY_FOR_PILOT exige evidencia real y criterios acordados.
   Cambio detectable:true y feedback quedan como decisiones posteriores separadas.

El orden favorece aprender con señales inferiores antes de la mayor oclusión y
ambigüedad de los brazos; no afirma que alguno ya sea detectable con confianza.

## 7. Qué habilitaría nuevamente cada fault

| Fault | Dependencias indispensables para reabrir evaluación | Evidencia que aún deberá producirse |
|---|---|---|
| Deadlift: cadera final | G1–G7; terminal independiente de hip ≥160°, misma cadena y baseline hip isotrópico, conventional revisado | Ventanas finales correctas e incompletas, retorno y clips parciales; desempeño retenido con calibración repetida |
| Air squat: rodilla final | G1–G7; air squat confirmado, final independiente de knee ≥155°, baseline knee por lado | Fases completas sin exigir extensión, negativos de ascenso en curso y atletas separados |
| HSPU strict: codo final | G1–G8; ambos brazos por lado, strict/inversión y final revisados, baseline en contexto invertido | Cobertura real con pared/oclusión, separación final/exit y asimetrías; validar si alcance bilateral resulta útil |
| Thruster: codo final | G1–G8; geometría/escala overhead, press final independiente del conteo, rack/variante revisados | Drive/press/retorno anotados, lockout parcial sostenido y extensión tardía; robustez a encuadre |
| OHS: flexión sostenida | G1–G8; fases squat sin exigir extensión de codo, brazos visibles, overhead/exit revisados | Rachas continuas durante squat frente a regrip/escape, gaps y perspectiva de agarre ancho |

Resolver un gap habilita una evaluación, no garantiza un resultado positivo de
factibilidad. Si la lateral no permite calidad bilateral, o si el final no se
separa de un movimiento todavía en curso, corresponde conservar abstención y
NOT_FEASIBLE_CURRENT_PIPELINE para ese alcance. No se propone añadir modelos.

## Verificación de esta entrega

Solo se agrega este Markdown. Se contrastaron estados, señales, gates y salida
con el código del checkout y con la validación cerrada (434 Python verdes).
No se reejecuta la suite para un cambio exclusivamente documental; no hay nuevas
mediciones sobre videos ni nuevas etiquetas. Revisión de enlaces locales y
git diff --check antes del cierre.
