
USE sistema_laboratorio;

CREATE ROLE IF NOT EXISTS 'rol_lab_admin';
CREATE ROLE IF NOT EXISTS 'rol_lab_operador';
CREATE ROLE IF NOT EXISTS 'rol_lab_consulta';

GRANT ALL PRIVILEGES ON sistema_laboratorio.* TO 'rol_lab_admin';

-- El operador consulta catalogo/historial y realiza cambios por procedimientos.
-- No tiene INSERT/UPDATE directo sobre productos o movimientos.
GRANT SELECT ON sistema_laboratorio.productos_lab TO 'rol_lab_operador';
GRANT SELECT ON sistema_laboratorio.movimientos TO 'rol_lab_operador';
GRANT SELECT ON sistema_laboratorio.vw_inventario_resumen TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_obtener_usuario_login TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_buscar_producto_codigo TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_registrar_producto TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_registrar_movimiento TO 'rol_lab_operador';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_historial_movimientos TO 'rol_lab_operador';

-- Consulta tiene acceso de lectura y puede usar las consultas de la aplicacion.
GRANT SELECT ON sistema_laboratorio.productos_lab TO 'rol_lab_consulta';
GRANT SELECT ON sistema_laboratorio.movimientos TO 'rol_lab_consulta';
GRANT SELECT ON sistema_laboratorio.vw_inventario_resumen TO 'rol_lab_consulta';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_obtener_usuario_login TO 'rol_lab_consulta';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_buscar_producto_codigo TO 'rol_lab_consulta';
GRANT EXECUTE ON PROCEDURE sistema_laboratorio.sp_historial_movimientos TO 'rol_lab_consulta';

