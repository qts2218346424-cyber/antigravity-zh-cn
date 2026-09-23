@echo off
chcp 65001 >nul
title Antigravity 后台自动维护与 GitHub 同步看门狗配置器

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
set "PS_SCRIPT=%SCRIPT_DIR%watchdog.ps1"
set "TASK_NAME=AntigravityLocalizationWatchdog"

echo ============================================================
echo      Antigravity 自动化版本跟踪与持续同步看门狗配置
echo ============================================================
echo.
echo [1] 注册 Windows 后台看门狗任务 (开机自启 + 每小时定时检测)
echo [2] 立即手动触发一次维护与 GitHub 同步
echo [3] 卸载 / 停止 Windows 后台看门狗任务
echo [4] 查看当前看门狗运行状态与日志
echo [Q] 退出
echo.
set /p "CHOICE=请输入选项数字 [1-4, Q]: "

if /i "%CHOICE%"=="1" goto INSTALL_TASK
if /i "%CHOICE%"=="2" goto RUN_NOW
if /i "%CHOICE%"=="3" goto UNINSTALL_TASK
if /i "%CHOICE%"=="4" goto VIEW_LOGS
if /i "%CHOICE%"=="Q" goto EXIT
goto EXIT

:INSTALL_TASK
echo.
echo [*] 正在注册 Windows 定时任务: %TASK_NAME% ...
schtasks /create /tn "%TASK_NAME%" /tr "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \"%PS_SCRIPT%\"" /sc HOURLY /mo 1 /f >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 权限不足，正在尝试以管理员权限注册...
    powershell -Command "Start-Process schtasks -ArgumentList '/create /tn \"%TASK_NAME%\" /tr \"powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File `\"%PS_SCRIPT%`\"\" /sc HOURLY /mo 1 /f' -Verb RunAs"
)
echo [OK] Windows 定时看门狗任务已成功挂载！
echo      系统将在后台每小时自动检测 Antigravity 是否升级，
echo      一旦发现新版将自动完成汉化并推送至 GitHub！
echo.
pause
goto EXIT

:RUN_NOW
echo.
echo [*] 正在手动执行一次版本检测与维护流水线...
python "%SCRIPT_DIR%auto_maintainer.py"
echo.
pause
goto EXIT

:UNINSTALL_TASK
echo.
echo [*] 正在注销 Windows 定时任务: %TASK_NAME% ...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
echo [OK] 已成功移除后台看门狗任务。
echo.
pause
goto EXIT

:VIEW_LOGS
echo.
echo ==================== 看门狗最近运行日志 ====================
if exist "%SCRIPT_DIR%watchdog.log" (
    powershell -Command "Get-Content '%SCRIPT_DIR%watchdog.log' -Tail 30"
) else (
    echo [i] 暂无看门狗日志记录。
)
echo ============================================================
echo.
pause
goto EXIT

:EXIT
exit /b 0
