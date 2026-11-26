

CREATE DATABASE IF NOT EXISTS sistema_laboratorio
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sistema_laboratorio;

CREATE TABLE IF NOT EXISTS usuarios (
  id_usuario INT AUTO_INCREMENT PRIMARY KEY,
  nombre_completo VARCHAR(120) NOT NULL,
  nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  rol ENUM('admin', 'operador', 'consulta') NOT NULL DEFAULT 'operador',
  estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
  fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_usuario_nombre_no_vacio
    CHECK (CHAR_LENGTH(TRIM(nombre_usuario)) > 0)
);

CREATE TABLE IF NOT EXISTS productos_lab (
  id_producto INT AUTO_INCREMENT PRIMARY KEY,
  codigo_barras VARCHAR(64) NOT NULL UNIQUE,
  nombre VARCHAR(120) NOT NULL,
  tipo ENUM('reactivo', 'material') NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  fecha_caducidad DATE NULL,
  descripcion VARCHAR(255) NULL,
  fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_codigo_barras_no_vacio
    CHECK (CHAR_LENGTH(TRIM(codigo_barras)) > 0),
  CONSTRAINT chk_nombre_producto_no_vacio
    CHECK (CHAR_LENGTH(TRIM(nombre)) > 0),
  CONSTRAINT chk_stock_no_negativo CHECK (stock >= 0)
);

CREATE TABLE IF NOT EXISTS movimientos (
  id_movimiento BIGINT AUTO_INCREMENT PRIMARY KEY,
  id_producto INT NOT NULL,
  id_usuario INT NOT NULL,
  tipo_movimiento ENUM('entrada', 'salida') NOT NULL,
  cantidad INT NOT NULL,
  fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_movimiento_producto FOREIGN KEY (id_producto)
    REFERENCES productos_lab(id_producto)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_movimiento_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios(id_usuario)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_cantidad_positiva CHECK (cantidad > 0),
  INDEX idx_movimientos_producto_fecha (id_producto, fecha_hora),
  INDEX idx_movimientos_usuario_fecha (id_usuario, fecha_hora)
);

CREATE TABLE IF NOT EXISTS auditoria (
  id_auditoria BIGINT AUTO_INCREMENT PRIMARY KEY,
  tabla_afectada VARCHAR(64) NOT NULL,
  id_registro VARCHAR(64) NOT NULL,
  tipo_operacion ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
  fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  id_movimiento BIGINT NULL,
  id_usuario INT NULL,
  usuario_responsable VARCHAR(120) NOT NULL,
  informacion_anterior JSON NULL,
  informacion_nueva JSON NULL,
  CONSTRAINT fk_auditoria_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios(id_usuario)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_auditoria_movimiento FOREIGN KEY (id_movimiento)
    REFERENCES movimientos(id_movimiento)
    ON UPDATE CASCADE ON DELETE SET NULL,
  INDEX idx_auditoria_tabla_fecha (tabla_afectada, fecha_hora),
  INDEX idx_auditoria_usuario_fecha (id_usuario, fecha_hora)
);

-- Cuentas locales de demostracion. Cambiar sus contrasenas antes de cualquier uso real.
-- Contrasena inicial de las tres cuentas: LabDemo-2026!
INSERT INTO usuarios
  (id_usuario, nombre_completo, nombre_usuario, password_hash, rol, estado)
VALUES
  (1, 'Administracion de laboratorio', 'admin_demo',
   'scrypt$16384$8$1$bGFiLWFkbWluLWRlbW8=$pCNR/yDhxaOputvvUcGfiakAPlQRcpmA7y0/wbrZ9tNuNY0XBLM8aidP0FR2XNmRYpATH8tIr522iftzb5qzcw==',
   'admin', 'activo'),
  (2, 'Operador de laboratorio', 'operador_demo',
   'scrypt$16384$8$1$bGFiLW9wZXJhZG9yLWRlbW8=$N0MKKYNOYGy5ZN17aNERps7SmvUsvaamEwaI1kum96ZsUdNpB+/Ngswl9UYlQp7xdjyx2t9U2il4bFrlVPOOpw==',
   'operador', 'activo'),
  (3, 'Consulta de laboratorio', 'consulta_demo',
   'scrypt$16384$8$1$bGFiLWNvbnN1bHRhLWRlbW8=$lFYn9fST0GHfV5XgFJmOhOeyjNLaS8Oa2bcVM/uKWrjNp+FsB1WEES/4r+vRIum5G/bNz42p6dF4uVkN7td72g==',
   'consulta', 'activo')
ON DUPLICATE KEY UPDATE
  nombre_completo = VALUES(nombre_completo),
  rol = VALUES(rol),
  estado = VALUES(estado);

INSERT INTO productos_lab
  (id_producto, codigo_barras, nombre, tipo, stock, fecha_caducidad, descripcion)
VALUES
  (1, '7501000000012', 'Etanol 96%', 'reactivo', 12, '2027-06-30', 'Botella de 1 litro'),
  (2, '7501000000029', 'Acetona', 'reactivo', 8, '2027-03-31', 'Botella de 500 mililitros'),
  (3, '7501000000036', 'Guantes de nitrilo', 'material', 40, NULL, 'Caja de 100 piezas'),
  (4, '7501000000043', 'Vaso de precipitados 250 ml', 'material', 15, NULL, 'Vidrio borosilicato')
ON DUPLICATE KEY UPDATE
  nombre = VALUES(nombre),
  tipo = VALUES(tipo),
  fecha_caducidad = VALUES(fecha_caducidad),
  descripcion = VALUES(descripcion);

-- Historial semilla de movimientos. El stock de productos_lab ya representa
-- el saldo posterior a estos movimientos. Se insertan antes de crear triggers.
INSERT INTO movimientos
  (id_movimiento, id_producto, id_usuario, tipo_movimiento, cantidad, fecha_hora)
VALUES
  (1, 1, 2, 'entrada', 14, '2026-11-18 09:00:00'),
  (2, 1, 2, 'salida',   2, '2026-11-20 10:15:00'),
  (3, 2, 2, 'entrada', 10, '2026-11-18 09:10:00'),
  (4, 2, 2, 'salida',   2, '2026-11-21 11:30:00'),
  (5, 3, 2, 'entrada', 50, '2026-11-18 09:20:00'),
  (6, 3, 2, 'salida',  10, '2026-11-22 12:00:00'),
  (7, 4, 2, 'entrada', 20, '2026-11-18 09:30:00'),
  (8, 4, 2, 'salida',   5, '2026-11-23 14:20:00')
ON DUPLICATE KEY UPDATE
  id_producto = VALUES(id_producto),
  id_usuario = VALUES(id_usuario),
  tipo_movimiento = VALUES(tipo_movimiento),
  cantidad = VALUES(cantidad),
  fecha_hora = VALUES(fecha_hora);
