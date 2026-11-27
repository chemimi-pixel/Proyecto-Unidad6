"""Verificaciones de integracion de Etapa 3; --mutate agrega movimientos de prueba."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import mysql.connector

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from laboratorio.database import Database
from laboratorio.security import verify_password


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mutate",
        action="store_true",
        help="Agrega una salida y su entrada compensatoria al historial; stock queda igual.",
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help="Cambia y restaura el nombre de un producto; genera dos filas de auditoria.",
    )
    args = parser.parse_args()
    database = Database()

    products = database.list_products()
    assert products, "El inventario no contiene productos."
    for username, expected_role in (
        ("admin_demo", "admin"),
        ("operador_demo", "operador"),
        ("consulta_demo", "consulta"),
    ):
        user = database.authenticate(username)
        assert user and user["estado"] == "activo", f"No se puede autenticar {username}."
        assert user["rol"] == expected_role, f"Rol inesperado para {username}."
        assert verify_password("LabDemo-2026!", user["password_hash"]), f"Hash invalido: {username}."

    product = database.find_product(products[0]["codigo_barras"])
    assert product, "No se encontro el producto por codigo de barras."
    history = database.movement_history()
    consumption = database.report_consumption()
    expirations = database.report_expiration()
    assert history, "No se devolvio el historial de movimientos."
    assert consumption, "El reporte de consumo no devolvio resultados."
    assert expirations, "El reporte de caducidad no devolvio resultados."
    print("PASS lecturas: inventario, 3 cuentas, busqueda, historial y 2 reportes")

    for label, sql, params in (
        (
            "actualizacion directa de stock",
            "UPDATE productos_lab SET stock = stock + 1 WHERE id_producto = %s",
            (product["id_producto"],),
        ),
        (
            "insercion directa de movimiento",
            "INSERT INTO movimientos (id_producto, id_usuario, tipo_movimiento, cantidad) "
            "VALUES (%s, %s, 'entrada', 1)",
            (product["id_producto"], 2),
        ),
    ):
        connection = database._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(sql, params)
            except mysql.connector.Error as error:
                assert error.errno in (1142, 1143), f"Denegacion inesperada en {label}: {error.errno}."
            else:
                connection.rollback()
                raise AssertionError(f"El rol tecnico permitio {label} directamente.")
            finally:
                cursor.close()
        finally:
            connection.rollback()
            connection.close()
    print("PASS privilegios: escritura directa de stock y movimientos denegada")

    if args.edit:
        original_name = product["nombre"]
        temporary_name = f"{original_name} [prueba etapa 3]"
        edit_operator = database.authenticate("operador_demo")
        assert edit_operator is not None
        fields = (
            int(edit_operator["id_usuario"]),
            int(product["id_producto"]),
            product["codigo_barras"],
            product["tipo"],
            product["fecha_caducidad"].isoformat() if product["fecha_caducidad"] else None,
            product["descripcion"],
        )
        try:
            database.update_product(fields[0], fields[1], fields[2], temporary_name,
                                   fields[3], fields[4], fields[5])
            updated = database.find_product(product["codigo_barras"])
            assert updated and updated["nombre"] == temporary_name
        finally:
            database.update_product(fields[0], fields[1], fields[2], original_name,
                                    fields[3], fields[4], fields[5])
        restored = database.find_product(product["codigo_barras"])
        assert restored and restored["nombre"] == original_name
        assert int(restored["stock"]) == int(product["stock"])
        print("PASS edicion: datos restaurados y stock intacto; 2 eventos de auditoria generados")

    if not args.mutate:
        print("SKIP escrituras; repite con --mutate para agregar dos movimientos de prueba.")
        return

    operator = database.authenticate("operador_demo")
    assert operator is not None
    product_id = int(product["id_producto"])
    user_id = int(operator["id_usuario"])
    initial_stock = int(product["stock"])
    assert initial_stock > 0, "Se necesita stock inicial para probar una salida valida."
    initial_history = len(database.movement_history(product_id))

    out_id, out_stock = database.register_movement(product_id, user_id, "salida", 1)
    assert out_stock == initial_stock - 1, "La salida no descuento una unidad."
    in_id, restored_stock = database.register_movement(product_id, user_id, "entrada", 1)
    assert restored_stock == initial_stock, "La entrada compensatoria no restauro el stock."
    print(f"PASS movimientos validos: salida {out_id}, entrada {in_id}, stock restaurado {restored_stock}")

    before_rejected_exit = len(database.movement_history(product_id))
    try:
        database.register_movement(product_id, user_id, "salida", initial_stock + 1)
    except mysql.connector.Error as error:
        assert error.errno == 1644, f"Error inesperado para la salida excesiva: {error.errno}."
    else:
        raise AssertionError("La base acepto una salida mayor al stock.")
    after_rejected_exit = database.find_product(product["codigo_barras"])
    assert after_rejected_exit and int(after_rejected_exit["stock"]) == initial_stock
    assert len(database.movement_history(product_id)) == before_rejected_exit
    print("PASS rollback/validacion: salida excesiva no cambio stock ni historial")

    product_count = len(database.list_products())
    try:
        database.register_product(
            user_id, product["codigo_barras"], "Producto duplicado de prueba",
            product["tipo"], 0, None, "Prueba de codigo unico",
        )
    except mysql.connector.Error as error:
        assert error.errno == 1062, f"Error inesperado para el codigo duplicado: {error.errno}."
    else:
        raise AssertionError("La base acepto un codigo de barras duplicado.")
    assert len(database.list_products()) == product_count
    print("PASS validacion: codigo duplicado rechazado sin crear producto")
    print(
        f"NOTA: se agregaron dos movimientos de prueba; el historial de este producto paso "
        f"de {initial_history} a {len(database.movement_history(product_id))}."
    )


if __name__ == "__main__":
    main()
