# Propuesta de política S11 y dependencia de respaldo S16

Fecha: 2026-10-11. **POLÍTICA APROBADA por respuesta explícita «Si» del propietario a la consulta S11/S16. MODO EFECTIVO NO ACTIVO.** La aprobación comprende gracia 24 h, cuarentena 7 días, backups 7 diarios + snapshot pre-release 30 días, RPO 24 h/RTO 4 h; no autoriza eliminación real, deploy ni proveedores. El arranque queda en dry-run; destino, responsable y evidencia de restore S16 pendientes.

## Política aprobada; condiciones de activación pendientes

| Categoría | Propuesta | Condición |
|---|---|---|
| Foto referenciada por sesión, otra entidad o contexto vigente | Conservar mientras exista referencia; no aplicar expiración por antigüedad | Incluir referencias múltiples, conversaciones cifradas y semana compartida viva; no asumir que solo training_session_id identifica uso |
| Cuenta desactivada | Bloquear lectura/compartición según S02/S05; conservar archivos referenciados | La desactivación no constituye permiso de borrado; exportación/eliminación asistida requiere decisión explícita |
| Foto sin referencias verificadas, web o WhatsApp | Elegible tras 24 h desde primera constatación de ausencia de referencias | El TTL WhatsApp de 24 h existe hoy; el cómputo unificado propuesto no se activa sin aprobación. Nunca usar solo mtime/fecha de subida para decidir |
| Foto elegible conocida | Cuarentena privada reversible 7 días antes de eliminación física | Revalidar referencias/bloqueos antes de mover/eliminar; preservar posibilidad de rollback; impedir unlink antes de una decisión persistida y recuperable |
| Archivo legacy, ruta desconocida o contexto no descifrable | Conservar y marcar para revisión manual | Ausencia de evidencia no demuestra ausencia de referencia |
| Archivo temporal nativo audio/FFmpeg | Mantener limpieza local del TemporaryDirectory existente | No ampliar la retención ni archivar grabaciones por esta tarea |
| Ejecución inicial de limpieza | Solo inventario/dry-run | El modo efectivo permanecerá bloqueado sin política configurada/aprobada, respaldo coherente y restore comprobado S16 |
| Backups (propuesta ya presente en runbook) | 7 respaldos diarios + copia pre-release conservada durante los 30 días del piloto | Cifrados, acceso restringido, claves separadas, integridad y eliminación aprobada; destino y responsable todavía por definir |
| Objetivos de recuperación | RPO máximo 24 h; RTO máximo 4 h | Objetivos propuestos, no medidos ni SLA; requieren aprobación y ensayo |

La cuarentena y los respaldos retienen datos privados durante los plazos propuestos aunque no exista lectura pública. Aceptar la propuesta debe incluir estos plazos; no se presume aprobación por aprobar el alcance técnico general.

## Implementación por etapas tras aprobación

1. Configuración controlada/validada, valores aprobados y evidencia de aprobación sin secretos; modo de limpieza efectiva deshabilitado hasta superar S16.
2. Inventario desde el root privado, normalización de rutas y rechazo de symlinks/escapes; referencias TrainingImage/TrainingSession/WhatsAppMedia/ConversationState y relaciones públicas derivadas; legacies ambiguos excluidos.
3. Dry-run por identificadores internos y conteos sin nombres, fotografías, teléfonos, tokens o contenido. Protecciones ante worker detenido y carreras entre nueva referencia y limpieza.
4. Journal/estado recuperable mínimo para cuarentena/commit; evitar borrado físico seguido de rollback de DB que deje una fila sin archivo. Exportación/limpieza individual asistida, sin reenvíos ni borrado masivo automático.
5. Pruebas sintéticas: referencias compartidas/múltiples, contexto activo/expirado, share activo/revocado/expirado, inactividad, legacy, falla de commit, reanudación de worker y restauración.
6. Preparar documentación/pruebas aisladas de dependencia S16 según la autorización del encargo; no declarar S11 cerrada ni S16 implementada solo con este plan. Ningún restore sobre base activa.

**Sin autorización de gasto, proveedores reales, deploy, altas, migraciones persistentes ni eliminación de archivos reales.** El destino/operador de backup sigue pendiente y no se sustituye por una ruta inventada.
