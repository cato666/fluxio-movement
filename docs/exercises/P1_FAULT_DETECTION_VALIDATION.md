# Validación experimental de los cinco faults priorizados

Fecha: 2026-10-03, America/Santiago. Solo experimentos offline; biblioteca,
`detectable:false`, UI, feedback y estados supported/reference_only intactos.

## Resultado de factibilidad

| Ejercicio / fault_id | Clasificación para pipeline actual | Resultado experimental condicionado |
|---|---|---|
| deadlift / incomplete_hip_extension | NOT_FEASIBLE_CURRENT_PIPELINE | Señal angular evaluable si un revisor aporta fase, calibración y calidad original |
| air_squat / incomplete_knee_extension | NOT_FEASIBLE_CURRENT_PIPELINE | Señal angular evaluable bajo los mismos supuestos |
| handstand_push_up / incomplete_elbow_lockout | NOT_FEASIBLE_CURRENT_PIPELINE | Componente de codo evaluable solo strict, con ambos brazos visibles y contexto invertido |
| thruster / incomplete_elbow_lockout | NOT_FEASIBLE_CURRENT_PIPELINE | Componente de codo evaluable solo en final de press revisado y contexto overhead |
| overhead_squat / sustained_elbow_flexion | NOT_FEASIBLE_CURRENT_PIPELINE | Déficit angular sostenido evaluable en fase squat overhead revisada |

**READY_FOR_PILOT: 0. NEEDS_MORE_DATA: 0. NOT_FEASIBLE_CURRENT_PIPELINE: 5.**
No faltan solamente más ejemplos: faltan contratos de fase, calidad y calibración
en el pipeline actual. Esta clasificación aplica a detección fiable sobre sus
resultados actuales; no significa que los landmarks originales sean inútiles ni
que sea necesario un nuevo modelo. Los núcleos numéricos funcionan con contexto
adicional explícito, pero ese contexto NO lo genera hoy producción. Después de
resolver esas dependencias, seguirá siendo necesario validar con video etiquetado.

## 1. Factibilidad: datos y criterios por fault

Índices MediaPipe existentes: hombro 11/12, codo 13/14, muñeca 15/16,
cadera 23/24, rodilla 25/26, tobillo 27/28. En piernas, solo se usa una cadena
coherente o ambas cadenas completamente visibles. El ángulo de codo actual
promedia brazos válidos sin indicar qué brazo contribuyó; por eso el experimento
de codo exige visibilidad de ambas cadenas. No se agrega una nueva métrica angular.

| Fault | Landmarks exactos necesarios | Métricas existentes | Vista y fase requerida | Condición candidata y threshold inicial | Tolerancia temporal |
|---|---|---|---|---|---|
| Deadlift: extensión final de cadera incompleta | Hombro–cadera–rodilla: 11–23–25 o 12–24–26 | hip_angle; pose_confidence y active_side como contexto | Lateral; final de ascenso con retorno/fin de intento confirmado por revisor; variante conventional | Ángulo de cadera consistentemente menor que extensión calibrada menos 15° en toda la ventana final | ≥0.25 s, ≥3 muestras únicas; sin gaps >0.12 s |
| Air squat: extensión final de rodilla incompleta | Cadera–rodilla–tobillo: 23–25–27 o 24–26–28 | knee_angle; pose_confidence, active_side | Lateral; final del ascenso, antes de nuevo descenso, intento completo; variante standard | Ángulo de rodilla consistentemente menor que extensión calibrada menos 15° en toda la ventana final | ≥0.25 s, ≥3 muestras únicas; sin gaps >0.12 s |
| HSPU strict: bloqueo de codo incompleto | Ambos brazos 11–13–15 y 12–14–16; inversión 11–23–27 y 12–24–28 | elbow_angle, inverted_body_ratio | Lateral; final de empuje, con descenso/ascenso íntegros revisados; strict | Codo medio < calibración −15° durante toda la ventana final, inverted_body_ratio ≥0.5 | ≥0.25 s, ≥3 muestras únicas; sin gaps >0.12 s |
| Thruster: bloqueo de codo incompleto | Ambos brazos 11–13–15 y 12–14–16; contexto inferior 23–25–27 y 24–26–28 | elbow_angle, wrist_lift; métricas inferiores disponibles para revisión de fase | Lateral; final de press después de squat/drive revisados; barbell | Codo medio < calibración −15° en toda la ventana final, wrist_lift ≥0.08 | ≥0.25 s, ≥3 muestras únicas; sin gaps >0.12 s |
| OHS: flexión sostenida de codos | Ambos brazos y cadenas inferiores, mismos índices que thruster | elbow_angle, wrist_lift; rodilla para revisión de fase | Lateral; descenso/fondo/ascenso con overhead previo establecido; barbell | Codo medio < calibración −15° en una racha continua dentro de fase revisada, wrist_lift ≥0.08 | Racha ≥0.25 s y ≥3 muestras; no unir rachas a través de ruido |

