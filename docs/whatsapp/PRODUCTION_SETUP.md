# Activar WhatsApp en Easypanel

La versión f1c04cf está publicada, pero la configuración del entorno es independiente del Sandbox. Compose pasa variables de WhatsApp a app y whatsapp-worker; ambos usan la misma DB, claves y storage. El worker espera app saludable (migraciones terminadas) y no expone puertos. Con WHATSAPP_ENABLED=false queda inactivo.

En Environment del Compose Service configurar:

```dotenv
WHATSAPP_ENABLED=true
WHATSAPP_PROVIDER=kapso
WHATSAPP_PUBLIC_NUMBER=+56920403095
KAPSO_PHONE_NUMBER_ID=<ID del número configurado en Kapso>
KAPSO_API_KEY=<credencial del entorno destino>
KAPSO_WEBHOOK_SECRET=<secreto del webhook destino>
WHATSAPP_ENCRYPTION_KEY=<clave Fernet persistente del entorno destino>
PHONE_HASH_KEY=<clave base64url persistente de al menos 32 bytes>
WHATSAPP_KEY_VERSION=1
WHATSAPP_ENCRYPTION_KEYS={}
```

No copiar secretos del Sandbox ni enviarlos por chat. PHONE_ENCRYPTION_KEY no es el nombre consumido: usar WHATSAPP_ENCRYPTION_KEY. No regenerar claves si el entorno ya tiene identidades. No cambiar DATABASE_URL ni volúmenes existentes.

Webhook Kapso POST:
https://proyectos-fluxio-movement.sgnetm.easypanel.host/webhooks/whatsapp/kapso

Configurar eventos received, sent, delivered, read y failed. Usar la firma X-Webhook-Signature. Si la validación HTTPS falla detrás de Easypanel, configurar FORWARDED_ALLOW_IPS con las IP/redes del proxy confiable; no adivinar IP ni confiar en cualquier origen por defecto.

Redeploy tras cambiar variables. Revisar app saludable, worker activo sin errores de configuración, UI de vinculación y un primer mensaje real. Si el número sigue siendo Sandbox Kapso, su activación sigue siendo necesaria. Vinculación local no existe automáticamente en la base productiva.

La confirmación de GitHub Actions solo acredita el disparo de deploy. Habilitación y recepción WhatsApp requieren comprobación posterior en el entorno destino.
