@echo off
@chcp 65001 >nul
title 退出桌面桌宠
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'desktop_pet_app\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo [OK] 桌面宠物已安全退出。
ping 127.0.0.1 -n 2 >nul
exit
