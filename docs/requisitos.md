# Requisitos del sistema de administracion de laboratorio

## Alcance acordado

Aplicacion de escritorio en Python para un laboratorio universitario. Administrara reactivos y materiales identificados por codigo de barras, sus existencias y fechas de caducidad, y el historial de entradas y salidas con su responsable. No incluye ventas, cobros ni funciones de punto de venta.

## Requisitos funcionales

| ID | Requisito |
|---|---|
| RF-01 | Iniciar sesion con nombre de usuario y contrasena verificada contra un hash; bloquear el acceso de cuentas inactivas. |
| RF-02 | Aplicar permisos por rol: administrador, operador y consulta. |
| RF-03 | Registrar reactivos y materiales con codigo de barras unico, nombre, tipo, existencias y caducidad opcional. |
| RF-04 | Buscar un producto leyendo su codigo con un lector fisico. La lectura debe iniciar una busqueda real y permitir seguir con una operacion del sistema. |
| RF-05 | Registrar entradas y salidas con cantidad, fecha y usuario responsable; actualizar existencias dentro de la misma transaccion. |
| RF-06 | Rechazar codigos vacios o duplicados, cantidades no positivas y salidas mayores que las existencias. |
| RF-07 | Consultar inventario, caducidades e historial de movimientos. |
| RF-08 | Presentar en la interfaz uno o dos reportes SQL utiles para el laboratorio. Cada reporte usara al menos tres caracteristicas de consulta avanzada indicadas en la practica. |
| RF-09 | Registrar automaticamente en auditoria las modificaciones de datos importantes, con operacion, fecha, usuario y datos anterior/nuevo cuando correspondan. |
| RF-10 | Usar desde la aplicacion al menos tres procedimientos almacenados, dos funciones almacenadas y los triggers definidos para el sistema. |
| RF-11 | Mostrar confirmaciones y errores comprensibles sin ocultar el resultado real de la operacion. |

## Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF-01 | La interfaz debe ser sencilla, clara y adecuada para un mini proyecto universitario. |
| RNF-02 | La aplicacion debe conectarse a MySQL y ejecutar operaciones reales; no se aceptan datos simulados como sustituto de la base de datos. |
| RNF-03 | Las contrasenas no se guardan en texto plano; la aplicacion almacena y verifica hashes con sal. |
| RNF-04 | Las reglas que protegen la integridad deben aplicarse en la base de datos, aun cuando la interfaz valide los datos antes de enviarlos. |
| RNF-05 | Las operaciones relacionadas deben ser atomicas: confirmar todo o revertirlo todo ante un error. |
| RNF-06 | El proyecto debe incluir instrucciones para instalar, configurar y ejecutar la aplicacion en el equipo de evaluacion. |
| RNF-07 | El codigo, los scripts y la documentacion deben ser comprensibles y explicables por el equipo. |

## Decisiones de alcance de la etapa 1

- Un registro de producto representa un reactivo o material con una fecha de caducidad opcional. El control por lotes se deja fuera porque no aparece como requisito obligatorio de la propuesta seleccionada.
- Toda variacion de existencias se registra como movimiento. El trigger posterior al alta de un movimiento actualiza el stock; el procedimiento almacenado envuelve la operacion en una transaccion.
- Los movimientos son historial operativo. El perfil operador no recibe permisos de modificacion directa de tablas; usa procedimientos almacenados.
- Los roles de la aplicacion viven en `usuarios`. El script de seguridad define ademas roles MySQL para limitar permisos de las cuentas de conexion.
- El lector fisico se tratara como entrada de codigo en la interfaz. La demostracion debe usar un dispositivo real, no una lectura digitada como sustituto.

## Criterios verificables al terminar el proyecto

1. El equipo puede crear la base desde cero con sus scripts y explicar el modelo y sus objetos.
2. La aplicacion inicia sesion y limita acciones segun los tres roles.
3. Un lector fisico encuentra un registro y permite completar una busqueda u operacion real.
4. Una entrada y una salida guardan su movimiento y actualizan el stock; una salida sin existencias falla sin dejar cambios parciales.
5. Los procedimientos, funciones, triggers de validacion y triggers de auditoria se ejecutan en el flujo real de la aplicacion.
6. La aplicacion muestra uno o dos reportes SQL que usan tres o mas caracteristicas avanzadas cada uno.
7. La entrega incluye documentacion, scripts SQL, codigo fuente en GitHub e imagenes o video como evidencia del lector.
