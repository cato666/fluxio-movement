# Validación de referencias P1

Fecha: 2026-10-03 (America/Santiago). Baseline: 20 ejercicios, commits
`31c22fb`, `e6368af`, `ba1544e`. Auditoría documental; catálogo sin modificaciones.

## Resultado y alcance de la evidencia

**20 NEEDS_TIMESTAMP_ADJUSTMENT; 0 VERIFIED; 0 NEEDS_REPLACEMENT.**
Aquí `NEEDS_TIMESTAMP_ADJUSTMENT` incluye **definir timestamps ausentes**.
Los 20 registros tienen `segments: []` y `segments_status: pending_review`.
No hay intervalos propuestos en configuración. El ejemplo 0–5 s de la solicitud
original no está registrado: no se considera un segmento aprobado ni se presupone
que contenga una repetición completa.

Se abrieron las 20 URLs /watch y se contrastaron sus títulos con el movimiento.
Dieciséis IDs coinciden con enlaces de reproductores publicados por CrossFit;
para los otros cuatro se conserva la evidencia del canal oficial recogida en
el baseline, con comprobación actual de título y comprobaciones adicionales
indicadas abajo. La lectura web de YouTube devuelve frecuentemente solo el footer,
errores de fetch o 429. La navegación del navegador permitió leer títulos; el
primer estado de algunas páginas aún era un esqueleto de carga.

**No se ha completado una reproducción visual íntegra de los 20 videos ni aprobado
ningún intervalo.** La revisión visual fue parcial (clean y pistol). El navegador
mostró anuncios previos de 10–15 s; esos tiempos NO son duración del contenido.
Un intento de embed directo del air squat devolvió error 153 de configuración:
no prueba que el video esté eliminado ni que el embed de la app falle.
No se descargaron archivos de video, audio ni copias del contenido.

## Criterios de clasificación

- `VERIFIED`: identidad oficial, variante correcta y reproducción del intervalo
  completo que muestra las fases declaradas, con inicio/fin y duración anotados.
- `NEEDS_TIMESTAMP_ADJUSTMENT`: identidad compatible, pero intervalo ausente,
  incompleto, sin inspección visual completa, demasiado corto o demasiado largo.
- `NEEDS_REPLACEMENT`: evidencia positiva de ejercicio/variante incorrectos,
  procedencia no oficial, indisponibilidad persistente confirmada o contenido
  sin demostración útil. Un error transitorio de herramienta no basta.

La coincidencia del título verifica identidad nominal; el enlace oficial verifica
procedencia. Ninguno, por separado, confirma una ejecución correcta fotograma a
fotograma. Las observaciones de la tabla describen **qué revisar**, salvo que se
identifiquen expresamente como observación visual.

## Registro por ejercicio

Todos los intervalos actuales: **ausentes**. En todas las filas, duración y
calificación largo/corto: **no evaluables** hasta seleccionar un intervalo.
La evidencia CrossFit enlazada se consultó durante esta revisión; las páginas
de error no se usan como prueba de ejecución.

