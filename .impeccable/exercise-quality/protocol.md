# Protocolo pendiente de dataset y hardware

## Dataset

Por ejercicio squat/deadlift/clean, conseguir grabaciones reales consentidas: ejecución correcta, técnica deficiente etiquetada por coach, repetición parcial, varias repeticiones, iluminación baja, encuadre imperfecto y oclusión parcial. No pedir realizar movimientos peligrosos para fabricar errores: usar ejemplos existentes aprobados por coach. No contar recortes, versiones degradadas o duplicados como sujetos/videos independientes.

Cobertura actual: squat ninguna; deadlift seis clips de una repetición y tres etiquetas fuente, dos sujetos; clean un complejo mixto con dos completas y un intento parcial. Iluminación baja, oclusión y encuadre adverso controlados faltan en los tres ejercicios. Técnica de clean sin adjudicación. Squat requiere fuente con licencia verificable o material propio; las fuentes investigadas no proporcionaron en esta ejecución un clip elegible incorporado.

Antes de analizar: ID, fuente/licencia/consentimiento, SHA256, ejercicio, vista real, condición, duración, FPS y resolución; conteo humano y ventanas inicio/recepción/cierre sin ver salida del algoritmo. Coach adjudica desacuerdos. Congelar versiones/modelo/perfiles. Registrar resultado, rechazo, tiempos, eventos, observaciones y confianza con su tipo. Emparejar eventos uno a uno mediante ventanas previamente etiquetadas; contar FP y FN, no solo diferencia neta de conteos. No generar porcentage de utilidad con cero sugerencias. Coach revisa todas las sugerencias y etiqueta útil/dudosa/irrelevante antes de ver métricas globales.

## Android Chrome e iPhone Safari reales

Estado de todas las pruebas: **NO EJECUTADO — sin dispositivos**. Registrar modelo, OS, navegador, fecha, conexión, formato/codec del archivo, captura de pantalla o grabación y respuestas del backend. Acceso mediante LAN de prueba o HTTPS autorizado; localhost del teléfono no apunta al PC. No exponer servidor públicamente como atajo.

1. Atleta: seleccionar MP4 desde archivos; verificar nombre, preview, reemplazo y subida persistida.
2. Seleccionar/capturar desde cámara: permisos, cancelación, orientación, codec real, preview y compatibilidad backend. Registrar rechazo con mensaje real, sin simular éxito.
3. Con teclado virtual abierto en objetivo/selector/feedback: CTA accesible, focus visible, ausencia de zoom y scroll bloqueado; conservar texto al cerrar teclado.
4. Video original y anotado: iniciar/pausar, pantalla completa, controles, audio si existe, seek y salto desde anotación a timestamp; esperar metadatos y confirmar posición efectiva.
5. Medir hit targets ≥44×44 CSS px; comprobar toque real en CTA, reemplazo, selector y navegación de momentos. Sin hover pegado.
6. Rotar vertical/horizontal con video en reproducción y formulario pendiente; conservar datos, no ocultar controles ni desplazar al usuario de forma inesperada; revisar safe areas.
7. Durante subida cortar y recuperar Wi-Fi/datos: distinguir fallo de subida de procesamiento, conservar archivo/borrador, reintentar sin duplicados y reconsultar backend.
8. Cortar conexión durante polling: mensaje temporal, recuperación y estado final persistido; fallo real de procesamiento debe permanecer distinguible.
9. Comparar mismos archivos y acciones con desktop. Documentar diferencias comprobadas; emulación responsive previa no sustituye estos pasos.

Cerrar solo con ambos equipos ejecutados, defectos documentados y persistencia reconsultada. Si quedan incompatibilidades de codec/captura, clasificarlas como calidad del video, UX o infraestructura con evidencia, no como éxito parcial silencioso.
