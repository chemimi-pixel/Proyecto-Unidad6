
USE sistema_laboratorio;

CREATE ROLE IF NOT EXISTS 'rol_lab_admin';
CREATE ROLE IF NOT EXISTS 'rol_lab_operador';
CREATE ROLE IF NOT EXISTS 'rol_lab_consulta';
CREATE ROLE IF NOT EXISTS 'rol_lab_aplicacion';

GRANT ALL PRIVILEGES ON sistema_laboratorio.* TO 'rol_lab_admin';

-- El operador consulta catalogo/historial y realiza cambios por procedimientos.
-- No tiene INSERT/UPDATE directo sobre productos o movimientos.
GRANT SELECT ON sistema_laboratorio.productos_lab TO 'rol_lab_operador';
GRANT SELECT ON sistema_laboratorio.movimientos TO 'rol_lab_operador';
GRANT SELECT ON sistema_laboratorio.vw_inventario_resumen TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_obtener_usuario_login TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_buscar_producto_codigo TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_registrar_producto TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_actualizar_producto TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_registrar_movimiento TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_historial_movimientos TO 'rol_lab_operador';

-- Consulta tiene acceso de lectura y puede usar las consultas de la aplicacion.
GRANT SELECT ON sistema_laboratorio.productos_lab TO 'rol_lab_consulta';
GRANT SELECT ON sistema_laboratorio.movimientos TO 'rol_lab_consulta';
GRANT SELECT ON sistema_laboratorio.vw_inventario_resumen TO 'rol_lab_consulta';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_obtener_usuario_login TO 'rol_lab_consulta';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_buscar_producto_codigo TO 'rol_lab_consulta';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_historial_movimientos TO 'rol_lab_consulta';

-- Cuenta tecnica local usada por la aplicacion de escritorio.
-- Los permisos de cada persona se aplican en Python con usuarios.rol.
GRANT SELECT ON sistema_laboratorio.productos_lab TO 'rol_lab_aplicacion';
GRANT SELECT ON sistema_laboratorio.movimientos TO 'rol_lab_aplicacion';
GRANT SELECT ON sistema_laboratorio.vw_inventario_resumen TO 'rol_lab_aplicacion';
GRANT SELECT (id_usuario, nombre_completo, nombre_usuario, rol, estado)
  ON sistema_laboratorio.usuarios TO 'rol_lab_aplicacion';
GRANT INSERT (nombre_completo, nombre_usuario, password_hash, rol, estado)
  ON sistema_laboratorio.usuarios TO 'rol_lab_aplicacion';
GRANT UPDATE (estado) ON sistema_laboratorio.usuarios TO 'rol_lab_aplicacion';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_obtener_usuario_login TO 'rol_lab_aplicacion';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_buscar_producto_codigo TO 'rol_lab_aplicacion';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_registrar_producto TO 'rol_lab_aplicacion';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_actualizar_producto TO 'rol_lab_aplicacion';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_registrar_movimiento TO 'rol_lab_aplicacion';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_historial_movimientos TO 'rol_lab_aplicacion';
GRANT EXECUTE ON FUNCTION sistema_laboratorio.fn_dias_para_caducar TO 'rol_lab_aplicacion';
GRANT EXECUTE ON FUNCTION sistema_laboratorio.fn_hay_existencia TO 'rol_lab_aplicacion';

-- Crear la cuenta MySQL con una contrasena local y asignarle el rol:
-- CREATE USER 'app_laboratorio'@'localhost' IDENTIFIED BY 'contrasena-local';
-- GRANT 'rol_lab_aplicacion' TO 'app_laboratorio'@'localhost';
-- SET DEFAULT ROLE 'rol_lab_aplicacion' TO 'app_laboratorio'@'localhost';

