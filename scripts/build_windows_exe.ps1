param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/5] Installing PyInstaller..."
& $Python -m pip install pyinstaller

Write-Host "[2/5] Generating icon file..."
& $Python scripts/generate_icon.py

Write-Host "[3/5] Building executable..."
& $Python -m PyInstaller `
  --noconfirm `
  --onefile `
  --windowed `
  --name BibliotecaPueblo `
  --icon assets/app_icon.ico `
  app.py

Write-Host "[4/5] Creating desktop shortcut..."
$desktop = [Environment]::GetFolderPath("Desktop")
$target = Join-Path (Get-Location) "dist\BibliotecaPueblo.exe"
$shortcutPath = Join-Path $desktop "Biblioteca de Mi Pueblo.lnk"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = (Get-Location).Path
$shortcut.IconLocation = "$target,0"
$shortcut.Description = "Gestión Biblioteca de Mi Pueblo"
$shortcut.Save()

Write-Host "[5/5] Done. EXE at dist\\BibliotecaPueblo.exe"
