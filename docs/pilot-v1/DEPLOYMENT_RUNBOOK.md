# Actualización Pilot A — política de respaldo aprobada, ejecución deshabilitada

El propietario aprueba objetivo privado S3 compatible/Azure Blob independiente del VPS, AES-256/TLS, PostgreSQL+archivos privados, frecuencia diaria/predeploy, siete copias diarias y copia pre-release durante piloto, rol propietario técnico, restore aislado y credenciales mínimas/alertas. **Proveedor, bucket/contenedor y responsable operativo formal no confirmados.** Preparados [configuración inerte](BACKUP_CONFIGURATION.example.json), [procedimiento](BACKUP_RESTORE_RUNBOOK.md) y [reporte S16](S16_IMPLEMENTATION_REPORT.md). Sin job instalado, respaldo, restore, migración, deploy ni infraestructura persistente.

S16 preparación documental, cierre BLOCKED; S11 parcial, limpieza efectiva BLOCKED. El inventario/guard S11 sigue siendo código vigente. S12–S15/S17–S18 no iniciadas; S14/digest pendiente. Retención y objetivos están aprobados, no medidos. Pilot **NO-GO**: E2E S05, costos extra video, paridad EasyPanel, proveedores reales y backup/restore destino permanecen pendientes. La evidencia histórica siguiente no sustituye este estado vigente.

---

# Runbook de despliegue Pilot v1.0

**Procedimiento propuesto, no ejecutado ni autorizado.** No desplegar, migrar bases persistentes, crear cuentas ni enviar mensajes por aprobar solamente este plan. Release owner solicita aprobación sobre commit/digest, backup, cambios SQL, destino, ventana y gasto concretos cuando estén listos.

## Rama, versión y artefactos

Preparar rama `codex/pilot-v1-stabilization` desde baseline acordada, transfiriendo selectivamente cambios locales con conocimiento del propietario. No reset/stash/clean masivo ni publicar todos los untracked. Candidato `v1.0.0-pilot.1-rc.1`; tag aprobado `v1.0.0-pilot.1`; corrección posterior `v1.0.0-pilot.2` con manifiesto independiente. Son nombres propuestos, no ramas/tags creados.

Manifiesto: commit limpio, PR/diff, tag, digest inmutable, app y worker iguales, head Alembic esperado, migraciones incluidas, versiones/modelo/checksum, lista ejercicio/vista, assets, configuración redactada, tests/scans, backup ID/hash/fecha, rollback digest y responsables. No incluir .env, claves, dumps, medios privados, debug.log, .impeccable o herramientas de agentes en imagen por accidente; revisar contexto COPY . . y .dockerignore.

Atención: workflow actual dispara POST EasyPanel en push main sin tests. No merge/push main hasta aprobar e implementar S15; no llamar webhook de deploy para comprobarlo.

## Predeploy

1. Resolver todos los gates de GO_NO_GO; comparar destino read-only: SHA/digest de API/worker, tabla alembic_version, mounts, rutas OpenAPI, proxy/TLS y DB conectada. Operador registra nombres de servicios/volúmenes reales; Compose es referencia, no prueba de configuración EasyPanel.
2. Revisar diferencias y SQL incremental desde revisión real a candidato. Local propone 0022; no asumir remoto 0021 por ausencia de rutas. Evaluar locks, unicidad email y compatibilidad viejo/nuevo; ensayo sobre copia aislada y contrato legacy. No ejecutar downgrade en producción.
3. Build/scan y test de imagen exacta con esquema nuevo y rollback. Comprobar dependencias FFmpeg/modelo, recursos CPU/memoria/disco, health API/DB y heartbeat worker.
4. Verificar APP_ENV production, SESSION_SECRET fuerte, HTTPS, claves de cifrado/hash/versiones, webhook secret y proxy allowlist sin revelar valores. APP/worker comparten storage y mismas claves/versiones. Evitar seed demo productivo y migración concurrente entre réplicas.
5. Configurar límites acordados de IA/video/chat, PUBLIC_BASE_URL HTTPS, TTL y canales; registrar presupuesto y responsables. Mantener WhatsApp/IA deshabilitados durante preparación/smoke sin gasto. No confundir worker sleep infinity con operativo.
6. Ventana sin uploads nuevos y sin trabajos activos; drenar o pausar ingress/worker con procedimiento ensayado. Avisar usuarios por canal autorizado; este runbook no autoriza enviar comunicaciones externas.

