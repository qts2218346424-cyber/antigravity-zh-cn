@echo off
setlocal EnableExtensions
set "PET_DIR=%~dp0pet"
cd /d "%~dp0"

title Antigravity Desktop Pet Launcher

if not exist "%PET_DIR%\run_pet.py" (
    echo [ERROR] Cannot find pet\run_pet.py in %~dp0
    pause
    exit /b 1
)

:: Find Python executable path
set "PY_BIN="
if exist "C:\Program Files\Python311\pythonw.exe" (
    set "PY_BIN=C:\Program Files\Python311\pythonw.exe"
) else (
    for /f "delims=" %%I in ('where pythonw 2^>nul') do if not defined PY_BIN set "PY_BIN=%%I"
)

if not defined PY_BIN (
    if exist "C:\Program Files\Python311\python.exe" (
        set "PY_BIN=C:\Program Files\Python311\python.exe"
    ) else (
        for /f "delims=" %%I in ('where python 2^>nul') do if not defined PY_BIN set "PY_BIN=%%I"
    )
)

if defined PY_BIN (
    start "" "%PY_BIN%" "%PET_DIR%\run_pet.py" %*
    exit /b 0
)

echo [ERROR] Python is not installed or not in PATH!
pause
exit /b 1
