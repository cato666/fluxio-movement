# Actualización de responsabilidades — 2026-10-11

Gastón administra EasyPanel; Codex no necesita acceso SSH ni sesión del panel. GitHub es origen de la versión publicada y GitHub Actions dispara deploy **solo bajo autorización expresa**. Codex prepara código/pruebas/manifiesto y sube exclusivamente refs aprobadas. Gastón aplica variables, obtiene inventario y evidencia redactada API/worker/DB/volúmenes/proxy, realiza backups/restore/rollback autorizados y confirma SHA/digests. Falta de acceso directo de Codex no es bloqueo; falta de evidencia verificable sí.

Workflow existente push main llama al webhook sin checks/gates: S15 permanece pendiente, YAML sin cambios. No push a main, merge, POST ni deploy. S16 sigue BLOCKED por pruebas operativas reales pendientes; continuar localmente con KeePassXC/Resend. Plan vigente: PILOT_A_RELEASE_PLAN.md y DEPLOYMENT_RUNBOOK.md; no solicitar nuevamente SSH para esta etapa.

---

## Historial anterior — instrucciones de acceso directo sustituidas

# S16 — inspección EasyPanel de lectura / alcance verificable

Fecha: 2026-10-11, America/Santiago. Base `7598e38a7a7a6137dd0217bb4efc6bfbb9b0f2d2`. Usuario autorizó exclusivamente lectura, no modificaciones, reinicios, migraciones, copias persistentes ni deploy. **Inspección administrativa BLOCKED por acceso no disponible; S16 BLOCKED.**

## Evidencia observada

- Git candidato en codex/pilot-v1-stabilization, base confirmada, cambios locales ajenos conservados.
- Documentación señala `proyectos-fluxio-movement.sgnetm.easypanel.host`. GET público `/health`: HTTP 200, certificado TLS validado por cliente; JSON expone campo `ok`, sin versión. HEAD `/`: 405 (método no admitido, no prueba de fallo del servicio). No redirects seguidos ni datos de atletas consultados.
- Navegador disponible: solo login local 127.0.0.1:65062; no sesión EasyPanel. No archivo ~/.ssh/config ni conector EasyPanel/SSH disponible. No se enumeraron claves privadas ni se probó SSH contra hosts desconocidos.
- Solo se revisaron nombres/presencia de variables relevantes en .env.example autorizado; no hay variables Resend/SMTP/EasyPanel/SSH. Es configuración local, no evidencia del entorno desplegado.

| Elemento requerido | Estado | Evidencia que debe obtenerse con acceso administrativo de lectura |
|---|---|---|
| API | Host público alcanzable; servicio/nombre/contenedor NOT VERIFIED | Proyecto, servicio, imagen/digest, runtime/version/commit, salud sin datos privados. |
| Worker WhatsApp | BLOCKED | Nombre, comando, imagen/digest, versión, heartbeat/cola/outbox agregados; no reenviar mensajes. |
| PostgreSQL | BLOCKED | Servicio, versión, DB/schema/roles y revisión; consultas de catálogo/count autorizadas, nunca contenido de filas. |
| Volúmenes persistentes | BLOCKED | Montajes API/worker/DB, driver/destino, alcance y disponibilidad; no crear/eliminar volúmenes. |
| Fotografías/videos | BLOCKED | STORAGE_PATH y original/whatsapp, annotated, analysis, training-images; inventario agregado/tamaño, referencias externas y symlinks. |
| Proxy/HTTPS | TLS público PASS limitado; proxy BLOCKED | Dominios/rutas, terminación HTTPS y política de forwarded headers/trusted proxy. No cambiar certificados/configuración. |
| Migraciones | BLOCKED | SELECT de alembic_version sin upgrade; comparar con 0024_training_save_requests del candidato, no asumir paridad. |
| API y worker | BLOCKED paridad | Commit/digest de ambos y configuración compatible; app pública no informa identidad verificable. |
| Variables de seguridad | BLOCKED | Solo presencia/ausencia y validación redactada de APP_ENV, SESSION_SECRET, WEB_ALLOWED_ORIGINS/proxies, WhatsApp encryption/signature/hash keys, weekly share keys, cuotas/reservas video, storage/DB, R2 y respaldo. Nombres exactos contra código del candidato; no exportar dotenv ni inspect Config.Env crudo. |

La inspección de lectura está autorizada; falta **URL administrativa/proyecto y sesión autenticada o referencia de acceso existente**. No pedir otra autorización genérica de lectura. No presentar host público como administración EasyPanel ni Docker local como producción. Una vez disponible acceso, completar tabla antes de pedir backup real.

No se enviaron correos, se generaron/copiaron claves, se instalaron jobs o se realizaron nuevas operaciones R2. Archivo local de evidencia HTTP: C:/Users/desarrollo/AppData/Local/Temp/s16-easypanel-public-read.json. Las pruebas sintéticas previas conservan PASS y no se repiten.
