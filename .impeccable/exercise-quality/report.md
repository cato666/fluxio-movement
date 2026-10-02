# MediciÃ³n inicial de calidad â€” 2026-10-02

Estado: **parcial, no aprobaciÃ³n de calidad general**. Sin cambios de producto, umbrales, perfiles, modelo o identidad visual. No hay telÃ©fonos disponibles ni coach evaluador; el usuario confirmÃ³ ambas limitaciones. No se sustituye hardware por emulaciÃ³n.

## MÃ©todo y evidencia

Se deduplicaron los uploads por SHA256: ocho archivos contienen tres payloads distintos. Se inspeccionaron contactos visuales y secuencias densas; se ejecutaron las funciones reales de preflight, anÃ¡lisis, codificaciÃ³n y ranking en `movement-athlete-test-tests`, sin red. El script verifica igualdad byte a byte entre los servicios/perfiles del contenedor y el checkout. Modelo, versiones y hashes estÃ¡n en `../review/exercise-quality/frozen-environment.json`. Los scripts reproducibles son `measure.py`, `measure-public.py` y `summarize.py` en ese directorio. Resultados completos, trazas, videos anotados y capturas permanecen allÃ­ como evidencia local ignorada por Git.

Los tiempos incluyen preflight, anÃ¡lisis y codificaciÃ³n local, excluyen subida, cola y proveedores externos. Las observaciones del proveedor externo estuvieron **deshabilitadas**: no se ha medido su calidad, latencia ni tasa de error. Los momentos son el ranking determinista existente. Confianza de pose, confianza de conteo y confianza de sugerencia son conceptos diferentes; ninguna se interpreta como probabilidad calibrada de correcciÃ³n tÃ©cnica.