El punto de partida es el diseño aprobado: déficit de 10° y banda de incertidumbre
de ±5°. El código exige **déficit >15°**, no ≥15°, para generar candidato.
Déficit <5° en toda la ventana significa ausencia de déficit observado; señales
intermedias/inestables producen abstención conservadora. Calibración explícita
entre 150° y 180° revisada por coach, en misma escala, vista y variante. La validación
de ese rango y de todos los números es pendiente; no son límites fisiológicos.

Se usó 0.25 s dentro del intervalo temporal del diseño. El límite de gap 0.12 s
se propone para evitar continuidad ficticia con muestreo nominal cercano a 15 Hz.
Es conservador: el stride actual puede generar solo 12 Hz a 24 fps. Ningún valor
se ajustó después de mirar resultados para hacer pasar los fixtures.

## Exclusiones y riesgos

Comunes: vista frontal/oblicua, identidad/variante sin confirmar, ROM adaptado,
intento parcial, fase no revisada, ausencia de calibración, geometría no verificada,
cadena con visibilidad <0.75, confianza global <0.8, lado cambiante, datos faltantes,
tiempos inválidos, gaps o cobertura incompleta. Las muestras deben abarcar la fase
revisada con margen máximo de 0.12 s en cada extremo. Timestamps duplicados
idénticos se deduplican; duplicados contradictorios y desorden temporal se rechazan.

| Fault | Exclusiones específicas | Riesgo de falso positivo | Riesgo de falso negativo |
|---|---|---|---|
| Deadlift | Setup, ascenso aún en curso, RDL/sumo/trap bar, drop seguro, variante o rango prescrito distintos | Final mal delimitado, proyección del torso, calibración incorrecta, inclinación de cámara; cadera angular no describe columna | Final breve o sin pausa; solo se publican reps completas; gate conservador elimina intentos; adaptación no documentada |
| Air squat | Fondo/descenso, ascenso recortado, box squat o ROM prescrito | Confundir subida con final, perspectiva, alternancia de lados, calibración que no representa al atleta | Bloqueo entre muestras, final sin meseta, contador omite intento incompleto |
| HSPU strict | Kipping, pike/box, paralelas/deficit, salida/descanso, cabeza/contactos no evaluados | Proyección del codo, ventana que contiene empuje aún válido, pose invertida mal estimada | Promedio bilateral oculta un codo flexionado; brazos ocluidos; poca duración de final |
| Thruster | Rack, drive, retorno normal, mancuernas/kettlebells/unilateral, variante adaptada | Muñecas altas durante fase equivocada, retorno mezclado con final, escala del encuadre | Press rápido; promedio de brazos; wrist_lift cae bajo gate por encuadre, no por técnica |
| OHS | Bajada voluntaria de carga, escape, setup/regrip, otra variante | Fase incluye salida normal de overhead; agarre amplio proyecta codos; wrist_lift no prueba control de barra | Flexión unilateral diluida en promedio; rachas cortas, oclusión; gates de conteo ocultan el fallo |

Se mantienen los límites del [diseño aprobado](P1_FAULT_DETECTION_DESIGN.md):
los ángulos se calculan sobre coordenadas normalizadas no isotrópicas; falta
calibración/verificación geométrica en resultados actuales. El experimento no
recalcula ni corrige geometría y exige `geometry_verified` explícito. La calidad
global puede mezclar lados; visibilidad articular no se persiste en timeline.
Las ventanas no se extraen del contador porque sus thresholds ya exigen bloqueo.

