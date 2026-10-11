# Actualización de responsabilidades — 2026-10-11

Gastón administra EasyPanel; Codex no necesita acceso SSH ni sesión del panel. GitHub es origen de la versión publicada y GitHub Actions dispara deploy **solo bajo autorización expresa**. Codex prepara código/pruebas/manifiesto y sube exclusivamente refs aprobadas. Gastón aplica variables, obtiene inventario y evidencia redactada API/worker/DB/volúmenes/proxy, realiza backups/restore/rollback autorizados y confirma SHA/digests. Falta de acceso directo de Codex no es bloqueo; falta de evidencia verificable sí.

Workflow existente push main llama al webhook sin checks/gates: S15 permanece pendiente, YAML sin cambios. No push a main, merge, POST ni deploy. S16 sigue BLOCKED por pruebas operativas reales pendientes; continuar localmente con KeePassXC/Resend. Plan vigente: PILOT_A_RELEASE_PLAN.md y DEPLOYMENT_RUNBOOK.md; no solicitar nuevamente SSH para esta etapa.

---

## Historial anterior — instrucciones de acceso directo sustituidas

# S16 — custodia KeePassXC, Resend y pruebas pendientes

Fecha: 2026-10-11. Operador: Gastón. **Preparación documental, no activación.** Referencias: [inspección](S16_EASYPANEL_INSPECTION.md), [reporte](S16_IMPLEMENTATION_REPORT.md).

## KeePassXC: decisión aprobada, ejecución pendiente

Custodia primaria elegida: base KDBX de KeePassXC en computador personal Windows. Segunda copia: dispositivo externo cifrado, separado del computador y VPS. Runtime: mecanismo seguro de secretos por definir. No se generó ni reemplazó clave AES, archivo KDBX, contraseña o keyfile. No se autoriza implícitamente sincronizar a nube ni guardar claves en R2.

Gastón debe indicar ubicación de KDBX y referencia del dispositivo externo, sin contraseña ni contenido. Dentro de su bóveda, custodiar cada **clave existente** como adjunto binario exacto de 32 bytes, con ID/version/fecha y backup-set relacionado; no usar el generador de contraseñas para reemplazarla. Las dos claves de ensayo anteriores son distintas: conservar entradas y asociación por set. No asumir una clave de producción que todavía no está configurada. Una futura clave nueva requiere autorización explícita.

