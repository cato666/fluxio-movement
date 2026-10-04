# Diseño de faults para los siete ejercicios supported

Fecha: 2026-10-03 (America/Santiago). Solo diseño: ningún algoritmo, fixture,
modelo, flag, referencia o estado del catálogo se modifica.

**Todos los faults de este documento tienen `detectable: false`.** Las prioridades
son prioridades de investigación/implementación futura, no promesas de detección.
Los trece ejercicios reference_only quedan fuera de esta fase.

## Evidencia y límites del pipeline actual

Fuentes de código:

- [analyzer.py](../../app/services/analyzer.py): `LANDMARK_GROUPS`, `_pose_quality`,
  `_pick_metrics`, `_press_metrics`, `_inverted_metrics`, `_front_deadlift_metrics`,
  construcción de `timeline` y muestreo aproximadamente a 15 Hz.
- [biomechanics.py](../../app/services/biomechanics.py): ángulos 2D de rodilla,
  cadera y línea hombro–cadera respecto de la vertical de imagen.
- [exercise_profiles.py](../../app/services/exercise_profiles.py): máquina de
  estados; emite repeticiones completadas, no intentos fallidos ni fases técnicas
  completas. `bottom_s` es el instante de confirmación del estado, no necesariamente
  el mínimo biomecánico. En clean/snatch, los estados no separan todos los tirones.
- [Perfiles JSON](../../app/services/exercise_profiles): métricas y thresholds de
  conteo; **sus thresholds no son umbrales validados de faults**.
- [Tests de perfiles](../../tests/test_exercise_profiles.py): secuencias sintéticas
  verifican conteo, confianza y gating; no validan faults contra video real.

Los grupos disponibles son hombro, codo, muñeca, cadera, rodilla y tobillo, ambos
lados. La pose bruta existe temporalmente; las coordenadas articulares y la
visibilidad por articulación NO se persisten en timeline. Sí se guardan `left`,
`right`, `active_side`, métricas fusionadas y `pose_confidence`. Los ángulos de
codo se promedian entre brazos válidos; no hay codo por lado persistido.

`_pose_quality` toma la mejor visibilidad de cada grupo, incluso de lados distintos.
Un promedio alto no asegura que todos los puntos de una cadena sean visibles.
Las métricas `left`/`right` no garantizan por sí mismas confianza de ese lado.
Para un fault futuro será necesaria calidad de **la misma cadena** y continuidad.

Las funciones calculan ángulos sobre x/y normalizados por ancho/alto distintos:
la geometría puede distorsionarse con la relación de aspecto. Antes de validar
umbrales físicos hay que estudiar una representación con escala isotrópica
(píxeles o corrección equivalente), y recalibrar sin alterar ahora el baseline.
`wrist_lift` tampoco es una distancia física: cambia con encuadre y escala.
`inverted_body_ratio` indica orden invertido de segmentos, no rectitud de columna.

No hay barra, discos, suelo, caja, pared, contacto, fuerza ni centro de presión
detectados. MediaPipe hip no es pliegue de cadera; knee no es borde superior de
rodilla. Hombro–cadera describe inclinación global, no curvatura lumbar. Los
landmarks de pie usados al dibujar no constituyen métricas de contacto validadas.

## Evidencia técnica externa

Estos enlaces sostienen el criterio educativo; **no validan el algoritmo ni los
umbrales propuestos**. Se consultaron en esta revisión. Se parafrasea, sin copiar
instrucciones extensas. No se usa una regla de competición como regla universal.

