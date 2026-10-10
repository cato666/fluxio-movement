# Pilot v1.0 — Alcance propuesto

Fecha: 2026-10-10, America/Santiago. Estado: plan para revisión y aprobación; **NO-GO actual**. Duración: 30 días desde la activación autorizada de los primeros 3 atletas; cohorte final de 10–15 atletas de CrossFit. Sin cobros ni suscripciones. Este documento no autoriza implementación, despliegue, migraciones persistentes, altas reales ni consumo de proveedores.

## Contrato del piloto

| Capacidad incluida | Límite y condición de habilitación |
| --- | --- |
| Alta asistida y login | Operador designado; cuentas individuales, activas y sin credenciales demo. Sin promesa de autoservicio o recuperación automática. |
| Bitácora manual, historial, edición y eliminación | Datos del propietario; confirmación de borrado y conservación tras reinicio. Eliminar sesión no implica hoy eliminar su archivo fotográfico. |
| Interpretación texto/foto | Borrador revisable; guardar explícitamente. JPEG/PNG/WebP, 8 MB y 24 MP máximos actuales; HEIC fuera del contrato. |
| Audio web | Permiso de micrófono y HTTPS; máximo actual 8 MB/180 s; texto revisado, audio temporal no archivado. |
| WhatsApp texto/foto/audio | Vinculación verificada, cuenta activa, límites efectivos por atleta/canal, confirmación vigente y control de gasto. Sin iniciar análisis biomecánico desde video del chat. |
| Resumen semanal | Estadística factual de registros, semana calendario Santiago; RPE con muestra. Sin envío programado, PR ni mejora deportiva inferida. |
| Enlace semanal | Opt-in separado de Guardar, aviso previo sobre enlace público vivo, notas/fotos futuras, TTL máximo 168 h y revocación. Sin publicación automática. |
| Análisis técnico de video | Solo intersección de catálogo supported, perfil/vista cargable y casos técnicos validados del candidato exacto. Calidad insuficiente exige abstención/error claro. |
| Coach opcional | Solo coach activo con disponibilidad confirmada y acceso autorizado al atleta/review; cupo y plazo acordados. Sin promesa de disponibilidad universal. |

Catálogo supported actual: air_squat, overhead_squat, deadlift, clean, snatch, thruster y handstand_push_up. Catálogo anuncia lateral/front; API usa side/front. Antes de habilitar cada combinación debe validarse su mapeo y perfil efectivo; no se certifican 14 combinaciones por estas etiquetas. Los otros 13 ejercicios reference_only y los perfiles nuevos locales no amplían este alcance.

## Exclusiones y compatibilidad

Postergar progreso/PR, nuevos deportes, pagos/suscripciones, red social/desafíos, ampliación biomecánica, asistente longitudinal y toda funcionalidad no implementada. Mantener TrainingSession, Analysis, reviews, contratos HTTP/WhatsApp y lectura de datos legacy. Correcciones pequeñas de seguridad/operación se proponen en el backlog; no se ejecutan en esta etapa. No reconstruir arquitectura ni introducir cola de video nueva para este piloto.

## Fuentes y entregables

Los ocho documentos de [product-audit](../product-audit/01_FUNCTIONAL_INVENTORY.md) son base histórica del 09-10: 01 inventario, 02 recorridos, 03 arquitectura, 04 multidisciplina, 05 brechas, 06 Free/Pro, 07 roadmap y 08 resumen. Sus propuestas comerciales y expansión quedan fuera de este piloto. La inspección actual contrasta código, migraciones y tests; no certifica proveedores ni despliegue.

Leer en orden: [readiness y resumen ejecutivo](RELEASE_READINESS.md), [backlog](STABILIZATION_BACKLOG.md), [validación](TEST_PLAN.md), [runbook](DEPLOYMENT_RUNBOOK.md), [operación](PILOT_OPERATIONS.md), [gates](GO_NO_GO_CHECKLIST.md).