| Ejercicio | URL actual y título contrastado | Procedencia/evidencia | Clasificación | Observaciones y criterio para el segmento |
|---|---|---|---|---|
| air_squat | [The Air Squat](https://www.youtube.com/watch?v=rMvwVtlqjTE) | [Página oficial](https://www.crossfit.com/essentials/the-air-squat): ID del embed coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Incluir postura inicial, descenso, fondo y retorno a extensión. El intento visual mostró anuncio; no aprobar 0–5 s. |
| front_squat | [The Front Squat](https://www.youtube.com/watch?v=uYumuL_G_V0) | [Página oficial](https://www.crossfit.com/essentials/the-front-squat): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Debe verse front rack durante el ciclo completo; evitar un recorte que solo enseñe agarre o setup. |
| overhead_squat | [The Overhead Squat](https://www.youtube.com/watch?v=pn8mqlG0nkE) | [Página oficial](https://www.crossfit.com/essentials/the-overhead-squat): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Mantener barra y pies en cuadro durante descenso, fondo y subida; revisar posición overhead sostenida. |
| deadlift | [The Deadlift](https://www.youtube.com/watch?v=1ZXobu7JvvE) | [Página oficial](https://www.crossfit.com/essentials/the-deadlift): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Incluir salida desde suelo y final de extensión; retorno si se declara un ciclo completo. No confundir con Romanian deadlift. |
| clean | [The Clean](https://www.youtube.com/watch?v=Ty14ogq_Vok) | [Página oficial](https://www.crossfit.com/essentials/the-clean-2): ID coincide; UI del canal @crossfit | NEEDS_TIMESTAMP_ADJUSTMENT | Observación visual parcial: demostradora con barra en setup, título y autor correctos; reproductor de contenido 1:00. Falta revisar un ciclo que incluya recepción y stand; no confundir recepción power. |
| power_clean | [The Power Clean](https://www.youtube.com/watch?v=KwYJTpQ_x5A) | Canal CrossFit documentado en baseline; título actual coincide; página oficial del índice no accesible en la herramienta | NEEDS_TIMESTAMP_ADJUSTMENT | Confirmar visualmente recepción por encima de paralelo y extensión final. La palabra power en el título no aprueba esa recepción. |
| snatch | [The Snatch](https://www.youtube.com/watch?v=GhxhiehJcQY) | Canal oficial documentado en baseline; UI de YouTube también muestra este ID como video CrossFit | NEEDS_TIMESTAMP_ADJUSTMENT | Incluir tirón, recepción overhead en squat y stand. El tiempo de anuncio no se usa como duración del video. |
| power_snatch | [The Power Snatch](https://www.youtube.com/watch?v=TL8SMp7RdXQ) | [Página oficial](https://www.crossfit.com/essentials/the-power-snatch): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Revisar recepción alta específica de power y bloqueo overhead. |
| push_press | [The Push Press](https://www.youtube.com/watch?v=iaBVSJm78ko) | [Página oficial](https://www.crossfit.com/essentials/the-push-press): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Incluir dip, drive y press; confirmar que no haya segunda flexión de recepción propia del jerk. |
| push_jerk | [The Push Jerk](https://www.youtube.com/watch?v=VrHNJXoSyXw) | [Página oficial](https://www.crossfit.com/essentials/the-push-jerk): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Debe verse segunda flexión, recepción con brazos extendidos y stand; excluir un recorte solo del dip/drive. |
| thruster | [The Thruster](https://www.youtube.com/watch?v=L219ltL15zk) | [Página oficial](https://www.crossfit.com/essentials/the-thruster): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Mostrar front squat conectado con impulso y press overhead. Revisar que el recorte no sugiera dos movimientos separados. |
| wall_ball | [The Wall-Ball Shot](https://www.youtube.com/watch?v=EqjGKsiIMCE) | [Página oficial](https://www.crossfit.com/essentials/the-wall-ball): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Incluir squat, lanzamiento a objetivo y recepción. Balón y objetivo visibles; no afirmar altura reglamentaria sin contexto. |
| box_jump | [The Box Jump](https://www.youtube.com/watch?v=NBY9-kTuHEk) | [Página oficial](https://www.crossfit.com/essentials/the-box-jump): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Despegue, aterrizaje y extensión sobre caja; incluir bajada si se enseña step-down. Excluir box jump-over. |
| kipping_pull_up | [The Kipping Pull-up](https://www.youtube.com/watch?v=lzRo-4pq_AY) | [Página oficial](https://www.crossfit.com/essentials/the-kipping-pull-up): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Arch/hollow, tirón y retorno; dos ciclos ayudan a enseñar ritmo. Excluir butterfly o strict. |
| chest_to_bar | [The Kipping Chest-to-Bar Pull-Up](https://www.youtube.com/watch?v=AyPTCEXTjOo) | [Página oficial](https://www.crossfit.com/essentials/the-kipping-chest-to-bar-pull-up): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Variante kipping explícita. Revisar contacto de pecho, no solo mentón sobre barra. No extender la referencia a strict/butterfly sin otra evidencia. |
| toes_to_bar | [The Kipping Toes-to-Bar](https://www.youtube.com/watch?v=6dHvTlsMvNY) | [Página oficial](https://www.crossfit.com/essentials/the-kipping-toes-to-bar): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Variante kipping. Incluir hang, oscilación, contacto de pies y retorno; contacto no oculto. |
| bar_muscle_up | [Kipping Bar Muscle-Up](https://www.youtube.com/watch?v=OCg3UXgzftc) | [Página oficial](https://www.crossfit.com/essentials/the-kipping-bar-muscle-up): ID coincide | NEEDS_TIMESTAMP_ADJUSTMENT | Variante kipping y barra fija, no anillas. Revisar transición y apoyo final completo. |
| handstand_push_up | [The Strict Handstand Push-Up](https://www.youtube.com/watch?v=0wDEO6shVjc) | Canal CrossFit documentado en baseline; título actual confirma strict | NEEDS_TIMESTAMP_ADJUSTMENT | El ID genérico usa referencia strict; no aprobar para kipping/deficit. Revisar soporte, descenso, fondo y extensión, con cabeza/manos visibles. |
| wall_walk | [The Wall Walk](https://www.youtube.com/watch?v=NK_OcHEm8yM) | [Página oficial](https://www.crossfit.com/essentials/the-wall-walk): ID coincide; título web correcto, UI inicial aún cargando | NEEDS_TIMESTAMP_ADJUSTMENT | Incluir prone, subida, posición superior, bajada y prone final. No inferir cumplimiento de líneas de competición. |
| pistol_squat | [The Single-Leg Squat](https://www.youtube.com/watch?v=keSzg7MaoVQ) | UI actual: título, autor CrossFit, enlace @crossfit y contenido 0:59 | NEEDS_TIMESTAMP_ADJUSTMENT | Observación visual en ~0:12: apoyo unilateral, pierna libre extendida y cue sobre no tocar suelo. Confirma variante pistol, pero no verifica todo el ciclo ni sus límites. |

## Evidencia de acceso y reproducción

1. Se abrió cada URL de la tabla mediante lectura web. Se obtuvieron títulos en
   parte de ellas y errores/footers en otras; estos resultados no permiten
   verificar contenido temporal.
2. Se navegó a las 20 URLs en el navegador. Los títulos visibles coinciden con la
   tabla excepto wall_walk, cuyo estado inicial mostraba solo YouTube; su título
   se corroboró con la lectura web y página oficial.
3. Se siguió el enlace de reproductor de las 16 páginas oficiales indicadas:
   el destino contenía exactamente el ID actual. Un fallo al cargar ese destino
   no invalida la evidencia del enlace que lo referencia.
4. Clean: lectura del autor @crossfit, título y duración del contenido; reproducción
   inicial con setup. Pistol: autor, duración y fotograma educativo ~0:12.
5. Anuncios en air squat, snatch, power snatch, push jerk, thruster, bar muscle-up,
   HSPU y pistol durante el primer estado. No se confundieron con contenido.
6. Las variantes power, strict y pistol tienen antecedente de canal oficial en
   baseline; salvo pistol, falta completar en esta fase su revisión visual y la
   comprobación actual del autor en la página totalmente cargada.

## Revisión temporal pendiente: procedimiento concreto

Para **cada fila** falta reproducir el contenido (sin anuncios), registrar duración
real, elegir un ciclo íntegro y volver a reproducir exactamente ese intervalo.
Registrar: `start_sec`, `end_sec`, fases efectivamente visibles, variante, vista,
oclusiones, cue mostrado, observación de ejecución y responsable de revisión.
Solo entonces cambiar la clasificación documental a VERIFIED.

Pautas editoriales propuestas, **no timestamps medidos ni reglas biomecánicas**:

- Un clip es demasiado corto si corta setup, recepción, contacto o posición final;
  esto prima sobre su número de segundos. Como alarma inicial, revisar clips <3 s.
- Para un ciclo de squat/hinge/press o un levantamiento, buscar aproximadamente
  5–15 s; para kipping cíclico, 8–20 s; para wall walk, 15–35 s. Son ventanas de
  trabajo a ajustar a velocidad normal/slow motion, nunca aprobar por duración sola.
- Revisar clips >30 s que repiten lo mismo o mezclan variantes; un wall walk o
  explicación necesaria puede justificar más tiempo. No recortar una fase para
  cumplir un máximo arbitrario.
- Añadir margen visible antes de inicio y después del final; no usar tiempo de
  anuncio, capítulo, logo o thumbnail como timestamp de ejecución.
- Elegir `correct_execution` solo después de revisión técnica por coach; un
  video oficial no convierte automáticamente cada fotograma en ejemplo perfecto.

No hay evidencia suficiente para pedir reemplazos. Las referencias actuales se
conservan. La fase A entrega trazabilidad de identidad y pendientes; **la aprobación
visual y temporal de los segmentos sigue abierta**.
