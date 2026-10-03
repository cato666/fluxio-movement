# Bitácora de entrenamiento

## Objetivo y diseño acordado

Registrar entrenamientos aunque no exista un video. El atleta entra a Bitácora,
inicia una conversación por sesión y describe el WOD por texto, imagen o voz.
Antes de guardar confirma una ficha editable. El historial presenta fecha,
entrenamiento y resultado; el detalle conserva programación, ejecución y contexto.
En teléfono el registro ocupa una columna; en escritorio conversación y ficha
comparten una vista de dos columnas. Se mantiene la identidad verde de Fluxio.

## Datos y reglas

- Fecha local del entrenamiento, título y bloques programados.
- Resultado realizado, cargas, series, repeticiones y adaptaciones explícitas.
- Esfuerzo percibido opcional de 1 a 10; no informado se conserva como nulo.
- Texto original como evidencia; nunca asumir Rx ni deducir resultados desde el WOD.
- Videos opcionales: asociar análisis propios a un movimiento y serie/ronda.
- Cada atleta accede exclusivamente a sus sesiones y análisis.
- Datos inciertos requieren corrección; no se inventan cargas ni resultados.

## Fases

1. **Base implementable:** sesiones persistentes, entrada por texto, ficha editable,
   historial y edición; vincular un análisis existente con contexto de movimiento.
   El texto se conserva íntegro; en esta fase no se promete extracción automática.
2. **Interpretación:** lectura de pizarra y extracción estructurada por IA de bloques
   de fuerza, por tiempo, AMRAP y EMOM; resultado separado de programación, campos
   inciertos y preguntas concretas. Imágenes privadas con validación y límites.
3. **Voz:** transcripción editable, permisos de micrófono y recuperación de errores;
   interpretar el texto con el mismo flujo de confirmación.
4. **Seguimiento:** búsqueda, comparaciones entre sesiones equivalentes y acceso
   contextual desde el análisis de video.

## Criterios de aceptación de fase 1

Crear y recuperar una sesión sin video; editar sin perder contexto; rechazar RPE
fuera de rango; rechazar análisis ajenos y sesiones ajenas; permitir varios bloques
en el texto; mostrar vacíos, errores, carga y guardado. La foto y el micrófono se
incorporan cuando sus integraciones funcionen. Aplicar migración 0016 al desplegar.

## Primera entrega

Fase 1 implementada en `/training`: registro por texto con confirmación manual,
edición, historial de las últimas 200 sesiones y videos opcionales. Programación,
resultado y adaptaciones se conservan como texto, todavía sin descomposición por
serie ni métricas comparables. La siguiente fase debe agregar bloques estructurados
y extracción desde texto e imagen. No hay OCR, transcripción ni chat con IA aún.

Validación: 165 tests Python, 41 tests JavaScript existentes y prueba de navegador
de creación/lectura/edición en escritorio y móvil. Migración verificada desde una
base nueva de pruebas. La aplicación principal no se ha desplegado ni migrado.

## Fase 2: interpretación de texto y pizarra

Implementada la extracción de un borrador con bloques de fuerza, por tiempo,
AMRAP, EMOM u otros. Cada bloque contiene título, formato, esquema y ejercicios
con su dosis; las series, reps y cargas mantienen las unidades originales en texto.
El resultado personal, adaptaciones y RPE se extraen por separado. La IA no debe
atribuir resultados de terceros, completar benchmarks por memoria ni asumir Rx.
Los datos desconocidos se dejan vacíos; las preguntas aparecen como pendientes.
El atleta agrega aclaraciones al texto y reinterpreta o edita la ficha directamente.

Los bloques muestran un resumen y despliegan su editor; pueden agregarse o quitarse
bloques y ejercicios. Editar la programación libre elimina los bloques anteriores
para evitar contradicciones. Reinterpretar reemplaza la ficha, con aviso previo en
pantalla; nunca guarda automáticamente ni cambia la fecha seleccionada.

Las fotos se suben por una API autenticada, con propietario, máximo 8 MB y formatos
JPEG/PNG/WebP. Se decodifican y normalizan a JPEG, quitando metadatos, limitando
resolución y sin exponerlas como archivos estáticos públicos. La sesión conserva
el ID de su imagen; solo su atleta puede consultarla, interpretarla o vincularla.
Quitar la foto la desvincula; esta fase no elimina archivos ni depura cargas huérfanas.

Configuración: `OPENAI_API_KEY`, `TRAINING_AI_ENABLED` y `TRAINING_AI_MODEL` (si
vacío, usa `AI_REASONING_MODEL`). Sin clave, la API devuelve 503 y permanece el
registro manual. Los fallos conservan la ficha actual. Aplicar migración 0017.
La voz se incorpora en la fase 3 descrita debajo.

Validación de fase 2: 173 tests Python, 41 JavaScript y flujo de navegador de carga
real de foto, edición de bloques, guardado/reapertura y recuperación ante error,
con respuesta de IA simulada. Integración OpenAI verificada por separado con una
pizarra sintética y texto: carga programada/realizada, resultado y RPE separados.
La vista previa aislada no tiene clave de IA; no se trasladaron credenciales.
La aplicación principal sigue sin desplegar ni migrar estos cambios.

Referencias: [entrada de imágenes](https://developers.openai.com/api/docs/guides/images-vision)
y [salidas estructuradas](https://developers.openai.com/api/docs/guides/structured-outputs).

## Fase 3: voz

Entrada por micrófono con MediaRecorder en HTTPS/localhost. El atleta solicita
permiso, graba hasta 3 minutos, termina, escucha y decide transcribir o descartar.
El audio se mantiene local hasta pulsar Transcribir; un fallo conserva la grabación
para reintentar. El texto se añade a la descripción existente sin sobrescribirla y
puede corregirse antes de interpretar el WOD. No interpreta ni guarda por sí solo.
Se liberan micrófono y URLs locales al terminar o salir. Los permisos denegados y
navegadores incompatibles explican cómo continuar escribiendo. El texto/ficha se
bloquean durante grabación/transcripción para evitar cambios concurrentes.

API autenticada `/api/training-sessions/transcribe`: máximo 8 MB, contenedores
WebM/MP4/WAV, validación real con FFprobe y conversión con FFmpeg a WAV mono.
Verifica duración incluso cuando el navegador no incluye ese dato en el WebM.
Los temporales se eliminan; no se conserva audio en la base ni en almacenamiento
del producto. Procesamiento con protocolos locales y tiempos de espera limitados.
`TRAINING_VOICE_ENABLED` habilita el servicio y `TRAINING_TRANSCRIPTION_MODEL`
selecciona el modelo (por defecto `gpt-transcribe`); requiere `OPENAI_API_KEY`.
No necesita migración ni dependencias nuevas. La vista previa permanece sin clave.

Pruebas de voz: validación/normalización real de WAV y proveedor simulado; límites,
roles, audio ilegible, transcripción vacía y errores. La prueba de navegador usa
micrófono sintético y respuestas simuladas para grabación, reproducción, reintento,
texto añadido y permiso denegado. No se ha probado reconocimiento de habla real ni
un teléfono físico. Referencia: [transcripción de audio](https://developers.openai.com/api/docs/guides/speech-to-text).

Resultado de validación: suite de 181 tests Python y 41 tests JavaScript existentes
aprobada; 9 tests específicos de voz aprobados tras agregar el caso WebM sin duración.
Grabación, escucha, error/reintento, texto añadido y permiso denegado verificados en
navegador con micrófono sintético. La vista previa local se actualizó sin credenciales;
la aplicación principal sigue sin desplegarse.
