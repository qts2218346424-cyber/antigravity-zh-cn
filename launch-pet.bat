@echo off
setlocal EnableExtensions
set "PET_DIR=%~dp0pet"

title Antigravity Desktop Pet Launcher

if not exist "%PET_DIR%\run_pet.py" (
    echo [ERROR] Cannot find pet\run_pet.py in %~dp0
    pause
    exit /b 1
)

:: Try pythonw for silent windowless launch
where pythonw >nul 2>&1
if %errorLevel% == 0 (
    start "" pythonw "%PET_DIR%\run_pet.py" %*
    exit /b 0
)

:: Fallback to python
where python >nul 2>&1
if %errorLevel% == 0 (
    start "" python "%PET_DIR%\run_pet.py" %*
    exit /b 0
)

echo [ERROR] Python is not installed or not in PATH!
pause
exit /b 1
