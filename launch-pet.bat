@echo off
chcp 65001 >nul 2>&1
setlocal

set "REPO_ROOT=%~dp0"
set "PET_SCRIPT=%REPO_ROOT%pet\run_pet.py"

if not exist "%PET_SCRIPT%" (
    echo [错误] 未在当前目录下找到 pet\run_pet.py！
    pause
    exit /b 1
)

:: 探测系统 Python 解释器
set "PY_BIN="
set "PY_CON="

if exist "C:\Program Files\Python311\pythonw.exe" (
    set "PY_BIN=C:\Program Files\Python311\pythonw.exe"
    set "PY_CON=C:\Program Files\Python311\python.exe"
)

if not defined PY_BIN (
    for /f "delims=" %%I in ('where pythonw 2^>nul') do if not defined PY_BIN set "PY_BIN=%%I"
)

if not defined PY_BIN (
    for /f "delims=" %%I in ('where python 2^>nul') do if not defined PY_BIN (
        set "PY_BIN=%%I"
        set "PY_CON=%%I"
    )
)

if not defined PY_BIN (
    echo [错误] 未检测到系统 Python 环境，请先安装 Python 3！
    pause
    exit /b 1
)

if not defined PY_CON set "PY_CON=%PY_BIN%"

:: 检查是否指定了前台调试或控制台模式
if "%~1"=="--debug" goto :run_debug
if "%~1"=="--console" goto :run_debug
if "%~1"=="--smoke" goto :run_debug

:: 后台无窗启动
start "" "%PY_BIN%" "%PET_SCRIPT%" %*
echo [OK] 桌面宠物已唤醒并在主屏幕右下角与系统托盘常驻呈现！
exit /b 0

:run_debug
echo 正在以调试/控制台模式启动 Antigravity 桌面宠物...
"%PY_CON%" "%PET_SCRIPT%" %*
pause
exit /b 0
