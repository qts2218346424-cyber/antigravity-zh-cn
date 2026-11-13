# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 规格文件：把汉化补丁 + 材质包管理 + 桌宠 + 自动重注入打成单个可执行文件
#   pyinstaller packaging/agzh_app.spec --noconfirm --clean
# 产物：dist/AntigravityZhCN(.exe)
import os
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
SCRIPTS = ROOT / "scripts"
RES = ROOT / "resources"

# 运行时需要的资源（词典、运行时 JS、启动动画素材、内置材质包）。排除维护用的大文件。
EXCLUDE_RES = {"untranslated.json", "untranslated_all.json", "untranslated_settings.json"}
datas = []
for p in RES.rglob("*"):
    if p.is_file() and p.name not in EXCLUDE_RES and "__pycache__" not in p.parts:
        datas.append((str(p), str(p.parent.relative_to(ROOT))))
# 打包版 resource_root() = sys._MEIPASS，脚本也作为数据随包（供 launch_pet 等按路径定位）
for name in ("desktop_pet_app.py",):
    datas.append((str(SCRIPTS / name), "scripts"))
# 界面图标（PNG 窗口图标 + ICO 任务栏图标），约 50 KB
APP_ASSETS = ROOT / "app" / "assets"
for p in APP_ASSETS.glob("*"):
    if p.is_file():
        datas.append((str(p), "app/assets"))

hidden = [
    "agzh", "agzh_core", "skin_manager", "skin_injector", "auto_reapply",
    "patch_antigravity", "splash_generator", "build_kimetsu_characters_splash", "localize_skills",
    "ui_kit", "media_helper",  # media_helper：打过补丁的 Antigravity 通过 “AntigravityZhCN --media” 调用
    "yaml", "PIL.Image",  # 预览图在后台用 Pillow 缩放后重新编码为 PNG，由 Tk 原生显示（无需 PIL.ImageTk）
]
if sys.platform == "win32":
    hidden += ["desktop_pet_app", "quota_helper", "winreg"]
    # 桌宠依赖可选：安装了才打进来
    for mod in ("webview", "pystray", "win32gui", "win32con"):
        try:
            __import__(mod)
            hidden.append(mod)
        except Exception:
            pass

block_cipher = None

a = Analysis(
    [str(ROOT / "app" / "agzh_app.py")],
    pathex=[str(SCRIPTS), str(RES), str(ROOT / "app")],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    # 不需要的大模块排除在外，保持单文件体积小
    excludes=["numpy", "pandas", "matplotlib", "scipy", "IPython", "pytest", "PIL.ImageQt", "PyQt5", "PyQt6",
              "PySide2", "PySide6", "tkinter.test", "pydoc_data"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AntigravityZhCN",
    debug=False,
    strip=False,
    upx=True,
    console=False,  # 图形界面程序，不弹黑色控制台
    disable_windowed_traceback=False,
    icon=str(APP_ASSETS / ("icon.ico" if sys.platform == "win32" else "icon.png")) if APP_ASSETS.is_dir() else None,
)

if sys.platform == "darwin":
    app = BUNDLE(exe, name="AntigravityZhCN.app", bundle_identifier="com.antigravity-zh-cn.manager")
