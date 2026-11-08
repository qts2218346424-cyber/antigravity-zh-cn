@echo off
@chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'E:\antigravity-cn\scripts\desktop_pet_app.py' -WorkingDirectory 'E:\antigravity-cn' -WindowStyle Hidden"
exit
