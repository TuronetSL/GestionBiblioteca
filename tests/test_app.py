from pathlib import Path

from app import BibliotecaService


def test_service_flow(tmp_path: Path):
    service = BibliotecaService(tmp_path / "test.sqlite")

    service.crear_libro("1984", "Orwell", "Distopía", "isbn-1984", 2)
    service.crear_socio("Lucía", "lucia@example.com", "", "")

    libros = service.listar_libros()
    socios = service.listar_socios()
    assert len(libros) == 1
    assert len(socios) == 1

    ok = service.crear_prestamo(libros[0]["id"], socios[0]["id"])
    assert ok is True

    prestamos = service.listar_prestamos()
    assert len(prestamos) == 1
    assert prestamos[0]["estado"] == "activo"

    service.devolver_prestamo(prestamos[0]["id"])
    prestamos = service.listar_prestamos()
    assert prestamos[0]["estado"] == "devuelto"


def test_prestamo_sin_copias(tmp_path: Path):
    service = BibliotecaService(tmp_path / "test.sqlite")

    service.crear_libro("Dune", "Herbert", "Ciencia ficción", "isbn-dune", 1)
    service.crear_socio("Ana", "ana@example.com", "", "")
    service.crear_socio("Luis", "luis@example.com", "", "")

    libro_id = service.listar_libros()[0]["id"]
    socios = service.listar_socios()

    assert service.crear_prestamo(libro_id, socios[0]["id"]) is True
    assert service.crear_prestamo(libro_id, socios[1]["id"]) is False
