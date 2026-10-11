# Pilot A — validación WhatsApp

Validación local final del candidato `03cfd4387a75f70fae60ccd2108a83d24dc57f31`: Python **820 PASS, 1 SKIPPED, 0 FAIL** (257,41 s); JavaScript **77 PASS, 0 FAIL/SKIPPED**. La prueba omitida requiere WEEKLY_RELEASE_PUBLIC_BASE_URL real y queda **NOT RUN**, sin afirmar paridad de dominio. PostgreSQL nuevo tmpfs, red interna nueva, sin puertos Docker publicados ni credenciales de proveedores; migraciones desde cero y worker vacío PASS; contenedores propios detenidos. Evidencia: `C:/Users/desarrollo/AppData/Local/Temp/fluxio-s05-integrated-2e4m_dlq/offline-tests.log` y `environment.json`. Tres advertencias de deprecación no bloquean estas pruebas. Workspace original: 153 rutas verificadas sin cambios.

Fecha: 2026-10-11, America/Santiago. Rama: codex/pilot-v1-stabilization. Candidato auditado: `03cfd4387a75f70fae60ccd2108a83d24dc57f31`. **Pilot A NO-GO**. Alcance obligatorio: bitácora + WhatsApp + video certificado + coach titular/suplente, 3–5 atletas, 30 días. Esta entrega no autoriza proveedores, infraestructura persistente ni publicación.

Estados: PASS = evidencia ejecutada y limitada a su entorno; FAIL = defecto/evaluación fallida demostrada; BLOCKED = falta autorización, acceso, responsable o dependencia; NOT RUN = sin ejecución. Resultados históricos no certifican el candidato final ni el destino.

## Evidencia y límites

PASS parcial histórico de Sandbox: vinculación individual, dos registros de texto, corrección, Save repetido sin registro adicional, resumen, fotografía interpretada y guardada con tres bloques y storage privado. Evidencia privada: TEMP/fluxio-s05-integrated-5vgudpqr/corrected-photo-save-results.json. Operador de pruebas autorizado, sin datos de atletas. 17 intentos / 17 DELIVERED registrados, cinco reservas IA, 0 transcripciones, 0,59 USD asignados. No suma importes facturados ni certifica canal actual.

FAIL configuración histórica de compartir por WhatsApp: PUBLIC_BASE_URL no configurado en QA que exponía solo webhook. Correctamente no se publicó enlace; no ampliar exposición para evitarlo. NOT RUN real: audio, cancelación end-to-end con nueva evidencia, consentimiento/revocación por chat y conciliación de cobros. Worker running=false en metadatos leídos; flag runtime_candidate antiguo. El QA parcialmente actualizado no es paridad API/worker de release. No asumir túnel vigente porque existe una URL anterior.

## Preparación y ensayo requerido

1. Confirmar autorización específica actual para teléfono de pruebas, ventana y gasto; no reutilizar permiso anterior para otra sesión/ampliación. No registrar teléfono en documentos.
2. Nuevo entorno exclusivo DB/storage sintéticos; comprobar hashes/candidato/API/worker/config, secretos presentes sin imprimirlos, cuotas y ledger acumulado.
3. HTTPS webhook exacto /webhooks/whatsapp/kapso, firma válida/inválida, allowlist y aislamiento. Acceso público al resumen solo mediante dominio/política explícitamente aprobados; ngrok limitado al webhook no sirve para compartir resumen.
4. Texto → propuesta → Guardar; Corrección → nueva reserva IA → Guardar; Cancelar → sin persistencia. Webhook repetido → sin nueva IA ni entrega.
5. Foto → download privado → interpretación → revisión de bloques/preguntas → Guardar; fotografía accesible solo por actor autorizado/enlace consentido.
6. Audio → transcripción e interpretación separadas → Guardar; fallo parcial no retranscribe éxito previo sin necesidad.
7. Resumen semanal; compartir solicita consentimiento, aceptar crea un enlace, rechazar no crea, revocar impide HTML/foto. Cuenta inactiva sin IA/entrega pendiente.
8. 402/429/timeout/UNCERTAIN simulados, sin provocar gasto real para reproducirlos; cuotas y presupuesto rechazan sin bucles.
9. Conciliar ledger, eventos de entrega y facturación Kapso; distinguir intentos, entregas, créditos, reservas y factura. Revisar inciertos sin retry ciego.

Cada caso: ID, candidato, actor sintético, timestamp, evento dedupe redactado, estado inbox/outbox/reserva, filas antes/después, evidencia sin PII y PASS/FAIL/BLOCKED/NOT RUN.

Límites piloto existentes: interpretación 3 y transcripción 3 diarias compartidas web/chat, WhatsApp 20 entrantes/20 salientes diarios, cinco entrantes/minuto/conversación. QA previa 20 físicos y 2 USD total; no reiniciar contador para esquivar límite. No se autoriza aquí nuevo consumo.

Responsable: QA y propietario aprobador de gasto. Cierre: todos los casos reales habilitados y persistencia PASS en versión candidata, presupuesto conciliado, permisos y privacidad conservados.
