create database if not exists sistema_laboratorio
  character set utf8mb4
  collate utf8mb4_unicode_ci;

use sistema_laboratorio;
-- usuarios
create table usuarios (
    id_usuario int auto_increment primary key,
    nombre_completo varchar(120) not null,
    nombre_usuario varchar(50) not null unique,
    password_hash varchar(255) not null,
    rol enum('admin', 'operador', 'consulta') not null default 'operador',
    estado enum('activo', 'inactivo') not null default 'activo'
);

-- materiales
create table productos_lab (
    id_producto int auto_increment primary key,
    codigo_barras varchar(64) not null unique,
    nombre varchar(120) not null,
    tipo enum('reactivo', 'material') not null,
    stock int not null default 0,
    fecha_caducidad date null,
    descripcion varchar(255) null,
    constraint chk_codigo_barras_no_vacio
        check (char_length(trim(codigo_barras)) > 0),
    constraint chk_stock_no_negativo
        check (stock >= 0)
);

-- movimientos
create table movimientos (
    id_movimiento int auto_increment primary key,
    id_producto int not null,
    id_usuario int not null,
    tipo_movimiento enum('entrada', 'salida') not null,
    cantidad int not null,
    fecha_hora datetime not null default current_timestamp,
    foreign key (id_producto) references productos_lab(id_producto)
        on update cascade on delete restrict,
    foreign key (id_usuario) references usuarios(id_usuario)
        on update cascade on delete restrict,
    constraint chk_cantidad_positiva
        check (cantidad > 0)
);