# Consumo de IA de la bitácora

La migración 0018 agrega `training_ai_usage`. Cada llamada al proveedor registra
atleta, operación, modelo, fecha, estado y latencia, sin depender de guardar una sesión.
Se captura antes del envío; los reintentos generan llamadas independientes. Solicitudes
rechazadas localmente o sin configuración no generan consumo.

La respuesta del proveedor aporta tokens de entrada/salida y de razonamiento;
estos últimos ya pertenecen a la salida y no se suman dos veces. Una respuesta
inválida que incluye usage conserva esos tokens aunque la operación falle.
Fallos de transporte quedan con tokens desconocidos, no con un cero inventado.

Dictado conserva además la duración del audio enviado. Si la respuesta solo reporta
duración o no trae usage, los tokens siguen siendo desconocidos. Referencia:
[Audio API](https://platform.openai.com/docs/api-reference/audio/voice-consent-list?lang=curl).

`/api/internal/ai-usage` y `/internal/usage` incorporan consumo de bitácora, agrupación
por atleta y las últimas llamadas, manteniendo acceso exclusivo al rol interno.
Las sumas se realizan en SQL y el historial visible se limita a 25 operaciones.
Solo se almacenan metadatos: no hay prompts, transcripciones, fotos ni audio en esta tabla.
No se calculan precios ni se reconstruye consumo anterior a esta actualización.
