# S17 — Historial: límite explícito y conservación verificada

Fecha: 2026-10-11. Rama `codex/pilot-v1-stabilization`. Base revisada `c5d176481fcacae0e61b4e1f644017bbe050db0b`, worktree inicialmente limpio. Una sola tarea seleccionada por autorización actual: la siguiente ejecutable con recursos locales. Estado: **cierre técnico local PASS con mitigación explícita del límite 200; pendiente de revisión del propietario.** Dirigidas y suites completas PASS. El cierre local es una mitigación explícita del listado de 200, no una ampliación funcional ni GO.

## Auditoría S08–S18 y selección

Se revisaron informes, backlog/dependencias, código, Git y herramientas disponibles. La autorización actual permite elegir una tarea ejecutable sin completar antes gates externos; no elimina las dependencias propias de cada fase.

| Fase | Estado verificado / dependencia |
|---|---|
| S08 | Implementada/validada históricamente: código dfe2f87, entrega f1a8bf4; 402/429/UNCERTAIN. No se reimplementa. |
| S09 | Cierre local PASS: código 1d739a8, entrega f7a7006; depende S06 ya implementada. |
| S10 | Cierre local PASS: código 09b4215, entrega 023736b; depende S01/S05; E2E integrado S05 permanece gate externo al cierre local. |
| S11 | Parcial: código a4aefd7, documentación bae3d9a; conserva fotos/inventario read-only. Depende S05/S16; cuarentena y eliminación bloqueadas. |
| S12 | No iniciada; S09 disponible, S16/restore pendiente. |
| S13 | No iniciada; S08 disponible, S12 pendiente; operador/canal/recepción de alertas no certificados. |
| S14 | No iniciada; S01 disponible. Build/identidad/escaneo del candidato no certificados. Dockerfile requiere obtención de paquetes/modelo; no scanner trivy/grype/syft disponible en PATH ni evidencia de base de vulnerabilidades local vigente. No se reutiliza digest de imagen anterior ni se afirma que S14 sea imposible: falta preparar/verificar sus prerrequisitos, fuera de esta tarea. |
| S15 | No iniciada; depende S14, gates/protección reales de CI no verificados; no se dispara workflow. |
| S16 | Preparación documental completada en c5d1764; depende S01/S14. Política aprobada; proveedor/destino/operador y restore operativo pendientes. No se repite preparación ni se realizan backups. |
| S17 | Seleccionada: depende de límites ya aprobados; pruebas 199/200/201 y mitigación acotada ejecutables con DB tmpfs y UI simulada existentes. |
| S18 | No iniciada; S03 disponible, S12 pendiente; coach/capacidad/clips reales autorizados sin certificar. |

No se ejecutaron builds, scans nuevos de vulnerabilidades, infraestructura, S12–S16 ni S18. La selección S17 no declara completadas fases omitidas.

## Antes, defectos reproducidos y cambio

El servicio devuelve hasta 200 filas del atleta, ordenadas por trained_on y created_at descendentes. El resumen semanal tiene consulta independiente, sin ese cap. Detalle/edición usan ID+ownership sin cap. Guardar manualmente no impone un máximo histórico de 200.

Reproducción antes de corrección: Python 7 PASS / 1 FAIL (empates sin orden total definido); JS S17 1 PASS / 2 FAIL (aviso ausente en 200/201). No pérdida real ni datos persistentes intervenidos. Defectos P2 de presentación y estabilidad del corte, mitigados en el alcance aprobado S17.

- `app/services/training_service.py`: añade ID descendente como tercer criterio para desempatar fechas idénticas; mantiene orden principal, cap 200, ownership, campos y contrato existentes. UUID no representa fecha adicional; solo desempate estable.
- `app/static/training.js`: cuando recibe 200 elementos muestra una nota accesible: «Esta lista muestra hasta 200 entrenamientos, ordenados por fecha. Los registros anteriores se conservan y puedes consultarlos por semana en el resumen semanal.» No afirma que sean todos ni que necesariamente existan más: la API no entrega conteo total. No inventa un total local ni confunde cuota IA con capacidad de almacenar.
- `tests/test_training_history_limit.py`: ocho casos de boundary, conservación, desempate, detalle/edición/foto histórica, aislamiento entre atletas, cuenta inactiva y guardado manual sobre cap sin consumo IA.
- `tests/training-ux.test.cjs`: tres casos 199/200/201, aviso solo cuando alcanza cap, resumen separado, accesibilidad y ausencia de overflow a 320/390/430/1440px.

