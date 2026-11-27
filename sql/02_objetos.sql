-- Funciones, procedimientos, vistas y triggers.
-- Ejecutar despues de sqlnofinal.sql. Compatible con MySQL 8.0.16+.
USE sistema_laboratorio;

DROP VIEW IF EXISTS vw_inventario_resumen;
DROP PROCEDURE IF EXISTS sp_buscar_producto_codigo;
DROP PROCEDURE IF EXISTS sp_obtener_usuario_login;
DROP PROCEDURE IF EXISTS sp_registrar_producto;
DROP PROCEDURE IF EXISTS sp_actualizar_producto;
DROP PROCEDURE IF EXISTS sp_registrar_movimiento;
DROP PROCEDURE IF EXISTS sp_historial_movimientos;
DROP FUNCTION IF EXISTS fn_dias_para_caducar;
DROP FUNCTION IF EXISTS fn_hay_existencia;
DROP TRIGGER IF EXISTS bi_productos_lab_validar;
DROP TRIGGER IF EXISTS bu_productos_lab_validar;
DROP TRIGGER IF EXISTS bi_movimientos_validar;
DROP TRIGGER IF EXISTS ai_movimientos_actualizar_stock;
DROP TRIGGER IF EXISTS ai_productos_lab_auditar;
DROP TRIGGER IF EXISTS au_productos_lab_auditar;
DROP TRIGGER IF EXISTS ad_productos_lab_auditar;

DELIMITER $$

CREATE FUNCTION fn_dias_para_caducar(p_fecha DATE)
RETURNS INT
NOT DETERMINISTIC
NO SQL
BEGIN
  IF p_fecha IS NULL THEN
    RETURN NULL;
  END IF;
  RETURN DATEDIFF(p_fecha, CURRENT_DATE());
END$$

CREATE FUNCTION fn_hay_existencia(p_id_producto INT)
RETURNS TINYINT
READS SQL DATA
BEGIN
  DECLARE v_stock INT DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_stock = NULL;

  SELECT stock INTO v_stock
  FROM productos_lab
  WHERE id_producto = p_id_producto;

  RETURN IF(v_stock > 0, 1, 0);
END$$

CREATE PROCEDURE sp_buscar_producto_codigo(IN p_codigo_barras VARCHAR(64))
READS SQL DATA
BEGIN
  SELECT id_producto, codigo_barras, nombre, tipo, stock,
         fecha_caducidad, descripcion
  FROM productos_lab
  WHERE codigo_barras = TRIM(p_codigo_barras);
END$$

CREATE PROCEDURE sp_obtener_usuario_login(IN p_nombre_usuario VARCHAR(50))
READS SQL DATA
BEGIN
  SELECT id_usuario, nombre_completo, nombre_usuario, password_hash, rol, estado
  FROM usuarios
  WHERE nombre_usuario = TRIM(p_nombre_usuario)
  LIMIT 1;
END$$

