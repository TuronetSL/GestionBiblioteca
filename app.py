from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from biblioteca.db import get_connection, init_db

DB_PATH = Path("data/biblioteca.sqlite")


class BibliotecaService:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def _conn(self):
        return get_connection(self.db_path)

    def stats(self) -> dict[str, int]:
        with self._conn() as conn:
            return {
                "libros": conn.execute("SELECT COUNT(*) c FROM libros").fetchone()["c"],
                "socios": conn.execute("SELECT COUNT(*) c FROM socios").fetchone()["c"],
                "prestamos": conn.execute("SELECT COUNT(*) c FROM prestamos WHERE estado != 'devuelto'").fetchone()["c"],
            }

    def listar_atrasados(self):
        with self._conn() as conn:
            conn.execute("UPDATE prestamos SET estado='atrasado' WHERE estado='activo' AND date(fecha_limite) < date('now')")
            conn.commit()
            return conn.execute(
                """SELECT p.id, l.titulo, s.nombre, p.fecha_limite
                FROM prestamos p
                JOIN libros l ON l.id = p.libro_id
                JOIN socios s ON s.id = p.socio_id
                WHERE p.estado='atrasado'
                ORDER BY p.fecha_limite ASC"""
            ).fetchall()

    def crear_libro(self, titulo: str, autor: str, categoria: str, isbn: str, total_copias: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO libros (titulo,autor,categoria,isbn,total_copias,copias_disponibles) VALUES (?,?,?,?,?,?)",
                (titulo, autor, categoria, isbn, total_copias, total_copias),
            )
            conn.commit()

    def listar_libros(self):
        with self._conn() as conn:
            return conn.execute("SELECT * FROM libros ORDER BY creado_en DESC").fetchall()

    def crear_socio(self, nombre: str, email: str, telefono: str, direccion: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO socios (nombre,email,telefono,direccion) VALUES (?,?,?,?)",
                (nombre, email, telefono, direccion),
            )
            conn.commit()

    def listar_socios(self):
        with self._conn() as conn:
            return conn.execute("SELECT * FROM socios ORDER BY creado_en DESC").fetchall()

    def crear_prestamo(self, libro_id: int, socio_id: int) -> bool:
        hoy = date.today()
        limite = hoy + timedelta(days=14)
        with self._conn() as conn:
            libro = conn.execute("SELECT copias_disponibles FROM libros WHERE id=?", (libro_id,)).fetchone()
            if not libro or libro["copias_disponibles"] <= 0:
                return False
            conn.execute(
                "INSERT INTO prestamos (libro_id,socio_id,fecha_prestamo,fecha_limite,estado) VALUES (?,?,?,?, 'activo')",
                (libro_id, socio_id, hoy.isoformat(), limite.isoformat()),
            )
            conn.execute("UPDATE libros SET copias_disponibles=copias_disponibles-1 WHERE id=?", (libro_id,))
            conn.commit()
        return True

    def devolver_prestamo(self, prestamo_id: int) -> None:
        with self._conn() as conn:
            prestamo = conn.execute("SELECT * FROM prestamos WHERE id=?", (prestamo_id,)).fetchone()
            if not prestamo or prestamo["estado"] == "devuelto":
                return
            conn.execute("UPDATE prestamos SET estado='devuelto', fecha_devolucion=date('now') WHERE id=?", (prestamo_id,))
            conn.execute("UPDATE libros SET copias_disponibles=copias_disponibles+1 WHERE id=?", (prestamo["libro_id"],))
            conn.commit()

    def listar_prestamos(self):
        with self._conn() as conn:
            conn.execute("UPDATE prestamos SET estado='atrasado' WHERE estado='activo' AND date(fecha_limite) < date('now')")
            conn.commit()
            return conn.execute(
                """SELECT p.*, l.titulo, s.nombre FROM prestamos p
                JOIN libros l ON l.id=p.libro_id
                JOIN socios s ON s.id=p.socio_id
                ORDER BY p.fecha_prestamo DESC"""
            ).fetchall()

    def libros_disponibles(self):
        with self._conn() as conn:
            return conn.execute("SELECT id,titulo,copias_disponibles FROM libros ORDER BY titulo").fetchall()

    def socios_disponibles(self):
        with self._conn() as conn:
            return conn.execute("SELECT id,nombre FROM socios ORDER BY nombre").fetchall()


