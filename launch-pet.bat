@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
set "PET_DIR=%~dp0pet"
cd /d "%~dp0"

title Antigravity 灵动桌面小宠物启动器

if not exist "%PET_DIR%\run_pet.py" (
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
) else (
    for /f "delims=" %%I in ('where pythonw 2^>nul') do if not defined PY_BIN set "PY_BIN=%%I"
    for /f "delims=" %%I in ('where python 2^>nul') do if not defined PY_CON set "PY_CON=%%I"
)

if not defined PY_BIN set "PY_BIN=%PY_CON%"

if not defined PY_BIN (
    echo [错误] 未检测到系统 Python 环境，请先安装 Python 3 并将其添加到系统环境变量 PATH 中！
    pause
    exit /b 1
)

:: 检查是否指定了前台调试或控制台模式
set "IS_DEBUG=0"
if "%~1"=="--debug" set "IS_DEBUG=1"
if "%~1"=="--console" set "IS_DEBUG=1"
if "%~1"=="--smoke" set "IS_DEBUG=1"

if "%IS_DEBUG%"=="1" (
    echo 正在以调试/控制台模式启动 Antigravity 桌面宠物...
    "%PY_CON%" "%PET_DIR%\run_pet.py" %*
    pause
    exit /b 0
)

:: 确保用户配置目录存在
if not exist "%USERPROFILE%\.gemini" mkdir "%USERPROFILE%\.gemini"

echo 正在唤醒 Antigravity 灵动桌面小宠物...
start "" "%PY_BIN%" "%PET_DIR%\run_pet.py" %*

:: 等待 2 秒检查是否成功驻留
timeout /t 2 /nobreak >nul 2>&1

echo [OK] 桌面宠物已唤醒并在主屏幕右下角与系统托盘常驻呈现！
echo 如需调试或查看控制台日志，请运行: launch-pet.bat --debug
timeout /t 3 /nobreak >nul 2>&1
exit /b 0
