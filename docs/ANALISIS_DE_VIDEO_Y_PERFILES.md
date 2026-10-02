# Análisis de video y perfiles de ejercicio

Esta guía describe cómo Movement Coach AI obtiene métricas de un video, cuenta repeticiones y selecciona el perfil correcto para cada ejercicio y vista. El análisis es una ayuda técnica para el coach: no sustituye la observación profesional ni permite diagnosticar lesiones.

## Flujo de análisis

```text
MP4
  -> validación de archivo, calidad y patrón general
  -> MediaPipe Pose Landmarker
  -> métricas biomecánicas 2D por muestra
  -> filtro de confianza de pose
  -> perfil del ejercicio + vista
  -> máquina de estados y conteo de repeticiones
  -> video anotado + analysis.json + persistencia PostgreSQL
```

1. El atleta o coach selecciona el ejercicio y si el video está **de costado** o **de frente**.
2. El preflight comprueba que el archivo puede abrirse, estima la calidad y detecta patrones incompatibles cuando son claros. Si no hay evidencia suficiente, el resultado es `INCONCLUSIVE`; no se inventa una coincidencia.
3. MediaPipe detecta una pose por frame. El pipeline toma aproximadamente 15 muestras por segundo y calcula posiciones de hombros, caderas, rodillas, tobillos, codos y muñecas cuando corresponden.
4. OpenCV dibuja los landmarks y métricas disponibles. FFmpeg convierte el resultado a H.264 para que el navegador reproduzca el video anotado.
5. El detector del perfil consume solo muestras con landmarks suficientes y una confianza de pose aceptable. Una repetición solo se crea al completar la secuencia de estados configurada.
6. Se persisten el video original, el anotado, `analysis.json`, las repeticiones, sus métricas y la confianza obtenida.

## Qué se guarda en el resultado

`analysis_json` contiene, entre otros, estos campos:

```json
{
  "exercise_profile": {
    "id": "squat-side",
    "version": "1.0",
    "view": "side"
  },
  "pose_quality": {
    "average_confidence": 0.84,
    "valid_samples": 245,
    "confidence": "high"
  },
  "repetition_count_confidence": "high",
  "repetitions": [
    {
      "repetition": 1,
      "start_s": 2.13,
      "bottom_s": 3.02,
      "end_s": 4.18,
      "profile": "squat-side",
      "profile_version": "1.0",
      "pose_confidence": 0.86,
      "count_confidence": "high"
    }
  ]
}
```

La confianza representa la visibilidad y estabilidad de los landmarks requeridos; no es una calificación de la técnica del atleta.

## Perfiles disponibles

Los perfiles están en [`app/services/exercise_profiles`](../app/services/exercise_profiles). Cada ejercicio tiene una variante para `side` y otra para `front`.

| Ejercicio | IDs de perfil |
| --- | --- |
| Sentadilla | `squat-side`, `squat-front` |
| Peso muerto | `deadlift-side`, `deadlift-front` |
| Clean | `clean-side`, `clean-front` |
| Clean & Jerk | `clean-and-jerk-side`, `clean-and-jerk-front` |
| Snatch | `snatch-side`, `snatch-front` |
| Press | `press-side`, `press-front` |
| Thruster | `thruster-side`, `thruster-front` |
| Otro | `other-side`, `other-front` |

`Clean` y `Clean & Jerk` son perfiles distintos. El segundo exige completar recepción del clean, extensión, dip del jerk y bloqueo sobre la cabeza antes de registrar la repetición.

## Estructura de un perfil

Un perfil es JSON declarativo. No se agrega lógica condicional por ejercicio al analizador.

```json
{
  "id": "squat-side",
  "version": "1.0",
  "aliases": ["squat", "sentadilla"],
  "views": ["side"],
  "required_landmarks": ["shoulder", "hip", "knee", "ankle"],
  "primary_signal": "knee_angle",
  "states": ["lockout", "descent", "bottom", "ascent"],
  "initial_state": "lockout",
  "bottom_state": "bottom",
  "transitions": [
    {
      "from": "lockout",
      "to": "descent",
      "signal": "knee_angle",
      "operator": "<=",
      "threshold": "descent_knee_max"
    }
  ],
  "thresholds": {
    "descent_knee_max": 145.0
  },
  "metrics": ["knee_angle", "hip_angle", "trunk_from_vertical"],
  "noise": {
    "min_confirm_frames": 2,
    "max_gap_s": 0.5,
    "min_rep_duration_s": 0.35,
    "max_rep_duration_s": 12.0,
    "cooldown_s": 0.25,
    "min_pose_confidence": 0.6
  }
}
```

### Campos principales