class BibliotecaDesktopApp(tk.Tk):
    def __init__(self, service: BibliotecaService) -> None:
        super().__init__()
        self.service = service
        self.title("Biblioteca de Mi Pueblo")
        self.geometry("1050x700")
        self.minsize(900, 620)

        self.notice_var = tk.StringVar()

        title = ttk.Label(self, text="📚 Biblioteca de Mi Pueblo", font=("Segoe UI", 18, "bold"))
        title.pack(pady=(12, 2))
        ttk.Label(self, text="Aplicación de gestión local", foreground="#4b5563").pack()

        notice = ttk.Label(self, textvariable=self.notice_var, foreground="#166534")
        notice.pack(pady=6)

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=8)

        self.tab_inicio = ttk.Frame(self.tabs)
        self.tab_libros = ttk.Frame(self.tabs)
        self.tab_socios = ttk.Frame(self.tabs)
        self.tab_prestamos = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_inicio, text="Inicio")
        self.tabs.add(self.tab_libros, text="Libros")
        self.tabs.add(self.tab_socios, text="Socios")
        self.tabs.add(self.tab_prestamos, text="Préstamos")

        self._build_inicio()
        self._build_libros()
        self._build_socios()
        self._build_prestamos()
        self.refresh_all()

    def set_notice(self, text: str) -> None:
        self.notice_var.set(text)
        self.after(3500, lambda: self.notice_var.set(""))

    def refresh_all(self):
        self.refresh_inicio()
        self.refresh_libros()
        self.refresh_socios()
        self.refresh_prestamos()

    def _build_inicio(self):
        stats_frame = ttk.Frame(self.tab_inicio)
        stats_frame.pack(fill="x", padx=16, pady=12)
        self.stats_labels = {}
        for i, key in enumerate(["libros", "socios", "prestamos"]):
            card = ttk.LabelFrame(stats_frame, text=key.capitalize())
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)
            label = ttk.Label(card, text="0", font=("Segoe UI", 22, "bold"))
            label.pack(padx=24, pady=18)
            self.stats_labels[key] = label

        ttk.Label(self.tab_inicio, text="Préstamos atrasados", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16)
        self.atrasados_tree = ttk.Treeview(self.tab_inicio, columns=("id", "libro", "socio", "limite"), show="headings", height=16)
        for col, text, width in [("id", "ID", 70), ("libro", "Libro", 300), ("socio", "Socio", 250), ("limite", "Fecha límite", 120)]:
            self.atrasados_tree.heading(col, text=text)
            self.atrasados_tree.column(col, width=width)
        self.atrasados_tree.pack(fill="both", expand=True, padx=16, pady=10)

    def _build_libros(self):
        form = ttk.LabelFrame(self.tab_libros, text="Nuevo libro")
        form.pack(fill="x", padx=16, pady=10)
        self.libro_vars = {k: tk.StringVar() for k in ["titulo", "autor", "categoria", "isbn", "copias"]}
        fields = [("Título", "titulo"), ("Autor", "autor"), ("Categoría", "categoria"), ("ISBN", "isbn"), ("Copias", "copias")]
        for i, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, padx=6, pady=6, sticky="w")
            ttk.Entry(form, textvariable=self.libro_vars[key], width=18).grid(row=1, column=i, padx=6, pady=6)
        ttk.Button(form, text="Guardar", command=self.on_add_libro).grid(row=1, column=len(fields), padx=8)

        self.libros_tree = ttk.Treeview(self.tab_libros, columns=("titulo", "autor", "categoria", "isbn", "disp"), show="headings", height=18)
        for col, text, w in [("titulo", "Título", 260), ("autor", "Autor", 220), ("categoria", "Categoría", 150), ("isbn", "ISBN", 140), ("disp", "Disponibles", 120)]:
            self.libros_tree.heading(col, text=text)
            self.libros_tree.column(col, width=w)
        self.libros_tree.pack(fill="both", expand=True, padx=16, pady=10)

    def _build_socios(self):
        form = ttk.LabelFrame(self.tab_socios, text="Nuevo socio")
        form.pack(fill="x", padx=16, pady=10)
        self.socio_vars = {k: tk.StringVar() for k in ["nombre", "email", "telefono", "direccion"]}
        fields = [("Nombre", "nombre"), ("Email", "email"), ("Teléfono", "telefono"), ("Dirección", "direccion")]
        for i, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, padx=6, pady=6, sticky="w")
            ttk.Entry(form, textvariable=self.socio_vars[key], width=24).grid(row=1, column=i, padx=6, pady=6)
        ttk.Button(form, text="Guardar", command=self.on_add_socio).grid(row=1, column=len(fields), padx=8)

        self.socios_tree = ttk.Treeview(self.tab_socios, columns=("nombre", "email", "telefono", "direccion"), show="headings", height=18)
        for col, text, w in [("nombre", "Nombre", 220), ("email", "Email", 250), ("telefono", "Teléfono", 140), ("direccion", "Dirección", 260)]:
            self.socios_tree.heading(col, text=text)
            self.socios_tree.column(col, width=w)
        self.socios_tree.pack(fill="both", expand=True, padx=16, pady=10)

    def _build_prestamos(self):
        form = ttk.LabelFrame(self.tab_prestamos, text="Nuevo préstamo")
        form.pack(fill="x", padx=16, pady=10)
        self.libro_combo = ttk.Combobox(form, state="readonly", width=50)
        self.socio_combo = ttk.Combobox(form, state="readonly", width=40)
        ttk.Label(form, text="Libro").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Label(form, text="Socio").grid(row=0, column=1, padx=6, pady=6, sticky="w")
        self.libro_combo.grid(row=1, column=0, padx=6, pady=6)
        self.socio_combo.grid(row=1, column=1, padx=6, pady=6)
        ttk.Button(form, text="Crear préstamo", command=self.on_add_prestamo).grid(row=1, column=2, padx=8)

        self.prestamos_tree = ttk.Treeview(
            self.tab_prestamos,
            columns=("id", "libro", "socio", "inicio", "limite", "estado"),
            show="headings",
            height=18,
        )
        for col, text, w in [
            ("id", "ID", 60),
            ("libro", "Libro", 240),
            ("socio", "Socio", 220),
            ("inicio", "Inicio", 110),
            ("limite", "Límite", 110),
            ("estado", "Estado", 100),
        ]:
            self.prestamos_tree.heading(col, text=text)
            self.prestamos_tree.column(col, width=w)
        self.prestamos_tree.pack(fill="both", expand=True, padx=16, pady=8)
        ttk.Button(self.tab_prestamos, text="Marcar como devuelto", command=self.on_devolver).pack(anchor="e", padx=16, pady=(0, 12))

    def refresh_inicio(self):
        stats = self.service.stats()
        for k, lbl in self.stats_labels.items():
            lbl.config(text=str(stats[k]))
        self._populate_tree(
            self.atrasados_tree,
            [(r["id"], r["titulo"], r["nombre"], r["fecha_limite"]) for r in self.service.listar_atrasados()],
        )

    def refresh_libros(self):
        self._populate_tree(
            self.libros_tree,
            [
                (r["titulo"], r["autor"], r["categoria"], r["isbn"], f"{r['copias_disponibles']}/{r['total_copias']}")
                for r in self.service.listar_libros()
            ],
        )

    def refresh_socios(self):
        self._populate_tree(
            self.socios_tree,
            [(r["nombre"], r["email"], r["telefono"] or "", r["direccion"] or "") for r in self.service.listar_socios()],
        )

    def refresh_prestamos(self):
        libros = self.service.libros_disponibles()
        socios = self.service.socios_disponibles()
        self.libro_map = {f"{l['titulo']} ({l['copias_disponibles']} disp.)": l["id"] for l in libros}
        self.socio_map = {s["nombre"]: s["id"] for s in socios}
        self.libro_combo["values"] = list(self.libro_map.keys())
        self.socio_combo["values"] = list(self.socio_map.keys())

        self._populate_tree(
            self.prestamos_tree,
            [(p["id"], p["titulo"], p["nombre"], p["fecha_prestamo"], p["fecha_limite"], p["estado"]) for p in self.service.listar_prestamos()],
        )

    @staticmethod
    def _populate_tree(tree: ttk.Treeview, rows: list[tuple]):
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", "end", values=row)

    def on_add_libro(self):
        try:
            self.service.crear_libro(
                self.libro_vars["titulo"].get().strip(),
                self.libro_vars["autor"].get().strip(),
                self.libro_vars["categoria"].get().strip(),
                self.libro_vars["isbn"].get().strip(),
                int(self.libro_vars["copias"].get().strip()),
            )
            for var in self.libro_vars.values():
                var.set("")
            self.set_notice("Libro añadido correctamente")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo crear el libro: {exc}")

    def on_add_socio(self):
        try:
            self.service.crear_socio(
                self.socio_vars["nombre"].get().strip(),
                self.socio_vars["email"].get().strip(),
                self.socio_vars["telefono"].get().strip(),
                self.socio_vars["direccion"].get().strip(),
            )
            for var in self.socio_vars.values():
                var.set("")
            self.set_notice("Socio registrado correctamente")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo registrar el socio: {exc}")

    def on_add_prestamo(self):
        libro = self.libro_combo.get()
        socio = self.socio_combo.get()
        if not libro or not socio:
            messagebox.showwarning("Aviso", "Selecciona libro y socio")
            return
        ok = self.service.crear_prestamo(self.libro_map[libro], self.socio_map[socio])
        if not ok:
            messagebox.showwarning("Sin disponibilidad", "No hay copias disponibles de ese libro")
            return
        self.set_notice("Préstamo creado correctamente")
        self.refresh_all()

    def on_devolver(self):
        selected = self.prestamos_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona un préstamo")
            return
        prestamo_id = int(self.prestamos_tree.item(selected[0], "values")[0])
        self.service.devolver_prestamo(prestamo_id)
        self.set_notice("Préstamo marcado como devuelto")
        self.refresh_all()


def run() -> None:
    service = BibliotecaService(DB_PATH)
    app = BibliotecaDesktopApp(service)
    app.mainloop()


if __name__ == "__main__":
    run()
