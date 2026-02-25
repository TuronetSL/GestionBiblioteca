import http.client
import threading
import time
from pathlib import Path
from urllib.parse import urlencode

import app
from biblioteca.db import init_db
from http.server import ThreadingHTTPServer


def start_server(db_path: Path, port: int):
    app.DB_PATH = db_path
    init_db(db_path)
    server = ThreadingHTTPServer(("127.0.0.1", port), app.BibliotecaHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    return server


def request(method: str, path: str, data=None, port=8765):
    conn = http.client.HTTPConnection("127.0.0.1", port)
    body = urlencode(data) if data else None
    headers = {"Content-Type": "application/x-www-form-urlencoded"} if data else {}
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    payload = resp.read().decode("utf-8", errors="ignore")
    return resp.status, payload, dict(resp.getheaders())


def test_home_and_flow(tmp_path):
    server = start_server(tmp_path / "test.sqlite", 8765)
    try:
        status, html, _ = request("GET", "/")
        assert status == 200
        assert "Biblioteca de Mi Pueblo" in html

        request("POST", "/libros", {
            "titulo": "1984", "autor": "Orwell", "categoria": "Distopía", "isbn": "abc", "total_copias": "2"
        })
        request("POST", "/socios", {
            "nombre": "Lucía", "email": "lucia@example.com", "telefono": "", "direccion": ""
        })
        status, html, _ = request("GET", "/prestamos")
        assert "1984" in html
        assert "Lucía" in html
    finally:
        server.shutdown()
