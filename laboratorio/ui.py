"""Interfaz grafica Tkinter del sistema de laboratorio."""

from __future__ import annotations

from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from .database import Database
from .security import hash_password


class LoginWindow(tk.Tk):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.user: dict[str, Any] | None = None
        self.title("Sistema de laboratorio | Inicio de sesion")
        self.geometry("390x275")
        self.resizable(False, False)
        self.configure(padx=24, pady=20)

        ttk.Label(self, text="Administracion de laboratorio", font=("Arial", 16, "bold")).pack(pady=(4, 20))
        form = ttk.Frame(self)
        form.pack(fill="x")
        ttk.Label(form, text="Usuario").grid(row=0, column=0, sticky="w", pady=6)
        self.username = ttk.Entry(form, width=30)
        self.username.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=6)
        ttk.Label(form, text="Contrasena").grid(row=1, column=0, sticky="w", pady=6)
        self.password = ttk.Entry(form, width=30, show="*")
        self.password.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=6)
        form.columnconfigure(1, weight=1)

        ttk.Button(self, text="Iniciar sesion", command=self._login).pack(fill="x", pady=(20, 8))
        self.password.bind("<Return>", lambda _event: self._login())
        self.username.focus_set()

    def _login(self) -> None:
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            messagebox.showwarning("Datos incompletos", "Escribe tu usuario y contrasena.", parent=self)
            return
        try:
            user = self.database.authenticate(username)
        except Exception as error:
            messagebox.showerror(
                "No se pudo conectar",
                f"Revisa MySQL y la configuracion local de la aplicacion.\n\n{error}",
                parent=self,
            )
            return
        if not user or user["estado"] != "activo":
            messagebox.showerror("Acceso denegado", "Usuario o contrasena incorrectos.", parent=self)
            self.password.delete(0, tk.END)
            return
        from .security import verify_password

        if not verify_password(password, user["password_hash"]):
            messagebox.showerror("Acceso denegado", "Usuario o contrasena incorrectos.", parent=self)
            self.password.delete(0, tk.END)
            return
        self.user = {key: value for key, value in user.items() if key != "password_hash"}
        self.destroy()


