@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 一体化管理器（源码运行版）：材质包 / 汉化补丁 / 桌宠 / 更新后自动重注入
rem 打包好的单文件版请到 GitHub Actions 的构建产物中下载 AntigravityZhCN.exe
where pythonw >nul 2>nul && (start "" pythonw "%~dp0app\agzh_app.py") || (start "" python "%~dp0app\agzh_app.py")
exit /b 0
