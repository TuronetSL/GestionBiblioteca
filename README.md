# Gestión de Biblioteca

Aplicación **de escritorio** para gestionar una biblioteca municipal, hecha en Python con `tkinter` + SQLite.

## Funcionalidades actuales

- Catálogo de libros (alta, búsqueda y borrado).
- Registro de socios (alta, búsqueda y borrado).
- Préstamos, devoluciones y borrado de préstamos.
- Detección de préstamos atrasados.
- Dashboard visual con métricas de estado y top de libros prestados.
- Resaltado visual por estado de préstamo (activo, atrasado, devuelto).
- Exportación de préstamos a CSV.

## Ejecutar

```bash
python app.py
```

Se abrirá una ventana de escritorio (no usa navegador web).

## Probar

```bash
python -m pytest tests/test_app.py
```

## Próximas mejoras recomendadas

- Sistema de usuarios/roles (bibliotecario, administrador).
- Historial por socio con fechas y préstamos pasados.
- Módulo de reservas de libros.
- Notificaciones automáticas de vencimientos (email/WhatsApp).
- Cálculo de sanciones por retraso.
- Backup/restauración de base de datos desde la interfaz.
