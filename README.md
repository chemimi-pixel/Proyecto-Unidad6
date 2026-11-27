# Sistema de administracion de laboratorio

Aplicacion de escritorio en Python/Tkinter para administrar reactivos y materiales, registrar entradas y salidas, controlar existencias y caducidades, y consultar reportes.

## Requisitos

- Python 3.10 o posterior
- MySQL 8.0.16 o posterior
- Lector fisico de codigos de barras configurado como teclado; normalmente envia Enter al finalizar cada lectura

## Preparar la base de datos

Desde una cuenta administradora de MySQL, ejecutar en este orden:

1. `sqlnofinal.sql`
2. `sql/02_objetos.sql`
3. `sql/03_seguridad.sql`

Despues, crear una cuenta MySQL local para la aplicacion y asignarle el rol tecnico:

```sql
CREATE USER 'app_laboratorio'@'localhost' IDENTIFIED BY 'elige-una-contrasena-local';
GRANT 'rol_lab_aplicacion' TO 'app_laboratorio'@'localhost';
SET DEFAULT ROLE 'rol_lab_aplicacion' TO 'app_laboratorio'@'localhost';
```

Usa una contrasena local propia y no la guardes en Git.

## Instalar y ejecutar

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` con el host, puerto, usuario y contrasena MySQL de tu equipo. Inicia la aplicacion con:

```bash
python main.py
```

Usuarios iniciales de demostracion (`admin_demo`, `operador_demo`, `consulta_demo`): contrasena temporal `LabDemo-2026!`. Cambia esas contrasenas antes de usar el sistema fuera de una demostracion local.

## Funciones

- Inicio de sesion con verificacion scrypt y bloqueo de cuentas inactivas.
- Inventario con busqueda por codigo de barras; el lector fisico escribe el codigo y activa la busqueda al enviar Enter.
- Registro y edicion de productos sin cambiar existencias directamente; altas y salidas se registran como movimientos por procedimientos y triggers de MySQL.
- Historial de movimientos y consulta de caducidades.
- Reportes de consumo por producto y de reactivos proximos a caducar.
- Administracion de cuentas visible solo para el rol administrador.
- Perfil consulta sin controles para modificar datos.

La aplicacion se conecta con una cuenta tecnica local; `usuarios.rol` aplica los permisos funcionales de cada usuario de la interfaz. Limita el acceso a las credenciales MySQL y mantenlas solo en `.env`.
