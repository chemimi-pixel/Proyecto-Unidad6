# Etapa 3: verificacion y evidencia

## Estado de verificacion

| Verificacion | Estado | Evidencia disponible |
|---|---|---|
| Compilacion de los modulos Python | Aprobada | `python3 -m compileall -q main.py laboratorio` termino sin errores. |
| Hash scrypt de las tres cuentas semilla | Aprobada | Se verificaron contra `LabDemo-2026!`. |
| Alta y verificacion de un hash nuevo | Aprobada | Hash temporal acepto la contrasena correcta y rechazo otra. |
| Disponibilidad del servidor MySQL | Aprobada | El servidor responde en `127.0.0.1:3306`. |
| Aplicacion de los tres scripts SQL en orden | Aprobada | Confirmado en MySQL Workbench: esquema, objetos y permisos ejecutados. |
| Dependencia Python MySQL | Aprobada | `mysql-connector-python 9.7.0` instalado en `.venv`. |
| Inicio de sesion de las tres cuentas semilla | Aprobada | Admin, operador y consulta activos; hashes correctos. |
| Inventario, busqueda por codigo, historial y reportes | Aprobada | 4 productos, 8 movimientos, busqueda existente y ambos reportes devolvieron filas. |
| Entradas/salidas y actualizacion de stock | Aprobada | Salida 9 y entrada 10 de prueba; el stock del producto volvio de 8 a 8. |
| Salida sin existencias y rollback | Aprobada | Salida excesiva rechazada; stock e historial no cambiaron. |
| Codigo de barras duplicado | Aprobada | Insercion rechazada y el total de productos se mantuvo. |
| Ejecucion de interfaz e inicio administrador | Aprobada | La ventana Tkinter abrio, acepto `admin_demo` y mostro el inventario de 4 productos. |
| Auditoria de movimientos y edicion | Aprobada | Workbench muestra 8 eventos; entradas/salidas enlazan `id_movimiento` y la edicion registra valores anterior/nuevo. |
| Restricciones de escritura directa | Aprobada | El verificador confirma que la cuenta de aplicacion no puede modificar directamente existencias ni movimientos. |
| Permisos por rol en la GUI | Implementada | Se comprobaron las tres cuentas en MySQL; la interfaz reserva Usuarios para admin, habilita operaciones para admin/operador y deja consulta en modo lectura. La ventana de admin tambien se abrio correctamente. |
| Busqueda manual por codigo | Aprobada | El campo acepta codigo escrito y busca al pulsar Enter; usa el mismo flujo previsto para el lector. |
| Lector fisico | Diferida | El sistema esta preparado para lectores que escriben el codigo y envian Enter. No se hara prueba ni se presentara evidencia hasta tener el dispositivo. |
| Ejecucion en equipo de presentacion | Preparada | Instalacion y configuracion estan documentadas; queda ejecutar en el equipo cuando el equipo de evaluacion este disponible. |

Las pruebas de movimientos agregaron dos registros de verificacion al historial del producto Acetona. Su stock quedo igual que al inicio; las filas quedan visibles en reportes como historial real de prueba. La prueba de edicion restauró el nombre original y agregó dos eventos a la auditoria.

## Preparacion

1. Ejecutar `sqlnofinal.sql`, `sql/02_objetos.sql` y `sql/03_seguridad.sql` en ese orden.
2. Crear el usuario MySQL de la aplicacion y asignar `rol_lab_aplicacion` (ver `README.md`).
3. Instalar dependencias, crear `.env` y configurar la conexion (ver `README.md`).
4. Iniciar con cada cuenta semilla: `admin_demo`, `operador_demo` y `consulta_demo`. Contrasena temporal local: `LabDemo-2026!`. El flujo de permisos esta en la interfaz y las tres cuentas se validaron contra MySQL.
5. Para demostrar la busqueda mientras no haya lector, escribir un codigo existente y pulsar Enter. Cuando se tenga el lector, confirmar que envia codigo y Enter, y guardar evidencia real en `evidencias/`.
6. El verificador repetible esta en `scripts/verificar_etapa3.py`; ejecuta primero sin `--mutate` para lecturas y usa esa opcion solo cuando se autorice agregar dos movimientos de prueba.