| Campo | Uso |
| --- | --- |
| `id` | Identificador único. Debe terminar en `-side` o `-front`. |
| `version` | Versión de configuración usada por el análisis. Súbela al cambiar criterios de forma relevante. |
| `aliases` | Nombres aceptados desde la interfaz o API. No deben solaparse con otro perfil de la misma vista. |
| `views` | Vistas que el perfil puede interpretar. Actualmente cada archivo usa una sola. |
| `required_landmarks` | Landmark groups que deben tener visibilidad suficiente para usar la muestra. |
| `primary_signal` | Señal indispensable para avanzar los estados, por ejemplo `knee_angle` o `hip_angle`. |
| `states` y `transitions` | Secuencia válida que debe completarse. Impide contar movimientos parciales. |
| `thresholds` | Valores parametrizables referidos por las transiciones. |
| `metrics` | Valores incluidos como mínimos y máximos en cada repetición. |
| `noise` | Tolerancias de duración, pérdida temporal de pose, confirmación y confianza. |

Una transición puede requerir varias condiciones. El bloqueo de Clean & Jerk, por ejemplo, exige extensión de rodilla y elevación mínima de muñeca:

```json
{
  "from": "jerk_drive",
  "to": "lockout",
  "completes_rep": true,
  "conditions": [
    { "signal": "knee_angle", "operator": ">=", "threshold": "standing_knee_min" },
    { "signal": "wrist_lift", "operator": ">=", "threshold": "lockout_wrist_min" }
  ]
}
```

## Cómo ajustar un perfil

1. Identifica el ejercicio y la vista que falló. No cambies a la vez los dos perfiles.
2. Revisa el `analysis_json` de varios videos conocidos: `timeline`, `repetitions`, `pose_quality` y los mínimos/máximos por repetición.
3. Ajusta primero un único umbral del archivo correspondiente, por ejemplo `bottom_knee_max`.
4. Si el detector cuenta antes de llegar al rango deseado, haz el umbral más estricto. Si deja de contar repeticiones válidas, relájalo gradualmente.
5. Sube `version` al modificar el criterio; los análisis anteriores conservarán qué versión se usó.
6. Ejecuta los tests de perfiles y añade una secuencia representativa del caso corregido.

Ejemplo: si una sentadilla frontal válida no llega a `115°` según MediaPipe y no se cuenta, prueba un ajuste pequeño de `bottom_knee_max` en `squat_front.json`, por ejemplo a `120.0`. No copies ese valor automáticamente a la vista lateral: la perspectiva cambia las mediciones 2D.

## Tolerancias y confianza

`noise` controla la robustez del conteo:

| Parámetro | Efecto |
| --- | --- |
| `min_confirm_frames` | Cantidad de muestras consecutivas necesarias para aceptar una transición. Aumentarlo reduce falsos positivos, pero puede omitir movimientos rápidos. |
| `max_gap_s` | Pérdida temporal máxima de pose aceptada. Si se supera, se descarta la repetición candidata. |
| `min_rep_duration_s` / `max_rep_duration_s` | Rango temporal permitido para una repetición completa. |
| `cooldown_s` | Separación mínima entre conteos; evita duplicados en un mismo bloqueo. |
| `min_pose_confidence` | Confianza mínima de landmarks requeridos. Muestras por debajo de este valor se ignoran. |

No conviene bajar `min_pose_confidence` para compensar videos mal encuadrados. Primero pide un video con cuerpo completo, buena luz y sin oclusiones. La vista seleccionada debe coincidir con el encuadre real.

## Corrección manual del coach

El coach puede corregir el resultado sin alterar el análisis original:

- **Descartar** una repetición detectada que sea falsa o parcial.
- **Restaurar** una repetición descartada.
- **Agregar repetición manual** indicando inicio, punto bajo y fin en segundos.

La corrección se guarda con `source = MANUAL` o con `correction_status = DISCARDED`. Las repeticiones descartadas dejan de formar parte del conteo visible y no pueden marcarse como mejor repetición o repetición a trabajar. Una revisión completada queda bloqueada para estas modificaciones.

Para una detección que fusionó dos repeticiones, descarta la detección fusionada y agrega las dos repeticiones manuales con sus timestamps.

## Validación antes de publicar un ajuste

Ejecuta los tests focalizados:

```bash
docker compose -f compose.test.yml build tests
docker compose -f compose.test.yml run --rm tests pytest tests/test_exercise_profiles.py tests/test_complete_review.py -q
```

Después, valida manualmente con videos etiquetados: una toma frontal y una lateral del ejercicio afectado, incluyendo una serie con número conocido de repeticiones y una secuencia parcial que no deba contarse.

## Límites actuales

- Las métricas son 2D y dependen de cámara, iluminación, ropa y oclusiones.
- Solo se detecta una persona por video.
- Un perfil mejor calibrado no corrige un ejercicio elegido incorrectamente; usa el reanálisis si fue necesario cambiar ejercicio o vista.
- Los valores iniciales son criterios técnicos del MVP y deben calibrarse con un conjunto de videos reales, etiquetados por coaches.
