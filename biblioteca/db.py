import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS libros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    autor TEXT NOT NULL,
    categoria TEXT NOT NULL,
    isbn TEXT UNIQUE NOT NULL,
    total_copias INTEGER NOT NULL CHECK(total_copias > 0),
    copias_disponibles INTEGER NOT NULL CHECK(copias_disponibles >= 0),
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS socios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    telefono TEXT,
    direccion TEXT,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prestamos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    libro_id INTEGER NOT NULL,
    socio_id INTEGER NOT NULL,
    fecha_prestamo TEXT NOT NULL,
    fecha_limite TEXT NOT NULL,
    fecha_devolucion TEXT,
    estado TEXT NOT NULL CHECK(estado IN ('activo', 'devuelto', 'atrasado')),
    FOREIGN KEY(libro_id) REFERENCES libros(id),
    FOREIGN KEY(socio_id) REFERENCES socios(id)
);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
