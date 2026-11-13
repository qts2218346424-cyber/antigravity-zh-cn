@echo off
@chcp 65001 >nul
cd /d "%~dp0"
rem 启动独立桌面桌宠（Windows），路径相对于本脚本所在目录
where pythonw >nul 2>nul && (start "" pythonw "%~dp0scripts\desktop_pet_app.py") || (start "" python "%~dp0scripts\desktop_pet_app.py")
exit /b 0
