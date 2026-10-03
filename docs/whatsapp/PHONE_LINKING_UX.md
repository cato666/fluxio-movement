# Vinculación de WhatsApp: propuesta UX

Estado: primera implementación de interfaz local, autorizada por el usuario. Separada de Kapso Sandbox Validation; no habilita Fase 4, merge ni deploy.

## Objetivo

Vincular la cuenta autenticada del atleta con su WhatsApp una sola vez, sin DevTools. Registrar por WhatsApp debe comenzar con tocar, enviar y recibir confirmación.

## Entrada y recorrido

En Bitácora, acción secundaria «Registrar por WhatsApp», respetando DESIGN.md y los componentes existentes. No competir con registrar un entrenamiento desde la web.

1. Consultar el estado de vinculación al abrir la opción.
2. Si no está vinculado, mostrar: «Vincula tu WhatsApp para registrar entrenamientos con fotos, audio o texto. Solo necesitas hacerlo una vez.» Acción principal: «Vincular mi WhatsApp».
3. Generar el challenge solo al pulsar la acción. Preparar el mensaje exacto devuelto por el servidor; no construir ni modificar el código.
4. En móvil: «Abrir WhatsApp» con destinatario configurado y mensaje preparado. El atleta debe pulsar Enviar dentro de WhatsApp; abrir la aplicación no acredita vinculación.
5. Desktop: QR del mismo enlace y alternativa «Abrir WhatsApp». Alternativa accesible «Copiar código» y destinatario visible para envío manual. QR opcional, sin servicio externo que reciba el código.
6. Al volver a Fluxio, consultar el estado. Solo linked=true permite mostrar «WhatsApp vinculado». Siguiente acción: «Envía una foto de tu WOD y cuéntanos tu resultado».

## Estados y acciones

| Estado | Mensaje y acción |
|---|---|
| Consultando | «Comprobando vinculación…», sin generar códigos automáticamente. |
| No vinculado | Explicación breve y «Vincular mi WhatsApp». |
| Generando | Feedback inmediato, evitar solicitudes simultáneas. |
| Pendiente | «Envía el mensaje para completar la vinculación», «Abrir WhatsApp» y «Ya lo envié». |
| Vencido | «El código venció. Genera otro para continuar», respetando expires_at del servidor. |
| Vinculado | Confirmación y guía para primer entrenamiento. |
| Sin conexión/error | Conservar el paso actual y ofrecer Reintentar; no mostrar éxito supuesto. |
| Canal no disponible | «WhatsApp no está disponible en este momento», mantener registro web disponible. |
| Límite de solicitudes | Mensaje de espera ante 429, sin bucle de generación. |
| Desvincular | Acción secundaria con confirmación: los nuevos mensajes dejarán de asociarse a la cuenta; conservar entrenamientos. |

Verificar estado al recuperar visibilidad y mediante «Ya lo envié». Si se incorpora polling, debe ser acotado, detenerse al cerrar/vencer/vincular y suspenderse en segundo plano. Un código vencido no invalida una identidad ya vinculada: consultar estado antes de ofrecer regeneración.

## Contratos existentes verificados

- POST /api/whatsapp/link-challenges: sesión autenticada de atleta; devuelve code y expires_at.
- GET /api/whatsapp/identity: devuelve linked y verified_at; no devuelve teléfono.
- DELETE /api/whatsapp/identity: revoca vinculación.

No cambiar APIs, permisos ni cifrado. No mostrar un teléfono supuestamente vinculado: el contrato no lo devuelve. No generar un challenge por cada visita ni reemplazar una vinculación activa automáticamente.

## Dependencia por resolver antes de implementar

El frontend necesita el número público de WhatsApp destinatario para el enlace. KAPSO_PHONE_NUMBER_ID es un ID del proveedor, no un número marcable. Los contratos actuales de vinculación no entregan destinatario. Definir cómo publicar ese dato no secreto mediante configuración existente; si no hay mecanismo, acordar una solución explícita sin inventar un número ni ampliar APIs silenciosamente.

Sandbox requiere activación y autorización del teléfono en Kapso; es preparación de pruebas, distinta de vincular la identidad de Fluxio. Confirmar que el enlace prellenado funciona con el número real del Sandbox y probarlo en Android/iOS.

## Privacidad y accesibilidad

No enviar códigos a analytics, logs, documentación o generadores QR externos. Evitar persistirlos en localStorage. El código viaja únicamente por el enlace de WhatsApp necesario y la copia voluntaria del usuario. No incluir credenciales Kapso en el cliente.