## Respaldo y migración

Propuesta RPO <=24 h durante piloto y cero escrituras perdidas en ventana de deploy; RTO <=4 h. Deben aprobarse y medirse; no SLA existente. Backup diario y antes de release; para ventana coordinar pausa de escrituras y worker, pg_dump consistente formato custom de DB más copia/snapshot storage y export seguro de claves/config necesarias para descifrar. Retención propuesta: 7 diarios y snapshot pre-release durante los 30 días, con acceso restringido/cifrado y política de eliminación aprobada.

Verificar checksum, tamaño, fecha, revisión Alembic y conteos; restaurar en instancia nueva aislada, probar sesión/fotos/reviews/identidades cifradas y medir tiempo. Un dump exitoso sin restore no habilita deploy. No listar claves ni contenido personal en reportes.

Con autorización explícita de migración persistente: ejecutar una vez upgrade al head aprobado en servicio de mantenimiento controlado; app actual ejecuta upgrade head + seed al arrancar, así que debe quedar controlado por S04/S16 antes. Esperar resultado SQL y verificar alembic_version. En fallo detener publicación; no iniciar otra migración ni downgrade automático. No copiar aquí comandos con destinos productivos sin conocer nombres y revisión real.

## Deploy EasyPanel

1. Confirmar autorización final, backup restaurable y rollback compatible; guardar manifiesto anterior.
2. Seleccionar proyecto/servicios verificados; fijar misma imagen por digest para API y worker, entorno redactado y volúmenes existentes. Nunca recrear DB ni seleccionar volumen vacío.
3. Aplicar migración aprobada en ventana, desplegar API y verificar /api/health/schema; luego worker con release/claves compatibles. Mantener ingress chat pausado hasta smoke y comprobación de cola.
4. Validar TLS/proxy, health/contrato/assets y montajes. Habilitar servicios reales solo con autorización de gasto y límites aprobados. Reactivar ingress de forma controlada; vigilar backlog y expiraciones.
5. Registrar hora Santiago, digest, revisión, checks y operador. No automatizar reinicios repetidos ante fallo ni retries de envío incierto.

## Smoke posterior

En destino autorizado: health y OpenAPI; login cuenta QA individual; manual guardar/leer/editar; semana; imagen propia denegada a segundo usuario; share opt-in/lector/revoke; rol coach sin acceso ajeno; cuenta QA desactivada en web/chat; media y DB sobreviven a reinicio autorizado. Borrado solo QA autorizado. Pequeño video perfil certificado con recursos medidos. Foto/audio/OpenAI y mensaje Kapso únicamente con permiso específico; si faltan pruebas reales obligatorias, release sigue pendiente, no PASS por fixture.

Comparar SHA/digest API-worker, revisión Alembic y assets; cola avanza sin duplicados y alertas funcionan. Tiempos/cuentas/links de smoke se redactan; revocar links QA creados y limpiar solo datos autorizados según política. Ver TEST_PLAN T01–T16.

## Rollback y recuperación

Triggers: exposición/permisos fallidos, pérdida/corrupción, schema incompatible, login general roto, cola sin recuperación o costo fuera de límite. Pausar canales/altas, conservar evidencias/volúmenes y decidir con release owner; no replay UNCERTAIN ni cobros adicionales automáticos.

Si esquema nuevo acepta binario anterior ensayado: volver API/worker al digest anterior y configuración compatible; conservar DB/storage y claves, smoke y observar. No asumir compatibilidad: 0022 agrega columnas/tablas pero el seed/ORM/guards también cambian. Si incompatibilidad o migración fallida: mantener mantenimiento, preferir hotfix acotado o restaurar respaldo a instancia nueva; reconciliar escrituras posteriores antes de cutover autorizado. Restaurar backup anterior puede perder registros nuevos, por eso requiere decisión explícita y recuperación/export previo.

Nunca `down -v`, borrar volúmenes, Alembic downgrade destructivo ni restore sobre DB activa como atajo. Job de video interrumpido queda FAILED; reanálisis existente solo tras revisar cuota/artefactos y aprobación de gasto si aplica. 402: verificar saldo/configuración con operador, luego recuperación individual ensayada; envío ambiguo exige reconciliar evidencia del proveedor antes de cualquier reenvío autorizado. Cerrar incidente con conteos/hashes, smoke, impacto y decisión de reanudar.
