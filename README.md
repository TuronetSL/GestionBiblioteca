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

## Icono propio en barra de tareas (Windows)

La app usa un icono propio generado automáticamente y establece un `AppUserModelID` para que en Windows aparezca como app propia en la barra de tareas (no con el icono genérico de Python).

## Ejecutar (modo desarrollo)

```bash
python app.py
```

Se abrirá una ventana de escritorio (no usa navegador web).

## Generar ejecutable `.exe` + acceso directo en escritorio (Windows)

### Opción rápida

```bat
scripts\build_windows_exe.bat
```

### Opción PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows_exe.ps1
```

Esto genera:
- Icono temporal en `assets/app_icon.ico` (generado por script, no versionado)
- `dist/BibliotecaPueblo.exe`
- Acceso directo en el escritorio: `Biblioteca de Mi Pueblo.lnk`

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