CREATE PROCEDURE sp_registrar_producto(
  IN p_id_usuario INT,
  IN p_codigo_barras VARCHAR(64),
  IN p_nombre VARCHAR(120),
  IN p_tipo VARCHAR(16),
  IN p_stock_inicial INT,
  IN p_fecha_caducidad DATE,
  IN p_descripcion VARCHAR(255),
  OUT p_id_producto INT
)
MODIFIES SQL DATA
BEGIN
  DECLARE v_nombre_usuario VARCHAR(50) DEFAULT NULL;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    SET @app_usuario_id = NULL;
    SET @app_nombre_usuario = NULL;
    RESIGNAL;
  END;

  SET p_id_producto = NULL;
  IF p_codigo_barras IS NULL OR CHAR_LENGTH(TRIM(p_codigo_barras)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El codigo de barras es obligatorio.';
  END IF;
  IF p_nombre IS NULL OR CHAR_LENGTH(TRIM(p_nombre)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El nombre del producto es obligatorio.';
  END IF;
  IF p_tipo IS NULL OR p_tipo NOT IN ('reactivo', 'material') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El tipo debe ser reactivo o material.';
  END IF;
  IF p_stock_inicial IS NULL OR p_stock_inicial < 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El stock inicial no puede ser negativo.';
  END IF;

  SELECT nombre_usuario INTO v_nombre_usuario
  FROM usuarios
  WHERE id_usuario = p_id_usuario AND estado = 'activo';
  IF v_nombre_usuario IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El usuario responsable no esta activo.';
  END IF;

  START TRANSACTION;
  SET @app_usuario_id = p_id_usuario;
  SET @app_nombre_usuario = v_nombre_usuario;
  INSERT INTO productos_lab
    (codigo_barras, nombre, tipo, stock, fecha_caducidad, descripcion)
  VALUES
    (TRIM(p_codigo_barras), TRIM(p_nombre), p_tipo, p_stock_inicial,
     p_fecha_caducidad, p_descripcion);
  SET p_id_producto = LAST_INSERT_ID();
  SET @app_usuario_id = NULL;
  SET @app_nombre_usuario = NULL;
  COMMIT;
END$$

CREATE PROCEDURE sp_actualizar_producto(
  IN p_id_usuario INT,
  IN p_id_producto INT,
  IN p_codigo_barras VARCHAR(64),
  IN p_nombre VARCHAR(120),
  IN p_tipo VARCHAR(16),
  IN p_fecha_caducidad DATE,
  IN p_descripcion VARCHAR(255)
)
MODIFIES SQL DATA
BEGIN
  DECLARE v_nombre_usuario VARCHAR(50) DEFAULT NULL;
  DECLARE v_producto_existe INT DEFAULT 0;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    SET @app_usuario_id = NULL;
    SET @app_nombre_usuario = NULL;
    RESIGNAL;
  END;

  IF p_codigo_barras IS NULL OR CHAR_LENGTH(TRIM(p_codigo_barras)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El codigo de barras es obligatorio.';
  END IF;
  IF p_nombre IS NULL OR CHAR_LENGTH(TRIM(p_nombre)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El nombre del producto es obligatorio.';
  END IF;
  IF p_tipo IS NULL OR p_tipo NOT IN ('reactivo', 'material') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El tipo debe ser reactivo o material.';
  END IF;

  SELECT nombre_usuario INTO v_nombre_usuario
  FROM usuarios
  WHERE id_usuario = p_id_usuario AND estado = 'activo';
  IF v_nombre_usuario IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El usuario responsable no esta activo.';
  END IF;
  SELECT COUNT(*) INTO v_producto_existe
  FROM productos_lab WHERE id_producto = p_id_producto;
  IF v_producto_existe = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El producto no existe.';
  END IF;

  START TRANSACTION;
  SET @app_usuario_id = p_id_usuario;
  SET @app_nombre_usuario = v_nombre_usuario;
  UPDATE productos_lab
  SET codigo_barras = TRIM(p_codigo_barras),
      nombre = TRIM(p_nombre),
      tipo = p_tipo,
      fecha_caducidad = p_fecha_caducidad,
      descripcion = p_descripcion
  WHERE id_producto = p_id_producto;
  SET @app_usuario_id = NULL;
  SET @app_nombre_usuario = NULL;
  COMMIT;
END$$

CREATE PROCEDURE sp_registrar_movimiento(
  IN p_id_producto INT,
  IN p_id_usuario INT,
  IN p_tipo_movimiento VARCHAR(16),
  IN p_cantidad INT,
  OUT p_id_movimiento BIGINT,
  OUT p_stock_resultante INT
)
MODIFIES SQL DATA
BEGIN
  DECLARE v_stock INT DEFAULT NULL;
  DECLARE v_nombre_usuario VARCHAR(50) DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_stock = NULL;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    SET @app_usuario_id = NULL;
    SET @app_nombre_usuario = NULL;
    RESIGNAL;
  END;

  SET p_id_movimiento = NULL;
  SET p_stock_resultante = NULL;
  IF p_tipo_movimiento IS NULL OR p_tipo_movimiento NOT IN ('entrada', 'salida') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El movimiento debe ser entrada o salida.';
  END IF;
  IF p_cantidad IS NULL OR p_cantidad <= 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cantidad debe ser mayor que cero.';
  END IF;

  SELECT nombre_usuario INTO v_nombre_usuario
  FROM usuarios
  WHERE id_usuario = p_id_usuario AND estado = 'activo';
  IF v_nombre_usuario IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El usuario responsable no esta activo.';
  END IF;

  START TRANSACTION;
  SELECT stock INTO v_stock
  FROM productos_lab
  WHERE id_producto = p_id_producto
  FOR UPDATE;

  IF v_stock IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El producto no existe.';
  END IF;
  IF p_tipo_movimiento = 'salida' AND v_stock < p_cantidad THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No hay existencias suficientes.';
  END IF;

  SET @app_usuario_id = p_id_usuario;
  SET @app_nombre_usuario = v_nombre_usuario;
  INSERT INTO movimientos (id_producto, id_usuario, tipo_movimiento, cantidad)
  VALUES (p_id_producto, p_id_usuario, p_tipo_movimiento, p_cantidad);
  SET p_id_movimiento = LAST_INSERT_ID();

  SELECT stock INTO p_stock_resultante
  FROM productos_lab
  WHERE id_producto = p_id_producto;
  SET @app_usuario_id = NULL;
  SET @app_nombre_usuario = NULL;
  COMMIT;
END$$

CREATE PROCEDURE sp_historial_movimientos(IN p_id_producto INT)
READS SQL DATA
BEGIN
  SELECT m.id_movimiento, p.codigo_barras, p.nombre AS producto,
         m.tipo_movimiento, m.cantidad, m.fecha_hora,
         u.id_usuario, u.nombre_completo AS responsable
  FROM movimientos AS m
  INNER JOIN productos_lab AS p ON p.id_producto = m.id_producto
  INNER JOIN usuarios AS u ON u.id_usuario = m.id_usuario
  WHERE p_id_producto IS NULL OR m.id_producto = p_id_producto
  ORDER BY m.fecha_hora DESC, m.id_movimiento DESC;
END$$

CREATE TRIGGER bi_productos_lab_validar
BEFORE INSERT ON productos_lab
FOR EACH ROW
BEGIN
  IF NEW.codigo_barras IS NULL OR CHAR_LENGTH(TRIM(NEW.codigo_barras)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El codigo de barras no puede estar vacio.';
  END IF;
  IF NEW.nombre IS NULL OR CHAR_LENGTH(TRIM(NEW.nombre)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El nombre del producto no puede estar vacio.';
  END IF;
  IF NEW.stock < 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El stock no puede ser negativo.';
  END IF;
END$$

CREATE TRIGGER bu_productos_lab_validar
BEFORE UPDATE ON productos_lab
FOR EACH ROW
BEGIN
  IF NEW.codigo_barras IS NULL OR CHAR_LENGTH(TRIM(NEW.codigo_barras)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El codigo de barras no puede estar vacio.';
  END IF;
  IF NEW.nombre IS NULL OR CHAR_LENGTH(TRIM(NEW.nombre)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El nombre del producto no puede estar vacio.';
  END IF;
  IF NEW.stock < 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El stock no puede ser negativo.';
  END IF;
END$$

CREATE TRIGGER bi_movimientos_validar
BEFORE INSERT ON movimientos
FOR EACH ROW
BEGIN
  DECLARE v_stock INT DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_stock = NULL;

  IF NEW.cantidad IS NULL OR NEW.cantidad <= 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cantidad debe ser mayor que cero.';
  END IF;
  SELECT stock INTO v_stock
  FROM productos_lab
  WHERE id_producto = NEW.id_producto;
  IF v_stock IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El producto del movimiento no existe.';
  END IF;
  IF NEW.tipo_movimiento = 'salida' AND v_stock < NEW.cantidad THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No hay existencias suficientes.';
  END IF;
END$$

CREATE TRIGGER ai_movimientos_actualizar_stock
AFTER INSERT ON movimientos
FOR EACH ROW
BEGIN
  DECLARE v_stock_anterior INT DEFAULT NULL;
  DECLARE v_nombre_usuario VARCHAR(50) DEFAULT NULL;
  DECLARE v_usuario_previo INT DEFAULT NULL;
  DECLARE v_nombre_previo VARCHAR(120) DEFAULT NULL;
  DECLARE v_movimiento_previo BIGINT DEFAULT NULL;

  SET v_usuario_previo = @app_usuario_id;
  SET v_nombre_previo = @app_nombre_usuario;
  SET v_movimiento_previo = @app_id_movimiento;
  SELECT nombre_usuario INTO v_nombre_usuario
  FROM usuarios WHERE id_usuario = NEW.id_usuario;
  SET @app_usuario_id = NEW.id_usuario;
  SET @app_nombre_usuario = v_nombre_usuario;
  SET @app_id_movimiento = NEW.id_movimiento;

  IF NEW.tipo_movimiento = 'entrada' THEN
    UPDATE productos_lab
    SET stock = stock + NEW.cantidad
    WHERE id_producto = NEW.id_producto;
  ELSE
    SELECT stock INTO v_stock_anterior
    FROM productos_lab
    WHERE id_producto = NEW.id_producto
    FOR UPDATE;
    IF v_stock_anterior < NEW.cantidad THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No hay existencias suficientes para registrar la salida.';
    END IF;
    UPDATE productos_lab
    SET stock = stock - NEW.cantidad
    WHERE id_producto = NEW.id_producto;
  END IF;

  SET @app_usuario_id = v_usuario_previo;
  SET @app_nombre_usuario = v_nombre_previo;
  SET @app_id_movimiento = v_movimiento_previo;
END$$

CREATE TRIGGER ai_productos_lab_auditar
AFTER INSERT ON productos_lab
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (tabla_afectada, id_registro, tipo_operacion, id_movimiento, id_usuario,
     usuario_responsable, informacion_anterior, informacion_nueva)
  VALUES
    ('productos_lab', CAST(NEW.id_producto AS CHAR), 'INSERT', @app_id_movimiento, @app_usuario_id,
     COALESCE(NULLIF(@app_nombre_usuario, ''), CURRENT_USER()), NULL,
     JSON_OBJECT('codigo_barras', NEW.codigo_barras, 'nombre', NEW.nombre,
                 'tipo', NEW.tipo, 'stock', NEW.stock,
                 'fecha_caducidad', NEW.fecha_caducidad,
                 'descripcion', NEW.descripcion));
END$$

CREATE TRIGGER au_productos_lab_auditar
AFTER UPDATE ON productos_lab
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (tabla_afectada, id_registro, tipo_operacion, id_movimiento, id_usuario,
     usuario_responsable, informacion_anterior, informacion_nueva)
  VALUES
    ('productos_lab', CAST(NEW.id_producto AS CHAR), 'UPDATE', @app_id_movimiento, @app_usuario_id,
     COALESCE(NULLIF(@app_nombre_usuario, ''), CURRENT_USER()),
     JSON_OBJECT('codigo_barras', OLD.codigo_barras, 'nombre', OLD.nombre,
                 'tipo', OLD.tipo, 'stock', OLD.stock,
                 'fecha_caducidad', OLD.fecha_caducidad,
                 'descripcion', OLD.descripcion),
     JSON_OBJECT('codigo_barras', NEW.codigo_barras, 'nombre', NEW.nombre,
                 'tipo', NEW.tipo, 'stock', NEW.stock,
                 'fecha_caducidad', NEW.fecha_caducidad,
                 'descripcion', NEW.descripcion));
END$$

CREATE TRIGGER ad_productos_lab_auditar
AFTER DELETE ON productos_lab
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (tabla_afectada, id_registro, tipo_operacion, id_movimiento, id_usuario,
     usuario_responsable, informacion_anterior, informacion_nueva)
  VALUES
    ('productos_lab', CAST(OLD.id_producto AS CHAR), 'DELETE', @app_id_movimiento, @app_usuario_id,
     COALESCE(NULLIF(@app_nombre_usuario, ''), CURRENT_USER()),
     JSON_OBJECT('codigo_barras', OLD.codigo_barras, 'nombre', OLD.nombre,
                 'tipo', OLD.tipo, 'stock', OLD.stock,
                 'fecha_caducidad', OLD.fecha_caducidad,
                 'descripcion', OLD.descripcion), NULL);
END$$

DELIMITER ;

CREATE OR REPLACE VIEW vw_inventario_resumen AS
SELECT p.id_producto, p.codigo_barras, p.nombre, p.tipo, p.stock,
       p.fecha_caducidad,
       fn_dias_para_caducar(p.fecha_caducidad) AS dias_para_caducar,
       fn_hay_existencia(p.id_producto) AS disponible,
       CASE
         WHEN p.fecha_caducidad IS NULL THEN 'sin caducidad'
         WHEN fn_dias_para_caducar(p.fecha_caducidad) < 0 THEN 'caducado'
         WHEN fn_dias_para_caducar(p.fecha_caducidad) <= 30 THEN 'proximo a caducar'
         ELSE 'vigente'
       END AS estado_caducidad
FROM productos_lab AS p;