| Clave | Fuente primaria | Criterio usado |
|---|---|---|
| S1 | [CrossFit: Air Squat](https://www.crossfit.com/essentials/the-air-squat) | Fondo y retorno a extensión; seguimiento de rodillas y postura. |
| S2 | [CrossFit: Overhead Squat](https://www.crossfit.com/essentials/the-overhead-squat) | Sostén overhead con codos extendidos; mecánica de squat. |
| S3 | [CrossFit: Deadlift](https://www.crossfit.com/essentials/the-deadlift) | Extensión final y coordinación inicial de torso/cadera; bajar controlado o soltar la carga puede ser válido. |
| S4 | [CrossFit: What Is a Clean?](https://www.crossfit.com/essentials/foundational-movement-clean-what-is-a-clean) | Flexión temprana de brazos antes de extensión inferior y falta de extensión. |
| S5 | [CrossFit: Missing the Bar Forward in the Snatch](https://www.crossfit.com/pro-coach/ask-a-coach-missing-bar-forward-snatch) | Diferencia entre tirón y recepción; flexión temprana de brazos y extensión del segundo tirón. |
| S6 | [CrossFit: Thruster](https://www.crossfit.com/essentials/the-thruster) | Squat seguido de impulso inferior y press; final con articulaciones extendidas. |
| S7 | [CrossFit: HSPU and You](https://www.crossfit.com/essentials/hspu-and-you-master-the-movement) | Variantes strict, kipping y escaladas requieren contexto separado. |
| S8 | [CrossFit Games: estándar strict HSPU 2019](https://games-assets.crossfit.com/2019-sdfoiwwe09835.pdf) | Ejemplo histórico explícito de extensión de brazos; NO regla vigente universal ni evaluación de no-rep. |
| S9 | [CrossFit: What Is a Snatch?](https://www.crossfit.com/essentials/foundational-movement-snatch) | Trayectoria y recepción dependen también de la barra. |

## Convenciones de diseño y abstención

Cada ficha siguiente declara su `fault_id`, nombre y descripción, categoría,
vista, landmarks, métricas, señal candidata, tolerancia, exclusiones, evidencia,
dificultad y prioridad. Identidad futura: `(exercise_id, fault_id)`. Un ID puede
reutilizarse entre ejercicios con parámetros y fases distintos. No se agregan
estos registros al catálogo todavía.

Condiciones comunes **G**, aplicables a todas las fichas candidatas:

1. Vista lateral real, cámara fija, sujeto completo y vertical de imagen
   razonablemente alineada con gravedad. Frontal/oblicua no se habilita por el
   simple hecho de que el contador la soporte.
2. Cadena articular visible y estable; estudiar gate conservador de visibilidad
   por punto ≥0.75 y confianza global ≥0.8. Son valores de exploración, no calibrados.
   Cambio de lado, blur, cortes, movimiento de cámara y oclusión ⇒ abstención.
3. Calibración de extensión observable del atleta durante posiciones válidas,
   en el mismo encuadre y variante, revisada por coach. Sin calibración adecuada
   ⇒ abstención. No usar la mejor rep de un conjunto defectuoso como verdad.
4. Probar diferencia de 10° respecto a extensión calibrada, con banda de incertidumbre
   de ±5°; confirmar solo fuera de la banda. Estudiar 0.20–0.30 s de continuidad y
   mínimo tres muestras válidas, usando tiempo real, no solo número de frames.
5. Estas tolerancias son hipótesis de ingeniería para fixtures. No diagnostican
   limitaciones anatómicas ni son equivalentes a un estándar de competición.
   Excluir rango adaptado prescrito, variantes, calentamiento y drills parciales.
6. Encontrar intentos/fases sin exigir el mismo bloqueo cuya ausencia se quiere
   evaluar. La ausencia de una rep contada NO prueba un fault. No puntuar un
   intervalo recortado o sin final observable, ni inventar un número de rep.

Las métricas de cada ficha se dividen en **actuales** y **derivaciones/requisitos
futuros**. Aunque los landmarks brutos existen durante el análisis, una derivación
futura no equivale a una señal disponible en resultados guardados.

## 1. air_squat

### `incomplete_knee_extension` — Extensión final de rodilla incompleta

- **Categoría y descripción coach:** extensión. Después de subir, la rodilla
  vuelve a un máximo estable claramente inferior al final calibrado del atleta.
- **Vista / landmarks:** lateral; cadera, rodilla y tobillo de la misma pierna.
- **Métricas:** actual `knee_angle`, `active_side`, tiempo; futuras calidad por
  cadena, ángulo con escala isotrópica y ventana de final independiente.
- **Condición candidata:** ascenso confirmado, seguido de meseta o inversión
  hacia siguiente descenso; máximo final < extensión calibrada −10°.
- **Tolerancia:** G; meseta estable ≥0.20 s. Si el atleta no pausa, evaluar máximo
  temporal con incertidumbre; sin suficientes muestras, abstenerse.
- **NO detectar:** bottom, descenso, rep aún subiendo, video que termina durante
  ascenso, squat parcial prescrito, giro de cámara o adaptación de movilidad.
- **Evidencia / dificultad / prioridad:** S1 y contador squat; media por cierre
  de intentos; **P1**. `detectable: false`.

### `limited_squat_excursion` — Recorrido de squat reducido respecto al objetivo

- **Categoría y descripción coach:** rango. Menor flexión observable que la
  profundidad objetivo individual revisada por coach; no afirmar pliegue bajo rodilla.
- **Vista / landmarks:** lateral; cadera, rodilla, tobillo; hombro como contexto.
- **Métricas:** actual mínimo `knee_angle`; futura ventana de descenso/ascenso
  independiente, calidad y objetivo personal corregido geométricamente.
- **Condición candidata:** mínimo de rodilla > mínimo objetivo +10° en un intento
  completo observado. No exigir transición al `bottom` del contador.
- **Tolerancia:** G; vecindad de mínimo ≥3 muestras, explorar margen 10–15°.
- **NO detectar:** box squat, rehab, target elevado, objetivo no registrado,
  pierna oculta, cámara frontal; ángulo solo no verifica profundidad reglamentaria.
- **Evidencia / dificultad / prioridad:** S1; media-alta; **P2**.
  `detectable: false`. No sustituye al fault actual `insufficient_depth`.

## 2. overhead_squat

### `sustained_elbow_flexion` — Flexión sostenida de codos en posición overhead

- **Categoría y descripción coach:** bloqueo. Un brazo pierde extensión de forma
  sostenida mientras la carga se mantiene sobre la cabeza durante el squat.
- **Vista / landmarks:** lateral, brazo entero visible; hombro, codo, muñeca;
  cadera, rodilla y tobillo para fase y contexto.
- **Métricas:** actuales `elbow_angle`, `wrist_lift`, `knee_angle`; futuras ángulo
  y confianza por brazo, altura relativa a torso y fase independiente del gating overhead.
- **Condición candidata:** brazo en overhead previamente establecido, flexión
  >10° respecto al bloqueo calibrado durante descenso/fondo/ascenso.
- **Tolerancia:** G, ≥0.25 s, banda ±5°. Muñeca alta es contexto, no prueba de barra estable.
- **NO detectar:** bajada voluntaria de barra antes/después de la rep, agarre
  amplio que oculte el brazo, escape seguro del implemento, ejercicio distinto.
- **Evidencia / dificultad / prioridad:** S2; media por métricas de brazo y fase;
  **P1**. `detectable: false`. No equivale a inestabilidad completa del overhead.

### `limited_squat_excursion` — Fondo reducido con carga overhead

- **Categoría y descripción coach:** rango. Fondo inferior al objetivo técnico
  individual observable, manteniendo contexto overhead.
- **Vista / landmarks:** lateral; cadera, rodilla, tobillo y brazo visible.
- **Métricas:** `knee_angle`, `wrist_lift`, `elbow_angle`; futuro objetivo de fondo
  y calidad por cadena. No usar solo reps aceptadas por el perfil overhead.
- **Condición candidata:** mínimo de rodilla > objetivo +10° en descenso/ascenso
  reconocibles; contexto overhead independiente.
- **Tolerancia:** G y vecindad del mínimo ≥3 muestras.
- **NO detectar:** target/ROM adaptado, pérdida deliberada de carga, drill de
  movilidad, un ángulo de rodilla sin fase o video oblicuo.
- **Evidencia / dificultad / prioridad:** S2; alta; **P2**. `detectable: false`.

## 3. deadlift

### `incomplete_hip_extension` — Extensión final de cadera incompleta

- **Categoría y descripción coach:** extensión. El final observado conserva
  flexión de cadera respecto a la postura de pie calibrada; no equivale a espalda redondeada.
- **Vista / landmarks:** lateral; hombro, cadera y rodilla, tobillo de contexto.
- **Métricas:** actuales `hip_angle`, `knee_angle`, `trunk_from_vertical`;
  futuras calidad por cadena y final independiente de `lockout_hip_min`.
- **Condición candidata:** después de ascenso, máximo de cadera en final observado
  < extensión calibrada −10°, con piernas cercanas a su final y siguiente retorno visible.
- **Tolerancia:** G; final ≥0.20 s. Sin meseta/retorno claro, abstención.
- **NO detectar:** setup, rep en curso, RDL/drill, caída de barra segura, limitación
  prescrita, video cortado; nunca exigir retorno lento para declarar correcta una rep.
- **Evidencia / dificultad / prioridad:** S3; media; **P1**. `detectable: false`.

### `early_torso_inclination_increase` — Torso se inclina más al iniciar el tirón

- **Categoría y descripción coach:** posición de torso / rodilla-cadera. Aumento
  temprano de inclinación respecto al setup; sugerencia de coordinación para revisar,
  sin afirmar que se conoce la altura de barra o la causa.
- **Vista / landmarks:** lateral; hombro, cadera, rodilla, tobillo de la misma cadena.
- **Métricas:** actuales `trunk_from_vertical`, `hip_angle`, `knee_angle`;
  futuras fase inicial validada y calidad por cadena. Coordenadas no persistidas
  serían necesarias para comparar velocidades verticales de hombro y cadera.
- **Condición candidata:** durante inicio de ascenso, inclinación aumenta >10°
  frente al setup mientras rodilla se extiende; primero validar ventana inicial
  por coach, porque no hay barra para saber cuándo pasa la rodilla.
- **Tolerancia:** G; incremento sostenido ≥0.20 s; explorar 10–15°.
- **NO detectar:** setup reajustándose, slack pull intencional, sumo/trap bar,
  distinta proporción corporal, movimiento posterior al paso de rodillas.
- **Evidencia / dificultad / prioridad:** S3; alta por fase y significado limitado;
  **P2**. `detectable: false`.

## 4. clean

### `early_arm_bend` — Flexión de brazos antes de la extensión inferior

- **Categoría y descripción coach:** extensión / coordinación. Flexión sostenida
  durante el tirón antes de la máxima extensión de cadera/rodilla, excluyendo third pull.
- **Vista / landmarks:** lateral; hombro, codo, muñeca, cadera, rodilla y tobillo.
- **Métricas:** timeline puede contener `elbow_angle` aunque perfil clean no lo
  agregue a métricas de rep; `hip_angle`, `knee_angle`. Futuros ángulo por brazo,
  calidad, secuencia de extensión y marcador temporal fiable de tirón/recepción.
- **Condición candidata:** caída de codo >10–15° desde brazo largo antes del
  pico de extensión inferior. No usar solo `knee_angle <155`: eso también ocurre
  legítimamente al tirar bajo la barra. Sin separación de fases, no evaluar.
- **Tolerancia:** explorar ≥0.15–0.20 s y ventaja temporal ≥0.15 s sobre extensión;
  mínimo 3 muestras; tirones demasiado rápidos a ~15 Hz ⇒ abstención.
- **NO detectar:** flexión del third pull/catch, hang/drill, arm bend previo
  mantenido sin cambio, oclusión con barra o extensión máxima no capturada.
- **Evidencia / dificultad / prioridad:** S4; alta; **P2**. `detectable: false`.

### `incomplete_stand_extension` — Stand incompleto después de la recepción

- **Categoría y descripción coach:** extensión. No recupera postura erguida
  calibrada después de una recepción reconocida, antes de retorno observado.
- **Vista / landmarks:** lateral; hombro, cadera, rodilla y tobillo.
- **Métricas:** actuales `hip_angle`, `knee_angle`; futuras fase catch/stand
  independiente y calidad. No se confirma soporte en front rack solo con estos puntos.
- **Condición candidata:** tras catch, máximos finales de rodilla o cadera
  permanecen >10° debajo de referencia calibrada y después comienza retorno.
- **Tolerancia:** G; ≥0.20 s de final observable; requerir catch y subida íntegros.
- **NO detectar:** squat de recepción, rep aún subiendo, complejo clean+front squat
  prescrito, power clean, drop seguro o encuadre cortado.
- **Evidencia / dificultad / prioridad:** [The Clean](https://www.crossfit.com/essentials/the-clean-2)
  y perfil clean; alta por inferencia de fase; **P2**. `detectable: false`.

## 5. snatch

### `sustained_elbow_flexion` — Codos flexionados durante sostén overhead

- **Categoría y descripción coach:** recepción / bloqueo. Flexión de brazos
  persistente después de establecer la recepción overhead; no calificar press-out
  bajo reglas de halterofilia.
- **Vista / landmarks:** lateral con brazo visible; hombro, codo, muñeca, cadera,
  rodilla y tobillo para contexto de recepción.
- **Métricas:** actuales de timeline `elbow_angle`, `wrist_lift`, rodilla; futuras
  medidas por brazo, altura normalizada y ventana de catch. El perfil snatch
  de conteo no prueba que la barra haya llegado arriba.
- **Condición candidata:** después de catch confirmado y muñeca sobre hombro,
  déficit de extensión >10° sostenido; excluir flexión normal del tirón.
- **Tolerancia:** G; ≥0.25 s; no interpretar muestras aisladas del turnover.
- **NO detectar:** third pull, bajada de barra, agarre ancho proyectado/oculto,
  intento fallido con escape, muscle/power snatch o pausa de un drill.
- **Evidencia / dificultad / prioridad:** S9; alta por fase y brazos; **P2**.
  `detectable: false`.

### `early_arm_bend` — Brazos se flexionan antes del final del segundo tirón

- **Categoría y descripción coach:** extensión / coordinación. Revisar que los
  brazos no anticipen la extensión de piernas/cadera; no deducir trayectoria de barra.
- **Vista / landmarks:** lateral; hombro, codo, muñeca, cadera, rodilla y tobillo.
- **Métricas:** codo, cadera, rodilla de timeline; futuras por brazo y fases
  first/second/third pull, que hoy no se publican como eventos técnicos completos.
- **Condición candidata:** como clean `early_arm_bend`, restringida al segundo
  tirón y antes de pico de extensión. El turnover normal queda explícitamente fuera.
- **Tolerancia:** diferencia 10–15°, ≥0.15–0.20 s y separación temporal ≥0.15 s;
  no resolver una secuencia más rápida que la incertidumbre de muestreo.
- **NO detectar:** turnover/catch, snatch balance, hang/drill, brazo oculto,
  extensión inferior entre muestras o manos demasiado abiertas para buena proyección.
- **Evidencia / dificultad / prioridad:** S5; alta; **P2**. `detectable: false`.

## 6. thruster

### `incomplete_elbow_lockout` — Extensión final de brazos incompleta

- **Categoría y descripción coach:** bloqueo. El final overhead después del drive
  muestra flexión de codo claramente mayor que la postura de extensión calibrada.
- **Vista / landmarks:** lateral; hombro, codo, muñeca y cadena inferior para fases.
- **Métricas:** actuales `elbow_angle`, `wrist_lift`, `knee_angle`; futuras por
  brazo, altura normalizada, calidad y final de press independiente de conteo.
- **Condición candidata:** squat+drive observados, llegada overhead y máximo de
  codo < bloqueo calibrado −10° antes del retorno de muñecas.
- **Tolerancia:** G; ≥0.20 s o vecindad de pico suficientemente muestreada;
  retorno rápido sin certeza de pico ⇒ abstención.
- **NO detectar:** front rack, press aún en curso, descenso normal, variante
  unilateral, kettlebell/dumbbell con definición distinta, movilidad adaptada.
- **Evidencia / dificultad / prioridad:** S6; media; **P1**. `detectable: false`.

### `early_press` — Press comienza antes de completar impulso inferior

- **Categoría y descripción coach:** extensión / coordinación. Extensión activa
  de codos se adelanta a la extensión inferior, en vez de aprovechar el drive.
- **Vista / landmarks:** lateral; hombro, codo, muñeca, cadera, rodilla y tobillo.
- **Métricas:** actuales codo, elevación de muñeca, rodilla y cadera; futuras
  derivadas suavizadas en tiempo real, separación entre alzada pasiva y press activo,
  y fases con calidad por brazo. La barra saliendo de rack no se observa directamente.
- **Condición candidata:** incremento de codo >10° y elevación sostenida antes
  de extensión inferior calibrada por ≥0.15 s. Solo con evidencia de press activo;
  `wrist_lift` subiendo por sí solo no basta.
- **Tolerancia:** explorar 10–15° y ≥0.15–0.20 s; incertidumbre de muestreo debe
  ser menor que separación temporal.
- **NO detectar:** alzada pasiva por drive, cambio de rack, coordinación correcta
  veloz, variante con mancuernas, rep recortada o codo oculto.
- **Evidencia / dificultad / prioridad:** S6; alta; **P2**. `detectable: false`.

## 7. handstand_push_up

### `incomplete_elbow_lockout` — Extensión final incompleta en HSPU strict

- **Categoría y descripción coach:** bloqueo. Tras el empuje invertido, el brazo
  no vuelve a la extensión observable calibrada antes del siguiente descenso.
- **Vista / landmarks:** lateral; hombro, codo, muñeca, cadera y tobillo.
- **Métricas:** actuales `elbow_angle`, `inverted_body_ratio`; futuras calidad
  por brazo y eventos de final independientes de `lockout_elbow_min`.
- **Condición candidata:** contexto invertido continuo, descenso+ascenso
  observados, máximo final < bloqueo calibrado −10° y nuevo descenso reconocible.
- **Tolerancia:** G; ≥0.20 s o máximo con vecindad fiable; no exigir hiperextensión.
- **NO detectar:** pike/box push-up, kipping, déficit/paralelas, descanso, salida
  voluntaria del handstand, manos/codos ocultos, amplitud adaptada o clip incompleto.
- **Evidencia / dificultad / prioridad:** S7, S8 y referencia strict; media;
  **P1**. `detectable: false`. No afirma contacto de cabeza o talones.

### `reduced_elbow_excursion` — Descenso de brazos reducido respecto al objetivo strict

- **Categoría y descripción coach:** rango. La flexión del codo en el fondo es
  menor que el objetivo individual, sin afirmar que la cabeza no toca suelo.
- **Vista / landmarks:** lateral; hombro, codo, muñeca, cadera, tobillo.
- **Métricas:** codo e inversión; futuras ventana de fondo independiente y objetivo
  revisado por coach, calidad y medidas por brazo.
- **Condición candidata:** mínimo del ciclo > mínimo objetivo +10°; no exigir
  pasar el threshold `bottom_elbow_max` del contador para evaluar el intento.
- **Tolerancia:** G; ≥3 muestras alrededor del mínimo; margen 10–15° por explorar.
- **NO detectar:** almohadilla/target elevado, ROM parcial prescrito, pike/box,
  déficit, kipping, cabeza no visible o objetivo de fondo desconocido.
- **Evidencia / dificultad / prioridad:** S7 y perfil; alta; **P2**.
  `detectable: false`. Contacto con suelo sigue fuera de observabilidad actual.

## Faults del catálogo que no pueden tratarse como detectables hoy

Los siete faults iniciales del baseline conservan exactamente su estado false.
Los siguientes son límites de esos IDs, no sustituciones automáticas por los
proxies anteriores. Las fichas de alcance restringido se mantienen separadas.

| Ejercicio / fault_id actual | Nombre y descripción coach | Vista y landmarks que harían falta | Métricas / condición candidata | Tolerancia y NO detectar | Evidencia / dificultad / prioridad | Estado |
|---|---|---|---|---|---|---|
| air_squat / `insufficient_depth` | Profundidad insuficiente: pliegue no alcanza posición objetivo | Lateral; cadera/rodilla, pero pliegue y borde de rodilla no están modelados | Relación vertical anatómica calibrada, ausente; ángulo de rodilla solo es proxy | Umbral pendiente; no evaluar targets, adaptación, oclusión o perspectiva incorrecta | S1; alta; P2 | detectable:false; bloqueado para criterio anatómico exacto |
| overhead_squat / `unstable_overhead` | Pérdida de estabilidad/alineación de carga overhead | Lateral y posiblemente frontal; hombro/codo/muñeca + barra y base de apoyo | Trayectoria/oscilación de barra relativa al apoyo; no existe señal suficiente | Tolerancia pendiente; excluir marcha de escape, regrip, cámara móvil | S2; alta; P3 | detectable:false; flexión de codo no prueba estabilidad total |
| deadlift / `rounded_back` | Pérdida de posición lumbar durante tirón | Lateral; puntos adicionales de columna, no solo hombro/cadera | Curvatura segmentaria lumbar, ausente; no hay condición defendible con inclinación global | No fijar umbral; excluir inclinación normal de torso o proporciones individuales | S3; no viable con puntos actuales; P3 | detectable:false |
| clean / `early_arm_bend` | Flexión de brazos antes de extensión inferior | Lateral; brazo y cadena inferior | Ver ficha específica: fases y calidad por brazo pendientes | Ver ficha; excluir third pull y catch | S4; alta; P2 | detectable:false; candidato de investigación |
| snatch / `unstable_catch` | Recepción overhead sin control de carga | Lateral/frontal según eje; brazo/cadera/pies + barra | Estabilidad relativa de implemento y apoyo en catch, no disponible | Tolerancia pendiente; no confundir reubicación de pies válida o escape con fault automático | S5/S9; alta; P3 | detectable:false; no inferible de conteo ni muñecas solamente |
| thruster / `early_press` | Press anticipa extensión inferior | Lateral; brazo y cadena inferior | Ver ficha: alzada pasiva y press activo deben diferenciarse | Ver ficha; no marcar el impulso de piernas como press | S6; alta; P2 | detectable:false; candidato de investigación |
| handstand_push_up / `incomplete_lockout` | Bloqueo incompleto del final invertido | Lateral; brazo/cadera/tobillo; pared/contacto para un estándar completo | `incomplete_elbow_lockout` es solo componente observable; no certifica final completo | Excluir variantes y contacto no visible; tolerancia G solo para codo | S7/S8; media para codo, alta para estándar completo; P1 para componente | detectable:false; no renombrar baseline automáticamente |

No proponer detección de valgo dinámico, presión en puntas/talones, curvatura
lumbar, low elbows de front rack, contacto de cabeza o trayectoria de barra a
partir de la media de ángulos actual. Algunas derivaciones serían posibles con
pose bruta y calibración adicional, pero no existen hoy métricas, confianza y
validación suficientes. Se prioriza abstención y revisión del coach.

## Cinco candidatos con mejor relación valor / facilidad / riesgo

Ranking cualitativo de diseño, **no rendimiento medido**. Todos P1 y false.
La facilidad es relativa: ninguno se activa solo agregando un threshold.

| Orden | Ejercicio / fault_id | Valor para coach | Facilidad relativa | Control principal de falsos positivos |
|---|---|---|---|---|
| 1 | deadlift / `incomplete_hip_extension` | Final claro y cue accionable | Media: señal actual de cadera | Lateral, referencia individual y final/retorno completo; excluir variantes |
| 2 | air_squat / `incomplete_knee_extension` | Consistencia de final de rep | Media: señal actual de rodilla | No confundir ascenso en curso con final; calibración y evidencia de inversión |
| 3 | handstand_push_up / `incomplete_elbow_lockout` | Final visible y fácil de revisar | Media: codo/inversión actuales | Solo strict, brazo visible, sin exigir contacto ni hiperextensión |
| 4 | thruster / `incomplete_elbow_lockout` | Final del press accionable | Media: codo y contexto overhead | Separar drive/press/retorno, no usar muñeca sola, abstenerse en reps muy rápidas |
| 5 | overhead_squat / `sustained_elbow_flexion` | Pérdida sostenida de soporte de brazos | Media: codo, wrist y rodilla actuales | Contexto overhead continuo, descartar escape y oclusión; no afirmar trayectoria de barra |

Se dejan ROM exacto, early arm bend, early press y recepción global para después:
necesitan más contexto o tienen mayor ambigüedad. Snatch y clean siguen cubiertos
por diseño, sin forzarles un lugar entre los cinco más sencillos.

## Puertas de validación antes de cambiar detectable

1. **Algoritmo:** especificar ámbito, geometría, calidad por cadena, fases/intentados,
   incertidumbre y abstenciones. No reutilizar como verdad el gating del contador
   que exige el mismo rango o bloqueo; podría ocultar todos los casos positivos.
2. **Fixtures:** secuencias sintéticas positivas y negativas con tiempos reales,
   muestreo irregular, extremos de aspect ratio, ruido, lado cambiante y datos
   faltantes. Incluir reps válidas justo dentro de la banda e intentos no contados.
3. **Tests:** límites de tolerancia/histeresis, abstención, no duplicación,
   timestamps, fallos sin rep asignable y contratos de findings. Mantener suite
   existente; no exigir número de rep ficticio para un intento incompleto.
4. **Video real autorizado:** clips propios aportados para validación, variantes
   explícitas y varios atletas/encuadres/velocidades; etiquetas y límites revisados
   por coaches, con adjudicación de desacuerdos. Referencias YouTube solo como
   material educativo, no descargarlas ni convertirlas en fixtures.
5. **Evaluación:** separar atletas de calibración y evaluación. Medir precisión,
   falsos positivos por rep/intento y por minuto, cobertura/abstenciones y error
   temporal; incluir intervalos de incertidumbre. Priorizar precisión sobre
   cobertura. El objetivo numérico y tamaño mínimo deben acordarse antes del piloto,
   sin inventar resultados ni anunciar bajo riesgo ya demostrado.
6. **Activación:** revisión documentada de algoritmo, fixtures, tests y video real
   para cada ejercicio/vista/variante. Solo entonces considerar `detectable:true`.
   Cambiar un fault no cambia automáticamente `analysis_status` del ejercicio.

Pendientes decisivos: geometría isotrópica y cadena articular con confianza,
observación de intentos fuera del contador, separación de fases y codos por brazo,
calibración por variante, aceptación del coach y contrato de findings para intentos
no contados. Todo permanece como diseño; no se implementa ninguna de estas piezas.
