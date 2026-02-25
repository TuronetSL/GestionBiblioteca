from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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

    def resumen_prestamos_estado(self) -> dict[str, int]:
        with self._conn() as conn:
            self._actualizar_atrasados(conn)
            rows = conn.execute("SELECT estado, COUNT(*) c FROM prestamos GROUP BY estado").fetchall()
            base = {"activo": 0, "devuelto": 0, "atrasado": 0}
            for row in rows:
                base[row["estado"]] = row["c"]
            return base

    def top_libros_prestados(self, limit: int = 5):
        with self._conn() as conn:
            return conn.execute(
                """
                SELECT l.titulo, COUNT(*) AS total
                FROM prestamos p
                JOIN libros l ON l.id = p.libro_id
                GROUP BY p.libro_id
                ORDER BY total DESC, l.titulo ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def listar_atrasados(self):
        with self._conn() as conn:
            self._actualizar_atrasados(conn)
            return conn.execute(
                """SELECT p.id, l.titulo, s.nombre, p.fecha_limite
                FROM prestamos p
                JOIN libros l ON l.id = p.libro_id
                JOIN socios s ON s.id = p.socio_id
                WHERE p.estado='atrasado'
                ORDER BY p.fecha_limite ASC"""
            ).fetchall()

    @staticmethod
    def _actualizar_atrasados(conn):
        conn.execute("UPDATE prestamos SET estado='atrasado' WHERE estado='activo' AND date(fecha_limite) < date('now')")
        conn.commit()

    def crear_libro(self, titulo: str, autor: str, categoria: str, isbn: str, total_copias: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO libros (titulo,autor,categoria,isbn,total_copias,copias_disponibles) VALUES (?,?,?,?,?,?)",
                (titulo, autor, categoria, isbn, total_copias, total_copias),
            )
            conn.commit()

    def borrar_libro(self, libro_id: int) -> None:
        with self._conn() as conn:
            activo = conn.execute(
                "SELECT COUNT(*) c FROM prestamos WHERE libro_id = ? AND estado IN ('activo', 'atrasado')",
                (libro_id,),
            ).fetchone()["c"]
            if activo > 0:
                raise ValueError("No puedes borrar un libro con préstamos activos o atrasados")
            conn.execute("DELETE FROM prestamos WHERE libro_id = ?", (libro_id,))
            conn.execute("DELETE FROM libros WHERE id = ?", (libro_id,))
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

    def borrar_socio(self, socio_id: int) -> None:
        with self._conn() as conn:
            activo = conn.execute(
                "SELECT COUNT(*) c FROM prestamos WHERE socio_id = ? AND estado IN ('activo', 'atrasado')",
                (socio_id,),
            ).fetchone()["c"]
            if activo > 0:
                raise ValueError("No puedes borrar un socio con préstamos activos o atrasados")
            conn.execute("DELETE FROM prestamos WHERE socio_id = ?", (socio_id,))
            conn.execute("DELETE FROM socios WHERE id = ?", (socio_id,))
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

    def borrar_prestamo(self, prestamo_id: int) -> None:
        with self._conn() as conn:
            prestamo = conn.execute("SELECT * FROM prestamos WHERE id=?", (prestamo_id,)).fetchone()
            if not prestamo:
                return
            if prestamo["estado"] in ("activo", "atrasado"):
                conn.execute("UPDATE libros SET copias_disponibles=copias_disponibles+1 WHERE id=?", (prestamo["libro_id"],))
            conn.execute("DELETE FROM prestamos WHERE id=?", (prestamo_id,))
            conn.commit()

    def listar_prestamos(self):
        with self._conn() as conn:
            self._actualizar_atrasados(conn)
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

    def exportar_prestamos_csv(self, ruta: Path) -> None:
        rows = self.listar_prestamos()
        with ruta.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "libro", "socio", "fecha_prestamo", "fecha_limite", "estado"])
            for row in rows:
                writer.writerow([row["id"], row["titulo"], row["nombre"], row["fecha_prestamo"], row["fecha_limite"], row["estado"]])


class BibliotecaDesktopApp(tk.Tk):
    def __init__(self, service: BibliotecaService) -> None:
        super().__init__()
        self.service = service
        self._setup_style()

        self.title("Biblioteca de Mi Pueblo")
        self.geometry("1200x780")
        self.minsize(1000, 700)
        self.configure(bg="#ecf2ff")

        self.notice_var = tk.StringVar()
        self.search_libros_var = tk.StringVar()
        self.search_socios_var = tk.StringVar()
        self.search_prestamos_var = tk.StringVar()

        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x", padx=14, pady=(12, 6))
        ttk.Label(header, text="📚 Biblioteca de Mi Pueblo", style="Title.TLabel").pack(anchor="w", padx=16, pady=(14, 2))
        ttk.Label(header, text="Gestión local · moderna · rápida", style="Subtitle.TLabel").pack(anchor="w", padx=16, pady=(0, 14))

        self.notice_label = ttk.Label(self, textvariable=self.notice_var, style="Notice.TLabel")
        self.notice_label.pack(fill="x", padx=16, pady=(0, 8))

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.tab_inicio = ttk.Frame(self.tabs, style="Card.TFrame")
        self.tab_libros = ttk.Frame(self.tabs, style="Card.TFrame")
        self.tab_socios = ttk.Frame(self.tabs, style="Card.TFrame")
        self.tab_prestamos = ttk.Frame(self.tabs, style="Card.TFrame")

        self.tabs.add(self.tab_inicio, text="📊 Inicio")
        self.tabs.add(self.tab_libros, text="📚 Libros")
        self.tabs.add(self.tab_socios, text="👥 Socios")
        self.tabs.add(self.tab_prestamos, text="🔁 Préstamos")

        self._build_inicio()
        self._build_libros()
        self._build_socios()
        self._build_prestamos()
        self.refresh_all()

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Header.TFrame", background="#1d4ed8")
        style.configure("Card.TFrame", background="#f6f9ff")
        style.configure("Title.TLabel", background="#1d4ed8", foreground="#ffffff", font=("Segoe UI", 21, "bold"))
        style.configure("Subtitle.TLabel", background="#1d4ed8", foreground="#dbeafe", font=("Segoe UI", 11))
        style.configure("Notice.TLabel", background="#ecf2ff", foreground="#065f46", font=("Segoe UI", 10, "bold"))

        style.configure("TLabelframe", background="#f6f9ff", bordercolor="#c6d4f6")
        style.configure("TLabelframe.Label", background="#f6f9ff", foreground="#1e3a8a", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10), bordercolor="#c6d4f6")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e5edff", foreground="#1e3a8a")
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#0f172a")])

        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(10, 7), foreground="#ffffff", background="#2563eb")
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=(10, 7), foreground="#ffffff", background="#dc2626")
        style.map("Danger.TButton", background=[("active", "#b91c1c")])

    def set_notice(self, text: str, ok: bool = True) -> None:
        icon = "✅" if ok else "⚠️"
        color = "#065f46" if ok else "#92400e"
        self.notice_label.configure(foreground=color)
        self.notice_var.set(f"{icon} {text}")
        self.after(3500, lambda: self.notice_var.set(""))

    def _build_inicio(self):
        stats_frame = ttk.Frame(self.tab_inicio, style="Card.TFrame")
        stats_frame.pack(fill="x", padx=16, pady=12)
        self.stats_labels = {}
        for i, (key, title) in enumerate([("libros", "Libros"), ("socios", "Socios"), ("prestamos", "Préstamos activos")]):
            card = ttk.LabelFrame(stats_frame, text=title)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)
            label = ttk.Label(card, text="0", font=("Segoe UI", 24, "bold"), foreground="#1d4ed8")
            label.pack(padx=24, pady=18)
            self.stats_labels[key] = label

        analytics = ttk.Frame(self.tab_inicio, style="Card.TFrame")
        analytics.pack(fill="x", padx=16, pady=8)
        self.estado_label = ttk.Label(analytics, text="", background="#f6f9ff", foreground="#1e3a8a", font=("Segoe UI", 10, "bold"))
        self.estado_label.pack(anchor="w")

        ttk.Label(analytics, text="Top libros prestados", background="#f6f9ff", foreground="#1e3a8a", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 4))
        self.top_canvas = tk.Canvas(analytics, height=130, bg="#f6f9ff", highlightthickness=0)
        self.top_canvas.pack(fill="x")

        ttk.Label(self.tab_inicio, text="Préstamos atrasados", font=("Segoe UI", 12, "bold"), background="#f6f9ff", foreground="#1e3a8a").pack(anchor="w", padx=16, pady=(10, 0))
        self.atrasados_tree = ttk.Treeview(self.tab_inicio, columns=("id", "libro", "socio", "limite"), show="headings", height=13)
        for col, text, width in [("id", "ID", 70), ("libro", "Libro", 320), ("socio", "Socio", 250), ("limite", "Fecha límite", 120)]:
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
        ttk.Button(form, text="Guardar libro", style="Accent.TButton", command=self.on_add_libro).grid(row=1, column=len(fields), padx=8)

        search = ttk.Frame(self.tab_libros, style="Card.TFrame")
        search.pack(fill="x", padx=16)
        ttk.Label(search, text="Buscar libro:", background="#f6f9ff").pack(side="left")
        ttk.Entry(search, textvariable=self.search_libros_var, width=30).pack(side="left", padx=8)
        self.search_libros_var.trace_add("write", lambda *_: self.refresh_libros())

        self.libros_tree = ttk.Treeview(self.tab_libros, columns=("id", "titulo", "autor", "categoria", "isbn", "disp"), show="headings", height=15)
        for col, text, w in [("id", "ID", 70), ("titulo", "Título", 250), ("autor", "Autor", 190), ("categoria", "Categoría", 140), ("isbn", "ISBN", 130), ("disp", "Disponibles", 100)]:
            self.libros_tree.heading(col, text=text)
            self.libros_tree.column(col, width=w)
        self.libros_tree.pack(fill="both", expand=True, padx=16, pady=10)
        ttk.Button(self.tab_libros, text="🗑 Borrar libro seleccionado", style="Danger.TButton", command=self.on_delete_libro).pack(anchor="e", padx=16, pady=(0, 12))

    def _build_socios(self):
        form = ttk.LabelFrame(self.tab_socios, text="Nuevo socio")
        form.pack(fill="x", padx=16, pady=10)
        self.socio_vars = {k: tk.StringVar() for k in ["nombre", "email", "telefono", "direccion"]}
        fields = [("Nombre", "nombre"), ("Email", "email"), ("Teléfono", "telefono"), ("Dirección", "direccion")]
        for i, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, padx=6, pady=6, sticky="w")
            ttk.Entry(form, textvariable=self.socio_vars[key], width=24).grid(row=1, column=i, padx=6, pady=6)
        ttk.Button(form, text="Guardar socio", style="Accent.TButton", command=self.on_add_socio).grid(row=1, column=len(fields), padx=8)

        search = ttk.Frame(self.tab_socios, style="Card.TFrame")
        search.pack(fill="x", padx=16)
        ttk.Label(search, text="Buscar socio:", background="#f6f9ff").pack(side="left")
        ttk.Entry(search, textvariable=self.search_socios_var, width=30).pack(side="left", padx=8)
        self.search_socios_var.trace_add("write", lambda *_: self.refresh_socios())

        self.socios_tree = ttk.Treeview(self.tab_socios, columns=("id", "nombre", "email", "telefono", "direccion"), show="headings", height=15)
        for col, text, w in [("id", "ID", 70), ("nombre", "Nombre", 200), ("email", "Email", 250), ("telefono", "Teléfono", 130), ("direccion", "Dirección", 250)]:
            self.socios_tree.heading(col, text=text)
            self.socios_tree.column(col, width=w)
        self.socios_tree.pack(fill="both", expand=True, padx=16, pady=10)
        ttk.Button(self.tab_socios, text="🗑 Borrar socio seleccionado", style="Danger.TButton", command=self.on_delete_socio).pack(anchor="e", padx=16, pady=(0, 12))

    def _build_prestamos(self):
        form = ttk.LabelFrame(self.tab_prestamos, text="Nuevo préstamo")
        form.pack(fill="x", padx=16, pady=10)
        self.libro_combo = ttk.Combobox(form, state="readonly", width=50)
        self.socio_combo = ttk.Combobox(form, state="readonly", width=36)
        ttk.Label(form, text="Libro").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Label(form, text="Socio").grid(row=0, column=1, padx=6, pady=6, sticky="w")
        self.libro_combo.grid(row=1, column=0, padx=6, pady=6)
        self.socio_combo.grid(row=1, column=1, padx=6, pady=6)
        ttk.Button(form, text="Crear préstamo", style="Accent.TButton", command=self.on_add_prestamo).grid(row=1, column=2, padx=8)

        search = ttk.Frame(self.tab_prestamos, style="Card.TFrame")
        search.pack(fill="x", padx=16)
        ttk.Label(search, text="Buscar préstamo:", background="#f6f9ff").pack(side="left")
        ttk.Entry(search, textvariable=self.search_prestamos_var, width=30).pack(side="left", padx=8)
        self.search_prestamos_var.trace_add("write", lambda *_: self.refresh_prestamos())

        self.prestamos_tree = ttk.Treeview(
            self.tab_prestamos,
            columns=("id", "libro", "socio", "inicio", "limite", "estado"),
            show="headings",
            height=15,
        )
        for col, text, w in [("id", "ID", 60), ("libro", "Libro", 220), ("socio", "Socio", 190), ("inicio", "Inicio", 110), ("limite", "Límite", 110), ("estado", "Estado", 90)]:
            self.prestamos_tree.heading(col, text=text)
            self.prestamos_tree.column(col, width=w)
        self.prestamos_tree.tag_configure("activo", background="#fef3c7")
        self.prestamos_tree.tag_configure("atrasado", background="#fecaca")
        self.prestamos_tree.tag_configure("devuelto", background="#dcfce7")
        self.prestamos_tree.pack(fill="both", expand=True, padx=16, pady=8)

        actions = ttk.Frame(self.tab_prestamos, style="Card.TFrame")
        actions.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(actions, text="Exportar CSV", command=self.on_exportar_csv).pack(side="left")
        ttk.Button(actions, text="Marcar devolución", style="Accent.TButton", command=self.on_devolver).pack(side="right", padx=(8, 0))
        ttk.Button(actions, text="🗑 Borrar préstamo", style="Danger.TButton", command=self.on_delete_prestamo).pack(side="right")

    def refresh_all(self):
        self.refresh_inicio()
        self.refresh_libros()
        self.refresh_socios()
        self.refresh_prestamos()

    def refresh_inicio(self):
        stats = self.service.stats()
        for key, lbl in self.stats_labels.items():
            lbl.config(text=str(stats[key]))
        resumen = self.service.resumen_prestamos_estado()
        self.estado_label.config(
            text=f"Estado préstamos → Activos: {resumen['activo']} · Atrasados: {resumen['atrasado']} · Devueltos: {resumen['devuelto']}"
        )
        self._populate_tree(self.atrasados_tree, [(r["id"], r["titulo"], r["nombre"], r["fecha_limite"]) for r in self.service.listar_atrasados()])
        self._render_top_libros_chart()

    def _render_top_libros_chart(self):
        data = self.service.top_libros_prestados(limit=5)
        self.top_canvas.delete("all")
        w = self.top_canvas.winfo_width() or 900
        max_value = max([r["total"] for r in data], default=1)
        for i, row in enumerate(data):
            y = 15 + i * 24
            bar_w = int((row["total"] / max_value) * (w - 260))
            self.top_canvas.create_text(10, y + 8, text=row["titulo"][:28], anchor="w", fill="#1f2937", font=("Segoe UI", 9))
            self.top_canvas.create_rectangle(220, y, 220 + bar_w, y + 16, fill="#3b82f6", width=0)
            self.top_canvas.create_text(230 + bar_w, y + 8, text=str(row["total"]), anchor="w", fill="#1e3a8a", font=("Segoe UI", 9, "bold"))

    def refresh_libros(self):
        query = self.search_libros_var.get().strip().lower()
        rows = []
        for r in self.service.listar_libros():
            text = f"{r['titulo']} {r['autor']} {r['categoria']} {r['isbn']}".lower()
            if query and query not in text:
                continue
            rows.append((r["id"], r["titulo"], r["autor"], r["categoria"], r["isbn"], f"{r['copias_disponibles']}/{r['total_copias']}"))
        self._populate_tree(self.libros_tree, rows)

    def refresh_socios(self):
        query = self.search_socios_var.get().strip().lower()
        rows = []
        for r in self.service.listar_socios():
            text = f"{r['nombre']} {r['email']} {r['telefono'] or ''} {r['direccion'] or ''}".lower()
            if query and query not in text:
                continue
            rows.append((r["id"], r["nombre"], r["email"], r["telefono"] or "", r["direccion"] or ""))
        self._populate_tree(self.socios_tree, rows)

    def refresh_prestamos(self):
        libros = self.service.libros_disponibles()
        socios = self.service.socios_disponibles()
        self.libro_map = {f"{l['titulo']} ({l['copias_disponibles']} disp.)": l["id"] for l in libros}
        self.socio_map = {s["nombre"]: s["id"] for s in socios}
        self.libro_combo["values"] = list(self.libro_map.keys())
        self.socio_combo["values"] = list(self.socio_map.keys())

        query = self.search_prestamos_var.get().strip().lower()
        self.prestamos_tree.delete(*self.prestamos_tree.get_children())
        for p in self.service.listar_prestamos():
            text = f"{p['titulo']} {p['nombre']} {p['estado']} {p['fecha_prestamo']} {p['fecha_limite']}".lower()
            if query and query not in text:
                continue
            self.prestamos_tree.insert(
                "",
                "end",
                values=(p["id"], p["titulo"], p["nombre"], p["fecha_prestamo"], p["fecha_limite"], p["estado"]),
                tags=(p["estado"],),
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

    def on_delete_libro(self):
        selected = self.libros_tree.selection()
        if not selected:
            return messagebox.showwarning("Aviso", "Selecciona un libro")
        libro_id = int(self.libros_tree.item(selected[0], "values")[0])
        if not messagebox.askyesno("Confirmar", "¿Seguro que quieres borrar el libro seleccionado?"):
            return
        try:
            self.service.borrar_libro(libro_id)
            self.set_notice("Libro borrado correctamente")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("No se pudo borrar", str(exc))

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

    def on_delete_socio(self):
        selected = self.socios_tree.selection()
        if not selected:
            return messagebox.showwarning("Aviso", "Selecciona un socio")
        socio_id = int(self.socios_tree.item(selected[0], "values")[0])
        if not messagebox.askyesno("Confirmar", "¿Seguro que quieres borrar el socio seleccionado?"):
            return
        try:
            self.service.borrar_socio(socio_id)
            self.set_notice("Socio borrado correctamente")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("No se pudo borrar", str(exc))

    def on_add_prestamo(self):
        libro = self.libro_combo.get()
        socio = self.socio_combo.get()
        if not libro or not socio:
            return messagebox.showwarning("Aviso", "Selecciona libro y socio")
        ok = self.service.crear_prestamo(self.libro_map[libro], self.socio_map[socio])
        if not ok:
            return self.set_notice("No hay copias disponibles de ese libro", ok=False)
        self.set_notice("Préstamo creado correctamente")
        self.refresh_all()

    def on_devolver(self):
        selected = self.prestamos_tree.selection()
        if not selected:
            return messagebox.showwarning("Aviso", "Selecciona un préstamo")
        prestamo_id = int(self.prestamos_tree.item(selected[0], "values")[0])
        self.service.devolver_prestamo(prestamo_id)
        self.set_notice("Préstamo marcado como devuelto")
        self.refresh_all()

    def on_delete_prestamo(self):
        selected = self.prestamos_tree.selection()
        if not selected:
            return messagebox.showwarning("Aviso", "Selecciona un préstamo")
        prestamo_id = int(self.prestamos_tree.item(selected[0], "values")[0])
        if not messagebox.askyesno("Confirmar", "¿Seguro que quieres borrar el préstamo seleccionado?"):
            return
        self.service.borrar_prestamo(prestamo_id)
        self.set_notice("Préstamo borrado correctamente")
        self.refresh_all()

    def on_exportar_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Guardar reporte")
        if not filename:
            return
        self.service.exportar_prestamos_csv(Path(filename))
        self.set_notice("Reporte CSV exportado")


def run() -> None:
    service = BibliotecaService(DB_PATH)
    app = BibliotecaDesktopApp(service)
    app.mainloop()


if __name__ == "__main__":
    run()
