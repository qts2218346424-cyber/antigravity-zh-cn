@echo off
chcp 65001 >nul
title Antigravity 简体中文汉化补丁安装器

:: 检查管理员提权
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunScript
) else (
    echo 正在请求管理员权限以修改程序文件...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

:RunScript
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows.ps1"
if %errorLevel% neq 0 (
    echo.
    echo 执行过程中出现提示或错误，请按任意键退出...
    pause >nul
)