En particular, el código NO descubre fases por sí mismo ni certifica que el
ejercicio/variante declarados por el caller sean correctos. `phase_reviewed`,
`complete_attempt` y calibración son supuestos manuales del experimento.
No bastaría activarlos automáticamente para salvar la falta de datos.

## 2. Implementación aislada y contrato de salida

- [experimental_faults.py](../../app/services/experimental_faults.py): cinco
  funciones públicas específicas, sin imports desde analyzer, rutas ni feedback.
- `EvaluationContext`: ejercicio, vista, variante, ventana/fase revisada,
  intento completo, calibración revisada, geometría y adaptación de rango.
- Samples: métricas de timeline existentes, `time_s`, `active_side`,
  `pose_confidence` y visibilidad original de landmarks. El runner offline retiene
  esa visibilidad temporalmente; **no modifica el esquema persistido de producción**.
- Las cinco funciones retornan `fault_id`, `detected`, `confidence`,
  `timestamp_start`, `timestamp_end`, `evidence` y `reason`.
- Detección condicionada ⇒ score fijo exploratorio 0.6 y timestamps de evidencia,
  nunca mensajes clínicos. No-detección/abstención ⇒ score 0 y timestamps null.
  `reason` distingue ausencia observada de imposibilidad de evaluación.
- `evidence.confidence_kind = uncalibrated_signal_score`: **0.6 no es probabilidad,
  precisión ni confianza clínica**. El score se limita deliberadamente; calibrarlo
  requiere datos reales etiquetados. No debe usarse para aprobar piloto.
- En finals, una extensión válida posterior dentro de ventana veta el candidato;
  en OHS se exige una racha continua. Un frame aislado no basta.
- Repetir el mismo frame con mismo timestamp no aumenta confianza o duración.
  Un mismo fotograma reetiquetado con tiempos distintos es indistinguible de una
  pausa genuina con estas métricas: queda como limitación, no garantía resuelta.

`detected:true` de una función experimental significa **candidato bajo los
supuestos aportados**, no `detectable:true` en la biblioteca.

## 3. Fixtures y tests

[Fixtures](../../tests/fixtures/experimental_faults.json) explícitos compartidos
entre cinco experimentos: caso correcto, claramente incorrecto, limítrofe,
landmarks incompletos, ruido temporal, movimiento parcial, frame duplicado y
ejercicio equivocado. Cada combinación se comprueba independientemente.

Los fixtures modelan **ventanas evaluadas**, no una reconstrucción ficticia del
movimiento entero. La fase y el intento completo son anotaciones sintéticas
explícitas. Calibración 175°; correcto 174–175°, incorrecto 149–151°, límite
164–165°. Los casos están lejos de o dentro de la banda propuesta; no se deduce
un umbral de las etiquetas artificiales.

[Tests](../../tests/test_experimental_faults.py) también cubren vista/variante,
calibración y fase ausentes, geometría, ROM adaptado, gaps, duplicados contradictorios,
tiempo desordenado, NaN, baja confianza, cambio de lado, contexto overhead/inversión,
extensión válida tardía, cobertura parcial y visibilidad null. Comprueban que los
experimentos no estén importados por producción y que todos los flags del catálogo
permanezcan false.

Regresión Python completa: **434 pasando** en 220.14 s, con tres warnings de
deprecación existentes. Base de tests desechable; sin cambios de dependencias.

Tests específicos: **132 pasando**, incluidas las 40 combinaciones de cinco faults
con ocho tipos de fixture. Los cinco casos correctos no generan candidatos; los
cinco claramente incorrectos sí; los cinco limítrofes se abstienen. Ruido, parcial,
duplicado sin duración, landmarks incompletos y ejercicio equivocado se abstienen.
Las observaciones sintéticas **no** estiman sensibilidad/especificidad sobre atletas.

## 4. Ejecución sobre videos locales

Se ejecutó [validate_experimental_faults.py](../../scripts/validate_experimental_faults.py)
con el modelo `pose_landmarker_lite.task` ya presente. El script falla si falta:
no llama a `ensure_model`, no descarga nada, no genera videos anotados y no escribe
feedback. Decodifica con OpenCV, usa el modelo existente y reutiliza `_pick_metrics`,
`_press_metrics` y `_pose_quality`. Guarda SHA-256 del modelo y de cada fuente.