Fuente pÃºblica: Conanta, Ivan; Virginia, Gloria (2026), [MyDeadlift, V1, DOI 10.17632/w5prmmxyt9.1](https://data.mendeley.com/datasets/w5prmmxyt9/1), CC BY 4.0. Se seleccionÃ³ el primer nombre ordenado de cada clase GB/PB/LLK para S04/S07; no se seleccionÃ³ segÃºn resultados. Etiquetas de tÃ©cnica proceden de sus autores, no de una nueva valoraciÃ³n clÃ­nica. Los seis clips se inspeccionaron visualmente: una elevaciÃ³n y descenso cada uno. Los archivos descargados son 464Ã—832, ~30 FPS, aunque la ficha describe captura 1920Ã—1080. No se transformaron los videos. Archivo original ZIP y hashes individuales conservados.

## Tabla por video

| Video / selecciÃ³n | Esperadas | Detectadas | Momentos | Pose media / conteo | Tiempo s | Resultado |
|---|---:|---:|---:|---|---:|---|
| GB_S04_R01 / Deadlift side | 1 | 0 | 0 | 0,92 / baja | 3,350 | falso negativo |
| GB_S07_R11 / Deadlift side | 1 | 1 | 0 | 0,94 / alta | 3,021 | conteo correcto |
| PB_S04_R01 / Deadlift side | 1 | 1 | 0 | 0,95 / alta | 3,613 | conteo correcto |
| PB_S07_R11 / Deadlift side | 1 | 1 | 0 | 0,95 / alta | 2,840 | conteo correcto |
| LLK_S04_R01 / Deadlift side | 1 | 1 | 0 | 0,92 / alta | 2,306 | conteo correcto |
| LLK_S07_R11 / Deadlift side | 1 | 1 | 0 | 0,92 / alta | 3,457 | conteo correcto |
| 03e7f82b46b6 / Clean front | 2 completas + 1 intento parcialÂ¹ | 3 | 2 | 0,98 / alta | 18,647 | FP provisional |
| mismo clean / side | mismo video, diagnÃ³stico de vista | 3 | 2 | 0,98 / alta | 17,282 | no muestra independiente |
| 4275e6d44d08 / Press front | 3 | 3 | 0 | 0,99 / alta | 4,160 | control fuera de baterÃ­a |
| landing-demo / Sentadilla side | no aplica | 0 | 0 | 0,92 condicional / baja | 7,614 | screencast, excluido |
| landing-analysis-example / Press | no aplica | no procesado | no aplica | no aplica | 1,105 | resoluciÃ³n rechazada |

Â¹ Clean es un complejo: dos recepciones y recuperaciones con continuaciÃ³n overhead; en el tercero libera la barra antes de ponerse de pie. Criterio provisional: retener la barra hasta recuperar la posiciÃ³n erguida. InspecciÃ³n del tercer intento cada 0,1 s en `clean-final-recovery.jpg`: libera ~23,4â€“23,5 s y se incorpora ~23,8 s. Necesita adjudicaciÃ³n por coach. No se etiqueta como ejecuciÃ³n tÃ©cnicamente correcta ni se usa como clean puro.

## MÃ©tricas separadas

Exactitud de conteo = videos con conteo exacto / videos elegibles. PrecisiÃ³n de eventos = TP/(TP+FP); recall = TP/(TP+FN). Un rechazo de preflight no cuenta como video procesado con cero detecciones. Sin promedios entre ejercicios.

| Ejercicio | n independiente | Conteo exacto | TP / FP / FN | PrecisiÃ³n / recall eventos | Sin detecciÃ³n | Momentos medios | Ãštiles para coach |
|---|---:|---:|---|---|---:|---:|---|
| Squat | 0 | N/E | N/E | N/E | N/E | N/E | N/E |
| Deadlift | 6, dos sujetos | 5/6 = 83,3% | 5 / 0 / 1 | 100% / 83,3% | 1/6 = 16,7% | 0 | N/E: ninguna sugerencia |
| Clean mixtoÂ¹ | 1 | 0/1 = 0%, provisional | 2 / 1 / 0 | 66,7% / 100%, provisional | 0/1 | 2 | N/E: falta coach |

Deadlift por clase: GB 1/2 conteos correctos, PB 2/2, LLK 2/2. Error absoluto medio 1/6 repeticiÃ³n por video; tiempo medio 3,098 s. No demuestra generalizaciÃ³n a otras cÃ¡maras, personas o condiciones. Si el coach considera completo el tercer clean, cambia a 3/3 eventos, cero FP y conteo exacto; conservar ambas interpretaciones hasta adjudicaciÃ³n.

## RevisiÃ³n manual de momentos

| Video | Momento | Confianza UI | ClasificaciÃ³n provisional | Evidencia |
|---|---|---|---|---|
| Clean front | rep 3, 22,6 s: mayor inclinaciÃ³n | media | dudosa | mÃ¡ximo 34,3Â° ocurre a 21,267 s, antes de recepciÃ³n; cambia a mÃ©tricas del lado derecho al invalidarse el izquierdo. ComparaciÃ³n 2D ambigua. |
| Clean front | rep 2, 12,0 s: menor profundidad | media | dudosa | mÃ­nimos de rodilla 40,6 / 49,5 / 46,5Â°. El mÃ­nimo de rep 3 corresponde al setup, no a la recepciÃ³n: comparaciÃ³n entre fases diferentes. |
| Clean side, diagnÃ³stico duplicado | mismos dos, 22,67 y 12,0 s | media | dudosas, no sumar | mismo archivo y valores; no dos videos independientes. |

Resultado Ãºnico: Ãºtiles 0, dudosas 2, irrelevantes 0, **valoraciÃ³n del asistente, no del coach**. Deadlift/Press/screencast no generaron sugerencias para clasificar. No se infiere que cero sugerencias equivalga a tÃ©cnica correcta. El ranking compara repeticiones y no constituye un clasificador universal de defectos.

## DiagnÃ³stico reproducido del E2E de cero repeticiones

El anÃ¡lisis persistido `ca8cdbb9216b` usÃ³ `landing-demo.mp4`, un screencast de la aplicaciÃ³n con cortes y pequeÃ±os fragmentos de press, seleccionando Sentadilla/side. El alias y perfil estÃ¡n soportados; **el contenido no es una captura continua del ejercicio seleccionado**.

- ResoluciÃ³n 1280Ã—720, duraciÃ³n 10 s, FPS 24: cumplen mÃ­nimos; no hay error de procesamiento. Estado COMPLETED y video anotado generado.
- Muestreo efectivo 12 Hz: 120 oportunidades, solo 27 muestras vÃ¡lidas (22,5%). Confianza media 0,92 calculada Ãºnicamente sobre poses aceptadas.
- Preflight acepta 9 muestras de 48 oportunidades (18,75%), pero informa 100% de cobertura porque divide 9 poses completas entre 9 poses aceptadas. **Defecto confirmado del denominador de cobertura**, en `app/services/exercise_validation.py`, `quality_report` y colector de muestras. No corregido en esta fase de mediciÃ³n.
- Perfil squat-side: descenso â‰¤145Â°, fondo â‰¤115Â°, ascenso â‰¥135Â°, cierre â‰¥155Â°; dos confirmaciones y mÃ¡ximo gap 0,5 s.
- 2,917 s, rodilla 130,2Â°: primera confirmaciÃ³n de descenso. 3,000 s, 114,1Â°: segunda, pasa a descenso; no puede confirmar tambiÃ©n el fondo en la misma muestra.
- Siguiente muestra 6,250 s: gap 3,250 s, reinicia candidato. No hay fondo/ascenso/cierre completos.
- Nueva ejecuciÃ³n reproduce las 27 muestras y cero reps. Traza anterior conservada en `e2e-persisted-trace.json`. El tiempo persistido anterior fue 13,723 s; no comparar con ejecuciÃ³n offline como mejora de rendimiento.

Causa principal: calidad/tipo de entrada incorrecto y discontinuidad de landmarks; seÃ±al de rodilla proveniente de otro movimiento. No hay evidencia para ajustar thresholds a partir de este E2E.

## Fallos y recomendaciones priorizadas

| Prioridad | Hallazgo | Clase | AcciÃ³n posterior a mediciÃ³n |
|---|---|---|---|
| P1 | Cobertura preflight engaÃ±osa | defecto del algoritmo de calidad / UX | corregir denominador con todas las oportunidades; preservar diagnÃ³stico, diseÃ±ar prueba especÃ­fica antes de implementaciÃ³n |
| P1 | GB_S04_R01, una rep real no contada | defecto candidato del conteo | landmarks 44 continuos, sin gaps >0,5 s; hip mÃ¡ximo 159,3Â°, threshold de cierre 160Â°. Estado final ascent, nunca lockout. Confirmar Ã¡ngulo/vista en mÃ¡s clips antes de ajustar |
| P1 | intento clean abandonado contado con confianza alta | limitaciÃ³n conocida / defecto candidato | el perfil cuenta rodilla, no retenciÃ³n de barra; adjudicar etiqueta y ampliar intentos fallidos antes de decidir correcciÃ³n |
| P2 | comparaciÃ³n de fases y lados en clean | limitaciÃ³n del ranking 2D | validar utilidad y localizaciÃ³n con coach; no traducir confianza alta de pose a certeza de tÃ©cnica |
| P2 | cero momentos en seis deadlifts, incluidos PB/LLK | limitaciÃ³n de cobertura de sugerencias | medir por separado conteo y utilidad; no vender detecciÃ³n universal de errores |
| P2 | dataset describe otra resoluciÃ³n | calidad/proveniencia del dataset | registrar bytes reales; no asumir parÃ¡metros del dispositivo de origen |
| Bloqueante de validaciÃ³n | squat, condiciones adversas, proveedor de observaciones y telÃ©fonos ausentes | entorno/cobertura | completar protocolo antes de aprobaciÃ³n general |

No se diagnosticaron fallos de infraestructura durante las ejecuciones locales. No se hicieron pruebas fÃ­sicas ni se identifican diferencias Android/iOS verificadas.

## Pendientes para cierre

Ver `protocol.md`: matriz de clips por condiciÃ³n, evaluaciÃ³n independiente por coach y protocolo de hardware. No bajar umbrales ni ampliar capacidades IA con este tamaÃ±o de muestra. La fase sigue abierta por falta de evidencia, no por fallos de las fases UX aprobadas.
