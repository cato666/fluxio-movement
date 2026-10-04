# Fluxio — recomposición visual

Fecha: 2026-10-04. Brief: reemplazar la composición anterior de bitácora, registro y recap utilizando los mockups como referencia conceptual.

## Antes y después

| Antes | Después |
| --- | --- |
| Cabecera pequeña y aislada | Título 44 px, subtítulo y CTA alineados |
| WhatsApp textual | Icono, descripción y chevron; vinculación existente conservada |
| Semana sin contenedor | Tarjeta horizontal con fecha corta y métricas reales |
| Actividad solo textual | Siete días accesibles con altura según número de sesiones |
| Gestión de enlaces entre el contenido principal | Gestión y mensajes dentro de Ver resumen |
| Columna de 800 px | Bitácora y registro hasta 1080 px |
| Nombre sin categoría | Badge derivado del formato o categoría explícita en el título |
| Metadata sin símbolos coherentes | Fecha y esfuerzo con SVG lineales de 1.75 px |
| Registro sin secciones diferenciadas | Banner previo a revisión, fecha/nombre agrupados, resultado protagonista y optionales con iconos |
| Recap largo | Hero, destacados factuales, timeline compacta y ejercicios reconocidos que se repiten |

La sidebar de 208 px ya era compacta; se conserva para priorizar la recomposición del contenido. Se mantiene el logo existente: no se crea un sustituto del símbolo F del mockup.

## Evidencia

Capturas antes: results/visual-v2/. Después: results/recomposition/.
Comparación visual de las cuatro vistas: results/recomposition/comparison.html.
Cobertura de las tres pantallas: 320, 390, 430, 768 y 1440 px; sin desbordamiento horizontal en los E2E.

- JavaScript: 62/62.
- Python semanal y seguridad: 18/18 antes de añadir dos checks de presentación factual y semana vacía.
- E2E atleta/coach/registro y E2E semanal/sharing: aprobados, con fotos, audio, edición y revocación.
- Detector: una ejecución sin hallazgos; results/releases/recomposition-design-detector.json.
- Revisión independiente: composición conforme al brief. Dos correcciones responsive puntuadas resueltas; disposición final ship al alcance de esas correcciones. Persistencia actualizada en DESIGN.md, DESIGN_V2.md y sidecar JSON.
- Regresión responsive: métricas medidas dentro de sus tarjetas y prescripción de tres ejercicios completa sin abrir el editor, a los cinco anchos.
- Suite Python completa: 454/454, con tres advertencias existentes; results/releases/recomposition-python-full.log.

## Alcance y límites

Backend, contratos API, rutas, permisos, TTL y revocación conservados. El recap presenta los mismos campos autorizados y mantiene semana actualizable, escaping, CSP, no-store, noindex y no-referrer.
Frecuencias: coincidencias explícitas de ocho nombres de ejercicios en el texto autorizado, por sesión; se muestran solo los repetidos. No representa un análisis exhaustivo de todos los movimientos ni evalúa técnica o rendimiento.
Los datos y fotos de las capturas son sintéticos; AI externa determinista en E2E. No certifica Kapso/OpenAI real.
Motion: entrada breve de la libreta, cambio de semana y contenido desplegado; reduced-motion elimina estas animaciones. No hay polling ni animación continua.
Falta prueba en teléfono físico para teclado, safe areas y comportamiento táctil. Sin push ni deploy en esta fase.