Botones táctiles de al menos 44 px, estados anunciados de forma accesible, navegación por teclado y foco coherente. QR siempre acompañado de alternativa textual; no depender de hover. Reutilizar modales/sheets y feedback del producto, sin un segundo sistema visual.

## Validación futura

Verificar cuenta atleta autenticada, emisión única por clic, apertura móvil y desktop, retorno de WhatsApp, vencimiento, error/429, canal deshabilitado, vínculo existente y desvinculación. Comprobar que abrir el enlace o copiar el código no muestra éxito antes de linked=true. No alterar datos de entrenamientos.

Esta entrega solo añade documentación. No se ejecutan tests por ausencia de cambios de código.


## Implementación inicial — 2026-10-03

Disponible como disclosure Registrar por WhatsApp en Bitácora, con generación explícita, enlace prellenado, copia alternativa, expiración, consulta al volver/Ya lo envié, errores y desvinculación confirmada. APIs existentes intactas. Código temporal solo en memoria; cleanup al cambiar vista. Sin polling ni animaciones nuevas. QR queda opcional para una iteración posterior, no se integra generador externo.

WHATSAPP_PUBLIC_NUMBER es configuración no secreta: número internacional marcable (por ejemplo + prefijo país y número), distinto de KAPSO_PHONE_NUMBER_ID. El HTML servido expone únicamente dígitos validados en metadata, con no-store; no expone credenciales ni modifica contratos API. Si está vacío, sigue disponible copiar código y enviarlo manualmente; pendiente confirmar destinatario real para activar Abrir WhatsApp. Configurar en el env del Sandbox y recrear API para incorporar cambios de env; reiniciar no recarga el env de un contenedor existente.

Validación dirigida: 29 tests Python foundation/contracts y 19 JavaScript vinculación/training UX aprobados. Inspección de capturas desktop/móvil y overflow en 320/390/430/1280 px aprobados bajo fixtures. Aún falta hardware real y apertura de WhatsApp con destinatario confirmado. Baseline completa 259/60/6 anterior a esta interfaz; no se afirma nueva suite completa. Sin merge ni deploy.


### Destinatario configurado en Sandbox

El usuario proporcionó el número público. Se configuró WHATSAPP_PUBLIC_NUMBER en .env.kapso-local (ignorado por Git) y se recreó únicamente la API para cargarlo. GET /training local devolvió 200, metadata con destinatario esperado y Cache-Control no-store. Apertura real en WhatsApp desde teléfono sigue pendiente; no se generó ningún código ni se revocó la identidad para esta comprobación. Para otros entornos hay que configurar su propio WHATSAPP_PUBLIC_NUMBER; .env.example conserva placeholder vacío.


### QR desktop y apertura por clic

Implementado por solicitud del usuario: a partir de 768 px se muestra QR junto a instrucciones; Abrir WhatsApp permanece como acción por clic. QR y botón codifican exactamente el mismo enlace wa.me con destinatario y mensaje temporal. WhatsApp decide la apertura web/aplicación según el equipo; falta validación real con WhatsApp Web activo y cámara del teléfono. No se fuerza una plataforma.

QR generado en navegador mediante copia local de Project Nayuki, MIT, en app/static/vendor/qrcodegen.js; licencia preservada en cabecera. Fuente: https://www.nayuki.io/res/qr-code-generator-library/qrcodegen.js. Sin requests a generadores externos ni nuevas APIs. Quiet zone de cuatro módulos, blanco/negro y canvas nítido. Eliminado al confirmar vinculación, vencer código, error o cleanup. Móvil mantiene enlace y copia sin QR. Sin motion agregado.

Tests de interfaz de vinculación: 2/2; breakpoint/overflow y eliminación tras vincular verificados. OpenCV decodificó captura de QR fixture y confirmó igualdad exacta con enlace por clic. Inspección visual desktop/móvil bajo fixture aprobada. No se probaron todavía QR/clic con código real ni se revocó identidad existente. Sin merge ni deploy.


## Confirmación manual de vinculación UI — 2026-10-03

El usuario indicó que probó la nueva interfaz de vinculación y funciona. Se registra aprobación manual del recorrido probado. No especificó si utilizó QR o enlace por clic: no se acredita cada alternativa por separado con esta confirmación. Generación/consulta/desvinculación y QR permanecen cubiertos por las pruebas dirigidas previas; regresión completa posterior a interfaz y QR sigue pendiente. Sin merge ni deploy.
