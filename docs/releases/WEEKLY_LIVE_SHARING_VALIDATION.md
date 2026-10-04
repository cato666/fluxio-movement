# Semana compartida actualizable

2026-10-04. Cambio autorizado: el mismo enlace muestra los entrenamientos actuales de su semana, incluidas nuevas fotos, resultados y notas.

- Causa: el lector público utilizaba el snapshot guardado al crear el enlace.
- Corrección: valida token, revocación y vencimiento antes de consultar por atleta propietario y semana original. Los enlaces existentes también se actualizan; no se extiende su expiración.
- Fotos: solo accesibles mientras estén vinculadas a una sesión actual del mismo atleta y semana. Eliminar o mover la sesión retira el acceso por ese enlace.
- Se conservan campos autorizados, escaping, no-store, noindex, no-referrer y CSP. No se comparten teléfonos, identidad privada, videos ni texto fuente.
- Avisos web, recap y WhatsApp explican que la semana se actualiza. Una pestaña ya abierta requiere recarga; sin polling.
- Sin migración: se conserva el snapshot histórico almacenado, pero no se utiliza para mostrar contenido ni autorizar fotos.

## Validación local

- 18 pruebas específicas aprobadas: cambios posteriores, enlace existente con snapshot vacío, fotografías, límites de semana, aislamiento entre atletas, expiración y revocación.
- JavaScript completo: 62/62.
- Python completo: 452/452; tres advertencias existentes de deprecación.
- Smoke HTTP real: mismo enlace antes/después de agregar y eliminar una sesión, seguido de revocación; aprobado.
- Vista localhost:8000 recargada conservando base y storage existentes. Sin deploy ni push.
- Evidencia de suite completa: results/releases/weekly-live-python.log.
