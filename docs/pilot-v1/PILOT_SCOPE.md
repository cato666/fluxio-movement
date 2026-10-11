# Estado vigente — cierre final Pilot A

Validación local final del candidato `03cfd4387a75f70fae60ccd2108a83d24dc57f31`: Python **820 PASS, 1 SKIPPED, 0 FAIL** (257,41 s); JavaScript **77 PASS, 0 FAIL/SKIPPED**. La prueba omitida requiere WEEKLY_RELEASE_PUBLIC_BASE_URL real y queda **NOT RUN**, sin afirmar paridad de dominio. PostgreSQL nuevo tmpfs, red interna nueva, sin puertos Docker publicados ni credenciales de proveedores; migraciones desde cero y worker vacío PASS; contenedores propios detenidos. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-2e4m_dlq/offline-tests.log` y `environment.json`. Tres advertencias de deprecación no bloquean estas pruebas. Workspace original: 153 rutas verificadas sin cambios.

Fecha: 2026-10-11, America/Santiago. Rama: codex/pilot-v1-stabilization. Candidato auditado: `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. **Pilot A NO-GO**. Alcance obligatorio: bitácora + WhatsApp + video certificado + coach titular/suplente, 3–5 atletas, 30 días. Esta entrega no autoriza proveedores, infraestructura persistente ni publicación.

Estados: PASS = evidencia ejecutada y limitada a su entorno; FAIL = defecto/evaluación fallida demostrada; BLOCKED = falta autorización, acceso, responsable o dependencia; NOT RUN = sin ejecución. Resultados históricos no certifican el candidato final ni el destino.

## Alcance vigente Pilot A

3–5 atletas CrossFit durante 30 días. Obligatorias bitácora completa, WhatsApp Kapso con OpenAI backend, video por combinaciones certificadas y revisión humana con titular/suplente. Respaldo Cloudflare R2, bucket identificado fluxio-movement-backups; archivos privados en storage actual. No nuevas capacidades ni catálogo; mes/año, pagos, red social y perfiles experimentales excluidos. Sin coach/video certificado no GO.

Consultar [readiness final](PILOT_A_FINAL_READINESS.md), [video](PILOT_A_VIDEO_CERTIFICATION.md), [WhatsApp](PILOT_A_WHATSAPP_VALIDATION.md) y [release](PILOT_A_RELEASE_PLAN.md).

---

## Evidencia histórica conservada — no sustituye estado vigente

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