class Dashboard(tk.Tk):
    def __init__(self, user: dict[str, Any], database: Database) -> None:
        super().__init__()
        self.user = user
        self.database = database
        self.can_operate = user["rol"] in ("admin", "operador")
        self.current_product: dict[str, Any] | None = None
        self.title("Sistema de administracion de laboratorio")
        self.geometry("1120x720")
        self.minsize(900, 600)

        self._build_header()
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._build_inventory_tab()
        self._build_movements_tab()
        self._build_reports_tab()
        if user["rol"] == "admin":
            self._build_users_tab()
        self.refresh_products()
        if user["rol"] == "admin":
            self.refresh_users()

    def _build_header(self) -> None:
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Laboratorio", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Label(
            header,
            text=f"{self.user['nombre_completo']}  |  {self.user['rol'].capitalize()}",
        ).pack(side="right")

    @staticmethod
    def _make_tree(parent: ttk.Frame, columns: list[tuple[str, str, int]]) -> ttk.Treeview:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        keys = [column[0] for column in columns]
        tree = ttk.Treeview(frame, columns=keys, show="headings", selectmode="browse")
        for key, heading, width in columns:
            tree.heading(key, text=heading)
            tree.column(key, width=width, minwidth=60, anchor="w")
        vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return tree

    def _build_inventory_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Inventario")
        search = ttk.LabelFrame(tab, text="Buscar por codigo de barras", padding=10)
        search.pack(fill="x", pady=(0, 10))
        self.inventory_barcode = ttk.Entry(search)
        self.inventory_barcode.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(search, text="Buscar", command=self._scan_inventory).pack(side="left")
        self.inventory_barcode.bind("<Return>", lambda _event: self._scan_inventory())
        ttk.Label(
            search,
            text="Escribe o escanea el codigo; Enter inicia la busqueda.",
        ).pack(side="left", padx=(14, 0))

        self.inventory_tree = self._make_tree(
            tab,
            [
                ("barcode", "Codigo", 140), ("name", "Producto", 220),
                ("type", "Tipo", 90), ("stock", "Existencias", 90),
                ("expiry", "Caducidad", 110), ("days", "Dias", 70),
                ("status", "Estado", 150),
            ],
        )
        actions = ttk.Frame(tab, padding=(0, 10, 0, 0))
        actions.pack(fill="x")
        ttk.Button(actions, text="Actualizar inventario", command=self.refresh_products).pack(side="left")
        if self.can_operate:
            ttk.Button(actions, text="Editar seleccionado", command=self._edit_selected_product).pack(side="right", padx=(8, 0))
            ttk.Button(actions, text="Registrar producto", command=self._open_product_dialog).pack(side="right")

    def _build_movements_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Movimientos")
        lookup = ttk.LabelFrame(tab, text="Producto", padding=10)
        lookup.pack(fill="x", pady=(0, 10))
        self.movement_barcode = ttk.Entry(lookup, width=28)
        self.movement_barcode.pack(side="left", padx=(0, 8))
        ttk.Button(lookup, text="Buscar / escanear", command=self._find_movement_product).pack(side="left")
        self.movement_barcode.bind("<Return>", lambda _event: self._find_movement_product())
        self.product_summary = ttk.Label(lookup, text="Escanea un producto para iniciar.")
        self.product_summary.pack(side="left", padx=16)

        form = ttk.LabelFrame(tab, text="Registrar movimiento", padding=10)
        form.pack(fill="x", pady=(0, 10))
        ttk.Label(form, text="Tipo").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.movement_type = ttk.Combobox(form, state="readonly", values=("entrada", "salida"), width=12)
        self.movement_type.set("entrada")
        self.movement_type.grid(row=0, column=1, sticky="w", padx=(0, 20))
        ttk.Label(form, text="Cantidad").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.movement_quantity = ttk.Entry(form, width=12)
        self.movement_quantity.grid(row=0, column=3, sticky="w", padx=(0, 20))
        self.register_movement_button = ttk.Button(
            form, text="Registrar movimiento", command=self._register_movement,
            state="normal" if self.can_operate else "disabled",
        )
        self.register_movement_button.grid(row=0, column=4, sticky="w")
        form.columnconfigure(5, weight=1)

        ttk.Label(tab, text="Historial reciente", font=("Arial", 11, "bold")).pack(anchor="w", pady=(4, 6))
        self.history_tree = self._make_tree(
            tab,
            [
                ("date", "Fecha y hora", 155), ("product", "Producto", 230),
                ("type", "Tipo", 90), ("quantity", "Cantidad", 90),
                ("responsible", "Responsable", 230),
            ],
        )
        self.refresh_history()

    def _build_reports_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Reportes")
        controls = ttk.Frame(tab)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text="Reporte").pack(side="left", padx=(0, 8))
        self.report_choice = ttk.Combobox(
            controls,
            state="readonly",
            values=("Consumo por producto", "Reactivos proximos a caducar"),
            width=34,
        )
        self.report_choice.current(0)
        self.report_choice.pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Generar", command=self.refresh_report).pack(side="left")
        ttk.Label(
            tab,
            text="Consultas SQL con JOIN, subconsultas, agregaciones y agrupaciones.",
        ).pack(anchor="w", pady=(0, 8))
        self.report_tree = self._make_tree(tab, [("result", "Resultados", 900)])
        self.report_choice.bind("<<ComboboxSelected>>", lambda _event: self.refresh_report())
        self.refresh_report()

    def _build_users_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="Usuarios")
        ttk.Label(
            tab, text="Solo administracion puede crear cuentas o cambiar su estado."
        ).pack(anchor="w", pady=(0, 8))
        self.users_tree = self._make_tree(
            tab,
            [
                ("name", "Nombre", 260), ("username", "Usuario", 180),
                ("role", "Rol", 120), ("state", "Estado", 120),
            ],
        )
        actions = ttk.Frame(tab, padding=(0, 10, 0, 0))
        actions.pack(fill="x")
        ttk.Button(actions, text="Crear usuario", command=self._open_user_dialog).pack(side="left")
        ttk.Button(actions, text="Activar / desactivar seleccionado", command=self._toggle_user).pack(side="right")

    def _show_error(self, title: str, error: Exception) -> None:
        messagebox.showerror(title, str(error), parent=self)

    def refresh_products(self) -> None:
        try:
            rows = self.database.list_products()
            self.inventory_tree.delete(*self.inventory_tree.get_children())
            for row in rows:
                expiry = row["fecha_caducidad"].isoformat() if row["fecha_caducidad"] else ""
                days = "" if row["dias_para_caducar"] is None else row["dias_para_caducar"]
                self.inventory_tree.insert(
                    "", "end", iid=str(row["id_producto"]),
                    values=(row["codigo_barras"], row["nombre"], row["tipo"],
                            row["stock"], expiry, days, row["estado_caducidad"]),
                )
        except Exception as error:
            self._show_error("No se pudo consultar el inventario", error)

    def _scan_inventory(self) -> None:
        barcode = self.inventory_barcode.get().strip()
        if not barcode:
            return
        try:
            product = self.database.find_product(barcode)
            if not product:
                messagebox.showinfo("Sin resultados", "No existe un producto con ese codigo.", parent=self)
                self.inventory_barcode.select_range(0, tk.END)
                return
            self.refresh_products()
            item_id = str(product["id_producto"])
            self.inventory_tree.selection_set(item_id)
            self.inventory_tree.focus(item_id)
            self.inventory_tree.see(item_id)
        except Exception as error:
            self._show_error("No se pudo buscar el producto", error)
        self.inventory_barcode.focus_set()
        self.inventory_barcode.select_range(0, tk.END)

    def _edit_selected_product(self) -> None:
        selection = self.inventory_tree.selection()
        if not selection:
            messagebox.showinfo("Selecciona un producto", "Elige un producto de la lista.", parent=self)
            return
        self._open_product_dialog(int(selection[0]))

    def _open_product_dialog(self, product_id: int | None = None) -> None:
        product = None
        if product_id is not None:
            item = self.inventory_tree.item(str(product_id), "values")
            try:
                product = self.database.find_product(item[0])
            except Exception as error:
                self._show_error("No se pudo cargar el producto", error)
                return
            if not product:
                messagebox.showerror("Producto no encontrado", "Actualiza el inventario e intenta de nuevo.", parent=self)
                return
        dialog = tk.Toplevel(self)
        dialog.title("Editar producto" if product else "Registrar producto")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)
        fields: dict[str, tk.Widget] = {}
        definitions = (
            ("Codigo de barras", "barcode"), ("Nombre", "name"),
            ("Tipo", "type"), ("Existencias" if product else "Stock inicial", "stock"),
            ("Caducidad (AAAA-MM-DD, opcional)", "expiry"), ("Descripcion", "description"),
        )
        for row_index, (label, key) in enumerate(definitions):
            ttk.Label(body, text=label).grid(row=row_index, column=0, sticky="w", pady=5)
            if key == "type":
                widget = ttk.Combobox(body, state="readonly", values=("reactivo", "material"), width=31)
                widget.set("reactivo")
            else:
                widget = ttk.Entry(body, width=34)
                if key == "stock":
                    widget.insert(0, str(product["stock"]) if product else "0")
                    if product:
                        widget.configure(state="disabled")
            widget.grid(row=row_index, column=1, padx=(12, 0), pady=5)
            fields[key] = widget

        if product:
            for key, value in (
                ("barcode", product["codigo_barras"]), ("name", product["nombre"]),
                ("expiry", product["fecha_caducidad"].isoformat() if product["fecha_caducidad"] else ""),
                ("description", product["descripcion"] or ""),
            ):
                fields[key].insert(0, value)  # type: ignore[attr-defined]
            fields["type"].set(product["tipo"])  # type: ignore[attr-defined]

        def save() -> None:
            barcode = fields["barcode"].get().strip()  # type: ignore[attr-defined]
            name = fields["name"].get().strip()  # type: ignore[attr-defined]
            kind = fields["type"].get()  # type: ignore[attr-defined]
            description = fields["description"].get().strip() or None  # type: ignore[attr-defined]
            expiration_text = fields["expiry"].get().strip()  # type: ignore[attr-defined]
            try:
                stock = int(fields["stock"].get()) if not product else int(product["stock"])  # type: ignore[attr-defined]
                if not barcode or not name or stock < 0:
                    raise ValueError("Codigo y nombre son obligatorios; el stock debe ser valido.")
                expiration = date.fromisoformat(expiration_text).isoformat() if expiration_text else None
                if product:
                    self.database.update_product(
                        int(self.user["id_usuario"]), product_id, barcode, name,
                        kind, expiration, description,
                    )
                else:
                    product_id = self.database.register_product(
                        int(self.user["id_usuario"]), barcode, name, kind, stock, expiration, description
                    )
            except ValueError as error:
                messagebox.showwarning("Revisa los datos", str(error), parent=dialog)
                return
            except Exception as error:
                self._show_error("No se pudo guardar el producto", error)
                return
            dialog.destroy()
            self.refresh_products()
            messagebox.showinfo(
                "Producto actualizado" if product else "Producto registrado",
                f"Se guardaron los datos del producto {product_id}.", parent=self,
            )

        ttk.Button(body, text="Guardar", command=save).grid(row=len(definitions), column=1, sticky="e", pady=(12, 0))

    def _find_movement_product(self) -> None:
        barcode = self.movement_barcode.get().strip()
        if not barcode:
            return
        try:
            self.current_product = self.database.find_product(barcode)
            if not self.current_product:
                self.product_summary.configure(text="No se encontro el producto.")
                messagebox.showinfo("Sin resultados", "No existe un producto con ese codigo.", parent=self)
                return
            product = self.current_product
            self.product_summary.configure(
                text=f"{product['nombre']} ({product['tipo']}) | Existencias: {product['stock']}"
            )
            self.movement_quantity.focus_set()
        except Exception as error:
            self._show_error("No se pudo buscar el producto", error)

    def _register_movement(self) -> None:
        if not self.can_operate:
            messagebox.showwarning("Sin permiso", "Tu rol es de solo consulta.", parent=self)
            return
        if not self.current_product:
            messagebox.showwarning("Falta producto", "Escanea o busca un producto primero.", parent=self)
            return
        try:
            quantity = int(self.movement_quantity.get())
            if quantity <= 0:
                raise ValueError("La cantidad debe ser mayor que cero.")
            movement_id, stock = self.database.register_movement(
                int(self.current_product["id_producto"]),
                int(self.user["id_usuario"]),
                self.movement_type.get(),
                quantity,
            )
            self.product_summary.configure(
                text=f"{self.current_product['nombre']} | Existencias actuales: {stock}"
            )
            self.movement_quantity.delete(0, tk.END)
            self.current_product = self.database.find_product(self.movement_barcode.get().strip())
            self.refresh_products()
            self.refresh_history()
            messagebox.showinfo(
                "Movimiento registrado",
                f"Movimiento {movement_id} guardado. Existencias: {stock}.",
                parent=self,
            )
        except ValueError as error:
            messagebox.showwarning("Cantidad invalida", str(error), parent=self)
        except Exception as error:
            self._show_error("No se pudo registrar el movimiento", error)

    def refresh_history(self) -> None:
        if not hasattr(self, "history_tree"):
            return
        try:
            rows = self.database.movement_history()
            self.history_tree.delete(*self.history_tree.get_children())
            for row in rows:
                self.history_tree.insert(
                    "", "end",
                    values=(row["fecha_hora"].strftime("%Y-%m-%d %H:%M"), row["producto"],
                            row["tipo_movimiento"], row["cantidad"], row["responsable"]),
                )
        except Exception as error:
            self._show_error("No se pudo consultar el historial", error)

    def refresh_report(self) -> None:
        if not hasattr(self, "report_tree"):
            return
        try:
            if self.report_choice.get() == "Consumo por producto":
                rows = self.database.report_consumption()
                values = [
                    f"{r['codigo_barras']} | {r['nombre']} | {r['tipo']} | "
                    f"Salidas: {r['total_salidas']} | Movimientos: {r['movimientos']} | "
                    f"Responsables: {r['responsables']}"
                    for r in rows
                ]
            else:
                rows = self.database.report_expiration()
                values = [
                    f"{r['codigo_barras']} | {r['nombre']} | Caduca: {r['fecha_caducidad']} | "
                    f"Dias restantes: {r['dias_restantes']} | Salidas: {r['salidas_registradas']} "
                    f"({r['numero_de_salidas']} movimientos)"
                    for r in rows
                ]
            self.report_tree.delete(*self.report_tree.get_children())
            for index, line in enumerate(values):
                self.report_tree.insert("", "end", iid=f"report-{index}", values=(line,))
            if not values:
                self.report_tree.insert("", "end", iid="report-empty", values=("No hay resultados para este reporte.",))
        except Exception as error:
            self._show_error("No se pudo generar el reporte", error)

    def refresh_users(self) -> None:
        if not hasattr(self, "users_tree"):
            return
        try:
            rows = self.database.list_users()
            self.users_tree.delete(*self.users_tree.get_children())
            for row in rows:
                self.users_tree.insert(
                    "", "end", iid=str(row["id_usuario"]),
                    values=(row["nombre_completo"], row["nombre_usuario"], row["rol"], row["estado"]),
                )
        except Exception as error:
            self._show_error("No se pudieron consultar los usuarios", error)

    def _open_user_dialog(self) -> None:
        if self.user["rol"] != "admin":
            return
        dialog = tk.Toplevel(self)
        dialog.title("Crear usuario")
        dialog.transient(self)
        dialog.grab_set()
        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)
        labels = ("Nombre completo", "Nombre de usuario", "Contrasena", "Rol")
        entries: list[tk.Widget] = []
        for index, label in enumerate(labels):
            ttk.Label(body, text=label).grid(row=index, column=0, sticky="w", pady=5)
            if label == "Rol":
                widget = ttk.Combobox(body, state="readonly", values=("admin", "operador", "consulta"), width=28)
                widget.set("operador")
            else:
                widget = ttk.Entry(body, width=31, show="*" if label == "Contrasena" else "")
            widget.grid(row=index, column=1, padx=(12, 0), pady=5)
            entries.append(widget)

        def save() -> None:
            full_name = entries[0].get().strip()  # type: ignore[attr-defined]
            username = entries[1].get().strip()  # type: ignore[attr-defined]
            password = entries[2].get()  # type: ignore[attr-defined]
            role = entries[3].get()  # type: ignore[attr-defined]
            if not full_name or not username or len(password) < 8:
                messagebox.showwarning(
                    "Revisa los datos", "Completa nombre y usuario; la contrasena debe tener al menos 8 caracteres.",
                    parent=dialog,
                )
                return
            try:
                new_id = self.database.create_user(full_name, username, hash_password(password), role)
            except Exception as error:
                self._show_error("No se pudo crear el usuario", error)
                return
            dialog.destroy()
            self.refresh_users()
            messagebox.showinfo("Usuario creado", f"Se creo la cuenta {username} (ID {new_id}).", parent=self)

        ttk.Button(body, text="Guardar", command=save).grid(row=4, column=1, sticky="e", pady=(12, 0))

    def _toggle_user(self) -> None:
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showinfo("Selecciona un usuario", "Elige una cuenta de la lista.", parent=self)
            return
        user_id = int(selection[0])
        values = self.users_tree.item(selection[0], "values")
        status = "inactivo" if values[3] == "activo" else "activo"
        if user_id == int(self.user["id_usuario"]):
            messagebox.showwarning("Cuenta actual", "No puedes desactivar tu propia cuenta.", parent=self)
            return
        try:
            self.database.set_user_status(user_id, status)
            self.refresh_users()
        except Exception as error:
            self._show_error("No se pudo actualizar la cuenta", error)
