# S10 â€” Integridad del registro: reproducciÃ³n y parada obligatoria

Fecha: 2026-10-11. Rama codex/pilot-v1-stabilization. Base documental f7a70067fc812d4c1248f2c2ccf5eccd6fee777e; cÃ³digo S09 1d739a86e73d9d1cc5e0c89d80eb809c699f03be.

**Estado: FAIL / BLOCKED, NO IMPLEMENTADA.** No cambios funcionales S10 ni commit de implementaciÃ³n. El commit documental de esta parada no constituye cierre tÃ©cnico S10.

## Evidencia reproducible

Tres casos sintÃ©ticos sobre PostgreSQL desechable: **0 PASS / 3 FAIL / 0 ERROR / 0 SKIPPED**, XML final en 1,37 s. No falla ambiental ni proveedor real. ReproducciÃ³n: C:/Users/desarrollo/AppData/Local/Temp/fluxio-s10-validation-20261011/reproduction.py y reproduction.xml. Se copiÃ³ solo al runner temporal como tests/test_s10_reproduction.py; no se incorporÃ³ un test fallido a la suite del candidato.

| ID / severidad | Pasos y resultado observado | Causa / archivos |
|---|---|---|
| S10-D01 / P1 | POST con resultados, adaptaciones, RPE y fuente. PUT vÃ¡lido con solo trained_on/title/workout. Resultado observado: result_text, adaptations, rpe y source_text anteriores se sustituyen por defaults. | TrainingService._assign usa model_dump completo tambiÃ©n al editar; app/services/training_service.py y training_contracts.py. |
| S10-D02 / P1 | Crear registro, aÃ±adir nota por add_athlete_note (flujo WhatsApp), editar solo tÃ­tulo/programaciÃ³n. La nota desaparece de adaptations visible. La copia interna athlete_notes continÃºa presente: se verificÃ³, no equivale a una nota visible consistente. | Mismo defecto de asignaciÃ³n; detalle/semana usan adaptations. No se borrÃ³ ningÃºn dato real. |
| S10-D03 / P1 | Dos POST iguales con la misma Idempotency-Key. Ambos 201, dos IDs distintos y dos filas persistidas. Una repeticiÃ³n tras perder la respuesta podrÃ­a duplicar el registro. | El endpoint create no recibe la clave; TrainingService.create crea siempre. El botÃ³n web bloquea doble click concurrente pero no hace idempotente un reintento tras respuesta perdida. app/training.py y app/static/training.js. |

Los mÃ©todos CRUD afectados no se modificaron en S09; el diff entre S08 y S09 lo confirma. Son defectos existentes descubiertos por pruebas nuevas, no evidencia de una regresiÃ³n causada por S09. La suite anterior 769 PASS permanece evidencia de su cobertura, pero no implica que S10 estÃ© aprobada.

## Alcance revisado

TrainingService, SessionPayload, TrainingSession y relaciones con TrainingImage/Analysis; adaptador HTTP; captura y notas WhatsApp; submit web; representaciÃ³n semanal. La confirmaciÃ³n WhatsApp existente usa bloqueo de identidad/estado, versiÃ³n/token, savepoint y clear; no se encontrÃ³ en esta lectura un motivo para sustituirla. La ausencia de un hallazgo no certifica todavÃ­a todas las pruebas S10 de restart, concurrencia, medios, legacy y notas.

## CorrecciÃ³n mÃ­nima propuesta para revisiÃ³n

1. En update, asignar Ãºnicamente campos explÃ­citamente presentes (`model_dump(exclude_unset=True)`), manteniendo campos obligatorios y validaciones de propiedad. Create conserva defaults actuales. Null y listas vacÃ­as explÃ­citos siguen permitiendo limpiar campos. AÃ±adir pruebas de foto, blocks, video_links, notas y valores legacy; probar rollback ante FK/validaciÃ³n fallida.
2. Hacer persistente y por atleta la idempotencia de creaciÃ³n, con comparaciÃ³n del payload normalizado y conflicto 409 ante reutilizaciÃ³n con otro contenido. Debe sobrevivir al reinicio y conservar tombstone tras borrar: no basta un cache en memoria o deshabilitar un botÃ³n. Revisar el mecanismo mÃ­nimo antes de elegir un cambio de esquema; ninguna migraciÃ³n se ha creado/aplicado.
3. En web, mantener una clave estable al reintentar el mismo borrador y generar una nueva solo cuando cambie el payload o comience otro registro; preservar borrador al fallar. No cambiar consentimiento S05 ni consumo S06/S09 para el registro manual.
4. Mantener la atomicidad de WhatsApp y probar doble confirmaciÃ³n, botÃ³n vencido, fallo tras guardado, notas web/chat, ownership y reincio con datos sintÃ©ticos. Definir campo visible canÃ³nico sin borrar notas histÃ³ricas.
5. Promover estos tres casos a pruebas del candidato solo al implementar la correcciÃ³n, aÃ±adir concurrencia real en PostgreSQL y regresiones S02â€“S09, cerrar suites Python/JS y commit limpio antes de S11.

No se propone limpiar duplicados existentes ni restaurar campos reales sin autorizaciÃ³n, evidencia y respaldo; no se ejecutÃ³ remediaciÃ³n sobre cuentas/datos existentes.

## RazÃ³n de la parada y riesgos

El encargo establece: Â«Detente inmediatamente cuando exista ... PÃ©rdida o corrupciÃ³n potencial de datosÂ» y Â«Una prueba obligatoria fallida sin resolverÂ». Estos tres casos activan esa regla; por eso no se aplicÃ³ cÃ³digo funcional S10 ni se avanzÃ³ a S11. Se solicita revisiÃ³n de los hallazgos y autorizaciÃ³n para reanudar su correcciÃ³n acotada. No es una limitaciÃ³n de Docker ni una solicitud para publicar.

Siguen abiertos: E2E integrado S05 BLOCKED; costos adicionales de video; paridad EasyPanel; proveedores reales; backup/restore del destino. S11 requiere ademÃ¡s polÃ­tica de retenciÃ³n aprobada y S16; sus decisiones se documentan sin implementar borrado.

RecomendaciÃ³n: **NO-GO; no cerrar S10 ni continuar fases**. Sin push, merge, deploy, proveedores reales, migraciones persistentes, cuentas reales o cambios al workspace original.
