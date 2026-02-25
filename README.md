# Gestión de Biblioteca

Aplicación **de escritorio** para gestionar una biblioteca municipal, hecha en Python con `tkinter` + SQLite.

## Funcionalidades

- Catálogo de libros (alta y borrado).
- Registro de socios (alta y borrado).
- Préstamos, devoluciones y borrado de préstamos.
- Detección de préstamos atrasados.
- Panel de resumen con métricas.
- Interfaz visual renovada (pestañas, tablas y botones de acción).

## Ejecutar

```bash
python app.py
```

Se abrirá una ventana de escritorio (no usa navegador web).

## Probar

```bash
python -m pytest tests/test_app.py
```