10 archivos locales, **5 contenidos únicos por hash**, **2.227 frames decodificados**.
Los duplicados no cuentan como sujetos ni como evidencia independiente.
La presencia de un MP4 no garantiza que sea video de atleta: se incluye el archivo
de 1 s sin pose y material de landing en la auditoría, sin inventar sus etiquetas.

| Fuente(s) | SHA-256, prefijo | Resolución / fps | Frames | Samples con pose válida | Rango de timestamps de samples |
|---|---|---|---|---|---|
| uploads/03e7f82b46b6.mp4; 0d9c1f4f4e7c; 2e88079d1b60; 36e31f310f2d; 9bf40bff8ddf | 18d1c84cb2b0 | 480×864 / 60 | 1519 | 380 | 0.000–25.267 s |
| uploads/1e3674ccebd5.mp4 | 5c6614a43629 | 320×240 / 15 | 15 | 0 | null |
| uploads/4275e6d44d08.mp4; 6cfb85bb3f78 | 79272521c067 | 480×864 / 24 | 201 | 99 | 0.167–8.333 s |
| app/static/landing-analysis-example.mp4 | 31d7ad258fc3 | 242×324 / 30 | 252 | 10 | 7.733–8.333 s |
| app/static/landing-demo.mp4 | 9c5fdd8c0cd8 | 1280×720 / 24 | 240 | 30 | 2.000–7.833 s |

**25 evaluaciones**: cada contenido se pasó a las cinco funciones como hipótesis
de ejercicio, no como etiqueta confirmada. Para todas: esperado `UNLABELED`;
observado `detected:false`, `confidence:0`, timestamps de fault `null`, reason
`incomplete_attempt`. La evidencia registra explícitamente identidad no confirmada
y la falta de ventana revisada, calibración y geometría. No se fabricaron timestamps
de un fault a partir del rango total de samples.

La abstención aparece antes de intentar medir déficit: comprobar que se rechaza
contexto incompleto no es validar detección sobre video real. No hay positivos
confirmados ni negativos confirmados, por lo que **no se calculan tasas de acierto,
falsos positivos o falsos negativos reales**. Los archivos de analysis previos
tampoco tienen etiquetas de faults y, en su mayoría, carecen de pose_confidence.

Evidencia completa reproducible: `results/experimental-faults/local-validation.json`
(resultado local; no contiene frames ni copias de videos). Incluye hashes completos,
resoluciones, samples, timestamps y resultado de cada combinación fuente/detector.
Ejecutar desde raíz con dependencias existentes:

```text
PYTHONPATH=. python scripts/validate_experimental_faults.py
pytest -q tests/test_experimental_faults.py
```

Los tests del proyecto requieren la base desechable movement_test y
TEST_DATABASE_RESET=1, como define tests/conftest.py. No ejecutar contra la base
normal. La ejecución de video es offline y no necesita base de datos.

## 5. Decisión y requisitos para continuar

Los cinco quedan NOT_FEASIBLE_CURRENT_PIPELINE para detección fiable automática.
El código experimental demuestra evaluación angular condicionada y abstenciones,
no suficiente confianza sobre datos reales.

Antes de reclasificar a NEEDS_MORE_DATA: conservar/verificar calidad de la misma
cadena, definir geometría y calibración reproducibles, aportar identidad/vista/
variante verificadas y fases de intentos independientes de conteo. Para brazos,
resolver media bilateral y exposición de métrica por lado o restringir formalmente
el alcance a flexión bilateral observable. Todo esto requiere una fase autorizada
posterior; no se incorpora ahora al pipeline.

Para READY_FOR_PILOT: además, fixtures de movimientos completos, videos propios
etiquetados por coaches, separación de atletas entre calibración/evaluación,
medidas de falsos positivos, cobertura y error temporal con incertidumbre, y
criterios de aceptación acordados antes del piloto. No se necesita ni se propone
entrenar modelos nuevos. Ningún READY_FOR_PILOT ni cambio a detectable:true en esta fase.
