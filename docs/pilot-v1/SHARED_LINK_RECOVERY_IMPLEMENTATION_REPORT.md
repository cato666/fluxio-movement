# Recuperación de enlaces compartidos desde la web

Cambio aprobado por el usuario: conservar token cifrado para permitir al propietario recuperar, abrir y copiar enlaces activos después de cerrar sesión.

## Contrato y seguridad

El hash continúa autenticando el enlace público. Se agrega protected_link (ciphertext y versión) en el JSONB snapshot existente; no requiere migración. Fernet aporta cifrado autenticado; el payload contiene token y propietario, sin contenido del entrenamiento. Al recuperar se valida propietario, hash, formato, consentimiento, vencimiento y revocación. GET autenticado del listado devuelve path y created_at solamente a la cuenta atleta activa propietaria; mantiene no-store. El replay de creación conserva path=null y no crea ni revive publicaciones.

Web: Ver enlace (nueva pestaña con noopener/noreferrer) y Copiar enlace; fallback de campo seleccionable cuando Clipboard no está disponible. No requiere nuevo consentimiento para recuperar un enlace vigente ya consentido.

## Configuración obligatoria para crear nuevos enlaces

App y worker deben recibir la misma clave Fernet aleatoria exclusiva vía gestor de secretos: WEEKLY_SHARE_ENCRYPTION_KEY y WEEKLY_SHARE_KEY_VERSION (predeterminado 1). No usar contraseñas ni SESSION_SECRET como clave. Alternativa para rotación: WEEKLY_SHARE_ENCRYPTION_KEYS, objeto JSON de versión a clave; WEEKLY_SHARE_KEY_VERSION selecciona la actual. Conservar versiones anteriores mientras haya enlaces vigentes. Si se define clave singular, reemplaza la versión actual del mapa. Nunca imprimir estas variables. Respaldar las claves cifradas separadamente con acceso mínimo.

Sin clave válida, nuevas publicaciones fallan con 503 sin guardar un enlace. Un fallo de descifrado no devuelve URL; no filtra excepciones ni secretos. La pérdida de claves impide recuperar URLs pero no modifica validación pública por hash: revocar explícitamente si se necesita retirar acceso.

Históricos sin ciphertext no son recuperables. El atleta debe revocar y crear uno nuevo con consentimiento; no se cambian ni reautorizan automáticamente. Históricos sin consentimiento continúan bloqueados.

## Verificación

Resultados finales y commit informados en entrega. Pruebas Python dirigidas sobre bases PostgreSQL nuevas con PGDATA tmpfs y redes exclusivas internas; proveedores simulados. Pruebas de creación/cifrado, recuperación, propietario ajeno, revocación, expiración, desactivación, clave ausente/inválida, ciphertext alterado, históricos, rotación e idempotencia. JavaScript: recuperación tras remount, abrir/copia fallback, ninguna publicación adicional y regresiones.

Prueba con dominio real permanece SKIPPED (PUBLIC_BASE_URL real no suministrado). Suite Python completa no ejecutada; esta verificación es dirigida. No hay proveedores reales, datos reales, migraciones persistentes, push, merge ni deploy. Workspace original intacto.

## Riesgos y activación

Configuración cifrado de producción/EasyPanel pendiente; no se modificó infraestructura. Restauración externa, costos de video, paridad EasyPanel y validaciones reales de canales siguen bloqueando GO. La UI local debe recargarse tras la actualización del QA; los enlaces anteriores requerirán regeneración explícita.

## Resultados finales

PASS: 356 pruebas Python dirigidas de WhatsApp y seguridad S02–S08. PASS: 60 pruebas adicionales de resumen y enlaces, incluyendo rotación; 1 SKIPPED por falta de PUBLIC_BASE_URL real. Las ejecuciones se superponen y no se suman como casos únicos. PASS: 33 pruebas JavaScript aplicables; se corrigió un selector ambiguo del test antes de repetir. PASS: integración real local navegador/API/PostgreSQL: login sintético, creación consentida, recarga, recuperación y revocación individual del único enlace creado por esta verificación. Captura revisada visualmente en escritorio. No se revocó el enlace histórico existente.

Evidencias privadas fuera de Git: fluxio-s05-integrated-6uv9hyew/offline-tests.log (356); fluxio-s05-integrated-oemwyawe/offline-tests.log (60 y 1 SKIPPED), bajo TEMP del usuario. Captura fluxio-share-recovery-real.png en TEMP, con enlace sintético ya revocado.

Se actualizaron archivos en tmpfs del QA local y se reinició únicamente su API, conservando el entorno DATABASE_URL movement_e2e_s05. Clave QA aleatoria exclusiva en /tmp/s05-weekly-share.key con permisos 0600, efímera. No se habilitó worker ni se consumieron proveedores. Antes de reanudar WhatsApp, inyectar la misma clave QA al worker; no afirmar paridad app/worker real sin esa activación. No se modifican claves productivas.

Fallo inicial de actualización por selección incorrecta del proceso: guard bloqueó antes de modificar el proceso; corregido seleccionando el único uvicorn del QA y validando su base sintética. PASS posterior de integración. Históricos siguen sin URL recuperable hasta que el propietario cree uno nuevo.
