# S16 — ensayo sintético R2 / estado vigente

Fecha: 2026-10-11, America/Santiago. Responsable operativo confirmado por el usuario: Gastón. Base documental `1f250ddc82e7dd9292c656d856c89073493f379d`; fuentes funcionales `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. Usuario autorizó lectura y luego upload/restore sintético a `fluxio-movement-backups`; no autorizó copias del producto, scheduler, borrado, deploy ni proveedores IA. **PASS del ensayo sintético; S16 continúa PARCIAL/BLOCKED y Pilot A NO-GO.**

## Evidencia y resultados

- PASS: esquema completo migrado desde cero únicamente en PostgreSQL 17.6 tmpfs nuevo, revisión `0024_training_save_requests`; red interna nueva, sin puertos publicados, proveedores deshabilitados y sin claves OpenAI/Kapso.
- PASS: conjunto coherente sin productores/worker ni escrituras concurrentes: PostgreSQL custom dump y cuatro archivos sintéticos (foto PNG válida, original/annotated con bytes de prueba, JSON de análisis). Los archivos de video son placeholders; este ensayo no certifica reproducción, biomecánica ni flujo de coach por API/navegador.
- PASS: cifrado cliente AES-256-GCM, clave aleatoria 256 bits, nonce 96 bits y AAD; clave separada del objeto R2, directorio local de recuperación restringido mediante ACL al usuario actual. TLS validado por cliente HTTPS. Clave incorrecta rechazada mediante InvalidTag.
- PASS: PUT y GET autenticados 200; igualdad del ciphertext y SHA-256 de DB/storage. Carga final 92.197 bytes, conservada en `synthetic-validation/eb25e70ccc31/backup.tar.aes256gcm`.
- PASS: pg_restore --exit-on-error en base nueva vacía `movement_s16_restore`, sin upgrade posterior; conteos iguales: 3 usuarios, 1 entrenamiento con nota, 1 foto, 1 análisis, 1 revisión completada. Archivos restaurados en directorio nuevo; referencias DB/storage verificadas, esquema conservado.
- PASS limitado: 5,31 s de ensayo interno (preparación de datos hasta comprobación), 3,62 s desde snapshot coherente hasta verificación. No incluye creación del entorno, recuperación por otro operador ni un incidente real; no constituye RTO/RPO operativo ni benchmark de datos reales.
- NOT VERIFIED: petición anónima al endpoint S3 devuelve 400 sin contenido; esto no demuestra ausencia de dominio público o r2.dev. Configuración de política respondió 501 NotImplemented y lectura de cifrado 403 AccessDenied en inspección previa. Cifrado cliente demostrado; configuración de cifrado del proveedor no verificada.
- FAIL del primer harness: esperaba únicamente 401/403 para la solicitud anónima y R2 devolvió 400. Corregida solo la expectativa del script temporal; no se relajó el requisito de privacidad ni se cambió código del producto. Segundo ensayo ejecutado en recursos nuevos. Primer objeto cifrado y clave sintética conservados, sin borrado; no fue marcado PASS de restauración.
- PASS: ambos grupos propios de contenedores detenidos; tmpfs no contiene datos persistentes al finalizar. Ninguna imagen, volumen, contenedor existente ni objeto R2 eliminado. Dos uploads pequeños conservados; cargos reales no conciliados ni estimados como tarifa.

Evidencia local final: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-90w55bof/` (environment.json y r2-trial-results.json). Primer intento: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-_m3i4zcv/`. Claves sintéticas fuera de Git y R2, en recovery-key-private de cada evidencia; custodia solo de ensayo, no producción. Los scripts temporales se conservan fuera del producto; sus hashes figuran en S16_SYNTHETIC_R2_EVIDENCE.json. No se copia ningún .env ni valores secretos.

## Cambios, regresiones y límites

Solo documentación y plantilla JSON inerte. Ejecución, scheduler, retención destructiva y limpieza de fotos continúan deshabilitados. No cambios funcionales, modelos o migraciones. Suites completas previas del mismo código: Python 820 PASS / 1 SKIPPED (dominio real faltante), JS 77 PASS. No se repiten por un cambio documental; restore no sustituye pruebas de sesión/coach/links del sistema restaurado.

No se escribió en el workspace original. Fingerprint de 153 rutas sin cambios; estado Git original difiere del histórico porque .env.example está modificado por configuración del usuario. Credenciales renovadas según confirmación del usuario; lectura únicamente, sin imprimir ni incorporar a Git. Riesgo pendiente: credenciales reales en un archivo plantilla habitualmente rastreado; no incluirlas en ningún commit.

## Pendientes para cierre

1. Verificar R2 private/r2.dev/domains, AES-256 del proveedor y permisos mínimos; identidades writer/reader separadas y autorización del conjunto definitivo.
2. Custodia duradera y separada de claves backup y todas las versiones WhatsApp/sharing; recuperación por Gastón desde ese almacén. No usar clave sintética local para datos del piloto.
3. Inventario y coherencia reales de DB/storage/configuración, candidato y artefactos; ensayo de aplicación restaurada con medios reproducibles, análisis/reviews, claves y controles S02–S08, no solo hashes/conteos.
4. Aprobación específica antes de respaldar/restaurar datos del producto. Medir tamaño representativo, transferencia/arranque/recuperación de claves e integridad y aceptar RTO/RPO.
5. Scheduler diario/predeploy, siete diarios y pre-release; horario/fechas, entrega real de alertas y retención revisada. No borrar los objetos de ensayo sin autorización individual.
6. Restantes gates: canales reales completos, video/costos, coaches nominales y certificación, alertas, CI con gates, artefacto/digest, paridad EasyPanel y rollback.

Recomendación: aceptar solo el ensayo sintético y revisar los pendientes; no cerrar S16, activar S11 ni declarar GO. Commit de esta entrega: consultar git log -1 -- docs/pilot-v1/S16_IMPLEMENTATION_REPORT.md.

---

## Evidencia histórica anterior — sustituida donde corresponda

# S16 — Preparación de configuración y procedimiento, sin ejecución

Fecha: 2026-10-11. Política objetivo Pilot A aprobada expresamente por el propietario: destino privado cifrado S3 compatible o Azure Blob independiente de VPS EasyPanel; AES-256/TLS; DB y archivos privados; diario/predeploy; siete diarios y pre-release durante piloto; propietario técnico como rol principal; restore aislado obligatorio; credenciales exclusivas mínimas; alertas de fallo/antigüedad.

Estado: **PREPARACIÓN DOCUMENTAL / BLOCKED para ejecución y cierre**. No hay proveedor, bucket ni responsable operativo formal confirmado. No se iniciaron operaciones persistentes ni implementación de job. Dependencias S01/S14 conservadas; S14 no certificada. S11 parcial sigue bloqueada para cuarentena/eliminación. Política/RPO/RTO aprobados no son evidencia de backup ni medición de restore.

## Archivos y contratos

- BACKUP_CONFIGURATION.example.json: plantilla JSON inerte, sin credenciales/destino real; ejecución/scheduler/limpieza deshabilitados. Null indica pendiente. No está conectada al runtime y no valida infraestructura.
- BACKUP_RESTORE_RUNBOOK.md: precondiciones, mapeo DB/storage/claves, permisos por roles, coherencia con escritores pausados, manifiesto protegido, retención, alertas, restore desechable, compatibilidad y rollback.
- DEPLOYMENT_RUNBOOK.md y documentos de seguimiento: referencias y estado vigente; información anterior conserva carácter histórico.

Código funcional, Compose, scripts de arranque, modelos y migraciones: **sin cambios**. No se instala cron ni integración S3/Azure, no se eligen servicios, no se crean recursos/cuentas/credenciales. Valores secretos excluidos.

## Validaciones de esta preparación

| Verificación | Estado |
|---|---|
| Parse JSON y comprobación de campos de seguridad/pendientes | PASS: JSON válido; ejecución/scheduler/limpieza deshabilitados; destinos y credenciales pendientes; política/retención/objetivos comprobados |
| git diff --check | PASS; enlaces locales nuevos comprobados |
| Fingerprint original | PASS: 153 paths sin cambios, estado/rama/HEAD originales conservados |
| Suites Python/JavaScript | SKIPPED: solo documentación/plantilla inerte; referencia S11 795 Python/72 JS PASS, no resultados nuevos |
| Respaldo real, upload proveedor y alertas entregadas | BLOCKED / NOT RUN |
| Restore sintético o real, RPO/RTO medidos | NOT RUN; preparación no equivale a ensayo |
| Permisos/cifrado/TLS del destino, paridad EasyPanel | BLOCKED / NOT VERIFIED |

## Riesgos y recomendación

Sin copia restaurable certificada no habilitar piloto ni limpieza efectiva. Crecimiento de fotos huérfanas sigue pendiente. La pausa coherente diaria tiene impacto de disponibilidad y exige ventana/operador; no fue ensayada. La retención no activa eliminación automática. Custodia de claves y acceso de restore deben verificarse separadamente del bucket. S11 y S16 no se declaran cerradas, otras fases no iniciadas por esta preparación.

Próximo paso: seleccionar y aprobar proveedor/destino y operador formal; revisar configuración concreta/permisos/canales, preparar ensayo aislado autorizado y registrar evidencia antes de activación. Este encargo no autoriza gasto ni acciones persistentes. Pilot **NO-GO** con cinco gates heredados conservados.

Commit documental de entrega: consultar git log -1 -- docs/pilot-v1/S16_IMPLEMENTATION_REPORT.md. Commit funcional continúa a4aefd7726a5d6f5f9b5c454bca16192ce0fe62d (S11 parcial); no commit funcional S16.
