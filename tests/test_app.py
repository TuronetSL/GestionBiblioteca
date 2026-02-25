from pathlib import Path

import pytest

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


def test_borrar_prestamo_activo_restaura_copia(tmp_path: Path):
    service = BibliotecaService(tmp_path / "test.sqlite")
    service.crear_libro("Neuromante", "Gibson", "Sci-Fi", "isbn-neuro", 1)
    service.crear_socio("Mario", "mario@example.com", "", "")

    libro = service.listar_libros()[0]
    socio = service.listar_socios()[0]

    assert service.crear_prestamo(libro["id"], socio["id"]) is True
    prestamo = service.listar_prestamos()[0]

    service.borrar_prestamo(prestamo["id"])

    assert len(service.listar_prestamos()) == 0
    libro = service.listar_libros()[0]
    assert libro["copias_disponibles"] == 1


def test_borrado_libro_y_socio_bloqueado_por_prestamo_activo(tmp_path: Path):
    service = BibliotecaService(tmp_path / "test.sqlite")
    service.crear_libro("It", "Stephen King", "Terror", "isbn-it", 2)
    service.crear_socio("Pablo", "pablo@example.com", "", "")

    libro = service.listar_libros()[0]
    socio = service.listar_socios()[0]
    service.crear_prestamo(libro["id"], socio["id"])

    with pytest.raises(ValueError):
        service.borrar_libro(libro["id"])

    with pytest.raises(ValueError):
        service.borrar_socio(socio["id"])


def test_borrar_libro_y_socio_sin_prestamos_activos(tmp_path: Path):
    service = BibliotecaService(tmp_path / "test.sqlite")
    service.crear_libro("Solaris", "Lem", "Sci-Fi", "isbn-solaris", 1)
    service.crear_socio("Elena", "elena@example.com", "", "")

    libro = service.listar_libros()[0]
    socio = service.listar_socios()[0]

    service.borrar_libro(libro["id"])
    service.borrar_socio(socio["id"])

    assert len(service.listar_libros()) == 0
    assert len(service.listar_socios()) == 0
