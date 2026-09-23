@echo off
setlocal EnableExtensions
set "AGY_DIR=%~dp0"

title Antigravity Chinese Localization Installer

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunDirect
)

echo Requesting administrator privileges...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$src = $env:AGY_DIR; $script = Join-Path $src 'scripts\install_windows.ps1'; $arg = '-NoProfile -ExecutionPolicy Bypass -File ' + [char]34 + $script + [char]34; try { Start-Process powershell.exe -ArgumentList $arg -WorkingDirectory $src -Verb RunAs -ErrorAction Stop; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
if %errorLevel% neq 0 (
    echo.
    echo Failed to request administrator privileges.
    echo Please right-click install-windows.bat and select 'Run as administrator'.
    pause
)
exit /b

:RunDirect
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows.ps1"
if %errorLevel% neq 0 (
    echo.
    pause
)