No paginación, exportador nuevo, módulo de progreso, eliminación para liberar espacio, límites nuevos ni cambios de políticas. Sin cambio de modelos/migración/revisión 0024 ni respuesta HTTP `{items: [...]}`. Cliente legacy sigue recibiendo los mismos campos; empates adquieren selección determinista.

## Pruebas y resultados

PostgreSQL 17.6 `movement_test`, guard TEST_DATABASE_RESET=1, PGDATA tmpfs sin mount persistente. Solo dos contenedores de pruebas propios reutilizados; red existente Internal=true y ningún puerto publicado. Alembic desde cero y roundtrip de contrato únicamente sobre DB desechable. Proveedores reales deshabilitados; ningún OpenAI/Kapso real.

| Verificación | Resultado |
|---|---|
| S17 backend | PASS: ocho casos, incluidos 199/200/201 y acceso al registro excluido del listado |
| Dirigidas + regresiones integridad/semana/contrato/fotos | PASS: 57; 0 FAIL / 0 ERROR / 0 SKIPPED; 22.63 s |
| Python completa | PASS: 803; 0 FAIL / 0 ERROR / 0 SKIPPED; 245.82 s; regresiones previas incluidas |
| JavaScript completa | PASS: 75; 0 FAIL / 0 SKIPPED / 0 CANCELLED; 25.962 s; incluye tres casos S17 |
| AST/hash de cuatro fuentes y diff | PASS; hashes runner coincidentes con candidato, sin bytecode generado |
| Workspace original | PASS: 153 paths, rama/HEAD/estado originales intactos |
| Exportación de historial | SKIPPED: no existe exportador implementado en el alcance; no se añade ni certifica uno. Consulta semanal y detalle propio sí ensayados. |
| E2E integrado S05 | BLOCKED; pruebas de navegador/API simulada y TestClient no sustituyen integración real |
| Restore real / video costos / EasyPanel / canales reales | PENDIENTE, no ejecutados |

Los 57 dirigidos incluyen los ocho S17 y son subconjunto de la suite completa; no sumar. Fallos iniciales son reproducciones resueltas, no resultado final. Tres warnings históricos de deprecación FastAPI/Starlette. Scanner limitado de patrones sobre 287 archivos rastreados sin coincidencias de credenciales/artefactos locales; no sustituye el scan de vulnerabilidades pendiente S14. Contenedores desechables propios detenidos tras conservar evidencia, sin borrar imágenes/contenedores/volúmenes existentes.

Evidencia local externa: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s17-validation-20261011/` con before.xml, targeted.xml, full.xml, summary.json, javascript.log, source-checksums.json y artefactos JS. Los datos son sintéticos. No se registran teléfonos, tokens, contraseñas o workouts reales.

## Riesgos y mitigación operativa

El listado **sigue limitado a 200**. No se garantiza que la cohorte nunca lo alcance: registro manual sin cuota histórica puede superar 200. La nota evita presentar la lista como historia completa, la consulta semanal abarca registros fuera del corte y detalle/edición privada por ID siguen funcionando. Para registros antiguos que no tienen enlace en el listado principal, consulta por semana permite lectura resumida; editar desde esa tarjeta no queda añadido por S17. Consulta por ID requiere conocer ese ID. No prometer paginación ni exportación completa disponibles.

Operador revisa volumen de historial por atleta mediante procedimiento autorizado; no elimina sesiones para liberar lista ni utiliza cuotas IA como límite de retención. Aviso operativo a 150 es propuesta del plan, no alerta automática implementada. Si se exige navegación completa/edición desde semanas anteriores o exportación como condición de alta, requiere una tarea posterior aprobada; esta entrega aplica la mitigación explícita compatible del backlog S17. No amplía la arquitectura.

Sin cambios de privacidad/sharing/coach/autenticación/cuotas; regresiones previas se verifican en suite completa. Cuarentena/limpieza S11, job/restore S16 y demás fases mantienen sus estados. Ningún fixture certifica destino o proveedor real.

## Cierre y revisión

Commit final: **un único commit independiente S17 con código, pruebas e informe**; su SHA se obtiene con `git log -1 --format=%H -- docs/pilot-v1/S17_IMPLEMENTATION_REPORT.md` y se entrega en el mensaje final. No contiene cambios funcionales de otras fases. Worktree limpio verificado después del commit. Se detiene para revisión conforme al último encargo, sin iniciar otra fase.

Pilot **NO-GO**. Cinco bloqueos obligatorios conservados: E2E integrado S05; restauración real de respaldos; costos adicionales de video; paridad con EasyPanel; pruebas reales de canales habilitados. Sin push/merge/deploy, migraciones persistentes, modificación del original o consumo de proveedores.
