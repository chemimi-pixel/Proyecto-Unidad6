# Etapa 2: aplicacion grafica

La interfaz se implemento con Tkinter y se conecta a MySQL usando `mysql-connector-python`. La configuracion local se lee desde `.env`; el ejemplo se encuentra en `.env.example`.

## Pantallas

- **Inicio de sesion:** consulta `sp_obtener_usuario_login`, verifica el hash scrypt con la biblioteca estandar de Python y rechaza cuentas inactivas.
- **Inventario:** muestra existencias y caducidades mediante `vw_inventario_resumen`; permite buscar, registrar y editar datos de producto. Las existencias solo cambian con movimientos.
- **Movimientos:** busca o escanea productos, registra entradas/salidas por `sp_registrar_movimiento` y muestra el historial. Solo administrador y operador pueden registrar movimientos.
- **Reportes:** presenta consumo por producto/responsable y reactivos proximos a caducar. Las consultas usan JOIN, subconsulta correlacionada, funciones, agregaciones, GROUP BY y HAVING.
- **Usuarios:** solo el administrador puede crear cuentas o activarlas/desactivarlas. Las contrasenas nuevas se guardan como hash scrypt.

## Lector fisico

El campo de codigo esta preparado para lectores USB que emulan teclado y envian Enter. La lectura inicia una busqueda real con `sp_buscar_producto_codigo`; en la pantalla de movimientos se puede continuar con el registro de una entrada o salida. La evidencia de presentacion debe obtenerse con el lector conectado.

## Permisos

La interfaz restringe el registro de productos y movimientos a los roles administrador y operador; el perfil consulta puede buscar, revisar historial y generar reportes. La pestaña de cuentas solo se muestra al administrador. La cuenta tecnica MySQL de la aplicacion usa `rol_lab_aplicacion`, con acceso limitado a las consultas, procedimientos y columnas que necesita.

## Continuacion

La etapa 3 debe recorrer casos exitosos y de error con MySQL, demostrar los roles y el lector fisico, revisar transacciones y auditoria, y preparar las evidencias y la entrega final.
