"""Acceso a MySQL y metodos de negocio usados por la interfaz."""

from __future__ import annotations

from typing import Any

import mysql.connector

from .config import database_config


class Database:
    def __init__(self) -> None:
        self.config = database_config()

    def _connect(self):
        return mysql.connector.connect(**self.config)

    @staticmethod
    def _drain_results(cursor) -> None:
        if cursor.with_rows:
            cursor.fetchall()
        while cursor.nextset():
            if cursor.with_rows:
                cursor.fetchall()

    def _call_for_rows(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall() if cursor.with_rows else []
            while cursor.nextset():
                if cursor.with_rows:
                    cursor.fetchall()
            cursor.close()
            return rows
        finally:
            connection.close()

    def _query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        finally:
            connection.close()

    def authenticate(self, username: str) -> dict[str, Any] | None:
        rows = self._call_for_rows("CALL sp_obtener_usuario_login(%s)", (username.strip(),))
        return rows[0] if rows else None

    def list_products(self) -> list[dict[str, Any]]:
        return self._query(
            """SELECT id_producto, codigo_barras, nombre, tipo, stock,
                      fecha_caducidad, dias_para_caducar, estado_caducidad
               FROM vw_inventario_resumen
               ORDER BY nombre"""
        )

    def find_product(self, barcode: str) -> dict[str, Any] | None:
        rows = self._call_for_rows("CALL sp_buscar_producto_codigo(%s)", (barcode.strip(),))
        return rows[0] if rows else None

    def register_product(
        self,
        user_id: int,
        barcode: str,
        name: str,
        product_type: str,
        stock: int,
        expiration: str | None,
        description: str | None,
    ) -> int:
        connection = self._connect()
        try:
            cursor = connection.cursor(buffered=True)
            cursor.execute(
                "CALL sp_registrar_producto(%s,%s,%s,%s,%s,%s,%s,@app_producto_id)",
                (user_id, barcode, name, product_type, stock, expiration, description),
            )
            self._drain_results(cursor)
            cursor.execute("SELECT @app_producto_id")
            product_id = int(cursor.fetchone()[0])
            connection.commit()
            cursor.close()
            return product_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def register_movement(
        self, product_id: int, user_id: int, movement_type: str, quantity: int
    ) -> tuple[int, int]:
        connection = self._connect()
        try:
            cursor = connection.cursor(buffered=True)
            cursor.execute(
                "CALL sp_registrar_movimiento(%s,%s,%s,%s,@app_movimiento_id,@app_stock_resultante)",
                (product_id, user_id, movement_type, quantity),
            )
            self._drain_results(cursor)
            cursor.execute("SELECT @app_movimiento_id, @app_stock_resultante")
            movement_id, stock = cursor.fetchone()
            connection.commit()
            cursor.close()
            return int(movement_id), int(stock)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def update_product(
        self,
        user_id: int,
        product_id: int,
        barcode: str,
        name: str,
        product_type: str,
        expiration: str | None,
        description: str | None,
    ) -> None:
        connection = self._connect()
        try:
            cursor = connection.cursor(buffered=True)
            cursor.execute(
                "CALL sp_actualizar_producto(%s,%s,%s,%s,%s,%s,%s)",
                (user_id, product_id, barcode, name, product_type, expiration, description),
            )
            self._drain_results(cursor)
            connection.commit()
            cursor.close()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def movement_history(self, product_id: int | None = None) -> list[dict[str, Any]]:
        return self._call_for_rows("CALL sp_historial_movimientos(%s)", (product_id,))

    def list_users(self) -> list[dict[str, Any]]:
        return self._query(
            """SELECT id_usuario, nombre_completo, nombre_usuario, rol, estado
               FROM usuarios ORDER BY nombre_completo"""
        )

    def create_user(
        self, full_name: str, username: str, password_hash: str, role: str
    ) -> int:
        connection = self._connect()
        try:
            cursor = connection.cursor(buffered=True)
            cursor.execute(
                """INSERT INTO usuarios
                   (nombre_completo, nombre_usuario, password_hash, rol, estado)
                   VALUES (%s,%s,%s,%s,'activo')""",
                (full_name.strip(), username.strip(), password_hash, role),
            )
            user_id = int(cursor.lastrowid)
            connection.commit()
            cursor.close()
            return user_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def set_user_status(self, user_id: int, status: str) -> None:
        connection = self._connect()
        try:
            cursor = connection.cursor(buffered=True)
            cursor.execute(
                "UPDATE usuarios SET estado = %s WHERE id_usuario = %s",
                (status, user_id),
            )
            connection.commit()
            cursor.close()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def report_consumption(self) -> list[dict[str, Any]]:
        # JOIN de tres tablas + agregaciones + GROUP BY + HAVING.
        return self._query(
            """SELECT p.codigo_barras, p.nombre, p.tipo,
                      COUNT(DISTINCT m.id_movimiento) AS movimientos,
                      SUM(CASE WHEN m.tipo_movimiento = 'salida'
                               THEN m.cantidad ELSE 0 END) AS total_salidas,
                      GROUP_CONCAT(DISTINCT u.nombre_completo
                                   ORDER BY u.nombre_completo SEPARATOR ', ') AS responsables
               FROM productos_lab AS p
               INNER JOIN movimientos AS m ON m.id_producto = p.id_producto
               INNER JOIN usuarios AS u ON u.id_usuario = m.id_usuario
               GROUP BY p.id_producto, p.codigo_barras, p.nombre, p.tipo
               HAVING total_salidas > 0
               ORDER BY total_salidas DESC, p.nombre"""
        )

    def report_expiration(self) -> list[dict[str, Any]]:
        # JOIN + subconsulta correlacionada + agregacion + GROUP BY + HAVING.
        return self._query(
            """SELECT p.codigo_barras, p.nombre, p.fecha_caducidad,
                      fn_dias_para_caducar(p.fecha_caducidad) AS dias_restantes,
                      COALESCE(SUM(m.cantidad), 0) AS salidas_registradas,
                      (SELECT COUNT(*) FROM movimientos AS mi
                       WHERE mi.id_producto = p.id_producto
                         AND mi.tipo_movimiento = 'salida') AS numero_de_salidas
               FROM productos_lab AS p
               LEFT JOIN movimientos AS m
                 ON m.id_producto = p.id_producto AND m.tipo_movimiento = 'salida'
               WHERE p.tipo = 'reactivo'
                 AND p.fecha_caducidad BETWEEN CURRENT_DATE()
                     AND DATE_ADD(CURRENT_DATE(), INTERVAL 180 DAY)
               GROUP BY p.id_producto, p.codigo_barras, p.nombre, p.fecha_caducidad
               HAVING salidas_registradas > 0
               ORDER BY p.fecha_caducidad, p.nombre"""
        )