Proteger KDBX con contraseña maestra y conservar los factores de desbloqueo recuperables por separado; si usa keyfile, custodiar también su copia fuera del único dispositivo. Nunca registrar esos factores en Git/logs/reportes. KeePassXC almacena el contenido en KDBX cifrado; conservar la base y sus factores es necesario para recuperación ([guía oficial](https://keepassxc.org/docs/KeePassXC_UserGuide)).

Ensayo necesario, diferente del restore ya aprobado: Gastón abre la copia externa desde entorno aislado sin depender de EasyPanel, recupera por ID una clave existente y verifica descifrado de un conjunto autorizado, comparando integridad sin mostrar clave. No modificar DB ni repetir todo pg_restore si basta comprobar custodia. Registrar fecha, versión/ID, resultado y participación del operador; no registrar hash del secreto ni exportar la bóveda. Elegir luego mecanismo runtime de secret mount/gestor; KeePassXC de recuperación **no automatiza** entrega de clave al job del servidor. No subir KDBX al VPS como única recuperación.

## Resend: compatibilidad actual y configuración

Auditoría de app/scripts: no cliente Resend, SMTP o envío de email implementado. pilot_backup_ops.py admite notify_operator como callback, exige ACK explícito y registra fallo de entrega; la plantilla SMTP anterior era solo contrato. Ambos transportes Resend son posibles, requieren adaptador acotado nuevo, configuración y pruebas offline antes del envío.

Propuesta: HTTPS API POST https://api.resend.com/emails, reutilizando stdlib y sin SDK externo. Variables privadas runtime propuestas: RESEND_API_KEY, BACKUP_ALERT_FROM, BACKUP_ALERT_TO, BACKUP_ALERTS_ENABLED=false. API key con permiso de envío y alcance al dominio necesario. Dominio y remitente elegidos por Gastón, verificados en Resend antes de probar. No alterar DNS/verificación automáticamente. No persistir direcciones privadas ni credenciales en plantilla Git.

Alternativa SMTP: smtp.resend.com:465, TLS implícito, username resend, API key como password; no degradación a texto plano. Resend documenta API, SMTP y dominio verificado: [API](https://resend.com/docs/api-reference/emails/send-email), [SMTP](https://resend.com/docs/send-with-smtp), [dominios](https://resend.com/docs/dashboard/domains/introduction). SMTP/API no están activos ni se llamó al proveedor.

Idempotencia: ID durable por evento/payload, no generar uno nuevo en retry; guardar estado accepted/uncertain/delivery_failed, nunca reintento ciego tras resultado ambiguo. La idempotencia del proveedor tiene ventana limitada y no reemplaza deduplicación local; ver [documentación Resend](https://resend.com/docs/dashboard/emails/idempotency-keys). Un 2xx de Resend no garantiza recepción. Confirmación de Gastón requerida. Pauta de recordatorios/escalado sin definir; no activar alertas periódicas hasta aprobarla.

## Prueba de alerta real: concreta pero aún sin direcciones

Antes del envío: confirmar destinatario privado de Gastón, remitente del dominio verificado, ubicación de API key y presupuesto/cupo permitido para **un** correo; implementar/testear adaptador con transporte falso y timeout/dedupe/errores sin secretos. Mostrar dirección concreta y mensaje final al pedir autorización, sin escribirlos en Git.

Mensaje propuesto:

```text
Asunto: Fluxio Pilot A — prueba de alerta S16
Prueba controlada de notificación de respaldos. No corresponde a un fallo real.
Evento: BACKUP_ALERT_TEST. Fecha UTC: <fecha>. ID operativo: <id opaco>.
Gastón: confirma la recepción de este correo para validar el canal de alertas.
```

No contiene entrenamientos, teléfonos, archivos, URL de backups ni claves. Código BACKUP_ALERT_TEST es solo propuesta de mensaje: el helper actual no admite ese código; el futuro adaptador deberá diferenciar test de fallos sin ampliar el whitelist silenciosamente. Autorización: “Autorizar un correo de prueba S16 por Resend, desde <remitente> a <destinatario>, mensaje revisado, sin otros envíos ni retries automáticos”. Ejecutar una vez, guardar ID del proveedor/resultado redactado y confirmación del operador. Si falla, detenerse; no activar scheduler como alternativa ni enviar correos de prueba repetidos.

## Respaldo representativo y restauración: preparar tras inspección real

1. Completar tabla EasyPanel de lectura ya autorizada. Verificar identidad/API+worker, DB/version/head, 29 tablas del candidato y otros schemas reales, montajes y tamaño de todos los medios y versiones de claves. No copiar datos durante inventario.
2. Presentar plan individual: servicios exactos a pausar/reanudar y ventana, conjunto DB/storage coherente, prefijo R2, tamaño/costo estimado, roles lector/writer y custodia, destino aislado, acceso y retención de copia. El helper actual 128 MiB no certifica capacidad de videos reales; medir tamaño y resolver antes de probar. Adaptador operacional aún pendiente.
3. Solicitar permiso específico de coordinación/mantenimiento y pg_dump completo + copia cifrada de medios existentes hacia R2; no autorizado ahora. Incluir política de datos privados y restricciones de lectura de la copia. No migraciones, resets ni eliminación de originales.
4. Solicitar permiso separado de descargar ese set concreto y restaurar a nueva instancia aislada con nueva DB/storage, providers disabled, sin entrypoint de seed/upgrade. Nunca reutilizar base del producto ni puertos públicos/redes con usuarios.
5. Verificar cada tabla/conteo y FK, archivos/hash, PNG/video decodificables, usuarios activos/inactivos, análisis/reviews/anotaciones, API/media privada, cuotas, sharing consentimiento/revocación/expiración y recuperación WhatsApp/sharing keys. No realizar envíos o IA. Medir tiempo desde simulación de incidente incluyendo descarga, claves, DB, storage y arranque/verificación; RPO y pérdidas potenciales según snapshot real.
6. Gastón acepta evidencia y manejo posterior de la copia. No borrar R2/DB/media ni cutover sin autorización adicional. Solo después presentar instalación de diario/pre-release y vigilancia independiente, horario America/Santiago, suplente, umbrales y alertas; no activación implícita por aprobar prueba.

## Datos/decisiones que debe entregar Gastón ahora

- URL administrativa y proyecto de EasyPanel; sesión autenticada o ubicación privada de acceso existente. Lectura ya autorizada.
- Referencias de KDBX y dispositivo externo cifrado; confirmar qué claves existentes se custodiarán, sin contenido. Elegir luego mecanismo de secretos runtime.
- Dirección destinataria y remitente privados, dominio Resend verificado o aún por verificar, ubicación de RESEND_API_KEY. No enviar credenciales por chat.

Estas referencias permiten preparar acciones concretas. No solicitar ni ejecutar respaldo real o correo hasta que el usuario pueda revisar destinatarios/servicios/conjunto/costos definidos. S16 permanece BLOCKED y Pilot NO-GO.
