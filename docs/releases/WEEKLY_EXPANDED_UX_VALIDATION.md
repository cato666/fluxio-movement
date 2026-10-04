# Validación del resumen semanal expandido

Fecha: 2026-10-04. Alcance: composición del resumen semanal autenticado dentro de Bitácora y presentación de las acciones existentes de compartir. Sin cambios adicionales de backend, API, permisos o expiración.

## Composición

Semana destacada, tres métricas horizontales, actividad discreta y filas compactas con foto, entrenamiento, resultado y esfuerzo. Navegación por iconos con áreas de 44 px; a 320 px las acciones secundarias quedan en una segunda línea para preservar la fecha completa. Compartir abre un diálogo en escritorio y un panel inferior en móvil.

Iconos: SVG lineales propios de la familia existente, trazo 1.75; no se añadió una librería.

## Persistencia y seguridad

Se consultan los enlaces activos persistidos mediante la API existente al montar o cambiar de semana. Se validó persistencia tras recargar, revocación individual y general, recuperación de errores y copia manual cuando el navegador rechaza el portapapeles. No se guardan tokens en localStorage.

La API devuelve identificador y vencimiento, pero conserva solamente el hash del token: las URLs anteriores y su fecha de creación no son recuperables. Se muestran sus datos y revocación; solo las URLs recién creadas en esta vista pueden copiarse. No se inventan fechas de creación.

## Evidencia

- Suite Python completa: 454/454; tres avisos de deprecación existentes.
- Suite JavaScript completa: 64/64.
- Recorrido HTTP real con PostgreSQL: navegación semanal, creación, recarga, fotos anónimas y revocación con acceso posterior 404.
- Capturas en `results/weekly-expanded/`: expanded y sheet a 1440, 768, 430, 390 y 320 px; las capturas de diálogo usan viewport real.
- Pruebas de teclado, Escape, retorno de foco, áreas táctiles, ausencia de overflow y preferencias de movimiento reducido.
- Detector: sin hallazgos bloqueantes; revisión independiente: ambos ajustes materiales resueltos, disposición ship sobre esos ajustes. Documentación del sistema en WEEKLY_EXPANDED_DESIGN_CHECK.md.

## Movimiento

| Interacción | Antes | Ahora |
|---|---|---|
| Abrir resumen | Entrada genérica CSS | Opacidad y desplazamiento de 4 px, 160 ms; cierre 100 ms |
| Abrir compartir | Controles dentro del resumen | Entrada de diálogo con opacidad y 12 px, 200 ms |
| Teclado / movimiento reducido | Comportamiento heredado | Apertura inmediata; animaciones cancelables al desmontar |

## Límites pendientes

No se probó en teléfono físico. La asociación a detalles usa los entrenamientos disponibles en el listado autenticado actual (máximo 200); un registro sin coincidencia se muestra sin enlace falso. Las limitaciones de recuperación de URLs requieren un cambio de contrato separado si se desea resolverlas.

Disponible localmente en http://localhost:8000/training. Health y recurso CSS respondieron 200. No se realizó deploy a producción.
