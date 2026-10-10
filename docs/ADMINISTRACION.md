# Administración y planes

Acceso: `/admin`, exclusivamente para `SYSTEM_ADMIN`. Incluye usuarios, planes,
organización, permisos por rol y los últimos 100 cambios administrativos.

## Usuarios

Crear cuentas de atleta, coach o administrador con usuario de acceso, nombre,
correo opcional, contraseña inicial, estado y plan Free/Pago. Editar datos,
restablecer contraseña y desactivar cuentas sin borrar su historial. Filtros por
nombre, usuario, correo, rol, estado y plan. Se muestra último acceso y consumo.
El correo es único y se normaliza; se conserva el acceso existente por usuario.
No se envían invitaciones ni correos: la entrega de credenciales es manual.

Desactivar una cuenta invalida sus siguientes solicitudes incluso con sesión
abierta. No se permite desactivar al último administrador activo. El rol de una
cuenta existente se conserva debido a las relaciones de atletas, coaches y
revisiones. Los permisos son los roles actuales del producto, no roles dinámicos:

- Atleta: bitácora, análisis propios, solicitudes de revisión y resúmenes.
- Coach: revisiones asignadas, creación de atletas y análisis para atletas.
- Administrador: cuentas, políticas, organización, auditoría y consumo interno.

## Planes e interacciones

Valores iniciales provisionales: Free 10 y Pago 200 interacciones mensuales.
Ambos habilitan inicialmente análisis de video, interpretación de WOD y dictado.
Administración puede modificar límites y deshabilitar cualquiera de esas funciones
por plan. Un límite cero impide todas las interacciones. Pago es una clasificación
administrativa; no implica cobro ni integración con un proveedor de pagos.

Cada solicitud admitida consume una interacción **antes** del procesamiento,
incluidos errores posteriores de validación o proveedor. El reanálisis consume
otra interacción. Los análisis iniciados por un coach descuentan del atleta.
Solicitudes rechazadas por plan o cuota no consumen. Lectura de historial,
registro manual de entrenamientos e imágenes no consumen esta cuota.
Los procesos internos de WhatsApp no se incluyen todavía en estas cuotas HTTP.

Periodo: mes calendario UTC. El consumo se conserva en `plan_interactions`; no
se borra al cambiar plan ni al modificar el límite. Una reserva con bloqueo de
fila evita que solicitudes simultáneas superen la cuota del usuario. Una reducción
del límite puede dejar sin saldo una cuenta hasta el mes siguiente o una ampliación.
Las operaciones deshabilitadas devuelven 403 y el agotamiento devuelve 429 con
mensaje legible. `GET /api/account/plan` informa plan, usados, restantes y funciones.

## Configuración, auditoría y persistencia

`GET /api/admin/users`, `POST /api/admin/users`, `PUT /api/admin/users/{id}`.
`GET /api/admin/settings`, `PUT /api/admin/plans`, `PUT /api/admin/organization`.
`GET /api/admin/audit`. Todos exigen administrador en el servidor.

`admin_settings` guarda organización y políticas; `admin_audit` registra actor,
fecha, acción, objetivo y cambios. Contraseñas nunca se incluyen en auditoría;
solo se registra que se restablecieron. Organización es configuración informativa
de esta instalación, sin multiempresa. Catálogos conservan la biblioteca de
ejercicios existente; no se añade un editor de perfiles biomecánicos.

Despliegue: ejecutar `alembic upgrade head` (migración `0022_administration`)
antes de iniciar la nueva versión. Las cuentas existentes quedan activas y Free.
El seed existente conserva cuentas y planes, pero sigue actualizando contraseñas
demo como antes; usarlo únicamente con la configuración de demo correspondiente.

Validación: `pytest -q tests/test_administration.py tests/test_basic_auth.py`;
suite completa al cerrar la fase en PostgreSQL `movement_test` aislado.

### Evidencia de implementación

La ejecución completa inicial pasó 374 casos antes de encontrar una prueba que
dejaba el esquema en `0021`. Esa prueba ahora restaura `head`; se verificaron los
grupos afectados y Administración: 102 aprobados y 1 omitido.
La última ejecución específica de Administración pasó 8 casos, incluida la
reserva simultánea de una cuota de una interacción sin exceder el límite.
La interfaz se
probó con respuestas simuladas en Chromium a 1440px y 390px: edición de usuario,
guardado de planes, ausencia de errores JavaScript y desbordamiento horizontal.
La revisión visual confirmó la distinción de la sección seleccionada. No se
modificó la base operativa ni se desplegó la aplicación.
