# Etapa 1: base de datos lista para la aplicacion

## Archivos y orden de ejecucion

1. `sqlnofinal.sql`: crea el esquema, tablas, restricciones e informacion inicial de demostracion.
2. `sql/02_objetos.sql`: crea funciones, procedimientos, vista y triggers.
3. `sql/03_seguridad.sql`: crea roles MySQL y concede permisos.

Ejecutar los tres archivos en ese orden con MySQL 8.0.16 o posterior desde una cuenta administradora. `sqlnofinal.sql` debe ejecutarse primero. Los otros dos reemplazan sus rutinas/triggers y son adecuados para volver a aplicar durante desarrollo. Los scripts no borran la base de datos.

## Datos de demostracion

Se incluyen tres usuarios (uno por rol) y cuatro productos. Las cuentas locales de demostracion comparten temporalmente la contrasena `LabDemo-2026!`; cambiarla antes de cualquier uso fuera de una demostracion local. El hash guardado usa scrypt con sal y parametros incluidos en el valor. La aplicacion de la etapa 2 debera verificar ese formato y nunca comparar contrasenas en texto plano almacenado.

El stock de los productos es una existencia inicial. A partir de ahi, las entradas y salidas se registran en `movimientos`. `ai_movimientos_actualizar_stock` ajusta el inventario dentro de la misma transaccion y los triggers de producto guardan la auditoria del cambio.

## Transaccion principal

`sp_registrar_movimiento` recibe producto, usuario responsable, tipo y cantidad. Inicia transaccion, bloquea el producto, comprueba existencia suficiente cuando es salida, inserta el movimiento y confirma. El trigger de movimiento ajusta stock; los triggers de auditoria registran ese cambio. Si alguna validacion o escritura falla, el procedimiento revierte la transaccion y propaga el error.

## Auditoria desde la aplicacion

`sp_registrar_producto` y `sp_registrar_movimiento` establecen temporalmente las variables de sesion `@app_usuario_id` y `@app_nombre_usuario` para que los triggers de producto guarden al usuario de la aplicacion. Si se ejecuta una modificacion manual sin ese contexto, auditoria conserva la cuenta MySQL que realizo el cambio en `usuario_responsable`.

## Seguridad

`usuarios.rol` controla el rol funcional de la aplicacion. `sql/03_seguridad.sql` crea roles MySQL separados: administrador, operador, consulta y aplicacion. Operadores no reciben permisos directos para insertar o actualizar productos/movimientos; usan procedimientos almacenados. El administrador local crea la cuenta MySQL de conexion y le asigna el rol tecnico de aplicacion.

El usuario `consulta` de la aplicacion es de solo lectura funcionalmente. La aplicacion de la etapa 2 tambien debe impedir operaciones no permitidas por rol, aunque el menu o boton no se muestre.

## Limites conocidos al cierre de etapa 1

- El lector fisico, la interfaz Python y los reportes visibles se implementaran en la etapa 2.
- Los reportes requeridos deberan usar al menos tres caracteristicas avanzadas de SQL; se definiran al implementar las pantallas.
- No hay configuracion de conexion ni contrasenas MySQL incluidas en el repositorio; se agregaran como configuracion local de la aplicacion y no se subiran credenciales al control de versiones.
