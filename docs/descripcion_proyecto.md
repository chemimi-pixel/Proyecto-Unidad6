# Descripcion y justificacion del sistema

## Problema

En un laboratorio universitario, el control manual de reactivos y materiales puede dificultar conocer las existencias actuales, registrar quien retiro o ingreso material, y detectar reactivos proximos a caducar. Si los movimientos y el inventario se conservan por separado, es facil que los saldos no coincidan o que no se pueda reconstruir el historial de un producto.

## Solucion propuesta

El Sistema de administracion de laboratorio es una aplicacion de escritorio en Python conectada a una base de datos relacional MySQL. Identifica productos con codigos de barras, registra entradas y salidas con usuario responsable, actualiza las existencias de forma transaccional y permite consultar el historial y reportes de consumo y caducidad.

## Justificacion

La propuesta atiende una necesidad concreta del laboratorio y aplica los temas del curso: modelo relacional, integridad referencial, restricciones, procedimientos almacenados, funciones, triggers de validacion y auditoria, control de acceso y consultas avanzadas. El lector fisico acelera la busqueda del registro y participa en una operacion real. La interfaz se mantiene sencilla para que el equipo pueda explicarla y demostrarla.

## Alcance y limites

El sistema administra reactivos y materiales, existencias, fechas de caducidad, usuarios e historial de movimientos. No es un punto de venta: no registra ventas, cobros ni clientes. El control por lotes no forma parte de la version acordada.