## Casos de verificacion

| ID | Caso | Resultado esperado | Evidencia a guardar |
|---|---|---|---|
| DB-01 | Crear el esquema desde cero y consultar las tablas | Existen `usuarios`, `productos_lab`, `movimientos` y `auditoria`, con datos semilla. | Salida de MySQL o captura del gestor. |
| AUTH-01 | Iniciar sesion con cada cuenta activa | Se abre la interfaz con el nombre y rol correctos. | Captura por rol, sin mostrar contrasenas. |
| AUTH-02 | Usar contrasena incorrecta y cuenta inactiva | La aplicacion rechaza el acceso con un mensaje general. | Captura del mensaje, sin datos sensibles. |
| ROLE-01 | Entrar como consulta | Puede buscar, revisar movimientos y reportes; no puede registrar producto ni movimiento ni ver la pestaña Usuarios. | Captura de la interfaz. |
| ROLE-02 | Entrar como operador | Puede registrar/editar productos y movimientos; no ve la pestaña Usuarios. | Captura de la interfaz. |
| ROLE-03 | Entrar como administrador | Puede realizar operaciones y administrar cuentas. | Captura de la interfaz. |
| BAR-01 | Escanear un codigo existente con el lector USB | El campo recibe codigo + Enter, encuentra el producto y permite continuar con un movimiento. | Foto o video corto del lector conectado y la pantalla con el resultado. |
| PROD-01 | Registrar producto con codigo nuevo y datos validos | Se agrega al inventario y aparece en la busqueda. | Captura antes/despues. |
| PROD-02 | Registrar codigo duplicado, codigo vacio o stock negativo | La base rechaza la operacion y el inventario queda igual. | Mensaje de error y captura del inventario. |
| PROD-03 | Editar nombre o caducidad | Cambian los datos; el stock no se edita desde el formulario. | Captura del registro actualizado. |
| MOV-01 | Registrar entrada | Se crea movimiento, aumenta el stock y queda el usuario responsable. | Captura del movimiento e inventario actualizado. |
| MOV-02 | Registrar salida disponible | Se crea movimiento, disminuye el stock y queda el usuario responsable. | Captura del movimiento e inventario actualizado. |
| MOV-03 | Intentar salida mayor al stock | La operacion falla y ni el stock ni el historial cambian. | Captura antes/despues y mensaje de error. |
| AUD-01 | Revisar auditoria despues de entrada, salida y edicion de producto | Se registran cambios con tabla, registro, operacion, fecha, usuario y valores anterior/nuevo cuando aplica; los ajustes de stock enlazan `id_movimiento`. | Consulta de `auditoria`. |
| REP-01 | Generar consumo por producto | Muestra salidas y responsables con JOIN de tres tablas, agregacion, GROUP BY y HAVING. | Captura del reporte. |
| REP-02 | Generar reactivos proximos a caducar | Muestra caducidad, dias y consumo usando JOIN, subconsulta, agregacion, GROUP BY y HAVING. | Captura del reporte. |
| DEP-01 | Ejecutar en el equipo de presentacion | La aplicacion conecta con la base y funciona sin depender del entorno de desarrollo. | Captura de ejecucion y archivo de instrucciones. |

## Lector fisico diferido

La integracion esta lista para un lector USB configurado como teclado y con Enter al final de la lectura. Hasta tener el dispositivo, se puede demostrar el mismo campo escribiendo el codigo y pulsando Enter. Despues, guardar en `evidencias/` una foto/video breve del lector conectado y una captura del resultado. No incluir contrasenas, hashes ni configuracion `.env`; no se sustituye la evidencia fisica por una simulacion.

## Resultado final de presentacion

Antes de entregar, ejecutar la app en el equipo de presentacion y anotar fecha/equipo. La prueba del lector queda diferida hasta contar con el dispositivo. Conservar capturas de los casos clave y preparar al equipo para explicar el modelo, los permisos, las transacciones, funciones y triggers.
