@echo off
setlocal
powershell -ExecutionPolicy Bypass -File scripts\build_windows_exe.ps1
endlocal
